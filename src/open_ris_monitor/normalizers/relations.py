"""Normalizers for meeting, meeting-item and document relation records."""

from __future__ import annotations

import re
from html import unescape
from typing import Any, Iterable, TypeVar, Callable

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


def _stable_unique(records: Iterable[T], key_fn: Callable[[T], str]) -> list[T]:
    seen = set()
    result = []
    for r in records:
        k = key_fn(r)
        if k not in seen:
            seen.add(k)
            result.append(r)
    return result


def normalize_meeting(raw: dict[str, Any], *, municipality_slug: str, source_system_id: str) -> Meeting | None:
    source_id = _as_text(raw.get("id") or raw.get("source_id"))
    if not source_id:
        return None

    return Meeting(
        id=f"{municipality_slug}-meeting-{source_id}",
        source_id=source_id,
        municipality_slug=municipality_slug,
        source_system_id=source_system_id,
        title=_as_text(raw.get("displayName") or raw.get("title")),
        date=_as_text(raw.get("date")),
        start_time=_as_text(raw.get("startTime") or raw.get("start_time")),
        description=_strip_html(raw.get("description")),
        location=_as_text(raw.get("location")),
        dmu_id=_as_text(raw.get("dmuId") or raw.get("dmu_id")),
        dmu_name=_as_text(raw.get("dmuName") or raw.get("dmu_name")),
        dmu_sort_order=_as_int(raw.get("dmuSortOrder") or raw.get("dmu_sort_order")),
        url=_as_text(raw.get("url")),
        is_confidential=_as_bool(raw.get("confidential") or raw.get("is_confidential")),
    )


def normalize_meetings(raw_meetings: list[dict[str, Any]], *, municipality_slug: str, source_system_id: str) -> list[Meeting]:
    records = [
        record
        for raw in raw_meetings
        if (record := normalize_meeting(raw, municipality_slug=municipality_slug, source_system_id=source_system_id)) is not None
    ]
    return _stable_unique(records, lambda record: record.id)


def normalize_meeting_item(raw: dict[str, Any], *, municipality_slug: str, source_system_id: str) -> MeetingItem | None:
    source_id = _as_text(raw.get("id") or raw.get("source_id"))
    
    # Uitgebreide en robuuste extractie voor de gekoppelde meeting ID (inclusief geneste objecten uit de tests)
    meeting_node = raw.get("meeting") if isinstance(raw.get("meeting"), dict) else {}
    meeting_source_id = _as_text(
        raw.get("meetingId")
        or raw.get("meeting_id")
        or raw.get("meeting_source_id")
        or meeting_node.get("id")
        or meeting_node.get("source_id")
    )
    
    if not source_id or not meeting_source_id:
        return None

    if "-" in meeting_source_id:
        meeting_source_id = meeting_source_id.split("-")[-1]

    sort_order = _as_int(raw.get("sortOrder") or raw.get("sort_order"))

    return MeetingItem(
        id=f"{municipality_slug}-meeting-item-{source_id}",
        source_id=source_id,
        meeting_id=f"{municipality_slug}-meeting-{meeting_source_id}",
        meeting_source_id=meeting_source_id,
        municipality_slug=municipality_slug,
        source_system_id=source_system_id,
        title=_as_text(raw.get("title")),
        number=_as_text(raw.get("number")),
        sort_order=sort_order,
        description=_strip_html(raw.get("description")),
        status_id=_as_text(raw.get("statusId") or raw.get("status_id")),
        status_description=_as_text(raw.get("statusDescription") or raw.get("status_description")),
        status_abbreviation=_as_text(raw.get("statusAbbreviation") or raw.get("status_abbreviation")),
        is_heading=_as_bool(raw.get("explanation") or raw.get("is_heading")),
        is_confidential=_as_bool(raw.get("confidential") or raw.get("is_confidential")),
    )


def normalize_meeting_items(raw_meeting_items: list[dict[str, Any]], *, municipality_slug: str, source_system_id: str) -> list[MeetingItem]:
    records = [
        record
        for raw in raw_meeting_items
        if (record := normalize_meeting_item(raw, municipality_slug=municipality_slug, source_system_id=source_system_id)) is not None
    ]
    return _stable_unique(records, lambda record: record.id)


def normalize_meeting_document_relation(raw: dict[str, Any], *, municipality_slug: str, source_system_id: str) -> MeetingDocumentRelation | None:
    doc_node = raw.get("document") if isinstance(raw.get("document"), dict) else raw
    meeting_source_id = _as_text(raw.get("meetingId") or raw.get("meeting_id"))
    document_source_id = _as_text(doc_node.get("id") or doc_node.get("source_id") or raw.get("documentId") or raw.get("document_id"))
    
    if not meeting_source_id or not document_source_id:
        return None

    if "-" in meeting_source_id:
        meeting_source_id = meeting_source_id.split("-")[-1]
    if "-" in document_source_id:
        document_source_id = document_source_id.split("-")[-1]

    rel_id = f"{municipality_slug}-meeting-{meeting_source_id}-document-{document_source_id}"

    return MeetingDocumentRelation(
        id=rel_id,
        meeting_id=f"{municipality_slug}-meeting-{meeting_source_id}",
        meeting_source_id=meeting_source_id,
        document_id=f"{municipality_slug}-document-{document_source_id}",
        document_source_id=document_source_id,
        document_object_id=str(doc_node.get("objectId") or doc_node.get("source_object_id") or doc_node.get("document_object_id") or ""),
        municipality_slug=municipality_slug,
        source_system_id=source_system_id,
        relation_type="meeting_document",
        source_path=f"/meetings/{meeting_source_id}/documents",
    )


def normalize_meeting_document_relations(raw_relations: list[dict[str, Any]], *, municipality_slug: str, source_system_id: str) -> list[MeetingDocumentRelation]:
    records = [
        record
        for raw in raw_relations
        if (record := normalize_meeting_document_relation(raw, municipality_slug=municipality_slug, source_system_id=source_system_id)) is not None
    ]
    return _stable_unique(records, lambda record: record.id)


def normalize_meeting_item_document_relation(raw: dict[str, Any], *, municipality_slug: str, source_system_id: str) -> MeetingItemDocumentRelation | None:
    doc_node = raw.get("document") if isinstance(raw.get("document"), dict) else raw
    meeting_item_source_id = _as_text(raw.get("meetingItemId") or raw.get("meeting_item_id"))
    meeting_source_id = _as_text(raw.get("meetingId") or raw.get("meeting_id"))
    document_source_id = _as_text(doc_node.get("id") or doc_node.get("source_id") or raw.get("documentId") or raw.get("document_id"))
    
    if not meeting_item_source_id or not document_source_id or not meeting_source_id:
        return None

    if "-" in meeting_item_source_id:
        meeting_item_source_id = meeting_item_source_id.split("-")[-1]
    if "-" in meeting_source_id:
        meeting_source_id = meeting_source_id.split("-")[-1]
    if "-" in document_source_id:
        document_source_id = document_source_id.split("-")[-1]

    rel_id = f"{municipality_slug}-meeting-item-{meeting_item_source_id}-document-{document_source_id}"

    return MeetingItemDocumentRelation(
        id=rel_id,
        meeting_item_id=f"{municipality_slug}-meeting-item-{meeting_item_source_id}",
        meeting_item_source_id=meeting_item_source_id,
        meeting_id=f"{municipality_slug}-meeting-{meeting_source_id}",
        meeting_source_id=meeting_source_id,
        document_id=f"{municipality_slug}-document-{document_source_id}",
        document_source_id=document_source_id,
        document_object_id=str(doc_node.get("objectId") or doc_node.get("source_object_id") or doc_node.get("document_object_id") or ""),
        municipality_slug=municipality_slug,
        source_system_id=source_system_id,
        relation_type="meeting_item_document",
        source_path=f"/meetingitems/{meeting_item_source_id}/documents",
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
