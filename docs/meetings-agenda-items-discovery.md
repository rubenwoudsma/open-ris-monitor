# Meetings en agenda-items discovery

Dit document beschrijft de uitkomst van het onderzoek naar vergaderingen, agenda-items en documentrelaties in de GemeenteOplossingen RIS API voor gemeente Huizen.

De technische discovery-output staat in:

```text
data/public/quality/gemeenteoplossingen_relation_discovery.json
```

## Aanleiding

Voor de Open RIS Monitor was eerst alleen de document-harvest beschikbaar via:

```text
/documents
/documents/{documentId}
/documents/{documentId}/download
```

Voor verdere verrijking is onderzocht hoe documenten gekoppeld kunnen worden aan vergaderingen en agenda-items.

## Belangrijkste conclusie

Agenda-items bestaan in de GemeenteOplossingen API niet als top-level `agendaItems` endpoint. De juiste term en route is:

```text
/meetings/{meetingId}/meetingitems
```

Daarnaast blijkt `/meetings` alleen onvoldoende als ingang voor historische dekking. De endpoint `/meetings` geeft vooral recente en toekomstige vergaderingen terug. Voor historische vergaderingen is `/meetingsessions` belangrijk, omdat daarin `container.meeting.id` voorkomt.

De bruikbare route is daarom:

```text
/meetingsessions
  -> container.meeting.id
  -> /meetings/{meetingId}
  -> /meetings/{meetingId}/meetingitems
  -> /meetings/{meetingId}/documents
```

## Bewezen endpoints

De discovery heeft bevestigd dat de volgende endpoints bruikbaar zijn:

```text
GET /meetings
GET /meetingsessions
GET /dmus
GET /events
GET /meetings/{meetingId}
GET /meetings/{meetingId}/meetingitems
GET /meetings/{meetingId}/documents
GET /meetingitems/{meetingItemId}
GET /meetingitems/{meetingItemId}/documents
```

Voor issue #15 zijn vooral deze endpoints relevant:

```text
GET /meetings
GET /meetingsessions
GET /meetings/{meetingId}
GET /meetings/{meetingId}/meetingitems
GET /meetings/{meetingId}/documents
GET /meetingitems/{meetingItemId}/documents
```

## Resultaat van de discovery-run

De laatste relation discovery-run vond:

```text
meeting_items_discovered: 602
populated_meeting_count: 62
working_path_count: 295
```

Voorbeelden van gevonden vergaderingen met agenda-items en documenten:

```text
meeting_id 19
Raadsvergadering 05 Jul 2018
33 agenda-items
2 documenten

meeting_id 20
Raadsvergadering 12 Jul 2018
14 agenda-items
2 documenten

meeting_id 27
Commissie Sociaal Domein 11 september 2018
25 agenda-items
2 documenten

meeting_id 29
Raadsvergadering 27 Sep 2018
36 agenda-items
2 documenten
```

Hiermee is bewezen dat de API voldoende informatie bevat om vergaderingen, agenda-items en documentrelaties op te bouwen.

## Structuur van meetingitems

Een meetingitem bevat in de response onder andere de volgende velden:

```text
id
sortOrder
number
title
description
location
confidential
isHeading
meetingSession
meeting
status
```

De geneste `meeting` bevat onder andere:

```text
id
confidential
location
description
date
startTime
dmu
url
meetingLabel
```

De `dmu` bevat het orgaan, bijvoorbeeld:

```text
id
name
sortOrder
```

Voorbeelden van organen zijn:

```text
Raadsvergadering
Commissie Sociaal Domein
Commissie Fysiek Domein
Commissie Algemeen Bestuur en Middelen (ABM)
Collegevergadering
Conformbesluiten openbaar
```

## Structuur van vergaderdocumenten

Documenten op vergaderniveau bevatten dezelfde basisvelden als de bestaande document-harvest:

```text
id
objectId
confidential
fileName
documentTypeLabel
description
fileSize
publicationDate
isTabsignDocument
```

Deze documenten kunnen via `/meetings/{meetingId}/documents` aan een vergadering worden gekoppeld.

## Belangrijke nuance

Niet elke meeting ID uit `meetingsessions.container.meeting.id` levert een geldige response op via `/meetings/{meetingId}`. Sommige detailroutes geven `404`, terwijl de geneste documenten- en meetingitems-routes leeg terugkomen.

Dit moet niet als fatale fout worden gezien. De harvester moet hier defensief mee omgaan:

```text
- accepteer 404 als normale bronvariatie
- sla alleen records op die geldig en publiek bruikbaar zijn
- gebruik meetingsessions als kandidaatbron voor historische meeting IDs
- dedupliceer meetings op meeting_id
- dedupliceer meetingitems op meetingitem_id
- dedupliceer relaties op combinatie van bron en doel
```

## Aanbevolen canonieke entiteiten voor issue #15

Voor de eerste implementatie worden de volgende entiteiten aanbevolen:

```text
Meeting
MeetingItem
MeetingDocumentRelation
MeetingItemDocumentRelation
```

### Meeting

Minimale velden:

```text
id
source_system
municipality_slug
source_id
date
start_time
description
location
dmu_id
dmu_name
url
is_confidential
raw
```

### MeetingItem

Minimale velden:

```text
id
source_system
municipality_slug
source_id
meeting_id
meeting_session_id
sort_order
number
title
description
location
status_id
status_description
is_heading
is_confidential
raw
```

### MeetingDocumentRelation

Minimale velden:

```text
id
municipality_slug
source_system
meeting_id
document_id
relation_type
source_path
```

### MeetingItemDocumentRelation

Minimale velden:

```text
id
municipality_slug
source_system
meeting_item_id
document_id
meeting_id
relation_type
source_path
```

## Aanbevolen public exports voor issue #15

De volgende bestanden kunnen worden toegevoegd aan `data/public/`:

```text
meetings.jsonl
meeting_items.jsonl
meeting_documents.jsonl
meeting_item_documents.jsonl
```

De bestaande bestanden blijven bestaan:

```text
documents.jsonl
document_versions.jsonl
harvest_runs.jsonl
latest.json
```

## Implicatie voor de pipeline

De pipeline moet worden uitgebreid met een optionele relationele harveststap:

```text
1. Harvest documents
2. Harvest meetingsessions
3. Extract candidate meeting IDs
4. Fetch meeting details
5. Fetch meetingitems per meeting
6. Fetch meeting-level documents
7. Fetch meetingitem-level documents
8. Normalize entities
9. Export JSONL files
10. Update latest.json
```

Voor de eerste versie van issue #15 is het verstandig om dit begrensd te houden met parameters zoals:

```text
--include-relations
--meeting-scan-limit
--meeting-item-limit
```

## Conclusie

De GemeenteOplossingen API bevat voldoende informatie om documenten te koppelen aan vergaderingen en agenda-items.

Issue #14 kan hiermee inhoudelijk worden afgesloten. Issue #15 kan starten met de implementatie van de relationele harvest en de bijbehorende canonieke modellen.
