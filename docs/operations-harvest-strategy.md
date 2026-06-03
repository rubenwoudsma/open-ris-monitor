# Operationele harveststrategie

Open RIS Monitor publiceert compacte JSONL-bestanden voor hergebruik en voor de statische GitHub Pages viewer. De operationele harvest moet daarom begrensd blijven: geen PDF's in Git, geen grote raw dumps in Git en alleen `data/public/` als commitbare output.

## Profielen

De CLI ondersteunt drie harvestprofielen via `--profile`.

| Profiel | Gebruik | Documentlimiet | Relationele limieten |
| --- | --- | ---: | --- |
| `quick` | Snelle controle van de pipeline en relationele exports | 10 latest documenten | 50 meetingsessies, batch 50, 200 agendapunten |
| `public` | Standaard handmatige publicatie naar `data/public/` | 250 documenten | 250 meetingsessies, batch 100, 1000 agendapunten |
| `backfill` | Grotere gecontroleerde aanvulling van historische dekking | standaard geen documentcap, met CLI override configureerbaar | 1000 meetingsessies, batch 100, 5000 agendapunten |

Alle profielen zetten relationele harvesting aan. Daardoor worden naast `documents.jsonl` en `harvest_runs.jsonl` ook de relationele public exports geschreven:

```text
data/public/meetings.jsonl
data/public/meeting_items.jsonl
data/public/meeting_documents.jsonl
data/public/meeting_item_documents.jsonl
```

`latest.json` blijft het publicatiecontract. Het bestand bevat de `outputs`, `relations_enabled` en `relations_summary` van de laatste run.

## CLI-gebruik

Snelle smoke test:

```bash
python -m open_ris_monitor.pipeline.run --municipality huizen --profile quick
```

Standaard publieke publicatie:

```bash
python -m open_ris_monitor.pipeline.run --municipality huizen --profile public
```

Grotere backfill, maar alsnog begrensd via expliciete override:

```bash
python -m open_ris_monitor.pipeline.run \
  --municipality huizen \
  --profile backfill \
  --max-documents 1000 \
  --meeting-scan-limit 1000 \
  --meeting-item-limit 5000
```

Expliciete CLI-parameters winnen altijd van profielwaarden. Bijvoorbeeld:

```bash
python -m open_ris_monitor.pipeline.run \
  --municipality huizen \
  --profile public \
  --max-documents 100 \
  --meeting-scan-limit 100
```

Gebruik `--no-include-relations` alleen voor diagnose. De publicatieworkflow verwacht relationele exports.

## GitHub Actions

De handmatige workflow `.github/workflows/publish-public-data.yml` gebruikt standaard:

```text
municipality: huizen
profile: public
```

De workflow doet vier dingen:

1. draait de bounded harvest met het gekozen profiel;
2. schrijft raw output naar `data/raw/latest/`;
3. uploadt raw output alleen als GitHub Actions artifact;
4. commit uitsluitend `data/public/` terug naar de branch.

De workflow commit geen `data/raw/` en geen PDF's. Voor forks kan dezelfde workflow worden gebruikt met een andere gemeenteconfiguratie, zolang de connectorconfiguratie en RIS-endpoints beschikbaar zijn.

## Wanneer welk profiel gebruiken

Gebruik `quick` voor een smoke test na codewijzigingen of als de RIS-koppeling gecontroleerd moet worden zonder veel data op te halen.

Gebruik `public` voor de normale handmatige publicatie van de live dataset. Dit is de standaard voor de workflow en de aanbevolen keuze voor de eerste operationele runs.

Gebruik `backfill` alleen bewust. Start liever met een expliciete `--max-documents` override en verhoog daarna stap voor stap. Daarmee blijft de GitHub Actions-runtime voorspelbaar en blijft `data/public/` compact.
