"""Normalizers for GemeenteOplossingen API records."""

from __future__ import annotations

import re
from collections.abc import Callable
from datetime import datetime
from typing import Any

from open_ris_monitor.connectors.gemeenteoplossingen import GemeenteOplossingenConnector
from open_ris_monitor.models.document import Document
from open_ris_monitor.normalizers.document_types import normalize_document_type


def _slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "unknown"


def _parse_publication_datetime(raw_value: Any) -> tuple[datetime | None, str | None]:
    """Parse the GemeenteOplossingen publicationDate object."""

    if not isinstance(raw_value, dict):
        return None, None

    date_value = raw_value.get("date")
    timezone_value = raw_value.get("timezone")
    timezone = timezone_value if isinstance(timezone_value, str) else None

    if not isinstance(date_value, str) or not date_value:
        return None, timezone

    normalized = date_value.replace(" ", "T")
    try:
        return datetime.fromisoformat(normalized), timezone
    except ValueError:
        return None, timezone


def _resolve_download_url_builder(
    *,
    connector: GemeenteOplossingenConnector | None = None,
    build_download_url: Callable[[str], str] | None = None,
) -> Callable[[str], str]:
    """Return a download URL builder from either the old or new call style."""

    if build_download_url is not None:
        return build_download_url
    if connector is not None:
        return connector.build_document_download_url
    raise ValueError("Either connector or build_download_url must be provided")


def normalize_document(
    raw_document: dict[str, Any],
    *,
    municipality_id: str,
    source_system_id: str,
    retrieved_at: datetime,
    municipality_slug: str | None = None,
    connector: GemeenteOplossingenConnector | None = None,
    build_download_url: Callable[[str], str] | None = None,
) -> Document:
    """Convert one raw GemeenteOplossingen document into a canonical Document."""

    url_builder = _resolve_download_url_builder(
        connector=connector,
        build_download_url=build_download_url,
    )
    source_id = str(raw_document["id"])
    source_object_id = raw_document.get("objectId")
    publication_datetime, publication_timezone = _parse_publication_datetime(
        raw_document.get("publicationDate")
    )
    description = raw_document.get("description")
    filename = raw_document.get("fileName")
    title = str(description or filename or f"Document {source_id}").strip()
    id_prefix = municipality_slug or municipality_id
    canonical_id = f"{_slugify(id_prefix)}-document-{source_id}"
    download_url = url_builder(source_id)
    source_document_type = raw_document.get("documentTypeLabel")
    normalized_type = normalize_document_type(
        str(source_document_type) if source_document_type is not None else None
    )

    return Document(
        id=canonical_id,
        municipality_id=municipality_id,
        source_system_id=source_system_id,
        source_id=source_id,
        source_object_id=str(source_object_id) if source_object_id is not None else None,
        title=title,
        description=str(description).strip() if description else None,
        document_type=str(source_document_type).strip() if source_document_type else None,
        normalized_document_type=normalized_type.value,
        normalized_document_type_label=normalized_type.label,
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
    retrieved_at: datetime,
    municipality_slug: str | None = None,
    connector: GemeenteOplossingenConnector | None = None,
    build_download_url: Callable[[str], str] | None = None,
) -> list[Document]:
    """Normalize a list of raw GemeenteOplossingen documents."""

    return [
        normalize_document(
            raw_document,
            municipality_id=municipality_id,
            municipality_slug=municipality_slug,
            source_system_id=source_system_id,
            connector=connector,
            build_download_url=build_download_url,
            retrieved_at=retrieved_at,
        )
        for raw_document in raw_documents
    ]
