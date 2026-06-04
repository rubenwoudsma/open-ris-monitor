from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if not path.exists():
        raise FileNotFoundError(f"JSONL file not found: {path}")

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


def _latest_harvest(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not rows:
        return None

    def sort_key(row: dict[str, Any]) -> tuple[str, str]:
        started = str(row.get("started_at") or row.get("finished_at") or "")
        identifier = str(row.get("id") or "")
        return started, identifier

    return sorted(rows, key=sort_key)[-1]


def _collect_ids(rows: list[dict[str, Any]], key: str) -> set[str]:
    values: set[str] = set()
    for row in rows:
        value = row.get(key)
        if isinstance(value, str) and value:
            values.add(value)
    return values


def build_quality_report(public_dir: Path) -> dict[str, Any]:
    documents = read_jsonl(public_dir / "documents.jsonl")
    document_versions = read_jsonl(public_dir / "document_versions.jsonl") if (public_dir / "document_versions.jsonl").exists() else []
    harvest_runs = read_jsonl(public_dir / "harvest_runs.jsonl") if (public_dir / "harvest_runs.jsonl").exists() else []
    meetings = read_jsonl(public_dir / "meetings.jsonl") if (public_dir / "meetings.jsonl").exists() else []
    meeting_items = read_jsonl(public_dir / "meeting_items.jsonl") if (public_dir / "meeting_items.jsonl").exists() else []
    meeting_documents = read_jsonl(public_dir / "meeting_documents.jsonl") if (public_dir / "meeting_documents.jsonl").exists() else []
    meeting_item_documents = read_jsonl(public_dir / "meeting_item_documents.jsonl") if (public_dir / "meeting_item_documents.jsonl").exists() else []

    document_ids = _collect_ids(documents, "id")
    meeting_ids = _collect_ids(meetings, "id")
    meeting_item_ids = _collect_ids(meeting_items, "id")

    related_document_ids: set[str] = set()
    for rel in meeting_documents:
        value = rel.get("document_id")
        if isinstance(value, str) and value:
            related_document_ids.add(value)

    for rel in meeting_item_documents:
        value = rel.get("document_id")
        if isinstance(value, str) and value:
            related_document_ids.add(value)

    orphan_meeting_document_relations = sum(
        1
        for rel in meeting_documents
        if rel.get("meeting_id") not in meeting_ids or rel.get("document_id") not in document_ids
    )
    orphan_meeting_item_document_relations = sum(
        1
        for rel in meeting_item_documents
        if rel.get("meeting_item_id") not in meeting_item_ids or rel.get("document_id") not in document_ids
    )

    meetings_with_items: defaultdict[str, int] = defaultdict(int)
    items_with_documents: defaultdict[str, int] = defaultdict(int)

    for item in meeting_items:
        meeting_id = item.get("meeting_id")
        if isinstance(meeting_id, str) and meeting_id:
            meetings_with_items[meeting_id] += 1

    for rel in meeting_item_documents:
        item_id = rel.get("meeting_item_id")
        if isinstance(item_id, str) and item_id:
            items_with_documents[item_id] += 1

    meetings_without_items = sum(1 for meeting in meetings if meetings_with_items.get(meeting.get("id"), 0) == 0)
    items_without_documents = sum(1 for item in meeting_items if items_with_documents.get(item.get("id"), 0) == 0)

    source_document_type_counter: Counter[str] = Counter()
    normalized_document_type_counter: Counter[str] = Counter()

    for doc in documents:
        source_type = doc.get("document_type")
        normalized_type = doc.get("normalized_document_type")

        if isinstance(source_type, str) and source_type:
            source_document_type_counter[source_type] += 1
        if isinstance(normalized_type, str) and normalized_type:
            normalized_document_type_counter[normalized_type] += 1
        else:
            normalized_document_type_counter["unknown"] += 1

    unknown_document_types = normalized_document_type_counter.get("unknown", 0)
    latest_run = _latest_harvest(harvest_runs)

    issues: list[dict[str, Any]] = []
    if orphan_meeting_document_relations:
        issues.append(
            {
                "severity": "warning",
                "code": "orphan_meeting_document_relations",
                "count": orphan_meeting_document_relations,
                "message": "Meeting-document relations reference missing records.",
            }
        )
    if orphan_meeting_item_document_relations:
        issues.append(
            {
                "severity": "warning",
                "code": "orphan_meeting_item_document_relations",
                "count": orphan_meeting_item_document_relations,
                "message": "Meeting-item-document relations reference missing records.",
            }
        )
    if unknown_document_types:
        issues.append(
            {
                "severity": "info",
                "code": "unknown_document_types",
                "count": unknown_document_types,
                "message": "Some documents are not mapped to a normalized document type.",
            }
        )
    if latest_run and latest_run.get("status") not in (None, "success"):
        issues.append(
            {
                "severity": "warning",
                "code": "latest_harvest_status",
                "count": 1,
                "message": f"The latest harvest status is {latest_run.get('status')}.",
            }
        )

    total_documents = len(documents)
    documents_with_relations = len(related_document_ids)
    coverage_pct = round((documents_with_relations / total_documents) * 100, 2) if total_documents else 0.0

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "counts": {
            "documents": len(documents),
            "document_versions": len(document_versions),
            "harvest_runs": len(harvest_runs),
            "meetings": len(meetings),
            "meeting_items": len(meeting_items),
            "meeting_documents": len(meeting_documents),
            "meeting_item_documents": len(meeting_item_documents),
        },
        "coverage": {
            "documents_with_relations": documents_with_relations,
            "documents_without_relations": max(total_documents - documents_with_relations, 0),
            "coverage_pct": coverage_pct,
        },
        "integrity": {
            "orphan_meeting_document_relations": orphan_meeting_document_relations,
            "orphan_meeting_item_document_relations": orphan_meeting_item_document_relations,
        },
        "activity": {
            "meetings_without_items": meetings_without_items,
            "items_without_documents": items_without_documents,
        },
        "document_types": {
            "source": dict(sorted(source_document_type_counter.items())),
            "normalized": dict(sorted(normalized_document_type_counter.items())),
            "unknown_count": unknown_document_types,
        },
        "harvest": {
            "latest_run_status": (latest_run or {}).get("status"),
            "latest_run": latest_run or {},
        },
        "issues": issues,
    }


def write_quality_report(public_dir: Path) -> dict[str, Any]:
    summary = build_quality_report(public_dir)
    output_dir = public_dir / "quality"
    output_dir.mkdir(parents=True, exist_ok=True)

    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    with (output_dir / "issues.jsonl").open("w", encoding="utf-8") as fh:
        for issue in summary["issues"]:
            fh.write(json.dumps(issue, ensure_ascii=False) + "\n")

    return summary
