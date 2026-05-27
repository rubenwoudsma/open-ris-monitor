# Source analysis, GemeenteOplossingen RIS API voor Huizen

## Status

Dit document hoort bij issue #1. De analyse is nu document-first, omdat de bestaande Huizen RIS Monitor beta al werkend gebruikmaakt van het documents-endpoint.

## Bewezen endpoint

Base URL:

```text
https://ris.gemeenteraadhuizen.nl/api/v2/
```

Document count:

```text
GET documents?limit=1
```

Verwacht responsepad:

```text
result.totalCount
```

Documenten ophalen:

```text
GET documents?limit={limit}&offset={offset}
```

Verwacht responsepad:

```text
result.documents
```

Documentdownload:

```text
GET documents/{document_id}/download
```

## MVP-besluit

Milestone 1 gebruikt een metadata-only aanpak:

- documenten ophalen via het bewezen endpoint
- raw JSON opslaan in `data/raw/latest/documents.json`
- geen PDF-bestanden committen
- geen tekstextractie in milestone 1

## Nog te valideren

- exacte veldnamen per documentrecord
- stabiele document-ID
- mogelijke endpoints voor vergaderingen
- mogelijke endpoints voor agendapunten
- relatievelden tussen documenten, vergaderingen en agendapunten
- volgorde van `documents` bij `offset` en `limit`

## Acceptatiecriteria voor issue #1

- het bewezen documents-endpoint is beschreven
- het responsepad `result.documents` is vastgelegd
- het downloadpatroon is vastgelegd
- open vragen voor meetings en agenda items zijn benoemd

## Eerste succesvolle harvest

Op 2026-05-27 is de eerste handmatige GitHub Actions harvest succesvol uitgevoerd.

Resultaat:
- documents_seen: 25
- meetings_seen: 0
- agenda_items_seen: 0
- status: success

De artifact bevatte:
- documents.json
- harvest_run.json

Conclusie:
Het endpoint `/documents?limit={limit}&offset={offset}` is bruikbaar voor een document-first MVP.
