"""Analysis helpers for document identity and document type reporting."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any

from open_ris_monitor.normalizers.document_types import normalize_document_type


def _value(record: dict[str, Any], key: str) -> str | None:
    value = record.get(key)
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _duplicate_report(records: list[dict[str, Any]], key: str) -> dict[str, Any]:
    values = [_value(record, key) for record in records]
    present_values = [value for value in values if value is not None]
    counts = Counter(present_values)
    duplicates = [
        {"value": value, "count": count}
        for value, count in sorted(counts.items())
        if count > 1
    ]
    return {
        "unique_count": len(counts),
        "missing_count": len(values) - len(present_values),
        "duplicate_count": sum(item["count"] for item in duplicates),
        "duplicates": duplicates,
    }


def analyse_identity(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Analyse source and canonical identifiers in a document export."""

    composite_values: list[str | None] = []
    for record in records:
        source_id = _value(record, "source_id")
        source_object_id = _value(record, "source_object_id")
        composite_values.append(
            f"{source_id}:{source_object_id}"
            if source_id is not None and source_object_id is not None
            else None
        )

    composite_counts = Counter(value for value in composite_values if value is not None)
    composite_duplicates = [
        {"value": value, "count": count}
        for value, count in sorted(composite_counts.items())
        if count > 1
    ]

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "documents_total": len(records),
        "canonical_id": _duplicate_report(records, "id"),
        "source_id": _duplicate_report(records, "source_id"),
        "source_object_id": _duplicate_report(records, "source_object_id"),
        "composite_source_key": {
            "description": "source_id + source_object_id",
            "unique_count": len(composite_counts),
            "missing_count": sum(1 for value in composite_values if value is None),
            "duplicate_count": sum(item["count"] for item in composite_duplicates),
            "duplicates": composite_duplicates,
        },
        "recommended_identity_key": "municipality_id + source_system_id + source_id + source_object_id",
        "notes": [
            "This report only analyses the current public export snapshot.",
            "Longitudinal stability requires comparing multiple harvest outputs over time.",
            "The original RIS identifiers remain source values; the canonical id should stay stable and traceable.",
        ],
    }


def analyse_document_types(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Analyse source and normalized document types."""

    mapping: dict[str, dict[str, Any]] = {}
    source_counts: Counter[str] = Counter()
    normalized_counts: Counter[str] = Counter()
    label_by_value: dict[str, str] = {}
    source_values_by_normalized: dict[str, list[str]] = defaultdict(list)

    for record in records:
        source_type = _value(record, "document_type") or "Onbekend"
        normalized = normalize_document_type(source_type)
        source_counts[source_type] += 1
        normalized_counts[normalized.value] += 1
        label_by_value[normalized.value] = normalized.label
        if source_type not in source_values_by_normalized[normalized.value]:
            source_values_by_normalized[normalized.value].append(source_type)

    for source_type, count in sorted(source_counts.items()):
        normalized = normalize_document_type(source_type)
        mapping[source_type] = {
            "count": count,
            "normalized_document_type": normalized.value,
            "normalized_document_type_label": normalized.label,
        }

    unknown_source_types = [
        {"document_type": source_type, "count": count}
        for source_type, count in source_counts.most_common()
        if normalize_document_type(source_type).value == "unknown"
    ]
    unknown_count = sum(item["count"] for item in unknown_source_types)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "documents_total": len(records),
        "source_document_type_count": len(source_counts),
        "normalized_document_type_count": len(normalized_counts),
        "unknown_document_type_count": unknown_count,
        "unknown_document_type_percentage": round((unknown_count / len(records) * 100), 2)
        if records
        else 0.0,
        "source_document_types": [
            {
                "document_type": source_type,
                "count": count,
                "normalized_document_type": normalize_document_type(source_type).value,
                "normalized_document_type_label": normalize_document_type(source_type).label,
            }
            for source_type, count in source_counts.most_common()
        ],
        "normalized_document_types": [
            {
                "normalized_document_type": value,
                "normalized_document_type_label": label_by_value[value],
                "count": count,
                "source_document_types": sorted(source_values_by_normalized[value]),
            }
            for value, count in normalized_counts.most_common()
        ],
        "mapping": mapping,
        "unknown_source_document_types": unknown_source_types,
        "notes": [
            "The source document_type value is kept for traceability.",
            "normalized_document_type is now part of the canonical Document export.",
            "Unknown should be reserved for genuinely missing or explicitly unknown source values.",
        ],
    }
