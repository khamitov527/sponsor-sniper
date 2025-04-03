import os
import requests
import json
from typing import List, Dict, Any, Tuple
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class SponsorClassifier:
    def __init__(self):
        """
        Initialize the sponsor classifier.
        """
        # Get DeepSeek API key from environment variables
        self.deepseek_api_key = os.getenv('DEEPSEEK_API_KEY')
        self.deepseek_api_url = "https://api.deepseek.com/v1/chat/completions"
        
        # If no DeepSeek API key is available, fall back to heuristic methods
        self.use_deepseek = self.deepseek_api_key is not None
        
        if not self.use_deepseek:
            print("WARNING: No DeepSeek API key found. Falling back to heuristic classification.")
        
        # Keyword list for heuristic fallback approach
        self.sponsor_keywords = [
            "sponsor", "sponsored", "sponsorship", "promotion", "promo code", 
            "discount", "offer", "check out", "link in description", "link below",
            "use code", "coupon", "deal", "limited time", "special offer", 
            "today's video is brought to you by", "thanks to", "brought to you by"
        ]
    
    def _preprocess_transcript(self, transcript: List[Dict[Any, Any]], window_size: int = 5) -> List[Tuple[str, float, float]]:
        """
        Preprocess transcript by creating overlapping windows of text segments.
        
        Args:
            transcript: List of transcript segments from YouTube API
            window_size: Number of segments to combine into a window
            
        Returns:
            List of tuples (text, start_time, end_time)
        """
        processed_segments = []
        
        # Make sure we have enough segments
        if len(transcript) < window_size:
            window_size = len(transcript)
            
        for i in range(len(transcript) - window_size + 1):
            window = transcript[i:i+window_size]
            
            # Combine text from all segments in the window
            text = " ".join([segment["text"] for segment in window])
            
            # Get start time from first segment and end time from last segment
            start_time = window[0]["start"]
            end_time = window[-1]["start"] + window[-1]["duration"]
            
            processed_segments.append((text, start_time, end_time))
            
        return processed_segments
    
    def _heuristic_classification(self, text: str) -> float:
        """
        Use keyword-based heuristics to classify sponsor content.
        
        Args:
            text: Text to classify
            
        Returns:
            Probability of being sponsor content (0-1)
        """
        text = text.lower()
        
        # Count the number of sponsor keywords in the text
        keyword_count = sum(1 for keyword in self.sponsor_keywords if keyword.lower() in text)
        
        # Simple probability based on keyword density
        return min(1.0, keyword_count / 3)  # Cap at 1.0
    
    def _deepseek_classification(self, transcript_segments: List[Tuple[str, float, float]]) -> List[Tuple[int, float, float, str, float]]:
        """
        Use DeepSeek API to classify sponsor segments in a transcript.
        
        Args:
            transcript_segments: List of processed transcript segments (text, start_time, end_time)
            
        Returns:
            List of tuples (segment_index, start_time, end_time, text, probability)
        """
        if not self.use_deepseek:
            # Fall back to heuristic classification
            return [(i, start, end, text, self._heuristic_classification(text)) 
                    for i, (text, start, end) in enumerate(transcript_segments)]
        
        # Create a formatted prompt with transcript segments and timestamps
        transcript_text = "\n".join([
            f"[{start:.1f}s - {end:.1f}s]: {text}"
            for text, start, end in transcript_segments
        ])
        
        # Prepare the prompt for DeepSeek API
        prompt = f"""You are an expert at identifying sponsored content in YouTube videos.
        
Below is a transcript from a YouTube video with timestamps. Your task is to:
1. Identify segments that contain sponsored content
2. For each segment, provide a confidence score between 0 and 1
3. Return ONLY the segments that are likely to be sponsored (score > 0)

Sponsored content typically includes:
- Explicit mentions of sponsors or partnerships
- Product promotions or endorsements
- Discount codes or special offers
- Links or calls to action to visit specific websites

Transcript:
{transcript_text}

For each segment that might contain sponsored content, return it in this format:
{{
  "segment_index": [index],
  "start_time": [start time in seconds],
  "end_time": [end time in seconds],
  "probability": [confidence score between 0 and 1],
  "text": [text content]
}}

Return your answer as a valid JSON list of sponsor segments.
"""
        
        try:
            # Call DeepSeek API
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.deepseek_api_key}"
            }
            
            payload = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": "You are an AI assistant specializing in identifying sponsored content in videos."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1,  # Low temperature for more consistent results
                "max_tokens": 4000
            }
            
            response = requests.post(self.deepseek_api_url, headers=headers, json=payload)
            response.raise_for_status()
            
            # Extract the response text
            result = response.json()
            response_text = result["choices"][0]["message"]["content"]
            
            # Parse the JSON response
            try:
                # Extract JSON from the response (it might be surrounded by markdown code blocks)
                json_text = response_text
                if "```json" in response_text:
                    json_text = response_text.split("```json")[1].split("```")[0].strip()
                elif "```" in response_text:
                    json_text = response_text.split("```")[1].split("```")[0].strip()
                
                sponsor_segments = json.loads(json_text)
                
                # Convert to our format
                result_segments = []
                for segment in sponsor_segments:
                    seg_index = segment.get("segment_index", 0)
                    start_time = segment.get("start_time", 0)
                    end_time = segment.get("end_time", 0)
                    probability = segment.get("probability", 0)
                    text = segment.get("text", "")
                    
                    result_segments.append((seg_index, start_time, end_time, text, probability))
                
                return result_segments
                
            except json.JSONDecodeError as e:
                print(f"Error parsing DeepSeek response: {e}")
                print(f"Response text: {response_text}")
                # Fall back to heuristic classification
                return [(i, start, end, text, self._heuristic_classification(text)) 
                        for i, (text, start, end) in enumerate(transcript_segments)]
                
        except Exception as e:
            print(f"Error calling DeepSeek API: {e}")
            # Fall back to heuristic classification
            return [(i, start, end, text, self._heuristic_classification(text)) 
                    for i, (text, start, end) in enumerate(transcript_segments)]
    
    def classify_segments(self, transcript: List[Dict[Any, Any]], threshold: float = 0.7) -> List[Dict[str, Any]]:
        """
        Classify transcript segments as sponsor content or not.
        
        Args:
            transcript: List of transcript segments from YouTube API
            threshold: Probability threshold for classifying as sponsor
            
        Returns:
            List of sponsor segments with start and end times
        """
        print(f"Classifying segments with threshold: {threshold}")
        
        if not transcript:
            print("Empty transcript")
            return []
            
        # Preprocess transcript into windows
        processed_segments = self._preprocess_transcript(transcript)
        
        # Use DeepSeek for classification if available, otherwise fall back to heuristics
        if self.use_deepseek:
            print("Using DeepSeek API for classification")
            segment_results = self._deepseek_classification(processed_segments)
            # Extract probabilities from the results
            sponsor_probabilities = [prob for _, _, _, _, prob in segment_results]
            # Use the segment results with index, start, end, text, probability
            segment_probs = [(i, start, end, text, prob) for i, start, end, text, prob in segment_results]
        else:
            print("Using heuristic classification")
            # Fallback to heuristic classification
            sponsor_probabilities = [self._heuristic_classification(text) for text, _, _ in processed_segments]
            segment_probs = [(i, start, end, text, self._heuristic_classification(text)) 
                           for i, (text, start, end) in enumerate(processed_segments)]
        
        # Log the number of segments with probabilities above different thresholds
        above_zero = sum(1 for p in sponsor_probabilities if p > 0)
        above_threshold = sum(1 for p in sponsor_probabilities if p >= threshold)
        print(f"Found {above_zero} segments with probability > 0")
        print(f"Found {above_threshold} segments with probability >= {threshold}")
        
        # Debug: print all segments with probability > 0
        for i, start, end, text, prob in segment_probs:
            if prob > 0:
                print(f"Debug - Segment {i} ({start:.1f}s - {end:.1f}s): {prob:.2f} probability")
                print(f"Text snippet: {text[:50]}...")
        
        # Identify sponsor segments based on threshold
        sponsor_segments = []
        in_sponsor = False
        current_start = 0
        
        # Sort by start time to handle any non-sequential results (especially from DeepSeek)
        sorted_probs = sorted(segment_probs, key=lambda x: x[1])
        
        for i, (_, start, end, _, prob) in enumerate(sorted_probs):
            # Start a new sponsor segment
            if prob >= threshold and not in_sponsor:
                in_sponsor = True
                current_start = start
            
            # End the current sponsor segment if probability drops below threshold
            # or if there's a significant gap (more than 10 seconds)
            elif in_sponsor and (prob < threshold or (i > 0 and start - sorted_probs[i-1][2] > 10)):
                sponsor_segments.append({
                    "startTime": current_start,
                    "endTime": sorted_probs[i-1][2]  # End time of previous segment
                })
                in_sponsor = False
        
        # Add the last segment if we're still in a sponsor segment
        if in_sponsor:
            sponsor_segments.append({
                "startTime": current_start,
                "endTime": sorted_probs[-1][2]  # End time of last segment
            })
        
        # Merge overlapping segments
        if sponsor_segments:
            merged_segments = [sponsor_segments[0]]
            
            for segment in sponsor_segments[1:]:
                prev = merged_segments[-1]
                
                # If current segment overlaps with previous, merge them
                if segment["startTime"] <= prev["endTime"] + 5:  # 5 second tolerance for gaps
                    prev["endTime"] = max(prev["endTime"], segment["endTime"])
                else:
                    merged_segments.append(segment)
            
            sponsor_segments = merged_segments
        
        return sponsor_segments 