# Meetings en agenda-items discovery

## Status

Deze discovery is afgerond. De uitkomst is gebruikt als basis voor issue #15.

## Conclusie

De GemeenteOplossingen API bevat voldoende informatie om documenten te koppelen aan vergaderingen en agendapunten.

De juiste route is niet een top-level `agendaItems` endpoint, maar de combinatie van meetingsessions, meetings, meetingitems en documentroutes.

## Werkende keten

```text
/meetingsessions
  -> container.meeting.id
  -> /meetings/{meetingId}
  -> /meetings/{meetingId}/meetingitems
  -> /meetings/{meetingId}/documents
  -> /meetingitems/{meetingItemId}/documents
```

## Belangrijke bevindingen

- `/meetingsessions` is nodig voor historische dekking.
- `/meetings` is vooral nuttig voor recente of toekomstige vergaderingen.
- Niet elke meeting ID uit `/meetingsessions` resolveert via `/meetings/{meetingId}`.
- Een 404 op meeting detail is bronvariatie en mag de harvest niet laten falen.
- Meeting items bevatten voldoende velden voor een canoniek agendapunt.
- Documenten zijn zowel op vergaderniveau als op agendapuntniveau vindbaar.

## Implementatie in issue #15

Issue #15 implementeert deze discovery in vier lagen:

```text
1. Connector endpoints
2. Optional raw relation harvest
3. Canonical relation normalization
4. Public relation exports
```

Geimplementeerde public exports:

```text
data/public/meetings.jsonl
data/public/meeting_items.jsonl
data/public/meeting_documents.jsonl
data/public/meeting_item_documents.jsonl
```

## Smoke-testresultaat

Een live smoke test voor Huizen leverde op:

```json
{
  "candidate_meetings_seen": 50,
  "meeting_document_relations_seen": 34,
  "meeting_item_document_relations_seen": 251,
  "meeting_items_seen": 200,
  "meeting_sessions_seen": 50,
  "meetings_seen": 33,
  "meetings_skipped": 17
}
```

Dit bevestigt dat de relationele route bruikbaar is voor de MVP.

## Vervolg

De discovery zelf is afgerond. Vervolgwerk hoort thuis in:

- issue #15 voor implementatie en PR-afronding
- issue #13 voor kwaliteitsrapportage
- issue #21 voor documenttypenormalisatie
- toekomstige viewer-issues voor relationele presentatie
