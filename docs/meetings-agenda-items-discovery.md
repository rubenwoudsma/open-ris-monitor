# Meetings en agenda-items discovery

## Doel

Issue #14 onderzoekt welke GemeenteOplossingen API-endpoints gebruikt kunnen worden voor vergaderingen en agendapunten.

De huidige Open RIS Monitor is document-first. De volgende inhoudelijke stap is het vinden van brondata waarmee documenten kunnen worden gekoppeld aan vergaderingen en agendapunten.

## Waarom eerst discovery?

Het bewezen endpoint is `documents?limit={limit}&offset={offset}`. Voor meetings en agenda-items is nog niet zeker welke endpoints beschikbaar zijn, welke namen worden gebruikt en welke responsevormen terugkomen.

Daarom voegt deze milestone nog geen definitieve `Meeting` of `AgendaItem` pipeline toe. Eerst wordt een discovery-rapport gemaakt.

## Nieuwe workflow

Deze milestone voegt een handmatige workflow toe:

```text
.github/workflows/discover-ris-api.yml
```

De workflow test kandidaat-endpoints en schrijft een rapport naar:

```text
data/public/quality/gemeenteoplossingen_endpoint_discovery.json
```

Het rapport wordt als artifact gepubliceerd. Het wordt niet automatisch gecommit.

## Kandidaat-endpoints

De standaardlijst bevat onder andere:

```text
documents
meetings
meeting
meetingsessions
sessions
events
calendar
agendas
agenda
agendaItems
agendaitems
agenda-items
items
committees
councils
organizations
```

Niet elk endpoint hoeft te bestaan. HTTP 404 of 403 is bruikbare informatie voor de analyse.

## Acceptatiecriteria voor issue #14

- De discovery workflow kan handmatig draaien.
- Het bewezen `documents` endpoint wordt herkend.
- Mogelijke meetings- en agenda-endpoints worden getest.
- Het rapport bevat statuscodes, responsevormen, result keys en sample keys.
- Het rapport maakt duidelijk welke endpoints kandidaat zijn voor een volgende implementatiestap.

## Vervolg na issue #14

Als geschikte endpoints zijn gevonden, wordt issue #15 opgepakt:

```text
Koppel documenten aan vergaderingen en agendapunten
```

Daarvoor zijn minimaal nodig:

- canonieke `Meeting` records
- canonieke `AgendaItem` records
- relaties tussen `Document`, `Meeting` en `AgendaItem`
- public exports zoals `meetings.jsonl`, `agenda_items.jsonl` en `relations.jsonl`
