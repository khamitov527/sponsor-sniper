"""
Test script for the DeepSeek API integration in sponsor detection.
This script demonstrates how to use the DeepSeek API to identify sponsor segments in a YouTube video.
"""

import os
import json
import datetime
from dotenv import load_dotenv
from sponsor_classifier import SponsorClassifier
from youtube_transcript_api import YouTubeTranscriptApi

def test_deepseek_detection(video_id, threshold=0.3, verbose=True):
    """Test the DeepSeek API integration for sponsor detection in a specific video."""
    
    # Load environment variables (including DeepSeek API key)
    load_dotenv()
    
    # Check if DeepSeek API key is set
    api_key = os.getenv('DEEPSEEK_API_KEY')
    if not api_key:
        print("WARNING: DeepSeek API key not found in .env file")
        print("The system will fall back to heuristic classification.")
    else:
        print(f"DeepSeek API key found. Will use DeepSeek API for classification.")
    
    try:
        print(f"Testing sponsor detection for video: {video_id}")
        
        # Initialize the classifier
        classifier = SponsorClassifier()
            
        # Get the transcript
        print(f"Fetching transcript for video: {video_id}")
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        print(f"Transcript length: {len(transcript_list)} segments")
        
        # Process the transcript into windows
        processed_segments = classifier._preprocess_transcript(transcript_list)
        print(f"Processed into {len(processed_segments)} windows")
        
        # Test a small sample first if the transcript is very large
        if len(processed_segments) > 100 and not verbose:
            print("Testing on a sample of 100 segments for faster results...")
            test_segments = processed_segments[:100]
        else:
            test_segments = processed_segments
        
        # Call DeepSeek API or fallback classification
        print("Calling classification...")
        segment_results = classifier._deepseek_classification(test_segments)
        
        # Create a log file with timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"logs/sponsors_{video_id}_{timestamp}.txt"
        
        # Ensure logs directory exists
        os.makedirs("logs", exist_ok=True)
        
        # Open log file
        with open(log_filename, 'w') as log_file:
            log_file.write(f"Sponsor Detection Log for Video ID: {video_id}\n")
            log_file.write(f"Timestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            log_file.write(f"Using threshold: {threshold}\n\n")
            
            # Log transcript info
            log_file.write("Fetching transcript...\n")
            log_file.write(f"Transcript length: {len(transcript_list)} segments\n\n")
            
            # Log segments with non-zero probability
            log_file.write("Segments with non-zero probability of being sponsors:\n")
            log_file.write("-" * 80 + "\n")
            
            found_sponsors = False
            for i, start, end, text, prob in segment_results:
                if prob > 0:
                    found_sponsors = True
                    log_file.write(f"Segment {i} ({start:.1f}s - {end:.1f}s): {prob:.2f} probability\n")
                    log_file.write(f"Text: {text[:100]}...\n")
                    log_file.write("-" * 80 + "\n")
                    
                    # Also print to console if verbose
                    if verbose:
                        print(f"Segment {i} ({start:.1f}s - {end:.1f}s): {prob:.2f} probability")
                        print(f"Text: {text[:100]}...")
                        print("-" * 80)
                
            if not found_sponsors:
                log_file.write("No sponsor segments found in the analyzed portion.\n")
                if verbose:
                    print("No sponsor segments found in the analyzed portion.")
        
        # Get the full sponsor segments
        print(f"\nClassifying full transcript with threshold: {threshold}")
        sponsor_segments = classifier.classify_segments(transcript_list, threshold=threshold)
        
        # Append sponsor segments to log file
        with open(log_filename, 'a') as log_file:
            log_file.write(f"\nDetected {len(sponsor_segments)} sponsor segments:\n")
            for i, segment in enumerate(sponsor_segments):
                start = segment["startTime"]
                end = segment["endTime"]
                duration = end - start
                log_file.write(f"Segment {i+1}: {start:.1f}s - {end:.1f}s (duration: {duration:.1f}s)\n")
                
                # Find matching text from processed segments
                matching_segments = [
                    (seg_text, seg_prob) 
                    for seg_i, seg_start, seg_end, seg_text, seg_prob in segment_results
                    if seg_start >= start - 1 and seg_end <= end + 1 and seg_prob >= threshold
                ]
                
                if matching_segments:
                    log_file.write("Detected sponsor keywords in:\n")
                    for text, prob in matching_segments[:3]:  # Show up to 3 matching segments
                        log_file.write(f"  - '{text[:100]}...' (probability: {prob:.2f})\n")
                log_file.write("\n")
        
        # Print the sponsor segments to console
        print(f"\nDetected {len(sponsor_segments)} sponsor segments:")
        for i, segment in enumerate(sponsor_segments):
            start = segment["startTime"]
            end = segment["endTime"]
            print(f"* {start:.1f}s - {end:.1f}s (duration: {end-start:.1f}s)")
        
        if not sponsor_segments:
            print("No sponsor segments detected.")
            
        print(f"\nLog file created: {log_filename}")
        return sponsor_segments
        
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    import sys
    
    # Parse command line arguments
    if len(sys.argv) < 2:
        print("Usage: python3 test_deepseek.py VIDEO_ID [threshold]")
        print("Example: python3 test_deepseek.py dQw4w9WgXcQ 0.3")
        sys.exit(1)
        
    video_id = sys.argv[1]
    threshold = float(sys.argv[2]) if len(sys.argv) > 2 else 0.3
    
    # Run the test
    test_deepseek_detection(video_id, threshold) 