#### 2. Updated Block Generation

- `parseContentToBlocks()` now splits long paragraphs into multiple paragraph blocks

- `parseMarkdown()` truncates individual rich_text elements to max length

- List items are truncated to prevent overflow

### Consequences

**Positive:**

- Workflow now handles transcripts of any length

- Text splits at word boundaries for readability

- No data loss – all content is preserved across multiple blocks

**Trade-offs:**

- Long transcripts appear as multiple paragraphs within toggles (visually acceptable)

- Slightly more blocks per page for long content

### Related

- ADR-001: Complete Notion Integration

- Notion API Docs: [Block limits](https://developers.notion.com/reference/request-limits#limits-for-property-values)

---

## ADR-003: Error Notification Rules and Email Configuration

**Date:** January 1, 2026

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
## ADR-XXX: [Title]

**Date:** [Date]

**Status:** [Proposed | Accepted | Deprecated | Superseded]

### Context

[What is the issue that we're seeing that is motivating this decision or change?]

### Decision

[What is the change that we're proposing and/or doing?]

### Consequences

[What becomes easier or more difficult to do because of this change?]

### Related

[Links to related documents, code, or other ADRs]
```