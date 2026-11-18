"""Normalization functions for the GemeenteOplossingen connector."""

from __future__ import annotations

from datetime import date, datetime, timezone
from html import unescape
import re
from typing import Any

from open_ris_monitor.models import Document, Meeting, MeetingItem
from open_ris_monitor.models.relations import (
    MeetingDocumentRelation,
    MeetingItemDocumentRelation,
)
from open_ris_monitor.normalizers.document_types import (
    normalize_document_type as normalize_type_details,
)

_TAG_RE = re.compile(r"<[^>]+>")
_WHITESPACE_RE = re.compile(r"\s+")


def _as_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _as_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "ja"}
    return bool(value)


def _parse_datetime_optional(value: Any) -> datetime | None:
    """Safely parse a string into a timezone-aware datetime."""
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None

    normalized = text.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except (TypeError, ValueError):
        return None

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _parse_date_optional(value: Any) -> date | None:
    """Safely parse a string into a date object."""
    text = _as_text(value)
    if not text:
        return None

    # Handle full datetimes by taking the date part
    if "T" in text or " " in text:
        text = text.split("T")[0].split(" ")[0]

    try:
        return date.fromisoformat(text)
    except (TypeError, ValueError):
        return None


def _strip_html(value: Any) -> str | None:
    """Remove HTML tags and clean up whitespace."""
    text = _as_text(value)
    if text is None:
        return None
    text = unescape(_TAG_RE.sub(" ", text))
    text = _WHITESPACE_RE.sub(" ", text).strip()
    return text or None


def normalize_document(
    raw_record: dict[str, Any],
    *,
    municipality_slug: str,
    retrieved_at: datetime,
    base_url: str,
) -> Document:
    """Map a raw GemeenteOplossingen document record to the canonical Document model."""
    source_id = str(raw_record["id"])
    source_object_id = str(raw_record["objectId"]) if raw_record.get("objectId") else None

    # The canonical ID is a stable, unique identifier for the document across all sources.
    canonical_id = f"doc:{municipality_slug}:gemeenteoplossingen:{source_id}"
    if source_object_id:
        canonical_id += f":{source_object_id}"

    source_type = raw_record.get("documentTypeLabel")
    normalized_type = normalize_type_details(source_type)

    # The source API provides a relative download path.
    download_path = raw_record.get("downloadUrl")
    download_url = (
        f"{base_url.rstrip('/')}/{download_path.lstrip('/')}" if base_url and download_path else None
    )

    return Document(
        id=canonical_id,
        municipality_slug=municipality_slug,
        source_id=source_id,
        source_object_id=source_object_id,
        title=raw_record.get("description"),
        description=raw_record.get("description"),
        document_type=source_type,
        publication_datetime=_parse_datetime_optional(raw_record.get("publicationDate")),
        is_confidential=raw_record.get("confidential", False),
        filename=raw_record.get("fileName"),
        file_size_bytes=raw_record.get("fileSize"),
        download_url=download_url,
        # The source URL (to the web page) is often not in the API record itself
        # and would be constructed based on known URL patterns if needed.
        source_url=None,
        normalized_document_type=normalized_type.value,
        normalized_document_type_label=normalized_type.label,
        retrieved_at=retrieved_at,
        raw=raw_record,
    )


def normalize_meeting_document_relation(
    raw_record: dict[str, Any],
    *,
    municipality_slug: str,
    source_system_id: str,
) -> MeetingDocumentRelation:
    """Map a raw GemeenteOplossingen meeting-document relation to the canonical model."""
    meeting_source_id = _as_text(raw_record.get("meeting_id"))
    if not meeting_source_id:
        raise ValueError("Relation is missing a parent meeting reference.")

    doc_data = raw_record.get("document")
    if not isinstance(doc_data, dict):
        raise ValueError("Relation is missing the nested document object.")

    doc_source_id = _as_text(doc_data.get("id"))
    if not doc_source_id:
        raise ValueError("Relation's nested document is missing an 'id'.")

    meeting_id = f"meet:{municipality_slug}:{source_system_id}:{meeting_source_id}"
    doc_object_id = _as_text(doc_data.get("objectId"))
    canonical_doc_id = f"doc:{municipality_slug}:{source_system_id}:{doc_source_id}"
    if doc_object_id:
        canonical_doc_id += f":{doc_object_id}"

    return MeetingDocumentRelation(
        id=f"{meeting_id}-doc-rel-{doc_source_id}",
        meeting_id=meeting_id,
        meeting_source_id=meeting_source_id,
        document_id=canonical_doc_id,
        document_source_id=doc_source_id,
        document_object_id=doc_object_id,
        municipality_slug=municipality_slug,
        source_system_id=source_system_id,
        relation_type="meeting_document",
        source_path=f"/meetings/{meeting_source_id}/documents",
    )


def normalize_meeting_item_document_relation(
    raw_record: dict[str, Any],
    *,
    municipality_slug: str,
    source_system_id: str,
) -> MeetingItemDocumentRelation:
    """Map a raw GemeenteOplossingen meeting-item-document relation to the canonical model."""
    meeting_source_id = _as_text(raw_record.get("meeting_id"))
    item_source_id = _as_text(raw_record.get("meeting_item_id"))

    if not meeting_source_id:
        raise ValueError("Relation is missing a parent meeting reference.")
    if not item_source_id:
        raise ValueError("Relation is missing a parent meeting item reference.")

    doc_data = raw_record.get("document")
    if not isinstance(doc_data, dict):
        raise ValueError("Relation is missing the nested document object.")

    doc_source_id = _as_text(doc_data.get("id"))
    if not doc_source_id:
        raise ValueError("Relation's nested document is missing an 'id'.")

    meeting_id = f"meet:{municipality_slug}:{source_system_id}:{meeting_source_id}"
    item_id = f"item:{municipality_slug}:{source_system_id}:{item_source_id}"
    doc_object_id = _as_text(doc_data.get("objectId"))
    canonical_doc_id = f"doc:{municipality_slug}:{source_system_id}:{doc_source_id}"
    if doc_object_id:
        canonical_doc_id += f":{doc_object_id}"

    return MeetingItemDocumentRelation(
        id=f"{item_id}-doc-rel-{doc_source_id}",
        meeting_item_id=item_id,
        meeting_item_source_id=item_source_id,
        meeting_id=meeting_id,
        meeting_source_id=meeting_source_id,
        document_id=canonical_doc_id,
        document_source_id=doc_source_id,
        document_object_id=doc_object_id,
        municipality_slug=municipality_slug,
        source_system_id=source_system_id,
        relation_type="meeting_item_document",
        source_path=f"/meetingitems/{item_source_id}/documents",
    )


def normalize_meeting_item(
    raw_record: dict[str, Any],
    *,
    municipality_slug: str,
    source_system_id: str,
    retrieved_at: datetime,
) -> MeetingItem:
    """Map a raw GemeenteOplossingen meeting item record to the canonical MeetingItem model."""
    source_id = str(raw_record["id"])

    meeting_source_id = (
        _as_text(raw_record.get("meeting_id"))
        or _as_text(raw_record.get("meetingId"))
        or _as_text(raw_record.get("meeting_source_id"))
        or _as_text(raw_record.get("meeting", {}).get("id"))
        or _as_text(raw_record.get("meeting", {}).get("source_id"))
    )
    if not meeting_source_id:
        raise ValueError(f"Meeting item with source_id '{source_id}' is missing a parent meeting reference.")

    canonical_id = f"item:{municipality_slug}:{source_system_id}:{source_id}"
    meeting_id = f"meet:{municipality_slug}:{source_system_id}:{meeting_source_id}"

    return MeetingItem(
        id=canonical_id,
        municipality_slug=municipality_slug,
        source_system_id=source_system_id,
        source_id=source_id,
        meeting_id=meeting_id,
        meeting_source_id=meeting_source_id,
        number=_as_text(raw_record.get("number")),
        sort_order=_as_int(raw_record.get("sort_order")) or _as_int(raw_record.get("sortOrder")),
        title=_strip_html(raw_record.get("title")) or _strip_html(raw_record.get("description")),
        is_heading=_as_bool(raw_record.get("is_heading") or raw_record.get("isHeading")),
        is_confidential=_as_bool(
            raw_record.get("is_confidential") or raw_record.get("confidential")
        ),
        retrieved_at=retrieved_at,
        raw=raw_record,
    )


def normalize_meeting(
    raw_record: dict[str, Any],
    *,
    municipality_slug: str,
    source_system_id: str,
    retrieved_at: datetime,
) -> Meeting:
    """Map a raw GemeenteOplossingen meeting record to the canonical Meeting model."""
    source_id = str(raw_record["id"])
    canonical_id = f"meet:{municipality_slug}:{source_system_id}:{source_id}"

    dmu = raw_record.get("dmu") if isinstance(raw_record.get("dmu"), dict) else {}

    return Meeting(
        id=canonical_id,
        municipality_slug=municipality_slug,
        source_system_id=source_system_id,
        source_id=source_id,
        title=_strip_html(raw_record.get("description")),
        date=_parse_date_optional(raw_record.get("date")),
        start_time=_as_text(raw_record.get("startTime") or raw_record.get("start_time")),
        location=_as_text(raw_record.get("location")),
        url=_as_text(raw_record.get("url")),
        is_confidential=raw_record.get("confidential", False)
        or raw_record.get("is_confidential", False),
        dmu_id=_as_text(dmu.get("id") or raw_record.get("dmuId") or raw_record.get("dmu_id")),
        dmu_name=_as_text(
            dmu.get("name") or raw_record.get("dmuName") or raw_record.get("dmu_name")
        ),
        dmu_sort_order=dmu.get("sortOrder")
        or raw_record.get("dmuSortOrder")
        or raw_record.get("dmu_sort_order"),
        retrieved_at=retrieved_at,
        raw=raw_record,
    )


def normalize_documents(
    raw_records: list[dict[str, Any]],
    *,
    municipality_slug: str,
    retrieved_at: datetime,
    base_url: str,
    **kwargs,  # absorb unused legacy arguments
) -> list[Document]:
    """Map a list of raw document records to a list of canonical Document models."""
    records: list[Document] = []
    for raw in raw_records:
        try:
            record = normalize_document(
                raw,
                municipality_slug=municipality_slug,
                retrieved_at=retrieved_at,
                base_url=base_url,
            )
            records.append(record)
        except Exception as exc:
            source_id = raw.get("id", "unknown")
            print(f"WARNING: Skipping document record with source_id '{source_id}' due to normalization error: {exc}")
    return records