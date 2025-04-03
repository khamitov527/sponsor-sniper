# Sponsor Sniper Backend

This directory contains the backend server for the Sponsor Sniper extension, which automatically detects and skips sponsor segments in YouTube videos.

## How It Works

The sponsor detection system uses the DeepSeek API (with a keyword-based fallback mechanism) to identify sponsor segments in YouTube video transcripts:

1. The system fetches the transcript for a YouTube video using the YouTube Transcript API.
2. The transcript is preprocessed into overlapping windows of text segments.
3. Each window is classified as either sponsor content or regular content using the DeepSeek API or our fallback heuristic approach.
4. Consecutive sponsor segments are merged to form larger sponsor blocks.
5. The identified sponsor segments are returned to the extension for skipping during playback.

## DeepSeek API Integration (Recommended)

The system primarily uses the DeepSeek API for accurate sponsor detection:

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

## Fallback Heuristic Approach

When the DeepSeek API is not available or fails, the system uses a keyword-based approach as a fallback mechanism:

1. The system looks for sponsor-related keywords in the text (e.g., "sponsor", "promo code", "discount", etc.).
2. The probability of a segment being sponsor content is calculated based on the density of these keywords.
3. Segments with a probability above a threshold are classified as sponsor content.

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

3. Configure the DeepSeek API:
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
- `GET /sponsors_log?v={video_id}` - Get sponsor segments with detailed log

## Testing

You can test the DeepSeek integration with a specific YouTube video:

```
python test_deepseek.py VIDEO_ID [threshold]
```

For example:
```
python test_deepseek.py dQw4w9WgXcQ 0.3
```

This will:
1. Fetch the transcript for the specified video
2. Process it using either DeepSeek API or the fallback mechanism
3. Display the detected sponsor segments 