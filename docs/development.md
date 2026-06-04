# Development

## Doel

Dit document beschrijft de werkafspraken rond ontwikkeling, publicatie en onderhoud van de repository.

Open RIS Monitor is klein gehouden zodat het met gewone GitHub-tools beheersbaar blijft. De nadruk ligt op herhaalbare exports, kleine PR's en duidelijke documentatie.

## Kernregels

- geen PDF-bestanden in Git,
- geen raw dumps in Git,
- raw output alleen tijdelijk als workflow artifact,
- `data/public/` is de commitbare public laag,
- de viewer blijft statisch en frameworkloos,
- de documentatie moet leesbaar blijven voor hergebruik door andere gemeenten.

## Aanpak voor wijzigingen

Werk bij voorkeur in kleine, reviewbare stappen.

Een logische volgorde is:

1. wijzig documentatie of configuratie,
2. test met een kleine harvest,
3. controleer de public exports,
4. werk daarna pas verder aan viewer of datamodel.

Dat maakt fouten makkelijker te herkennen en houdt PR's compact.

## Harvestprofielen

Gebruik de profielen uit `docs/harvesting.md`:

- `quick` voor smoke tests,
- `public` voor normale publicatie,
- `backfill` voor grotere historische aanvulling.

## Verhoudingen tussen bestanden

De belangrijkste contracten zijn:

- `README.md` voor de hoofduitleg,
- `docs/architecture.md` voor de systeemlagen,
- `docs/data-model.md` voor de canonieke entiteiten,
- `docs/harvesting.md` voor bron- en workflowkennis,
- `docs/quality.md` voor rapportage en controles,
- `docs/roadmap.md` voor de volgende stappen,
- `docs/adding-a-municipality.md` voor forks en nieuwe gemeenten.

## Publicatie

De publicatieketen is bewust simpel:

- brondata ophalen,
- normaliseren,
- publiceren naar JSONL,
- viewer leest direct uit `data/public/`.

Dat betekent dat wijzigingen aan de public exports zorgvuldig moeten gebeuren. Als een bestand onderdeel is van het public contract, moet een wijziging daarvan in de roadmap en PR-beschrijving genoemd worden.

## Forks en andere gemeenten

De repository is bedoeld om te kunnen forken.

Nieuwe gemeenten zouden in principe via configuratie moeten kunnen starten. Alleen wanneer een andere RIS-leverancier wordt gebruikt, hoort daar een nieuwe connector bij.

Zie `docs/adding-a-municipality.md`.

## Onderhoudstips

- houd de README actueel als de hoofdinformatie verandert,
- houd de roadmap synchroon met afgeronde issues,
- consolideer tijdelijke issue-notities in stabiele docs,
- bewaar bronanalyse en kwaliteit als aparte, leesbare secties,
- vermijd grote, moeilijk te reviewen documentatie-sprongen.

## Verder lezen

- `README.md`
- `docs/roadmap.md`
- `docs/adding-a-municipality.md`
