from __future__ import annotations

import json
from collections import Counter
from collections.abc import Callable
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, TypeVar

from open_ris_monitor.exporters.json_exporter import write_json
from open_ris_monitor.models import Document, Meeting, MeetingItem
from open_ris_monitor.models.organization import (
    OrganizationGroup,
    OrganizationPerson,
    OrganizationPosition,
    OrganizationRole,
)
from open_ris_monitor.models.relations import (
    MeetingDocumentRelation,
    MeetingItemDocumentRelation,
)

T = TypeVar("T")

def read_jsonl_optional(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []

    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            text = line.strip()
            if not text:
                continue
            record = json.loads(text)
            if not isinstance(record, dict):
                raise ValueError(f"Expected JSON object on line {line_number} in {path}")
            records.append(record)
    return records


def read_json_optional(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    return value if isinstance(value, dict) else {}


def _pick(*values: Any) -> str:
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return ""

def _parse_datetime(value: Any) -> datetime | None:
    raw = _pick(value)
    if not raw:
        return None
    normalized = raw.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)

def _count_by_year(records: list[T], get_date: Callable[[T], date | datetime | None]) -> list[dict[str, Any]]:
    counter: Counter[str] = Counter()
    for record in records:
        dt = get_date(record)
        if dt:
            counter[str(dt.year)] += 1
    return [{"year": year, "count": count} for year, count in sorted(counter.items())]


def _document_type(doc: Document) -> str:
    return doc.normalized_document_type_label or doc.document_type or "Onbekend"


def _documents_by_type(documents: list[Document], limit: int = 12) -> list[dict[str, Any]]:
    counter: Counter[str] = Counter(_document_type(doc) for doc in documents)
    return [
        {"document_type": document_type, "count": count}
        for document_type, count in sorted(counter.items(), key=lambda item: (-item[1], item[0].lower()))[:limit]
    ]

def _as_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        result = int(value)
    except (TypeError, ValueError):
        return None
    return result if result >= 0 else None

def _document_size(doc: Document) -> int | None:
    return doc.file_size_bytes


def _document_size_summary(documents: list[Document]) -> dict[str, Any]:
    sizes = [size for row in documents if (size := _document_size(row)) is not None]
    total = sum(sizes)
    average = round(total / len(sizes)) if sizes else 0
    largest = max(sizes) if sizes else 0
    return {
        "known_count": len(sizes),
        "unknown_count": max(len(documents) - len(sizes), 0),
        "total_bytes": total,
        "average_bytes": average,
        "largest_bytes": largest,
    }

def _document_size_buckets(documents: list[Document]) -> list[dict[str, Any]]:
    buckets = [
        ("Onbekend", None, None),
        ("0-100 KB", 0, 100 * 1024),
        ("100 KB-1 MB", 100 * 1024, 1024 * 1024),
        ("1-5 MB", 1024 * 1024, 5 * 1024 * 1024),
        ("> 5 MB", 5 * 1024 * 1024, None),
    ]
    counts = dict.fromkeys((label for label, _, _ in buckets), 0)
    for document in documents:
        size = _document_size(document)
        if size is None:
            counts["Onbekend"] += 1
            continue
        for label, lower, upper in buckets[1:]:
            if lower is not None and size < lower:
                continue
            if upper is not None and size >= upper:
                continue
            counts[label] += 1
            break
    return [{"bucket": label, "count": counts[label]} for label, _, _ in buckets]

def _document_identifier_groups(document: Document | dict[str, Any]) -> dict[str, set[str]]:
    if isinstance(document, Document):
        doc_id = document.id
        source_id = document.source_id
        source_object_id = document.source_object_id
        download_url = document.download_url
        source_url = document.source_url
        raw_values = document.raw or {}
    else:
        doc_id = _pick(document.get("id"))
        source_id = _pick(document.get("source_id"))
        source_object_id = _pick(document.get("source_object_id"))
        download_url = _pick(document.get("download_url"))
        source_url = _pick(document.get("source_url"))
        raw = document.get("raw")
        raw_values = raw if isinstance(raw, dict) else {}

    return {
        "id": {doc_id},
        "source_id": {source_id, _pick(raw_values.get("id"))},
        "object_id": {
            source_object_id,
            _pick(raw_values.get("objectId")),
            _pick(raw_values.get("object_id")),
        },
        "url": {
            download_url,
            source_url,
            _pick(raw_values.get("downloadUrl")),
            _pick(raw_values.get("download_url")),
        },
    }

def _relation_document_identifier_groups(
    relation: MeetingDocumentRelation | MeetingItemDocumentRelation | dict[str, Any]
) -> dict[str, set[str]]:
    if isinstance(relation, (MeetingDocumentRelation, MeetingItemDocumentRelation)):
        return {
            "id": {relation.document_id},
            "source_id": {relation.document_source_id},
            "object_id": {relation.document_object_id},
            "url": set(),
        }

    document = relation.get("document")
    document_values = document if isinstance(document, dict) else {}
    return {
        "id": {_pick(relation.get("document_id"))},
        "source_id": {_pick(relation.get("document_source_id")), _pick(document_values.get("id"))},
        "object_id": {
            _pick(relation.get("document_object_id")),
            _pick(document_values.get("objectId")),
            _pick(document_values.get("object_id")),
        },
        "url": {
            _pick(relation.get("document_url")),
            _pick(relation.get("download_url")),
            _pick(relation.get("source_url")),
            _pick(document_values.get("downloadUrl")),
            _pick(document_values.get("download_url")),
        },
    }

def _clean_identifier_groups(groups: dict[str, set[str]]) -> dict[str, set[str]]:
    return {key: {value for value in values if value} for key, values in groups.items()}

def _has_typed_identifier_overlap(document: Document | dict[str, Any], relation_groups: dict[str, set[str]]) -> bool:
    document_groups = _clean_identifier_groups(_document_identifier_groups(document))
    return any(document_groups.get(key, set()) & relation_groups.get(key, set()) for key in relation_groups)

def _linked_document_count(
    documents: list[Document],
    meeting_documents: list[MeetingDocumentRelation],
    meeting_item_documents: list[MeetingItemDocumentRelation],
) -> int:
    relation_groups = {"id": set(), "source_id": set(), "object_id": set(), "url": set()}
    for relation in [*meeting_documents, *meeting_item_documents]:
        for key, values in _clean_identifier_groups(_relation_document_identifier_groups(relation)).items():
            relation_groups.setdefault(key, set()).update(values)

    return sum(1 for document in documents if _has_typed_identifier_overlap(document, relation_groups))

def _count_meeting_items_by_year(
    meeting_items: list[MeetingItem],
    meetings: list[Meeting],
) -> list[dict[str, Any]]:
    meeting_year_by_id: dict[str, int] = {}
    for meeting in meetings:
        if meeting.date:
            meeting_year_by_id[meeting.id] = meeting.date.year

    counter: Counter[str] = Counter()
    for item in meeting_items:
        year = meeting_year_by_id.get(item.meeting_id)
        if year:
            counter[str(year)] += 1
    return [{"year": year, "count": count} for year, count in sorted(counter.items())]

def _freshness(generated_at: str, now: datetime) -> dict[str, Any]:
    parsed = _parse_datetime(generated_at)
    if not parsed:
        return {"generated_at": generated_at, "age_days": None, "status": "unknown"}
    age_days = max((now - parsed).days, 0)
    if age_days <= 2:
        status = "fresh"
    elif age_days <= 14:
        status = "aging"
    else:
        status = "stale"
    return {"generated_at": generated_at, "age_days": age_days, "status": status}

def build_dashboard_summary(public_dir: Path, now: datetime | None = None) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    latest = read_json_optional(public_dir / "latest.json")

    documents = [Document.model_validate(d) for d in read_jsonl_optional(public_dir / "documents.jsonl")]
    # document_versions are not yet modeled with Pydantic
    document_versions = read_jsonl_optional(public_dir / "document_versions.jsonl")
    meetings = [Meeting.model_validate(m) for m in read_jsonl_optional(public_dir / "meetings.jsonl")]
    meeting_items = [
        MeetingItem.model_validate(i) for i in read_jsonl_optional(public_dir / "meeting_items.jsonl")
    ]
    meeting_documents = [
        MeetingDocumentRelation.model_validate(r)
        for r in read_jsonl_optional(public_dir / "meeting_documents.jsonl")
    ]
    meeting_item_documents = [
        MeetingItemDocumentRelation.model_validate(r)
        for r in read_jsonl_optional(public_dir / "meeting_item_documents.jsonl")
    ]
    groups = [
        OrganizationGroup.model_validate(g) for g in read_jsonl_optional(public_dir / "organization_groups.jsonl")
    ]
    persons = [
        OrganizationPerson.model_validate(p) for p in read_jsonl_optional(public_dir / "organization_persons.jsonl")
    ]
    roles = [OrganizationRole.model_validate(r) for r in read_jsonl_optional(public_dir / "organization_roles.jsonl")]
    positions = [
        OrganizationPosition.model_validate(p) for p in read_jsonl_optional(public_dir / "organization_positions.jsonl")
    ]

    generated_at = _pick(latest.get("generated_at"), now.isoformat())
    total_documents = len(documents)
    linked_documents = _linked_document_count(documents, meeting_documents, meeting_item_documents)
    unlinked_documents = max(total_documents - linked_documents, 0)
    coverage_ratio = round(linked_documents / total_documents, 4) if total_documents else 0.0

    return {
        "schema_version": 1,
        "municipality_id": _pick(latest.get("municipality_id"), latest.get("municipality")),
        "generated_at": now.isoformat(),
        "dataset_generated_at": generated_at,
        "profile": _pick(latest.get("profile"), latest.get("harvest_profile"), latest.get("mode"), "public"),
        "totals": {
            "documents": total_documents,
            "document_versions": len(document_versions),
            "meetings": len(meetings),
            "meeting_items": len(meeting_items),
            "meeting_documents": len(meeting_documents),
            "meeting_item_documents": len(meeting_item_documents),
            "linked_documents": linked_documents,
            "unlinked_documents": unlinked_documents,
            "organization_groups": len(groups),
            "organization_persons": len(persons),
            "organization_roles": len(roles),
            "organization_positions": len(positions),
        },
        "coverage": {
            "documents_with_any_meeting_context": linked_documents,
            "documents_with_any_meeting_context_ratio": coverage_ratio,
            "documents_without_meeting_context": unlinked_documents,
        },
        "freshness": _freshness(generated_at, now),
        "document_file_size": _document_size_summary(documents),
        "documents_by_year": _count_by_year(documents, lambda doc: doc.publication_datetime),
        "documents_by_type": _documents_by_type(documents),
        "documents_by_size_bucket": _document_size_buckets(documents),
        "meetings_by_year": _count_by_year(meetings, lambda m: m.date),
        "meeting_items_by_year": _count_meeting_items_by_year(meeting_items, meetings),
    }

def write_dashboard_summary(public_dir: Path) -> dict[str, Any]:
    dashboard = build_dashboard_summary(public_dir)
    output_path = public_dir / "quality" / "dashboard.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(output_path, dashboard)
    return dashboard
