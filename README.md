# Sponsor Sniper

A Chrome extension that automatically skips sponsorship segments in YouTube videos using machine learning.

## Features

- Automatically detects sponsorship segments in YouTube videos using ML
- Uses transformer-based models from Hugging Face for accurate sponsor detection
- Skips to the end of any detected sponsor segment
- Configurable settings through a popup interface
- Lightweight and efficient

## How It Works

Sponsor Sniper uses a machine learning approach to detect sponsor segments in YouTube videos:

1. The extension extracts the video ID from the YouTube URL
2. It requests the video transcript from our backend server
3. Our ML classifier analyzes the transcript to identify sponsor segments
4. The extension automatically skips these segments during video playback

## Installation (Development Mode)

1. Clone or download this repository
2. Set up the backend server:
   ```
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows, use: venv\Scripts\activate
   pip install -r requirements.txt
   python main.py
   ```
3. Open Chrome and navigate to `chrome://extensions/`
4. Enable "Developer mode" by toggling the switch in the top right corner
5. Click "Load unpacked" and select the project directory
6. The extension should now be installed and active

## Usage

1. Navigate to any YouTube video
2. The extension will automatically detect and skip sponsorship segments
3. Configure settings by clicking the extension icon in the toolbar

## Technologies Used

- Chrome Extension API (Manifest V3)
- JavaScript
- Flask (Python backend)
- Hugging Face Transformers for ML-based sponsor detection
- YouTube Transcript API

## Project Structure

- `manifest.json`: Configuration file for the Chrome extension
- `content.js`: Content script that runs on YouTube pages
- `popup.html` & `popup.js`: User interface for extension settings
- `images/`: Directory containing icon assets
- `backend/`: Python backend with ML-based sponsor detection
  - `main.py`: Flask server with API endpoints
  - `sponsor_classifier.py`: ML classifier for sponsor detection
  - `fine_tune.py`: Script for fine-tuning the ML model

## License

MIT 