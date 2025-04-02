"""
Test script for the sponsor classifier.
This will test specific segments from the transcript of a given video.
"""

from sponsor_classifier import SponsorClassifier
from youtube_transcript_api import YouTubeTranscriptApi
import json
import sys

def test_classifier_on_video(video_id, window_size=5, threshold=0.3):
    """Test the classifier on a specific video."""
    try:
        # Initialize the classifier
        classifier = SponsorClassifier()
        
        # Get the transcript
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        
        # Process the transcript into windows
        processed_segments = classifier._preprocess_transcript(transcript, window_size)
        
        # Calculate the probability for each segment
        for i, (text, start, end) in enumerate(processed_segments):
            prob = classifier._heuristic_classification(text)
            if prob > 0.0:  # Only show segments with some probability of being a sponsor
                print(f"Segment {i} ({start:.1f}s - {end:.1f}s): {prob:.2f} probability")
                print(f"Text: {text}")
                print("-" * 80)
        
        # Get the sponsor segments using the classifier with a lower threshold
        sponsor_segments = classifier.classify_segments(transcript, threshold=threshold)
        
        # Print the sponsor segments
        print("\nDetected sponsor segments (threshold = {:.1f}):".format(threshold))
        for segment in sponsor_segments:
            start = segment["startTime"]
            end = segment["endTime"]
            print(f"* {start:.1f}s - {end:.1f}s (duration: {end-start:.1f}s)")
        
        if not sponsor_segments:
            print("No sponsor segments detected.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        video_id = sys.argv[1]
    else:
        video_id = "JHjhw8Ek3Zk"  # Default video ID
    
    # Use a lower threshold to detect potential sponsor content
    threshold = 0.3
    
    print(f"Testing classifier on video: {video_id}")
    test_classifier_on_video(video_id, threshold=threshold) 