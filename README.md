# Sponsor Sniper

A Chrome extension that automatically skips sponsorship segments in YouTube videos using AI-powered detection.

## Features

- Automatically detects sponsorship segments in YouTube videos using AI
- Uses DeepSeek API for accurate sponsor detection (with fallback mechanism)
- Skips to the end of any detected sponsor segment
- Configurable settings through a popup interface
- Lightweight and efficient

## How It Works

Sponsor Sniper uses the DeepSeek API to detect sponsor segments in YouTube videos:

1. The extension extracts the video ID from the YouTube URL
2. It requests the video transcript from our backend server
3. The DeepSeek API analyzes the transcript to identify sponsor segments
4. If DeepSeek API is unavailable, falls back to keyword-based detection
5. The extension automatically skips these segments during video playback

## Installation (Development Mode)

1. Clone or download this repository
2. Set up the backend server:
   ```bash
   cd backend
   
   # Create and activate virtual environment
   python3 -m venv venv
   source venv/bin/activate  # On Unix/macOS
   # or
   .\venv\Scripts\activate  # On Windows
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Configure DeepSeek API
   cp .env.example .env
   # Edit .env and add your DeepSeek API key
   
   # Start the server
   python3 main.py
   ```
3. Open Chrome and navigate to `chrome://extensions/`
4. Enable "Developer mode" by toggling the switch in the top right corner
5. Click "Load unpacked" and select the project directory
6. The extension should now be installed and active

## Usage

1. Navigate to any YouTube video
2. The extension will automatically detect and skip sponsorship segments
3. Configure settings by clicking the extension icon in the toolbar

## Testing

You can test the sponsor detection with any YouTube video:

```bash
cd backend
source venv/bin/activate  # On Unix/macOS
# or
.\venv\Scripts\activate  # On Windows

python3 test_deepseek.py VIDEO_ID [threshold] [include_transcript]
```

Example:
```bash
python3 test_deepseek.py hCyvqRq5YmM 0.3 1
```

For more detailed testing instructions, see the [backend README](backend/README.md).

## Technologies Used

- Chrome Extension API (Manifest V3)
- JavaScript
- Flask (Python backend)
- DeepSeek API for AI-powered sponsor detection
- YouTube Transcript API

## Project Structure

- `manifest.json`: Configuration file for the Chrome extension
- `content.js`: Content script that runs on YouTube pages
- `popup.html` & `popup.js`: User interface for extension settings
- `images/`: Directory containing icon assets
- `backend/`: Python backend for sponsor detection
  - `main.py`: Flask server with API endpoints
  - `test_deepseek.py`: Script for testing sponsor detection
  - `requirements.txt`: Python dependencies
  - `.env.example`: Example environment configuration

## License

MIT 