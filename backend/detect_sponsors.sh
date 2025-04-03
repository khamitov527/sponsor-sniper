#!/bin/bash

# Sponsor Sniper - Command line script for detecting sponsors in YouTube videos
# Usage: ./detect_sponsors.sh <youtube_video_id> [threshold] [include_transcript]

# Default threshold
THRESHOLD=0.3

# Default include_transcript (1 = yes, 0 = no)
INCLUDE_TRANSCRIPT=1

# Check if video ID is provided
if [ -z "$1" ]; then
    echo "Error: Please provide a YouTube video ID"
    echo "Usage: ./detect_sponsors.sh <youtube_video_id> [threshold] [include_transcript]"
    echo "Arguments:"
    echo "  youtube_video_id: The YouTube video ID"
    echo "  threshold: Detection threshold (default: 0.3)"
    echo "  include_transcript: Whether to include full transcript in log (1 or 0, default: 1)"
    exit 1
fi

# Set video ID
VIDEO_ID=$1

# Set threshold if provided
if [ ! -z "$2" ]; then
    THRESHOLD=$2
fi

# Set include_transcript if provided
if [ ! -z "$3" ]; then
    INCLUDE_TRANSCRIPT=$3
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Make sure backend server is running
echo "Checking if backend server is running..."
if ! curl -s http://localhost:8080/ping > /dev/null; then
    echo "The backend server doesn't seem to be running."
    echo "Do you want to start it now? (y/n)"
    read answer
    if [ "$answer" == "y" ] || [ "$answer" == "Y" ]; then
        echo "Starting the backend server..."
        # Try to ensure we're in the virtual environment
        if [ -f "venv/bin/activate" ]; then
            source venv/bin/activate
            echo "Virtual environment activated."
        fi
        python main.py &
        SERVER_PID=$!
        echo "Server started with PID: $SERVER_PID"
        echo "Waiting for server to start..."
        sleep 5
    else
        echo "Please start the server manually and try again."
        exit 1
    fi
fi

# Make the request to the API
echo "Detecting sponsors in video: $VIDEO_ID with threshold: $THRESHOLD"
echo "Include full transcript: $([ "$INCLUDE_TRANSCRIPT" == "1" ] && echo "Yes" || echo "No")"
echo "Please wait, this may take a moment as we analyze the video transcript..."

# Make the API request
RESPONSE=$(curl -s "http://localhost:8080/sponsors_log?v=$VIDEO_ID&threshold=$THRESHOLD&include_transcript=$INCLUDE_TRANSCRIPT")

# Extract log file path using proper JSON parsing
# Use Python for reliable JSON parsing
LOG_FILE=$(python3 -c "import sys, json; print(json.loads(sys.stdin.read()).get('log_file', ''))" <<< "$RESPONSE")

# Count sponsors in response
SPONSOR_COUNT=$(python3 -c "import sys, json; print(len(json.loads(sys.stdin.read()).get('sponsors', [])))" <<< "$RESPONSE")

if [ -n "$LOG_FILE" ] && [ -f "$LOG_FILE" ]; then
    echo "✅ Detection completed successfully!"
    echo "📊 Found $SPONSOR_COUNT sponsor segments"
    echo "📝 Log file created: $LOG_FILE"
    if [ "$INCLUDE_TRANSCRIPT" == "1" ]; then
        echo "📄 Full transcript included in log file"
    fi
    echo "Do you want to view the log file now? (y/n)"
    read answer
    if [ "$answer" == "y" ] || [ "$answer" == "Y" ]; then
        cat "$LOG_FILE"
    else
        echo "You can view the log file later with: cat $LOG_FILE"
    fi
else
    echo "Log file was created but could not be extracted from response."
    echo "API response: $RESPONSE"
    
    # Try to find the log file in the logs directory
    LATEST_LOG=$(ls -t logs | grep "sponsors_${VIDEO_ID}" | head -1)
    if [ -n "$LATEST_LOG" ]; then
        LATEST_LOG="logs/$LATEST_LOG"
        echo "Found log file: $LATEST_LOG"
        echo "Do you want to view the log file now? (y/n)"
        read answer
        if [ "$answer" == "y" ] || [ "$answer" == "Y" ]; then
            cat "$LATEST_LOG"
        else
            echo "You can view the log file later with: cat $LATEST_LOG"
        fi
    fi
fi

echo "Sponsor detection complete." 