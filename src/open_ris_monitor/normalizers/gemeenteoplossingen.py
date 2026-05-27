"""Normalizers for GemeenteOplossingen API records."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from open_ris_monitor.connectors.gemeenteoplossingen import GemeenteOplossingenConnector
from open_ris_monitor.models.document import Document


def _slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "unknown"


def _parse_publication_datetime(raw_value: Any) -> tuple[datetime | None, str | None]:
    if not isinstance(raw_value, dict):
        return None, None

    date_value = raw_value.get("date")
    timezone_value = raw_value.get("timezone")
    if not isinstance(date_value, str) or not date_value:
        return None, timezone_value if isinstance(timezone_value, str) else None

    normalized = date_value.replace(" ", "T")
    try:
        return datetime.fromisoformat(normalized), timezone_value if isinstance(timezone_value, str) else None
    except ValueError:
        return None, timezone_value if isinstance(timezone_value, str) else None


def normalize_document(
    raw_document: dict[str, Any],
    *,
    municipality_id: str,
    source_system_id: str,
    connector: GemeenteOplossingenConnector,
    retrieved_at: datetime,
) -> Document:
    """Convert one raw GemeenteOplossingen document into a canonical Document."""
    source_id = str(raw_document["id"])
    source_object_id = raw_document.get("objectId")
    publication_datetime, publication_timezone = _parse_publication_datetime(
        raw_document.get("publicationDate")
    )

    description = raw_document.get("description")
    filename = raw_document.get("fileName")
    title = str(description or filename or f"Document {source_id}").strip()

    canonical_id = f"{_slugify(municipality_id)}-document-{source_id}"
    download_url = connector.build_document_download_url(source_id)

    return Document(
        id=canonical_id,
        municipality_id=municipality_id,
        source_system_id=source_system_id,
        source_id=source_id,
        source_object_id=str(source_object_id) if source_object_id is not None else None,
        title=title,
        description=str(description).strip() if description else None,
        document_type=raw_document.get("documentTypeLabel"),
        filename=raw_document.get("fileName"),
        file_size_bytes=raw_document.get("fileSize"),
        publication_datetime=publication_datetime,
        publication_timezone=publication_timezone,
        is_confidential=bool(raw_document.get("confidential")),
        is_tabsign_document=bool(raw_document.get("isTabsignDocument")),
        source_url=download_url,
        download_url=download_url,
        retrieved_at=retrieved_at,
        raw=raw_document,
    )


def normalize_documents(
    raw_documents: list[dict[str, Any]],
    *,
    municipality_id: str,
    source_system_id: str,
    connector: GemeenteOplossingenConnector,
    retrieved_at: datetime,
) -> list[Document]:
    """Normalize a list of raw documents."""
    return [
        normalize_document(
            raw_document,
            municipality_id=municipality_id,
            source_system_id=source_system_id,
            connector=connector,
            retrieved_at=retrieved_at,
        )
        for raw_document in raw_documents
    ]
