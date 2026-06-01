# GemeenteOplossingen API route map

This document records the routes that are relevant for moving from a document-only harvest to meetings, meeting items and document relations.

## Confirmed by live discovery

The first discovery run against `https://ris.gemeenteraadhuizen.nl/api/v2/` showed that these list endpoints respond successfully:

- `/documents`
- `/meetings`
- `/meetingsessions`
- `/events`

The discovery run also showed that generic agenda endpoints such as `/agendas`, `/agenda`, `/agendaItems`, `/agendaitems` and `/agenda-items` return HTTP 400. Agenda items are therefore not exposed as a top-level collection in this API.

## Relevant documented routes

The API documentation describes the following routes as relevant for the next phase.

### Meetings

- `GET /meetings`
- `GET /meetings/{meetingId}`
- `GET /dmus/`
- `GET /dmus/{dmuId}/meetings`

### Meeting items

- `GET /meetings/{meetingId}/meetingitems`
- `GET /meetingitems/{meetingItemId}`

### Document relations

- `GET /meetings/{meetingId}/documents`
- `GET /meetingitems/{meetingItemId}/documents`
- `GET /documents/{documentId}`
- `GET /documents/{documentId}/download`

### Events and attachments

- `GET /events`
- `GET /events/{eventId}`
- `GET /events/{eventId}/attachments`
- `GET /attachments/{attachmentId}`
- `GET /attachments/{attachmentId}/download`

Events and attachments may be relevant later, but they should not be part of the first meeting and agenda item implementation unless the meeting/document routes turn out to be insufficient.

## Recommended interpretation

For this project, the term `AgendaItem` should map to the GemeenteOplossingen `meetingitem` resource.

That means:

```text
Meeting
  /meetings/{meetingId}
  /meetings

AgendaItem
  /meetingitems/{meetingItemId}
  /meetings/{meetingId}/meetingitems

Document relations
  /meetings/{meetingId}/documents
  /meetingitems/{meetingItemId}/documents
```

## Recommended next step

Before implementing canonical models for `Meeting` and `AgendaItem`, run the targeted relation discovery workflow. It selects a small number of meetings and probes:

- meeting details
- meeting items per meeting
- documents per meeting
- documents per meeting item

The output should be reviewed before implementing issue #15.
