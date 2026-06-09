from __future__ import annotations

from datetime import datetime, timezone

from open_ris_monitor.normalizers.gemeenteoplossingen import normalize_document, normalize_documents


def _retrieved_at() -> datetime:
    return datetime(2026, 6, 9, 12, 0, 0, tzinfo=timezone.utc)


def test_gemeenteoplossingen_document_metadata_is_preserved_from_source_payload() -> None:
    raw_document = {
        "id": 25892,
        "objectId": 43243,
        "title": "Verzoek commissiebehandeling",
        "description": "Verzoek commissiebehandeling over raadsinformatie",
        "documentTypeLabel": "Overig",
        "fileName": "Verzoek commissiebehandeling.pdf",
        "fileSize": 62118,
        "publicationDate": {
            "date": "2026-05-19 10:15:30.000000",
            "timezone_type": 3,
            "timezone": "Europe/Amsterdam",
        },
    }

    document = normalize_document(
        raw_document,
        municipality_id="gm0406",
        municipality_slug="huizen",
        source_system_id="huizen-gemeenteoplossingen",
        retrieved_at=_retrieved_at(),
        build_download_url=lambda source_id: f"https://ris.gemeenteraadhuizen.nl/api/v2/documents/{source_id}/download",
    )

    assert document.id == "huizen-document-25892"
    assert document.source_id == "25892"
    assert document.source_object_id == "43243"
    assert document.title == "Verzoek commissiebehandeling"
    assert document.description == "Verzoek commissiebehandeling over raadsinformatie"
    assert document.document_type == "Overig"
    assert document.normalized_document_type == "other"
    assert document.normalized_document_type_label == "Overig"
    assert document.filename == "Verzoek commissiebehandeling.pdf"
    assert document.file_size_bytes == 62118
    assert document.publication_datetime is not None
    assert document.publication_datetime.isoformat() == "2026-05-19T10:15:30"
    assert document.publication_timezone == "Europe/Amsterdam"
    assert str(document.download_url) == "https://ris.gemeenteraadhuizen.nl/api/v2/documents/25892/download"
    assert document.raw["documentTypeLabel"] == "Overig"
    assert document.raw["fileName"] == "Verzoek commissiebehandeling.pdf"
    assert document.raw["fileSize"] == 62118


def test_gemeenteoplossingen_document_type_label_drives_human_label_not_technical_type() -> None:
    raw_document = {
        "id": "25927",
        "objectId": "98765",
        "description": "Raadsvoorstel Vaststellen jaarverslag en jaarrekening 2025",
        "documentTypeLabel": "Raadsvoorstel",
        "fileName": "Raadsvoorstel jaarstukken 2025 DEF.pdf",
        "fileSize": 245760,
        "publicationDate": {"date": "2026-05-27 18:08:50.000000", "timezone": "Europe/Amsterdam"},
    }

    document = normalize_document(
        raw_document,
        municipality_id="gm0406",
        municipality_slug="huizen",
        source_system_id="huizen-gemeenteoplossingen",
        retrieved_at=_retrieved_at(),
    )

    assert document.source_id == "25927"
    assert document.source_object_id == "98765"
    assert document.document_type == "Raadsvoorstel"
    assert document.normalized_document_type == "proposal"
    assert document.normalized_document_type_label == "Voorstel"
    assert document.filename == "Raadsvoorstel jaarstukken 2025 DEF.pdf"
    assert document.file_size_bytes == 245760


def test_normalize_documents_skips_records_without_source_identifier_but_keeps_metadata_for_valid_records() -> None:
    documents = normalize_documents(
        [
            {
                "id": None,
                "title": "Record zonder bron-id",
                "documentTypeLabel": "Overig",
                "fileName": "zonder-id.pdf",
                "fileSize": 1,
            },
            {
                "id": 26000,
                "objectId": 26001,
                "title": "Motie openbaar bestuur",
                "documentTypeLabel": "Moties",
                "fileName": "motie-openbaar-bestuur.pdf",
                "fileSize": 4096,
            },
        ],
        municipality_id="gm0406",
        municipality_slug="huizen",
        source_system_id="huizen-gemeenteoplossingen",
        retrieved_at=_retrieved_at(),
    )

    assert len(documents) == 1
    assert documents[0].id == "huizen-document-26000"
    assert documents[0].source_id == "26000"
    assert documents[0].source_object_id == "26001"
    assert documents[0].document_type == "Moties"
    assert documents[0].normalized_document_type == "motion"
    assert documents[0].normalized_document_type_label == "Motie"
    assert documents[0].filename == "motie-openbaar-bestuur.pdf"
    assert documents[0].file_size_bytes == 4096
