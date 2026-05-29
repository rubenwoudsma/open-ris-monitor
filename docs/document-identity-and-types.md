# Documentidentiteit en documenttypen

Deze notitie hoort bij issue #22. Het doel is om de betrouwbaarheid van documentidentiteit te onderzoeken en tegelijk inzicht te krijgen in de documenttypen die het RIS levert.

## Waarom dit belangrijk is

De Open RIS Monitor gebruikt documenten als eerste kernobject. Voor versiebeheer, checksums, kwaliteitsrapportage en latere koppelingen met vergaderingen en agendapunten moet duidelijk zijn welke identifier stabiel genoeg is.

De bron levert onder meer:

- `source_id`, afkomstig uit het RIS-veld `id`
- `source_object_id`, afkomstig uit het RIS-veld `objectId`
- `document_type`, afkomstig uit `documentTypeLabel`

## Analyse-output

De analyse publiceert twee rapporten:

```text
 data/public/quality/id_stability.json
 data/public/quality/document_types.json
```

Deze rapporten worden gemaakt op basis van `data/public/documents.jsonl`.

## Documentidentiteit

Het rapport `id_stability.json` bevat onder meer:

- totaal aantal documenten
- aantal unieke canonieke ids
- aantal unieke `source_id` waarden
- aantal unieke `source_object_id` waarden
- ontbrekende waarden
- dubbele waarden
- aanbevolen identiteitssleutel

Voorlopige voorkeursrichting:

```text
municipality_id + source_system_id + source_id + source_object_id
```

Deze keuze is voorzichtig, omdat nog onderzocht moet worden of `id` of `objectId` stabieler is over meerdere harvests.

## Documenttypen

Het rapport `document_types.json` bevat:

- alle bronwaarden uit `document_type`
- aantallen per bronwaarde
- voorgestelde compacte categorie per bronwaarde
- aantallen per compacte categorie

Voorbeeld:

```text
Raadsvoorstel -> proposal
Bijlage -> attachment
Agenda -> agenda
Mededelingen -> announcement
Ingekomen stuk -> incoming_document
Overig -> other
```

De originele bronwaarde blijft altijd behouden. Een latere milestone kan een extra veld toevoegen aan het canonieke Document-model:

```text
source_document_type
normalized_document_type
```

## Bewuste beperking

Deze analyse kijkt naar de actuele public export. Echte stabiliteit over tijd kan pas worden vastgesteld door meerdere harvests naast elkaar te vergelijken.
