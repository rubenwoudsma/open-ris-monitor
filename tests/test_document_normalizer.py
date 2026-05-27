"""Tests for document normalization."""

from __future__ import annotations

from datetime import datetime, timezone

from open_ris_monitor.connectors.gemeenteoplossingen import GemeenteOplossingenConnector
from open_ris_monitor.normalizers.gemeenteoplossingen import normalize_document


def test_normalize_document_maps_known_gemeenteoplossingen_fields() -> None:
    raw_document = {
        "confidential": 0,
        "description": "Raadsvoorstel Vaststellen jaarverslag en jaarrekening 2025",
        "documentTypeLabel": "Raadsvoorstel",
        "fileName": "Raadsvoorstel jaarstukken 2025 DEF.pdf",
        "fileSize": 69562,
        "id": 25927,
        "isTabsignDocument": False,
        "objectId": 43290,
        "publicationDate": {
            "date": "2026-05-27 00:00:00.000000",
            "timezone": "Europe/Berlin",
            "timezone_type": 3,
        },
    }
    connector = GemeenteOplossingenConnector("https://ris.gemeenteraadhuizen.nl/api/v2/")

    document = normalize_document(
        raw_document,
        municipality_id="gm0406",
        source_system_id="huizen-gemeenteoplossingen",
        connector=connector,
        retrieved_at=datetime(2026, 5, 27, 18, 8, 50, tzinfo=timezone.utc),
    )

    assert document.id == "gm0406-document-25927"
    assert document.source_id == "25927"
    assert document.source_object_id == "43290"
    assert document.title == "Raadsvoorstel Vaststellen jaarverslag en jaarrekening 2025"
    assert document.document_type == "Raadsvoorstel"
    assert document.filename == "Raadsvoorstel jaarstukken 2025 DEF.pdf"
    assert document.file_size_bytes == 69562
    assert document.publication_timezone == "Europe/Berlin"
    assert document.is_confidential is False
    assert str(document.download_url).endswith("/documents/25927/download")
