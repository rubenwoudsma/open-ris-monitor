# Architectuur

## Doel

Open RIS Monitor is opgezet als een kleine open-data-infrastructuur voor gemeentelijke raadsinformatie. De kern is niet de viewer, maar de dataketen.

De pipeline moet brondata uit een RIS ophalen, normaliseren naar een canoniek model, publiceren als gewone bestanden en tonen in een statische viewer.

## Lagen

```text
+------------------------------------------------------+
| Website / Viewer                                     |
| GitHub Pages, statische site, downloadbare datasets  |
+------------------------------------------------------+
                          |
                          v
+------------------------------------------------------+
| Publicatielaag                                       |
| JSONL, JSON, zoekindexen, rapportages                |
+------------------------------------------------------+
                          |
                          v
+------------------------------------------------------+
| Verrijkingslaag                                      |
| Checksums, kwaliteit, documenttypen, relaties        |
+------------------------------------------------------+
                          |
                          v
+------------------------------------------------------+
| Normalisatielaag                                     |
| Brondata naar canoniek RIS-model                     |
+------------------------------------------------------+
                          |
                          v
+------------------------------------------------------+
| Raw harvest output                                   |
| Oorspronkelijke API-responses, artifact-only in MVP  |
+------------------------------------------------------+
                          |
                          v
+------------------------------------------------------+
| Bronconnectors                                       |
| GemeenteOplossingen, later andere leveranciers       |
+------------------------------------------------------+
```

## Ontwerpprincipes

1. De frontend is niet de bron van waarheid.
2. Bronconnectors zijn verwisselbaar.
3. Het canonieke datamodel is het contract tussen bron en publicatie.
4. Publicatie gebeurt zoveel mogelijk als gewone bestanden.
5. PDF's worden niet standaard in Git opgeslagen.
6. Elke run is herleidbaar via `HarvestRun` en `latest.json`.
7. Datakwaliteit wordt expliciet zichtbaar gemaakt.
8. Grotere datasets worden stapsgewijs ondersteund met paginering en begrenzing.
9. Relationele context wordt apart gepubliceerd, niet hard in documentrecords ingebakken.
10. De repository moet forkable blijven zonder database, backend of externe zoekmachine.

## Huidige pipeline

```text
1. Configuratie lezen
2. Connector initialiseren
3. Brondata ophalen via latest of full mode
4. Raw latest opslaan als artifact
5. Documenten normaliseren naar canonieke objecten
6. Optioneel relationele data ophalen
7. Meetings, meeting items en documentrelaties normaliseren
8. Public exports genereren
9. data/public optioneel terugcommitten
10. GitHub Pages-site leest data/public
```

## Document harvest

De documenttak blijft de basis van het systeem.

```text
/documents
  -> raw documents
  -> Document
  -> data/public/documents.jsonl
```

Documentversies en checksums worden apart gepubliceerd in:

```text
data/public/document_versions.jsonl
```

PDF-bestanden worden niet structureel in Git opgeslagen.

## Relationele harvest

Issue #15 voegt een optionele relationele harvest toe. De GemeenteOplossingen-route is:

```text
/meetingsessions
  -> container.meeting.id
  -> /meetings/{meetingId}
  -> /meetings/{meetingId}/meetingitems
  -> /meetings/{meetingId}/documents
  -> /meetingitems/{meetingItemId}/documents
```

Deze route wordt bewust optioneel gehouden via `--include-relations`, zodat snelle documentharvests klein blijven.

## Bronconnectors

Een connector vertaalt een specifiek RIS naar ruwe bronrecords. De rest van het systeem mag niet afhankelijk zijn van leverancier-specifieke details.

Huidig connectorcontract voor documenten:

```text
fetch_document_count()
fetch_documents_page(limit, offset)
fetch_latest_documents(limit)
fetch_all_documents(batch_size, max_documents)
build_document_download_url(document_id)
```

Uitgebreid connectorcontract voor relationele data:

```text
fetch_meeting_sessions_page(limit, offset)
fetch_meeting(meeting_id)
fetch_meeting_items(meeting_id)
fetch_meeting_documents(meeting_id)
fetch_meeting_item_documents(meeting_item_id)
```

`fetch_meeting(meeting_id)` mag `None` teruggeven wanneer de bron een meeting uit `/meetingsessions` niet via `/meetings/{meetingId}` beschikbaar maakt. Dat is bronvariatie, geen fatale fout.

## Normalisatie

De normalisatielaag zet bronrecords om naar stabiele canonieke records:

```text
Document
Meeting
MeetingItem
MeetingDocumentRelation
MeetingItemDocumentRelation
HarvestRun
```

Bron-ID's blijven altijd bewaard. Canonieke identifiers zijn stabiel en volgen het patroon:

```text
{municipality_slug}-{resource_type}-{source_id}
```

Voorbeelden:

```text
huizen-document-158
huizen-meeting-19
huizen-meeting-item-142
huizen-meeting-19-document-3127
huizen-meeting-item-142-document-158
```

## Publicatie

De publicatielaag levert stabiele bestanden op.

Geimplementeerd:

```text
data/public/documents.jsonl
data/public/document_versions.jsonl
data/public/harvest_runs.jsonl
data/public/meetings.jsonl
data/public/meeting_items.jsonl
data/public/meeting_documents.jsonl
data/public/meeting_item_documents.jsonl
data/public/latest.json
```

Gepland:

```text
data/public/quality_issues.jsonl
data/public/document_type_mappings.jsonl
data/public/search_index.json
```

## Viewer

De viewer in `site/` is bewust frameworkloos. De site leest direct uit `data/public` en gebruikt client-side zoeken, filteren, sorteren en paginering.

De huidige viewer draait op:

```text
https://rubenwoudsma.github.io/open-ris-monitor/site/index.html
```

De volgende viewerstap is relationele context tonen bij documenten:

```text
Document
  -> gekoppelde vergadering(en)
  -> gekoppelde agendapunt(en)
```

Later kan dit worden uitgebreid naar een agenda- en vergaderbrowser.

## Operationele strategie

Voor volledige historische dekking moet de harvest incrementeel blijven:

```text
1. Kleine scheduled latest harvests
2. Periodieke bounded full harvests
3. Relationele backfill in vensters
4. Public exports compact houden
5. Raw output als artifact bewaren, niet in Git
6. PDF's buiten Git houden
```

Zie `docs/operations-harvest-strategy.md` voor het operationele ontwerp.
