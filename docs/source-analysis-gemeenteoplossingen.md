# Source analysis: GemeenteOplossingen API, Huizen

## Status

De document-first harvest is bewezen via GitHub Actions. De workflow haalt documenten op uit het Huizer RIS en schrijft de ruwe output als artifact.

## Bewezen endpoint

Base URL:

```text
https://ris.gemeenteraadhuizen.nl/api/v2/
```

Documenten:

```text
GET /documents?limit={limit}&offset={offset}
```

Bewezen responsepad:

```text
result.documents
```

Telling:

```text
GET /documents?limit=1
result.totalCount
```

Downloadpatroon:

```text
GET /documents/{id}/download
```

## Eerste succesvolle harvest

Op 2026-05-27 is een handmatige GitHub Actions harvest succesvol uitgevoerd.

Resultaat:

```text
documents_seen: 25
meetings_seen: 0
agenda_items_seen: 0
status: success
```

De artifact bevatte:

```text
documents.json
harvest_run.json
```

Conclusie: het endpoint `/documents?limit={limit}&offset={offset}` is bruikbaar voor een document-first MVP.

## Beschikbare bronvelden in documentrecords

De eerste harvest bevestigt onder andere deze velden:

| Bronveld | Betekenis | Canoniek veld |
|---|---|---|
| `id` | Document-ID in bron | `source_id` |
| `objectId` | Object-ID in bron | `source_object_id` |
| `description` | Omschrijving/titel | `title`, `description` |
| `documentTypeLabel` | Type document | `document_type` |
| `fileName` | Bestandsnaam | `filename` |
| `fileSize` | Bestandsgrootte in bytes | `file_size_bytes` |
| `publicationDate.date` | Publicatiedatum | `publication_datetime` |
| `publicationDate.timezone` | Tijdzone | `publication_timezone` |
| `confidential` | Vertrouwelijkheidsindicator | `is_confidential` |
| `isTabsignDocument` | Tabsign-indicator | `is_tabsign_document` |

## Open punten

Voor latere issues moeten nog worden onderzocht:

- endpoints voor vergaderingen;
- endpoints voor agendapunten;
- relatie tussen document, vergadering en agendapunt;
- eventuele detail-endpoints voor documentmetadata;
- betrouwbaarheid van `objectId` als relatieve sleutel.
