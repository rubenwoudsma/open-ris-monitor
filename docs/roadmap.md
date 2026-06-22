# Roadmap

This roadmap is intentionally conservative. Open RIS Monitor should remain a focused civic open-source reference implementation, not a central platform or enterprise data product.

## Completed or MVP-complete foundations

- Document-first harvest for the Huizen reference implementation.
- GemeenteOplossingen connector path for public RIS metadata.
- Canonical document exports.
- Document version metadata when checksum enrichment is enabled.
- No PDF storage in Git.
- GitHub Pages static viewer.
- Public JSONL exports under `data/public/`.
- Latest/public/backfill harvest profiles.
- Scheduled public harvest workflow.
- Concurrency protection for harvest workflows.
- Relation exports for meetings and meeting items where the source supports them.
- Document type normalization and fallback labels.
- Dataset freshness and basic metadata in `latest.json`.
- Basic quality reports under `data/public/quality/`.
- Export validation in CI.

## Current MVP documentation focus

The current milestone is documentation coherence before MVP 1.0:

- README as the public front door;
- practical municipality onboarding guide;
- connector documentation for the current GemeenteOplossingen implementation;
- accurate harvesting, export, quality and validation documentation;
- conservative roadmap cleanup.

This supports:

- issue #52, Municipality Onboarding Guide;
- issue #57, Connector Interface Documentation;
- README and documentation consistency before MVP 1.0.

## Before MVP 1.0

The remaining pre-1.0 work should focus on stability and adoption, not scope expansion.

Recommended priorities:

1. Keep the export contract stable and documented.
2. Keep validation strict enough to prevent empty or corrupt public output.
3. Keep the Huizen reference deployment healthy.
4. Make onboarding for another GemeenteOplossingen municipality practical and honest.
5. Document connector expectations without over-engineering abstractions.
6. Keep the static viewer robust against missing or messy source fields.
7. Prepare release notes and verify the license file before tagging v1.0.

## Can wait until after MVP 1.0

- Full search index strategy beyond basic client-side filtering.
- Export partitioning by year or month.
- Additional RIS vendor implementations.
- A formal connector base class, unless a second vendor makes the interface clear.
- More advanced quality scoring.
- Monthly scheduled backfill automation.
- Optional PDF preview in the viewer.
- OCR or text extraction.
- Notification features.

## Out of scope

Open RIS Monitor is not intended to become:

- a national portal;
- a SaaS platform;
- a central aggregator;
- an OCR platform;
- a PDF archive;
- a notification service;
- a generic enterprise data platform.

## Release checklist for v1.0

- README explains what the project is and is not.
- Onboarding guide works for the supported GemeenteOplossingen path.
- Connector documentation explains current support and future vendor expectations.
- Export contract and schema version policy are documented.
- Harvest profiles and cadence are documented.
- Quality and freshness metadata are documented.
- CI validation passes.
- Generated public data is not accidentally changed in documentation PRs.
- License text is final.
- GitHub Pages site loads the public dataset correctly.

## Related documentation

- `README.md`
- `docs/adding-a-municipality.md`
- `docs/connectors.md`
- `docs/export-contract.md`
- `docs/harvesting.md`
- `docs/quality.md`
