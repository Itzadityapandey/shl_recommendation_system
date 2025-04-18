import pandas as pd
import requests
from bs4 import BeautifulSoup
import json
import google.generativeai as genai
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import re

import streamlit as st
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
 # Replace with your API key from https://ai.google.dev/
GEMINI_EMBEDDING_MODEL = "text-embedding-004"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def get_gemini_embedding(text):
    """Generate embedding using text-embedding-004."""
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_EMBEDDING_MODEL}:embedContent?key={GEMINI_API_KEY}"
        headers = {"Content-Type": "application/json"}
        data = {
            "model": f"models/{GEMINI_EMBEDDING_MODEL}",
            "content": {"parts": [{"text": text}]}
        }
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        embedding = response.json()["embedding"]["values"]
        return embedding
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return []

def scrape_job_description(url):
    """Generically scrape job description from hiring links, focusing on <p> tags."""
    print(f"Attempting to scrape URL: {url}")
    try:
        # Fetch the page
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        print(f"Response status: {response.status_code}")
        
        soup = BeautifulSoup(response.content, "html.parser")
        
        # Step 1: Extract all <p> tags
        paragraphs = soup.find_all("p")
        description_parts = []
        
        # Keywords indicating job description content
        job_keywords = [
            "responsibilities", "duties", "qualifications", "requirements",
            "skills", "experience", "role", "position", "overview", "description"
        ]
        
        # Filter <p> tags likely to contain job description
        for p in paragraphs:
            text = p.get_text(strip=True)
            # Skip empty or short paragraphs, or those with boilerplate text
            if len(text) < 50 or any(phrase in text.lower() for phrase in ["apply now", "privacy policy", "equal opportunity", "cookie policy"]):
                continue
            # Prioritize paragraphs with job-related keywords or significant length
            if len(text) > 100 or any(keyword in text.lower() for keyword in job_keywords):
                description_parts.append(text)
        
        # Step 2: Fallback to <div> or <section> if <p> tags are insufficient
        if not description_parts or sum(len(part) for part in description_parts) < 200:
            print("Insufficient content from <p> tags, trying <div> and <section>...")
            for tag in soup.find_all(["div", "section"]):
                text = tag.get_text(strip=True)
                if len(text) > 200 and any(keyword in text.lower() for keyword in job_keywords):
                    # Split into sentences to mimic paragraph structure
                    sentences = re.split(r'[.!?]+', text)
                    sentences = [s.strip() for s in sentences if len(s.strip()) > 50]
                    description_parts.extend(sentences)
                    break
        
        # Step 3: Combine and clean description
        if description_parts:
            description = " ".join(description_parts)
            # Clean up excessive whitespace and boilerplate
            description = re.sub(r'\s+', ' ', description).strip()
            # Limit to 5000 characters to avoid Gemini API limits
            description = description[:5000]
            print(f"Extracted description (first 100 chars): {description[:100]}...")
            return description
        else:
            print("No relevant description found in <p>, <div>, or <section> tags.")
            return "N/A"
            
    except Exception as e:
        print(f"Error scraping job description from {url}: {e}")
        return "N/A"

def recommend_assessments(job_description=None, job_url=None, dataset_path="shl_assessments.csv", top_n=10):
    """Recommend assessments based on job description or URL."""
    try:
        # Load dataset and remove duplicates
        df = pd.read_csv(dataset_path)
        if df.empty:
            print("Error: Dataset is empty.")
            return []
        
        # Remove duplicates based on 'name' or 'url'
        df = df.drop_duplicates(subset=["name", "url"], keep="first")
        if df.empty:
            print("Error: Dataset is empty after removing duplicates.")
            return []

        # Get job description
        if job_url:
            job_description = scrape_job_description(job_url)
            if job_description == "N/A":
                print("Failed to scrape job description. Please provide text input.")
                return []
        elif not job_description:
            print("Error: No job description or URL provided.")
            return []

        # Generate embedding for job description
        job_embedding = get_gemini_embedding(job_description)
        if not job_embedding:
            print("Failed to generate embedding for job description.")
            return []

        # Parse assessment embeddings
        assessment_embeddings = []
        valid_indices = []
        for idx, emb_str in enumerate(df["embedding"]):
            try:
                emb = json.loads(emb_str)
                if emb:  # Ensure embedding is not empty
                    assessment_embeddings.append(emb)
                    valid_indices.append(idx)
            except:
                continue

        if not assessment_embeddings:
            print("No valid assessment embeddings found.")
            return []

        # Compute cosine similarity
        assessment_embeddings = np.array(assessment_embeddings)
        job_embedding = np.array([job_embedding])
        similarities = cosine_similarity(job_embedding, assessment_embeddings)[0]

        # Get top N assessments
        top_indices = np.argsort(similarities)[-top_n:][::-1]
        recommendations = []
        for idx in top_indices:
            df_idx = valid_indices[idx]
            recommendations.append({
                "name": df.iloc[df_idx]["name"],
                "url": df.iloc[df_idx]["url"],
                "description": df.iloc[df_idx]["description"],
                "test_type": df.iloc[df_idx]["test_type"],
                "similarity": similarities[idx]
            })

        return recommendations

    except Exception as e:
        print(f"Error in recommendation: {e}")
        return []
