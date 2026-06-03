# Issue 37: public harvest robustness for recent document runs

The public profile now prefers recent documents. This makes the public run more useful for demos, but it can also expose more relation endpoint calls than a quick run.

A single transient timeout on a relation endpoint should not fail the whole public harvest. Relation data is enrichment. The core document export should still be published when one meeting, meeting document, meeting item, or meeting item document request fails.

This change records relation endpoint failures in the raw relation harvest result and in the relation summary, while continuing with the remaining bounded relation harvest.

## Behaviour

- Missing meetings that return `None` are still counted as skipped meetings.
- Request timeouts and invalid relation responses for individual relation endpoints are recorded in `relation_errors`.
- A failed meeting fetch skips that meeting and continues with the next candidate meeting.
- A failed meeting document fetch skips only meeting-document relations for that meeting.
- A failed meeting item fetch skips item harvesting for that meeting.
- A failed meeting item document fetch skips only that item-document relation.
- Unexpected programming errors are still raised.

## Validation

Run:

```bash
pytest tests/test_relation_harvest.py
pytest
```

Then run the manual `Publish public RIS data` workflow with:

- `municipality`: `huizen`
- `profile`: `quick`
- `profile`: `public`

The public run may report relation errors in `latest.json` or raw artifact summaries, but a single transient relation timeout should no longer fail the workflow.
