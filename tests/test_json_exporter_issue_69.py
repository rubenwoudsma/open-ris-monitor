"""Regression tests for issue #69 JSONL export hardening."""

from __future__ import annotations

import json

from open_ris_monitor.exporters.json_exporter import write_jsonl


def test_write_jsonl_escapes_unicode_line_separators_as_one_physical_line(tmp_path) -> None:
    path = tmp_path / "documents.jsonl"

    write_jsonl(
        path,
        [
            {
                "id": "huizen-document-line-separators",
                "schema_version": "1.0.0",
                "title": "Titel met echte newline\nnext en unicode separator\u2028next",
                "document_type": "Raadsvoorstel",
                "normalized_document_type": "raadsvoorstel",
                "date": "2026-06-15",
                "download_url": "https://example.invalid/document.pdf",
                "source_id": "line-separators",
                "filename": "stuk\u2029naam.pdf",
                "file_size_bytes": "2048",
                "text": "Regel 1\r\nRegel 2\u0085Regel 3",
            }
        ],
    )

    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    parsed = json.loads(lines[0])
    assert parsed["id"] == "huizen-document-line-separators"
    assert parsed["title"] == "Titel met echte newline\nnext en unicode separator\u2028next"
    assert parsed["filename"] == "stuk\u2029naam.pdf"
    assert parsed["text"] == "Regel 1\r\nRegel 2\u0085Regel 3"


def test_write_jsonl_escapes_quotes_and_control_characters_in_generic_exports(tmp_path) -> None:
    path = tmp_path / "meeting_documents.jsonl"

    write_jsonl(
        path,
        [
            {
                "id": "rel-1",
                "meeting_id": "huizen-meeting-1",
                "document_id": "huizen-document-1",
                "label": "Bijlage \"A\"\nmet toelichting\u2028extra",
            }
        ],
    )

    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    parsed = json.loads(lines[0])
    assert parsed["label"] == "Bijlage \"A\"\nmet toelichting\u2028extra"
