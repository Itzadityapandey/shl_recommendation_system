from flask import Flask, request, jsonify
from recommenderRender import recommend_assessments  
import os

app = Flask(__name__)

# Health check route
@app.route('/', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

@app.route('/recommend', methods=['POST'])
def recommend():
    data = request.get_json()
    job_description = data.get('job_description')
    job_url = data.get('job_url')
    if not job_description and not job_url:
        return jsonify({"error": "Job description or URL is required"}), 400
    recommendations = recommend_assessments(job_description=job_description, job_url=job_url, top_n=10)
    if recommendations:
        # Construct each recommendation with explicit key order
        ordered_recommendations = [
            {
                "url": rec["url"],  # First field
                "adaptive_support": rec["adaptive_support"].capitalize(),
                "description": rec["description"],
                "duration": (
                    int(rec["duration"].split()[0])
                    if isinstance(rec["duration"], str) and "minutes" in rec["duration"].lower()
                    else 0
                ),
                "remote_support": rec["remote_support"].capitalize(),
                "test_type": [rec["test_type"]] if not isinstance(rec["test_type"], list) else rec["test_type"]
            } for rec in recommendations
        ]
        # Construct the final response with explicit key order
        json_output = {"recommended_assessments": ordered_recommendations}
        return jsonify(json_output)
    return jsonify({"error": "No recommendations found"}), 404

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
