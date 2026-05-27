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
| Oorspronkelijke API-responses, compact en versieerbaar |
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

## Pipeline

```text
1. Configuratie lezen
2. Connector initialiseren
3. Brondata ophalen
4. Raw latest opslaan
5. Normaliseren naar canonieke objecten
6. Relaties leggen
7. PDF's tijdelijk downloaden, indien geconfigureerd
8. Checksums en tekstextractie maken
9. Kwaliteitsissues detecteren
10. Public exports genereren
11. Website bouwen of actualiseren
```

## Bronconnectors

Een connector vertaalt een specifiek RIS naar ruwe bronrecords. De rest van het systeem mag niet afhankelijk zijn van leverancier-specifieke details.

Minimaal connectorcontract:

```text
fetch_meetings()
fetch_agenda_items()
fetch_documents()
fetch_document_file()
```

## Publicatie

De publicatielaag levert stabiele bestanden op:

```text
data/public/meetings.jsonl
data/public/agenda_items.jsonl
data/public/documents.jsonl
data/public/document_versions.jsonl
data/public/quality_issues.jsonl
data/public/harvest_runs.jsonl
data/public/latest.json
```

Deze bestanden zijn de basis voor GitHub Pages, Streamlit of andere hergebruikers.
