# Architectuur

## Doel

Open RIS Monitor is opgezet als een kleine open-data-infrastructuur voor gemeentelijke raadsinformatie. De kern is niet de viewer, maar de dataketen.

## Lagen

```text
+------------------------------------------------------+
| Website / Viewer                                     |
| GitHub Pages, Streamlit, downloadbare datasets        |
+------------------------------------------------------+
                         |
                         v
+------------------------------------------------------+
| Publicatielaag                                       |
| JSON, JSONL, CSV, JSON-LD, zoekindex, rapportages     |
+------------------------------------------------------+
                         |
                         v
+------------------------------------------------------+
| Verrijkingslaag                                      |
| Tekstextractie, checksums, classificatie, relaties    |
+------------------------------------------------------+
                         |
                         v
+------------------------------------------------------+
| Normalisatielaag                                     |
| Brondata naar canoniek RIS-model                      |
+------------------------------------------------------+
                         |
                         v
+------------------------------------------------------+
| Raw archief                                          |
| Oorspronkelijke API-responses, artifact-only in MVP    |
+------------------------------------------------------+
                         |
                         v
+------------------------------------------------------+
| Bronconnectors                                       |
| GemeenteOplossingen, later andere leveranciers        |
+------------------------------------------------------+
```

## Ontwerpprincipes

1. De frontend is niet de bron van waarheid.
2. Bronconnectors zijn verwisselbaar.
3. Het canonieke datamodel is het contract tussen bron en publicatie.
4. Publicatie gebeurt zoveel mogelijk als gewone bestanden.
5. PDF's worden niet standaard in Git opgeslagen.
6. Elke run is herleidbaar via `HarvestRun`.
7. Datakwaliteit wordt expliciet zichtbaar gemaakt.
8. Grotere datasets worden stapsgewijs ondersteund met paginering en begrenzing.

## Huidige pipeline

```text
1. Configuratie lezen
2. Connector initialiseren
3. Brondata ophalen via latest of full mode
4. Raw latest opslaan als artifact
5. Normaliseren naar canonieke objecten
6. Public exports genereren
7. data/public optioneel terugcommitten
8. GitHub Pages-site leest data/public
```

## Bronconnectors

Een connector vertaalt een specifiek RIS naar ruwe bronrecords. De rest van het systeem mag niet afhankelijk zijn van leverancier-specifieke details.

Huidig document-first connectorcontract:

```text
fetch_document_count()
fetch_documents_page(limit, offset)
fetch_latest_documents(limit)
fetch_all_documents(batch_size, max_documents)
build_document_download_url(document_id)
```

Later wordt dit uitgebreid met:

```text
fetch_meetings()
fetch_agenda_items()
fetch_document_file()
```

## Publicatie

De publicatielaag levert stabiele bestanden op. In de huidige MVP zijn geïmplementeerd:

```text
data/public/documents.jsonl
data/public/harvest_runs.jsonl
data/public/latest.json
```

Gepland:

```text
data/public/meetings.jsonl
data/public/agenda_items.jsonl
data/public/document_versions.jsonl
data/public/quality_issues.jsonl
data/public/relations.jsonl
```

## Viewer

De viewer in `site/` is bewust frameworkloos. De site leest direct uit `data/public` en gebruikt client-side zoeken, filteren, sorteren en paginering. Daarmee blijft het project eenvoudig te forken en te hosten via GitHub Pages.
