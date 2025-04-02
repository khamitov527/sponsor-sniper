# Sponsor Sniper Backend

This directory contains the backend server for the Sponsor Sniper extension, which automatically detects and skips sponsor segments in YouTube videos.

## How It Works

The sponsor detection system uses a machine learning approach to identify sponsor segments in YouTube video transcripts:

1. The system fetches the transcript for a YouTube video using the YouTube Transcript API.
2. The transcript is preprocessed into overlapping windows of text segments.
3. Each window is classified as either sponsor content or regular content using our ML classifier.
4. Consecutive sponsor segments are merged to form larger sponsor blocks.
5. The identified sponsor segments are returned to the extension for skipping during playback.

## Machine Learning Classifier

The system uses a transformer-based text classification model from Hugging Face to identify sponsor content:

- **Base Model**: DistilBERT (a lighter, faster version of BERT)
- **Classification**: Binary classification (sponsor vs. non-sponsor)
- **Fallback Mechanism**: When the fine-tuned model is not available or during development, the system falls back to a keyword-based heuristic approach.

### Fallback Heuristic Approach

The current implementation uses a keyword-based approach as a fallback mechanism until the ML model is properly fine-tuned:

1. The system looks for sponsor-related keywords in the text (e.g., "sponsor", "promo code", "discount", etc.).
2. The probability of a segment being sponsor content is calculated based on the density of these keywords.
3. Segments with a probability above a threshold are classified as sponsor content.

### Future Improvements

The classifier will be improved in the following ways:

1. **Fine-tuning**: The model will be fine-tuned on a labeled dataset of sponsor segments from real YouTube videos.
2. **Contextual Understanding**: The model will learn to identify sponsor content based on contextual clues, not just keywords.
3. **Temporal Information**: The classification will incorporate temporal features of the video to improve accuracy.

## Setup and Running

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Run the server:
   ```
   python main.py
   ```

## API Endpoints

- `GET /ping` - Health check endpoint
- `GET /sponsors?v={video_id}` - Get sponsor segments for a YouTube video
- `GET /transcript?v={video_id}` - Get the transcript for a YouTube video 