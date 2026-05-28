# Gemeente toevoegen

## Doel

Een nieuwe gemeente moet zoveel mogelijk via configuratie toegevoegd kunnen worden. Alleen wanneer een andere RIS-leverancier wordt gebruikt, is een nieuwe connector nodig.

Dit document beschrijft de gewenste route voor iemand die deze repo forked voor een eigen gemeente.

## Stap 1, fork of nieuwe branch maken

Fork de repository of maak een branch in een eigen repo.

Aanbevolen branchnaam:

```text
add-municipality-<gemeente-slug>
```

## Stap 2, configuratie kopieren

Kopieer:

```text
config/municipalities/example.yml
```

Naar:

```text
config/municipalities/<gemeente-slug>.yml
```

Voorbeeld:

```text
config/municipalities/huizen.yml
```

## Stap 3, basisgegevens invullen

Voorbeeld:

```yaml
municipality:
  name: Huizen
  slug: huizen
  official_identifier: gm0406
  country: NL
  website_url: https://www.huizen.nl
  ris_url: https://ris.gemeenteraadhuizen.nl
  timezone: Europe/Amsterdam
```

## Stap 4, bron instellen

Voor GemeenteOplossingen:

```yaml
source_system:
  vendor: GemeenteOplossingen
  connector: gemeenteoplossingen
  base_url: https://ris.gemeenteraadhuizen.nl/api/v2/
  api_version: v2
```

Als de gemeente een andere RIS-leverancier gebruikt, is waarschijnlijk een nieuwe connector nodig onder:

```text
src/open_ris_monitor/connectors/
```

## Stap 5, opslagbeleid kiezen

Voor een eerste test:

```yaml
storage:
  mode: metadata_only
  commit_pdf_files: false
```

Gebruik geen PDF-opslag in Git als standaardinstelling.

## Stap 6, eerste harvest testen zonder commit

Start de harvest via GitHub Actions:

```text
Actions -> Harvest -> Run workflow
```

Gebruik eerst:

```text
municipality: <gemeente-slug>
limit: 25
commit_public: false
```

Controleer daarna de artifacts:

```text
raw-harvest-<gemeente-slug>
public-export-<gemeente-slug>
```

## Stap 7, public exports controleren

Controleer minimaal:

```text
documents.jsonl
harvest_runs.jsonl
latest.json
```

Let op:

- Zijn er documenten opgehaald?
- Zijn de documenttitels bruikbaar?
- Zijn documenttypen gevuld?
- Werken de downloadlinks?
- Is de publicatiedatum beschikbaar?

## Stap 8, public exports committen

Als de test goed is, draai opnieuw met:

```text
commit_public: true
```

De workflow commit dan alleen:

```text
data/public/
```

De workflow commit niet:

```text
data/raw/
PDF-bestanden
tijdelijke downloadbestanden
```

## Stap 9, GitHub Pages controleren

Controleer de website:

```text
https://<gebruikersnaam>.github.io/open-ris-monitor/site/index.html
```

Controleer of de site de nieuwe gemeentegegevens en documenten toont.

## Stap 10, documenteer afwijkingen

Elke RIS-leverancier kan net andere velden of endpoints gebruiken. Leg afwijkingen vast in:

```text
docs/source-analysis-<leverancier>.md
```

Voorbeelden van belangrijke vragen:

- Welk endpoint levert documenten?
- Is er `totalCount` of andere paginering?
- Hoe worden vergaderingen ontsloten?
- Hoe worden agendapunten ontsloten?
- Is er een directe documentdownloadlink?
- Zijn relaties tussen documenten, vergaderingen en agendapunten beschikbaar?

## Minimale acceptatiecriteria voor een nieuwe gemeente

Een nieuwe gemeente is minimaal bruikbaar als:

- er een configuratiebestand bestaat
- de harvest workflow documenten kan ophalen
- `documents.jsonl` wordt gemaakt
- `latest.json` wordt gemaakt
- de GitHub Pages-site de documenten kan tonen
- PDF's niet in Git worden opgeslagen

## Richting voor verdere uitbreiding

Na een werkende document-first MVP kan de gemeente-uitbreiding doorgroeien naar:

- volledige harvest met paginering
- checksums en documentversies
- kwaliteitsrapportage
- meetings en agenda-items
- relaties tussen documenten en agendapunten
- JSON-LD of linked data exports
