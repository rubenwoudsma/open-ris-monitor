# Connectors

This document describes the connector boundary for Open RIS Monitor.

The current proven connector is for GemeenteOplossingen, as used by the Huizen reference implementation. This PR does not introduce a new connector framework or abstract base class. It documents the current responsibilities so future vendor adapters can be added deliberately.

## Current supported connector

| Vendor | Connector key | Status |
|---|---|---|
| GemeenteOplossingen | `gemeenteoplossingen` | Proven for the Huizen reference implementation. |
| Other RIS vendors | not yet implemented | Requires new connector and normalization work. |

## Where connector code lives

Connector and source-specific logic is expected under:

```text
src/open_ris_monitor/
```

The exact module layout may evolve, but the rest of the system should keep vendor-specific behavior behind the harvesting and normalization boundary.

## Connector responsibilities

A connector is responsible for retrieving raw public source objects from a RIS vendor. It should not decide the final public data contract. That belongs to the canonical model and exporter layer.

A connector should provide or support:

- source API base URL handling;
- pagination with `limit` and `offset` where the vendor supports it;
- bounded retrieval for safe local tests;
- latest or recent retrieval for daily public updates;
- backfill retrieval for controlled historical loading;
- document metadata retrieval;
- meeting metadata retrieval where supported;
- agenda or meeting-item retrieval where supported;
- document-to-meeting and document-to-agenda raw relation discovery where supported;
- stable source identifiers for downstream canonical IDs;
- retry and back-off behavior for temporary upstream failures;
- clear failure behavior when a source route is unavailable.

A connector should not:

- store PDFs in Git;
- write public JSONL directly;
- hide source data quality problems by inventing unsupported relations;
- require a backend service;
- require a database;
- turn the project into a multi-tenant central platform.

## GemeenteOplossingen source concepts

The GemeenteOplossingen API exposes public objects such as documents, meetings, meeting items, DMUs, events and attachments. Public requests can be unauthenticated. The API uses `limit` and `offset` parameters on list routes, and individual objects can be fetched by ID.

Important source routes for the current implementation include:

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
GET /dmus
GET /dmus/{dmuId}/meetings
GET /events
GET /events/{eventId}
GET /events/{eventId}/attachments
```

Not every route is equally useful for every municipality or time period. Some routes provide better coverage for future meetings, while others may be needed for historical context.

## Raw to canonical mapping

The connector returns vendor-shaped records. Normalization maps those records into canonical Open RIS Monitor entities.

Typical GemeenteOplossingen document mapping:

| Source field | Canonical field | Notes |
|---|---|---|
| `id` | `source_id` | Source document identifier. |
| `objectId` | `source_object_id` | Additional source identifier when present. |
| `description` | `title`, `description` | Often the best available readable title. |
| `documentTypeLabel` | `document_type` | Cleaned and given fallback labels downstream. |
| `fileName` | `filename` | Original source filename. |
| `fileSize` | `file_size_bytes` | Source-reported size. |
| `publicationDate` | `publication_datetime` | Normalized to an ISO-like timestamp when possible. |
| `confidential` | `is_confidential` | Public deployments should only publish public objects. |

Typical meeting and agenda mapping:

| Source concept | Canonical concept |
|---|---|
| meeting | `Meeting` |
| meeting item | `MeetingItem` or agenda item |
| meeting document route | document-to-meeting relation |
| meeting item document route | document-to-agenda relation |
| DMU or group | body, committee or decision-making unit metadata when used |

## Pagination and harvest modes

Connectors should support three practical access patterns:

| Mode or profile | Purpose | Connector behavior |
|---|---|---|
| `quick` | Smoke test and diagnostics | Fetch a small bounded window. |
| `public` | Normal public dataset update | Fetch the configured public window and relation context. |
| `backfill` | Historical loading or recovery | Fetch broader ranges with explicit limits. |

Where list routes use pagination, use bounded `limit` and `offset` loops. A connector should stop when the configured limit is reached, the upstream returns no more records, or a non-retryable error occurs.

## Errors, retries and back-off

Temporary upstream errors should be retried with limited exponential back-off. Retryable examples include:

```text
408 Request Timeout
429 Too Many Requests
500 Internal Server Error
502 Bad Gateway
503 Service Unavailable
504 Gateway Timeout
network connect timeout
network read timeout
```

When the upstream sends `Retry-After`, respect it.

Do not blindly retry normal client errors:

```text
400 Bad Request
401 Unauthorized
403 Forbidden
404 Not Found
```

A known exception is a meeting detail 404 during relation discovery. That can be source variation and should not necessarily fail the whole harvest when the rest of the dataset is usable.

## Keeping a connector operational

A connector is not finished when the first harvest succeeds. It should be treated as a small operational contract with the upstream RIS vendor. For the current GemeenteOplossingen path, keep these checks visible when maintaining or adapting the project.

### Routine checks

| Area | What to check | Why it matters |
|---|---|---|
| API reachability | Confirm list and detail routes still respond. | A public site can become stale without an obvious frontend error. |
| Pagination | Confirm `limit` and `offset` still return complete windows. | Missing pages can silently reduce the dataset. |
| Date filters | Confirm bounded and latest runs still select the intended period. | A wrong window can overwrite a healthy dataset with incomplete output. |
| Confidentiality | Confirm confidential source records are not published. | Public deployments should only expose public metadata. |
| Relation routes | Confirm meeting-document and meeting-item-document routes still work. | Broken relation routes reduce context even when document harvesting works. |
| Document type fields | Confirm `documentTypeLabel` or fallback fields still exist. | Type labels drive filtering and public readability. |
| Counts | Compare new counts with previous successful runs. | This guards against zero-byte or sharply reduced outputs. |
| Rate limits | Watch for 429 responses or recurring timeouts. | Forks should avoid stressing the upstream vendor API. |

### When the upstream changes

When a vendor changes route behavior or payload fields, prefer this order of work:

1. Capture a small failing example in a local fixture or issue description.
2. Confirm whether harvesting, normalization or relation building is affected.
3. Update the connector or normalizer with the smallest safe change.
4. Add or update tests for the changed source shape.
5. Run export validation and check `latest.json` counts.
6. Confirm the static viewer still loads documents, meetings and relation context.

Do not solve source variation by broadening the public data contract without documenting it. Source-specific variation belongs in the connector or normalizer. Public JSONL fields should remain stable.

### Future vendor adaptation path

For another RIS vendor, the recommended path is incremental:

1. Document the vendor API routes and authentication requirements.
2. Prove document metadata harvesting first.
3. Map source records into the existing `Document` model.
4. Add meetings and agenda items only after document harvesting is stable.
5. Add relations only when the source exposes reliable links.
6. Keep the public export contract unchanged where possible.
7. Only introduce a shared connector interface after a second implementation shows the common shape.

This keeps the system running while avoiding premature abstractions. It also matches the current project principle that the Huizen GemeenteOplossingen implementation is the proven reference path.

## What an alternate vendor connector must provide

A new vendor connector should prove that it can produce the raw inputs needed for the canonical model:

- documents with stable source IDs, titles, types, filenames and publication metadata;
- meetings with stable source IDs, dates, titles and body or committee context where available;
- agenda or meeting items with stable source IDs and ordering where available;
- relations between documents, meetings and agenda items, or enough raw data to derive them honestly;
- source URLs or download URLs for public documents;
- bounded retrieval for safe tests;
- clear behavior for missing or incomplete source fields.

It does not need to implement every future concept, such as persons, roles, decisions, OCR text or topic classification.

## What is intentionally not abstracted yet

The project does not yet define a large `BaseConnector` hierarchy. That is intentional. At the current MVP stage, documentation and a proven reference implementation are more valuable than premature abstraction for unknown vendors.

A future abstraction should be added only when a second vendor implementation makes the common interface clear.

## Related documentation

- [adding-a-municipality.md](adding-a-municipality.md)
- [architecture.md](architecture.md)
- [data-model.md](data-model.md)
- [harvesting.md](harvesting.md)
- [export-contract.md](export-contract.md)
