# Roadmap

Deze roadmap beschrijft de beoogde ontwikkeling van Open RIS Monitor. De volgorde is bewust incrementeel: eerst een werkende document-first keten, daarna pas verrijking, bredere RIS-structuur en linked data.

## Afgerond

### Milestone 1, document-first harvest

Status: afgerond.

Resultaat:

- GitHub Actions workflow voor handmatige harvest
- Gemeente Huizen als eerste configuratie
- GemeenteOplossingen connector voor het documents-endpoint
- Raw output als artifact
- Eerste succesvolle harvest met 25 documenten

Belangrijke keuze:

- eerst metadata-only werken
- geen PDF-bestanden opslaan in Git

### Milestone 2, canonieke modellen en public exports

Status: afgerond.

Resultaat:

- canoniek Document model
- normalisatie van GemeenteOplossingen-documenten
- export naar `data/public/documents.jsonl`
- export naar `data/public/harvest_runs.jsonl`
- export naar `data/public/latest.json`
- public export artifact in GitHub Actions

Belangrijke keuze:

- frontend en hergebruikers lezen niet uit raw brondata, maar uit de canonieke public export

## Huidige milestone

### Milestone 3, publieke site

Status: in uitvoering.

Doel:

- bestaande `data/public` bestanden zichtbaar maken via een eenvoudige GitHub Pages-site
- geen build-framework gebruiken
- site direct laten lezen uit `data/public/latest.json` en `data/public/documents.jsonl`

Scope:

- dashboard met laatste harvestinformatie
- documenttabel
- zoeken op titel, bestandsnaam en documenttype
- filteren op documenttype
- links naar publieke databestanden

Niet in scope:

- automatische commit van nieuwe harvest-output
- PDF-downloads en tekstextractie
- vergaderingen en agendapunten
- eigen backend API

Acceptatiecriteria:

- `site/index.html` laadt zonder buildstap
- site leest `data/public/latest.json`
- site leest `data/public/documents.jsonl`
- documenttabel toont de genormaliseerde documenten
- eenvoudige zoekfunctie werkt client-side
- README beschrijft hoe de site gebruikt kan worden

## Volgende milestones

### Milestone 4, public export persistentie

Gekoppeld aan issue #9.

Doel:

- bepalen hoe gegenereerde public exports structureel beschikbaar blijven
- voorkomen dat raw data en grote bestanden onnodig in Git groeien

Mogelijke aanpakken:

1. `data/public` automatisch committen bij een succesvolle harvest
2. alleen committen wanneer de inhoud gewijzigd is
3. public exports publiceren via GitHub Pages zonder raw data te committen
4. raw data artifact-only houden

Aanbevolen richting:

- `data/public` mag structureel gepubliceerd worden
- `data/raw` blijft in principe artifact-only
- automatische commits pas toevoegen nadat de website goed werkt

### Milestone 5, documentkwaliteit en versies

Doel:

- documentversies bijhouden
- checksums berekenen
- bestandsgrootte monitoren
- kwaliteitsissues vastleggen

Mogelijke outputs:

```text
data/public/document_versions.jsonl
data/public/quality_issues.jsonl
```

Voorbeelden van kwaliteitsissues:

- generieke bestandsnaam
- ontbrekende titel
- ontbrekend documenttype
- extreem groot bestand
- ontbrekende publicatiedatum

### Milestone 6, tijdelijke PDF-verwerking

Doel:

- PDF's tijdelijk downloaden tijdens de harvest
- tekst extraheren waar mogelijk
- PDF zelf niet committen

Mogelijke outputs:

```text
data/public/document_text_index.jsonl
data/public/text/<document-id>.txt
```

Besluitpunt:

- tekstextracten wel of niet structureel opslaan in Git

### Milestone 7, vergaderingen en agendapunten

Doel:

- RIS-structuur uitbreiden van document-first naar volledige context
- vergaderingen, agendapunten en documentrelaties ophalen
- canonieke modellen voor Meeting en AgendaItem activeren

Gewenste relaties:

```text
Meeting -> AgendaItem -> Document
Meeting -> Document
AgendaItem -> Decision
```

### Milestone 8, forkbaarheid voor andere gemeenten

Doel:

- documenteren hoe een andere gemeente toegevoegd kan worden
- voorbeeldconfiguraties verbeteren
- connector-contract aanscherpen
- tests toevoegen met fixturedata

Output:

```text
docs/adding-a-municipality.md
config/municipalities/example.yml
```

### Milestone 9, linked data en open standaarden

Doel:

- JSON-LD export toevoegen
- aansluiten op relevante begrippen uit Open Raadsinformatie waar praktisch mogelijk
- stabiele URI's voor documenten, vergaderingen en agendapunten

Mogelijke outputs:

```text
data/public/jsonld/documents.jsonld
data/public/jsonld/meetings.jsonld
```

## Principes

1. Houd de pipeline belangrijker dan de viewer.
2. Raw brondata is nuttig, maar public exports vormen het contract.
3. Geen PDF's in Git zolang daar geen expliciet opslagbeleid voor is.
4. Maak elke uitbreiding eerst werkend voor Huizen, daarna pas generiek.
5. Documenteer aannames en beperkingen in de repo.
6. Houd het project forkbaar voor andere gemeenten.
