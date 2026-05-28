# Opslagbeleid

## Uitgangspunt

De repository moet klein, forkbaar en onderhoudbaar blijven. Daarom worden PDF-bestanden niet standaard in Git opgeslagen en blijft raw data in principe artifact-only.

Het opslagbeleid maakt onderscheid tussen:

```text
data/raw/       brondata en debugging, beperkt bewaren
data/public/    publicatiebestanden, bedoeld voor hergebruik en GitHub Pages
artifacts/      tijdelijke output van GitHub Actions
```

## Huidig beleid

| Locatie | Status | Doel |
|---|---|---|
| `data/raw/` | niet automatisch committen | debugging en controle |
| `data/public/` | wel automatisch committen bij `commit_public=true` | publieke dataset en website |
| GitHub Actions artifacts | tijdelijk bewaren | inspectie van run-output |
| PDF-bestanden | niet opslaan in Git | alleen later tijdelijk verwerken |

## Huidige MVP-modus

```yaml
storage:
  mode: metadata_only
  commit_raw_api: false
  commit_public_exports: true
  commit_pdf_files: false
```

In de huidige fase worden vooral metadata en public exports opgeslagen. PDF-verwerking komt pas later.

## Wat bewaren we wel?

- Genormaliseerde JSONL-bestanden.
- Public JSON-bestanden.
- Harvest-run metadata.
- Beperkte voorbeelddata in `data/public/`.
- Raw harvest-output als tijdelijk artifact.
- Later: checksums van documenten.
- Later: kwaliteitsrapporten.

## Wat bewaren we niet standaard?

- PDF-bestanden.
- Dagelijkse volledige duplicaten van alle brondata.
- Grote databasebestanden.
- Grote tijdelijke analysebestanden.
- Onbeperkte raw snapshots.

## Waarom data/raw artifact-only blijft

Raw data is waardevol voor inspectie, maar kan snel groeien en is sterk afhankelijk van de bronstructuur. Daarom geldt:

```text
data/raw/latest wordt tijdens de workflow gemaakt
data/raw/latest wordt als artifact geupload
data/raw/latest wordt niet automatisch naar Git gecommit
```

Een handmatige raw snapshot kan tijdelijk nuttig zijn voor analyse, maar is geen structureel publicatiebeleid.

## Waarom data/public wel gecommit mag worden

`data/public/` bevat de gestandaardiseerde public exports. Deze bestanden zijn:

- kleiner dan raw brondata
- stabieler qua structuur
- direct bruikbaar voor GitHub Pages
- geschikt voor hergebruik door anderen
- onderdeel van het publieke contract van het project

Daarom mag de harvest workflow `data/public/` automatisch bijwerken als `commit_public=true`.

## Tijdelijke PDF-verwerking, later

In latere fases mag de pipeline PDF's tijdelijk downloaden om:

- SHA256-checksums te berekenen
- bestandsgrootte te controleren
- tekst te extraheren
- te bepalen of OCR nodig zou zijn
- documentversies te detecteren

Na verwerking wordt de PDF verwijderd uit de tijdelijke workspace.

## Opslagmodi

### metadata_only

Alleen metadata, links en basiscontroles. Dit is de huidige MVP-modus.

### metadata_plus_checksums

Metadata plus tijdelijk downloaden van PDF's voor checksums en documentversies. PDF's worden niet gecommit.

### metadata_plus_text

Metadata, checksums en tekstextracten. Alleen gebruiken als tekstbestanden beheersbaar blijven.

### full_archive

Volledige PDF-archivering. Alleen later overwegen met externe opslag, Git LFS, releases of een publiek archief. Niet geschikt als standaardmodus voor deze repo.

## Richtlijn voor toekomstige wijzigingen

Voeg geen grote bestanden of structurele raw snapshots toe zonder expliciet issue en PR-besluit. De standaard blijft:

```text
public exports in Git
raw data als artifact
PDF's buiten Git
```
