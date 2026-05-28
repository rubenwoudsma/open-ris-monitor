# Architectuur

Open RIS Monitor bestaat uit een kleine gelaagde pipeline.

```text
RIS API
  -> Bronconnector
  -> Raw harvest output
  -> Normalisatie
  -> Public exports
  -> GitHub Pages viewer
```

## Bronconnector

De connector bevat bron-specifieke logica. Voor Huizen is dit de GemeenteOplossingen API v2.

De connector levert raw records op. Hij normaliseert niet.

Belangrijke documentfuncties:

```text
fetch_document_count()
fetch_documents_page(limit, offset)
fetch_latest_documents(limit)
fetch_all_documents(batch_size, max_documents)
build_document_download_url(document_id)
```

## Raw harvest

Raw output wordt geschreven naar `data/raw/latest/` tijdens de workflow-run. Deze data wordt als artifact geupload en niet automatisch gecommit.

## Normalisatie

De normalisatielaag zet bron-specifieke documenten om naar het canonieke `Document` model.

## Public exports

`data/public/` bevat herbruikbare, lichte exports.

```text
data/public/documents.jsonl
data/public/harvest_runs.jsonl
data/public/latest.json
```

Deze bestanden mogen automatisch worden gecommit.

## Viewer

De viewer in `site/` leest direct uit `data/public/`. Er is geen backend of build-stap nodig.

## Harvest modes

De pipeline ondersteunt twee modi:

- `latest`, bedoeld voor snelle updates.
- `full`, bedoeld voor paginated harvesting in batches.

Full mode gebruikt `batch_size` en `max_documents`, zodat grotere harvests gecontroleerd kunnen worden uitgevoerd.
