# Video Processor - Implementation Spec

## Overview

Cloud Function that processes video URLs (TikTok, YouTube, Spotify podcasts) with AI analysis, transcription, and music recognition. Uploads to Google Cloud Storage and returns structured JSON for n8n orchestration.

## Architecture

```
video-enricher (Cloud Function)
├── Download (yt-dlp primary, RapidAPI fallback)
├── Upload to GCS (temporary storage with public URLs)
├── Gemini 2.0 Flash Analysis (full video analysis)
├── AssemblyAI Transcription (audio → text)
├── Validation (shared utilities)
└── Return JSON response
```

## Implementation Details

### Cloud Function

**Name:** `video-downloader` (GCP) / `video-enricher` (local)
**Runtime:** Python 3.11
**Region:** us-central1
**Memory:** 1024MB
**Timeout:** 540s (9 minutes)

### Entry Point

```python
@functions_framework.http
def download_and_store(request):
    """Main Cloud Function entry point."""
```

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `video_url` | string | Yes | URL of video to process |
| `filename` | string | No | Custom filename (auto-generated if not provided) |
| `extract_audio` | boolean | No | Extract audio (default: true) |
| `transcribe_audio` | boolean | No | Transcribe audio (default: true) |
| `analyze_video` | boolean | No | Run Gemini analysis (default: true) |
| `gemini_api_key` | string | No | Override Gemini API key |
| `assemblyai_api_key` | string | No | Override AssemblyAI API key |

### Download Pipeline

**Source Detection:**
```python
def download_video(url, tmpdir):
    if is_spotify_podcast(url):
        return download_spotify_podcast(url, tmpdir)
    elif 'tiktok' in url.lower():
        return download_tiktok_video(url, tmpdir)
    else:
        return download_with_ytdlp(url, tmpdir)
```

**TikTok Download:**
- Primary: yt-dlp (free, unlimited)
- Fallback: RapidAPI (paid, reliable)
- Uses NullLogger to avoid stdout issues in Cloud Functions

**YouTube Download:**
- yt-dlp with anti-bot measures
- Multiple player clients: ios, android_vr, tv_embedded
- Custom User-Agent header

**Spotify Podcasts:**
1. Get metadata via oEmbed API
2. Search YouTube for episode using title
3. Download from YouTube if found
4. Fallback to YouTube Data API search

### Video Analysis

**Model:** Gemini 2.0 Flash (gemini-2.0-flash)

**Process:**
1. Upload video to Gemini File API
2. Wait for processing (max 120s)
3. Generate analysis with structured prompt
4. Clean up uploaded file

**Analysis Sections:**
- Visual Content
- Audio Content
- Style & Production
- Mood & Tone
- Key Messages
- Content Category

### Audio Transcription

**Service:** AssemblyAI

**Features:**
- Automatic language detection
- Punctuation and text formatting
- Word-level timestamps
- Confidence scoring

### Smart Filename Generation

```python
def generate_smart_filename(title, uploader, ext='mp4'):
    """Generate filename matching existing convention.
    Uses smart truncation at word boundaries (max 70 chars for title).
    """
```

Uses shared utilities:
- `sanitize_title()` - Remove invalid characters
- `truncate_title()` - Truncate at word boundary (max 70 chars)

### Validation

Uses `shared/analysis_utils.py`:
- Validates required analysis sections
- Checks for missing fields
- Returns validation errors for n8n handling

## Response Schema

```json
{
  "success": true,
  "video": {
    "file_name": "Smart-Title-Here - Uploader Name.mp4",
    "public_url": "https://storage.googleapis.com/bucket/videos/...",
    "size_bytes": 12345678,
    "blob_name": "videos/Smart-Title-Here - Uploader Name.mp4"
  },
  "metadata": {
    "title": "Smart Title Here",
    "duration": 60,
    "uploader": "Uploader Name",
    "video_id": "abc123",
    "source": "tiktok",
    "thumbnail": "https://..."
  },
  "audio": {
    "file_name": "Smart-Title-Here - Uploader Name.mp3",
    "public_url": "https://storage.googleapis.com/bucket/videos/...",
    "size_bytes": 1234567
  },
  "transcription": {
    "text": "Full transcript here...",
    "confidence": 0.96,
    "language": "en",
    "duration_seconds": 60,
    "word_count": 150
  },
  "gemini_analysis": {
    "analysis": "Detailed analysis with sections...",
    "model": "gemini-2.0-flash"
  },
  "validation": {
    "valid": true,
    "errors": [],
    "required_sections": ["Visual Content", "Audio Content", ...]
  }
}
```

## Error Handling

**Error Response:**
```json
{
  "success": false,
  "error": "Error message",
  "traceback": "Full stack trace"
}
```

**Partial Results:** Function continues processing even if some components fail. Errors are included in the response for n8n to handle.

**Recoverable Errors:**
- Rate limits (HTTP 429)
- Timeouts
- "Sign in to confirm" (YouTube bot detection)

**Non-Recoverable Errors:**
- Invalid URL format
- Video not found (404)
- Missing required API keys

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | Yes | Google Gemini API key |
| `ASSEMBLYAI_API_KEY` | Yes | AssemblyAI transcription key |
| `GCS_BUCKET` | No | Storage bucket (default: video-processor-temp-rhe) |
| `GOOGLE_SERVICE_ACCOUNT` | No | Service account JSON (auto in GCP) |
| `RAPIDAPI_KEY` | No | RapidAPI key for TikTok fallback |

## Dependencies

```
functions-framework==3.*
google-cloud-storage==2.*
google-generativeai==0.*
assemblyai==0.*
yt-dlp
```

## Deployment

```bash
cd video-enricher
gcloud functions deploy video-downloader \
  --gen2 --runtime=python311 --region=us-central1 \
  --trigger-http --allow-unauthenticated \
  --memory=1024MB --timeout=540s \
  --set-env-vars="GEMINI_API_KEY=xxx,ASSEMBLYAI_API_KEY=xxx"
```

## Performance

| Metric | Target | Actual |
|--------|--------|--------|
| Processing time | <30s | ~25-30s |
| Cost per video | <$0.06 | ~$0.017 |
| Transcription accuracy | >95% | 96% |

## Shared Utilities

Uses `/shared/` module for consistency:

| Module | Functions Used |
|--------|----------------|
| `title_utils.py` | `truncate_title()`, `sanitize_title()`, `validate_title()` |
| `analysis_utils.py` | `validate_video_enrichment()`, `REQUIRED_ANALYSIS_SECTIONS` |

## Testing

```bash
# Unit tests
pytest tests/unit/test_video_enricher.py -v

# Manual test
curl -X POST $ENDPOINT \
  -H 'Content-Type: application/json' \
  -d '{"video_url":"https://www.tiktok.com/@user/video/123"}'
```

## Changelog

| Date | Change |
|------|--------|
| 2024-12-23 | Initial implementation |
| 2024-12-28 | Upgraded to Gemini 2.0 Flash |
| 2024-12-29 | Added Spotify podcast support via YouTube search |
| 2025-12-31 | Added shared utilities, validation |

---

**Product Spec:** [Video-Processor-Product-Spec.md](Video-Processor-Product-Spec.md)

**Last Updated:** December 31, 2025
