from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/ping', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "ok"})

@app.route('/sponsors', methods=['GET'])
def get_sponsors():
    """
    Get sponsors for a specific YouTube video.
    
    Query Parameters:
        v: YouTube video ID
    """
    video_id = request.args.get('v')
    if not video_id:
        return jsonify({"detail": "Video ID (v) is required"}), 400
    
    # Placeholder: This is where you'll implement the actual sponsor retrieval logic
    return jsonify({"video_id": video_id, "sponsors": []})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True) 