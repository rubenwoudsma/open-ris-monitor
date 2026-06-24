# Open RIS Monitor

[![Validate](https://github.com/rubenwoudsma/open-ris-monitor/actions/workflows/validate.yml/badge.svg)](https://github.com/rubenwoudsma/open-ris-monitor/actions/workflows/validate.yml)
[![Harvest](https://github.com/rubenwoudsma/open-ris-monitor/actions/workflows/harvest.yml/badge.svg)](https://github.com/rubenwoudsma/open-ris-monitor/actions/workflows/harvest.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](pyproject.toml)

Open RIS Monitor is a small, reproducible open-data pipeline and static viewer for public municipal council information from a RIS [Raadsinformatiesysteem]. It harvests public source metadata, normalizes it into compact JSONL files, builds context between documents, meetings and agenda items, and publishes the result as a static GitHub Pages site.

Reference implementation: **Gemeente Huizen**, using the **GemeenteOplossingen** API.

Live viewer:

```text
https://rubenwoudsma.github.io/open-ris-monitor/site/index.html
```

Current release status: **MVP 1.1**. The project now includes document, meeting, agenda-item and council organisation context while preserving the original static, no-backend architecture.

## Why this exists

Municipal council information is public, but it is often hard to reuse. Documents may be spread across meetings, agenda items and vendor-specific APIs. A citizen, journalist, council member or civic-tech developer may be able to download individual PDFs, but still miss the context around those documents:

- which meeting a document belongs to;
- which agenda item it was used for;
- whether the document has versions;
- when the dataset was last refreshed;
- how the council organisation is structured.

Open RIS Monitor focuses on that practical gap. It turns public RIS metadata into a predictable, inspectable and forkable static dataset.

## What it does

The project uses a deliberately small pipeline:

```text
source RIS API
-> harvest
-> normalization
-> relation building
-> JSONL exports
-> static site
-> GitHub Pages
```

There is no runtime server and no database. The generated files are the public data contract. The viewer reads those files directly in the browser.

The Huizen reference deployment currently supports:

- GemeenteOplossingen API harvesting;
- `quick`, `public`, `backfill` and `full` harvest profiles;
- document metadata normalization;
- document type cleanup and fallback labels;
- document version metadata when checksum enrichment is enabled;
- meeting and agenda-item exports;
- document-to-meeting and document-to-agenda-item relation exports;
- dataset freshness metadata in `latest.json`;
- basic quality reports under `data/public/quality/`;
- public organisation exports for groups, persons, roles, positions and group memberships;
- a static viewer for documents, meetings and organisation context;
- client-side search and filtering;
- GitHub Actions based validation and scheduled harvesting.

## Viewer features

The static viewer provides three main entry points:

### Documents

The document view is the primary entry point. It supports searching, filtering, sorting and opening document details. Where the source data exposes enough context, documents link back to related meetings and agenda items.

### Meetings

The meetings view shows council meetings and agenda context. It includes filtering for past/current and future meetings, so upcoming meetings do not obscure historical results.

### Organisation

The organisation view provides civic context for the council organisation. It shows groups, people, roles and positions using public RIS organisation endpoints. It is intended as a lightweight overview, not as a political profile directory.

The organisation view focuses on:

- council groups, especially fractions;
- council members;
- fraction chairs;
- the mayor or council chair role where exposed by the RIS API;
- committee members;
- the griffie as council support;
- active and inactive positions;
- group memberships where the public API exposes them.

The organisation export does not enrich, scrape or infer extra personal data. Nested user-management metadata from the RIS API is deliberately excluded.

## What it deliberately does not do

Open RIS Monitor is not intended to become:

- a national portal;
- a SaaS platform;
- a central aggregator;
- an OCR platform;
- a PDF archive;
- a notification service;
- a generic enterprise data platform;
- a political profiling tool.

The project does not store PDFs in Git. PDF files may be downloaded temporarily during a workflow for checksum metadata, then discarded.

## Design principles

- static site only;
- GitHub Pages deployment;
- no backend;
- no database;
- no PDF storage in Git;
- compact JSONL exports;
- document-first design;
- municipality-specific deployments;
- forkable architecture;
- reproducible GitHub Actions workflows;
- conservative public data publication.

## Public data exports

The public dataset is written to `data/public/`. Important files include:

```text
data/public/documents.jsonl
data/public/document_versions.jsonl
data/public/harvest_runs.jsonl
data/public/meetings.jsonl
data/public/meeting_items.jsonl
data/public/meeting_documents.jsonl
data/public/meeting_item_documents.jsonl
data/public/organization_groups.jsonl
data/public/organization_persons.jsonl
data/public/organization_roles.jsonl
data/public/organization_positions.jsonl
data/public/organization_group_memberships.jsonl
data/public/latest.json
data/public/quality/summary.json
data/public/quality/issues.jsonl
```

`latest.json` is the operational summary for the current public dataset. It records the municipality, generation timestamp, run profile, output files, relation status, organisation status and dataset totals.

## Harvest profiles and cadence

The repository supports multiple harvest profiles:

- `quick`, for a small local smoke test;
- `public`, for the regular public update flow;
- `backfill`, for broader public refreshes and organisation refreshes;
- `full`, for complete or more expensive harvesting when explicitly needed.

The intended operational pattern is:

- run the public harvest regularly for document and meeting updates;
- run a backfill manually or on a monthly schedule for broader refreshes;
- refresh organisation data through the backfill flow because council organisation data changes less frequently than documents and agendas.

## Quick start for developers

Requirements:

- Python 3.11 or newer;
- Git;
- access to the public GemeenteOplossingen API endpoint for the target municipality.

Install locally:

```bash
python -m pip install --upgrade pip
python -m pip install -e .[dev]
```

Run tests and linting:

```bash
python -m pytest
ruff check .
```

Run a small local smoke test:

```bash
python -m open_ris_monitor.pipeline.run \
  --municipality huizen \
  --profile quick
```

Run a bounded public-style harvest:

```bash
python -m open_ris_monitor.pipeline.run \
  --municipality huizen \
  --profile public \
  --max-documents 100 \
  --meeting-scan-limit 100
```

Run a backfill profile, including organisation data when configured by the profile:

```bash
python -m open_ris_monitor.pipeline.run \
  --municipality huizen \
  --profile backfill
```

Validate public exports:

```bash
python -m open_ris_monitor.exporters.validate_exports
```

Generate quality reports:

```bash
python -m open_ris_monitor.analysis.generate_public_reports \
  --public-dir data/public
```

Build or validate the static frontend where applicable:

```bash
npx tsc -p tsconfig.json
```

## GitHub Actions operation

The reference deployment uses GitHub Actions for validation, harvesting and publication. Manual harvest runs can be started from the GitHub Actions UI.

For a normal manual public refresh, use the public profile and commit public output when appropriate.

For an organisation refresh, use the backfill profile and commit public output when appropriate. This keeps organisation harvesting out of the daily flow while still making it easy to refresh when council membership changes.

## Adopting another municipality

For another municipality using GemeenteOplossingen, the intended path is:

1. fork the repository;
2. add a municipality profile under `config/municipalities/`;
3. run a quick or bounded test harvest;
4. validate the output;
5. enable GitHub Actions;
6. enable GitHub Pages.

For another RIS vendor, code changes are likely required. The project currently has a proven GemeenteOplossingen implementation, not a fully generic multi-vendor connector framework.

Start with:

- [Adding a municipality](docs/adding-a-municipality.md)
- [Connectors](docs/connectors.md)

## Documentation index

- [Architecture](docs/architecture.md), pipeline shape and design constraints.
- [Data model](docs/data-model.md), canonical entities, identifiers and relations.
- [Export contract](docs/export-contract.md), public JSONL and metadata contract.
- [Harvesting](docs/harvesting.md), profiles, cadence, retries and recovery.
- [Quality](docs/quality.md), freshness, health and report interpretation.
- [Adding a municipality](docs/adding-a-municipality.md), practical onboarding guide for forks.
- [Connectors](docs/connectors.md), current GemeenteOplossingen connector and future vendor expectations.
- [Development](docs/development.md), local development and PR hygiene.
- [Validation and CI](docs/validatie-ci.md), checks run by GitHub Actions.
- [Roadmap](docs/roadmap.md), conservative MVP and post-MVP direction.

## Repository policy

Commit source code, configuration, documentation and approved public exports only.

Do not commit:

- `data/raw/`;
- downloaded PDFs;
- temporary caches;
- local virtual environments;
- generated diagnostics outside the documented public output paths.

## Current MVP status

Open RIS Monitor is live as an MVP 1.1 reference implementation for Gemeente Huizen.

The project now demonstrates the full intended shape:

- public RIS harvesting;
- normalized document metadata;
- meeting and agenda context;
- relation exports;
- dataset freshness metadata;
- organisation context;
- static viewer;
- GitHub Actions based publication;
- no backend and no database.

Future work should remain conservative and should protect the small static architecture. Suitable next improvements include export contract hardening, release governance, documentation polish and small usability improvements.

## License

This repository declares an MIT license. Verify that the `LICENSE` file contains the complete final license text before depending on the license statement for redistribution.
