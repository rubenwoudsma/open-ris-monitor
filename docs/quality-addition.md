## Identiteitscontrole

Open RIS Monitor publiceert een identiteitsanalyse via:

```text
data/public/quality/id_stability.json
```

De analyse controleert:

- ontbrekende identifiers
- dubbele identifiers
- source_id gebruik
- source_object_id gebruik
- samengestelde sleutels

Doel is vroegtijdig signaleren wanneer een bronleverancier identifiergedrag wijzigt.

Werkelijke stabiliteit kan alleen worden vastgesteld door meerdere harvests over tijd te vergelijken.

## Documenttypekwaliteit

Open RIS Monitor publiceert een documenttyperapport via:

```text
data/public/quality/document_types.json
```

Dit rapport helpt controleren:

- welke bronwaarden voorkomen
- hoe deze worden gemapt
- hoeveel documenten in iedere categorie vallen
- hoeveel documenten als `unknown` worden geclassificeerd

Het doel is een stabiele set documentcategorieën te behouden zonder de oorspronkelijke RIS-waarde te verliezen.

## Mappingbeleid

De documenttypemapping moet:

- bruikbaar zijn voor gebruikers
- bruikbaar zijn voor analyses
- leveranciersneutraal blijven
- herleidbaar blijven naar de bron

Voorbeelden:

| Bronwaarde | Genormaliseerd |
|---|---|
| Raadsvoorstel | proposal |
| Collegevoorstel (Intern) | proposal |
| Bijlage | attachment |
| Rapportage (Intern) | report |
| Toezeggingenlijst | commitment |
| Uitnodigingen | invitation |
| Verzoek om informatie | request |
| Onbekend | unknown |

`unknown` wordt uitsluitend gebruikt wanneer een bronwaarde ontbreekt of expliciet onbekend is.
