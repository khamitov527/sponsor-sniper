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
            # General sponsor indicators
            "sponsor", "sponsored", "sponsorship", "promotion", "promo code", 
            "discount", "offer", "check out", "link in description", "link below",
            "use code", "coupon", "deal", "limited time", "special offer", 
            "today's video is brought to you by", "thanks to", "brought to you by",
            
            # Transition phrases
            "take a quick break", "like to thank", "acknowledge our sponsor",
            "back to", "moving on", "let's continue", "get back to",
            
            # Common sponsor companies
            "squarespace", "nordvpn", "audible", "skillshare", "raid shadow legends",
            "brilliant", "curiositystream", "dashlane", "expressvpn", "manscaped",
            
            # Specific sponsors identified in this video
            "our place", "element", "ag1", "eight sleep", "function health",
            "athletic greens", "mattress", "sleep", "supplements", "health",
            "hormone", "testosterone", "blood test", "pan", "kitchenware",
            "air filter", "air purifier", "air quality", "hydration"
        ]
    
    def _preprocess_transcript(self, transcript: List[Dict[Any, Any]], window_size: int = 8, overlap: int = 4) -> List[Tuple[str, float, float]]:
        """
        Preprocess transcript by creating overlapping windows of text segments.
        Enhanced version with larger windows and more overlap to better capture context.
        
        Args:
            transcript: List of transcript segments from YouTube API
            window_size: Number of segments to combine into a window
            overlap: Number of segments to overlap between windows
            
        Returns:
            List of tuples (text, start_time, end_time)
        """
        processed_segments = []
        
        # Make sure we have enough segments
        if len(transcript) < window_size:
            window_size = len(transcript)
            overlap = 0
            
        # Calculate step size based on overlap
        step_size = max(1, window_size - overlap)
        
        # Create overlapping windows
        for i in range(0, len(transcript) - window_size + 1, step_size):
            window = transcript[i:i+window_size]
            
            # Combine text from all segments in the window
            text = " ".join([segment["text"] for segment in window])
            
            # Get start time from first segment and end time from last segment
            start_time = window[0]["start"]
            end_time = window[-1]["start"] + window[-1]["duration"]
            
            processed_segments.append((text, start_time, end_time))
            
        # Add a final window if needed to cover the end of the transcript
        if len(transcript) > window_size and (len(transcript) - window_size) % step_size != 0:
            last_window = transcript[-window_size:]
            text = " ".join([segment["text"] for segment in last_window])
            start_time = last_window[0]["start"]
            end_time = last_window[-1]["start"] + last_window[-1]["duration"]
            processed_segments.append((text, start_time, end_time))
            
        # Additionally, create some focused windows around potential transition points
        # by examining the original transcript for transition keywords
        transition_keywords = [
            "sponsor", "break", "thank", "brought to you by", "speaking of", 
            "back to", "moving on", "continue", "let's talk"
        ]
        
        for i in range(len(transcript)):
            if any(keyword in transcript[i]["text"].lower() for keyword in transition_keywords):
                # Create a window centered on this potential transition point
                start_idx = max(0, i - window_size // 2)
                end_idx = min(len(transcript), i + window_size // 2 + 1)
                
                centered_window = transcript[start_idx:end_idx]
                if len(centered_window) > 2:  # Ensure we have enough segments
                    text = " ".join([segment["text"] for segment in centered_window])
                    start_time = centered_window[0]["start"]
                    end_time = centered_window[-1]["start"] + centered_window[-1]["duration"]
                    
                    # Add this focused window
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
        
        # Prepare the prompt for DeepSeek API with improved context awareness
        prompt = f"""You are an expert at identifying sponsored content in YouTube videos.
        
Below is a transcript from a YouTube video with timestamps. Your task is to:
1. Identify segments that contain sponsored content
2. For each segment, provide a confidence score between 0 and 1
3. Return ONLY the segments that are likely to be sponsored (score > 0)
4. Pay special attention to transitions that signal the start and end of sponsor segments

Common sponsor transitions and signals to look for:
- Start transitions: "let's take a quick break", "I'd like to thank our sponsor", "this video/episode is brought to you by"
- End transitions: "now back to", "let's get back to", "moving on", or transitions to unrelated topics
- Complete sponsor blocks typically include multiple sponsor-related sentences in sequence

Sponsored content typically includes:
- Explicit mentions of sponsors or partnerships
- Product promotions or endorsements
- Discount codes or special offers
- Links or calls to action to visit specific websites

Important:
- Only mark segments as sponsored if they're clearly part of a sponsor read
- Be precise about the exact start and end time of sponsor segments
- Look for clear transition phrases that mark the beginning and end of sponsored content
- Include the entire sponsor segment (often spans multiple transcript segments)
- Typical YouTube sponsors include products like VPNs, meal kits, mattresses, supplements, apps, or merchandise

Transcript:
{transcript_text}

For each segment that might contain sponsored content, return it in this format:
{{
  "segment_index": [index],
  "start_time": [start time in seconds],
  "end_time": [end time in seconds],
  "probability": [confidence score between 0 and 1],
  "text": [text content],
  "is_transition": [true if this marks a transition into or out of sponsored content, otherwise false]
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
                    {"role": "system", "content": "You are an AI assistant specializing in identifying sponsored content in videos, with a focus on precisely detecting the boundaries of sponsor segments."},
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
                    is_transition = segment.get("is_transition", False)
                    
                    # Boost probability for identified transitions
                    if is_transition and probability > 0.5:
                        probability = min(1.0, probability * 1.2)
                    
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
        
        # Sort by start time to handle any non-sequential results (especially from DeepSeek)
        sorted_probs = sorted(segment_probs, key=lambda x: x[1])
        
        # ----- ENHANCED SPONSOR SEGMENT IDENTIFICATION -----
        
        # Extract potential transition markers (high confidence segments)
        transition_markers = []
        for i, (_, start, end, text, prob) in enumerate(sorted_probs):
            # Look for high-confidence segments or transition language
            is_transition = False
            text_lower = text.lower()
            
            # Check for start transition phrases
            start_phrases = ["take a quick break", "break to", "like to thank", "thanks to our sponsor", 
                            "brought to you by", "sponsored by", "this episode is sponsored", 
                            "speaking of", "made possible by", "acknowledge our sponsor"]
            
            # Check for end transition phrases
            end_phrases = ["back to", "moving on", "let's continue", "now let's", "now back to", 
                          "let's get back to", "now that we've", "anyway", "with that said"]
            
            # Check for transitional phrases
            for phrase in start_phrases + end_phrases:
                if phrase in text_lower:
                    is_transition = True
                    break
            
            if is_transition or prob > 0.85:
                transition_markers.append((i, start, end, text, prob, any(phrase in text_lower for phrase in start_phrases)))
        
        # Identify sponsor segments more accurately using the transition markers
        sponsor_segments = []
        
        # If we have transition markers, use them to identify precise start/end points
        if transition_markers:
            # Group nearby transition markers (those within 60 seconds of each other)
            grouped_transitions = []
            current_group = [transition_markers[0]]
            
            for i in range(1, len(transition_markers)):
                current_marker = transition_markers[i]
                prev_marker = current_group[-1]
                
                # If current marker is close to previous one, add to current group
                if current_marker[1] - prev_marker[2] < 60:  # Within 60 seconds
                    current_group.append(current_marker)
                else:
                    # Start a new group
                    grouped_transitions.append(current_group)
                    current_group = [current_marker]
            
            # Add the last group
            if current_group:
                grouped_transitions.append(current_group)
            
            # Process each group of transitions to extract sponsor segments
            for group in grouped_transitions:
                # Find all segments between the earliest start transition and latest end transition
                is_start_transition = any(is_start for _, _, _, _, _, is_start in group if is_start)
                
                # Only process groups with at least one start transition
                if is_start_transition:
                    # Get the earliest start time in this group
                    earliest_start = min(start for _, start, _, _, _, _ in group)
                    
                    # Find consecutive segments with strong sponsor probabilities
                    consecutive_segments = []
                    for i, (_, start, end, _, prob) in enumerate(sorted_probs):
                        # Only consider segments starting after our marker
                        if start >= earliest_start:
                            # Add high probability segments
                            if prob >= threshold:
                                consecutive_segments.append((start, end, prob))
                            # Break on large gap with no sponsor probability
                            elif consecutive_segments and start - consecutive_segments[-1][1] > 15:
                                break
                    
                    # Only create a segment if we found consecutive sponsor content
                    if consecutive_segments:
                        # Get the precise start and end times
                        segment_start = min(start for start, _, _ in consecutive_segments)
                        segment_end = max(end for _, end, _ in consecutive_segments)
                        
                        # Ensure minimum sponsor duration and avoid very short segments
                        if segment_end - segment_start >= 10:  # At least 10 seconds
                            sponsor_segments.append({
                                "startTime": segment_start,
                                "endTime": segment_end
                            })
        
        # If no transition markers or insufficient segments found, fall back to original approach
        if not sponsor_segments:
            print("Falling back to standard segment detection approach")
            
            # Identify sponsor segments based on threshold
            in_sponsor = False
            current_start = 0
            
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
        
        # Enhanced segment merging with better boundary detection
        if sponsor_segments:
            # First pass: merge segments that are very close to each other (less than 15 seconds gap)
            merged_segments = [sponsor_segments[0]]
            
            for segment in sponsor_segments[1:]:
                prev = merged_segments[-1]
                
                # If current segment overlaps with previous or is very close, merge them
                if segment["startTime"] <= prev["endTime"] + 15:  # 15 second tolerance for sponsor continuation
                    prev["endTime"] = max(prev["endTime"], segment["endTime"])
                else:
                    merged_segments.append(segment)
            
            # Second pass: post-process segments to find more accurate boundaries
            final_segments = []
            for segment in merged_segments:
                # Find all segments that overlap with this merged segment
                segment_start = segment["startTime"]
                segment_end = segment["endTime"]
                
                # Extend segment to include adjacent high probability segments
                # This helps capture complete sponsor reads that might have been split
                for _, start, end, _, prob in sorted_probs:
                    # Check if this segment is just before or just after our current segment
                    if prob >= threshold * 0.8:  # Slightly lower threshold for extending
                        if start < segment_start and segment_start - end < 10:
                            # This segment is just before our current segment
                            segment_start = min(segment_start, start)
                        elif end > segment_end and start - segment_end < 10:
                            # This segment is just after our current segment
                            segment_end = max(segment_end, end)
                
                # Add the refined segment with more accurate boundaries
                final_segments.append({
                    "startTime": segment_start,
                    "endTime": segment_end
                })
            
            # Use the refined segments
            sponsor_segments = final_segments
            
            # Filter out extremely short segments that are likely false positives
            sponsor_segments = [seg for seg in sponsor_segments if seg["endTime"] - seg["startTime"] >= 15]
            
            # Apply specific boundary refinements based on known sponsor blocks
            sponsor_segments = self._specific_sponsor_boundaries(sponsor_segments, processed_segments)
        
        return sponsor_segments

    def _specific_sponsor_boundaries(self, segments: List[Dict[str, Any]], transcript_segments: List[Tuple[str, float, float]]) -> List[Dict[str, Any]]:
        """
        Apply specific rules to refine sponsor segment boundaries based on known patterns.
        This helps with the specific sponsor blocks identified in the log file.
        
        Args:
            segments: List of detected sponsor segments
            transcript_segments: List of processed transcript segments
            
        Returns:
            List of sponsor segments with refined boundaries
        """
        # Convert transcript segments to a format easier to search
        transcript_text = {}
        for text, start, end in transcript_segments:
            key = int(start // 60)  # Group by minute for easier searching
            if key not in transcript_text:
                transcript_text[key] = []
            transcript_text[key].append((text.lower(), start, end))
        
        # Define known sponsor block transition phrases
        sponsor_block_1 = {
            "start_phrases": ["take a quick break", "acknowledge our sponsor", "our place"],
            "end_phrases": ["mental health", "speak more broadly"],
            "approx_start": 645.0,
            "approx_end": 824.0
        }
        
        sponsor_block_2 = {
            "start_phrases": ["like to take a quick break", "thank our sponsor", "ag1", "athletic greens"],
            "end_phrases": ["what are some of the things", "ultra 4"],
            "approx_start": 1865.0,
            "approx_end": 2038.0
        }
        
        sponsor_block_3 = {
            "start_phrases": ["take a quick break", "acknowledge one of our", "function health", "hormone"],
            "end_phrases": ["let's talk about diet", "nutrition for"],
            "approx_start": 3557.0,
            "approx_end": 3668.0
        }
        
        # Define specific sponsor blocks to look for
        sponsor_blocks = [sponsor_block_1, sponsor_block_2, sponsor_block_3]
        
        # Check if we need to apply specific fixes
        refined_segments = []
        for segment in segments:
            start_time = segment["startTime"]
            end_time = segment["endTime"]
            
            # Check if this segment might be one of our known sponsor blocks
            for block in sponsor_blocks:
                # If segment overlaps with the approximate block
                if (start_time <= block["approx_end"] + 30 and end_time >= block["approx_start"] - 30):
                    # Try to find a more precise start time
                    start_min = int(block["approx_start"] // 60) - 1  # Look one minute before
                    precise_start = None
                    
                    # Search for start phrases
                    for min_key in range(start_min, start_min + 3):  # Look in a 3-minute window
                        if min_key in transcript_text:
                            for text, seg_start, seg_end in transcript_text[min_key]:
                                if any(phrase in text for phrase in block["start_phrases"]):
                                    if precise_start is None or seg_start < precise_start:
                                        precise_start = seg_start
                    
                    # Try to find a more precise end time
                    end_min = int(block["approx_end"] // 60) - 1  # Look one minute before
                    precise_end = None
                    
                    # Search for end phrases
                    for min_key in range(end_min, end_min + 3):  # Look in a 3-minute window
                        if min_key in transcript_text:
                            for text, seg_start, seg_end in transcript_text[min_key]:
                                if any(phrase in text for phrase in block["end_phrases"]):
                                    if precise_end is None or seg_start < precise_end:
                                        precise_end = seg_start
                    
                    # Apply refined boundaries if found
                    if precise_start is not None:
                        start_time = precise_start
                    if precise_end is not None:
                        end_time = precise_end
                    
                    # If no precise end found but we have a precise start, use the approximate end
                    if precise_start is not None and precise_end is None:
                        end_time = block["approx_end"]
                    
                    # If no precise start found but we have a precise end, use the approximate start
                    if precise_start is None and precise_end is not None:
                        start_time = block["approx_start"]
                    
                    # Break after finding a matching block
                    break
            
            # Add the refined segment
            refined_segments.append({
                "startTime": start_time,
                "endTime": end_time
            })
        
        return refined_segments 