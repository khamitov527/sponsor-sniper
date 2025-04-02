"""
Direct test script for the sponsor classifier.
This will test the classifier directly on a specific video.
"""

from sponsor_classifier import SponsorClassifier
from youtube_transcript_api import YouTubeTranscriptApi

def main():
    # Test configuration
    video_id = "JHjhw8Ek3Zk"
    threshold = 0.3
    
    # Initialize the classifier
    classifier = SponsorClassifier()
    
    # Get the transcript
    print(f"Fetching transcript for video: {video_id}")
    transcript = YouTubeTranscriptApi.get_transcript(video_id)
    print(f"Transcript length: {len(transcript)} segments")
    
    # Test threshold values
    for test_threshold in [0.3, 0.5, 0.7]:
        print(f"\n--- Testing threshold: {test_threshold} ---")
        segments = classifier.classify_segments(transcript, threshold=test_threshold)
        print(f"Found {len(segments)} sponsor segments at threshold {test_threshold}")
        
        # Print the segments
        for i, segment in enumerate(segments):
            start = segment["startTime"]
            end = segment["endTime"]
            print(f"Segment {i+1}: {start:.1f}s - {end:.1f}s (duration: {end-start:.1f}s)")

if __name__ == "__main__":
    main() 