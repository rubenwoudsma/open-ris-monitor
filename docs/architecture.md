# Architecture

Open RIS Monitor is a small static open-data pipeline for municipal council information. The core product is not a backend service. The core product is the reproducible data chain from public RIS source data to compact public files and a static viewer.

## Pipeline

```text
source RIS API
-> harvest
-> normalization
-> relation building
-> JSONL exports
-> static site
-> GitHub Pages
```

The Huizen reference implementation currently uses the GemeenteOplossingen API.

## System layers

```text
+------------------------------------------------------+
| Static viewer                                        |
| site/, client-side HTML, CSS and JavaScript          |
+------------------------------------------------------+
                         ^
                         |
+------------------------------------------------------+
| Public data layer                                    |
| data/public/*.jsonl, latest.json, quality reports    |
+------------------------------------------------------+
                         ^
                         |
+------------------------------------------------------+
| Export and validation layer                          |
| JSONL writers, schema/integrity checks, summaries    |
+------------------------------------------------------+
                         ^
                         |
+------------------------------------------------------+
| Canonical model and relations                        |
| documents, meetings, meeting items, relations        |
+------------------------------------------------------+
                         ^
                         |
+------------------------------------------------------+
| Normalization layer                                  |
| vendor-shaped raw records to canonical records       |
+------------------------------------------------------+
                         ^
                         |
+------------------------------------------------------+
| Connector layer                                      |
| GemeenteOplossingen API, future vendors later        |
+------------------------------------------------------+
```

## Design constraints

- static site only;
- GitHub Pages deployment;
- no backend;
- no database;
- no PDF storage in Git;
- compact JSONL exports;
- document-first design;
- municipality-specific deployments;
- forkable architecture;
- reproducible GitHub Actions workflows.

These constraints are part of the architecture, not temporary limitations.

## Source connector boundary

A connector talks to a vendor API and retrieves raw source records. The rest of the system should not depend on vendor-specific field names or route shapes.

The current proven connector path is GemeenteOplossingen. See `docs/connectors.md` for connector responsibilities and current route knowledge.

## Normalization boundary

Normalization converts raw vendor objects into canonical Open RIS Monitor records. This is where source-specific names such as `documentTypeLabel`, `objectId` or `meetingItemId` are mapped into stable public concepts such as document type, source ID and relation target.

The source may be messy. The canonical model should be stable, defensive and honest about missing data.

## Relation building

The project is document-first, but documents become more useful when linked to the meeting and agenda context where they were used.

The relation builder uses source routes such as meeting documents and meeting-item documents to create public relation exports. It should not invent relations that are not supported by source data.

Known source variation is expected. For example, a future or historical meeting may not resolve through every meeting detail route. That should be handled as source variation when other useful public data can still be harvested.

## Public data layer

The public data layer is the read-only contract consumed by the static viewer and potential downstream users.

Typical public outputs:

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

`latest.json` acts as the operational manifest for the latest generated dataset.

## Static viewer

The viewer under `site/` reads public files directly from GitHub Pages. Search, filtering, sorting and detail rendering happen in the browser.

The viewer must be defensive. Missing titles, malformed dates or absent relations should not result in a blank page. Upstream data quality issues should be visible or gracefully skipped, not crash the UI.

## GitHub Actions

GitHub Actions runs validation and harvesting.

- `.github/workflows/validate.yml` runs tests, linting and export integrity validation.
- `.github/workflows/harvest.yml` runs scheduled and manual harvests, generates quality reports, validates public output and optionally commits `data/public/`.

The harvest workflow uses concurrency so two harvests on the same branch do not publish over each other.

## Why no backend and no database

The project is designed for low-maintenance civic open source. A static repository is easier to fork, inspect, mirror and preserve than a hosted application with runtime infrastructure.

The trade-off is intentional:

- data is refreshed by workflow runs, not live queries;
- search is client-side;
- datasets must stay compact;
- public files must remain stable and validated.

## Related documentation

- `docs/data-model.md`
- `docs/export-contract.md`
- `docs/harvesting.md`
- `docs/connectors.md`
- `docs/quality.md`
