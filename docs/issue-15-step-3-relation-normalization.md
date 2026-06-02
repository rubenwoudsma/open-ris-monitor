# Issue #15, stap 3, relation normalization

Deze stap voegt de canonieke modellen en normalisatie toe voor de relationele data die in stap 2 raw is opgehaald.

## Nieuwe modellen

Bestand:

- `src/open_ris_monitor/models/relations.py`

Modellen:

- `Meeting`
- `MeetingItem`
- `MeetingDocumentRelation`
- `MeetingItemDocumentRelation`

## Nieuwe normalizers

Bestand:

- `src/open_ris_monitor/normalizers/relations.py`

Belangrijkste functies:

- `normalize_meetings(...)`
- `normalize_meeting_items(...)`
- `normalize_meeting_document_relations(...)`
- `normalize_meeting_item_document_relations(...)`
- `normalize_relation_harvest(...)`

## ID-beleid

De normalisatie gebruikt stabiele, forkbare identifiers:

```text
huizen-meeting-19
huizen-meeting-item-142
huizen-meeting-19-document-3127
huizen-meeting-item-142-document-158
```

De bron-ID blijft altijd beschikbaar als `source_id`, `meeting_source_id`, `meeting_item_source_id` of `document_source_id`.

## Bewuste ontwerpkeuzes

- `MeetingItem` is de technische naam, omdat GemeenteOplossingen deze term gebruikt.
- Functioneel is `MeetingItem` het agenda-item.
- Records zonder noodzakelijke bron-ID worden overgeslagen.
- HTML in omschrijvingen en titels wordt gestript.
- Duplicaten worden stabiel verwijderd op canonieke ID.
- Deze stap schrijft nog geen public JSONL exports. Dat volgt in stap 4.

## Tests

Nieuw testbestand:

- `tests/test_relation_normalization.py`

De tests controleren:

- meeting-normalisatie
- meeting-item-normalisatie
- meeting-documentrelaties
- meeting-item-documentrelaties
- deduplicatie
- normalisatie van de volledige raw relation harvest bucket
