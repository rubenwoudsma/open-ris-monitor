# Adding a municipality

This guide explains the practical path for adapting Open RIS Monitor to another municipality.

The shortest supported path is another municipality that uses the GemeenteOplossingen API in a similar way to the Huizen reference implementation. A municipality using another RIS vendor will likely need a new connector or adapter before the normal pipeline can be reused.

## What you need first

- A fork or clone of this repository.
- Python 3.11 or newer.
- A public RIS endpoint for the municipality.
- A clear municipality slug, for example `huizen`, `hilversum` or `bussum`.
- Enough time to run a small bounded harvest before enabling scheduled publishing.

## Supported adoption paths

| Situation | Expected effort | Notes |
|---|---:|---|
| Another GemeenteOplossingen municipality with compatible API routes | Low to medium | Usually starts with configuration and bounded validation. |
| GemeenteOplossingen with route or payload differences | Medium | Configuration plus connector or normalization adjustments may be needed. |
| Another RIS vendor | High | A new connector is likely required. See [connectors.md](connectors.md). |

Do not claim a new municipality is supported until a bounded harvest has been run and the generated public exports have been validated.

## Step 1, fork or clone

Fork the repository on GitHub, or clone it locally:

```bash
git clone https://github.com/rubenwoudsma/open-ris-monitor.git
cd open-ris-monitor
python -m pip install --upgrade pip
python -m pip install -e .[dev]
```

Run the baseline checks before changing anything:

```bash
python -m pytest
ruff check .
```

## Step 2, choose the municipality slug

Use a stable lowercase slug. Prefer ASCII letters, digits and hyphens only.

Examples:

```text
huizen
hilversum
gooise-meren
```

The slug is used in configuration, generated identifiers, workflow inputs and output metadata. Changing it later may change public IDs, so choose it carefully.

## Step 3, create or copy a municipality profile

If the repository contains an example profile, copy it:

```bash
cp config/municipalities/example.yml config/municipalities/my-municipality.yml
```

If there is no example profile, copy the closest existing GemeenteOplossingen profile and adjust it carefully.

A profile should describe at least:

```yaml
municipality:
  name: Huizen
  slug: huizen
  official_identifier: gm0406
  country: NL
  website_url: https://www.huizen.nl
  ris_url: https://ris.gemeenteraadhuizen.nl
  timezone: Europe/Amsterdam

source_system:
  vendor: GemeenteOplossingen
  connector: gemeenteoplossingen
  base_url: https://ris.gemeenteraadhuizen.nl/api/v2/
  api_version: v2

storage:
  commit_pdf_files: false
```

Keep `commit_pdf_files` false. Open RIS Monitor does not store PDFs in Git.

## Step 4, verify the source API

For a GemeenteOplossingen municipality, confirm that the public API exposes the routes needed by the current connector. The Huizen implementation relies on routes such as:

```text
GET /documents
GET /documents/{documentId}
GET /documents/{documentId}/download
GET /meetings
GET /meetings/{meetingId}
GET /meetings/{meetingId}/documents
GET /meetings/{meetingId}/meetingitems
GET /meetingitems/{meetingItemId}
GET /meetingitems/{meetingItemId}/documents
```

Some source systems expose different historical and future meeting coverage. A missing meeting detail may be source variation rather than a fatal error, but it should be documented during onboarding.

## Step 5, run a small local harvest

Start with a small smoke test:

```bash
python -m open_ris_monitor.pipeline.run \
  --municipality huizen \
  --profile quick
```

Replace `huizen` with the new slug after the profile exists.

Then run a bounded public-style test:

```bash
python -m open_ris_monitor.pipeline.run \
  --municipality my-municipality \
  --profile public \
  --max-documents 100 \
  --meeting-scan-limit 100
```

Use explicit limits while onboarding. This keeps runtime, API load and review scope predictable.

## Step 6, inspect the public exports

Check that `data/public/` contains the expected files. At minimum:

```text
data/public/documents.jsonl
data/public/harvest_runs.jsonl
data/public/latest.json
```

For the normal relational public workflow, also expect:

```text
data/public/meetings.jsonl
data/public/meeting_items.jsonl
data/public/meeting_documents.jsonl
data/public/meeting_item_documents.jsonl
data/public/quality/summary.json
data/public/quality/issues.jsonl
```

Validate that:

- JSONL files contain valid JSON per line;
- `latest.json` points to existing output files;
- the municipality name and slug are correct;
- document counts are plausible;
- relation counts are plausible for the selected source window;
- no PDFs or raw API dumps were added to Git.

## Step 7, generate quality reports

```bash
python -m open_ris_monitor.analysis.generate_public_reports \
  --public-dir data/public
```

Review the summary and issues files. Warnings do not automatically mean the dataset is unusable. They should be interpreted as signals about source quality, relation coverage and freshness.

## Step 8, run validation

Run the local checks again:

```bash
python -m pytest
ruff check .
python -m open_ris_monitor.exporters.validate_exports
```

If export validation fails, do not publish the dataset. Fix the profile, connector or normalization issue first.

## Step 9, enable GitHub Actions

In the forked repository, enable GitHub Actions.

Use `.github/workflows/harvest.yml` for scheduled public harvesting. The default scheduled profile is intended to be `public`, not `backfill`.

Recommended cadence for a fork:

```text
23 3 * * *
```

Choose a non-hourly minute, for example 17, 23, 41 or 52. This reduces the chance that many forks hit the same upstream API at exactly the same time.

## Step 10, configure GitHub Pages

Publish the static viewer from the repository settings. The current viewer lives under:

```text
site/index.html
```

After publication, open the site and check:

- the viewer loads without console errors;
- documents are visible;
- meetings are visible when relational exports exist;
- the dataset footer shows the expected municipality and generation timestamp;
- links to source documents work.

## Step 11, avoid accidental generated-data commits

During docs-only or code-only changes, avoid committing generated public data accidentally.

Before committing:

```bash
git status --short
```

Only include `data/public/` when the PR is intentionally updating the public dataset. Never commit:

```text
data/raw/
*.pdf
local caches
temporary downloads
```

## Latest, public and backfill usage

Use `quick` for smoke tests and diagnostics.

Use `public` for the regular public dataset.

Use `backfill` only for controlled historical filling, recovery or initial broad loading. Do not schedule daily backfills. Prefer manual backfill runs with explicit limits.

## Troubleshooting checklist

- Wrong or empty dataset: check the profile slug and `base_url`.
- API timeout or 429: reduce limits and retry later.
- Missing meetings: verify whether the source uses `/meetings`, `/events`, `/dmus` or `/meetingsessions` differently.
- Missing agenda-item relations: inspect nested meeting item routes for the selected meeting window.
- Export validation failure: inspect the failing file and line number.
- Viewer shows stale data: check `data/public/latest.json` and the last successful harvest workflow.
- GitHub Pages asset errors: confirm relative paths and repository Pages settings.
- Unexpected generated files in Git: reset raw output, PDFs and local caches before committing.

## Known limitations

- GemeenteOplossingen is the proven connector path today.
- Other RIS vendors require adapter work.
- Source data quality varies by municipality and by meeting status.
- Planned or future meetings may have incomplete document and agenda relations.
- Open RIS Monitor does not archive PDFs, perform OCR or redact source documents.

## Related documentation

- [connectors.md](connectors.md)
- [harvesting.md](harvesting.md)
- [export-contract.md](export-contract.md)
- [quality.md](quality.md)
- [development.md](development.md)
