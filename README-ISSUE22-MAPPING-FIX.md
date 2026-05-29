# Issue 22 mapping fix

This update reduces unnecessary `unknown` document type classifications in the document type analysis report.

It does not yet change the canonical `Document` model. It only improves the analysis report under:

```text
data/public/quality/document_types.json
```

The goal is to keep the viewer and future quality reports more useful by mapping known GemeenteOplossingen labels into compact categories, while reserving `unknown` for truly unknown or missing values.

Recommended test:

```text
mode: full
batch_size: 100
max_documents: 1000
enrich_checksums: false
commit_public: false
```

Then check that:

```text
data/public/quality/document_types.json
```

contains a lower `unknown_document_type_count` and a list of `unknown_source_document_types`.
