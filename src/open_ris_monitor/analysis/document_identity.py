from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _as_string(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


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
    """Map source document type labels to a compact analytical category.

    This is deliberately conservative. The original source value should always
    remain available on the canonical Document record. The normalized value is
    intended for filtering, dashboards and quality reports.
    """
    if not source_type:
        return "unknown"

    value = source_type.strip().lower()

    if "agenda" in value:
        return "agenda"
    if "bijlage" in value:
        return "attachment"
    if "raadsvoorstel" in value or "voorstel" in value:
        return "proposal"
    if "mededeling" in value:
        return "announcement"
    if "ingekomen" in value:
        return "incoming_document"
    if "resum" in value or "verslag" in value or "notulen" in value:
        return "minutes_or_summary"
    if "besluit" in value:
        return "decision"
    if "motie" in value:
        return "motion"
    if "amendement" in value:
        return "amendment"
    if "vraag" in value or "vragen" in value:
        return "question"
    if "overig" in value:
        return "other"

    return "unknown"


def analyze_document_identity(documents: list[dict[str, Any]]) -> dict[str, Any]:
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
        },
        "recommended_identity_key": recommended_identity_key,
        "notes": [
            "This report only analyses the current public export snapshot.",
            "Longitudinal stability requires comparing multiple harvest outputs over time.",
            "The original RIS identifiers remain source values; the canonical id should stay stable and traceable.",
        ],
    }


def analyze_document_types(documents: list[dict[str, Any]]) -> dict[str, Any]:
    source_types = [document.get("document_type") or "Onbekend" for document in documents]
    source_counter = Counter(source_types)
    normalized_counter = Counter(normalize_document_type(document.get("document_type")) for document in documents)

    mappings: dict[str, dict[str, Any]] = {}
    for source_type, count in sorted(source_counter.items(), key=lambda item: (-item[1], item[0])):
        normalized = normalize_document_type(None if source_type == "Onbekend" else source_type)
        mappings[source_type] = {
            "count": count,
            "normalized_document_type": normalized,
        }

    return {
        "generated_at": _utc_now(),
        "documents_total": len(documents),
        "source_document_type_count": len(source_counter),
        "normalized_document_type_count": len(normalized_counter),
        "source_document_types": [
            {"document_type": key, "count": value, "normalized_document_type": mappings[key]["normalized_document_type"]}
            for key, value in sorted(source_counter.items(), key=lambda item: (-item[1], item[0]))
        ],
        "normalized_document_types": [
            {"normalized_document_type": key, "count": value}
            for key, value in sorted(normalized_counter.items(), key=lambda item: (-item[1], item[0]))
        ],
        "mapping": mappings,
        "notes": [
            "The source document_type value is kept for traceability.",
            "The normalized_document_type proposal is intended for future viewer filters and quality reports.",
            "Unknown mappings should be reviewed before adding normalized_document_type to the canonical Document model.",
        ],
    }
