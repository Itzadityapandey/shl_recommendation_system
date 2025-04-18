import streamlit as st
from recommender import recommend_assessments

st.set_page_config(page_title="SHL Assessment Recommender", layout="wide")

st.title("SHL Assessment Recommender")
st.markdown("Enter a job description or a job posting URL to get recommended SHL assessments.")

# Input selection
input_type = st.radio("Input Type", ["Text", "URL"])

if input_type == "Text":
    job_desc = st.text_area("Enter Job Description", height=200, placeholder="e.g., We are seeking an Administrative Assistant to manage routine clerical tasks...")
    if st.button("Recommend"):
        if job_desc:
            with st.spinner("Generating recommendations..."):
                recommendations = recommend_assessments(job_description=job_desc, top_n=10)
            if recommendations:
                st.success("Recommendations generated!")
                for i, rec in enumerate(recommendations, 1):
                    st.subheader(f"{i}. {rec['name']} (Similarity: {rec['similarity']:.4f})")
                    st.write(f"[Link to Assessment]({rec['url']})")
                    st.write(f"**Description**: {rec['description']}")
                    st.write(f"**Test Type**: {rec['test_type']}")
                    st.write("---")
            else:
                st.error("No recommendations found. Please check the input or dataset.")
        else:
            st.error("Please enter a job description.")
else:
    job_url = st.text_input("Enter Job URL", placeholder="e.g., https://www.indeed.com/viewjob?jk=1234567890")
    if st.button("Recommend"):
        if job_url:
            with st.spinner("Scraping job description and generating recommendations..."):
                recommendations = recommend_assessments(job_url=job_url, top_n=10)
            if recommendations:
                st.success("Recommendations generated!")
                for i, rec in enumerate(recommendations, 1):
                    st.subheader(f"{i}. {rec['name']} (Similarity: {rec['similarity']:.4f})")
                    st.write(f"[Link to Assessment]({rec['url']})")
                    st.write(f"**Description**: {rec['description']}")
                    st.write(f"**Test Type**: {rec['test_type']}")
                    st.write("---")
            else:
                st.error("No recommendations found. Please check the URL or dataset.")
        else:
            st.error("Please enter a job URL.")

# Footer
st.markdown("---")
st.markdown("Built with Streamlit | Data sourced from SHL Assessment Catalog")