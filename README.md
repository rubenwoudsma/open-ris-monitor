# Open RIS Monitor

[![Validate](https://github.com/rubenwoudsma/open-ris-monitor/actions/workflows/validate.yml/badge.svg)](https://github.com/rubenwoudsma/open-ris-monitor/actions/workflows/validate.yml)
[![Harvest](https://github.com/rubenwoudsma/open-ris-monitor/actions/workflows/harvest.yml/badge.svg)](https://github.com/rubenwoudsma/open-ris-monitor/actions/workflows/harvest.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](pyproject.toml)

Open RIS Monitor is a small, reproducible open-data pipeline for public council information from a municipal RIS. It harvests source metadata, normalizes it into compact public data files, builds document-to-meeting context, and exposes the result through a static GitHub Pages viewer.

Current reference implementation: **Gemeente Huizen**, using the **GemeenteOplossingen** API.

Live viewer:

```text
https://rubenwoudsma.github.io/open-ris-monitor/site/index.html
```

## Problem

Municipal council information is public, but it is often difficult to reuse. Documents can be spread across meetings, agenda items and vendor-specific APIs. A citizen, journalist, council member or civic-tech developer may be able to download individual files, but still miss the context: what meeting a document belongs to, what agenda item it was used for, and when the dataset was last refreshed.

Open RIS Monitor focuses on that practical gap. It turns public RIS metadata into a predictable, inspectable and forkable static dataset.

## Solution

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

There is no runtime server and no database. The generated files are the public contract. The viewer reads those files directly in the browser.

## What it can do today

Open RIS Monitor currently supports the Huizen reference deployment with:

- GemeenteOplossingen API harvesting;
- latest, public and backfill harvest profiles;
- document metadata normalization;
- document type cleanup and fallback labels;
- meeting and agenda-item relation exports where the source exposes usable links;
- document version metadata when checksum enrichment is enabled;
- dataset freshness metadata in `latest.json`;
- compact JSONL public exports under `data/public/`;
- basic quality reports under `data/public/quality/`;
- a static GitHub Pages viewer for documents and meetings;
- GitHub Actions based validation and scheduled harvesting.

## What it deliberately does not do

Open RIS Monitor is not intended to become:

- a national portal;
- a SaaS platform;
- a central aggregator;
- an OCR platform;
- a PDF archive;
- a notification service;
- a generic enterprise data platform.

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
- reproducible GitHub Actions workflows.

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
data/public/latest.json
data/public/quality/summary.json
data/public/quality/issues.jsonl
```

`latest.json` is the operational summary for the current public dataset. It records the municipality, generation timestamp, run profile, output files, relation status and dataset totals.

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

Generate quality reports:

```bash
python -m open_ris_monitor.analysis.generate_public_reports \
  --public-dir data/public
```

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

## Adopting another municipality

For another municipality using GemeenteOplossingen, the intended path is to fork the repository, add a municipality profile under `config/municipalities/`, run a bounded test harvest, validate the output, then enable GitHub Actions and GitHub Pages.

For another RIS vendor, documentation is available, but code changes are likely required. The project currently has a proven GemeenteOplossingen implementation, not a fully generic multi-vendor connector framework.

Start with [Adding a municipality](docs/adding-a-municipality.md) and [Connectors](docs/connectors.md).

## Repository policy

Commit source code, configuration, documentation and approved public exports only.

Do not commit:

- `data/raw/`;
- downloaded PDFs;
- temporary caches;
- local virtual environments;
- generated diagnostics outside the documented public output paths.

## Current MVP status

The project is approaching MVP 1.0 as a Huizen reference implementation. The main remaining work is documentation coherence, release governance, and conservative hardening of the public data contract. The architecture should remain small and static.

## License

This repository declares an MIT license. Before a formal v1.0 release, verify that the `LICENSE` file contains the complete final license text.

### MVP 1.1 organisation context

Open RIS Monitor can also publish a small static `Organisatie` view. This view uses the public RIS organisation endpoints for groups, persons, roles and positions, with optional group membership where the API exposes it. The output is intended as civic context for the council organisation, not as a political profile directory. Nested user-management metadata is excluded from the public export.
