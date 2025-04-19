from flask import Flask, request, jsonify
from recommenderRender import recommend_assessments  # Updated import

app = Flask(__name__)

@app.route('/recommend', methods=['POST'])
def recommend():
    data = request.get_json()
    job_description = data.get('job_description')
    job_url = data.get('job_url')
    if not job_description and not job_url:
        return jsonify({"error": "Job description or URL is required"}), 400
    recommendations = recommend_assessments(job_description=job_description, job_url=job_url, top_n=10)
    if recommendations:
        json_output = {
            "recommended_assessments": [
                {
                    "url": rec["url"],
                    "adaptive_support": rec["adaptive_support"],
                    "description": rec["description"],
                    "duration": int(rec["duration"].split()[0]) if isinstance(rec["duration"], str) and "minutes" in rec["duration"] else (int(rec["duration"]) if rec["duration"].isdigit() else 0),
                    "remote_support": rec["remote_support"],
                    "test_type": [rec["test_type"]] if not isinstance(rec["test_type"], list) else rec["test_type"]
                } for rec in recommendations
            ]
        }
        return jsonify(json_output)
    return jsonify({"error": "No recommendations found"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
