# Open RIS Monitor

Open RIS Monitor is een generieke, forkbare open-data-pipeline voor publieke raadsinformatie uit gemeentelijke raadsinformatiesystemen [RIS].

De eerste implementatie richt zich op de gemeente Huizen en het RIS van leverancier GemeenteOplossingen. Het doel is om publieke raadsinformatie periodiek op te halen, te normaliseren naar een canoniek datamodel, licht te verrijken en te publiceren als herbruikbare open bestanden.

## Doelen

- Publieke raadsinformatie beter vindbaar en herbruikbaar maken.
- Niet alleen een viewer bouwen, maar een reproduceerbare dataketen.
- Een generieke structuur maken die door andere gemeenten of inwoners kan worden geforkt.
- Metadata, relaties, tekstextracten, checksums en kwaliteitsrapportages publiceren.
- Binnen GitHub, GitHub Actions en GitHub Pages kunnen draaien.

## Niet-doelen voor de eerste versie

- Geen volledig PDF-archief in Git.
- Geen eigen backend of database-server.
- Geen volledige RDF-triplestore.
- Geen ondersteuning voor alle RIS-leveranciers in de eerste versie.
- Geen AI-samenvattingen als basisfunctionaliteit.

## Architectuur

De oplossing bestaat uit lagen:

1. Bronconnectors
2. Raw archief
3. Normalisatie naar canoniek datamodel
4. Verrijking
5. Publicatie als bestanden
6. Website of viewer

Zie [`docs/architecture.md`](docs/architecture.md) voor de uitgebreide beschrijving.

## Canoniek datamodel

Het project gebruikt een eigen minimaal canoniek model, geinspireerd op de gedachte achter Open Raadsinformatie, maar praktisch genoeg om binnen een kleine GitHub-gebaseerde pipeline te werken.

Belangrijkste entiteiten:

- Municipality
- SourceSystem
- Meeting
- AgendaItem
- Document
- DocumentVersion
- HarvestRun
- QualityIssue

Zie [`docs/data-model.md`](docs/data-model.md).

## Opslagstrategie

PDF-bestanden worden in de aanbevolen MVP-aanpak niet in Git opgeslagen. De pipeline kan PDF's tijdelijk downloaden om tekst, checksums en metadata te extraheren. Daarna worden alleen lichte afgeleide bestanden gepubliceerd.

Zie [`docs/storage-policy.md`](docs/storage-policy.md).

## Repo-indeling

```text
open-ris-monitor/
  config/municipalities/     Gemeenteconfiguraties
  docs/                      Architectuur en ontwerpdocumentatie
  src/open_ris_monitor/      Python package
  data/                      Lokale en gepubliceerde data
  site/                      Statische website voor GitHub Pages
  tests/                     Tests
  .github/workflows/         GitHub Actions
```

## Starten met Huizen

De configuratie voor Huizen staat in:

```text
config/municipalities/huizen.yml
```

## Ontwikkelvolgorde

1. Repo-structuur en documentatie neerzetten.
2. GemeenteOplossingen connector bouwen.
3. Raw API responses opslaan.
4. Canonieke modellen implementeren.
5. JSONL exports genereren.
6. Checksums, tekstextractie en kwaliteitsrapport toevoegen.
7. GitHub Pages site publiceren.
8. Forkbaarheid documenteren.

## Licentie

Voorstel: MIT voor code en CC0 of CC BY 4.0 voor gegenereerde metadata. Maak dit expliciet voordat de eerste publieke release wordt gemaakt.
