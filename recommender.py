 # Replace with your API key from https://ai.google.dev/
import pandas as pd
import requests
from bs4 import BeautifulSoup
import json
import google.generativeai as genai
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import re
import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time

# Load API key from Streamlit secrets
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
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
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        print(f"Response status: {response.status_code}")
        
        soup = BeautifulSoup(response.content, "html.parser")
        
        paragraphs = soup.find_all("p")
        description_parts = []
        
        job_keywords = [
            "responsibilities", "duties", "qualifications", "requirements",
            "skills", "experience", "role", "position", "overview", "description"
        ]
        
        for p in paragraphs:
            text = p.get_text(strip=True)
            if len(text) < 50 or any(phrase in text.lower() for phrase in ["apply now", "privacy policy", "equal opportunity", "cookie policy"]):
                continue
            if len(text) > 100 or any(keyword in text.lower() for keyword in job_keywords):
                description_parts.append(text)
        
        if not description_parts or sum(len(part) for part in description_parts) < 200:
            print("Insufficient content from <p> tags, trying <div> and <section>...")
            for tag in soup.find_all(["div", "section"]):
                text = tag.get_text(strip=True)
                if len(text) > 200 and any(keyword in text.lower() for keyword in job_keywords):
                    sentences = re.split(r'[.!?]+', text)
                    sentences = [s.strip() for s in sentences if len(s.strip()) > 50]
                    description_parts.extend(sentences)
                    break
        
        if description_parts:
            description = " ".join(description_parts)
            description = re.sub(r'\s+', ' ', description).strip()
            description = description[:5000]
            print(f"Extracted description (first 100 chars): {description[:100]}...")
            return description
        else:
            print("No relevant description found in <p>, <div>, or <section> tags.")
            return "N/A"
            
    except Exception as e:
        print(f"Error scraping job description from {url}: {e}")
        return "N/A"

def fetch_duration(url):
    """Fetch duration from assessment URL using Selenium fallback."""
    try:
        # Initial attempt with requests
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
        else:
            raise Exception(f"Non-200 status: {response.status_code}")

        duration_info = "N/A"
        # Target the specific Assessment length section
        duration_section = soup.find("h4", string="Assessment length")
        if duration_section:
            duration_p = duration_section.find_next("p")
            if duration_p:
                duration_match = re.search(r"Approximate Completion Time in minutes = (\d+)", duration_p.get_text(), re.IGNORECASE)
                if duration_match:
                    duration_info = f"{duration_match.group(1)} minutes"
                    print(f"Debug: Found duration {duration_info} for {url}")
                else:
                    print(f"Debug: Duration pattern not matched in {url}, text: {duration_p.get_text()}")

        # Fallback to Selenium for dynamic content
        if duration_info == "N/A":
            options = Options()
            options.add_argument("--headless")
            driver = webdriver.Chrome(options=options, executable_path=ChromeDriverManager().install())
            driver.get(url)
            time.sleep(2)  # Wait for JavaScript
            soup = BeautifulSoup(driver.page_source, "html.parser")
            driver.quit()

            duration_section = soup.find("h4", string="Assessment length")
            if duration_section:
                duration_p = duration_section.find_next("p")
                if duration_p:
                    duration_match = re.search(r"Approximate Completion Time in minutes = (\d+)", duration_p.get_text(), re.IGNORECASE)
                    if duration_match:
                        duration_info = f"{duration_match.group(1)} minutes"
                        print(f"Debug: Found duration {duration_info} via Selenium for {url}")
            if duration_info == "N/A":
                print(f"Debug: No duration found in {url}")

        return duration_info

    except Exception as e:
        print(f"Error fetching duration for {url}: {e}")
        return "N/A"

def recommend_assessments(job_description=None, job_url=None, dataset_path="shl_assessments.csv", top_n=10):
    """Recommend assessments based on job description or URL and fetch durations for recommended ones."""
    try:
        # Load dataset and remove duplicates
        df = pd.read_csv(dataset_path)
        if df.empty:
            print("Error: Dataset is empty.")
            return []
        
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
                if emb:
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
            row = df.iloc[df_idx]
            # Crawl the URL to get duration for recommended assessment
            duration = fetch_duration(row["url"])
            recommendations.append({
                "name": row["name"],
                "url": row["url"],
                "description": row["description"],
                "duration": duration,
                "test_type": row["test_type"],
                "remote_support": row["remote_support"],
                "adaptive_support": row["adaptive_support"],
                "similarity": similarities[idx]
            })

        return recommendations

    except Exception as e:
        print(f"Error in recommendation: {e}")
        return []

# Streamlit UI
if __name__ == "__main__":
    st.title("SHL Assessment Recommender")
    input_type = st.radio("Select input type:", ["Job Description Text", "Job Description URL"])
    
    job_desc = ""
    if input_type == "Job Description Text":
        job_desc = st.text_area("Paste the job description here:")
    elif input_type == "Job Description URL":
        job_url = st.text_input("Enter the job description URL:")
        if job_url:
            job_desc = scrape_job_description(job_url)
    
    if st.button("Recommend Assessments") and job_desc.strip():
        with st.spinner("Generating recommendations..."):
            recs = recommend_assessments(job_description=job_desc if input_type == "Job Description Text" else None, job_url=job_url if input_type == "Job Description URL" else None)
            if recs:
                st.table(pd.DataFrame(recs))
            else:
                st.error("No recommendations generated.")
