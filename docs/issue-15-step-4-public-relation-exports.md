# Issue 15, step 4: public relation exports

This step promotes the normalized meeting relation data from internal canonical records to public JSONL exports.

## Added public exports

When `--include-relations` is used, the pipeline now writes:

- `data/public/meetings.jsonl`
- `data/public/meeting_items.jsonl`
- `data/public/meeting_documents.jsonl`
- `data/public/meeting_item_documents.jsonl`

The existing exports remain unchanged:

- `data/public/documents.jsonl`
- `data/public/harvest_runs.jsonl`
- `data/public/document_versions.jsonl`, when checksum enrichment is enabled
- `data/public/latest.json`

## latest.json

The `outputs` block in `latest.json` now includes relation export pointers when relation harvest is enabled.

Example:

```json
{
  "outputs": {
    "documents": "documents.jsonl",
    "harvest_runs": "harvest_runs.jsonl",
    "document_versions": null,
    "meetings": "meetings.jsonl",
    "meeting_items": "meeting_items.jsonl",
    "meeting_documents": "meeting_documents.jsonl",
    "meeting_item_documents": "meeting_item_documents.jsonl"
  }
}
```

## Scope

This step does not add viewer changes, quality reporting, or document type normalization. It only publishes the canonical relation records introduced in step 3.
