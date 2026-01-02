**Status:** Implemented

### Context

The error notification system needed refinement:

1. Email was configured to send to a non-existent address (`roy@royengel.com`)

1. Email sender showed as raw address, not a friendly name

1. Notification triggers were too narrow – some important failures were not being reported

1. AI analysis failures were silently ignored

1. Missing critical content (transcripts, prices, code snippets) went unnoticed

### Decision

#### 1. Email Configuration Updates

<!-- Table not supported -->

#### 2. Enhanced Notification Triggers

Updated `is_error()` function in `tests/unit/test_notification_logic.py`:

<!-- Table not supported -->

#### 3. Error Classification

Errors are classified into tiers:

<!-- Table not supported -->

### Consequences

**Positive:**

- Notifications now arrive at working email address

- Email clearly shows "LifeOS" as sender

- AI failures are now tracked and reported

- Content-specific failures (no transcript, no price, no code) are caught

- Better visibility into processing quality

**Trade-offs:**

- May generate more notifications initially (expected during tuning)

- Some "false positives" for content that genuinely has no transcript/price/code

### Related

- ADR-001: Complete Notion Integration (original error handling)

- n8n Workflow: `Bookmark_Processor` (Send Error Email node)

- Test file: `tests/unit/test_notification_logic.py`

---

## ADR-004: Error Handling Flow Fixes and Resilience

**Date:** January 1, 2026

**Status:** Implemented

### Context

Testing the error notification system revealed several issues in the error handling flow:

1. Error branch bypassed `Normalize Results` node, causing missing `notionPageId`

1. `Detect URL Type` only accepted camelCase `notionPageId`, not snake_case from webhooks

1. `Set Error Status` used wrong property name ("Status" instead of "Sync Status")

1. `Set Error Status` used wrong property type ("status" instead of "select")

1. Nodes in error chain failed silently without propagating data to subsequent nodes

1. Email credentials not persisted after workflow updates

### Decision

#### 1. Rewired Error Flow

- Changed `Call Processor` error output to route through `Normalize Results` instead of directly to `Set Error Status`

- This ensures `notionPageId` and other normalized data is available in error branch

#### 2. Snake Case Support

Updated `Detect URL Type` node to accept both formats:

```javascript
notionPageId = body.pageId || body.notionPageId || body.notion_page_id || null;
```

#### 3. Correct Notion Property

<!-- Table not supported -->

#### 4. Node Resilience

Made error handling nodes continue on failure to prevent cascade failures:

<!-- Table not supported -->

#### 5. Stable Data References

Updated error nodes to reference data from `Has Error?` node instead of previous node:

```javascript
$('Has Error?').item.json.notionPageId
$('Has Error?').item.json.url
$('Has Error?').item.json.error
```

### Consequences

**Positive:**

- Error handling now completes even if individual steps fail

- Notion page gets red callout with error message

- Sync Status correctly set to "Error"

- Email notifications sent via Gmail SMTP

- Workflow accepts both camelCase and snake_case input

**Trade-offs:**

- Some error steps may silently fail (logged but not blocking)

- Email sender shows as user's Gmail (Gmail SMTP limitation)

### Related

- ADR-001: Complete Notion Integration

- ADR-003: Error Notification Rules

- n8n Workflow: `Bookmark_Processor` (ID: DJVhLZKH7YIuvGv8)

---

## ADR Template

Use this template for future ADRs:

```markdown
## ADR-XXX: Title

**Date:** Date

**Status:** Proposed | Accepted | Deprecated | Superseded

### Context

What is the issue that we're seeing that is motivating this decision or change?

### Decision

What is the change that we're proposing and/or doing?

### Consequences

What becomes easier or more difficult to do because of this change?

### Related

Links to related documents, code, or other ADRs
```

> **Last synced:** January 1, 2026 16:30 UTC

This document tracks architectural decisions made during the development of the Bookmark Knowledge Base system.

---

## ADR-001: Complete Notion Integration with Page Body Content and Error Handling

**Date:** December 27, 2025

**Status:** Implemented and deployed (commit 9dd4593)

### Context

The Bookmark_Processor n8n workflow was interrupted during initial implementation, leaving gaps in the Notion integration. The workflow could update page properties but was missing:

1. Page body content (AI Analysis, Transcript, Visual Analysis, Code Snippets, Music Recognition)

1. Sync Status property mapping

1. Error handling with notifications

### Decision

Complete the implementation by adding:

#### 1. Page Body Content Flow – 6 new nodes

<!-- Table not supported -->

#### 2. Error Handling Branch – 6 new nodes

<!-- Table not supported -->

#### 3. Property Mappings

- Added `Sync Status = "Not Synced"` to Build Notion Payload node

### Consequences

**Positive:**

- Workflow now has 22 nodes (up from 10)

- Full enrichment data now appears in Notion page body with proper formatting:

  – AI Analysis (heading + paragraph)