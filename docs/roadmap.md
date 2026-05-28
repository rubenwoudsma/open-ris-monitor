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

### Milestone 4, automatisch bijwerken van data/public

Status: afgerond.

Gerelateerd issue:

```text
#9 Automatisch bijwerken van data/public na harvest
```

Resultaat:

- De harvest workflow heeft een input `commit_public`.
- Bij `commit_public: true` commit de workflow alleen wijzigingen onder `data/public/`.
- Bij `commit_public: false` worden alleen artifacts gemaakt.
- `data/raw/` blijft artifact-only.
- PDF-bestanden worden niet gecommit.
- GitHub Pages kan de nieuwste public exports tonen zonder handmatige upload.

## Actueel

### Documentatie bijwerken na publicatiemilestones

Doel:

De documentatie moet de huidige status van het project goed weergeven, zodat de repo begrijpelijk en forkbaar blijft.

Scope:

- README actualiseren.
- Architectuur actualiseren.
- Datamodel actualiseren.
- Opslagbeleid actualiseren.
- Handleiding voor nieuwe gemeenten actualiseren.

## Volgende technische issues

### Issue #11, volledige document-harvest met paginering

Doel:

De harvester moet meer dan de laatste 25 documenten kunnen ophalen door het GemeenteOplossingen `documents` endpoint in batches te benaderen.

Voorlopige richting:

- `totalCount` ophalen.
- `limit` en `offset` gebruiken.
- `fetch_all_documents` toevoegen aan de connector.
- Duplicaten voorkomen op basis van `source_id`.
- Een configureerbare limiet behouden, zodat test-runs klein kunnen blijven.
- Workflow input toevoegen voor `harvest_mode`, bijvoorbeeld `latest` of `full`.

### Issue #12, document_versions en checksum metadata

Doel:

Documentwijzigingen detecteerbaar maken zonder PDF's structureel in Git op te slaan.

Voorlopige richting:

- PDF's tijdelijk downloaden tijdens de workflow.
- SHA256 en bestandsgrootte vastleggen.
- `document_versions.jsonl` toevoegen.
- PDF's niet committen.
- Alleen metadata en checksums publiceren.

### Issue #13, kwaliteitsrapportage

Doel:

Datakwaliteit zichtbaar maken voor inwoners, journalisten, gemeente en hergebruikers.

Voorlopige signalen:

- generieke bestandsnamen
- ontbrekende publicatiedatum
- ontbrekend documenttype
- zeer grote bestanden
- mogelijk vertrouwelijke documenten
- dode downloadlinks
- ontbrekende relatie met vergadering of agendapunt

### Issue #14, meetings en agenda-items endpoints onderzoeken

Doel:

Onderzoeken hoe GemeenteOplossingen vergaderingen en agendapunten ontsluit, zodat documenten later aan de juiste context kunnen worden gekoppeld.

Voorlopige richting:

- API-endpoints inventariseren.
- Relaties tussen documenten, `objectId`, vergaderingen en agendapunten onderzoeken.
- Canonieke modellen uitbreiden met `Meeting` en `AgendaItem`.
- Relaties expliciet vastleggen in een `relations.jsonl` export.

## Latere richting

Na deze issues kan het project doorgroeien naar:

- tekstextractie uit PDF's
- JSON-LD export
- dossierclustering
- ondersteuning voor meerdere gemeenten
- ondersteuning voor meerdere RIS-leveranciers
- automatische dagelijkse harvests
- kwaliteitsdashboard per gemeente
- archiefstrategie buiten Git voor PDF-bestanden

## Architectuurbewaking

Bij iedere nieuwe milestone moet worden gecontroleerd of de wijziging past binnen deze uitgangspunten:

1. De public exports blijven het contract voor hergebruikers.
2. De viewer blijft vervangbaar.
3. Raw data blijft beperkt en wordt niet automatisch onbeperkt gecommit.
4. PDF's blijven buiten Git.
5. Nieuwe bronlogica hoort in connectors.
6. Nieuwe domeinlogica hoort in normalizers, models, enrichers of exporters.
7. Huizen-specifieke keuzes moeten zoveel mogelijk in configuratie blijven.
