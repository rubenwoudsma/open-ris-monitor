# Storage policy

## Doel

De opslagstrategie houdt de repository licht, forkbaar en geschikt voor GitHub Pages.

## data/raw

`data/raw/` bevat raw bronoutput. Deze data wordt tijdens de harvest aangemaakt en als artifact geupload.

Beleid:

- Niet automatisch committen.
- Alleen gebruiken voor inspectie en debugging.
- Geen PDF-bestanden opslaan.

## data/public

`data/public/` bevat genormaliseerde, herbruikbare exports.

Beleid:

- Mag automatisch worden gecommit door GitHub Actions.
- Wordt gebruikt door GitHub Pages.
- Bevat lichte bestanden zoals JSONL en JSON.

## PDF-bestanden

PDF-bestanden worden niet opgeslagen in Git.

Latere verrijking mag PDF's tijdelijk downloaden om metadata, checksums of tekst te extraheren. Daarna worden PDF's verwijderd uit de workflow-runner.

## Full harvest

Full harvests moeten gecontroleerd worden uitgevoerd met:

```text
batch_size
max_documents
```

Zo voorkomen we onnodige belasting van de bron-API en onbeheersbare groei van de repository.
