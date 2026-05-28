from datetime import datetime, timezone

from open_ris_monitor.enrichers.checksum import build_document_version, sha256_bytes
from open_ris_monitor.models.document import Document


def test_sha256_bytes_returns_expected_digest() -> None:
    assert sha256_bytes(b"abc") == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


def test_build_document_version_detects_changed_content() -> None:
    document = Document(
        id="huizen-document-123",
        municipality_id="gm0406",
        source_system_id="huizen-gemeenteoplossingen",
        source_id="123",
        source_object_id="456",
        title="Test document",
        filename="test.pdf",
        file_size_bytes=3,
        retrieved_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        download_url="https://ris.gemeenteraadhuizen.nl/api/v2/documents/123/download",
        raw={},
    )
    previous = {
        "id": "old-version",
        "document_id": "huizen-document-123",
        "sha256": "previous-digest",
    }

    version = build_document_version(
        document,
        file_content=b"abc",
        retrieved_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
        previous_versions_by_document_id={"huizen-document-123": previous},
    )

    assert version.document_id == "huizen-document-123"
    assert version.downloaded_file_size_bytes == 3
    assert version.content_changed is True
    assert version.previous_version_id == "old-version"
