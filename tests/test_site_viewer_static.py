from pathlib import Path


def test_viewer_uses_dom_table_rows_instead_of_raw_html_fragments():
    app_js = Path("site/assets/app.js").read_text(encoding="utf-8")

    assert 'document.createElement("tr")' in app_js
    assert 'document.createElement("td")' in app_js
    assert "elements.tableBody.replaceChildren()" in app_js


def test_viewer_supports_outputs_and_exports_manifest_keys():
    app_js = Path("site/assets/app.js").read_text(encoding="utf-8")

    assert "latest.outputs || latest.exports" in app_js


def test_viewer_has_robust_jsonl_parser():
    app_js = Path("site/assets/app.js").read_text(encoding="utf-8")

    assert "function parseJsonObjects" in app_js
    assert "concatenated JSON objects" in app_js
    assert "JSONL-bestand bevat geen parsebare records" in app_js


def test_viewer_reports_document_relation_match_count():
    app_js = Path("site/assets/app.js").read_text(encoding="utf-8")

    assert "documentsWithRelations" in app_js
    assert "getoonde documenten hebben een koppeling" in app_js


def test_viewer_matches_relations_on_multiple_document_identifiers():
    app_js = Path("site/assets/app.js").read_text(encoding="utf-8")

    assert "function getDocumentIdentifiers" in app_js
    assert "function getRelationDocumentIdentifiers" in app_js
    assert "document_source_id" in app_js
    assert "document_object_id" in app_js
    assert "getLookupRelations" in app_js
