# Documenttypen

De Open RIS Monitor bewaart altijd de oorspronkelijke documenttypewaarde uit het RIS. Deze waarde staat in `document_type` en blijft nodig voor herleidbaarheid naar de bron.

Vanaf issue #19 voegt de normalisatie daarnaast twee velden toe aan het canonieke `Document` model:

- `normalized_document_type`
- `normalized_document_type_label`

Deze velden maken de publieke dataset en viewer beter bruikbaar. De bronwaarden uit GemeenteOplossingen kunnen namelijk veel varianten bevatten, zoals `Raadsvoorstel`, `Raadsvoorstel (Intern)`, `Collegevoorstel (Intern)`, `Resumé ABM`, `Resumé Fysiek Domein`, `Kennisgeving (Inkomend)` en `Document ter kennisname (Inkomend)`.

## Ontwerpprincipe

```text
document_type = originele RIS-waarde
normalized_document_type = compacte analysecategorie
normalized_document_type_label = gebruikersvriendelijk Nederlands label
```

De bronwaarde wordt dus niet overschreven.

## Voorbeelden

| document_type | normalized_document_type | normalized_document_type_label |
|---|---|---|
| Raadsvoorstel | proposal | Voorstel |
| Collegevoorstel (Intern) | proposal | Voorstel |
| Bijlage | attachment | Bijlage |
| Raadsbesluit | decision | Besluit |
| Document ter kennisname (Inkomend) | notice | Kennisgeving of ter kennisname |
| Resumé ABM | minutes_or_summary | Notulen, verslag of resume |
| Toezeggingen | commitment | Toezegging |
| Onbekend | unknown | Onbekend |

## Gebruik in de viewer

De website filtert voortaan standaard op `normalized_document_type`. De oorspronkelijke bronwaarde blijft zichtbaar in een aparte kolom.

## Gebruik in kwaliteitsrapportage

De rapportage `data/public/quality/document_types.json` blijft bestaan. Deze rapportage kan worden gebruikt om te controleren of nieuwe bronwaarden goed worden ingedeeld en of `unknown` beperkt blijft tot ontbrekende of expliciet onbekende waarden.
