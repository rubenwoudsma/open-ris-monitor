"""Normalizers for meeting, meeting-item and document relation records."""

from __future__ import annotations

import re
from html import unescape
from typing import Any, Iterable, TypeVar

from open_ris_monitor.models.relations import (
    Meeting,
    MeetingDocumentRelation,
    MeetingItem,
    MeetingItemDocumentRelation,
)

T = TypeVar("T")

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


def _strip_html(value: Any) -> str | None:
    text = _as_text(value)
    if text is None:
        return None
    text = unescape(_TAG_RE.sub(" ", text))
    text = _WHITESPACE_RE.sub(" ", text).strip()
    return text or None


def _stable_unique(records: Iterable[T], key_fn: lambda r: str) -> list[T]:
    seen = set()
    result = []
    for r in records:
        k = key_fn(r)
        if k not in seen:
            seen.add(k)
            result.append(r)
    return result


def normalize_meeting(raw: dict[str, Any], *, municipality_slug: str, source_system_id: str) -> Meeting | None:
    source_id = _as_text(raw.get("id"))
    if not source_id:
        return None

    return Meeting(
        id=f"{municipality_slug}-meeting-{source_id}",
        source_id=source_id,
        municipality_slug=municipality_slug,
        source_system_id=source_system_id,
        schema_version="1.0.0",
        title=_as_text(raw.get("displayName") or raw.get("title")),
        date=_as_text(raw.get("date")),
        start_time=_as_text(raw.get("startTime")),
        description=_strip_html(raw.get("description")),
        location=_as_text(raw.get("location")),
        dmu_id=_as_text(raw.get("dmuId")),
        dmu_name=_as_text(raw.get("dmuName")),
        dmu_sort_order=_as_int(raw.get("dmuSortOrder")),
        url=_as_text(raw.get("url")),
        is_confidential=_as_bool(raw.get("confidential")),
    )


def normalize_meetings(raw_meetings: list[dict[str, Any]], *, municipality_slug: str, source_system_id: str) -> list[Meeting]:
    records = [
        record
        for raw in raw_meetings
        if (record := normalize_meeting(raw, municipality_slug=municipality_slug, source_system_id=source_system_id)) is not None
    ]
    return _stable_unique(records, lambda record: record.id)


def normalize_meeting_item(raw: dict[str, Any], *, municipality_slug: str, source_system_id: str) -> MeetingItem | None:
    source_id = _as_text(raw.get("id"))
    meeting_source_id = _as_text(raw.get("meetingId"))
    if not source_id or not meeting_source_id:
        return None

    sort_order = _as_int(raw.get("sortOrder"))

    return MeetingItem(
        id=f"{municipality_slug}-meetingitem-{source_id}",
        source_id=source_id,
        meeting_id=f"{municipality_slug}-meeting-{meeting_source_id}",
        meeting_source_id=meeting_source_id,
        municipality_slug=municipality_slug,
        source_system_id=source_system_id,
        schema_version="1.0.0",
        title=_as_text(raw.get("title")),
        number=_as_text(raw.get("number")),
        sort_order=sort_order,
        sequence=sort_order,  # Direct mappen voor v1.0.0 contract
        description=_strip_html(raw.get("description")),
        status_id=_as_text(raw.get("statusId")),
        status_description=_as_text(raw.get("statusDescription")),
        status_abbreviation=_as_text(raw.get("statusAbbreviation")),
        is_heading=_as_bool(raw.get("explanation")),
        is_confidential=_as_bool(raw.get("confidential")),
    )


def normalize_meeting_items(raw_meeting_items: list[dict[str, Any]], *, municipality_slug: str, source_system_id: str) -> list[MeetingItem]:
    records = [
        record
        for raw in raw_meeting_items
        if (record := normalize_meeting_item(raw, municipality_slug=municipality_slug, source_system_id=source_system_id)) is not None
    ]
    return _stable_unique(records, lambda record: record.id)


def normalize_meeting_document_relation(raw: dict[str, Any], *, municipality_slug: str, source_system_id: str) -> MeetingDocumentRelation | None:
    meeting_source_id = _as_text(raw.get("meetingId"))
    document_source_id = _as_text(raw.get("documentId"))
    if not meeting_source_id or not document_source_id:
        return None

    m_id = f"{municipality_slug}-meeting-{meeting_source_id}"
    d_id = f"{municipality_slug}-document-{document_source_id}"
    rel_id = f"{m_id}-rel-{d_id}"

    return MeetingDocumentRelation(
        id=rel_id,
        meeting_id=m_id,
        meeting_source_id=meeting_source_id,
        document_id=d_id,
        document_source_id=document_source_id,
        municipality_slug=municipality_slug,
        source_system_id=source_system_id,
        relation_type="meeting_document",
        source_path="meetingDocuments",
        schema_version="1.0.0",
        source_id=d_id,
        target_id=m_id,
        type="document_to_meeting",
    )


def normalize_meeting_document_relations(raw_relations: list[dict[str, Any]], *, municipality_slug: str, source_system_id: str) -> list[MeetingDocumentRelation]:
    records = [
        record
        for raw in raw_relations
        if (record := normalize_meeting_document_relation(raw, municipality_slug=municipality_slug, source_system_id=source_system_id)) is not None
    ]
    return _stable_unique(records, lambda record: record.id)


def normalize_meeting_item_document_relation(raw: dict[str, Any], *, municipality_slug: str, source_system_id: str) -> MeetingItemDocumentRelation | None:
    meeting_item_source_id = _as_text(raw.get("meetingItemId"))
    meeting_source_id = _as_text(raw.get("meetingId"))
    document_source_id = _as_text(raw.get("documentId"))
    if not meeting_item_source_id or not document_source_id or not meeting_source_id:
        return None

    mi_id = f"{municipality_slug}-meetingitem-{meeting_item_source_id}"
    m_id = f"{municipality_slug}-meeting-{meeting_source_id}"
    d_id = f"{municipality_slug}-document-{document_source_id}"
    rel_id = f"{mi_id}-rel-{d_id}"

    return MeetingItemDocumentRelation(
        id=rel_id,
        meeting_item_id=mi_id,
        meeting_item_source_id=meeting_item_source_id,
        meeting_id=m_id,
        meeting_source_id=meeting_source_id,
        document_id=d_id,
        document_source_id=document_source_id,
        municipality_slug=municipality_slug,
        source_system_id=source_system_id,
        relation_type="meeting_item_document",
        source_path="meetingItemDocuments",
        schema_version="1.0.0",
        source_id=d_id,
        target_id=mi_id,
        type="document_to_agenda_item",
    )


def normalize_meeting_item_document_relations(raw_relations: list[dict[str, Any]], *, municipality_slug: str, source_system_id: str) -> list[MeetingItemDocumentRelation]:
    records = [
        record
        for raw in raw_relations
        if (record := normalize_meeting_item_document_relation(raw, municipality_slug=municipality_slug, source_system_id=source_system_id)) is not None
    ]
    return _stable_unique(records, lambda record: record.id)


def normalize_relation_harvest(relation_harvest: dict[str, Any], *, municipality_slug: str, source_system_id: str) -> dict[str, list[Any]]:
    """Normalize the raw relation harvest returned by collect_raw_relation_harvest."""
    return {
        "meetings": normalize_meetings(relation_harvest.get("meetings", []), municipality_slug=municipality_slug, source_system_id=source_system_id),
        "meeting_items": normalize_meeting_items(relation_harvest.get("meeting_items", []), municipality_slug=municipality_slug, source_system_id=source_system_id),
        "meeting_documents": normalize_meeting_document_relations(relation_harvest.get("meeting_documents", []), municipality_slug=municipality_slug, source_system_id=source_system_id),
        "meeting_item_documents": normalize_meeting_item_document_relations(relation_harvest.get("meeting_item_documents", []), municipality_slug=municipality_slug, source_system_id=source_system_id),
    }
