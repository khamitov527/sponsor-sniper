import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import numpy as np
from typing import List, Dict, Any, Tuple
import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class SponsorClassifier:
    def __init__(self, model_name: str = "distilbert-base-uncased"):
        """
        Initialize the sponsor classifier.
        
        Args:
            model_name: Name of the pretrained model to use from Hugging Face.
        """
        # Get DeepSeek API key from environment variables
        self.deepseek_api_key = os.getenv('DEEPSEEK_API_KEY')
        self.deepseek_api_url = "https://api.deepseek.com/v1/chat/completions"
        
        # If no DeepSeek API key is available, fall back to ML methods
        self.use_deepseek = self.deepseek_api_key is not None
        
        if not self.use_deepseek:
            print("WARNING: No DeepSeek API key found. Falling back to heuristic classification.")
            # ML model initialization (commented out but kept for fallback)
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=2)
            self.model.to(self.device)
            
            # Set model to evaluation mode
            self.model.eval()
        
        # If no fine-tuned model is available, we'll use a simple heuristic approach
        # as a fallback until the model is properly trained
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
        # This is a very basic heuristic and should be replaced with ML model predictions
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
        
        # Only use the segments with probabilities above threshold for merging
        filtered_segments = [(i, start, end) for i, start, end, _, prob in segment_probs if prob >= threshold]
        
        if not filtered_segments:
            return []
            
        # Sort by start time
        filtered_segments.sort(key=lambda x: x[1])
        
        # Merge nearby segments (within 20 seconds of each other)
        merged_segments = []
        current_segment = filtered_segments[0]
        
        for i, start, end in filtered_segments[1:]:
            _, prev_start, prev_end = current_segment
            
            # If this segment starts within 20 seconds of the previous segment ending
            if start - prev_end <= 20:
                # Merge the segments
                current_segment = (current_segment[0], prev_start, end)
            else:
                # Add the current segment to the merged list and start a new one
                merged_segments.append(current_segment)
                current_segment = (i, start, end)
                
        # Add the last segment
        merged_segments.append(current_segment)
        
        # Convert to required format
        for _, start, end in merged_segments:
            sponsor_segments.append({
                "startTime": start,
                "endTime": end
            })
        
        print(f"Returning {len(sponsor_segments)} sponsor segments")
        return sponsor_segments
        
    def fine_tune_model(self, training_data):
        """
        Fine-tune the model on sponsor detection data.
        
        NOTE: This is a placeholder method. Actual implementation would depend on
        having a labeled dataset of sponsor segments.
        """
        # TODO: Implement fine-tuning when labeled data is available
        pass 