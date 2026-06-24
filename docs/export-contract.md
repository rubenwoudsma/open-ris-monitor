# Export contract

The export contract is the boundary between the harvest pipeline, the static viewer and downstream users. Since Open RIS Monitor has no database or backend, the public files are the contract.

## Public output location

Public exports are written under:

```text
data/public/
```

Typical files:

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

Raw source files, PDFs and temporary downloads are not part of the public export contract.

## Format

Most public datasets are JSON Lines files. Each non-empty line is one JSON object.

```text
one object per line
UTF-8
no surrounding array
```

`latest.json` and compact quality summaries are normal JSON files.

## Schema versioning

Canonical public records should include:

```json
"schema_version": "1.0.0"
```

Use semantic versioning for the public contract:

| Version part | Meaning |
|---|---|
| MAJOR | Breaking structural change. |
| MINOR | Backward-compatible optional fields or non-breaking additions. |
| PATCH | Clarifications, documentation or validation corrections. |

If a legacy file is missing `schema_version`, treat that as a pre-1.0 compatibility concern and document it in the PR that changes the export.

## Compatibility policy

For MVP 1.0:

- do not remove public fields without a major version change;
- prefer adding optional fields over changing existing field meaning;
- keep stable identifiers stable;
- preserve source identifiers separately from canonical identifiers;
- keep relation direction documented;
- validate JSONL before publishing;
- fail closed when outputs are empty or structurally invalid.

## `latest.json`

`latest.json` is the operational manifest for the current generated dataset. It should be safe for the viewer and maintainers to read first.

Expected information includes:

- municipality slug and name;
- generated timestamp;
- harvest profile or run type;
- relation harvesting status;
- output file paths;
- document, meeting and relation totals;
- latest-run counts;
- quality summary location;
- latest successful full or backfill timestamp when available.

Do not treat a successful `latest` run as proof that the complete historical dataset was rebuilt. A `latest` run may update recent records while preserving the broader public dataset.

## Core JSONL exports

### `documents.jsonl`

Canonical public document metadata. It should include stable canonical ID, source ID, title, description, document type, filename, publication date, source URL, download URL when public, confidentiality flag and municipality context.

### `document_versions.jsonl`

Observed version or checksum metadata. It exists when checksum enrichment is enabled or when version tracking has been generated. It must not imply that PDFs are stored in Git.

### `harvest_runs.jsonl`

Operational run records, including timestamps, status, profile and counts.

### `meetings.jsonl`

Canonical meeting context where the source provides usable meeting data.

### `meeting_items.jsonl`

Agenda or meeting item context where the source provides usable meeting-item data.

### `meeting_documents.jsonl`

Relations between meetings and documents.

### `meeting_item_documents.jsonl`

Relations between meeting items and documents.

## Quality outputs

Quality outputs live under:

```text
data/public/quality/
```

They provide dataset health signals, not a separate product. They are intended to help maintainers and the viewer interpret completeness, freshness and relation coverage.

## Validation expectations

Validation should check:

- `latest.json` is valid JSON;
- JSONL files contain valid JSON per line;
- output files referenced by `latest.json` exist;
- required relational exports exist for normal public runs;
- no generated public dataset is unexpectedly empty;
- relation references point to known records where that check is implemented;
- no PDFs are present in public output.

## Breaking changes

A change is breaking when it removes fields, changes field meaning, changes identifier format, changes relation direction, moves public file paths or changes JSONL into another format.

Breaking changes should be avoided before v1.0 unless needed to stabilize the contract.

## Related documentation

- [data-model.md](data-model.md)
- [harvesting.md](harvesting.md)
- [quality.md](quality.md)
- [validatie-ci.md](validatie-ci.md)

## MVP 1.1 organisation exports

MVP 1.1 adds optional public organisation exports for civic context. These files are generated from the public GO/Open Raadsinformatie organisation endpoints and are expected to change slowly. The monthly backfill profile includes them by default, while daily latest harvests preserve existing organisation output references when the files already exist.

New optional files under `data/public/`:

- `organization_groups.jsonl`, groups such as `fractie`, `commissie`, `orgaan` and unknown or other types;
- `organization_persons.jsonl`, public person fields only, including name parts, display name, public email and active status;
- `organization_roles.jsonl`, roles and a conservative `role_category` for UI grouping;
- `organization_positions.jsonl`, person-role positions with start date, end date and active flag where derivable;
- `organization_group_memberships.jsonl`, grounded group membership from `/groups/{groupId}/persons` when available.

The public person export deliberately excludes nested `user` metadata such as `usermanagementId`. The organisation view must not infer party or group membership from names or role labels. It may only use relations present in the API payloads.
