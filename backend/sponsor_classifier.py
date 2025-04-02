import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import numpy as np
from typing import List, Dict, Any, Tuple

class SponsorClassifier:
    def __init__(self, model_name: str = "distilbert-base-uncased"):
        """
        Initialize the sponsor classifier.
        
        Args:
            model_name: Name of the pretrained model to use from Hugging Face.
        """
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
        
        # Placeholder for model predictions (using heuristics for now)
        # TODO: Replace with actual model predictions once fine-tuned model is available
        sponsor_probabilities = [self._heuristic_classification(text) for text, _, _ in processed_segments]
        
        # Log the number of segments with probabilities above different thresholds
        above_zero = sum(1 for p in sponsor_probabilities if p > 0)
        above_threshold = sum(1 for p in sponsor_probabilities if p >= threshold)
        print(f"Found {above_zero} segments with probability > 0")
        print(f"Found {above_threshold} segments with probability >= {threshold}")
        
        # Debug: print all segments with probability > 0
        for i, ((text, start, end), prob) in enumerate(zip(processed_segments, sponsor_probabilities)):
            if prob > 0:
                print(f"Debug - Segment {i} ({start:.1f}s - {end:.1f}s): {prob:.2f} probability")
                print(f"Text snippet: {text[:50]}...")
        
        # Identify sponsor segments based on threshold
        sponsor_segments = []
        in_sponsor = False
        current_start = 0
        
        for i, ((_, start_time, end_time), prob) in enumerate(zip(processed_segments, sponsor_probabilities)):
            is_sponsor = prob >= threshold
            
            if is_sponsor and not in_sponsor:
                # Start of a new sponsor segment
                in_sponsor = True
                current_start = start_time
            elif not is_sponsor and in_sponsor:
                # End of a sponsor segment
                in_sponsor = False
                sponsor_segments.append({
                    "startTime": current_start,
                    "endTime": end_time
                })
                
        # If we're still in a sponsor segment at the end
        if in_sponsor:
            sponsor_segments.append({
                "startTime": current_start,
                "endTime": processed_segments[-1][2]
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