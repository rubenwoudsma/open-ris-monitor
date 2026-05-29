# Issue #22 pakket

Dit pakket voegt rapportage toe voor documentidentiteit en documenttypen.

## Bestanden

```text
src/open_ris_monitor/analysis/__init__.py
src/open_ris_monitor/analysis/document_identity.py
src/open_ris_monitor/analysis/generate_public_reports.py
tests/test_document_identity_analysis.py
docs/document-identity-and-types.md
```

## Workflow-stap toevoegen

Voeg in `.github/workflows/harvest.yml` na de stap `Run metadata-only harvest and public export` deze stap toe, vóór `Show generated output` en vóór upload/commit van artifacts:

```yaml
      - name: Generate public quality reports
        run: |
          python -m open_ris_monitor.analysis.generate_public_reports \
            --public-dir data/public
```

Hierdoor ontstaan:

```text
data/public/quality/id_stability.json
data/public/quality/document_types.json
```

Ook wordt `data/public/latest.json` uitgebreid met verwijzingen naar deze rapporten.

## Commit-message

```text
Add document identity and type analysis reports
```
