# Issue #37: public harvest moet recente documenten prefereren

## Context

Het `public` profiel is bedoeld voor de publieke GitHub Pages dataset. Die dataset moet compact blijven, maar voor demo, test en MVP-gebruik is het belangrijker dat de site recente documenten toont dan dat de eerste historische documenten uit het bronsysteem worden gepubliceerd.

De eerdere public run haalde een bounded set documenten op via `full` mode met `max_documents: 250`. Als de bron standaard historisch of oplopend teruggeeft, publiceert dit vooral oude documenten.

## Keuze

Het `public` profiel gebruikt voortaan `latest` mode met `limit: 250`.

Daarmee blijft de public harvest:

- bounded
- GitHub Actions-vriendelijk
- compact genoeg voor `data/public`
- geschikt voor een statische GitHub Pages site
- relationeel verrijkt via `include_relations: true`

## Profielgedrag

| Profiel | Doel | Documentselectie |
| --- | --- | --- |
| `quick` | Smoke test | Laatste 10 documenten |
| `public` | Publieke site | Laatste 250 documenten |
| `backfill` | Historische of grotere run | Full mode, configureerbaar |

## Out of scope

Deze wijziging doet bewust geen volledige backfill en voegt geen scheduled harvest toe. Die blijven aparte operationele stappen.

Ook viewerwijzigingen horen niet bij dit issue. De viewer sorteert binnen de gepubliceerde dataset, maar de harvest bepaalt welke documenten in die dataset terechtkomen.

## Testen

Run lokaal of via GitHub Actions:

```bash
pytest
```

Draai daarna handmatig de workflow `Publish public RIS data` met:

```text
municipality: huizen
profile: public
```

Controleer daarna:

- `data/public/documents.jsonl` bevat een bounded set documenten
- `data/public/latest.json` heeft `mode: latest`
- relationele exports worden nog steeds gegenereerd
- de live site toont recentere documenten dan de eerdere 2018-only public run
