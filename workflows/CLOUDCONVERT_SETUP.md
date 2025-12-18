# CloudConvert Setup for Large Video Files

## Problem

OpenAI Whisper has a 25MB file size limit. Many TikTok videos exceed this limit, causing transcription to fail with error 413.

## Solution

Use CloudConvert API to extract audio as MP3 before sending to Whisper. MP3 audio is typically 1-5MB, well under the limit.

## Implementation

### Option 1: Import Updated Workflow (Recommended)

1. **Export current workflow** (backup):
   - Go to n8n workflows
   - Open "TikTok Video Complete Processor"
   - Click "..." menu → Export

2. **Deactivate current workflow**:
   - Toggle the workflow to inactive

3. **Import new workflow**:
   - Go to n8n workflows
   - Click "Import from File"
   - Select: `TikTok_Complete_Processor_WITH_CLOUDCONVERT.json`
   - This will create a new workflow with CloudConvert integration

4. **Activate new workflow**:
   - Toggle the new workflow to active
   - Delete or keep the old workflow as backup

### Option 2: Manual Addition (If Import Fails)

1. **Open current workflow** in n8n editor

2. **Delete old CloudConvert nodes** (if any):
   - "Create CloudConvert Job"
   - "Upload to CloudConvert"
   - "Wait for Conversion"
   - "Download MP3"

3. **Add new Code node**:
   - Position: Between "Download Video" and "Transcribe Audio"
   - Name: "CloudConvert Audio Extract"
   - Code: See code block below

4. **Connect nodes**:
   - "Download Video" → "CloudConvert Audio Extract"
   - "CloudConvert Audio Extract" → "Transcribe Audio"
   - Keep existing "Download Video" → "Upload to Google Drive" connection

5. **Test workflow** with large video

### Code Node Implementation

```javascript
// CloudConvert async workflow with polling
const apiKey = 'YOUR_CLOUDCONVERT_API_KEY_HERE';
const videoUrl = $('Get Video Info').item.json.video_download_url;

// Step 1: Create job with import/url (CloudConvert downloads file)
const jobResponse = await $http.request({
  method: 'POST',
  url: 'https://api.cloudconvert.com/v2/jobs',
  headers: {
    'Authorization': `Bearer ${apiKey}`,
    'Content-Type': 'application/json'
  },
  body: {
    tasks: {
      'import-video': {
        operation: 'import/url',
        url: videoUrl,
        filename: 'video.mp4'
      },
      'convert-audio': {
        operation: 'convert',
        input: ['import-video'],
        output_format: 'mp3',
        audio_codec: 'mp3',
        audio_bitrate: 128
      },
      'export-audio': {
        operation: 'export/url',
        input: ['convert-audio']
      }
    }
  }
});

const jobData = await jobResponse.json();
const jobUrl = jobData.data.links.self;

// Step 2: Poll for completion (max 60 seconds)
let exportUrl = null;
for (let attempt = 0; attempt < 30; attempt++) {
  await new Promise(resolve => setTimeout(resolve, 2000)); // Wait 2s

  const statusResponse = await $http.request({
    method: 'GET',
    url: jobUrl,
    headers: {
      'Authorization': `Bearer ${apiKey}`
    }
  });

  const statusData = await statusResponse.json();
  const status = statusData.data.status;

  if (status === 'finished') {
    const exportTask = statusData.data.tasks.find(t => t.name === 'export-audio');
    exportUrl = exportTask.result.files[0].url;
    break;
  } else if (status === 'error') {
    throw new Error('CloudConvert conversion failed');
  }
}

if (!exportUrl) {
  throw new Error('CloudConvert job timed out after 60 seconds');
}

// Step 3: Download MP3
const mp3Response = await $http.request({
  method: 'GET',
  url: exportUrl,
  encoding: 'arraybuffer'
});

// Return as binary data for Whisper
return {
  binary: {
    data: mp3Response.body
  }
};
```

## CloudConvert API Key

Your CloudConvert API key is already configured in n8n credentials with ID `6ntH86z73QMaDw41`.

If using Option 2 (manual code), replace `YOUR_CLOUDCONVERT_API_KEY_HERE` with:
```
eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiIxIiwianRpIjoiNTA5OGI3MTIzYjNjYTNkOWEyNDJhYzg2MmQ0YTJiMjM5YWNjMGZhMTNlZTRlZTU1MmFiYjUxZjFhMzRlY2JkNzA3N2UzN2I0OTMzZWFlMzYiLCJpYXQiOjE3MzQ0NzAzMDQuMDE0MTIsIm5iZiI6MTczNDQ3MDMwNC4wMTQxMjIsImV4cCI6NDg4ODE0MzkwNC4wMDk4OTMsInN1YiI6IjczMDYwNjQ3Iiwic2NvcGVzIjpbInVzZXIucmVhZCIsInVzZXIud3JpdGUiLCJ0YXNrLnJlYWQiLCJ0YXNrLndyaXRlIiwid2ViaG9vay5yZWFkIiwid2ViaG9vay53cml0ZSIsInByZXNldC5yZWFkIiwicHJlc2V0LndyaXRlIl19.KbEAkJNXAO2lPyPn2YyO2JEzd2gOD0wGqJZNQGEaCOneBG52b0-Xh6vKL6Fh56OsYAiJYDwpJETv-yv9WYKb7EvEaWTrE3HqtqAp0rULjWW3ooP9v-qiNy8EIJnzQB2BWYPl5DYx-mnEBOXi8jqLnbWuBvZAjvTRs8kO3nHxbzkTSW9_L4L1HhvTKEOKZ4Tz5Og8Y5WrPk0NhWMW5qJqvRKdU0BkdGBOqpLcZnTt8uP2dHH8sLgS0EBrBpY-NxY7qjO-zTZZ0e0Y9UjJXjKPqn9F7oR1nMvzYqgfKwOZ3bL8ooOT7uHEAQo4Ol9n2FjE0hpN_kJT7gHgZZLXtbkKDQ
```

## How It Works

1. **import/url**: CloudConvert downloads the video directly from TikTok's CDN (no manual upload needed)
2. **convert**: Extracts audio track and converts to MP3 (128kbps)
3. **export/url**: Makes MP3 available for download
4. **Polling**: Checks job status every 2 seconds for up to 60 seconds
5. **Download**: Retrieves MP3 file as binary data
6. **Whisper**: Transcribes the smaller MP3 file

## Cost & Limits

- **Free Tier**: 25 conversions per day
- **Cost per conversion**: ~$0.001-0.002
- **Processing time**: 5-15 seconds for most TikTok videos
- **File size reduction**: 25MB video → 1-5MB MP3

## Testing

Test with the video that previously failed:
```bash
curl -X POST https://royhen.app.n8n.cloud/webhook/analyze-video-complete \
  -H 'Content-Type: application/json' \
  -d '{"video_url":"https://www.tiktok.com/@agentic.james/video/7583734051748482317"}'
```

Expected result: Successful transcription with CloudConvert handling the large video file.

## Troubleshooting

### Error: "Unauthenticated"
- Check that API key is correct in the code
- Verify CloudConvert credential ID is `6ntH86z73QMaDw41`

### Error: "Job timed out"
- Increase timeout from 30 attempts (60s) to 45 attempts (90s)
- Check CloudConvert dashboard for failed jobs

### Error: "Cannot read property 'files' of undefined"
- Job finished but export task missing result
- Check CloudConvert logs for conversion errors
- Verify video URL is accessible

## Alternative: Simple Timeout Increase

If CloudConvert is still too complex, you can temporarily test with smaller videos while we work on the integration. But per your requirement "I don't want to skip anything. This is crucial", the CloudConvert solution is necessary for handling all video sizes.

## Next Steps

1. Import the updated workflow
2. Test with the large video
3. If successful, commit workflow to git
4. Update README with CloudConvert integration details
