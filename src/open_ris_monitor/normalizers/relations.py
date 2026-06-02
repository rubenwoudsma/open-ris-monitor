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


def _stable_unique(records: Iterable[T], key_fn) -> list[T]:
    seen: set[str] = set()
    result: list[T] = []
    for record in records:
        key = key_fn(record)
        if key in seen:
            continue
        seen.add(key)
        result.append(record)
    return result


def _canonical_id(municipality_slug: str, resource_type: str, source_id: str) -> str:
    return f"{municipality_slug}-{resource_type}-{source_id}"


def _document_source_id(document: dict[str, Any]) -> str | None:
    return _as_text(document.get("id"))


def _document_object_id(document: dict[str, Any]) -> str | None:
    return _as_text(document.get("objectId")) or _as_text(document.get("object_id"))


def _meeting_source_id_from_item(raw: dict[str, Any]) -> str | None:
    direct = _as_text(raw.get("meeting_id"))
    if direct is not None:
        return direct

    meeting = raw.get("meeting")
    if isinstance(meeting, dict):
        return _as_text(meeting.get("id"))

    return None


def normalize_meeting(
    raw: dict[str, Any],
    *,
    municipality_slug: str,
    source_system_id: str,
) -> Meeting | None:
    """Normalize one raw meeting record.

    Records without source ID are skipped by returning None.
    """

    source_id = _as_text(raw.get("id"))
    if source_id is None:
        return None

    dmu = raw.get("dmu")
    if not isinstance(dmu, dict):
        dmu = {}

    return Meeting(
        id=_canonical_id(municipality_slug, "meeting", source_id),
        source_id=source_id,
        municipality_slug=municipality_slug,
        source_system_id=source_system_id,
        date=_as_text(raw.get("date")),
        start_time=_as_text(raw.get("startTime")) or _as_text(raw.get("start_time")),
        description=_strip_html(raw.get("description")),
        location=_as_text(raw.get("location")),
        dmu_id=_as_text(dmu.get("id")),
        dmu_name=_as_text(dmu.get("name")),
        dmu_sort_order=_as_int(dmu.get("sortOrder")),
        url=_as_text(raw.get("url")),
        is_confidential=_as_bool(raw.get("confidential")),
    )


def normalize_meetings(
    raw_meetings: Iterable[dict[str, Any]],
    *,
    municipality_slug: str,
    source_system_id: str,
) -> list[Meeting]:
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
    return _stable_unique(records, lambda record: record.id)


def normalize_meeting_item(
    raw: dict[str, Any],
    *,
    municipality_slug: str,
    source_system_id: str,
) -> MeetingItem | None:
    """Normalize one raw meeting item record."""

    source_id = _as_text(raw.get("id"))
    meeting_source_id = _meeting_source_id_from_item(raw)
    if source_id is None or meeting_source_id is None:
        return None

    status = raw.get("status")
    if not isinstance(status, dict):
        status = {}

    return MeetingItem(
        id=_canonical_id(municipality_slug, "meeting-item", source_id),
        source_id=source_id,
        meeting_id=_canonical_id(municipality_slug, "meeting", meeting_source_id),
        meeting_source_id=meeting_source_id,
        municipality_slug=municipality_slug,
        source_system_id=source_system_id,
        number=_as_text(raw.get("number")),
        sort_order=_as_int(raw.get("sortOrder")) or _as_int(raw.get("sort_order")),
        title=_strip_html(raw.get("title")),
        description=_strip_html(raw.get("description")),
        status_id=_as_text(status.get("id")),
        status_description=_strip_html(status.get("description")),
        status_abbreviation=_as_text(status.get("abbreviation")),
        is_heading=_as_bool(raw.get("isHeading") or raw.get("is_heading")),
        is_confidential=_as_bool(raw.get("confidential")),
    )


def normalize_meeting_items(
    raw_items: Iterable[dict[str, Any]],
    *,
    municipality_slug: str,
    source_system_id: str,
) -> list[MeetingItem]:
    records = [
        record
        for raw in raw_items
        if (
            record := normalize_meeting_item(
                raw,
                municipality_slug=municipality_slug,
                source_system_id=source_system_id,
            )
        )
        is not None
    ]
    return _stable_unique(records, lambda record: record.id)


def normalize_meeting_document_relation(
    raw: dict[str, Any],
    *,
    municipality_slug: str,
    source_system_id: str,
) -> MeetingDocumentRelation | None:
    """Normalize one meeting-document relation from the raw harvest shape."""

    meeting_source_id = _as_text(raw.get("meeting_id"))
    document = raw.get("document")
    if not isinstance(document, dict):
        document = {}
    document_source_id = _document_source_id(document)

    if meeting_source_id is None or document_source_id is None:
        return None

    meeting_id = _canonical_id(municipality_slug, "meeting", meeting_source_id)
    document_id = _canonical_id(municipality_slug, "document", document_source_id)

    return MeetingDocumentRelation(
        id=f"{meeting_id}-document-{document_source_id}",
        meeting_id=meeting_id,
        meeting_source_id=meeting_source_id,
        document_id=document_id,
        document_source_id=document_source_id,
        document_object_id=_document_object_id(document),
        municipality_slug=municipality_slug,
        source_system_id=source_system_id,
        relation_type="meeting_document",
        source_path=f"/meetings/{meeting_source_id}/documents",
    )


def normalize_meeting_document_relations(
    raw_relations: Iterable[dict[str, Any]],
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


def normalize_meeting_item_document_relation(
    raw: dict[str, Any],
    *,
    municipality_slug: str,
    source_system_id: str,
) -> MeetingItemDocumentRelation | None:
    """Normalize one meeting-item-document relation from the raw harvest shape."""

    meeting_source_id = _as_text(raw.get("meeting_id"))
    meeting_item_source_id = _as_text(raw.get("meeting_item_id"))
    document = raw.get("document")
    if not isinstance(document, dict):
        document = {}
    document_source_id = _document_source_id(document)

    if meeting_source_id is None or meeting_item_source_id is None or document_source_id is None:
        return None

    meeting_id = _canonical_id(municipality_slug, "meeting", meeting_source_id)
    meeting_item_id = _canonical_id(municipality_slug, "meeting-item", meeting_item_source_id)
    document_id = _canonical_id(municipality_slug, "document", document_source_id)

    return MeetingItemDocumentRelation(
        id=f"{meeting_item_id}-document-{document_source_id}",
        meeting_item_id=meeting_item_id,
        meeting_item_source_id=meeting_item_source_id,
        meeting_id=meeting_id,
        meeting_source_id=meeting_source_id,
        document_id=document_id,
        document_source_id=document_source_id,
        document_object_id=_document_object_id(document),
        municipality_slug=municipality_slug,
        source_system_id=source_system_id,
        relation_type="meeting_item_document",
        source_path=f"/meetingitems/{meeting_item_source_id}/documents",
    )


def normalize_meeting_item_document_relations(
    raw_relations: Iterable[dict[str, Any]],
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
