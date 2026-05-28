"""Regression tests for pipeline serialization."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from open_ris_monitor.exporters.json_exporter import write_jsonl
from open_ris_monitor.models.document import Document


def test_write_jsonl_accepts_pydantic_documents(tmp_path) -> None:
    document = Document(
        id="huizen-document-25927",
        municipality_id="gm0406",
        source_system_id="huizen-gemeenteoplossingen",
        source_id="25927",
        title="Raadsvoorstel Vaststellen jaarverslag en jaarrekening 2025",
        filename="Raadsvoorstel jaarstukken 2025 DEF.pdf",
        retrieved_at=datetime(2026, 5, 27, 18, 8, 50, tzinfo=timezone.utc),
        download_url="https://ris.gemeenteraadhuizen.nl/api/v2/documents/25927/download",
    )

    output = tmp_path / "documents.jsonl"
    write_jsonl(output, [document])

    records = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]

    assert records[0]["id"] == "huizen-document-25927"
    assert records[0]["source_id"] == "25927"
    assert records[0]["retrieved_at"] == "2026-05-27T18:08:50Z"
    assert records[0]["download_url"].endswith("/documents/25927/download")
