# Roadmap

## Completed

- Document-first harvest for Huizen
- Canonical document exports
- GitHub Pages viewer
- Automatic `data/public` updates after harvest
- Paginated full document harvest with `latest` and `full` modes

## Current milestone, issue #12

Add document versions and checksum metadata.

Scope:

- Temporarily download a limited number of documents during harvest
- Calculate SHA-256 checksums
- Publish `data/public/document_versions.jsonl`
- Preserve existing document versions and add new observations
- Keep PDF files out of Git

Out of scope for this milestone:

- PDF archiving
- OCR
- text extraction
- complete checksum coverage for every historical document by default

## Upcoming

- #13 Add quality reporting
- #14 Research meetings and agenda-items endpoints
- #15 Link documents to meetings and agenda items
- #18 Improve document viewer for larger datasets, completed separately
- #19 Normalize document types
- #22 Research document id and objectId stability
