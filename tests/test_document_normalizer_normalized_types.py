from datetime import datetime, timezone

from open_ris_monitor.normalizers.gemeenteoplossingen import normalize_document


def test_normalize_document_adds_normalized_document_type() -> None:
    raw_document = {
        "id": 25927,
        "objectId": 43290,
        "description": "Raadsvoorstel Vaststellen jaarverslag en jaarrekening 2025",
        "documentTypeLabel": "Raadsvoorstel",
        "fileName": "Raadsvoorstel jaarstukken 2025 DEF.pdf",
        "fileSize": 69562,
        "confidential": 0,
        "isTabsignDocument": False,
        "publicationDate": {
            "date": "2026-05-27 00:00:00.000000",
            "timezone": "Europe/Berlin",
        },
    }

    document = normalize_document(
        raw_document,
        municipality_id="gm0406",
        municipality_slug="huizen",
        source_system_id="huizen-gemeenteoplossingen",
        build_download_url=lambda source_id: f"https://example.test/documents/{source_id}/download",
        retrieved_at=datetime.now(timezone.utc),
    )

    assert document.document_type == "Raadsvoorstel"
    assert document.normalized_document_type == "proposal"
    assert document.normalized_document_type_label == "Voorstel"
