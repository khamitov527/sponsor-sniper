"""
Script to analyze sponsor segments in a YouTube video with detailed logging.
"""

from sponsor_classifier import SponsorClassifier
from youtube_transcript_api import YouTubeTranscriptApi
import sys
import json

def analyze_video(video_id, threshold=0.3, verbose=True):
    """Analyze a YouTube video for sponsor segments with detailed logging."""
    print(f"Analyzing video: {video_id} with threshold: {threshold}")
    
    try:
        # Get the transcript
        print(f"Fetching transcript for video: {video_id}")
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        print(f"Transcript length: {len(transcript)} segments")
        
        # Initialize the classifier
        classifier = SponsorClassifier()
        
        # Process the transcript
        processed_segments = classifier._preprocess_transcript(transcript)
        
        # Get sponsor probabilities for each segment
        segment_probs = []
        for i, (text, start, end) in enumerate(processed_segments):
            prob = classifier._heuristic_classification(text)
            segment_probs.append((i, start, end, text, prob))
        
        # Display segments with probabilities above 0
        if verbose:
            print("\nSegments with non-zero probability:")
            for i, start, end, text, prob in segment_probs:
                if prob > 0:
                    print(f"Segment {i} ({start:.1f}s - {end:.1f}s): {prob:.2f} probability")
                    print(f"Text: {text[:100]}...")
                    print("-" * 80)
        
        # Get sponsor segments
        sponsor_segments = classifier.classify_segments(transcript, threshold=threshold)
        
        # Display sponsor segments
        print(f"\nDetected {len(sponsor_segments)} sponsor segments:")
        
        if verbose:
            for i, segment in enumerate(sponsor_segments):
                start = segment["startTime"]
                end = segment["endTime"]
                duration = end - start
                print(f"Segment {i+1}: {start:.1f}s - {end:.1f}s (duration: {duration:.1f}s)")
                
                # Find original text from processed segments
                matching_segments = [
                    (seg_text, seg_prob) 
                    for seg_i, seg_start, seg_end, seg_text, seg_prob in segment_probs
                    if seg_start >= start - 1 and seg_end <= end + 1 and seg_prob >= threshold
                ]
                
                if matching_segments:
                    print("Detected sponsor keywords in:")
                    for text, prob in matching_segments[:3]:  # Show up to 3 matching segments
                        print(f"  - '{text[:100]}...' (probability: {prob:.2f})")
                print()
        
        return sponsor_segments
        
    except Exception as e:
        print(f"Error analyzing video: {e}")
        return []

if __name__ == "__main__":
    video_id = "hCyvqRq5YmM"  # Default to the Huberman Lab podcast video
    
    if len(sys.argv) > 1:
        video_id = sys.argv[1]
    
    threshold = 0.3
    if len(sys.argv) > 2:
        threshold = float(sys.argv[2])
    
    sponsor_segments = analyze_video(video_id, threshold)
    print(f"Summary: Found {len(sponsor_segments)} sponsor segments in video {video_id}")
    
    # Output in JSON format for potential use
    json_output = {
        "video_id": video_id,
        "threshold": threshold,
        "sponsors": sponsor_segments
    }
    
    with open(f"sponsors_{video_id}.json", "w") as f:
        json.dump(json_output, f, indent=2)
    
    print(f"Results saved to sponsors_{video_id}.json") 