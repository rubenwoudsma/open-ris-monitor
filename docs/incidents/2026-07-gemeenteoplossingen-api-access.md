# Incident review: GemeenteOplossingen API access, July 2026

## Status

The repository-side diagnosis and hardening are complete. The public Huizen harvest cannot honestly be declared restored while the upstream API continues to reject normal public requests from GitHub-hosted runners and other clients.

The implementation in this incident branch does three things:

1. produces actionable diagnostics before harvesting;
2. prevents failed, empty or partial harvests from changing the public dataset;
3. provides a bounded probe that can show whether routing or access differs by endpoint, redirect, client or User-Agent.

It does not attempt to bypass upstream access controls and does not silently replace `/documents` with an unproven alternative.

## Timeline from the supplied Action logs

| Time [UTC] | Observation |
| --- | --- |
| 2026-07-16 05:57:30 | Successful scheduled run starts on runner 2.335.1, Ubuntu 24.04.4, image 20260714.240.1. |
| 2026-07-16 05:57:32 | Repository commit `34e0065b62e77f7b619dd769a61a6b26cfa676ea` is checked out. |
| 2026-07-16 06:02:15 | Public profile succeeds with 250 documents, 250 meetings and 1,000 meeting items. |
| 2026-07-16 06:02:18 | Data-only commit `71ac941d8a02a85018774913581738cac10f4715` is created and pushed. |
| 2026-07-17 05:57:51 | First failed scheduled run starts with the same runner version, OS, image and Python 3.11.15. |
| 2026-07-17 05:57:53 | It checks out the preceding data-only commit `71ac941d8a02a85018774913581738cac10f4715`. |
| 2026-07-17 05:58:00 | The first document count request receives HTTP 404 at `/api/v2/documents?limit=1&offset=0`. |
| 2026-07-17 05:58:00 | The job exits before report generation, artifacts, commit or push. |

The supplied logs are stored outside the repository as:

```text
logs_79801029879.zip  successful run
logs_80041166520.zip  first failed run
```

## Repository comparison

No code, configuration, workflow, dependency declaration or secret change occurred between the successful and failed runs.

The successful run created commit `71ac941`, containing generated files under `data/public/`. The failed run checked out that exact commit. Both runs installed the package in the same way and used the same GitHub Actions runner image and Python version.

This excludes a repository regression as the primary cause of the overnight change.

## Production endpoint observations

A bounded external check on 3 August 2026 found an HTML access-denied response at the Huizen API root and at tested collection routes. The response was not the documented JSON envelope. The page contained:

```text
Toegang geweigerd: foutcode 9e4edb5b6b850c41.
```

The first failed GitHub-hosted run instead received HTTP 404. Different outward responses for the same API family, depending on client or infrastructure path, are consistent with a reverse proxy, WAF, bot filter, IP rule or other access-control layer.

A representative GemeenteOplossingen installation for Woudenberg returned the same access-denied text and error code during the comparison. This makes a Huizen-only application defect less likely.

## Root-cause classification

Best-supported category:

```text
upstream routing or access-control change, probably at reverse-proxy or WAF level
```

Supporting facts:

- the same repository code succeeded one day earlier;
- the first request failed before local state or output mutation;
- current responses are HTML where public API JSON is expected;
- the status presented to GitHub Actions [404] differs from the access-denied response presented to another client;
- at least one other GemeenteOplossingen installation shows the same denial signature;
- the supplied API documentation still describes unauthenticated public access.

Not proven:

- which organisation or supplier made the change;
- the exact deployment time or rule;
- whether Open RIS Monitor was specifically targeted;
- whether the change was intentional, accidental or part of a broader security rollout.

The timing relative to publication of Open RIS Monitor is legitimate to raise with the municipality and supplier, but timing alone is not evidence of motive or targeting.

## API specification comparison

The supplied Open Raadsinformatie API documentation [version 2.0.15] describes:

- public access without required authentication for non-confidential objects;
- the standard response envelope `status`, `code`, `messages`, `result`;
- `GET /documents/{documentId}` and `/download`;
- meeting and meeting-item document relations;
- `limit` and `offset` on collection and relation routes.

The production HTML denial therefore does not match the documented API contract.

## General document collection versus relation routes

The repository contains known identifiers from the last valid dataset, including document, meeting and meeting-item source IDs. The new diagnostic command uses those existing IDs, never random IDs, and can test:

```text
/documents/{documentId}
/documents/{documentId}/download  [Range: bytes=0-0]
/meetings/{meetingId}/documents
/meetings/{meetingId}/meetingitems
/meetingitems/{meetingItemId}/documents
```

The current execution environment could not make direct socket connections to the public host, so these object-level probes must be run through GitHub Actions or a normal local network. After a failed preflight, the updated workflow automatically runs only the seven-request core probe and uploads the report. The full object and relation matrix remains a deliberate manual diagnostic command.

## Why no relation-only harvesting fallback was implemented

The last valid public dataset contains 17,082 documents. The canonical relation files identify 1,440 unique document IDs with a meeting or agenda relation, which is 8.43 percent. The existing dashboard uses a different calculation and reports 1,664 linked documents, or 9.74 percent. That metric discrepancy is itself another reason not to treat the current relation harvest as a complete discovery source.

Even when the higher dashboard figure is used, a relation-only strategy could omit at least 15,418 documents, about 90.26 percent of the collection. Using the canonical relation IDs, the possible omission is 15,642 documents, about 91.57 percent.

It would also create unresolved problems for:

- documents that are public but not attached to a meeting or agenda item;
- changed documents that do not reappear in the scanned relation window;
- deletion detection;
- historical completeness;
- API call volume and rate limiting;
- existing relation-coverage quality metrics.

Implementing that approach would create a misleading partial dataset. It is rejected unless the supplier can prove complete relation coverage or restore a supported collection mechanism.

## Open State comparison

The current Open State GemeenteOplossingen extractor:

- defaults to API v1 unless `api_version` is configured;
- discovers documents directly with `GET /documents` and date filters;
- does not use meeting or meeting-item relations as document discovery fallback;
- converts any non-200 response into an empty result;
- contains no retry, WAF or endpoint-variant compatibility logic in the extractor itself.

Their Huizen source is present and currently inherits the default API v1 configuration. This does not provide a proven replacement for the Open RIS Monitor v2 route. It also does not establish from public code alone whether their Huizen import stopped on exactly 17 July 2026.

The useful lesson is limited: API version and source paths should be configurable and diagnosed explicitly. Open State's silent non-200-to-empty behavior should not be copied because it could make an outage look like a valid empty collection.

## Implemented controls

- typed HTTP errors with sanitized URL, status, Content-Type, redirects and bounded body preview;
- separate timeout, connection, HTTP, HTML, Content-Type and JSON-envelope classifications;
- bounded retry for timeouts, connection failures, 429 and selected 5xx responses;
- `Retry-After` support;
- no retry of structural 404 responses;
- strict document `totalCount` validation;
- incomplete-pagination detection;
- cheap preflight before output writes;
- seven-request automated core probe and a deliberate full probe with known IDs;
- optional project and browser-like User-Agent comparison for manual diagnosis;
- explicit diagnostic comparison of known base-path or API-version candidates;
- staging under `data/.harvest-staging`;
- validation and shrink protection before promotion;
- rollback-capable promotion of raw and public directories;
- commit and push only after successful promotion;
- job summary and diagnostic artifacts.

## Required upstream action

The production harvest can resume only when one of these supported conditions is provided:

1. unauthenticated public API access is restored for normal HTTP clients and GitHub-hosted runners;
2. the municipality or supplier publishes and documents a replacement public base URL or API version;
3. a legitimate API credential or allowlisting process is made available for public-data harvesting;
4. the supplier documents a complete supported collection endpoint that preserves the current document coverage.

A browser-only route or a User-Agent impersonation workaround is not an acceptable structural solution.

## Safe verification after upstream repair

1. Run the preflight command and inspect both required endpoints.
2. Run the full bounded incident probe and compare project and browser diagnostic results.
3. Run a manual `quick` profile without committing.
4. Run a manual `public` profile without committing and inspect staged counts.
5. Validate exports and quality reports.
6. Enable `commit_public` only after the generated totals are plausible.
7. Confirm the live site shows the new valid `generated_at` timestamp.

Commands are documented in [harvesting.md](../harvesting.md) and [adding-a-municipality.md](../adding-a-municipality.md).
