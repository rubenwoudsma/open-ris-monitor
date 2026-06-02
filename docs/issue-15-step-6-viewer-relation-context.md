# Issue #15 step 6, viewer relation context

This step adds minimal relation-aware rendering to the static viewer.

## Scope

The viewer now optionally loads:

- `meetings.jsonl`
- `meeting_items.jsonl`
- `meeting_documents.jsonl`
- `meeting_item_documents.jsonl`

It builds lookup tables by canonical document ID and shows meeting and meeting-item context inside the existing document table.

## Design choices

- The viewer remains static and frameworkless.
- Relation exports are optional. Missing relation files do not break the document viewer.
- Documents without relations are rendered normally.
- The existing table structure is preserved.
- Relation context is rendered in the title column to avoid a larger UI redesign.

## Validation

Manual validation:

1. Open the GitHub Pages viewer.
2. Confirm the document table still loads.
3. Search for a document known to have meeting-item relations.
4. Confirm the title column shows meeting and agenda item context.
5. Confirm documents without relation context still render normally.

