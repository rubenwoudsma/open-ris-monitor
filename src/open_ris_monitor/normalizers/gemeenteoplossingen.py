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
    if build_download_url is not None:
        return build_download_url
    if connector is not None and hasattr(connector, "build_download_url"):
        return connector.build_document_download_url
    return lambda source_id: f"https://mock-download-url/api/v2/documents/{source_id}/download"


def _as_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _first_text(raw: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = _as_text(raw.get(key))
        if value:
            return value
    return None


def _nested_mapping(raw: dict[str, Any], key: str) -> dict[str, Any]:
    value = raw.get(key)
    return value if isinstance(value, dict) else {}


def _nested_first_text(raw: dict[str, Any], object_key: str, *keys: str) -> str | None:
    nested = _nested_mapping(raw, object_key)
    return _first_text(nested, *keys) if nested else None


def _as_positive_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed >= 0 else None


def _resolve_file_size(raw_document: dict[str, Any]) -> int | None:
    """Return file size from known GemeenteOplossingen field variants."""
    for value in (
        raw_document.get("fileSize"),
        raw_document.get("file_size"),
        raw_document.get("file_size_bytes"),
        raw_document.get("sizeBytes"),
        raw_document.get("size_bytes"),
        raw_document.get("filesize"),
        raw_document.get("size"),
        raw_document.get("bytes"),
        _nested_mapping(raw_document, "file").get("fileSize"),
        _nested_mapping(raw_document, "file").get("size"),
        _nested_mapping(raw_document, "file").get("bytes"),
        _nested_mapping(raw_document, "attachment").get("fileSize"),
        _nested_mapping(raw_document, "attachment").get("size"),
    ):
        parsed = _as_positive_int(value)
        if parsed is not None:
            return parsed
    return None


def _resolve_source_document_type(raw_document: dict[str, Any]) -> str | None:
    """Return the most descriptive source document type value available."""
    direct = _first_text(
        raw_document,
        "documentTypeLabel",
        "document_type_label",
        "documentTypeDescription",
        "document_type_description",
        "documentTypeName",
        "document_type_name",
        "documentType",
        "document_type",
        "typeLabel",
        "type_label",
        "type",
    )
    if direct:
        return direct
    for object_key in ("documentType", "document_type", "type"):
        nested = _nested_first_text(
            raw_document,
            object_key,
            "label",
            "description",
            "name",
            "title",
            "value",
            "id",
        )
        if nested:
            return nested
    return None


def _resolve_document_url(
    raw_document: dict[str, Any],
    *,
    source_id: str,
    url_builder: Callable[[str], str],
) -> str:
    """Return a usable public document URL, falling back to the download endpoint."""
    explicit = (
        _first_text(
            raw_document,
            "downloadUrl",
            "download_url",
            "sourceUrl",
            "source_url",
            "fileUrl",
            "file_url",
            "documentUrl",
            "document_url",
            "webUrl",
            "web_url",
            "url",
        )
        or _nested_first_text(raw_document, "file", "downloadUrl", "download_url", "url", "href")
        or _nested_first_text(raw_document, "attachment", "downloadUrl", "download_url", "url", "href")
    )
    return explicit or url_builder(source_id)


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
    """Normalize a raw GemeenteOplossingen document into a Canonical Document."""
    source_id = str(raw_document.get("id") or raw_document.get("source_id") or "")
    if not municipality_slug:
        municipality_slug = _slugify(municipality_id)

    url_builder = _resolve_download_url_builder(
        connector=connector,
        build_download_url=build_download_url,
    )
    document_url = _resolve_document_url(raw_document, source_id=source_id, url_builder=url_builder)

    publication_datetime, publication_timezone = _parse_publication_datetime(
        raw_document.get("publicationDate") or raw_document.get("publication_date")
    )

    title_value = raw_document.get("title") or raw_document.get("description") or ""
    description_value = raw_document.get("description")

    source_document_type = _resolve_source_document_type(raw_document)
    normalized_type = normalize_document_type(source_document_type)

    source_obj_id = raw_document.get("objectId") or raw_document.get("source_object_id")
    source_object_id_str = str(source_obj_id) if source_obj_id is not None else None

    return Document(
        id=f"{municipality_slug}-document-{source_id}",
        schema_version="1.0.0",
        municipality_id=municipality_id,
        source_system_id=source_system_id,
        source_id=source_id,
        source_object_id=source_object_id_str,
        title=str(title_value).strip(),
        description=str(description_value).strip() if description_value else None,
        document_type=str(source_document_type).strip() if source_document_type else None,
        normalized_document_type=normalized_type.value,
        normalized_document_type_label=normalized_type.label,
        filename=(
            raw_document.get("fileName")
            or raw_document.get("filename")
            or raw_document.get("file_name")
            or _nested_mapping(raw_document, "file").get("fileName")
            or _nested_mapping(raw_document, "file").get("name")
        ),
        file_size_bytes=_resolve_file_size(raw_document),
        publication_datetime=publication_datetime,
        publication_timezone=publication_timezone,
        is_confidential=bool(raw_document.get("confidential") or raw_document.get("is_confidential")),
        is_tabsign_document=bool(raw_document.get("isTabsignDocument") or raw_document.get("is_tabsign_document")),
        source_url=document_url,
        download_url=document_url,
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
        if raw_document.get("id") is not None or raw_document.get("source_id") is not None
    ]
