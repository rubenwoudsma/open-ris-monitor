# Open RIS Monitor

Open RIS Monitor is een open-data-pipeline en eenvoudige publicatiesite voor publieke raadsinformatie uit een gemeentelijk Raadsinformatiesysteem, RIS. De eerste implementatie richt zich op de gemeente Huizen en gebruikt de GemeenteOplossingen API.

Het project is bedoeld als herbruikbaar startpunt voor anderen die vergelijkbare RIS-data voor hun eigen gemeente willen ophalen, normaliseren en publiceren.

## Huidige status

De huidige versie is een document-first, metadata-only MVP.

Wat werkt nu:

- document-first harvest voor gemeente Huizen
- ophalen van documenten via het GemeenteOplossingen `documents` endpoint
- opslag van raw harvest-output als GitHub Actions artifact
- normalisatie naar een canoniek documentmodel
- public export naar JSONL en JSON
- automatisch bijwerken van `data/public/` na een handmatige harvest, indien `commit_public` is ingeschakeld
- eenvoudige GitHub Pages-site in `site/`

Wat bewust nog niet in scope zit:

- PDF-bestanden structureel opslaan in Git
- tekstextractie uit PDF's
- checksums en documentversies
- volledige harvest met paginering
- vergaderingen en agendapunten
- linked data export
- automatische dagelijkse harvests

## Website

De publieke website is beschikbaar via:

```text
https://rubenwoudsma.github.io/open-ris-monitor/site/index.html
```

De website leest de publieke exportbestanden uit:

```text
data/public/latest.json
data/public/documents.jsonl
```

## Projectopzet

```text
open-ris-monitor/
  .github/workflows/       GitHub Actions voor validatie, harvest en sitechecks
  config/municipalities/   Gemeenteconfiguraties
  data/raw/                Ruwe API-output, vooral artifact-only
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
  -> data/public, committed public exports
  -> site/index.html, GitHub Pages viewer
```

Belangrijk uitgangspunt:

- `data/raw/` is bedoeld voor debugging, controle en tijdelijke inspectie.
- `data/public/` is bedoeld voor hergebruik, publicatie en de website.
- De frontend is niet de bron van waarheid. De public exports zijn dat.

## Publieke databestanden

De belangrijkste bestanden zijn:

```text
data/public/latest.json
data/public/documents.jsonl
data/public/harvest_runs.jsonl
```

`latest.json` bevat een samenvatting van de laatste export. `documents.jsonl` bevat een canoniek document per regel. `harvest_runs.jsonl` bevat informatie over uitgevoerde harvest-runs.

## Harvest handmatig draaien

De harvest wordt voorlopig handmatig gestart via GitHub Actions.

Ga naar:

```text
Actions -> Harvest -> Run workflow
```

Gebruik bijvoorbeeld:

```text
municipality: huizen
limit: 25
commit_public: true
```

De workflow maakt artifacts:

```text
raw-harvest-huizen
public-export-huizen
```

Als `commit_public` op `true` staat, commit de workflow alleen wijzigingen onder:

```text
data/public/
```

De workflow commit niet:

```text
data/raw/
PDF-bestanden
tijdelijke downloadbestanden
```

## Waarom PDF's niet in Git worden opgeslagen

PDF's kunnen groot zijn en Git bewaart historie. Daarom slaat de MVP geen PDF-bestanden structureel op in de repository. In latere fases kan de workflow PDF's tijdelijk downloaden om checksums, bestandsgrootte en tekstextractie te bepalen. De PDF zelf blijft dan buiten Git.

## Architectuur en datamodel

De architectuur blijft gericht op een generiek, forkbaar open-data-project. De kern is niet de website, maar de pipeline:

```text
bronconnector -> raw data -> normalisatie -> public exports -> viewer
```

Zie voor de details:

```text
docs/architecture.md
docs/data-model.md
docs/storage-policy.md
```

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

De eerstvolgende technische stap is volledige document-harvesting met paginering. Daarna volgen documentversies, checksums, kwaliteitsrapportage en onderzoek naar meetings en agenda-items.
