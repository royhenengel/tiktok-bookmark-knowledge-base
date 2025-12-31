# Bookmark Knowledge Base - Implementation Spec

## Overview

AI-powered bookmark knowledge management system. Processes various content types (videos, articles, links) through specialized processors, generating structured metadata for personal knowledge organization. Built with n8n Cloud orchestration and Google Cloud infrastructure.

## Architecture

```
Bookmark Knowledge Base (n8n Orchestration)
    ├── Video Processor (Complete) - TikTok, YouTube, Spotify podcasts
    ├── Webpage Processor (Complete) - Articles, products, code, social
    └── Unified JSON Output → Notion Storage / Google Drive
```

## Components

### Video Processor (Complete)

- **Purpose:** Process video URLs with full metadata extraction
- **Inputs:** TikTok, YouTube, Spotify podcast URLs via webhook
- **Outputs:** Structured JSON with transcription, tags, music, Drive link
- **See:** [Video-Processor-Implementation-Spec.md](Video-Processor-Implementation-Spec.md)

### Webpage Processor (Complete)

- **Purpose:** Process webpage URLs with metadata and AI analysis
- **Inputs:** Article, product, code, social media URLs
- **Outputs:** Title, author, type, reading time, AI summary, price extraction
- **Cloud Function:** `webpage-enricher`

### Spotify Podcast Processor (Complete)

**Date:** December 29, 2025 | **Status:** Implemented (commit 781ea57)

- **Purpose:** Process Spotify podcast episodes with full metadata extraction and transcription
- **Inputs:** Spotify episode URL (open.spotify.com/episode/...)
- **Outputs:** Episode title, description, show info, duration, release date, AI analysis, full transcript
- **APIs Used:** Spotify Web API (Client Credentials), iTunes Search API, RSS feed parsing, AssemblyAI

#### Processing Pipeline

1. **Spotify Web API:** Fetch rich episode metadata (title, description, show name, publisher, duration, release date)
2. **iTunes Search API:** Find podcast RSS feed URL using show name
3. **RSS Feed Parsing:** Locate episode audio URL using fuzzy title matching + duration verification
4. **AssemblyAI Transcription:** Transcribe audio directly from URL (~28 seconds for 26-minute episode)
5. **Gemini AI Analysis:** Generate summary and key insights from transcript

#### Environment Variables

- `SPOTIFY_CLIENT_ID` - Spotify Developer App Client ID
- `SPOTIFY_CLIENT_SECRET` - Spotify Developer App Client Secret
- `ASSEMBLYAI_API_KEY` - AssemblyAI API key for transcription

## Two-Tier Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         n8n Cloud                              │
│  (Orchestration - handles URLs only, no large binaries)        │
└─────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Google Cloud Functions                        │
│  video-enricher: Downloads videos, Gemini analysis, transcription│
│  webpage-enricher: Fetches pages, extracts metadata, AI summary │
└─────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Google Cloud Storage                         │
│  (Temporary storage with public URLs)                          │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

1. Content URL received via webhook/trigger
2. Router determines content type (Video/Webpage/Spotify)
3. Dispatch to appropriate Cloud Function
4. Processor returns unified JSON schema
5. Store in Notion + media files to Google Drive
6. Return confirmation

## Notion Schema

### Database: Resources
**ID:** `2cf4df89-4a69-819f-941c-f3f8703ef620`

### Property vs Page Body Framework

**Use a Property when:**
- You'd filter by it (e.g., "Show all bookmarks from youtube.com")
- You'd sort by it (e.g., "Longest articles first")
- You'd see it in list view
- It's short (under ~200 characters)
- It's structured (numbers, dates, selects)

**Use Page Body when:**
- It's long (transcripts can be 1000+ words)
- You only need it when deep-diving
- It needs formatting (code snippets, line breaks)
- It's reference material

### Properties

| Property | Type | Purpose |
|----------|------|---------|
| Title | title | Bookmark name |
| Link | url | The URL |
| Type | select | Video, Podcast, Website, Document, Social media |
| Status | status | Inbox → To review → Saved |
| AI Summary | rich_text | 2-3 sentence auto-generated summary |
| Domain | rich_text | Extracted from URL (e.g., "tiktok.com") |
| Author | rich_text | Content creator/author name |
| Reading Time | number | Estimated minutes to read |
| Price | number | Product price for shopping bookmarks |
| Topics | relation | Links to Topics DB |
| Project | relation | Links to Projects DB |
| Area | relation | Links to Areas DB |

### Page Body Content

| Content | Purpose |
|---------|---------|
| AI Analysis | Detailed paragraphs about key takeaways |
| Transcript | Video/audio speech-to-text (1000+ words) |
| Visual Analysis | Detailed breakdown of video content |
| Code Snippet | Programming code from dev resources |
| Music Recognition | List of recognized songs from videos |

## Content Type Detection

| Type | URL Patterns |
|------|--------------|
| Video | tiktok.com, youtube.com, vimeo.com, youtu.be |
| Podcast | spotify.com/episode, podcasts.apple.com |
| Social media | twitter.com, x.com, instagram.com, linkedin.com/posts |
| Document | docs.google.com, notion.so |
| Website | Everything else |

## Error Handling

- Each processor handles its own errors independently
- Router returns error if content type not supported
- Failed processing logged for retry
- Partial results still saved when possible
- n8n sends email notification on failures

## Implementation Steps

- [x] Video Processor (TikTok) - Complete
- [x] Notion integration for storing processed content - Complete
- [x] Webpage Processor (articles, products, code) - Complete
- [x] Spotify Podcast Processor - Complete
- [x] Content type router - Complete
- [ ] YouTube Processor (extended support)
- [ ] Browser extension trigger

## Shared Utilities

Centralized validation in `/shared/` module:

| Module | Purpose |
|--------|---------|
| `title_utils.py` | Title validation, 70-char truncation at word boundaries |
| `analysis_utils.py` | Gemini analysis parsing, section icons, validation |

See [shared/README.md](../shared/README.md) for details.

## Testing Strategy

- Test each processor independently
- Verify unified output schema consistency
- End-to-end tests with various content types
- 102 pytest tests covering contracts and validation

```bash
pytest tests/unit/test_error_contracts.py -v
```

## Prerequisites

- n8n Cloud account (https://n8n.io)
- Google Cloud account with billing enabled
- Gemini API key (video analysis)
- AssemblyAI API key (audio transcription)
- ACRCloud account (music recognition)
- Google Drive OAuth2 credentials
- Spotify Developer credentials (for podcasts)

## Future Improvements

- Browser extension for one-click bookmarking
- Mobile app integration
- Full-text search across all processed content
- Auto-categorization into Notion databases

---

**Product Spec:** [Bookmark-Knowledge-Base-Product-Spec.md](Bookmark-Knowledge-Base-Product-Spec.md)

**Last Updated:** December 31, 2025
