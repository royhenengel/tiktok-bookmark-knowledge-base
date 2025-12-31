# Video Processor - Product Spec

## Goal

Build an automated video analysis system that extracts comprehensive metadata, transcriptions, music identification, and visual analysis from videos, storing them in Google Drive with structured JSON output.

## Requirements

- Download videos reliably (yt-dlp primary, RapidAPI fallback)
- Generate smart titles (50-70 chars, SEO-optimized)
- Extract content tags (topic, style, mood, format, purpose)
- Create rich descriptions (visual + audio content)
- Transcribe audio via AssemblyAI (96% accuracy)
- Analyze videos via Gemini 2.0 Flash (full video analysis)
- Identify music via ACRCloud (≥70% confidence threshold)
- Upload videos to Google Drive with descriptive filenames
- Return structured JSON output
- Process in ~25-30 seconds per video
- Cost target: <$0.06 per video (actual: ~$0.017)

## Scope

### In Scope (Phase 1 - TikTok)

- TikTok video processing end-to-end
- n8n Cloud orchestration + Google Cloud Function for downloads
- AssemblyAI transcription, Gemini 2.0 Flash analysis, ACRCloud music ID
- Google Drive storage, Cloud Storage backup

### Out of Scope (Future Phases)

- YouTube video support (Phase 2)
- Batch processing interface
- Cost monitoring dashboard
- Shazam fallback for low-confidence matches

## Success Criteria

- End-to-end processing completes successfully
- Transcription accuracy ≥95%
- Music recognition returns matches for songs with ≥70% confidence
- Videos uploaded to Drive with proper naming
- JSON output includes all required fields
- Processing time ≤30 seconds
- Cost per video ≤$0.06

## Features - Working

- End-to-end video processing via n8n + Cloud Function
- Cloud Function handles video download via yt-dlp (free, unlimited) with RapidAPI fallback
- Gemini 2.0 Flash analysis of full video content
- AssemblyAI audio transcription (96% accuracy, URL-based - no upload needed)
- ACRCloud music recognition with confidence scoring
- Automated Google Drive uploads with smart filenames
- GPT-4 Mini metadata generation
- Structured JSON output

## Features - Planned

- RapidAPI Shazam fallback for low-confidence matches
- Batch processing interface
- Cost monitoring dashboard

## Output Capabilities

- Smart Titles (50-70 characters, SEO-optimized)
- Content Tags (topic, style, mood, format, purpose)
- Rich Descriptions (covering visual and audio content)
- Audio Transcriptions (via AssemblyAI)
- Visual Analysis (via Gemini 2.0 Flash)
- Music Recognition (via ACRCloud - identifies songs with confidence scoring)
- Google Drive Storage (organized video library with descriptive filenames)
- Cloud Storage Backup (videos stored in Google Cloud Storage)

## Changelog

| Date | Change |
|------|--------|
| 2024-12-23 | Initial spec |
| 2024-12-28 | Updated to Gemini 2.0 Flash for video analysis |
| 2025-12-31 | Added shared utilities, section icons |

---

**Implementation Spec:** [Video-Processor-Implementation-Spec.md](Video-Processor-Implementation-Spec.md)

**Last Updated:** December 31, 2025
