# Issue 37, align public relation exports with recent public documents

## Context

The public profile now publishes a bounded `latest` document set. That solved the
2018-only demo problem, but it exposed a consistency issue: the relation harvest
could still scan the first meeting sessions from the source endpoint while
`documents.jsonl` contained the latest documents.

That can lead to this viewer message even when relation files are populated:

```text
250 documenten geladen. Relationele context: 187 vergaderingen, 1000 agendapunten. 0 getoonde documenten hebben een koppeling.
```

The relation files exist, but their document identifiers do not overlap with the
current public documents.

## Change

This PR step keeps the public export internally consistent:

- latest document harvests use the latest meeting-session window for relation harvesting
- public relation exports are filtered to relations that overlap with `documents.jsonl`
- `meetings.jsonl` and `meeting_items.jsonl` are reduced to the meetings and items referenced by those remaining relations
- `latest.json` gets a `relations_publication_summary` block that separates raw relation harvest counts from published relation counts
- the viewer matches relation records on multiple document identifiers instead of only `document_id`

## Expected latest.json shape

```json
{
  "relations_summary": {
    "meeting_session_scan_mode": "latest",
    "meetings_seen": 187,
    "meeting_items_seen": 1000,
    "meeting_document_relations_seen": 188,
    "meeting_item_document_relations_seen": 818
  },
  "relations_publication_summary": {
    "documents_published": 250,
    "documents_with_published_relations": 42,
    "raw_meetings_seen": 187,
    "raw_meeting_items_seen": 1000,
    "raw_meeting_document_relations_seen": 188,
    "raw_meeting_item_document_relations_seen": 818,
    "published_meetings": 25,
    "published_meeting_items": 40,
    "published_meeting_document_relations": 12,
    "published_meeting_item_document_relations": 60
  }
}
```

Numbers are examples. The important part is that raw harvest counts and published
overlap counts are both visible.

## Out of scope

- full historical backfill
- scheduled harvests
- agenda browser UI
- document type normalization
- quality reporting dashboard
