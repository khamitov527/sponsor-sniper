from flask import Flask, jsonify, request
from flask_cors import CORS
from youtube_transcript_api import YouTubeTranscriptApi
from sponsor_classifier import SponsorClassifier
import logging

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Set up logging
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize the sponsor classifier
classifier = SponsorClassifier()

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
        threshold: Optional - Probability threshold for classifying as sponsor (default: 0.7)
    """
    video_id = request.args.get('v')
    if not video_id:
        return jsonify({"detail": "Video ID (v) is required"}), 400
    
    # Get threshold parameter (default to 0.7 if not provided)
    try:
        threshold = float(request.args.get('threshold', 0.7))
        # Ensure threshold is between 0 and 1
        threshold = max(0.0, min(1.0, threshold))
        logger.info(f"Using threshold: {threshold}")
    except ValueError:
        threshold = 0.7
        logger.warning(f"Invalid threshold provided, using default: {threshold}")
    
    try:
        # Fetch transcript for the video
        logger.info(f"Fetching transcript for video: {video_id}")
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        logger.info(f"Transcript length: {len(transcript_list)} segments")
        
        # Classify sponsor segments using our ML classifier
        logger.info(f"Classifying sponsor segments with threshold: {threshold}")
        sponsor_segments = classifier.classify_segments(transcript_list, threshold=threshold)
        logger.info(f"Found {len(sponsor_segments)} sponsor segments")
        
        # Print the segments for debugging
        for i, segment in enumerate(sponsor_segments):
            start = segment["startTime"]
            end = segment["endTime"]
            logger.info(f"Segment {i+1}: {start:.1f}s - {end:.1f}s (duration: {end-start:.1f}s)")
        
        return jsonify({
            "video_id": video_id,
            "sponsors": sponsor_segments,
            "threshold": threshold,
            "success": True
        })
    except Exception as e:
        logger.error(f"Error processing video {video_id}: {str(e)}")
        return jsonify({
            "video_id": video_id,
            "error": str(e),
            "sponsors": [],
            "success": False
        }), 400

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
        logger.info(f"Fetching transcript for video: {video_id}")
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        logger.info(f"Transcript length: {len(transcript_list)} segments")
        
        return jsonify({
            "video_id": video_id,
            "transcript": transcript_list,
            "success": True
        })
    except Exception as e:
        logger.error(f"Error fetching transcript for video {video_id}: {str(e)}")
        return jsonify({
            "video_id": video_id,
            "error": str(e),
            "success": False
        }), 400

if __name__ == "__main__":
    logger.info("Starting Sponsor Sniper backend server")
    app.run(host="0.0.0.0", port=8000, debug=True) 