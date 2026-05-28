# Open RIS Monitor

Open RIS Monitor is een open-data-pipeline en eenvoudige publicatiesite voor publieke raadsinformatie uit een gemeentelijk Raadsinformatiesysteem, RIS. De eerste implementatie richt zich op de gemeente Huizen en gebruikt de GemeenteOplossingen API.

Het project is bedoeld als herbruikbaar startpunt voor anderen die vergelijkbare RIS-data voor hun eigen gemeente willen ophalen, normaliseren en publiceren.

## Huidige status

De huidige versie is een metadata-only MVP met een document-first aanpak.

Wat werkt nu:

- document-first harvest voor gemeente Huizen
- ophalen van documenten via het RIS `documents` endpoint
- ondersteuning voor `latest` en `full` harvest modes
- paginated full harvest met `batch_size` en `max_documents`
- opslag van raw harvest-output als GitHub Actions artifact
- normalisatie naar een canoniek documentmodel
- automatische public export naar `data/public`
- eenvoudige GitHub Pages-site in `site/`
- documentviewer met zoeken, filteren, sorteren en paginering

Wat bewust nog niet in scope zit:

- PDF-bestanden structureel opslaan in Git
- tekstextractie uit PDF's
- checksums en documentversies
- kwaliteitsrapportage
- vergaderingen en agendapunten
- linked data export

## Projectopzet

```text
open-ris-monitor/
  .github/workflows/       GitHub Actions voor validatie, harvest en sitechecks
  config/municipalities/   Gemeenteconfiguraties
  data/raw/                Ruwe API-output, artifact-only voor analyse en debugging
  data/public/             Publieke exportbestanden voor hergebruik en website
  docs/                    Architectuur, datamodel, roadmap en handleidingen
  site/                    Statische viewer voor GitHub Pages
  src/open_ris_monitor/    Python-code voor connectors, normalisatie en export
  tests/                   Tests voor modellen, normalisatie en exports
```

## Dataflow

```text
GemeenteOplossingen RIS API
  -> GitHub Actions harvest
  -> data/raw/latest, artifact-only
  -> normalisatie naar canoniek model
  -> data/public, automatisch commitbaar
  -> site/index.html
```

`data/raw/latest` wordt vooral als artifact beschikbaar gemaakt. `data/public` bevat de bestanden die bedoeld zijn voor hergebruik en voor de website.

## Publieke databestanden

De belangrijkste bestanden zijn:

```text
data/public/latest.json
data/public/documents.jsonl
data/public/harvest_runs.jsonl
```

`latest.json` bevat een samenvatting van de laatste export. `documents.jsonl` bevat één canoniek document per regel. `harvest_runs.jsonl` bevat informatie over uitgevoerde harvest-runs.

## Website

De statische website staat in:

```text
site/index.html
```

De site leest de publieke exportbestanden uit:

```text
data/public/latest.json
data/public/documents.jsonl
```

Voor deze repository is de website bereikbaar via:

```text
https://rubenwoudsma.github.io/open-ris-monitor/site/
```

De viewer ondersteunt:

- zoeken op titel, bestandsnaam, type en bron-id
- filteren op documenttype
- sorteren op datum, titel, type en bestandsgrootte
- paginering voor grotere datasets
- horizontaal scrollbare tabelcontainer

## Harvest handmatig draaien

De harvest wordt voorlopig handmatig gestart via GitHub Actions.

Ga naar:

```text
Actions -> Harvest -> Run workflow
```

Voor een kleine test:

```text
municipality: huizen
mode: latest
limit: 25
commit_public: false
```

Voor een grotere, begrensde harvest:

```text
municipality: huizen
mode: full
batch_size: 100
max_documents: 500
commit_public: true
```

De workflow maakt artifacts voor raw en public output. Bij `commit_public: true` wordt alleen `data/public/` teruggeschreven naar de repository.

## Waarom PDF's niet in Git worden opgeslagen

PDF's kunnen groot zijn en Git bewaart historie. Daarom slaat de MVP geen PDF-bestanden structureel op in de repository. In latere fases kan de workflow PDF's tijdelijk downloaden om checksums, bestandsgrootte en tekstextractie te bepalen, maar de PDF zelf blijft dan buiten Git.

## Een andere gemeente toevoegen

Een nieuwe gemeente krijgt een eigen configuratiebestand onder:

```text
config/municipalities/<slug>.yml
```

Voor een gemeente met dezelfde leverancier kan de bestaande GemeenteOplossingen connector mogelijk opnieuw worden gebruikt. Voor andere leveranciers komt er een nieuwe connector onder:

```text
src/open_ris_monitor/connectors/
```

Zie ook:

```text
docs/adding-a-municipality.md
```

## Roadmap

De actuele roadmap staat in:

```text
docs/roadmap.md
```

De eerstvolgende stappen zijn:

- documentversies en checksums toevoegen
- kwaliteitsrapportage toevoegen
- meetings en agenda-items endpoints onderzoeken
- documenten koppelen aan vergaderingen en agendapunten
