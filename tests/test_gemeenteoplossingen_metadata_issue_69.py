from __future__ import annotations

from datetime import datetime, timezone

from open_ris_monitor.normalizers.gemeenteoplossingen import normalize_document


def test_normalize_document_uses_source_file_url_and_file_size_variants() -> None:
    document = normalize_document(
        {
            "id": 123,
            "title": "Voorstel openbare ruimte",
            "objectId": "OBJ-123",
            "documentType": {"description": "Raadsvoorstel"},
            "file": {
                "downloadUrl": "https://example.invalid/document/123.pdf",
                "fileSize": "2048",
                "fileName": "voorstel.pdf",
            },
        },
        municipality_id="gm0406",
        municipality_slug="huizen",
        source_system_id="gemeenteoplossingen-huizen",
        build_download_url=lambda source_id: f"https://fallback.invalid/{source_id}",
        retrieved_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )

    assert document.id == "huizen-document-123"
    assert document.source_object_id == "OBJ-123"
    assert document.document_type == "Raadsvoorstel"
    assert document.filename == "voorstel.pdf"
    assert document.file_size_bytes == 2048
    assert str(document.download_url) == "https://example.invalid/document/123.pdf"
    assert str(document.source_url) == "https://example.invalid/document/123.pdf"


def test_normalize_document_falls_back_to_download_endpoint_when_source_url_is_absent() -> None:
    document = normalize_document(
        {"id": "456", "title": "Besluitenlijst", "fileSize": 10},
        municipality_id="gm0406",
        municipality_slug="huizen",
        source_system_id="gemeenteoplossingen-huizen",
        build_download_url=lambda source_id: f"https://fallback.invalid/{source_id}/download",
        retrieved_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )

    assert str(document.download_url) == "https://fallback.invalid/456/download"
    assert str(document.source_url) == "https://fallback.invalid/456/download"
    assert document.file_size_bytes == 10
