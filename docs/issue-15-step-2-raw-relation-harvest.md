# Issue #15, step 2, raw relation harvest

This step adds a bounded raw relation harvest on top of the meeting endpoint connector methods from step 1.

## Added

- `open_ris_monitor.pipeline.relations`
- extraction of meeting IDs from `meetingsessions[].container.meeting.id`
- stable deduplication of candidate meeting IDs
- bounded meetingsession pagination
- optional raw relation harvest through `--include-relations`
- raw artifact output under `data/raw/latest/`

## Raw artifacts

When `--include-relations` is enabled, the pipeline writes:

- `data/raw/latest/meetingsessions.json`
- `data/raw/latest/meeting_ids.json`
- `data/raw/latest/meetings.json`
- `data/raw/latest/meeting_items.json`
- `data/raw/latest/meeting_documents.json`
- `data/raw/latest/meeting_item_documents.json`
- `data/raw/latest/relation_harvest_summary.json`

These files are intentionally raw inspection artifacts. Canonical public JSONL exports are planned for a later step in issue #15.

## Example command

```bash
python -m open_ris_monitor.pipeline.run \
  --municipality huizen \
  --mode latest \
  --limit 10 \
  --include-relations \
  --meeting-scan-limit 50 \
  --meeting-item-limit 200
```

## Design notes

- The document-first harvest remains the default.
- Relation harvesting is opt-in through `--include-relations`.
- Missing meeting detail routes are handled by the connector from step 1, where `fetch_meeting()` returns `None` for 404 responses.
- This step does not add canonical `Meeting`, `MeetingItem` or relation models yet.
- This step does not add public relation JSONL exports yet.
