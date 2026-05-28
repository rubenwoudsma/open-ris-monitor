# Roadmap

Deze roadmap beschrijft de gefaseerde ontwikkeling van Open RIS Monitor. Het uitgangspunt is dat elke fase een werkende, kleine uitbreiding oplevert en dat de repository forkbaar blijft voor andere gemeenten.

## Afgerond

### Milestone 1, document-first harvest

Status: afgerond.

Resultaat:

- Gemeente Huizen is als eerste configuratie toegevoegd.
- De GemeenteOplossingen connector kan de laatste documenten ophalen.
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

## Actueel

### Issue #9, automatisch bijwerken van `data/public` na harvest

Doel:

Na een handmatige harvest moet de workflow de gegenereerde public exports automatisch kunnen terugschrijven naar de repository, zodat GitHub Pages direct de nieuwste publieke data toont.

Scope:

- `data/public/` mag automatisch worden gecommit.
- `data/raw/` blijft artifact-only.
- PDF-bestanden worden niet gecommit.
- De workflow moet ook zonder commit kunnen draaien voor testdoeleinden.

Acceptatiecriteria:

- De harvest-workflow heeft een input `commit_public`.
- Bij `commit_public: true` commit de workflow alleen wijzigingen onder `data/public/`.
- Bij `commit_public: false` worden alleen artifacts gemaakt.
- Als er geen wijzigingen zijn, maakt de workflow geen lege commit.
- README beschrijft het publicatiebeleid.

## Volgende issues

### Issue #11, volledige document-harvest met paginering

Doel:

De harvester moet meer dan de laatste 25 documenten kunnen ophalen door het GemeenteOplossingen `documents` endpoint in batches te benaderen.

Voorlopige richting:

- `totalCount` ophalen.
- `limit` en `offset` gebruiken.
- `fetch_all_documents` toevoegen aan de connector.
- Duplicaten voorkomen op basis van `source_id`.
- Een configureerbare limiet behouden, zodat test-runs klein kunnen blijven.

### Issue #12, document_versions en checksum metadata

Doel:

Documentwijzigingen detecteerbaar maken zonder PDF's structureel in Git op te slaan.

Voorlopige richting:

- PDF's tijdelijk downloaden tijdens de workflow.
- SHA256 en bestandsgrootte vastleggen.
- `document_versions.jsonl` toevoegen.
- PDF's niet committen.

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

### Issue #14, meetings en agenda-items endpoints onderzoeken

Doel:

Onderzoeken hoe GemeenteOplossingen vergaderingen en agendapunten ontsluit, zodat documenten later aan de juiste context kunnen worden gekoppeld.

Voorlopige richting:

- API-endpoints inventariseren.
- Relaties tussen documenten, objectId, vergaderingen en agendapunten onderzoeken.
- Canonieke modellen uitbreiden met `Meeting` en `AgendaItem`.

## Latere richting

Na deze issues kan het project doorgroeien naar:

- tekstextractie uit PDF's
- linked data of JSON-LD export
- dossierclustering
- ondersteuning voor meerdere gemeenten
- ondersteuning voor meerdere RIS-leveranciers
- automatische dagelijkse harvests
