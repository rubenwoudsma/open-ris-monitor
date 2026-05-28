# Roadmap

## Afgerond

### Milestone 1, document-first harvest

De eerste GitHub Actions harvest haalt documentmetadata op uit het GemeenteOplossingen documents-endpoint.

### Milestone 2, canonieke exports

Ruwe documenten worden genormaliseerd naar een canoniek `Document` model en gepubliceerd als JSONL.

### Milestone 3, publieke viewer

GitHub Pages toont een eenvoudige viewer bovenop `data/public/documents.jsonl` en `data/public/latest.json`.

### Milestone 4, automatische publicatie van public exports

De Harvest workflow kan `data/public/` automatisch terugcommitten naar de repo. `data/raw/` blijft artifact-only.

## In uitvoering

### Issue #11, volledige document-harvest met paginering

Doel: het documents-endpoint gecontroleerd in meerdere batches ophalen.

Scope:

- `latest` en `full` harvest modes.
- `batch_size` voor paginaformaat.
- `max_documents` als veiligheidslimiet.
- Deduplicatie op bron-ID.
- Duidelijke logging in GitHub Actions.
- Public exports blijven hetzelfde formaat houden.

## Volgende stappen

### Issue #12, document_versions en checksum metadata

Na volledige of grotere harvests kunnen documentversies en checksums worden toegevoegd.

### Issue #13, kwaliteitsrapportage

Kwaliteitsissues zoals ontbrekende titels, generieke bestandsnamen en grote bestanden kunnen apart worden gepubliceerd.

### Issue #14, meetings en agenda-items endpoints

Onderzoeken hoe documenten gekoppeld kunnen worden aan vergaderingen en agendapunten.
