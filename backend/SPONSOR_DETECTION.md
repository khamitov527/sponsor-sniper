# Sponsor Detection Tool

This tool allows you to detect sponsor segments in YouTube videos and save detailed logs for analysis.

## Prerequisites

- Python 3.6+
- Virtual environment with required packages installed (see `requirements.txt`)
- YouTube video ID
- DeepSeek API key (optional, will use fallback mechanism if not provided)

## Setup

1. Make sure you've installed all required packages:
   ```
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. Configure DeepSeek API (recommended for best results):
   ```
   cp .env.example .env
   # Edit .env file to add your DeepSeek API key
   ```

3. Start the backend server:
   ```
   python main.py
   ```

## Using the Sponsor Detection Tool

### Option 1: Using the provided shell script (recommended)

The easiest way to detect sponsors and generate logs is using the included shell script:

```
./detect_sponsors.sh <youtube_video_id> [threshold]
```

For example:
```
./detect_sponsors.sh hCyvqRq5YmM 0.3
```

The script will:
1. Check if the server is running and start it if needed
2. Make the API request to detect sponsors
3. Create a log file with detailed analysis
4. Offer to display the log file contents
5. If the log file path cannot be extracted from the API response, the script will automatically find the most recent log file for the video ID

### Option 2: Using curl directly

You can also use curl directly to call the API endpoint:

```
curl "http://localhost:8080/sponsors_log?v=<youtube_video_id>&threshold=<threshold>"
```

For example:
```
curl "http://localhost:8080/sponsors_log?v=hCyvqRq5YmM&threshold=0.3"
```

The response will include the path to the generated log file.

### Option 3: Using the test_deepseek.py script

For direct testing of the DeepSeek functionality (or the fallback mechanism):

```
python3 test_deepseek.py <youtube_video_id> [threshold]
```

For example:
```
python3 test_deepseek.py hCyvqRq5YmM 0.3
```

### Log File Format

The log files are stored in the `logs` directory with filenames in the format:
```
sponsors_<video_id>_<timestamp>.txt
```

Each log file contains:
1. Basic information about the video and detection parameters
2. List of segments with non-zero probability of being sponsors
3. Detailed breakdown of detected sponsor segments
4. Text snippets that triggered the detection

## Detection Methods

The system uses two approaches for sponsor detection:

1. **DeepSeek API (Primary)**: Uses DeepSeek's advanced language model for highly accurate sponsor detection. Requires a valid API key.

2. **Keyword-based Heuristics (Fallback)**: If the DeepSeek API is unavailable or fails, the system falls back to a keyword-based approach that looks for common sponsor-related phrases like "sponsor," "promo code," etc.

## Adjusting the Detection Threshold

The detection threshold controls how sensitive the system is to potential sponsor content:

- **Lower threshold (e.g., 0.3)**: More segments will be detected, including potential false positives
- **Higher threshold (e.g., 0.7)**: Only segments with high confidence will be detected

The default threshold is 0.3, which provides a good balance between detecting most sponsor segments while keeping false positives manageable.

## Example Commands

Detect sponsors in a video with default threshold (0.3):
```
./detect_sponsors.sh JHjhw8Ek3Zk
```

Detect sponsors with custom threshold:
```
./detect_sponsors.sh hCyvqRq5YmM 0.5
```

View a specific log file:
```
cat logs/sponsors_hCyvqRq5YmM_20250402_191210.txt
```

## Testing Results

The tool has been tested with various YouTube videos:

1. **Video ID: hCyvqRq5YmM** - 15 sponsor segments detected
2. **Video ID: JHjhw8Ek3Zk** - 9 sponsor segments detected
3. **Video ID: dQw4w9WgXcQ** - 0 sponsor segments detected (no sponsors found)

These results demonstrate the tool's ability to identify sponsor content across different types of videos with varying content. 