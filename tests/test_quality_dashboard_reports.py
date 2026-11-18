"""Verify report generation from the compact public export contract."""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema.validators import validator_for

from open_ris_monitor.analysis.generate_public_reports import generate_reports
from open_ris_monitor.exporters.generate_schemas import generate_schemas


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def test_reports_cover_direct_and_agenda_links_without_internal_model_fields(
    tmp_path: Path,
) -> None:
    public_dir = tmp_path / "public"
    public_dir.mkdir()
    _write_jsonl(
        public_dir / "documents.jsonl",
        [
            {"id": "doc-1", "title": "Linked", "date": "2026-11-01"},
            {"id": "doc-2", "title": "Unlinked", "date": "2026-10-01"},
        ],
    )
    _write_jsonl(
        public_dir / "meetings.jsonl",
        [
            {"id": "meeting-1", "date": "2026-11-01"},
            {"id": "meeting-2", "date": "2026-11-02"},
            {"id": "meeting-3", "description": "No documents", "date": "invalid"},
        ],
    )
    _write_jsonl(
        public_dir / "meeting_documents.jsonl",
        [{"meeting_id": "meeting-1", "document_id": "doc-1"}],
    )
    _write_jsonl(
        public_dir / "meeting_item_documents.jsonl",
        [{"meeting_id": "meeting-2", "document_id": "doc-1"}],
    )
    (public_dir / "latest.json").write_text('{"outputs": {}}', encoding="utf-8")

    generate_reports(public_dir)
    schemas = tmp_path / "schemas"
    schemas.mkdir()
    # Generating report schemas must never replace the compact JSONL contract.
    document_schema_path = schemas / "document.schema.json"
    document_schema_path.write_text('{"title": "Existing public contract"}', encoding="utf-8")
    generate_schemas(schemas)

    reports = {}
    for name in ("unlinked_documents", "meetings_without_documents"):
        report = json.loads((public_dir / "quality" / f"{name}.json").read_text(encoding="utf-8"))
        schema = json.loads((schemas / f"{name}.schema.json").read_text(encoding="utf-8"))
        validator = validator_for(schema)
        validator.check_schema(schema)
        validator(schema).validate(report)
        reports[name] = report

    assert reports["unlinked_documents"]["unlinked_documents_count"] == 1
    assert reports["unlinked_documents"]["findings"][0]["document_id"] == "doc-2"
    assert reports["meetings_without_documents"]["meetings_without_documents_count"] == 1
    assert reports["meetings_without_documents"]["findings"][0]["meeting_id"] == "meeting-3"
    assert reports["meetings_without_documents"]["findings"][0]["date"] is None
    assert json.loads(document_schema_path.read_text(encoding="utf-8")) == {
        "title": "Existing public contract"
    }
    latest = json.loads((public_dir / "latest.json").read_text(encoding="utf-8"))
    assert latest["outputs"]["unlinked_documents"] == "quality/unlinked_documents.json"
    assert (
        latest["outputs"]["meetings_without_documents"] == "quality/meetings_without_documents.json"
    )
