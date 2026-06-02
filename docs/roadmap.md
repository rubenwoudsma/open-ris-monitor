# Roadmap

## Completed

- Document-first harvest for Huizen
- Canonical document exports
- GitHub Pages viewer
- Automatic `data/public` updates after harvest
- Paginated full document harvest with `latest` and `full` modes
- Document versions and checksum metadata
- #14 Research meetings and agenda-items endpoints
- #15 Step 1: GemeenteOplossingen meeting relation endpoints
- #15 Step 2: Optional raw meeting relation harvest
- #15 Step 3: Canonical meeting relation normalization
- #15 Step 4: Public meeting relation exports

## Current milestone, issue #15

Link documents to meetings and agenda items.

Implemented foundation:

- meeting harvest based on `/meetingsessions` and `/meetings/{meetingId}`
- meeting item harvest based on `/meetings/{meetingId}/meetingitems`
- meeting-level document relations based on `/meetings/{meetingId}/documents`
- meeting-item-level document relations based on `/meetingitems/{meetingItemId}/documents`
- canonical `Meeting` records
- canonical `MeetingItem` records
- canonical `MeetingDocumentRelation` records
- canonical `MeetingItemDocumentRelation` records
- public exports for meetings, meeting items and relations
- `latest.json` pointers to relation exports
- relation harvest summary counters

Remaining within issue #15:

- update documentation and operational guidance
- decide whether temporary smoke workflows should be removed before merge
- optionally add minimal viewer support for relation context
- open PR with clear scope and validation notes

Out of scope for this milestone:

- PDF archiving
- OCR
- text extraction
- AI summaries
- full agenda viewer redesign
- complete support for all RIS vendors
- perfect historical completeness in a single workflow run

## Upcoming

### #13 Add quality reporting

Quality reporting should use the relation layer. Examples:

- document without meeting relation
- meeting without meeting items
- meeting item without documents
- relation pointing to a missing document
- relation pointing to a missing meeting item
- suspicious duplicate relation
- confidential source records that leak into public exports

### #21 Normalize document types

Document type normalization should use both the source document type and relation context. For example, a document labelled `Bijlage` may be more meaningful when attached to a specific agenda item.

### Viewer improvement

Short-term viewer goal:

- show linked meeting context on a document detail row or panel
- show linked meeting item context where available
- keep the viewer static and frameworkless

Later viewer goals:

- meeting browser
- agenda item browser
- relation-aware filters
- downloadable subsets
- search index generated from public JSONL

### Operational harvest strategy

Build toward full historical coverage through bounded, resumable harvests:

- small daily latest harvests
- scheduled relation refreshes
- bounded full harvest windows
- backfill by meeting session range or offset window
- no raw or PDF archive in Git
- compact public JSONL exports only

See `docs/operations-harvest-strategy.md`.

### Multi-source support

After the GemeenteOplossingen implementation stabilizes:

- document a connector interface for other RIS suppliers
- add supplier capability flags
- distinguish source endpoints from canonical output
- keep public exports stable across suppliers
