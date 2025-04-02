# Sponsor Sniper

A Chrome extension that automatically skips sponsorship segments in YouTube videos.

## Features

- Automatically detects sponsorship segments in YouTube videos
- Skips to the end of any detected sponsor segment
- Configurable settings through a popup interface
- Lightweight and efficient

## Installation (Development Mode)

1. Clone or download this repository
2. Open Chrome and navigate to `chrome://extensions/`
3. Enable "Developer mode" by toggling the switch in the top right corner
4. Click "Load unpacked" and select the project directory
5. The extension should now be installed and active

## Usage

1. Navigate to any YouTube video
2. The extension will automatically detect and skip sponsorship segments
3. Configure settings by clicking the extension icon in the toolbar

## Technologies Used

- Chrome Extension API (Manifest V3)
- JavaScript
- Machine Learning for sponsor detection (backend)

## Project Structure

- `manifest.json`: Configuration file for the Chrome extension
- `content.js`: Content script that runs on YouTube pages
- `popup.html` & `popup.js`: User interface for extension settings
- `images/`: Directory containing icon assets

## License

MIT 