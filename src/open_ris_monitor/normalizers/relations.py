"""Normalizers for meeting, meeting-item and document relation records."""

from __future__ import annotations

import re
from html import unescape
from datetime import datetime
from collections.abc import Callable, Iterable
from typing import Any, TypeVar

from open_ris_monitor.models import (
    Meeting,
    MeetingItem,
)
from open_ris_monitor.models.relations import (
    MeetingDocumentRelation,
    MeetingItemDocumentRelation,
)
from open_ris_monitor.normalizers.gemeenteoplossingen import (
    normalize_meeting as normalize_go_meeting,
    normalize_meeting_item as normalize_go_meeting_item,
    normalize_meeting_document_relation as normalize_go_meeting_document_relation,
    normalize_meeting_item_document_relation as normalize_go_meeting_item_document_relation,
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


def normalize_meetings(
    raw_meetings: list[dict[str, Any]],
    *,
    municipality_slug: str,
    source_system_id: str,
    retrieved_at: datetime,
) -> list[Meeting]:
    """Normalize a list of raw meeting records."""
    records: list[Meeting] = []
    for raw in raw_meetings:
        try:
            record = normalize_go_meeting(
                raw,
                municipality_slug=municipality_slug,
                source_system_id=source_system_id,
                retrieved_at=retrieved_at,
            )
            records.append(record)
        except Exception as exc:
            source_id = raw.get("id", "unknown")
            print(f"WARNING: Skipping meeting record with source_id '{source_id}' due to normalization error: {exc}")
    # Zorg voor unieke records op basis van het stabiele ID
    return _stable_unique(records, lambda record: record.id)


def normalize_meeting_items(
    raw_meeting_items: list[dict[str, Any]],
    *,
    municipality_slug: str,
    source_system_id: str,
    retrieved_at: datetime,
) -> list[MeetingItem]:
    """Normalize a list of raw meeting item records."""
    records: list[MeetingItem] = []
    for raw in raw_meeting_items:
        try:
            record = normalize_go_meeting_item(
                raw,
                municipality_slug=municipality_slug,
                source_system_id=source_system_id,
                retrieved_at=retrieved_at,
            )
            records.append(record)
        except Exception as exc:
            source_id = raw.get("id", "unknown")
            print(f"WARNING: Skipping meeting item record with source_id '{source_id}' due to normalization error: {exc}")
    # Zorg voor unieke records op basis van het stabiele ID
    return _stable_unique(records, lambda record: record.id)

def normalize_meeting_document_relations(
    raw_relations: list[dict[str, Any]],
    *,
    municipality_slug: str,
    source_system_id: str,
) -> list[MeetingDocumentRelation]:
    records: list[MeetingDocumentRelation] = []
    for raw in raw_relations:
        try:
            record = normalize_go_meeting_document_relation(
                raw,
                municipality_slug=municipality_slug,
                source_system_id=source_system_id,
            )
            records.append(record)
        except Exception as exc:
            meeting_id = raw.get("meeting_id", "unknown")
            doc_id = raw.get("document", {}).get("id", "unknown")
            print(
                f"WARNING: Skipping meeting-document relation for meeting '{meeting_id}' and document '{doc_id}' "
                f"due to normalization error: {exc}"
            )
    return _stable_unique(records, lambda record: record.id)


def normalize_meeting_item_document_relations(
    raw_relations: list[dict[str, Any]],
    *,
    municipality_slug: str,
    source_system_id: str,
) -> list[MeetingItemDocumentRelation]:
    records: list[MeetingItemDocumentRelation] = []
    for raw in raw_relations:
        try:
            record = normalize_go_meeting_item_document_relation(
                raw,
                municipality_slug=municipality_slug,
                source_system_id=source_system_id,
            )
            records.append(record)
        except Exception as exc:
            item_id = raw.get("meeting_item_id", "unknown")
            doc_id = raw.get("document", {}).get("id", "unknown")
            print(f"WARNING: Skipping item-document relation for item '{item_id}' and document '{doc_id}' due to normalization error: {exc}")
    return _stable_unique(records, lambda record: record.id)


def normalize_relation_harvest(
    relation_harvest: dict[str, Any],
    *,
    municipality_slug: str,
    source_system_id: str,
    retrieved_at: datetime,
) -> dict[str, list[Any]]:
    """Normalize the raw relation harvest returned by collect_raw_relation_harvest."""
    return {
        "meetings": normalize_meetings(
            relation_harvest.get("meetings", []),
            municipality_slug=municipality_slug,
            source_system_id=source_system_id,
            retrieved_at=retrieved_at,
        ),
        "meeting_items": normalize_meeting_items(
            relation_harvest.get("meeting_items", []),
            municipality_slug=municipality_slug,
            source_system_id=source_system_id,
            retrieved_at=retrieved_at,
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
