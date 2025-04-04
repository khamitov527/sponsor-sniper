from flask import Flask, jsonify, request
from flask_cors import CORS
from youtube_transcript_api import YouTubeTranscriptApi
import logging
import json
import os
import sys
from datetime import datetime
from functools import wraps

app = Flask(__name__)
# Enable CORS with more permissive configuration for Chrome extensions
CORS(app, origins=["*"], allow_headers=["*"], supports_credentials=True)

# Add CORS headers to all responses
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET,PUT,POST,DELETE,OPTIONS'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    return response

# Set up logging
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

# Check for sponsor_classifier.py and import appropriately
try:
    from sponsor_classifier import SponsorClassifier
    classifier = SponsorClassifier()
    logger.info("Sponsor classifier loaded successfully")
except ImportError:
    logger.error("Failed to import SponsorClassifier, some endpoints may not work")
    classifier = None

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
    
    # Log request details
    logger.info(f"Sponsor detection request received. URL: {request.url}")
    logger.info(f"Client IP: {request.remote_addr}, User Agent: {request.headers.get('User-Agent', 'Unknown')}")
    
    if not video_id:
        logger.error("No video ID provided in request")
        return jsonify({"detail": "Video ID (v) is required", "success": False}), 400
    
    # Get threshold parameter (default to 0.3 if not provided)
    try:
        threshold = float(request.args.get('threshold', 0.3))
        # Ensure threshold is between 0 and 1
        threshold = max(0.0, min(1.0, threshold))
        logger.info(f"Using threshold: {threshold}")
    except ValueError as e:
        threshold = 0.3
        logger.warning(f"Invalid threshold provided ({request.args.get('threshold')}), using default: {threshold}. Error: {str(e)}")
    
    try:
        # Check if classifier is available
        if not classifier:
            raise Exception("Sponsor classifier not available")
        
        # Fetch transcript for the video
        logger.info(f"Fetching transcript for video: {video_id}")
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        logger.info(f"Transcript length: {len(transcript_list)} segments")
        
        # Classify sponsor segments using DeepSeek API or heuristic fallback
        logger.info(f"Classifying sponsor segments with threshold: {threshold}")
        sponsor_segments = classifier.classify_segments(transcript_list, threshold=threshold)
        logger.info(f"Found {len(sponsor_segments)} sponsor segments")
        
        # Print the segments for debugging
        for i, segment in enumerate(sponsor_segments):
            start = segment["startTime"]
            end = segment["endTime"]
            logger.info(f"Segment {i+1}: {start:.1f}s - {end:.1f}s (duration: {end-start:.1f}s)")
        
        # Create response
        response = {
            "video_id": video_id,
            "sponsors": sponsor_segments,
            "threshold": threshold,
            "success": True
        }
        
        logger.info(f"Returning response with {len(sponsor_segments)} segments")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error processing video {video_id}: {str(e)}", exc_info=True)
        return jsonify({
            "video_id": video_id,
            "error": str(e),
            "sponsors": [],
            "success": False
        }), 400

@app.route('/sponsors_log', methods=['GET'])
def get_sponsors_with_log():
    """
    Get sponsors for a specific YouTube video and create a detailed log file.
    
    Query Parameters:
        v: YouTube video ID
        threshold: Optional - Probability threshold for classifying as sponsor (default: 0.3)
        include_transcript: Optional - Whether to include full transcript in log (1 for yes, 0 for no, default: 1)
    """
    video_id = request.args.get('v')
    if not video_id:
        return jsonify({"detail": "Video ID (v) is required"}), 400
    
    # Get threshold parameter (default to 0.3 if not provided)
    try:
        threshold = float(request.args.get('threshold', 0.3))
        # Ensure threshold is between 0 and 1
        threshold = max(0.0, min(1.0, threshold))
        logger.info(f"Using threshold: {threshold}")
    except ValueError:
        threshold = 0.3
        logger.warning(f"Invalid threshold provided, using default: {threshold}")
    
    # Get include_transcript parameter (default to True)
    include_transcript = request.args.get('include_transcript', '1') == '1'
    logger.info(f"Include transcript in log: {include_transcript}")
    
    try:
        # Create a log file with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"logs/sponsors_{video_id}_{timestamp}.txt"
        
        # Open log file
        with open(log_filename, 'w') as log_file:
            log_file.write(f"Sponsor Detection Log for Video ID: {video_id}\n")
            log_file.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            log_file.write(f"Using threshold: {threshold}\n\n")
            
            # Fetch transcript for the video
            log_file.write("Fetching transcript...\n")
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            log_file.write(f"Transcript length: {len(transcript_list)} segments\n\n")
            
            # Include full transcript if requested
            if include_transcript:
                log_file.write("== FULL TRANSCRIPT ==\n")
                log_file.write("-" * 80 + "\n\n")
                
                # Sort transcript by start time
                sorted_transcript = sorted(transcript_list, key=lambda x: x['start'])
                
                for i, segment in enumerate(sorted_transcript):
                    start_time = segment['start']
                    duration = segment['duration']
                    end_time = start_time + duration
                    text = segment['text']
                    
                    timestamp_str = f"[{start_time:.1f}s - {end_time:.1f}s]"
                    log_file.write(f"{timestamp_str}: {text}\n")
                
                log_file.write("\n" + "-" * 80 + "\n\n")
            
            # Process transcript and get segments with probabilities
            processed_segments = classifier._preprocess_transcript(transcript_list)
            
            # Calculate probabilities for each segment
            log_file.write("Segments with non-zero probability of being sponsors:\n")
            log_file.write("-" * 80 + "\n")
            
            # Get segment probabilities (either from DeepSeek or fallback)
            segment_results = classifier._deepseek_classification(processed_segments)
            segment_probs = [(i, start, end, text, prob) for i, start, end, text, prob in segment_results]
                
            # Log segments with non-zero probability
            found_sponsors = False
            for i, start, end, text, prob in segment_probs:
                if prob > 0:
                    found_sponsors = True
                    log_file.write(f"Segment {i} ({start:.1f}s - {end:.1f}s): {prob:.2f} probability\n")
                    log_file.write(f"Text: {text[:100]}...\n")
                    log_file.write("-" * 80 + "\n")
            
            if not found_sponsors:
                log_file.write("No sponsor segments found in the analyzed portion.\n")
            
            # Classify sponsor segments
            log_file.write("\nClassifying segments with threshold: {:.1f}\n".format(threshold))
            sponsor_segments = classifier.classify_segments(transcript_list, threshold=threshold)
            
            # Write results to log
            log_file.write(f"\nDetected {len(sponsor_segments)} sponsor segments:\n")
            
            for i, segment in enumerate(sponsor_segments):
                start = segment["startTime"]
                end = segment["endTime"]
                duration = end - start
                log_file.write(f"Segment {i+1}: {start:.1f}s - {end:.1f}s (duration: {duration:.1f}s)\n")
                
                # Find matching text from processed segments
                matching_segments = [
                    (seg_text, seg_prob) 
                    for seg_i, seg_start, seg_end, seg_text, seg_prob in segment_probs
                    if seg_start >= start - 1 and seg_end <= end + 1 and seg_prob >= threshold
                ]
                
                if matching_segments:
                    log_file.write("Detected sponsor keywords in:\n")
                    for text, prob in matching_segments[:3]:  # Show up to 3 matching segments
                        log_file.write(f"  - '{text[:100]}...' (probability: {prob:.2f})\n")
                log_file.write("\n")
                
        logger.info(f"Log file created: {log_filename}")
        logger.info(f"Full transcript included in log: {include_transcript}")
        
        return jsonify({
            "video_id": video_id,
            "sponsors": sponsor_segments,
            "threshold": threshold,
            "log_file": log_filename,
            "include_transcript": include_transcript,
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
    import sys
    
    # Check for --test flag
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        logger.info("Running in test mode. Checking setup...")
        try:
            # Output setup info
            deepseek_key = os.getenv('DEEPSEEK_API_KEY')
            if deepseek_key:
                logger.info("DeepSeek API key is configured.")
            else:
                logger.warning("No DeepSeek API key found. Will use fallback mechanism.")
            
            # Check if we can import all required modules
            required_modules = ["flask", "flask_cors", "youtube_transcript_api"]
            missing_modules = []
            for module in required_modules:
                try:
                    __import__(module)
                except ImportError:
                    missing_modules.append(module)
            
            if missing_modules:
                logger.error(f"Missing required modules: {', '.join(missing_modules)}")
                logger.error("Please install with: pip install -r requirements.txt")
                sys.exit(1)
            else:
                logger.info("All required modules are installed.")
                logger.info("Setup looks good! You can start the server normally with: python main.py")
                sys.exit(0)
                
        except Exception as e:
            logger.error(f"Error during test: {e}")
            sys.exit(1)
    else:
        logger.info("Starting Sponsor Sniper backend server")
        app.run(host="0.0.0.0", port=8080, debug=True) 