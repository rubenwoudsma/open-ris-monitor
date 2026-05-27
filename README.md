# Open RIS Monitor

Open RIS Monitor is een generieke, forkbare open-data-pipeline voor publieke raadsinformatie uit gemeentelijke raadsinformatiesystemen [RIS]. De eerste implementatie richt zich op de gemeente Huizen en het RIS van leverancier GemeenteOplossingen.

## Doelen

- Publieke raadsinformatie beter vindbaar en herbruikbaar maken.
- Niet alleen een viewer bouwen, maar een reproduceerbare dataketen.
- Een generieke structuur maken die door andere gemeenten of inwoners kan worden geforkt.
- Binnen GitHub, GitHub Actions en GitHub Pages kunnen draaien.

## Milestone 1

Milestone 1 is document-first en metadata-only:

1. Lees `config/municipalities/huizen.yml`.
2. Haal de laatste documenten op via de GemeenteOplossingen API.
3. Schrijf raw output naar `data/raw/latest/documents.json`.
4. Commit geen PDF-bestanden.

## Handmatige harvest

```bash
python -m open_ris_monitor.pipeline.run --municipality huizen --limit 25
```

## Repo-indeling

```text
config/municipalities/   Gemeenteconfiguraties
docs/                    Architectuur en ontwerpdocumentatie
src/open_ris_monitor/    Python package
data/                    Lokale en gepubliceerde data
site/                    Statische website voor GitHub Pages
tests/                   Tests
.github/workflows/       GitHub Actions
```
