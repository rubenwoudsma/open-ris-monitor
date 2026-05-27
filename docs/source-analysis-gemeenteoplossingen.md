# Source analysis, GemeenteOplossingen API, gemeente Huizen

Status: concept voor issue #1  
Branch: `milestone-1-huizen-harvest`  
Bron: https://ris.gemeenteraadhuizen.nl/api/v2/

## 1. Doel

Dit document beschrijft de eerste werkende analyse van de GemeenteOplossingen API voor het raadsinformatiesysteem van de gemeente Huizen. Het doel is om vast te leggen welke API-onderdelen aantoonbaar werken, welke responsevorm gebruikt wordt en hoe deze brondata later kan worden gemapt naar het canonieke model van Open RIS Monitor.

Deze analyse vervangt de eerdere, te voorzichtige aanname dat de API-root zelf leidend moest zijn. De bestaande Huizen RIS Monitor bewijst dat ten minste het endpoint `documents` werkt met `limit` en `offset` parameters.

## 2. Basisgegevens

| Onderdeel | Waarde |
|---|---|
| Leverancier | GemeenteOplossingen |
| Gemeente | Huizen |
| RIS website | https://ris.gemeenteraadhuizen.nl/ |
| API base URL | https://ris.gemeenteraadhuizen.nl/api/v2/ |
| Bewezen endpoint | `documents` |
| Bewezen downloadpatroon | `documents/{id}/download` |
| Bewezen paginering | `limit` en `offset` |
| Bewezen responsepad | `result.documents` |
| Bewezen totaalveld | `result.totalCount` |

## 3. Bewezen werking vanuit bestaande Streamlit-app

De bestaande Huizen RIS Monitor gebruikt de volgende API-aanpak:

```python
API_BASE = "https://ris.gemeenteraadhuizen.nl/api/v2/"

r = requests.get(f"{API_BASE}documents?limit=1")
total = int(r.json()["result"]["totalCount"])

offset = max(0, total - fetch_limit)
r = requests.get(f"{API_BASE}documents?limit={fetch_limit}&offset={offset}")
documents = r.json()["result"]["documents"]
```

Voor documentdownloads gebruikt de bestaande app:

```python
download_url = f"https://ris.gemeenteraadhuizen.nl/api/v2/documents/{doc_id}/download"
```

Daarmee zijn voor milestone 1 minimaal de volgende zaken zeker genoeg om op te bouwen:

1. documenten kunnen via de API worden opgehaald;
2. het aantal documenten kan via `result.totalCount` worden bepaald;
3. paginering werkt via `limit` en `offset`;
4. documenten staan in `result.documents`;
5. een document bevat een `id` waarmee een download-URL kan worden opgebouwd.

## 4. Bewezen velden in documentobjecten

De bestaande Streamlit-app gebruikt de volgende documentvelden:

| Bronveld | Betekenis in bestaande app | Opmerking |
|---|---|---|
| `id` | document-ID | Wordt gebruikt voor download-URL |
| `publicationDate.date` | publicatiedatum | Datumstring bevat tijd en fracties |
| `description` | titel of omschrijving | Voorkeursveld voor titel |
| `fileName` | bestandsnaam | Fallback voor titel |
| `documentTypeLabel` | documenttype | Bijvoorbeeld besluit, bijlage, motie, enzovoort |

Voor de eerste MVP moeten we niet meer velden verplicht maken dan deze. Extra velden kunnen worden bewaard in `source_data` of `raw`.

## 5. Voorlopige endpointanalyse

### 5.1 Documents

Endpoint:

```text
GET https://ris.gemeenteraadhuizen.nl/api/v2/documents?limit={limit}&offset={offset}
```

Verwachte responsevorm:

```json
{
  "result": {
    "totalCount": 1234,
    "documents": [
      {
        "id": 123,
        "description": "...",
        "fileName": "...",
        "documentTypeLabel": "...",
        "publicationDate": {
          "date": "2026-05-21 20:00:00.000000"
        }
      }
    ]
  }
}
```

Downloadpatroon:

```text
GET https://ris.gemeenteraadhuizen.nl/api/v2/documents/{id}/download
```

MVP-status:

```text
Bewezen bruikbaar.
```

### 5.2 Meetings

Mogelijk endpoint, nog te valideren:

```text
GET https://ris.gemeenteraadhuizen.nl/api/v2/meetings?limit={limit}&offset={offset}
```

MVP-status:

```text
Nog niet bewezen vanuit bestaande Streamlit-app.
```

### 5.3 Agenda items

Mogelijke endpointvormen, nog te valideren:

```text
GET https://ris.gemeenteraadhuizen.nl/api/v2/agenda-items?limit={limit}&offset={offset}
GET https://ris.gemeenteraadhuizen.nl/api/v2/agendaitems?limit={limit}&offset={offset}
GET https://ris.gemeenteraadhuizen.nl/api/v2/meetings/{meeting_id}/agenda-items
```

MVP-status:

```text
Nog niet bewezen vanuit bestaande Streamlit-app.
```

## 6. Implicatie voor milestone 1

Milestone 1 moet worden versimpeld naar een document-first MVP:

```text
Eerst documents ophalen en publiceren.
Daarna pas meetings en agenda items toevoegen zodra de endpoints bewezen zijn.
```

Dat betekent dat issue #3, Bouw eerste Huizen harvester, in eerste instantie alleen hoeft te bewijzen dat `documents` werkt.

Voorgestelde volgorde:

1. `documents?limit=1` ophalen;
2. `result.totalCount` lezen;
3. laatste batch documenten ophalen met `limit` en `offset`;
4. raw response opslaan als `data/raw/latest/documents.json`;
5. documentrecords normaliseren naar `data/public/documents.jsonl`.

## 7. Mapping naar canoniek Document-model

| Canoniek veld | Bronveld | Regel |
|---|---|---|
| `id` | `id` | Bijvoorbeeld `huizen-document-{id}` |
| `source_id` | `id` | Bron-ID ongewijzigd bewaren |
| `municipality_id` | config | Voor Huizen: `gm0406` |
| `source_system_id` | config | Bijvoorbeeld `huizen-gemeenteoplossingen` |
| `title` | `description`, fallback `fileName` | Als titel generiek is, combineren met documenttype |
| `document_type` | `documentTypeLabel` | Fallback `onbekend` |
| `filename` | `fileName` | Fallback leeg of null |
| `date_published` | `publicationDate.date` | Converteren naar ISO datum waar mogelijk |
| `download_url` | `id` | `{base_url}documents/{id}/download` |
| `source_url` | onbekend | Later aanvullen indien beschikbaar |
| `raw` | volledig object | Voorlopig bewaren voor traceerbaarheid |

## 8. Normalisatieregels voor titels

De bestaande Streamlit-app bevat al een nuttige curator-regel:

```python
title = document.get("description") or document.get("fileName") or "Geen titel"
document_type = document.get("documentTypeLabel", "Onbekend")

if title.lower() in ["besluit", "besluit.pdf", "bijlage", "bijlage.pdf"]:
    title = f"{document_type}: {title}"
```

Deze regel kan worden overgenomen in de normalisatielaag, maar moet daar als afgeleide titel worden behandeld. De originele bronvelden blijven beschikbaar in `raw`.

## 9. Open vragen

Voor issue #1 blijven deze vragen open:

1. Bestaan `meetings` en `agenda_items` als API-endpoints, en welke namen gebruiken ze exact?
2. Kan een document gekoppeld worden aan een vergadering of agendapunt via velden in het documentobject?
3. Bevat het documentobject een publieke webpagina-URL naast de download-URL?
4. Welke documenttypes komen voor in `documentTypeLabel`?
5. Is er sortering mogelijk via queryparameters, of is offset op basis van `totalCount` voldoende?
6. Is er filtering op publicatiedatum mogelijk?
7. Is de API stabiel zonder aanvullende headers?

## 10. Advies voor issue #1

Issue #1 kan nog niet volledig gesloten worden, maar kan wel worden aangescherpt:

```text
Scope issue #1:
Bevestig en documenteer minimaal het documents-endpoint volledig.
Meetings en agenda items mogen als vervolgonderzoek blijven staan.
```

Acceptatiecriteria voor afronding issue #1:

- `documents?limit=1` is getest;
- `totalCount` is vastgelegd;
- minimaal één voorbeeldobject is opgenomen in dit document;
- de gebruikte velden zijn beschreven;
- open vragen voor meetings en agenda items zijn benoemd.

## 11. Advies voor issue #2

Het connector-contract moet document-first zijn, met optionele methodes voor meetings en agenda items.

Minimaal verplicht voor milestone 1:

```python
fetch_documents(limit: int, offset: int = 0) -> list[dict]
fetch_document_count() -> int
build_document_download_url(document_id: str | int) -> str
```

Optioneel voor latere milestones:

```python
fetch_meetings(limit: int, offset: int = 0) -> list[dict]
fetch_agenda_items(limit: int, offset: int = 0) -> list[dict]
download_document(document_id: str | int) -> bytes
```
