# Quality

Open RIS Monitor publishes a compact quality layer next to the public dataset. The goal is to make dataset freshness, completeness and relation consistency easier to inspect.

The quality layer is intentionally modest. It is not a full observability platform and not a health scoring product.

## Public quality outputs

Quality reports are written under:

```text
data/public/quality/
```

Expected files can include:

```text
data/public/quality/summary.json
data/public/quality/issues.jsonl
data/public/quality/document_types.json
data/public/quality/id_stability.json
```

The exact set can evolve, but `summary.json` and `issues.jsonl` are the main files for MVP-level interpretation.

## What quality checks cover

The current quality layer focuses on:

- dataset totals;
- latest harvest status;
- generated timestamp and freshness metadata;
- document type distribution;
- unknown or fallback document types;
- relation coverage between documents, meetings and meeting items;
- referential integrity where relation targets are known;
- meetings without agenda items;
- agenda items without documents;
- unexpected drops in counts when detectable.

## Dataset freshness

Freshness answers the question: how recently was the public dataset generated?

The viewer and maintainers should use `data/public/latest.json` first. It should contain the generated timestamp and run context for the latest public output.

A fresh `latest.json` does not always mean a full historical backfill just ran. It may represent a daily public update that preserves a broader existing dataset.

## Dataset totals

Dataset totals help identify obvious problems:

- documents;
- document versions;
- harvest runs;
- meetings;
- meeting items;
- document-to-meeting relations;
- document-to-meeting-item relations.

Totals should be interpreted relative to harvest profile and configured limits. A bounded test run will naturally have smaller counts than a full or backfill run.

## Relation coverage

Relation coverage shows how many documents are linked to meeting or agenda context.

Missing relations can mean several different things:

- the document is genuinely not linked by the source;
- the meeting is planned and not complete yet;
- the source exposes the link through another route;
- the connector did not scan far enough because of configured limits;
- the upstream API returned incomplete data.

A document without relations is a warning signal, not automatically a pipeline failure.

## Document type quality

Document type quality checks whether public labels are useful and stable.

Signals to watch:

- many `unknown` values;
- raw source labels that should have been normalized;
- document type fallback labels increasing unexpectedly;
- types that are too generic to help users filter.

## When quality should fail a run

Warnings can be informative. A run should fail or be treated as unsafe when:

- required public files are missing;
- JSONL is invalid;
- `latest.json` is invalid or references missing files;
- the current output is unexpectedly empty;
- document totals drop sharply without an intentional bounded run;
- relation files reference missing documents, meetings or meeting items;
- the last harvest status is not successful for a scheduled publication.

## Manual quality report command

```bash
python -m open_ris_monitor.analysis.generate_public_reports \
  --public-dir data/public
```

## Interpreting quality reports

Use quality reports as operational evidence, not as a replacement for source review.

For MVP, the most useful questions are:

- Did the harvest run successfully?
- Was the dataset generated recently?
- Are the main export files present?
- Are document counts plausible?
- Are relation counts plausible?
- Are document type labels useful?
- Did validation prevent empty or broken output?

## Related documentation

- `docs/harvesting.md`
- `docs/export-contract.md`
- `docs/validatie-ci.md`
