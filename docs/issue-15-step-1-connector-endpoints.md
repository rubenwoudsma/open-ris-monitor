# Issue #15, stap 1, connector endpoints

Dit pakket bevat de eerste gecontroleerde stap voor issue #15: het uitbreiden van de GemeenteOplossingen connector met meeting- en documentrelatie-endpoints.

## Inhoud

Gewijzigd bestand:

- `src/open_ris_monitor/connectors/gemeenteoplossingen.py`

Nieuw testbestand:

- `tests/test_gemeenteoplossingen_meeting_endpoints.py`

## Nieuwe connector-methodes

- `fetch_meeting_sessions_page(limit, offset)` voor `/meetingsessions`
- `fetch_meeting(meeting_id)` voor `/meetings/{meetingId}`
- `fetch_meeting_items(meeting_id)` voor `/meetings/{meetingId}/meetingitems`
- `fetch_meeting_documents(meeting_id)` voor `/meetings/{meetingId}/documents`
- `fetch_meeting_item_documents(meeting_item_id)` voor `/meetingitems/{meetingItemId}/documents`

## Bewuste ontwerpkeuzes

- `fetch_meeting()` retourneert `None` bij een 404.
- Andere endpoints blijven fouten doorgeven, zodat echte API-problemen zichtbaar blijven.
- Deze stap voegt nog geen relationele harvest, normalisatie of exports toe.
- De bestaande document-methodes blijven ongewijzigd beschikbaar.

## Lokale validatie

Voer na uploaden naar de branch uit:

```bash
python -m pytest tests/test_gemeenteoplossingen_connector.py \
  tests/test_gemeenteoplossingen_pagination.py \
  tests/test_connector.py \
  tests/test_gemeenteoplossingen_meeting_endpoints.py
```

Daarna eventueel de volledige testset:

```bash
python -m pytest
```

## Commitvoorstel

```text
Add GemeenteOplossingen meeting relation endpoints
```
