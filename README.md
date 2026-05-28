# Open RIS Monitor

Open RIS Monitor harvests public council information from a municipal RIS, normalizes it into reusable public data files, and exposes the result through a static GitHub Pages viewer.

## Current status

The project currently supports a document-first flow for the municipality of Huizen:

1. GitHub Actions runs a harvest.
2. GemeenteOplossingen document metadata is fetched through the RIS API.
3. Documents are normalized into canonical `Document` records.
4. Public exports are written to `data/public/`.
5. GitHub Pages reads the public exports.

The harvest supports:

- `latest` mode, for the newest documents
- `full` mode, for paginated document harvesting
- optional public export commits
- optional checksum enrichment for a limited number of documents

PDF files are not stored in Git. When checksum enrichment is enabled, PDFs are downloaded temporarily during the workflow and discarded after the checksum has been calculated.

## Public outputs

The public data layer currently contains:

- `data/public/documents.jsonl`
- `data/public/harvest_runs.jsonl`
- `data/public/latest.json`
- `data/public/document_versions.jsonl`, when checksum enrichment is enabled

## Harvest examples

Metadata-only latest harvest:

```bash
python -m open_ris_monitor.pipeline.run --municipality huizen --mode latest --limit 25
```

Paginated full metadata harvest:

```bash
python -m open_ris_monitor.pipeline.run --municipality huizen --mode full --batch-size 100 --max-documents 1000
```

Checksum enrichment for a limited set of documents:

```bash
python -m open_ris_monitor.pipeline.run \
  --municipality huizen \
  --mode full \
  --batch-size 100 \
  --max-documents 1000 \
  --enrich-checksums \
  --checksum-max-documents 50
```

## Storage policy

- `data/public/` contains reusable public exports and may be committed.
- `data/raw/` is primarily workflow output and should remain artifact-only by default.
- PDFs are not committed to Git.
- Checksums are stored as metadata in `document_versions.jsonl`.
