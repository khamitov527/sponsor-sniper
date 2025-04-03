# Sponsor Sniper Backend

This directory contains the backend server for the Sponsor Sniper extension, which automatically detects and skips sponsor segments in YouTube videos.

## How It Works

The sponsor detection system uses either the DeepSeek API or a machine learning approach to identify sponsor segments in YouTube video transcripts:

1. The system fetches the transcript for a YouTube video using the YouTube Transcript API.
2. The transcript is preprocessed into overlapping windows of text segments.
3. Each window is classified as either sponsor content or regular content using DeepSeek API or our ML classifier.
4. Consecutive sponsor segments are merged to form larger sponsor blocks.
5. The identified sponsor segments are returned to the extension for skipping during playback.

## DeepSeek API Integration (Recommended)

The system now primarily uses the DeepSeek API for more accurate sponsor detection:

- **How it works**: The system sends the video transcript with timestamps to DeepSeek's language model which analyzes the content and identifies sponsored segments.
- **Configuration**: Set up your DeepSeek API key in the `.env` file (copy from `.env.example`).
- **Fallback**: If the DeepSeek API key is not configured or if the API call fails, the system will automatically fall back to the heuristic approach.

### Setting up DeepSeek API

1. Sign up for an account at [DeepSeek Platform](https://platform.deepseek.com/)
2. Get your API key from the dashboard
3. Copy `.env.example` to `.env` and add your API key:
   ```
   cp .env.example .env
   ```
4. Edit the `.env` file and replace `your_deepseek_api_key_here` with your actual API key

## Machine Learning Classifier (Legacy)

The system can still use a transformer-based text classification model as a fallback:

- **Base Model**: DistilBERT (a lighter, faster version of BERT)
- **Classification**: Binary classification (sponsor vs. non-sponsor)
- **Fallback Mechanism**: When the DeepSeek API is not available or during development, the system falls back to a keyword-based heuristic approach.

### Fallback Heuristic Approach

The current implementation uses a keyword-based approach as a fallback mechanism:

1. The system looks for sponsor-related keywords in the text (e.g., "sponsor", "promo code", "discount", etc.).
2. The probability of a segment being sponsor content is calculated based on the density of these keywords.
3. Segments with a probability above a threshold are classified as sponsor content.

### Future Improvements

The classifier will be improved in the following ways:

1. **Fine-tuning**: The model will be fine-tuned on a labeled dataset of sponsor segments from real YouTube videos.
2. **Contextual Understanding**: The model will learn to identify sponsor content based on contextual clues, not just keywords.
3. **Temporal Information**: The classification will incorporate temporal features of the video to improve accuracy.

## Setup and Running

1. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use: venv\Scripts\activate
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Configure the DeepSeek API (recommended):
   ```
   cp .env.example .env
   # Edit .env file to add your DeepSeek API key
   ```

4. Run the server:
   ```
   python main.py
   ```

## API Endpoints

- `GET /ping` - Health check endpoint
- `GET /sponsors?v={video_id}` - Get sponsor segments for a YouTube video
- `GET /transcript?v={video_id}` - Get the transcript for a YouTube video 