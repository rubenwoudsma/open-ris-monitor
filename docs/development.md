# Development

This document describes local development and review hygiene for Open RIS Monitor.

The project is intentionally small. Use ordinary GitHub tools, small pull requests and reproducible commands.

## Requirements

- Python 3.11 or newer;
- Git;
- internet access for live RIS harvest tests;
- a shell environment that can run the commands below.

## Install

```bash
python -m pip install --upgrade pip
python -m pip install -e .[dev]
```

## Local checks

Run tests:

```bash
python -m pytest
```

Run linting:

```bash
ruff check .
```

Validate public exports when `data/public/` is present:

```bash
python -m open_ris_monitor.exporters.validate_exports
```

## Local harvest smoke test

Use `quick` first:

```bash
python -m open_ris_monitor.pipeline.run \
  --municipality huizen \
  --profile quick
```

Use bounded public-style runs for development:

```bash
python -m open_ris_monitor.pipeline.run \
  --municipality huizen \
  --profile public \
  --max-documents 100 \
  --meeting-scan-limit 100
```

Use `backfill` only when intentionally testing historical coverage or recovery.

## Generate quality reports

```bash
python -m open_ris_monitor.analysis.generate_public_reports \
  --public-dir data/public
```

## Repository rules

Do not commit:

```text
data/raw/
*.pdf
temporary downloads
local caches
virtual environments
```

Only commit `data/public/` when the PR intentionally updates the published dataset. For documentation-only changes, avoid generated data changes.

Check before every commit:

```bash
git status --short
```

## Recommended PR style

Keep PRs small and reviewable. Prefer one primary goal per PR.

Good PR categories:

- documentation-only;
- connector or harvesting fix;
- export contract or validation fix;
- frontend-only improvement;
- generated public data refresh.

Avoid mixing documentation refreshes with unrelated harvesting or frontend behavior changes.

## Important documents

- `README.md`, project front door.
- `docs/architecture.md`, system shape and constraints.
- `docs/data-model.md`, canonical entities and relations.
- `docs/export-contract.md`, public output contract.
- `docs/harvesting.md`, profiles, cadence and recovery.
- `docs/quality.md`, quality report interpretation.
- `docs/adding-a-municipality.md`, fork and onboarding steps.
- `docs/connectors.md`, connector responsibilities.
- `docs/roadmap.md`, MVP direction.
- `docs/validatie-ci.md`, CI and validation.

## GitHub Actions

The main workflows are:

```text
.github/workflows/validate.yml
.github/workflows/harvest.yml
```

`validate.yml` runs tests, Ruff and export integrity validation.

`harvest.yml` runs scheduled and manual harvests, generates reports, validates outputs and optionally commits `data/public/`.

## Frontend development

The viewer lives under `site/` and is static. Do not introduce a backend or database for viewer features. Keep asset paths compatible with GitHub Pages forks.

The frontend should be defensive against source data problems. Missing fields, malformed dates or absent relations should render gracefully.
