# Meetings and agenda-items discovery

This document describes the discovery step for issue #14.

The document-first flow is already proven through the `documents` endpoint. Meetings and agenda-items should not be implemented by guessing endpoint names. Instead, the `Discover RIS API` workflow probes candidate endpoints and writes a report to:

```text
data/public/quality/gemeenteoplossingen_endpoint_discovery.json
```

The report records:

- endpoint name
- HTTP status
- response shape
- top-level response keys
- `result` keys, when present
- sample record keys, when a list is returned
- likely meeting and agenda endpoints

The report is discovery output. It should be reviewed before adding canonical `Meeting` and `AgendaItem` models.

## How to run

Use GitHub Actions:

```text
Actions -> Discover RIS API -> Run workflow
```

Recommended first run:

```text
municipality: huizen
limit: 3
endpoints: leave empty
commit_report: false
```

If the report is useful and should be preserved:

```text
commit_report: true
```

## Next step

After identifying stable endpoints and response shapes, issue #15 can add:

- `Meeting` model
- `AgendaItem` model
- `meetings.jsonl`
- `agenda_items.jsonl`
- document relation exports
