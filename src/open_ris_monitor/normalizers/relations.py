"""Normalizers for meeting, meeting-item and document relation records."""

from __future__ import annotations

import re
from html import unescape
from typing import Any, Iterable, TypeVar
from dataclasses import dataclass, asdict

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


def _stable_unique(records: Iterable[T], key_fn: callable) -> list[T]:
    seen = set()
    result = []
    for r in records:
        k = key_fn(r)
        if k not in seen:
            seen.add(k)
            result.append(r)
    return result


def normalize_meeting(
    raw: dict[str, Any],
    *,
    municipality_slug: str,
    source_system_id: str,
) -> Meeting | None:
    """Normalize a raw meeting record."""
    source_id = _as_text(raw.get("id")) or _as_text(raw.get("source_id"))
    if not source_id:
        return None

    # Defensieve lookup voor dmu fields
    dmu_id = _as_text(raw.get("dmu_id")) or _as_text(raw.get("dmuId")) or _as_text(raw.get("dmu", {}).get("id"))
    dmu_name = _as_text(raw.get("dmu_name")) or _as_text(raw.get("dmuName")) or _as_text(raw.get("dmu", {}).get("name"))
    dmu_sort_order = _as_int(raw.get("dmu_sort_order")) or _as_int(raw.get("dmuSortOrder")) or _as_int(raw.get("dmu", {}).get("sortOrder"))

    return Meeting(
        id=f"{municipality_slug}-meeting-{source_id}",
        source_id=source_id,
        municipality_slug=municipality_slug,
        source_system_id=source_system_id,
        date=_as_text(raw.get("date")),
        start_time=_as_text(raw.get("start_time")) or _as_text(raw.get("startTime")),
        description=_strip_html(raw.get("description")),
        location=_as_text(raw.get("location")),
        dmu_id=dmu_id,
        dmu_name=dmu_name,
        dmu_sort_order=dmu_sort_order,
        url=_as_text(raw.get("url")),
        is_confidential=_as_bool(raw.get("is_confidential") or raw.get("confidential")),
    )


def normalize_meeting_item(
    raw: dict[str, Any],
    *,
    municipality_slug: str,
    source_system_id: str,
) -> MeetingItem | None:
    """Normalize a raw meeting item (agenda item)."""
    source_id = _as_text(raw.get("id")) or _as_text(raw.get("source_id"))
    if not source_id:
        return None

    # Defensieve lookup voor gekoppelde meeting_id (plat of genest)
    meeting_source_id = (
        _as_text(raw.get("meeting_id"))
        or _as_text(raw.get("meetingId"))
        or _as_text(raw.get("meeting_source_id"))
        or _as_text(raw.get("meeting", {}).get("id"))
        or _as_text(raw.get("meeting", {}).get("source_id"))
    )
    if not meeting_source_id:
        return None

    # Defensieve lookup voor status eigenschappen
    status_id = _as_text(raw.get("status_id")) or _as_text(raw.get("statusId")) or _as_text(raw.get("status", {}).get("id"))
    status_desc = _as_text(raw.get("status_description")) or _as_text(raw.get("statusDescription")) or _as_text(raw.get("status", {}).get("description"))
    status_abbr = _as_text(raw.get("status_abbreviation")) or _as_text(raw.get("statusAbbreviation")) or _as_text(raw.get("status", {}).get("abbreviation"))

    return MeetingItem(
        id=f"{municipality_slug}-meeting-item-{source_id}",
        source_id=source_id,
        meeting_id=f"{municipality_slug}-meeting-{meeting_source_id}",
        meeting_source_id=meeting_source_id,
        municipality_slug=municipality_slug,
        source_system_id=source_system_id,
        number=_as_text(raw.get("number")),
        sort_order=_as_int(raw.get("sort_order")) or _as_int(raw.get("sortOrder")),
        title=_strip_html(raw.get("title")),
        description=_strip_html(raw.get("description")),
        status_id=status_id,
        status_description=status_desc,
        status_abbreviation=status_abbr,
        is_heading=_as_bool(raw.get("is_heading") or raw.get("isHeading")),
        is_confidential=_as_bool(raw.get("is_confidential") or raw.get("confidential")),
    )


def normalize_meeting_document_relation(
    raw: dict[str, Any],
    *,
    municipality_slug: str,
    source_system_id: str,
) -> MeetingDocumentRelation | None:
    """Normalize a relation record between a meeting and a document."""
    meeting_source_id = _as_text(raw.get("meeting_id")) or _as_text(raw.get("meetingId"))
    doc_data = raw.get("document", {})
    doc_source_id = _as_text(doc_data.get("id")) or _as_text(doc_data.get("source_id"))

    if not meeting_source_id or not doc_source_id:
        return None

    meeting_id = f"{municipality_slug}-meeting-{meeting_source_id}"
    document_id = f"{municipality_slug}-document-{doc_source_id}"
    
    return MeetingDocumentRelation(
        id=f"{meeting_id}-document-{doc_source_id}",
        meeting_id=meeting_id,
        meeting_source_id=meeting_source_id,
        document_id=document_id,
        document_source_id=doc_source_id,
        document_object_id=_as_text(doc_data.get("source_object_id")) or _as_text(doc_data.get("objectId")),
        municipality_slug=municipality_slug,
        source_system_id=source_system_id,
        relation_type="meeting_document",
        source_path=f"/meetings/{meeting_source_id}/documents",
    )


def normalize_meeting_item_document_relation(
    raw: dict[str, Any],
    *,
    municipality_slug: str,
    source_system_id: str,
) -> MeetingItemDocumentRelation | None:
    """Normalize a relation record between a meeting item and a document."""
    meeting_source_id = _as_text(raw.get("meeting_id")) or _as_text(raw.get("meetingId"))
    item_source_id = _as_text(raw.get("meeting_item_id")) or _as_text(raw.get("meetingItemId"))
    doc_data = raw.get("document", {})
    doc_source_id = _as_text(doc_data.get("id")) or _as_text(doc_data.get("source_id"))

    if not meeting_source_id or not item_source_id or not doc_source_id:
        return None

    meeting_id = f"{municipality_slug}-meeting-{meeting_source_id}"
    item_id = f"{municipality_slug}-meeting-item-{item_source_id}"
    document_id = f"{municipality_slug}-document-{doc_source_id}"

    return MeetingItemDocumentRelation(
        id=f"{item_id}-document-{doc_source_id}",
        meeting_item_id=item_id,
        meeting_item_source_id=item_source_id,
        meeting_id=meeting_id,
        meeting_source_id=meeting_source_id,
        document_id=document_id,
        document_source_id=doc_source_id,
        document_object_id=_as_text(doc_data.get("source_object_id")) or _as_text(doc_data.get("objectId")),
        municipality_slug=municipality_slug,
        source_system_id=source_system_id,
        relation_type="meeting_item_document",
        source_path=f"/meetingitems/{item_source_id}/documents",
    )


def normalize_meetings(
    raw_meetings: list[dict[str, Any]],
    *,
    municipality_slug: str,
    source_system_id: str,
) -> list[Meeting]:
    """Normalize a list of raw meeting records."""
    records = [
        record
        for raw in raw_meetings
        if (
            record := normalize_meeting(
                raw,
                municipality_slug=municipality_slug,
                source_system_id=source_system_id,
            )
        )
        is not None
    ]
    # Zorg voor unieke records op basis van het stabiele ID
    return _stable_unique(records, lambda record: record.id)


def normalize_meeting_items(
    raw_meeting_items: list[dict[str, Any]],
    *,
    municipality_slug: str,
    source_system_id: str,
) -> list[MeetingItem]:
    """Normalize a list of raw meeting item records."""
    records = [
        record
        for raw in raw_meeting_items
        if (
            record := normalize_meeting_item(
                raw,
                municipality_slug=municipality_slug,
                source_system_id=source_system_id,
            )
        )
        is not None
    ]
    # Zorg voor unieke records op basis van het stabiele ID
    return _stable_unique(records, lambda record: record.id)

def normalize_meeting_document_relations(
    raw_relations: list[dict[str, Any]],
    *,
    municipality_slug: str,
    source_system_id: str,
) -> list[MeetingDocumentRelation]:
    records = [
        record
        for raw in raw_relations
        if (
            record := normalize_meeting_document_relation(
                raw,
                municipality_slug=municipality_slug,
                source_system_id=source_system_id,
            )
        )
        is not None
    ]
    return _stable_unique(records, lambda record: record.id)


def normalize_meeting_item_document_relations(
    raw_relations: list[dict[str, Any]],
    *,
    municipality_slug: str,
    source_system_id: str,
) -> list[MeetingItemDocumentRelation]:
    records = [
        record
        for raw in raw_relations
        if (
            record := normalize_meeting_item_document_relation(
                raw,
                municipality_slug=municipality_slug,
                source_system_id=source_system_id,
            )
        )
        is not None
    ]
    return _stable_unique(records, lambda record: record.id)


def normalize_relation_harvest(
    relation_harvest: dict[str, Any],
    *,
    municipality_slug: str,
    source_system_id: str,
) -> dict[str, list[Any]]:
    """Normalize the raw relation harvest returned by collect_raw_relation_harvest."""
    return {
        "meetings": normalize_meetings(
            relation_harvest.get("meetings", []),
            municipality_slug=municipality_slug,
            source_system_id=source_system_id,
        ),
        "meeting_items": normalize_meeting_items(
            relation_harvest.get("meeting_items", []),
            municipality_slug=municipality_slug,
            source_system_id=source_system_id,
        ),
        "meeting_documents": normalize_meeting_document_relations(
            relation_harvest.get("meeting_documents", []),
            municipality_slug=municipality_slug,
            source_system_id=source_system_id,
        ),
        "meeting_item_documents": normalize_meeting_item_document_relations(
            relation_harvest.get("meeting_item_documents", []),
            municipality_slug=municipality_slug,
            source_system_id=source_system_id,
        ),
    }
