# Open RIS Monitor

Open RIS Monitor is a small, reproducible open-data pipeline for public council information. The first implementation uses the GemeenteOplossingen API of the municipality of Huizen.

Live viewer:

```text
https://rubenwoudsma.github.io/open-ris-monitor/site/index.html
```

## What this project is

Open RIS Monitor turns RIS data into a small static public dataset that is easy to inspect, reuse and fork for another municipality.

The project is designed around a simple idea:

1. fetch source data from a RIS,
2. normalize it to a canonical model,
3. publish compact JSONL exports,
4. show the result in a static GitHub Pages viewer.

## Why it exists

The repository is meant to stay small, transparent and reusable.

It avoids the usual pile-up of raw dumps, PDFs and hidden intermediate data. Instead, it keeps the public output compact and explicit, so another municipality can reuse the same approach with minimal friction.

## Example use

For Huizen, the workflow harvests documents and, where available, relations to meetings and agenda items. The public exports are published as plain files in `data/public/`, which the static viewer reads directly.

A typical public run uses the manual GitHub Actions workflow with the `public` profile.

## How it fits together

The core pipeline is:

- RIS source connector
- normalization to a canonical model
- enrichment with checksums, quality and relations
- publication as JSONL and JSON files
- static viewer on GitHub Pages

The architecture and data model are documented in `docs/architecture.md` and `docs/data-model.md`.

## Public outputs

The durable public layer is `data/public/`.

Current exports include:

- `documents.jsonl`
- `document_versions.jsonl`
- `harvest_runs.jsonl`
- `meetings.jsonl`
- `meeting_items.jsonl`
- `meeting_documents.jsonl`
- `meeting_item_documents.jsonl`
- `latest.json`

## Using this for another municipality

The repository is meant to be forkable.

For a new municipality, the usual path is:

1. copy the municipality configuration,
2. point it at the right RIS source,
3. test a small harvest,
4. inspect the public exports,
5. publish only `data/public/`.

If the municipality uses another RIS vendor, a new connector may be needed.

See `docs/adding-a-municipality.md`.

## Roadmap

The current focus is on:

- quality reporting,
- documentation cleanup and consolidation,
- a cleaner GitHub-like UI,
- better navigation between documents, meetings and relations.

See `docs/roadmap.md`.

## Development

The repository is intentionally small and reviewable.

A few guiding rules:

- no PDFs in Git,
- no raw dumps in Git,
- raw output only as temporary workflow artifact,
- keep the viewer static,
- keep public exports compact and stable,
- prefer small, uploadable changes.

See `docs/development.md` for the working conventions.
