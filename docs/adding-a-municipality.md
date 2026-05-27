# Gemeente toevoegen

## Doel

Een nieuwe gemeente moet zoveel mogelijk via configuratie toegevoegd kunnen worden. Alleen wanneer een andere RIS-leverancier wordt gebruikt, is mogelijk een nieuwe connector nodig.

## Stap 1, configuratie kopieren

Kopieer:

```text
config/municipalities/example.yml
```

Naar:

```text
config/municipalities/{gemeente-slug}.yml
```

## Stap 2, basisgegevens invullen

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

## Stap 3, bron instellen

```yaml
source_system:
  vendor: GemeenteOplossingen
  connector: gemeenteoplossingen
  base_url: https://ris.gemeenteraadhuizen.nl/api/v2/
  api_version: v2
```

## Stap 4, opslagbeleid kiezen

```yaml
storage:
  mode: metadata_plus_text
  commit_pdf_files: false
```

## Stap 5, test-run uitvoeren

```bash
python -m open_ris_monitor.pipeline.run --config config/municipalities/huizen.yml
```

## Stap 6, output controleren

Controleer minimaal:

- meetings.jsonl
- agenda_items.jsonl
- documents.jsonl
- quality_issues.jsonl
- latest.json
