# Source analysis, GemeenteOplossingen RIS API

## Status

**Status:** concept voor issue #1, nog te valideren tegen de live API van Huizen.

Deze analyse beschrijft hoe de GemeenteOplossingen API voor het Raadsinformatiesysteem van de gemeente Huizen onderzocht moet worden en welke aannames voorlopig in de connector worden gebruikt.

De publieke basis-URL voor Huizen is:

```text
https://ris.gemeenteraadhuizen.nl/api/v2/
```

De API-root zelf kan een foutmelding of geen directory listing geven. Dat betekent niet automatisch dat de API niet bruikbaar is. Het kan zijn dat alleen concrete endpoints werken.

## Doel van deze analyse

Het doel van deze analyse is om vast te leggen:

1. welke endpoints beschikbaar zijn,
2. hoe responses zijn opgebouwd,
3. hoe vergaderingen, agendapunten en documenten aan elkaar gekoppeld zijn,
4. of paginering aanwezig is,
5. welke velden bruikbaar zijn voor het canonieke datamodel,
6. welke onzekerheden nog openstaan.

Deze analyse is de basis voor:

- issue #2, connector-contract,
- issue #3, eerste Huizen harvester,
- issue #4, canonieke modellen,
- issue #5, publieke JSONL-exports.

## Bron

| Onderdeel | Waarde |
|---|---|
| Gemeente | Huizen |
| RIS | Gemeenteraad Huizen |
| Leverancier | GemeenteOplossingen |
| API-versie | v2 |
| Basis-URL | `https://ris.gemeenteraadhuizen.nl/api/v2/` |
| Gemeenteconfig | `config/municipalities/huizen.yml` |

## Voorlopige endpoint-kandidaten

De endpointnamen hieronder zijn voorlopige kandidaten. Ze moeten worden gevalideerd in de browser, via GitHub Codespaces, of met een handmatige GitHub Action.

| Resource | Kandidaat-endpoint | Verwachte inhoud | Status |
|---|---|---|---|
| Vergaderingen | `/vergaderingen` | Lijst met vergaderingen | Te valideren |
| Agendapunten | `/agendapunten` | Lijst met agendapunten | Te valideren |
| Documenten | `/documenten` | Lijst met documentmetadata | Te valideren |

Mogelijke alternatieve namen die gecontroleerd moeten worden:

```text
/meetings
/vergadering
/agenda
/agendas
/agendapunten
/documenten
/documents
/bestanden
```

## Verwachte kernrelaties

Voor de MVP willen we minimaal deze relaties kunnen afleiden:

```text
Meeting
  contains AgendaItem

AgendaItem
  has Document

Document
  belongs to AgendaItem, optional
  belongs to Meeting, optional
```

De relatievelden kunnen per bron verschillen. Mogelijke veldnamen zijn:

```text
meeting_id
vergadering_id
vergaderingId
agenda_item_id
agendapunt_id
agendapuntId
document_id
documentId
id
```

De normalisatielaag moet daarom tolerant zijn voor verschillende veldnamen.

## Te verzamelen voorbeeldresponses

Vul dit onderdeel aan zodra de API lokaal of via Codespaces is geïnspecteerd.

### Vergaderingen

Endpoint:

```text
GET https://ris.gemeenteraadhuizen.nl/api/v2/...
```

Voorbeeldresponse:

```json
{
  "todo": "plak hier een kleine geanonimiseerde of publieke voorbeeldresponse"
}
```

Belangrijke velden:

| Canoniek veld | Bronveld | Status |
|---|---|---|
| `source_id` | `id` of alternatief | Te valideren |
| `title` | `title`, `titel`, `naam` | Te valideren |
| `start_datetime` | `datum`, `start`, `starttijd` | Te valideren |
| `location` | `locatie` | Te valideren |
| `web_url` | `url`, `link`, `webUrl` | Te valideren |

### Agendapunten

Endpoint:

```text
GET https://ris.gemeenteraadhuizen.nl/api/v2/...
```

Voorbeeldresponse:

```json
{
  "todo": "plak hier een kleine geanonimiseerde of publieke voorbeeldresponse"
}
```

Belangrijke velden:

| Canoniek veld | Bronveld | Status |
|---|---|---|
| `source_id` | `id` of alternatief | Te valideren |
| `meeting_source_id` | `vergadering_id` of alternatief | Te valideren |
| `number` | `nummer`, `volgnummer` | Te valideren |
| `title` | `title`, `titel`, `onderwerp` | Te valideren |
| `description` | `omschrijving`, `toelichting` | Te valideren |

### Documenten

Endpoint:

```text
GET https://ris.gemeenteraadhuizen.nl/api/v2/...
```

Voorbeeldresponse:

```json
{
  "todo": "plak hier een kleine geanonimiseerde of publieke voorbeeldresponse"
}
```

Belangrijke velden:

| Canoniek veld | Bronveld | Status |
|---|---|---|
| `source_id` | `id` of alternatief | Te valideren |
| `title` | `title`, `titel`, `naam` | Te valideren |
| `filename` | `filename`, `bestandsnaam` | Te valideren |
| `download_url` | `url`, `downloadUrl`, `bestandUrl` | Te valideren |
| `meeting_source_id` | `vergadering_id` of alternatief | Te valideren |
| `agenda_item_source_id` | `agendapunt_id` of alternatief | Te valideren |

## Responsevormen waarmee de connector rekening moet houden

De connector moet meerdere responsevormen aankunnen:

### Directe lijst

```json
[
  {"id": 1},
  {"id": 2}
]
```

### Object met data-lijst

```json
{
  "data": [
    {"id": 1},
    {"id": 2}
  ]
}
```

### Object met items-lijst

```json
{
  "items": [
    {"id": 1},
    {"id": 2}
  ]
}
```

### Object met results-lijst

```json
{
  "results": [
    {"id": 1},
    {"id": 2}
  ]
}
```

## Paginering

Nog te valideren.

Mogelijke vormen:

```text
?page=1
?page=1&pageSize=100
?skip=0&take=100
?offset=0&limit=100
```

De eerste connector hoeft nog geen perfecte paginering te ondersteunen. Voor de MVP is het acceptabel om eerst de eerste responsevorm te ondersteunen en paginering daarna expliciet te maken.

## Documentdownloadbeleid

Voor de MVP geldt:

```text
PDF's niet opslaan in Git.
PDF's eventueel later tijdelijk downloaden tijdens een workflow.
Voor issue #1 tot en met #5 nog geen PDF-verwerking verplicht maken.
```

Documentlinks worden wel opgeslagen als metadata, zodat latere verrijking mogelijk blijft.

## Open vragen

1. Wat zijn de exacte endpointnamen voor vergaderingen, agendapunten en documenten?
2. Is er paginering, en zo ja, hoe werkt die?
3. Zijn documentlinks directe downloadlinks of webpagina-links?
4. Zijn agendapunten direct gekoppeld aan vergaderingen?
5. Zijn documenten direct gekoppeld aan agendapunten, vergaderingen, of beide?
6. Zijn IDs stabiel over meerdere runs?
7. Worden gewijzigde documenten onder dezelfde ID gepubliceerd of als nieuw document?
8. Zijn historische vergaderingen volledig beschikbaar via de API?

## Aanbevolen acceptatiecriteria voor issue #1

Issue #1 kan worden gesloten wanneer:

- minimaal één werkend endpoint is vastgesteld,
- voorbeeldresponses zijn toegevoegd aan dit document,
- bekend is hoe vergaderingen, agendapunten en documenten worden gekoppeld,
- open vragen zijn bijgewerkt,
- duidelijk is welke aannames issue #2 en #3 mogen gebruiken.

## Vervolg

Na deze analyse:

1. connector-contract aanscherpen in `src/open_ris_monitor/connectors/base.py`,
2. GemeenteOplossingen connector defensief implementeren,
3. eerste raw harvest maken,
4. pas daarna canonieke normalisatie toevoegen.
