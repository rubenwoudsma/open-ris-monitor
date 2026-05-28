# Architectuur

## Doel

Open RIS Monitor is opgezet als een kleine open-data-infrastructuur voor gemeentelijke raadsinformatie. De kern is niet de viewer, maar de dataketen.

De eerste implementatie richt zich op Huizen en de GemeenteOplossingen API. De architectuur moet echter generiek genoeg blijven om later ook andere gemeenten en andere RIS-leveranciers te ondersteunen.

## Huidige werkende keten

De huidige MVP werkt document-first:

```text
GemeenteOplossingen RIS API
  -> GitHub Actions harvest
  -> raw harvest-output, artifact-only
  -> normalisatie naar canoniek Document model
  -> data/public, committed public exports
  -> GitHub Pages-site in site/
```

Hiermee is de eerste verticale slice werkend: brondata ophalen, normaliseren, publiceren en tonen.

## Doelarchitectuur

```text
+------------------------------------------------------+
| Website / Viewer                                     |
| GitHub Pages, Streamlit, downloadbare datasets        |
+------------------------------------------------------+
                         |
                         v
+------------------------------------------------------+
| Publicatielaag                                       |
| JSONL, JSON, CSV, JSON-LD, zoekindex, rapportages     |
+------------------------------------------------------+
                         |
                         v
+------------------------------------------------------+
| Verrijkingslaag                                      |
| Checksums, tekstextractie, classificatie, kwaliteit   |
+------------------------------------------------------+
                         |
                         v
+------------------------------------------------------+
| Normalisatielaag                                     |
| Brondata naar canoniek RIS-model                      |
+------------------------------------------------------+
                         |
                         v
+------------------------------------------------------+
| Raw archief                                          |
| Oorspronkelijke API-responses, beperkt en controleerbaar |
+------------------------------------------------------+
                         |
                         v
+------------------------------------------------------+
| Bronconnectors                                       |
| GemeenteOplossingen, later andere leveranciers        |
+------------------------------------------------------+
```

## Ontwerpprincipes

1. De frontend is niet de bron van waarheid.
2. Bronconnectors zijn verwisselbaar.
3. Het canonieke datamodel is het contract tussen bron en publicatie.
4. Publicatie gebeurt zoveel mogelijk als gewone bestanden.
5. `data/public/` is de stabiele publicatielaag.
6. `data/raw/` is vooral bedoeld voor debugging, audit en tijdelijke inspectie.
7. PDF's worden niet standaard in Git opgeslagen.
8. Elke run is herleidbaar via `HarvestRun`.
9. Datakwaliteit wordt expliciet zichtbaar gemaakt.
10. Elke nieuwe fase moet de repo forkbaarder maken, niet afhankelijker van Huizen-specifieke aannames.

## Lagen

### 1. Bronconnectors

Een connector vertaalt een specifiek RIS naar ruwe bronrecords. De rest van het systeem mag niet afhankelijk zijn van leverancier-specifieke details.

Huidige connector:

```text
src/open_ris_monitor/connectors/gemeenteoplossingen.py
```

Huidige document-first functies:

```text
fetch_document_count()
fetch_documents(limit, offset)
fetch_latest_documents(limit)
build_document_download_url(document_id)
```

Doel voor latere fases:

```text
fetch_all_documents(batch_size, max_documents)
fetch_meetings()
fetch_agenda_items()
fetch_document_file(document_id)
```

### 2. Raw data

Raw data is de zo letterlijk mogelijke respons van het bronsysteem. Deze laag is nuttig voor debugging, analyse en controle.

Huidig beleid:

```text
data/raw/latest/ wordt tijdens de workflow gemaakt
data/raw/latest/ wordt als artifact geupload
data/raw/ wordt niet automatisch gecommit
```

Dit voorkomt dat de repository snel groeit door bronresponsen of tijdelijke bestanden.

### 3. Normalisatie

Normalisatie zet leverancier-specifieke bronrecords om naar canonieke objecten.

Voorbeeld:

```text
GemeenteOplossingen document
  -> canoniek Document
```

De website en exports mogen niet rechtstreeks afhankelijk zijn van velden zoals `documentTypeLabel` of `objectId`. Die velden worden gemapt naar canonieke velden zoals `document_type` en `source_object_id`.

### 4. Verrijking

Deze laag is grotendeels nog toekomstig. Voorbeelden:

```text
checksums
bestandsgroottecontrole
PDF-tekstextractie
document_versions
kwaliteitssignalen
dossier- of onderwerpclustering
```

Belangrijk: verrijking moet altijd onderscheid maken tussen officiele brondata en afgeleide projectdata.

### 5. Publicatie

De publicatielaag levert stabiele bestanden op voor hergebruik en website.

Huidig werkend:

```text
data/public/documents.jsonl
data/public/harvest_runs.jsonl
data/public/latest.json
```

Toekomstig:

```text
data/public/meetings.jsonl
data/public/agenda_items.jsonl
data/public/document_versions.jsonl
data/public/quality_issues.jsonl
data/public/relations.jsonl
data/public/jsonld/*.jsonld
```

### 6. Viewer

De huidige viewer is een frameworkloze GitHub Pages-site in:

```text
site/
```

De viewer leest alleen uit `data/public/`. Daarmee blijft de viewer vervangbaar. Een andere frontend, zoals Streamlit of een eigen dashboard, kan dezelfde public exports gebruiken.

## Pipeline

Huidige pipeline:

```text
1. Configuratie lezen
2. GemeenteOplossingen connector initialiseren
3. Laatste documenten ophalen
4. Raw latest opslaan
5. Normaliseren naar canonieke documenten
6. Public exports genereren
7. Artifacts uploaden
8. Optioneel data/public committen
9. GitHub Pages toont de actuele data
```

Toekomstige pipeline:

```text
1. Configuratie lezen
2. Connector initialiseren
3. Brondata ophalen met paginering
4. Raw latest opslaan
5. Normaliseren naar canonieke objecten
6. Relaties leggen
7. PDF's tijdelijk downloaden, indien geconfigureerd
8. Checksums en tekstextractie maken
9. Kwaliteitsissues detecteren
10. Public exports genereren
11. data/public bijwerken
12. Website toont actuele public exports
```

## Architectuurbesluit: data/public wel, data/raw niet automatisch committen

Voor de huidige fase geldt:

```text
data/public/ wordt automatisch bijgewerkt als commit_public=true
data/raw/ blijft artifact-only
```

Reden:

- `data/public/` is compact, stabiel en bedoeld voor hergebruik.
- `data/raw/` is bronafhankelijk, tijdelijker en kan snel groeien.
- De repository moet klein en forkbaar blijven.

## Relatie tot het datamodel

Het datamodel blijft richtinggevend. De huidige implementation gebruikt alleen `Document` en `HarvestRun`, maar de architectuur blijft voorbereid op:

```text
Municipality
SourceSystem
Meeting
AgendaItem
Document
DocumentVersion
HarvestRun
QualityIssue
Relation
```

Dit betekent dat de huidige document-first MVP geen eindmodel is, maar een werkende eerste doorsnede door de doelarchitectuur.
