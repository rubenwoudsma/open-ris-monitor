# Voting and decision outcome research

This note records the post-live feasibility review for adding voting or decision-outcome insight to Open RIS Monitor.

## Verdict

Full voting insight is not safe to implement from the currently documented GemeenteOplossingen Open Raadsinformatie API contract.

The current API documentation exposes useful public metadata for documents, meetings, meeting items and council organisation data. It does not document explicit endpoints for votes, voting results, per-person voting records, party voting records, motions, amendments, toezeggingen or formal decision outcomes.

Recommended classification: **research issue, not implementation issue**.

## API surface inspected

The documented API route groups inspected were:

```text
/attachments
/dmus
/documents
/events
/groups
/meetings
/meetingitems
/persons
/positions
/roles
```

The relevant documented relation routes inspected were:

```text
/events/{eventId}/attachments
/dmus/{dmuId}/meetings
/meetings/{meetingId}/documents
/meetingitems/{meetingItemId}/documents
/meetings/{meetingId}/meetingitems
/documents/{documentId}/persons
/groups/{groupId}/persons
/roles/{roleId}/persons
/persons/{personId}/positions
/roles/{roleId}/positions
```

## Data that is available

Open RIS Monitor can safely use machine-readable metadata that the API already exposes or that the current pipeline already normalizes:

- document metadata, including title, filename, document type label, description, confidentiality marker and file size;
- meeting metadata, including date, time, decision-making unit and location;
- agenda item metadata, including number, title, description, sort order and location;
- document-to-meeting links;
- document-to-agenda-item links;
- organisation metadata, including groups, persons, roles, positions and group memberships.

This supports navigation and context, not vote reconstruction.

## Data that is missing

The currently documented API contract does not expose:

- vote records;
- vote result objects;
- per-person voting behavior;
- per-party voting behavior;
- explicit motion objects;
- explicit amendment objects;
- explicit toezegging objects;
- structured agenda-item decision outcomes;
- structured meeting-item status values such as accepted, rejected, withdrawn or amended.

## Safe feature options

### Option A, explicit voting data

Not implementable now.

This would require a documented endpoint or source payload that exposes vote objects and their relation to meetings, agenda items, persons or parties. The current documented API surface does not show such a contract.

### Option B, decision and outcome metadata

Not safely implementable as structured outcomes yet.

A limited future feature could show a `Besluitvorming` section on an agenda item only if machine-readable source metadata exposes such fields. The current documented agenda item model contains title, description, number, sort order and location, but no structured decision outcome.

### Option C, document-based inference

Possible only as a cautious document-discovery feature, not as voting insight.

A future feature could add filters or labels for likely decision-related documents based on document type labels or titles, for example `besluit`, `motie`, `amendement` or `stemuitslag`, when such labels appear in public document metadata.

Guardrails:

- do not claim a vote result from a PDF title alone;
- do not infer per-person or per-party voting behavior;
- do not add OCR or PDF text extraction as part of this project direction;
- use language such as `mogelijk besluitdocument` only when the signal is title-based or type-label-based.

### Option D, out of scope for now

Recommended for MVP 1.2 and near-term post-live work.

Open RIS Monitor should keep the current document-first, static architecture and open a research issue to verify whether the live source API has any undocumented vote or decision fields for Huizen.

## Recommended GitHub issue

Title:

```text
Research voting and decision outcome support in RIS API
```

Body:

```markdown
## Context

Open RIS Monitor currently exposes documents, meetings, agenda items, relations and council organisation context. It does not expose voting insight.

The documented GemeenteOplossingen Open Raadsinformatie API currently shows route groups for attachments, DMUs, documents, events, groups, meetings, meeting items, persons, positions and roles. It does not document explicit vote, voting-result, motion, amendment, toezegging or structured decision-outcome endpoints.

## Goal

Determine whether voting or decision-outcome insight can be implemented safely without OCR, PDF text extraction, a backend or unsupported inference.

## Research questions

- Does the live Huizen API expose undocumented vote or decision fields?
- Do meeting items include structured outcome/status fields in real responses?
- Do document type labels reliably identify besluiten, moties, amendementen or stemmingsdocumenten?
- Can any feature be implemented without claiming per-person or per-party voting behavior?

## Acceptance criteria

- Document the exact endpoints inspected.
- Include sample payload fields from real public responses where available.
- State clearly whether explicit vote data exists.
- If no explicit vote data exists, propose only a limited decision-document discovery feature.
- Do not add OCR, PDF text extraction, a backend, database, scraping outside the public API or unsupported political inference.
```

## Recommendation

Do not add a frontend voting tab yet. If this becomes a feature, start with a small research PR that samples live API responses and records whether any machine-readable outcome fields exist. Only implement a user-facing feature when the source data can support the claim.
