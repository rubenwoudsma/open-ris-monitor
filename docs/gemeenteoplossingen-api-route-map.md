# GemeenteOplossingen API route map

This document records the routes discovered for the Huizen RIS implementation.

## Proven top-level routes

- `/documents`
- `/meetings`
- `/dmus`
- `/events`
- `/meetingsessions`

## Proven nested meeting routes

- `/meetings/{meetingId}`
- `/meetings/{meetingId}/documents`
- `/meetings/{meetingId}/meetingitems`
- `/meetingitems/{meetingItemId}`
- `/meetingitems/{meetingItemId}/documents`

## Discovery note

The `/meetings` endpoint returns recent and future meetings first. These may not yet have agenda items or documents. The `/meetingsessions` endpoint exposes historical meetings through `container.meeting.id`; those IDs are useful candidates for relation discovery.

## Next implementation target

Issue #15 should use the proven chain:

```text
meetings -> meetingitems -> documents
```

and should also preserve DMU information from each meeting.
