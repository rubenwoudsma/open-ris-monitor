# Open RIS Monitor

Open RIS Monitor is een kleine, reproduceerbare open-data-pipeline voor publieke raadsinformatie. De eerste implementatie gebruikt de GemeenteOplossingen API van de gemeente Huizen.

Live viewer:

<https://rubenwoudsma.github.io/open-ris-monitor/site/index.html>

## Huidige status

De huidige MVP werkt document-first:

1. GitHub Actions haalt documentmetadata op uit het RIS.
2. De ruwe harvest wordt bewaard als tijdelijk artifact.
3. Documenten worden genormaliseerd naar een canoniek `Document` model.
4. `data/public/` wordt gegenereerd met JSONL en metadata.
5. GitHub Pages leest de bestanden uit `data/public/`.

## Harvest modes

De Harvest workflow ondersteunt twee modi.

### Latest mode

Haalt de meest recente documenten op.

Gebruik dit voor snelle controles en kleine updates.

```text
mode: latest
limit: 25
```

### Full mode

Haalt documenten in batches op met `limit` en `offset`.

Gebruik dit om de public dataset gecontroleerd uit te breiden.

```text
mode: full
batch_size: 100
max_documents: 500
```

`max_documents` is een veiligheidslimiet. Gebruik `0` alleen wanneer je bewust zonder expliciete cap wilt harvesten.

## Publicatiebeleid

- `data/public/` mag automatisch worden gecommit door de Harvest workflow.
- `data/raw/` blijft artifact-only en wordt niet automatisch gecommit.
- PDF-bestanden worden niet opgeslagen in Git.
- De eerste publieke viewer is bewust statisch en frameworkloos.

## Volgende milestones

- Volledige document-harvest met paginering verder valideren.
- Documentversies en checksums toevoegen.
- Kwaliteitsrapportage toevoegen.
- Meetings en agenda-items endpoints onderzoeken.
