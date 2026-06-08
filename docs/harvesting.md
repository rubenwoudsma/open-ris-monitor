# Harvesting en bronanalyse

## Doel

Dit document beschrijft hoe Open RIS Monitor openbare raadsinformatie ophaalt, normaliseert en publiceert voor de Huizen-implementatie.

Het document heeft drie doelen:

1. vastleggen welke GemeenteOplossingen API-routes bewezen werken;
2. uitleggen hoe documenten, vergaderingen en agendapunten relationeel worden gekoppeld;
3. vastleggen welke operationele harvestprofielen, cadence, limieten, stopcriteria en succescriteria gelden.

Open RIS Monitor blijft hierbij bewust lichtgewicht:

- static site only;
- geen backend;
- geen database;
- geen PDF-opslag in Git;
- compacte publicatie via JSONL;
- herhaalbare GitHub Actions workflows.

## Bronbasis

De Huizen-implementatie gebruikt de GemeenteOplossingen API.

Base URL:

```text
https://ris.gemeenteraadhuizen.nl/api/v2/
```

Bewezen documentendpoint:

```text
GET /documents?limit={limit}&offset={offset}
```

Bewezen responsepad:

```text
result.documents
```

Telling:

```text
GET /documents?limit=1
result.totalCount
```

Downloadpatroon:

```text
GET /documents/{id}/download
```

PDF-bestanden worden niet opgeslagen in Git. Downloads mogen alleen tijdelijk worden gebruikt voor afgeleide metadata, bijvoorbeeld checksumverrijking, waarna alleen compacte metadata wordt gepubliceerd.

## Bewezen top-level routes

De volgende routes zijn bewezen bruikbaar voor Huizen:

```text
/documents
/meetings
/dmus
/events
/meetingsessions
```

## Bewezen nested meeting routes

De volgende nested routes zijn bewezen bruikbaar voor relationele context:

```text
/meetings/{meetingId}
/meetings/{meetingId}/documents
/meetings/{meetingId}/meetingitems
/meetingitems/{meetingItemId}
/meetingitems/{meetingItemId}/documents
```

## Relationele keten

De relationele discovery heeft bevestigd dat documenten gekoppeld kunnen worden aan vergaderingen en agendapunten.

Werkende keten:

```text
/meetingsessions
  -> container.meeting.id
  -> /meetings/{meetingId}
  -> /meetings/{meetingId}/meetingitems
  -> /meetings/{meetingId}/documents
  -> /meetingitems/{meetingItemId}/documents
```

Belangrijke observaties:

- `/meetingsessions` is nodig voor historische dekking.
- `/meetings` is vooral nuttig voor recente of toekomstige vergaderingen.
- Niet elke meeting ID uit `/meetingsessions` resolveert via `/meetings/{meetingId}`.
- Een 404 op meeting detail is bronvariatie en mag de harvest niet laten falen.
- Meeting items bevatten voldoende velden voor een canoniek agendapunt.
- Documenten zijn zowel op vergaderniveau als op agendapuntniveau vindbaar.

## Huizen-bronvelden

De eerste documentharvest bevestigde onder andere deze velden:

| Bronveld | Betekenis | Canoniek veld |
|---|---|---|
| `id` | Document-ID in bron | `source_id` |
| `objectId` | Object-ID in bron | `source_object_id` |
| `description` | Omschrijving of titel | `title`, `description` |
| `documentTypeLabel` | Type document | `document_type` |
| `fileName` | Bestandsnaam | `filename` |
| `fileSize` | Bestandsgrootte in bytes | `file_size_bytes` |
| `publicationDate.date` | Publicatiedatum | `publication_datetime` |
| `publicationDate.timezone` | Tijdzone | `publication_timezone` |
| `confidential` | Vertrouwelijkheidsindicator | `is_confidential` |
| `isTabsignDocument` | Tabsign-indicator | `is_tabsign_document` |

## Harvestprofielen

De CLI ondersteunt drie operationele profielen via `--profile`.

| Profiel | Doel | Gebruik | Publicatiegedrag |
|---|---|---|---|
| `quick` | Snelle controle | Lokale smoke test, diagnose, beperkte CI-check | Niet bedoeld als normale publicatiebron |
| `public` | Dagelijkse publicatie | Standaard scheduled harvest voor GitHub Pages | Publiceert `data/public/` |
| `backfill` | Historische aanvulling of herstel | Handmatig via `workflow_dispatch` of lokaal | Alleen bewust uitvoeren, bij voorkeur met expliciete limieten |

Alle profielen zetten standaard relationele harvesting aan. Daardoor worden naast documentexports ook relationele exports geschreven.

Belangrijkste public outputs:

```text
data/public/documents.jsonl
data/public/document_versions.jsonl
data/public/harvest_runs.jsonl
data/public/meetings.jsonl
data/public/meeting_items.jsonl
data/public/meeting_documents.jsonl
data/public/meeting_item_documents.jsonl
data/public/latest.json
```

Kwaliteitsrapporten worden gepubliceerd onder:

```text
data/public/quality/
```

`latest.json` blijft het operationele publicatiecontract voor de laatste run. Dit bestand bevat onder andere de outputs, relationele status en samenvatting van de laatste publicatie.

## Profielbeleid

### `quick`

Gebruik `quick` voor:

- snelle lokale controle na codewijzigingen;
- diagnose van de RIS-koppeling;
- controle of de pipeline start, normaliseert en public exports kan schrijven;
- beperkte test runs zonder zware API-belasting.

`quick` is niet bedoeld als bron voor de live dataset.

### `public`

Gebruik `public` voor:

- de dagelijkse scheduled harvest;
- reguliere publicatie naar `data/public/`;
- bijwerken van de GitHub Pages dataset.

Dit is het standaardprofiel voor operationeel gebruik.

### `backfill`

Gebruik `backfill` voor:

- gecontroleerde historische aanvulling;
- herstel na gemiste runs;
- initiële vulling of herbouw van bredere historische dekking.

`backfill` draait niet automatisch scheduled. Start dit profiel alleen handmatig. Gebruik waar mogelijk expliciete limieten, zodat runtime, API-belasting en GitHub Actions-verbruik voorspelbaar blijven.

## Cadence policy

De standaard operationele cadence is:

```text
Dagelijks, profile=public
```

De scheduled workflow draait bewust niet exact op het hele uur. Dit verlaagt de kans dat meerdere forks tegelijk dezelfde upstream API belasten.

Aanbevolen scheduled cadence:

```text
23 3 * * *
```

Betekenis:

- eenmaal per dag;
- rond 03:23 UTC;
- standaard gemeente: `huizen`;
- standaard profiel: `public`;
- public output wordt bij scheduled runs terug gecommit naar de branch.

Hourly harvesting is bewust niet gekozen. Gemeentelijke raadsinformatie wijzigt doorgaans niet op uurbasis, terwijl hourly runs meer GitHub Actions-minuten gebruiken en meer druk op de GemeenteOplossingen API leggen.

Weekly harvesting is ook niet ideaal als standaard, omdat agenda's en documenten in de dagen voor een vergadering nog kunnen wijzigen.

De gekozen baseline is daarom:

```text
daily public harvest, manual backfill when needed
```

## GitHub Actions workflow

De operationele harvest workflow staat in:

```text
.github/workflows/harvest.yml
```

De workflow ondersteunt twee startmodi:

1. scheduled run;
2. handmatige run via `workflow_dispatch`.

### Scheduled run

Een scheduled run gebruikt standaard:

```text
municipality: huizen
profile: public
commit_public: true
```

De scheduled run is bedoeld als normale publicatie-run voor de live dataset.

### Manual dispatch

Een handmatige run ondersteunt deze inputs:

| Input | Doel | Standaard |
|---|---|---|
| `municipality` | Gemeenteconfiguratie | `huizen` |
| `profile` | Harvestprofiel | `public` |
| `enrich_checksums` | Tijdelijk PDF's downloaden voor checksumverrijking | `false` |
| `checksum_max_documents` | Maximum aantal documenten voor checksumverrijking | `50` |
| `commit_public` | Public output terug committen | `false` |

Handmatige runs committen `data/public/` alleen als `commit_public=true`.

### Concurrency

De workflow gebruikt concurrency, zodat twee harvests op dezelfde branch elkaar niet tegelijk kunnen overschrijven.

Policy:

```text
concurrency group: harvest-${{ github.ref }}
cancel-in-progress: false
```

Dit betekent dat een tweede run wacht of niet parallel publiceert, in plaats van een lopende harvest halverwege af te breken.

## Retry en back-off policy

De GemeenteOplossingen connector moet robuust omgaan met tijdelijke upstreamproblemen.

De connector mag retries uitvoeren bij tijdelijke fouten zoals:

```text
408 Request Timeout
429 Too Many Requests
500 Internal Server Error
502 Bad Gateway
503 Service Unavailable
504 Gateway Timeout
connect timeout
read timeout
tijdelijke netwerkfouten
```

De retrystrategie gebruikt beperkte retries met exponential back-off. Als de upstream een `Retry-After` header meegeeft, moet die worden gerespecteerd.

Niet alle fouten zijn retrybaar. Client errors zoals onderstaande worden niet blind opnieuw geprobeerd:

```text
400 Bad Request
401 Unauthorized
403 Forbidden
404 Not Found
```

Uitzondering: een 404 op een meeting detailroute kan bronvariatie zijn. Die specifieke situatie mag relationele harvesting niet volledig laten falen, zolang de rest van de brondata bruikbaar blijft.

## Stopcriteria

Een harvest stopt wanneer één van de volgende situaties optreedt:

1. het profielvenster of de profiellimieten zijn volledig verwerkt;
2. de expliciete CLI-limieten zijn bereikt;
3. de upstream API geeft geen extra records meer terug;
4. een niet-herstelbare fout treedt op;
5. exportvalidatie of integriteitscontrole faalt.

Expliciete CLI-parameters winnen altijd van profielwaarden. Dit maakt gecontroleerde runs mogelijk zonder nieuwe profielen toe te voegen.

Voorbeeld:

```bash
python -m open_ris_monitor.pipeline.run \
  --municipality huizen \
  --profile public \
  --max-documents 100 \
  --meeting-scan-limit 100
```

## Failure policy

De pipeline moet fail closed werken.

Dat betekent:

- een upstream outage mag niet leiden tot een succesvolle lege publicatie;
- een lege of ongeldig gegenereerde dataset telt niet als succes;
- ongeldige JSONL of schema-incompatibele output mag niet worden gepubliceerd;
- bij failure blijft de vorige succesvolle publicatie leidend;
- de GitHub Action moet zichtbaar falen, zodat onderhouders kunnen ingrijpen.

De pipeline mag dus niet stilletjes slagen wanneer de bron tijdelijk onbereikbaar is of nul bruikbare records oplevert terwijl records verwacht worden.

## Succescriteria

Een harvest telt als succesvol wanneer aan alle onderstaande voorwaarden is voldaan:

1. de run eindigt zonder niet-herstelbare connectorfouten;
2. public JSONL-bestanden zijn gegenereerd;
3. `data/public/latest.json` bestaat en verwijst naar de gegenereerde outputs;
4. relationele exports zijn aanwezig, tenzij bewust met een diagnoseflag uitgeschakeld;
5. kwaliteitsrapporten onder `data/public/quality/` zijn gegenereerd;
6. exportvalidatie slaagt;
7. de output bevat geen PDF-bestanden;
8. scheduled runs committen uitsluitend toegestane public output terug naar Git.

Minimale verwachte public output:

```text
data/public/documents.jsonl
data/public/harvest_runs.jsonl
data/public/latest.json
```

Verwachte relationele public output:

```text
data/public/meetings.jsonl
data/public/meeting_items.jsonl
data/public/meeting_documents.jsonl
data/public/meeting_item_documents.jsonl
```

Verwachte kwaliteitsoutput:

```text
data/public/quality/summary.json
data/public/quality/issues.jsonl
```

## Commit policy

De workflow mag public data committen, maar niet alle gegenereerde data hoort in Git.

Wel toegestaan:

```text
data/public/
```

Niet toegestaan:

```text
data/raw/
*.pdf
grote tijdelijke downloads
lokale caches
```

Raw harvest output mag als tijdelijk GitHub Actions artifact worden geüpload, met beperkte retention, maar hoort niet als permanente Git-data te worden opgeslagen.

## CLI-gebruik

Snelle smoke test:

```bash
python -m open_ris_monitor.pipeline.run \
  --municipality huizen \
  --profile quick
```

Standaard publieke harvest:

```bash
python -m open_ris_monitor.pipeline.run \
  --municipality huizen \
  --profile public
```

Gecontroleerde backfill:

```bash
python -m open_ris_monitor.pipeline.run \
  --municipality huizen \
  --profile backfill \
  --max-documents 1000 \
  --meeting-scan-limit 1000 \
  --meeting-item-limit 5000
```

Diagnose zonder relationele exports:

```bash
python -m open_ris_monitor.pipeline.run \
  --municipality huizen \
  --profile quick \
  --no-include-relations
```

Gebruik `--no-include-relations` alleen voor diagnose. De normale publicatieworkflow verwacht relationele exports.

## Wanneer welk profiel gebruiken

Gebruik `quick` wanneer:

- je lokaal snel wilt controleren of de pipeline werkt;
- je retry- of connectorgedrag wilt testen;
- je geen volledige publicatie wilt draaien.

Gebruik `public` wanneer:

- je de live dataset wilt bijwerken;
- de scheduled workflow draait;
- je een normale handmatige publicatie wilt uitvoeren.

Gebruik `backfill` wanneer:

- je historische dekking wilt aanvullen;
- een eerdere periode opnieuw opgebouwd moet worden;
- je na een storing gecontroleerd wilt herstellen.

Gebruik `backfill` nooit als automatische dagelijkse workflow.

## Recovery policy

Bij een mislukte scheduled run:

1. controleer de GitHub Actions logs;
2. bepaal of het om upstream outage, rate limiting, codefout of validatiefout gaat;
3. draai eventueel handmatig `quick` om de bronkoppeling te testen;
4. draai daarna handmatig `public` als herstelrun;
5. gebruik `backfill` alleen als data uit een langere periode opnieuw opgebouwd moet worden.

Bij upstream outage hoeft niet direct data te worden aangepast. De vorige succesvolle publicatie blijft beschikbaar via GitHub Pages.

## Forking policy

Forks kunnen dezelfde workflow gebruiken met een andere gemeenteconfiguratie, zolang:

- de gemeenteconfiguratie bestaat onder `config/municipalities/`;
- de connector de benodigde bronroutes ondersteunt;
- de fork een eigen GitHub Actions schedule kiest;
- de cron niet exact op het hele uur hoeft te draaien.

Aanbevolen voor forks:

```text
Kies een eigen willekeurige minuut in de cron, bijvoorbeeld 17, 23, 41 of 52.
```

Dit voorkomt dat meerdere forks tegelijk dezelfde upstream leverancier belasten.

## Verder lezen

- `docs/architecture.md`
- `docs/data-model.md`
- `docs/export-contract.md`
- `docs/quality.md`
- `docs/validatie-ci.md`
- `docs/adding-a-municipality.md`
