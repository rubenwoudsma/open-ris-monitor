# Open RIS Monitor

Open RIS Monitor is een kleine, reproduceerbare open-data-pipeline voor publieke raadsinformatie. De eerste implementatie gebruikt de GemeenteOplossingen API van de gemeente Huizen.

Live viewer:

```text
https://rubenwoudsma.github.io/open-ris-monitor/site/index.html
```

## Huidige status

De MVP is uitgebreid van document-first naar relationele publicatie:

1. GitHub Actions haalt documentmetadata op uit het RIS.
2. De ruwe harvest wordt bewaard als tijdelijk artifact.
3. Documenten worden genormaliseerd naar een canoniek `Document` model.
4. Optioneel worden vergaderingen, agendapunten en documentrelaties opgehaald.
5. Relationele data wordt genormaliseerd naar `Meeting`, `MeetingItem`, `MeetingDocumentRelation` en `MeetingItemDocumentRelation`.
6. `data/public/` wordt gegenereerd met JSONL en metadata.
7. GitHub Pages leest de bestanden uit `data/public/`.

## Public exports

De publieke dataset bestaat uit statische bestanden. Deze bestanden vormen het contract voor de viewer en voor hergebruikers.

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

`latest.json` verwijst naar de actuele outputs en bevat, wanneer relationele harvesting actief is, ook `relations_enabled` en `relations_summary`.

## Harvest modes

De Harvest workflow ondersteunt twee hoofdmodi.

### Latest mode

Haalt de meest recente documenten op. Gebruik dit voor snelle controles en kleine updates.

```text
mode: latest
limit: 25
```

Met relationele context:

```text
mode: latest
limit: 25
include_relations: true
meeting_scan_limit: 50
meeting_item_limit: 200
```

### Full mode

Haalt documenten in batches op met `limit` en `offset`. Gebruik dit om de public dataset gecontroleerd uit te breiden.

```text
mode: full
batch_size: 100
max_documents: 500
```

`max_documents` is een veiligheidslimiet. Gebruik `0` alleen wanneer je bewust zonder expliciete cap wilt harvesten.

## Publicatiebeleid

- `data/public/` mag automatisch worden gecommit door de Harvest workflow.
- `data/raw/` blijft artifact-only en wordt niet automatisch gecommit.
- PDF-bestanden worden niet opgeslagen in Git.
- Relationele harvest-output wordt als kleine JSONL-bestanden gepubliceerd.
- Grote of langdurige harvests moeten incrementeel en begrensd worden uitgevoerd.
- De eerste publieke viewer is bewust statisch en frameworkloos.

## Volgende milestones

- Relationele data tonen in de viewer.
- Kwaliteitsrapportage uitbreiden met relationele checks.
- Documenttypen normaliseren met behulp van relationele context.
- Harveststrategie verder operationaliseren voor volledige historische dekking.
- Onderzoek naar ondersteuning voor andere RIS-leveranciers.
