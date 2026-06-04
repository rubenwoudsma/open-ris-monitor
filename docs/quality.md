# Kwaliteitsrapportage

## Doel

Open RIS Monitor moet niet alleen data publiceren, maar ook laten zien hoe compleet en betrouwbaar die data is.

Kwaliteitsrapportage hoort daarom tot de kern van het project, niet tot een losse bijzaak.

## Huidige rapporten

De huidige kwaliteits- en analyse-uitvoer zit in `data/public/quality/`.

### Identiteit en stabiliteit

Bestand:

```text
data/public/quality/id_stability.json
```

Deze analyse kijkt onder andere naar:

- canonical document ids
- source ids
- source object ids
- composite source keys, `source_id + source_object_id`
- duplicate values
- missing values

De bedoeling is om te zien of een bron-id voldoende stabiel en traceerbaar is over meerdere harvests.

### Documenttypen

Bestand:

```text
data/public/quality/document_types.json
```

Deze analyse bewaart de originele RIS-documenttypewaarde en koppelt die aan een compacte analytische categorie.

Belangrijke principes:

- de bronwaarde blijft altijd zichtbaar,
- `unknown` gebruik je alleen als de bronwaarde ontbreekt of expliciet onbekend is,
- filters en dashboards mogen de compacte categorie gebruiken,
- de bronwaarde blijft nodig voor herleidbaarheid.

Voorbeeldcategorieën:

| Bronlabel | Compacte categorie |
|---|---|
| Raadsvoorstel | proposal |
| Collegevoorstel (Intern) | proposal |
| Bijlage | attachment |
| Document ter kennisname (Inkomend) | notice |
| Kennisgeving (Inkomend) | notice |
| Rapportage (Intern) | report |
| Toezeggingenlijst (Intern) | commitment |
| Uitnodigingen (Intern) | invitation |
| Verzoek om informatie (Inkomend) | request |
| Zienswijze (Inkomend) | objection_or_response |
| Onbekend | unknown |

## Verhouding tot het canonieke model

Het canonieke `Document`-model bewaart zowel de bronwaarde als de genormaliseerde documenttypevelden. De kwaliteitsrapportage helpt om te controleren of die mapping nog klopt en of nieuwe waarden niet stilletjes wegvallen naar `unknown`.

## Richting voor issue #13

De volgende stap is een expliciete kwaliteitsrapportage over volledigheid en relatie-dekking.

Waarschijnlijke checks:

- documenten zonder gepubliceerde relationele koppeling,
- relationele koppelingen naar ontbrekende documenten,
- vergaderingen zonder agendapunten,
- agendapunten zonder documenten,
- dubbele of verdachte relationele koppelingen,
- verschillen tussen raw relationele tellingen en gepubliceerde overlap,
- lege of ontbrekende public exports,
- plotselinge veranderingen in documenttypeverdeling,
- onverwachte groei van `unknown`.

## Praktisch gebruik

Kwaliteitsrapportage moet helpen om drie vragen snel te beantwoorden:

1. Is de harvest nog gezond?
2. Is de publicatie nog compleet?
3. Is de bronvariant nog goed genoeg begrepen om veilig te publiceren?

## Verder lezen

- `docs/data-model.md`
- `docs/harvesting.md`
- `docs/roadmap.md`
