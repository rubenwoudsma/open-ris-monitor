# Roadmap

Deze roadmap beschrijft de gefaseerde ontwikkeling van Open RIS Monitor. Het uitgangspunt is dat elke fase een werkende, kleine uitbreiding oplevert en dat de repository forkbaar blijft voor andere gemeenten.

## Afgerond

### Milestone 1, document-first harvest

Status: afgerond.

Resultaat:

- Gemeente Huizen is als eerste configuratie toegevoegd.
- De GemeenteOplossingen connector kan documenten ophalen.
- De harvest draait via GitHub Actions.
- Raw harvest-output wordt als artifact beschikbaar gemaakt.

### Milestone 2, canonieke modellen en publieke exports

Status: afgerond.

Resultaat:

- Raw GemeenteOplossingen-documenten worden genormaliseerd naar een canoniek documentmodel.
- De pipeline maakt `documents.jsonl`, `harvest_runs.jsonl` en `latest.json`.
- De public export wordt als artifact beschikbaar gemaakt.

### Milestone 3, publieke site

Status: afgerond.

Resultaat:

- Een eenvoudige frameworkloze GitHub Pages-site is toegevoegd in `site/`.
- De site leest `data/public/latest.json` en `data/public/documents.jsonl`.
- De site toont harvestinformatie, documenttypen, zoekfunctie en documentlinks.

### Issue #9, automatisch bijwerken van `data/public` na harvest

Status: afgerond.

Resultaat:

- De harvest-workflow heeft een input `commit_public`.
- Bij `commit_public: true` commit de workflow alleen wijzigingen onder `data/public/`.
- Bij `commit_public: false` worden alleen artifacts gemaakt.
- `data/raw/` blijft artifact-only.

### Issue #11, volledige document-harvest met paginering

Status: afgerond.

Resultaat:

- De workflow ondersteunt `latest` en `full` harvest modes.
- De GemeenteOplossingen connector ondersteunt paginering met `limit` en `offset`.
- `batch_size` en `max_documents` houden grotere harvests beheersbaar.
- De public exportstructuur blijft gelijk, zodat de site dezelfde data kan blijven lezen.

### Issue #18, documentviewer geschikt voor grotere datasets

Status: afgerond na merge van deze wijziging.

Resultaat:

- De documentviewer toont niet meer alle documenten in één lange tabel.
- De viewer ondersteunt paginering, page size, sortering en filters.
- De horizontale scrollbar is beschikbaar rond de tabelcontainer.
- Lange titels en bestandsnamen breken beter af.
- De oplossing blijft frameworkloos en geschikt voor GitHub Pages.

## Volgende issues

### Issue #12, document_versions en checksum metadata

Doel: documentwijzigingen detecteerbaar maken zonder PDF's structureel in Git op te slaan.

Voorlopige richting:

- PDF's tijdelijk downloaden tijdens de workflow.
- SHA256 en bestandsgrootte vastleggen.
- `document_versions.jsonl` toevoegen.
- PDF's niet committen.

### Issue #13, kwaliteitsrapportage

Doel: datakwaliteit zichtbaar maken voor inwoners, journalisten, gemeente en hergebruikers.

Voorlopige signalen:

- generieke bestandsnamen
- ontbrekende publicatiedatum
- ontbrekend documenttype
- zeer grote bestanden
- mogelijk vertrouwelijke documenten
- dode downloadlinks

### Issue #14, meetings en agenda-items endpoints onderzoeken

Doel: onderzoeken hoe GemeenteOplossingen vergaderingen en agendapunten ontsluit, zodat documenten later aan de juiste context kunnen worden gekoppeld.

Voorlopige richting:

- API-endpoints inventariseren.
- Relaties tussen documenten, `objectId`, vergaderingen en agendapunten onderzoeken.
- Canonieke modellen uitbreiden met `Meeting` en `AgendaItem`.

### Issue #15, documenten koppelen aan vergaderingen en agendapunten

Doel: de document-first dataset uitbreiden met context, zodat documenten niet alleen als losse bestanden worden getoond.

Voorlopige richting:

- `Meeting` en `AgendaItem` modellen implementeren.
- Relaties publiceren in `relations.jsonl` of via velden op `Document`.
- De site uitbreiden met contextkolommen of dossierweergave.

## Latere richting

Na deze issues kan het project doorgroeien naar:

- tekstextractie uit PDF's
- linked data of JSON-LD export
- dossierclustering
- ondersteuning voor meerdere gemeenten
- ondersteuning voor meerdere RIS-leveranciers
- automatische dagelijkse harvests
