# Validation and CI

This document describes the automated validation used by Open RIS Monitor.

The filename is kept as `validatie-ci.md` to avoid unnecessary link churn. The content is in English to match the rest of the refreshed documentation set.

## Goal

The static viewer depends on files in `data/public/`. Validation protects the public site and downstream users from broken generated output.

Validation should prevent:

1. invalid JSON or JSONL;
2. missing public output files;
3. `latest.json` references to files that do not exist;
4. empty publications caused by upstream 200 responses with no useful data;
5. accidental replacement of a healthy historical dataset with a broken one;
6. schema or contract drift that the viewer cannot handle.

## GitHub Actions workflows

Main workflows:

```text
.github/workflows/validate.yml
.github/workflows/harvest.yml
```

`validate.yml` is expected to run on pushes and pull requests. It installs the project, runs tests, runs Ruff and validates exports.

`harvest.yml` runs scheduled and manual harvests. It generates public output, generates quality reports, validates the generated public data, uploads artifacts and commits `data/public/` only when configured to do so.

## Local validation commands

Run tests:

```bash
python -m pytest
```

Run Ruff:

```bash
ruff check .
```

Validate exports:

```bash
python -m open_ris_monitor.exporters.validate_exports
```

Validate JSON manually when diagnosing:

```bash
python -m json.tool data/public/latest.json > /tmp/latest.json
```


## What the test suite should cover

The exact test files may evolve, but the validation suite should make the project safe to run as a static public data pipeline. A healthy test set should include these categories.

| Test area | Purpose | Examples |
|---|---|---|
| Normalization tests | Verify that vendor-shaped records become canonical records. | Document titles, document type fallbacks, timestamps, source IDs. |
| Export tests | Verify that JSONL writers produce parseable and contract-aligned records. | Required fields, schema version fields, stable output paths. |
| Relation tests | Verify that document, meeting and agenda relations are built consistently. | Meeting-document links, meeting-item-document links, missing relation handling. |
| Harvest profile tests | Verify that quick, public, bounded and backfill behavior stays intentional. | Date windows, limits, latest-run behavior. |
| Quality tests | Verify that quality summaries and issue records are generated correctly. | Counts, orphan or unlinked records, freshness metadata. |
| Frontend data contract tests | Verify that exported data remains safe for the static viewer. | Missing fields, malformed dates, defensive parsing assumptions. |
| Workflow safety tests | Verify that generated output is not replaced by empty or implausibly small datasets. | Zero-record guard, missing file guard, latest manifest checks. |

These tests do not need to make live requests to the RIS API. Prefer fixtures and small representative examples for normal CI. Live or large harvest checks should remain explicit manual or scheduled operations.

## How to read validation results

When a validation run fails, first classify the failure:

| Failure type | Likely meaning | First check |
|---|---|---|
| Unit test failure | Code behavior changed. | Inspect the failing test name and fixture. |
| Ruff failure | Style, unused import or static code issue. | Run `ruff check .` locally. |
| Export validation failure | Generated public files are missing or malformed. | Inspect `data/public/latest.json` and referenced paths. |
| Empty output failure | Upstream returned no usable records or the harvest window is wrong. | Check harvest profile, date window and source API availability. |
| Link or docs failure, if added later | Documentation references are broken. | Check relative paths from the current Markdown file. |

## Export validation checklist

Validation should check:

- `data/public/latest.json` exists;
- `latest.json` is valid JSON;
- output paths listed in `latest.json` exist;
- required JSONL exports are present for normal public runs;
- every non-empty JSONL line parses as JSON;
- relation exports are present when relations are enabled;
- generated public output contains no PDFs;
- quality reports exist when expected;
- counts are plausible for the selected profile.

## Empty output guard

A source API can fail in a way that still returns HTTP 200. A schema-only validation may not catch that. Validation should also guard against zero-record or sharply reduced output when records are expected.

The policy is fail closed:

```text
invalid output -> fail the workflow -> keep previous successful public dataset
```

## Documentation PR checklist

For documentation-only changes:

- run tests and Ruff when the repository is available locally;
- do not modify harvesting logic;
- do not modify frontend behavior;
- do not commit generated `data/public/` unless the PR intentionally updates data;
- check changed Markdown links;
- ensure badges in [README.md](../README.md) refer to workflows that exist;
- ensure docs do not claim unsupported vendor support.

## Related documentation

- [export-contract.md](export-contract.md)
- [harvesting.md](harvesting.md)
- [quality.md](quality.md)
- [development.md](development.md)
