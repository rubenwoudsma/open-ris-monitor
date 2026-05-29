# Document identity and document type analysis

This project keeps the original GemeenteOplossingen source fields, but adds analysis reports that help decide which identifiers and document categories are safe to use in the canonical model and public viewer.

## Identity analysis

The identity report is written to:

```text
data/public/quality/id_stability.json
```

It checks:

- canonical document ids
- source ids
- source object ids
- composite source keys, `source_id + source_object_id`
- duplicate and missing values

The current recommendation is to use the following traceable identity basis for versioning:

```text
municipality_id + source_system_id + source_id + source_object_id
```

This is still a snapshot analysis. True stability requires comparing several harvests over time.

## Document type analysis

The document type report is written to:

```text
data/public/quality/document_types.json
```

The report keeps the original RIS document type value and proposes a compact analytical category.

The source value remains important for traceability:

```text
source document type: Document ter kennisname (Inkomend)
```

The compact value is useful for filters and dashboards:

```text
normalized document type: notice
```

## Mapping principle

The mapping should be broad enough for users and future analysis, but not so broad that everything becomes `other` or `unknown`.

`unknown` should only be used when the source value is missing or explicitly says `Onbekend`.

Examples:

| Source label | Compact category |
|---|---|
| Raadsvoorstel | proposal |
| Collegevoorstel (Intern) | proposal |
| Bijlage | attachment |
| Document ter kennisname (Inkomend) | notice |
| Kennisgeving (Inkomend) | notice |
| Rapportage (Intern) | report |
| Toezeggingenlijst (Intern) | commitment |
| Uitnodigingen (Intern) | invitation |
| Verzoek om informatie (Inkomend) | request |
| Zienswijze (Inkomend) | objection_or_response |
| Onbekend | unknown |

This is still an analysis layer. Adding `normalized_document_type` to the canonical `Document` model should be handled in a separate issue after reviewing the report output.
