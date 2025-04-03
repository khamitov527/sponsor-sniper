# Using DeepSeek API for Sponsor Detection

This guide explains how to set up and use the DeepSeek API integration for more accurate sponsor detection in YouTube videos.

## What is DeepSeek?

DeepSeek provides powerful language models that can understand and analyze text. We use these models to identify sponsor segments in YouTube video transcripts with high accuracy.

## Setup Instructions

1. **Sign up for a DeepSeek account**:
   - Go to [DeepSeek Platform](https://platform.deepseek.com/)
   - Create an account and sign in
   - Navigate to your API settings to get your API key

2. **Configure your API key**:
   - Copy the example environment file:
     ```
     cp .env.example .env
     ```
   - Edit the `.env` file and replace `your_deepseek_api_key_here` with your actual API key

3. **Install dependencies**:
   - Make sure you have all required packages:
     ```
     pip install -r requirements.txt
     ```

## Testing the DeepSeek Integration

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
2. Send the transcript to DeepSeek for analysis
3. Display the detected sponsor segments

## Fallback Mechanism

If the DeepSeek API is not available (for example, if the API key is not configured or if the API call fails), the system will automatically fall back to the heuristic approach.

## Using the API Endpoint

The regular API endpoint `/sponsors` will automatically use DeepSeek if it's configured:

```
GET /sponsors?v=VIDEO_ID&threshold=0.3
```

## Troubleshooting

1. **API Key Issues**:
   - Make sure your `.env` file is properly configured
   - Check that your API key is valid and has not expired
   - Ensure you have sufficient credits in your DeepSeek account

2. **No Sponsor Segments Detected**:
   - Try adjusting the threshold (lower values will detect more segments)
   - Verify that the video actually contains sponsor content
   - Check if the transcript is available for the video

3. **Error Responses**:
   - If you see an API error, check the DeepSeek status page
   - Ensure your request is properly formatted
   - Check your network connection

## API Quotas and Limits

Be aware that DeepSeek API may have usage limits and quotas. Check your DeepSeek account dashboard for current usage and limits.

## Privacy Considerations

When using the DeepSeek API:
- Video transcripts are sent to DeepSeek's servers for processing
- No user identification or personal data is sent
- Only the text content of the transcript is processed 