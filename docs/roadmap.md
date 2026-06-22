# Roadmap

This roadmap is intentionally conservative. Open RIS Monitor should remain a focused civic open-source reference implementation, not a central platform or enterprise data product.

The roadmap is not a promise list. It is a scope guard for MVP 1.0 and the first post-MVP improvements.

## Roadmap shape

| Horizon | Goal | Level of detail |
|---|---|---|
| MVP 1.0 | Stable reference deployment for Huizen and a practical path for similar GemeenteOplossingen municipalities. | Concrete enough to close issues and prepare a release. |
| After MVP 1.0 | Improve scale, search and adoption once the reference deployment is stable. | Directional, because the right solution depends on real usage. |
| Out of scope | Prevent the project from drifting into a platform, archive or notification product. | Explicit, to protect maintainability. |

## Completed or MVP-complete foundations

- Document-first harvest for the Huizen reference implementation.
- GemeenteOplossingen connector path for public RIS metadata.
- Canonical document exports.
- Document version metadata when checksum enrichment is enabled.
- No PDF storage in Git.
- GitHub Pages static viewer.
- Public JSONL exports under `data/public/`.
- Latest, public and backfill harvest profiles.
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

| Priority | Workstream | Outcome |
|---|---|---|
| 1 | Export contract | Public JSONL fields and schema version policy are stable enough for downstream users. |
| 2 | Validation and safety | CI fails on malformed, missing, empty or sharply reduced public output. |
| 3 | Reference deployment | The Huizen public site and data exports remain healthy. |
| 4 | Onboarding | A similar GemeenteOplossingen municipality can follow the docs without guessing the project shape. |
| 5 | Connectors | Current connector responsibilities are documented without introducing a large abstraction framework. |
| 6 | Static viewer resilience | The viewer handles missing or messy source fields without crashing. |
| 7 | Release preparation | License, release notes and public documentation are checked before tagging v1.0. |

## After MVP 1.0

These items can wait until there is real pressure from dataset size, user feedback or a second implementation:

| Topic | Trigger | Likely direction |
|---|---|---|
| Search index strategy | Client-side filtering becomes slow or too limited. | Add a compact static index. |
| Export partitioning | Public JSONL files become too large for reliable browser loading. | Partition by year or another stable dimension. |
| Additional vendors | A concrete municipality needs a non-GemeenteOplossingen adapter. | Add a second connector and then extract a common interface if justified. |
| Advanced quality scoring | Basic counts are not enough to explain dataset health. | Add simple transparent metrics before composite scores. |
| Monthly backfill automation | Manual backfill becomes operationally annoying before go-live. | Add a scheduled workflow with conservative safeguards. |
| Optional PDF preview | Users need quicker inspection from the static viewer. | Add a lightweight preview that still does not store PDFs in Git. |

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

- [README.md](../README.md)
- [adding-a-municipality.md](adding-a-municipality.md)
- [connectors.md](connectors.md)
- [export-contract.md](export-contract.md)
- [harvesting.md](harvesting.md)
- [quality.md](quality.md)
