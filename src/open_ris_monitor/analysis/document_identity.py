"""Analysis helpers for document identity and document type reporting."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any

from open_ris_monitor.normalizers.document_types import (
    NormalizedDocumentType,
    normalize_document_type as normalize_document_type_details,
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _as_string(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _value(record: dict[str, Any], key: str) -> str | None:
    return _as_string(record.get(key))


def _duplicates(values: list[str | None]) -> dict[str, int]:
    counter = Counter(value for value in values if value)
    return {key: count for key, count in sorted(counter.items()) if count > 1}


def _duplicate_examples(documents: list[dict[str, Any]], field: str, limit: int = 25) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for document in documents:
        value = _as_string(document.get(field))
        if value:
            grouped[value].append(document)

    examples: list[dict[str, Any]] = []
    for value, items in sorted(grouped.items()):
        if len(items) <= 1:
            continue
        examples.append(
            {
                field: value,
                "count": len(items),
                "documents": [
                    {
                        "id": item.get("id"),
                        "source_id": item.get("source_id"),
                        "source_object_id": item.get("source_object_id"),
                        "title": item.get("title"),
                        "filename": item.get("filename"),
                    }
                    for item in items[:5]
                ],
            }
        )
        if len(examples) >= limit:
            break
    return examples


def normalize_document_type(source_type: str | None) -> str:
    """Compatibility wrapper returning only the compact type value.

    The canonical normalizer returns a NormalizedDocumentType object with both
    value and label. The issue 22 analysis tests and public reports originally
    imported this helper from this module and expected a string. Keep that
    public helper available while using the central mapping underneath.
    """

    return normalize_document_type_details(source_type).value


def _normalize_with_label(source_type: str | None) -> NormalizedDocumentType:
    return normalize_document_type_details(source_type)


def analyze_document_identity(documents: list[dict[str, Any]]) -> dict[str, Any]:
    """Analyze source and canonical identifiers in a document export."""

    source_ids = [_as_string(document.get("source_id")) for document in documents]
    object_ids = [_as_string(document.get("source_object_id")) for document in documents]
    canonical_ids = [_as_string(document.get("id")) for document in documents]

    duplicate_source_ids = _duplicates(source_ids)
    duplicate_object_ids = _duplicates(object_ids)
    duplicate_canonical_ids = _duplicates(canonical_ids)

    composite_keys: list[str | None] = []
    for document in documents:
        source_id = _as_string(document.get("source_id"))
        object_id = _as_string(document.get("source_object_id"))
        if source_id and object_id:
            composite_keys.append(f"{source_id}:{object_id}")
        else:
            composite_keys.append(None)

    duplicate_composite_keys = _duplicates(composite_keys)

    recommended_identity_key = "municipality_id + source_system_id + source_id + source_object_id"
    if duplicate_composite_keys:
        recommended_identity_key = "needs_review"
    elif any(object_id is None for object_id in object_ids):
        recommended_identity_key = "municipality_id + source_system_id + source_id"

    return {
        "generated_at": _utc_now(),
        "documents_total": len(documents),
        "canonical_id": {
            "unique_count": len({value for value in canonical_ids if value}),
            "missing_count": sum(1 for value in canonical_ids if not value),
            "duplicate_count": sum(duplicate_canonical_ids.values()),
            "duplicates": _duplicate_examples(documents, "id"),
        },
        "source_id": {
            "unique_count": len({value for value in source_ids if value}),
            "missing_count": sum(1 for value in source_ids if not value),
            "duplicate_count": sum(duplicate_source_ids.values()),
            "duplicates": _duplicate_examples(documents, "source_id"),
        },
        "source_object_id": {
            "unique_count": len({value for value in object_ids if value}),
            "missing_count": sum(1 for value in object_ids if not value),
            "duplicate_count": sum(duplicate_object_ids.values()),
            "duplicates": _duplicate_examples(documents, "source_object_id"),
        },
        "composite_source_key": {
            "description": "source_id + source_object_id",
            "unique_count": len({value for value in composite_keys if value}),
            "missing_count": sum(1 for value in composite_keys if not value),
            "duplicate_count": sum(duplicate_composite_keys.values()),
            "duplicates": [
                {"value": value, "count": count}
                for value, count in sorted(duplicate_composite_keys.items())
            ],
        },
        "recommended_identity_key": recommended_identity_key,
        "notes": [
            "This report only analyses the current public export snapshot.",
            "Longitudinal stability requires comparing multiple harvest outputs over time.",
            "The original RIS identifiers remain source values; the canonical id should stay stable and traceable.",
        ],
    }


def analyze_document_types(documents: list[dict[str, Any]]) -> dict[str, Any]:
    """Analyze source and normalized document types."""

    source_counter: Counter[str] = Counter()
    normalized_counter: Counter[str] = Counter()
    label_by_value: dict[str, str] = {}
    source_values_by_normalized: dict[str, list[str]] = defaultdict(list)

    for document in documents:
        source_type = _as_string(document.get("document_type")) or "Onbekend"
        normalized = _normalize_with_label(source_type)
        source_counter[source_type] += 1
        normalized_counter[normalized.value] += 1
        label_by_value[normalized.value] = normalized.label
        if source_type not in source_values_by_normalized[normalized.value]:
            source_values_by_normalized[normalized.value].append(source_type)

    mappings: dict[str, dict[str, Any]] = {}
    for source_type, count in sorted(source_counter.items()):
        normalized = _normalize_with_label(source_type)
        mappings[source_type] = {
            "count": count,
            "normalized_document_type": normalized.value,
            "normalized_document_type_label": normalized.label,
        }

    unknown_source_types = [
        {"document_type": source_type, "count": count}
        for source_type, count in source_counter.most_common()
        if _normalize_with_label(source_type).value == "unknown"
    ]
    unknown_count = sum(item["count"] for item in unknown_source_types)

    return {
        "generated_at": _utc_now(),
        "documents_total": len(documents),
        "source_document_type_count": len(source_counter),
        "normalized_document_type_count": len(normalized_counter),
        "unknown_document_type_count": unknown_count,
        "unknown_document_type_percentage": round((unknown_count / len(documents) * 100), 2)
        if documents
        else 0.0,
        "source_document_types": [
            {
                "document_type": source_type,
                "count": count,
                "normalized_document_type": _normalize_with_label(source_type).value,
                "normalized_document_type_label": _normalize_with_label(source_type).label,
            }
            for source_type, count in source_counter.most_common()
        ],
        "normalized_document_types": [
            {
                "normalized_document_type": value,
                "normalized_document_type_label": label_by_value[value],
                "count": count,
                "source_document_types": sorted(source_values_by_normalized[value]),
            }
            for value, count in normalized_counter.most_common()
        ],
        "mapping": mappings,
        "unknown_source_document_types": unknown_source_types,
        "notes": [
            "The source document_type value is kept for traceability.",
            "normalized_document_type is now part of the canonical Document export.",
            "Unknown should be reserved for genuinely missing or explicitly unknown source values.",
        ],
    }


# Backwards-compatible Dutch spelling aliases. A previous issue 19 package used
# analyse_* names, while the issue 22 tests and reporting script use analyze_*.
analyse_identity = analyze_document_identity
analyse_document_types = analyze_document_types
