"""Tests for the public document export contract."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from open_ris_monitor.exporters.json_exporter import write_jsonl
from open_ris_monitor.models.document import Document


def test_public_document_export_preserves_source_metadata(tmp_path: Path) -> None:
    document = Document(
        id="huizen-document-25892",
        municipality_id="huizen",
        source_system_id="gemeenteoplossingen",
        source_id="25892",
        source_object_id="43243",
        title="Verzoek commissiebehandeling",
        description=None,
        document_type="Ingekomen stuk",
        normalized_document_type="incoming_document",
        normalized_document_type_label="Ingekomen stuk",
        filename="Verzoek commissiebehandeling.pdf",
        file_size_bytes=62118,
        publication_datetime=datetime(2026, 5, 19, tzinfo=timezone.utc),
        publication_timezone="Europe/Amsterdam",
        source_url="https://ris.gemeenteraadhuizen.nl/api/v2/documents/25892/download",
        download_url="https://ris.gemeenteraadhuizen.nl/api/v2/documents/25892/download",
        retrieved_at=datetime(2026, 6, 9, tzinfo=timezone.utc),
        raw={
            "documentTypeLabel": "Ingekomen stuk",
            "fileName": "Verzoek commissiebehandeling.pdf",
            "fileSize": 62118,
            "id": 25892,
            "objectId": 43243,
        },
    )

    export_path = tmp_path / "data" / "public" / "documents.jsonl"
    write_jsonl(export_path, [document])

    exported = json.loads(export_path.read_text(encoding="utf-8"))

    assert exported == {
        "id": "huizen-document-25892",
        "schema_version": "1.0.0",
        "title": "Verzoek commissiebehandeling",
        "type": "incoming_document",
        "document_type": "Ingekomen stuk",
        "normalized_document_type": "incoming_document",
        "normalized_document_type_label": "Ingekomen stuk",
        "date": "2026-05-19",
        "url": "https://ris.gemeenteraadhuizen.nl/api/v2/documents/25892/download",
        "download_url": "https://ris.gemeenteraadhuizen.nl/api/v2/documents/25892/download",
        "retrieved_at": "2026-06-09T00:00:00Z",
        "source_id": "25892",
        "source_object_id": "43243",
        "filename": "Verzoek commissiebehandeling.pdf",
        "file_size_bytes": 62118,
        "text": None,
    }
    assert "raw" not in exported
    assert "municipality_id" not in exported


def test_public_document_export_accepts_existing_compact_dict(tmp_path: Path) -> None:
    export_path = tmp_path / "documents.jsonl"

    write_jsonl(
        export_path,
        [
            {
                "id": "huizen-document-1",
                "schema_version": "1.0.0",
                "title": "Compact record",
                "type": "proposal",
                "date": "2026-01-02",
                "url": "https://example.test/document.pdf",
                "file_size_bytes": "123",
            }
        ],
    )

    exported = json.loads(export_path.read_text(encoding="utf-8"))

    assert exported["type"] == "proposal"
    assert exported["normalized_document_type"] == "proposal"
    assert exported["file_size_bytes"] == 123
    assert exported["date"] == "2026-01-02"
