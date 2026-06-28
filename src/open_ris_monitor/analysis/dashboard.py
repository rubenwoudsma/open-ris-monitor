from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from open_ris_monitor.exporters.json_exporter import write_json


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


def _year(value: Any) -> str | None:
    raw = _pick(value)
    if not raw:
        return None
    parsed = _parse_datetime(raw)
    if parsed:
        return str(parsed.year)
    if len(raw) >= 4 and raw[:4].isdigit():
        return raw[:4]
    return None


def _count_by_year(rows: list[dict[str, Any]], *date_keys: str) -> list[dict[str, Any]]:
    counter: Counter[str] = Counter()
    for row in rows:
        year = None
        for key in date_keys:
            year = _year(row.get(key))
            if year:
                break
        if year:
            counter[year] += 1
    return [{"year": year, "count": counter[year]} for year in sorted(counter)]


def _document_type(row: dict[str, Any]) -> str:
    return _pick(
        row.get("normalized_document_type_label"),
        row.get("document_type_label"),
        row.get("document_type"),
        row.get("normalized_document_type"),
        "Onbekend",
    )


def _documents_by_type(documents: list[dict[str, Any]], limit: int = 12) -> list[dict[str, Any]]:
    counter: Counter[str] = Counter(_document_type(row) for row in documents)
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


def _document_size(row: dict[str, Any]) -> int | None:
    return _as_int(_pick(row.get("file_size_bytes"), row.get("size_bytes"), row.get("file_size")))


def _document_size_summary(documents: list[dict[str, Any]]) -> dict[str, Any]:
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


def _document_size_buckets(documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
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


def _document_identifiers(document: dict[str, Any]) -> set[str]:
    identifiers = {
        _pick(document.get("id")),
        _pick(document.get("source_id")),
        _pick(document.get("source_object_id")),
        _pick(document.get("download_url")),
        _pick(document.get("source_url")),
    }
    raw = document.get("raw")
    if isinstance(raw, dict):
        identifiers.update(
            {
                _pick(raw.get("id")),
                _pick(raw.get("objectId")),
                _pick(raw.get("object_id")),
                _pick(raw.get("downloadUrl")),
                _pick(raw.get("download_url")),
            }
        )
    return {identifier for identifier in identifiers if identifier}


def _relation_document_identifiers(relation: dict[str, Any]) -> set[str]:
    identifiers = {
        _pick(relation.get("document_id")),
        _pick(relation.get("document_source_id")),
        _pick(relation.get("document_object_id")),
        _pick(relation.get("document_url")),
        _pick(relation.get("download_url")),
        _pick(relation.get("source_url")),
    }
    document = relation.get("document")
    if isinstance(document, dict):
        identifiers.update(
            {
                _pick(document.get("id")),
                _pick(document.get("objectId")),
                _pick(document.get("object_id")),
                _pick(document.get("downloadUrl")),
                _pick(document.get("download_url")),
            }
        )
    return {identifier for identifier in identifiers if identifier}


def _document_identifier_groups(document: dict[str, Any]) -> dict[str, set[str]]:
    raw = document.get("raw")
    raw_values = raw if isinstance(raw, dict) else {}
    return {
        "id": {_pick(document.get("id"))},
        "source_id": {_pick(document.get("source_id")), _pick(raw_values.get("id"))},
        "object_id": {
            _pick(document.get("source_object_id")),
            _pick(raw_values.get("objectId")),
            _pick(raw_values.get("object_id")),
        },
        "url": {
            _pick(document.get("download_url")),
            _pick(document.get("source_url")),
            _pick(raw_values.get("downloadUrl")),
            _pick(raw_values.get("download_url")),
        },
    }


def _relation_document_identifier_groups(relation: dict[str, Any]) -> dict[str, set[str]]:
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


def _has_typed_identifier_overlap(document: dict[str, Any], relation_groups: dict[str, set[str]]) -> bool:
    document_groups = _clean_identifier_groups(_document_identifier_groups(document))
    return any(document_groups.get(key, set()) & relation_groups.get(key, set()) for key in relation_groups)


def _linked_document_count(
    documents: list[dict[str, Any]],
    meeting_documents: list[dict[str, Any]],
    meeting_item_documents: list[dict[str, Any]],
) -> int:
    relation_groups = {"id": set(), "source_id": set(), "object_id": set(), "url": set()}
    for relation in [*meeting_documents, *meeting_item_documents]:
        for key, values in _clean_identifier_groups(_relation_document_identifier_groups(relation)).items():
            relation_groups.setdefault(key, set()).update(values)

    return sum(1 for document in documents if _has_typed_identifier_overlap(document, relation_groups))


def _count_meeting_items_by_year(
    meeting_items: list[dict[str, Any]],
    meetings: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    meeting_year_by_id: dict[str, str] = {}
    for meeting in meetings:
        year = _year(_pick(meeting.get("date"), meeting.get("start_date"), meeting.get("publication_date")))
        if not year:
            continue
        for identifier in (_pick(meeting.get("id")), _pick(meeting.get("source_id"))):
            if identifier:
                meeting_year_by_id[identifier] = year

    counter: Counter[str] = Counter()
    for item in meeting_items:
        year = None
        for key in ("meeting_date", "date", "created_at"):
            year = _year(item.get(key))
            if year:
                break
        if not year:
            year = meeting_year_by_id.get(_pick(item.get("meeting_id"))) or meeting_year_by_id.get(_pick(item.get("meeting_source_id")))
        if year:
            counter[year] += 1
    return [{"year": year, "count": counter[year]} for year in sorted(counter)]


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
    documents = read_jsonl_optional(public_dir / "documents.jsonl")
    document_versions = read_jsonl_optional(public_dir / "document_versions.jsonl")
    meetings = read_jsonl_optional(public_dir / "meetings.jsonl")
    meeting_items = read_jsonl_optional(public_dir / "meeting_items.jsonl")
    meeting_documents = read_jsonl_optional(public_dir / "meeting_documents.jsonl")
    meeting_item_documents = read_jsonl_optional(public_dir / "meeting_item_documents.jsonl")
    groups = read_jsonl_optional(public_dir / "organization_groups.jsonl")
    persons = read_jsonl_optional(public_dir / "organization_persons.jsonl")
    roles = read_jsonl_optional(public_dir / "organization_roles.jsonl")
    positions = read_jsonl_optional(public_dir / "organization_positions.jsonl")

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
        "documents_by_year": _count_by_year(
            documents,
            "publication_datetime",
            "date_published",
            "publication_date",
            "document_date",
            "date",
            "retrieved_at",
        ),
        "documents_by_type": _documents_by_type(documents),
        "documents_by_size_bucket": _document_size_buckets(documents),
        "meetings_by_year": _count_by_year(meetings, "date", "start_date", "publication_date"),
        "meeting_items_by_year": _count_meeting_items_by_year(meeting_items, meetings),
    }


def write_dashboard_summary(public_dir: Path) -> dict[str, Any]:
    dashboard = build_dashboard_summary(public_dir)
    output_path = public_dir / "quality" / "dashboard.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(output_path, dashboard)
    return dashboard
