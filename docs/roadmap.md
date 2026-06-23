# Roadmap

## Completed

- Document-first harvest for Huizen
- Canonical document exports
- GitHub Pages viewer
- Automatic `data/public` updates after harvest
- Paginated full document harvest with `latest` and `full` modes
- Document versions and checksum metadata
- #14 Research meetings and agenda-items endpoints
- #15 Step 1: GemeenteOplossingen meeting relation endpoints
- #15 Step 2: Optional raw meeting relation harvest
- #15 Step 3: Canonical meeting relation normalization
- #15 Step 4: Public meeting relation exports
- Daily scheduled public harvest cadence
- Monthly scheduled public backfill cadence

## Current MVP focus

The project is moving from working reference implementation to MVP 1.0 readiness.

The remaining MVP work should stay small and conservative:

- preserve the static GitHub Pages architecture;
- keep public exports compact and stable;
- avoid generated PDF storage, OCR, backend services or databases;
- prefer bounded operational improvements before heavier frontend or export changes.

## Upcoming

### #89 URL state for search and filters

Useful for sharing exact search and filter views. Keep this small and frontend-only:

- restore search state from URL parameters;
- update the URL without a full page reload;
- do not introduce a router framework.

### #98 Optional PDF preview

Useful but optional. It must remain a viewer convenience only:

- use existing external document URLs;
- do not store PDFs in Git;
- do not add OCR or text extraction;
- preserve direct open/download links.

## Post-MVP candidates

### #56 Export Partitioning Strategy

Can wait until measured file sizes or browser performance show a concrete need. Do not introduce sharding or a manifest system before the current export contract requires it.

### #58 Search Index Strategy

Can wait while native client-side filtering remains fast enough. If search becomes slow, prefer a small static client-side approach before adding generated indexes or heavier dependencies.

## Operational harvest strategy

Build toward full historical coverage through bounded, resumable harvests:

- scheduled daily public harvests;
- scheduled monthly backfills;
- manual backfill for recovery or first seeding;
- no raw or PDF archive in Git;
- compact public JSONL exports only.

See `docs/harvesting.md`.

## Multi-source support

After the GemeenteOplossingen implementation stabilizes:

- document a connector interface for other RIS suppliers;
- add supplier capability flags;
- distinguish source endpoints from canonical output;
- keep public exports stable across suppliers.
