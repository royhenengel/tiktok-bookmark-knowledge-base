# Bookmark Knowledge Base - Product Spec

## Goal

Build an AI-powered knowledge management system that automatically processes bookmarked content (videos, articles, links) to generate rich metadata, transcriptions, and structured data for personal knowledge organization.

## Requirements

- Support multiple content sources (TikTok, YouTube, Spotify, webpages)
- Modular architecture: each source has its own processor
- Unified output format across all processors
- Integration with Notion for knowledge storage
- Google Drive for media file storage
- Cost-effective processing (<$0.10 per item target)

## Scope

### In Scope

- Video Processor module (see: [Video-Processor-Product-Spec.md](Video-Processor-Product-Spec.md))
- Webpage Processor module (articles, products, code repos)
- Spotify Podcast Processor
- n8n workflow orchestration
- Google Cloud infrastructure
- Structured JSON output format

### Out of Scope (Future)

- Browser extension for bookmarking
- Mobile app integration
- Full-text search across processed content

## Success Criteria

- Each processor module works independently
- Unified output schema across sources
- Reliable end-to-end processing
- Cost stays within budget
- Extensible architecture for new sources

## Related Specs

- [Video-Processor-Product-Spec.md](Video-Processor-Product-Spec.md) - Video processor details
- [Bookmark-Knowledge-Base-Implementation-Spec.md](Bookmark-Knowledge-Base-Implementation-Spec.md) - Technical implementation

## Implementation Status

- **Repository:** https://github.com/royhenengel/bookmark-knoledge-base
- **Current status:** ✅ End-to-end pipeline working for videos and webpages
- **Processing time:** ~25-30 seconds per video, ~5 seconds per webpage
- **Actual cost:** ~$0.017 per video, ~$0.011 per webpage (target < $0.10)

## Project Status

- **Project Name:** Bookmarks Knowledge Base
- **Status:** 🚀 Active Development
- **Completed:**
  - Phase 1 - TikTok Video Analyzer ✅
  - Webpage Enricher (articles, products, code) ✅
  - Spotify Podcast Processor ✅
  - Full Notion Integration ✅
- **Current Phase:** Maintenance and improvements
- **Next Phase:** YouTube extended support

## Changelog

| Date | Change |
|------|--------|
| 2024-12-23 | Initial spec |
| 2024-12-27 | Completed Notion integration |
| 2024-12-28 | Added webpage-enricher |
| 2024-12-29 | Added Spotify podcast support |
| 2025-12-31 | Added shared utilities, test infrastructure |

---

**Last Updated:** December 31, 2025
