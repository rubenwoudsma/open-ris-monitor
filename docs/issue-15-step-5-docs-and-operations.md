# Issue #15, stap 5, docs en operationele basis

## Doel

Deze stap werkt de documentatie bij na de succesvolle implementatie van relationele harvesting, normalisatie en public exports.

De repo verschuift hiermee van document-first MVP naar een relationele open-data-basis.

## Aangepaste bestanden

```text
README.md
docs/architecture.md
docs/data-model.md
docs/roadmap.md
docs/meetings-agenda-items-discovery.md
docs/operations-harvest-strategy.md
```

## Belangrijkste wijzigingen

- README beschrijft nu de relationele MVP.
- Architecture documenteert de optionele relationele pipeline.
- Data model bevat `Meeting`, `MeetingItem`, `MeetingDocumentRelation` en `MeetingItemDocumentRelation` als geimplementeerd.
- Roadmap plaatst #14 en de eerste #15-stappen bij completed.
- Discovery documenteert dat het onderzoek is afgerond en geimplementeerd.
- Operations document beschrijft hoe full harvesting beheersbaar blijft binnen GitHub.

## Geen codewijziging

Deze stap bevat bewust geen pipelinecode, normalizers, models of viewerwijzigingen.

## Acceptatiecriteria

- De docs noemen de nieuwe public relation exports.
- De docs leggen uit dat `MeetingItem` functioneel het agendapunt is.
- De docs benoemen `latest.json` met `outputs`, `relations_enabled` en `relations_summary`.
- De docs houden PDF's en raw data buiten Git.
- De docs beschrijven een bounded harveststrategie.
- De roadmap is niet meer in tegenspraak met de uitgevoerde discovery.

## Commitvoorstel

```bash
git add README.md \
  docs/architecture.md \
  docs/data-model.md \
  docs/roadmap.md \
  docs/meetings-agenda-items-discovery.md \
  docs/operations-harvest-strategy.md \
  docs/issue-15-step-5-docs-and-operations.md

git commit -m "Update docs for meeting relation exports"
```
