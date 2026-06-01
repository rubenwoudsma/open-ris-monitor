# GemeenteOplossingen API route map

This document records the relevant API routes for the Open RIS Monitor implementation.

## Proven top-level routes

The first discovery runs confirmed these top-level routes for Huizen:

- `/documents`
- `/meetings`
- `/dmus`
- `/events`
- `/meetingsessions`

## Meeting and agenda item routes

The GemeenteOplossingen API documentation uses `meetingitems` for agenda items. Agenda items are not exposed as a top-level `/agendaItems` endpoint.

Relevant routes:

- `/meetings`
- `/meetings/{meetingId}`
- `/meetings/{meetingId}/meetingitems`
- `/meetingitems/{meetingItemId}`
- `/meetings/{meetingId}/documents`
- `/meetingitems/{meetingItemId}/documents`

## Manual meeting ID discovery

The relation discovery workflow supports optional manual meeting IDs. This is useful when the newest meetings do not contain agenda items or documents.

Example input:

```text
42745,40215,40074
```

The workflow will probe:

- `/meetings/{id}`
- `/meetings/{id}/meetingitems`
- `/meetings/{id}/documents`

If meeting items are discovered, it will also probe:

- `/meetingitems/{meetingItemId}`
- `/meetingitems/{meetingItemId}/documents`

## Next implementation step

After finding populated meetings and meeting items, issue #15 can implement canonical exports:

- `meetings.jsonl`
- `agenda_items.jsonl`
- `relations.jsonl`
