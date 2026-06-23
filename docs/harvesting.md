# Harvesting

This document describes how Open RIS Monitor harvests, normalizes and publishes public council information for the Huizen reference implementation.

Open RIS Monitor remains deliberately lightweight:

- static site only;
- no backend;
- no database;
- no PDF storage in Git;
- compact JSONL publication;
- reproducible GitHub Actions workflows.

## Source basis

The Huizen implementation uses the GemeenteOplossingen API.

Base URL:

```text
https://ris.gemeenteraadhuizen.nl/api/v2/
```

Important document routes:

```text
GET /documents?limit={limit}&offset={offset}
GET /documents/{documentId}
GET /documents/{documentId}/download
```

PDF files are not stored in Git. Downloads may be used temporarily for derived metadata, such as checksums, after which only compact metadata is kept.

## Proven route groups

Useful GemeenteOplossingen route groups include:

```text
/documents
/meetings
/dmus
/events
/meetingsessions
```

Useful nested relation routes include:

```text
/meetings/{meetingId}
/meetings/{meetingId}/documents
/meetings/{meetingId}/meetingitems
/meetingitems/{meetingItemId}
/meetingitems/{meetingItemId}/documents
```

## Relation discovery

The working relation chain is:

```text
/meetingsessions -> container.meeting.id -> /meetings/{meetingId} -> /meetings/{meetingId}/meetingitems -> /meetings/{meetingId}/documents -> /meetingitems/{meetingItemId}/documents
```

Important observations:

- `/meetingsessions` can be needed for historical coverage;
- `/meetings` can be useful for recent or future meetings;
- not every meeting ID resolves through every detail route;
- a 404 on a meeting detail route can be source variation and should not always fail the harvest;
- meeting items can provide enough fields for agenda context;
- documents can be linked at meeting level and meeting-item level.

## Harvest profiles

The CLI supports operational profiles with `--profile`.

| Profile | Purpose | Typical use | Publication behavior |
|---|---|---|---|
| `quick` | Smoke test and diagnostics | Local checks, small CI-like verification | Not intended as normal publication source. |
| `public` | Regular public dataset update | Scheduled daily harvest and normal manual update | Publishes `data/public/`. |
| `backfill` | Historical filling or recovery | Monthly scheduled backfill, manual workflow dispatch or local controlled run | Use deliberately because it can process a much larger source window. |

All normal public profiles are expected to include relation exports unless a diagnostic flag disables them.

## Important public outputs

```text
data/public/documents.jsonl
data/public/document_versions.jsonl
data/public/harvest_runs.jsonl
data/public/meetings.jsonl
data/public/meeting_items.jsonl
data/public/meeting_documents.jsonl
data/public/meeting_item_documents.jsonl
data/public/latest.json
data/public/quality/summary.json
data/public/quality/issues.jsonl
```

`latest.json` is the operational manifest for the latest generated public dataset. It should contain output paths, totals, generation timestamp, relation status and run profile information.

## Latest, public and backfill

Use `quick` for fast local confidence.

Use `public` for the live dataset. Scheduled daily GitHub Actions runs use this profile.

Use `backfill` for initial historical loading, controlled historical extension, recovery after a longer gap or the monthly scheduled full refresh.

Do not schedule daily backfills. A `latest` or recent-window style run must not shrink the full public dataset accidentally. The intended behavior is to update recent information while preserving the broader public output unless a full or backfill run is deliberately performed.

## Cadence policy

The standard operational cadence is:

```text
daily public harvest
monthly full/backfill harvest
manual backfill when needed
```

Recommended scheduled crons for the Huizen reference implementation:

```text
23 3 * * *
41 3 1 * *
```

The first schedule runs the daily public refresh around 03:23 UTC. The second schedule runs a monthly backfill on the first day of the month around 03:41 UTC.

The non-hourly minutes are intentional. They reduce the chance that multiple forks hit the same upstream API at the exact same time.

Hourly harvesting is not the default because municipal council information generally does not change hourly, while hourly runs increase GitHub Actions usage and upstream API pressure. Weekly harvesting is not ideal as a default because agendas and documents can still change in the days before a meeting.

Forks should choose their own non-hourly minute for both schedules. Good random minutes include:

```text
17, 23, 41 or 52
```

## GitHub Actions workflow

The harvest workflow lives at:

```text
.github/workflows/harvest.yml
```

It supports:

1. scheduled daily public runs;
2. scheduled monthly backfill runs;
3. manual `workflow_dispatch` runs.

Scheduled runs are resolved inside the workflow:

| Trigger | Profile | Publication |
|---|---|---|
| `23 3 * * *` | `public` | commits `data/public/` |
| `41 3 1 * *` | `backfill` | commits `data/public/` |

Manual runs can be used for quick tests, public recovery runs or backfills. Manual publication remains opt-in through `commit_public`.

## Manual workflow inputs

Typical inputs:

| Input | Purpose | Typical value |
|---|---|---|
| `municipality` | Municipality profile slug | `huizen` |
| `profile` | Harvest profile | `quick`, `public`, `backfill` |
| `mode` | Optional explicit override for profile mode | empty, `latest`, `full` |
| `limit` | Optional explicit latest limit | empty or `25` |
| `batch_size` | Optional explicit full batch size | empty or `100` |
| `max_documents` | Optional explicit full limit | empty for profile default |
| `enrich_checksums` | Temporarily download selected PDFs for checksums | `false` |
| `checksum_max_documents` | Maximum checksum-enriched documents | `50` |
| `commit_public` | Commit generated `data/public/` output | `false` for manual tests, `true` for intentional publication |

## Concurrency

The harvest workflow uses concurrency to avoid two harvests publishing over each other on the same branch.

Policy intent:

```text
cancel-in-progress: false
```

A second run should wait or avoid parallel publication rather than interrupting a run midway.

## Retry and back-off policy

The connector should retry temporary upstream problems with limited exponential back-off.

Retryable examples:

```text
408 Request Timeout
429 Too Many Requests
500 Internal Server Error
502 Bad Gateway
503 Service Unavailable
504 Gateway Timeout
connect timeout
read timeout
temporary network failures
```

If the upstream returns `Retry-After`, respect it.

Do not blindly retry normal client errors:

```text
400 Bad Request
401 Unauthorized
403 Forbidden
404 Not Found
```

Exception: a 404 on a meeting detail route can be source variation during relation harvesting. That should be handled without failing the entire harvest when other useful data remains available.

## Stop criteria

A harvest stops when:

1. the profile window or configured limits are processed;
2. explicit CLI limits are reached;
3. the upstream returns no more records;
4. a non-recoverable connector error occurs;
5. export validation or integrity validation fails.

Explicit CLI parameters should override profile defaults. This makes bounded runs possible without creating new profiles.

Example:

```bash
python -m open_ris_monitor.pipeline.run \
  --municipality huizen \
  --profile public \
  --max-documents 100 \
  --meeting-scan-limit 100
```

## Failure policy

The pipeline should fail closed.

That means:

- an upstream outage must not produce a successful empty publication;
- a zero-record dataset is not a valid success when records are expected;
- invalid JSONL or schema-incompatible output must not be published;
- the previous successful publication remains the public reference after a failure;
- the GitHub Action should fail visibly so maintainers can act.

## Success criteria

A harvest is successful when:

1. the run ends without non-recoverable connector errors;
2. public JSONL files are generated;
3. `data/public/latest.json` exists;
4. `latest.json` references existing output files;
5. relational exports are present for normal public runs;
6. quality reports are generated;
7. export validation succeeds;
8. no PDF files are included in public output;
9. scheduled runs commit only allowed public output.

## Commit policy

Allowed:

```text
data/public/
```

Not allowed:

```text
data/raw/
*.pdf
large temporary downloads
local caches
```

Raw harvest output may be uploaded as a short-lived GitHub Actions artifact, but should not be stored as permanent Git data.

## Recovery policy

After a failed scheduled run:

1. inspect the GitHub Actions logs;
2. determine whether it is upstream outage, rate limiting, validation failure or code failure;
3. run `quick` manually to test the connector;
4. run `public` manually if the source is healthy;
5. use `backfill` when a longer period must be rebuilt.

Run a manual backfill when:

- a scheduled monthly backfill failed and the upstream source is healthy again;
- a longer outage left gaps in the public dataset;
- a new relation-harvest improvement needs to rebuild historical coverage;
- a new municipality fork is seeded for the first time.

Do not overwrite a healthy historical dataset with a failing or empty run.

## Forking policy

Forks can reuse the same workflow when:

- a municipality profile exists under `config/municipalities/`;
- the connector supports the needed source routes;
- the fork chooses its own GitHub Actions schedules;
- the cron uses a non-hourly minute.

Recommended random minutes for forks:

```text
17, 23, 41 or 52
```

## Related documentation

- [connectors.md](connectors.md)
- [adding-a-municipality.md](adding-a-municipality.md)
- [export-contract.md](export-contract.md)
- [quality.md](quality.md)
- [validatie-ci.md](validatie-ci.md)
