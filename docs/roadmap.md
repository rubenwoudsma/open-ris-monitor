# Roadmap

Open RIS Monitor is een kleine, reproduceerbare open-data-pipeline voor publieke raadsinformatie. De huidige focus ligt op compacte public exports, een statische GitHub Pages viewer en een relationele laag voor vergaderingen, agendapunten en documentkoppelingen.

## Uitgangspunten

- Geen PDF-bestanden in Git.
- Geen grote raw dumps in Git.
- Raw data alleen tijdelijk, bijvoorbeeld als GitHub Actions artifact.
- `data/public/` blijft de compacte, commitbare public export.
- De viewer blijft statisch, frameworkloos en geschikt voor GitHub Pages.
- De public exports blijven zo stabiel mogelijk voor hergebruikers en forks.
- Gemeente Huizen blijft de eerste implementatie, maar de opzet moet overdraagbaar blijven naar andere gemeenten en RIS-leveranciers.

## Afgerond

- Document-first harvest voor Huizen.
- Canonieke documentexports.
- GitHub Pages viewer.
- Automatische publicatie van `data/public/` na harvest.
- Gepagineerde documentharvest met `latest` en `full` modes.
- Documentversies en checksummetadata.
- #14 Research naar meetings- en agenda-item-endpoints.
- #15 Documenten koppelen aan vergaderingen en agendapunten.
- #31 Viewer verbeteren na relationele exports.
- #32 Harveststrategie en backfill operationaliseren.
- #33 Relationele dekking verbeteren en valideren via quick en public runs.
- #37 Public harvest prefereert recente documenten via het public profiel met latest mode.

## Huidige stand

De CLI ondersteunt drie harvestprofielen:

- `quick` voor snelle smoke tests.
- `public` voor de handmatige publicatie van de live dataset.
- `backfill` voor gecontroleerde historische aanvulling.

De handmatige workflow voor publieke RIS-data gebruikt standaard het profiel `public`. Dat profiel publiceert compacte JSONL-bestanden in `data/public/` en schrijft geen PDF's of raw dumps naar Git.

De public export bestaat momenteel uit:

- `documents.jsonl`
- `harvest_runs.jsonl`
- `meetings.jsonl`
- `meeting_items.jsonl`
- `meeting_documents.jsonl`
- `meeting_item_documents.jsonl`
- `latest.json`

`latest.json` is het publicatiecontract. Het bevat de outputpaden, relationele status, relationele samenvatting en publicatie-informatie over de overlap tussen gepubliceerde documenten en relationele koppelingen.

De viewer toont documentmetadata, compacte documenttypen en relationele context bij documenten waar die koppeling beschikbaar is. De volgende stap is niet nog meer relationele data verzamelen, maar de relationele laag beter navigeerbaar maken.

## Eerstvolgende volgorde

### 1. Roadmap actualiseren

Deze stap is bewust klein en documentatiegericht. Doel is om de roadmap gelijk te trekken met de afgeronde relationele mijlpalen en de geplande volgorde van de komende issues.

Resultaat:

- verouderde #15-focus verwijderen;
- afgeronde relationele en operationele issues markeren als afgerond;
- komende issues in de gewenste volgorde zetten;
- duidelijke scopegrens houden tussen documentatie, viewerfunctionaliteit en kwaliteitsrapportage.

### 2. #34 Eenvoudige agenda- en vergaderingbrowser

Doel: een eenvoudige statische browser toevoegen voor vergaderingen en agendapunten op basis van de bestaande relationele public exports.

Scope voor een eerste kleine implementatie:

- vergaderingen tonen uit `meetings.jsonl`;
- filteren op datum en bestuursorgaan of vergaderingstype, voor zover beschikbaar in de export;
- agendapunten per vergadering tonen uit `meeting_items.jsonl`;
- documenten per agendapunt tonen via `meeting_item_documents.jsonl`;
- teruglink of verwijzing naar documentrecords in de bestaande documententabel;
- geen backend, geen zoekindex, geen PDF-preview en geen framework.

Aanpak:

- hergebruik de bestaande JSONL-loader en relationele lookups in `site/assets/app.js`;
- voeg een compacte sectie toe in `site/index.html`, bijvoorbeeld boven of onder de documententabel;
- houd de eerste versie read-only en client-side;
- toon graceful fallback wanneer relationele exports ontbreken of leeg zijn.

### 3. #21 Documenttypen normaliseren

Doel: documenttypen verder normaliseren voor filtering, analyse en hergebruik.

Richting:

- originele RIS-bronwaarde behouden;
- genormaliseerde documenttypewaarde blijven publiceren;
- mapping centraal documenteren;
- relationele context gebruiken voor betere duiding, bijvoorbeeld bij bijlagen bij agendapunten;
- onbekende of niet-mappende waarden expliciet laten terugvallen op `unknown` of `other`.

### 4. #13 Kwaliteitsrapportage toevoegen

Doel: kwaliteitsrapportage uitbreiden op basis van de documentlaag en de relationele laag.

Mogelijke checks:

- documenten zonder gepubliceerde relationele koppeling;
- relationele koppelingen naar ontbrekende documenten;
- vergaderingen zonder agendapunten;
- agendapunten zonder documenten;
- dubbele of verdachte relationele koppelingen;
- verschillen tussen raw relationele tellingen en gepubliceerde relationele overlap;
- signalering wanneer public exports ontbreken of leeg zijn.

### 5. Docs cleanup

Later volgt een aparte cleanup om tijdelijke issue-documentatie te consolideren in `docs/`. Dit is bewust geen onderdeel van de komende kleine PR's, zodat functionele stappen klein en goed reviewbaar blijven.

## Operationele harveststrategie

De operationele lijn blijft:

- kleine `quick` runs voor smoke tests;
- `public` runs voor de live dataset;
- begrensde `backfill` runs voor historische dekking;
- raw output alleen tijdelijk bewaren;
- alleen compacte public JSONL committen;
- geen PDF-archief in Git.

Zie ook `docs/operations-harvest-strategy.md`.

## Latere richting

Na stabilisatie van Huizen:

- connectorinterface documenteren voor andere RIS-leveranciers;
- leverancier-capabilities expliciet maken;
- bron-endpoints scheiden van canonieke outputmodellen;
- public exportcontract stabiel houden over leveranciers heen;
- viewer uitbreidbaar houden zonder zware frameworkkeuze.
