# GemeenteOplossingen API route map

This document records the API routes used by Open RIS Monitor for GemeenteOplossingen.

## Proven top-level routes

- `/documents`
- `/meetings`
- `/dmus`
- `/events`
- `/meetingsessions`

## Proven relation routes

- `/meetings/{meetingId}`
- `/meetings/{meetingId}/documents`
- `/meetings/{meetingId}/meetingitems`
- `/meetingitems/{meetingItemId}`
- `/meetingitems/{meetingItemId}/documents`

## Notes

Meeting items are not exposed through a top-level `/agendaItems` endpoint. The documented route is:

```text
/meetings/{meetingId}/meetingitems
```

`meetingsessions` can contain `container.meeting.id`. These IDs are useful for discovering historical meetings with actual agenda structure, because the newest meetings can be future meetings without agenda items or documents yet.

Manual IDs supplied to the discovery workflow must be meeting IDs. If `/meetings/{id}` returns 404, the supplied value is probably not a meeting ID.
