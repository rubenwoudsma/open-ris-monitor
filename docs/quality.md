# Kwaliteitsrapportage

Open RIS Monitor publiceert een compacte kwaliteitslaag naast de publieke dataset. Het doel is om snel te zien of de actuele export bruikbaar, consistent en voldoende volledig is voor hergebruik.

## Doel van de rapportage

De kwaliteitsrapportage controleert vooral de publieke dataset, niet de code zelf. De focus ligt op:

- volledigheid van de export
- relatiedekking tussen documenten, vergaderingen en agendapunten
- verwijzingsintegriteit
- documenttypenormalisatie
- signalen over recente harvests

## Public output

De rapportage schrijft resultaten weg naar:

```text
data/public/quality/id_stability.json
data/public/quality/document_types.json
data/public/quality/summary.json
data/public/quality/issues.jsonl
```

De summary is bedoeld voor snelle weergave in viewer of README. De issues-file bevat losse bevindingen per regel zodat die later eenvoudig te filteren of te tonen is.

## Handmatig gebruik

De bestaande analyseworkflow blijft het entrypoint:

```bash
python -m open_ris_monitor.analysis.generate_public_reports --public-dir data/public
```

De nieuwe quality package wordt daaronder aangeroepen en schrijft de bredere rapportage weg.

## Wat wordt gecontroleerd

### Datasetstatistieken

Minimaal worden geteld:

- documenten
- documentversies
- harvest runs
- vergaderingen
- agendapunten
- document-vergaderrelaties
- document-agendapuntrelaties

### Relatiedekking

De rapportage berekent hoeveel documenten aan ten minste één relatie gekoppeld zijn.

### Verwijzingsintegriteit

De rapportage controleert of relaties verwijzen naar bestaande documenten, vergaderingen en agendapunten.

### Vergader- en agendapuntkwaliteit

De rapportage signaleert:

- vergaderingen zonder agendapunten
- agendapunten zonder documenten

### Documenttypekwaliteit

De rapportage telt documenttypen en signaleert wanneer `unknown` voorkomt.

### Harvestkwaliteit

De rapportage vermeldt de laatste harveststatus en de belangrijkste tellingen uit `harvest_runs.jsonl`.

## Interpretatie

Een rapport is niet automatisch foutloos omdat er waarschuwingen zijn. Sommige bevindingen zijn informatief, bijvoorbeeld documenten zonder relatie. Een storing is vooral relevant wanneer:

- het aantal documenten onverwacht sterk daalt
- relaties verwijzen naar ontbrekende records
- `unknown` documenttypen oplopen
- de laatste harvest geen successtatus heeft
