# Opslagbeleid

## Uitgangspunt

De repository moet klein, forkbaar en onderhoudbaar blijven. Daarom worden PDF-bestanden niet standaard in Git opgeslagen.

## Aanbevolen MVP-modus

```yaml
storage:
  mode: metadata_plus_text
  commit_raw_api: true
  commit_pdf_files: false
  keep_action_artifacts_days: 3
```

## Wat bewaren we wel?

- Raw API responses, beperkt tot latest of compacte snapshots.
- Genormaliseerde JSONL-bestanden.
- Public JSON en CSV exports.
- Checksums van documenten.
- Tekstextracten, zolang deze beheersbaar blijven.
- Kwaliteitsrapporten.
- Harvest logs op hoofdlijnen.

## Wat bewaren we niet standaard?

- PDF-bestanden.
- Dagelijkse volledige duplicaten van alle brondata.
- Grote databasebestanden.
- Grote tijdelijke analysebestanden.

## Tijdelijke PDF-verwerking

De pipeline mag PDF's tijdelijk downloaden om:

- SHA256-checksums te berekenen.
- Bestandsgrootte te bepalen.
- Tekst te extraheren.
- Te bepalen of OCR nodig zou zijn.

Na verwerking wordt de PDF verwijderd uit de tijdelijke workspace.

## Opslagmodi

### metadata_only

Alleen metadata, links en eventuele basiscontroles.

### metadata_plus_text

Aanbevolen voor de MVP. Metadata, checksums, tekstextracten en kwaliteitsinformatie.

### full_archive

Alleen later overwegen met externe opslag, Git LFS, releases of een publiek archief.
