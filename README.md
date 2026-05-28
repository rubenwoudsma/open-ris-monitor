# Open RIS Monitor

Open RIS Monitor is een open-data-pipeline en eenvoudige publicatiesite voor publieke raadsinformatie uit een gemeentelijk Raadsinformatiesysteem, RIS. De eerste implementatie richt zich op de gemeente Huizen en gebruikt de GemeenteOplossingen API.

Het project is bedoeld als herbruikbaar startpunt voor anderen die vergelijkbare RIS-data voor hun eigen gemeente willen ophalen, normaliseren en publiceren.

## Huidige status

De huidige versie is een metadata-only MVP.

Wat werkt nu:

- document-first harvest voor gemeente Huizen
- ophalen van de laatste documenten via het RIS documents-endpoint
- opslag van raw harvest-output als GitHub Actions artifact
- normalisatie naar een canoniek documentmodel
- public export naar JSONL en JSON
- eenvoudige GitHub Pages-site in `site/`
- optioneel automatisch committen van `data/public` na een handmatige harvest

Wat bewust nog niet in scope zit:

- PDF-bestanden structureel opslaan in Git
- tekstextractie uit PDF's
- checksums en documentversies
- vergaderingen en agendapunten
- linked data export
- automatische commit van `data/raw`

## Projectopzet

```text
open-ris-monitor/
  .github/workflows/       GitHub Actions voor validatie, harvest en sitechecks
  config/municipalities/   Gemeenteconfiguraties
  data/raw/                Ruwe API-output, voor analyse en debugging
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
  -> data/public
  -> optionele commit van data/public
  -> site/index.html
```

In de huidige MVP wordt `data/raw/latest` vooral als artifact beschikbaar gemaakt. `data/public` bevat de bestanden die bedoeld zijn voor hergebruik en voor de website. Via de harvest-workflow kan `data/public` automatisch terug naar de actieve branch worden gecommit.

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

Voor deze repository is de site beschikbaar via:

```text
https://rubenwoudsma.github.io/open-ris-monitor/site/
```

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

De workflow maakt twee artifacts:

```text
raw-harvest-huizen
public-export-huizen
```

Als `commit_public` op `true` staat, commit de workflow alleen de gegenereerde bestanden onder `data/public/` terug naar de actieve branch. `data/raw/` wordt niet automatisch gecommit en blijft artifact-only.

Voor testen op een featurebranch kun je `commit_public` tijdelijk op `false` zetten. De artifacts worden dan nog steeds gemaakt, maar de branch wordt niet automatisch aangepast.

## Publicatiebeleid voor data

Voor deze MVP geldt:

```text
data/raw      niet automatisch committen, alleen artifact voor debugging
data/public   wel bedoeld voor publicatie en GitHub Pages
PDF's         niet opslaan in Git
```

Deze keuze houdt de repository licht, terwijl de publieke website toch reproduceerbare data kan tonen.

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

- volledige document-harvest met paginering
- documentversies en checksums toevoegen
- kwaliteitsrapportage toevoegen
- later vergaderingen en agendapunten toevoegen
