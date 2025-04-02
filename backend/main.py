from flask import Flask, jsonify, request
from flask_cors import CORS
from youtube_transcript_api import YouTubeTranscriptApi

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

@app.route('/transcript', methods=['GET'])
def get_transcript():
    """
    Get transcript for a specific YouTube video.
    
    Query Parameters:
        v: YouTube video ID
    """
    video_id = request.args.get('v')
    if not video_id:
        return jsonify({"detail": "Video ID (v) is required"}), 400
    
    try:
        # Fetch transcript for the video
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        
        return jsonify({
            "video_id": video_id,
            "transcript": transcript_list,
            "success": True
        })
    except Exception as e:
        return jsonify({
            "video_id": video_id,
            "error": str(e),
            "success": False
        }), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True) 