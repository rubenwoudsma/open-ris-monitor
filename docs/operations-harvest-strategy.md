# Operationele harveststrategie

## Doel

Open RIS Monitor moet kunnen doorgroeien naar een volledige operationele versie zonder dat de GitHub-repository te groot wordt, workflows te lang lopen of ruwe data onnodig in Git terechtkomt.

De strategie is daarom:

```text
kleine herhaalbare stappen + compacte public exports + raw artifacts buiten Git
```

## Uitgangspunten

1. `data/public/` is het publieke contract.
2. `data/raw/` is tijdelijk en artifact-only.
3. PDF-bestanden worden niet in Git opgeslagen.
4. Full harvests zijn begrensd, hervatbaar en controleerbaar.
5. Relationele harvests zijn optioneel en configureerbaar.
6. Backfills worden in vensters uitgevoerd, niet als een onbeperkte alles-in-een-run.
7. Elke run moet kunnen rapporteren wat wel en niet is verwerkt.

## Huidige operationele basis

De huidige pipeline ondersteunt:

```text
latest mode
full mode
limit
batch_size
max_documents
include_relations
meeting_scan_limit
meeting_session_batch_size
meeting_item_limit
```

De relationele smoke-test toont aan dat een kleine live-run werkt met:

```text
10 documents seen
50 meeting sessions seen
33 meetings seen
200 meeting items seen
34 meeting-document relations seen
251 meeting-item-document relations seen
17 meetings skipped
```

## Aanbevolen harvestlagen

### 1. Snelle latest harvest

Doel: dagelijkse of handmatige controle.

```text
mode: latest
limit: 25
include_relations: false
```

Gebruik dit voor:

- snelle smoke tests
- nieuwe documenten signaleren
- viewer actueel houden
- lage workflowduur

### 2. Latest harvest met relationele context

Doel: recente documenten met vergadercontext publiceren.

```text
mode: latest
limit: 25
include_relations: true
meeting_scan_limit: 50
meeting_item_limit: 200
```

Gebruik dit voor:

- controleren dat de relationele keten gezond blijft
- recente vergaderingen en agenda-items verversen
- public exports bijwerken zonder volledige backfill

### 3. Bounded full harvest

Doel: dataset gecontroleerd uitbreiden.

```text
mode: full
batch_size: 100
max_documents: 500
include_relations: false
```

Gebruik dit voor:

- historische documentdekking uitbreiden
- repositorygroei monitoren
- verwerkingstijd meten

### 4. Relationele backfill in vensters

Doel: historische vergadercontext stapsgewijs uitbreiden.

```text
mode: latest
include_relations: true
meeting_scan_limit: 250
meeting_session_batch_size: 100
meeting_item_limit: 1000
```

Later kan dit beter worden gemaakt met expliciete vensters:

```text
meeting_session_offset
meeting_session_limit
from_date
to_date
```

## Waarom geen onbeperkte full harvest in een keer

Een onbeperkte full harvest is kwetsbaar:

- meer kans op API-timeouts
- meer kans op workflow-timeouts
- grotere commits
- grotere JSONL-bestanden
- moeilijker te debuggen
- lastiger te hervatten

Een operationeel systeem moet daarom per run klein genoeg blijven om betrouwbaar te zijn.

## GitHub-repositorybeleid

De repository moet klein en gezond blijven.

Wel in Git:

```text
data/public/*.jsonl
data/public/latest.json
data/public/quality/*.json
site/*
docs/*
src/*
tests/*
```

Niet in Git:

```text
data/raw/*
PDF-bestanden
volledige API-dumps
workflow artifacts
OCR-output
tekstextracties van alle PDF's
```

Mogelijk later extern opslaan:

```text
PDF-cache
full raw archive
large search index
full text index
```

## Public export compact houden

Public JSONL-bestanden moeten compact blijven:

- geen volledige raw API-records in public JSONL
- geen PDF-inhoud
- geen base64
- geen grote nested blobs
- alleen canonieke velden en noodzakelijke bron-ID's

Voor debugbaarheid blijft raw output beschikbaar als artifact tijdens tests en smoke-runs.

## Commitstrategie

Automatische commits naar `data/public/` moeten voorspelbaar blijven:

```text
1. generate public exports
2. compare with existing public exports
3. commit only when changed
4. keep commit message machine-readable
5. avoid committing raw data
```

Voor grote backfills is het beter om tijdelijke branches te gebruiken:

```text
backfill/huizen-documents-0000-0500
backfill/huizen-relations-2018-q3
```

Na controle kunnen de public outputs naar `main`.

## Resume-strategie

Voor volledige dekking is een checkpoint-mechanisme wenselijk.

Mogelijke opties:

```text
data/public/harvest_state.json
```

of:

```text
data/public/harvest_runs.jsonl
```

Met velden zoals:

```json
{
  "municipality_slug": "huizen",
  "source_system_id": "huizen-gemeenteoplossingen",
  "resource_type": "meeting_sessions",
  "last_successful_offset": 250,
  "last_successful_date": "2019-01-31",
  "updated_at": "2026-06-02T13:00:00Z"
}
```

## Kwaliteitschecks voor operationele runs

Minimale checks:

```text
- latest.json bestaat
- documents.jsonl bestaat
- harvest_runs.jsonl bestaat
- relation exports bestaan wanneer relations_enabled true is
- line counts zijn groter dan nul voor geactiveerde exports
- manifest verwijst naar bestaande bestanden
- JSONL is parsebaar
- relation IDs zijn uniek
- relation targets hebben het verwachte ID-patroon
```

Relationele checks:

```text
- meeting item verwijst naar bestaande meeting
- meeting-documentrelatie verwijst naar bestaande meeting
- meeting-item-documentrelatie verwijst naar bestaande meeting item
- documentrelatie verwijst naar canonieke document-ID
- skipped meetings worden geteld
```

## Pad naar operationele versie

### Fase 1, huidige MVP stabiliseren

- issue #15 afronden
- docs bijwerken
- tijdelijke smoke workflows opruimen of ombouwen
- PR naar `main`
- viewer minimaal relation-aware maken

### Fase 2, gecontroleerde historische dekking

- full document harvest in batches
- relationele backfill in vensters
- line counts en bestandsgroei monitoren
- kwaliteitsrapportage toevoegen

### Fase 3, publieke bruikbaarheid

- viewer uitbreiden met documentcontext
- downloadbare datasets beter documenteren
- datamodel versie geven
- voorbeeldqueries toevoegen

### Fase 4, bredere Open RIS-basis

- connector capability model
- tweede gemeente of tweede RIS-leverancier onderzoeken
- algemene documenttype-taxonomie
- relationele kwaliteitschecks
- externe opslagstrategie voor grote artefacten

## Beslissing voor nu

Voor issue #15 is het voldoende dat:

```text
- relationele harvest optioneel werkt
- public relation exports bestaan
- latest.json de relationele outputs beschrijft
- docs de nieuwe architectuur uitleggen
- operationele risico's expliciet zijn benoemd
```

Een volledige historische backfill hoeft niet in issue #15 te worden opgelost.
