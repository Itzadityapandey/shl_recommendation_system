# SHL Assessment Recommender

An intelligent system that recommends relevant SHL assessments based on a job description or a job posting URL. It uses Google Gemini embeddings for semantic matching and Streamlit for an interactive user interface.This project is a web-based tool designed to recommend SHL assessments for hiring managers based on job descriptions or job posting URLs. The system is optimized for easy access and deployment.



## Features

- Accepts job descriptions via text or URL
- Extracts and cleans job content from web pages
- Generates embeddings using the Google Gemini API
- Computes semantic similarity with pre-embedded SHL assessments
- Recommends top assessments with metadata and links
- Provides both interactive UI and JSON output for API use
- Supports automated SHL catalog crawling and dataset updates



## How It Works

1. User submits a job description or a job posting URL.
2. The description is embedded using Gemini.
3. A dataset of SHL assessments (with precomputed embeddings) is loaded.
4. Cosine similarity is used to identify the closest matches.
5. The top recommendations are displayed with relevant details.



## Architecture

<p align="center">
  <img src="assets/assetsarchitecture.png" alt="SHL Architecture" width="300"/>
</p>
The system follows a modular design:
- Input layer (URL or text)
- Embedding generation via Gemini API
- Similarity scoring using scikit-learn
- Result rendering in Streamlit UI and JSON output



## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/shl-assessment-recommender.git
cd shl-assessment-recommender
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure API Key

Create a `.streamlit/secrets.toml` file:

```toml
GEMINI_API_KEY = "your_gemini_api_key"
```

> Do not commit this file. Add it to `.gitignore`.



## Deployment (Streamlit Cloud)

1. Push the project to GitHub.
2. Go to [streamlit.io/cloud](https://streamlit.io/cloud).
3. Connect your repository.
4. Add the `GEMINI_API_KEY` in the Secrets section of the app settings.
5. Deploy your app.



## 🧪 API Testing & Usage

In addition to the Streamlit interface, the system provides a RESTful API for integration into external workflows.

### 🔍 Health Check

**GET**  
`https://shl-recommendation-system-6d1j.onrender.com/`

**Response:**

```json
{ "status": "healthy" }
```

### 🧠 Recommendation Endpoint

**POST**  
`https://shl-recommendation-system-6d1j.onrender.com/recommend`

#### Example Input (JSON)

```json
{
  "job_description": "We are looking for a data analyst with strong SQL and Python skills."
}
```

or

```json
{
  "job_url": "https://example.com/job-posting"
}
```

#### Sample Output

```json
[
  {
    "Assessment Name": "Data Analysis Test",
    "URL": "https://www.shl.com/...",
    "Remote Testing Support": "Yes",
    "Adaptive/IRT Support": "Yes",
    "Duration": "40 mins",
    "Test Type": "Cognitive"
  }
]
```

You can test the API via [Postman](https://www.postman.com/) or any REST client.

---

## 🧯 Error Handling

| Scenario               | Response                          |
|------------------------|-----------------------------------|
| Missing API key        | Instruction to set credentials    |
| No input provided      | Prompt requesting input           |
| Invalid job URL        | Validation error                  |
| Gemini API failure     | Graceful fallback or error shown  |
| No matching assessments| Friendly message displayed        |

---

## Project Structure

```
├── app.py                  # Streamlit frontend
├── recommender.py          # Embedding and similarity logic
├── crawler.py              # SHL scraper and embedding builder
├── shl_assessments.csv # Assessment dataset
├── assets/
│   └── assetsarchitecture.png  # Architecture diagram
├── requirements.txt        # Dependencies
└── .streamlit/
    └── secrets.toml        # API key (excluded from Git)
```





## Technologies Used

- Google Gemini API (text embeddings)
- scikit-learn (cosine similarity)
- BeautifulSoup (web scraping)
- Streamlit (web interface)
- pandas, numpy (data processing)

