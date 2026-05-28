# Storage policy

## Public data

`data/public/` is the durable public data layer. It is intended to be committed and read by the GitHub Pages site.

Current public outputs:

- `documents.jsonl`
- `harvest_runs.jsonl`
- `latest.json`
- `document_versions.jsonl`, when checksum enrichment is enabled

## Raw data

`data/raw/` is used during the workflow and uploaded as a GitHub Actions artifact. It is not the primary public dataset and should not be automatically committed.

## PDF files

PDF files are not stored in Git. During checksum enrichment, PDFs may be downloaded temporarily inside GitHub Actions. The only durable output is metadata, such as SHA-256 checksums and downloaded file size.

## Checksums

Checksums are stored in `data/public/document_versions.jsonl`. A checksum observation is treated as a document version. If the same document receives a different SHA-256 hash in a later run, this is evidence that the source file changed.
