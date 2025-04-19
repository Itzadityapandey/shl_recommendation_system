import streamlit as st
from recommender import recommend_assessments
import pandas as pd
import json

st.set_page_config(page_title="SHL Assessment Recommender", layout="wide")

# Sidebar for inputs
st.sidebar.header("Input Options")
input_type = st.sidebar.radio("Select Input Type", ["Text", "URL"])

if input_type == "Text":
    job_desc = st.sidebar.text_area("Enter Job Description", height=200, placeholder="e.g., We are seeking an Administrative Assistant to manage routine clerical tasks...")
else:
    job_url = st.sidebar.text_input("Enter Job URL", placeholder="e.g., https://www.indeed.com/viewjob?jk=1234567890")

# Main content area
st.title("SHL Assessment Recommender")
st.markdown("Discover tailored SHL assessments based on your job requirements.")

# Health Check
st.sidebar.subheader("System Check")
if st.sidebar.button("Check API Health"):
    st.sidebar.json({"status": "healthy"})

# Recommendation button
if st.sidebar.button("Generate Recommendations"):
    if input_type == "Text" and job_desc:
        with st.spinner("Generating recommendations..."):
            recommendations = recommend_assessments(job_description=job_desc, top_n=10)
    elif input_type == "URL" and job_url:
        with st.spinner("Scraping job description and generating recommendations..."):
            recommendations = recommend_assessments(job_url=job_url, top_n=10)
    else:
        st.error("Please provide a job description or URL.")
        st.stop()

    if recommendations:
        st.success("Recommendations generated!")
        # Convert to DataFrame for tabular display, excluding description and adding index starting from 1
        df = pd.DataFrame(recommendations)
        df = df[["name", "url", "duration", "test_type", "remote_support", "adaptive_support"]]
        # Make URL clickable as a hyperlink
        df["url"] = df["url"].apply(lambda x: f'<a href="{x}" target="_blank">{x}</a>')
        df["test_type"] = df["test_type"].apply(lambda x: ", ".join(x) if isinstance(x, list) else x)
        df["duration"] = df["duration"].apply(lambda x: x if x != "N/A" else x + " minutes")
        # Reset index to start from 1
        df.index = df.index + 1
        # Render table with HTML for clickable links
        st.write(df.to_html(escape=False), unsafe_allow_html=True)

        # JSON Output with description included
        json_output = {
            "recommended_assessments": [
                {
                    "url": rec["url"],
                    "adaptive_support": rec["adaptive_support"],
                    "description": rec["description"],
                    "duration": int(rec["duration"].split()[0]) if rec["duration"] != "N/A" and "minutes" in rec["duration"] else 0,
                    "remote_support": rec["remote_support"],
                    "test_type": [rec["test_type"]] if not isinstance(rec["test_type"], list) else rec["test_type"]
                } for rec in recommendations
            ]
        }
        st.subheader("JSON Output (for API)")
        st.json(json_output)
    else:
        st.error("No recommendations found. Please check the input or dataset.")

# Footer
st.markdown("---")
st.markdown("Powered by Streamlit | Data from SHL Assessment Catalog")
