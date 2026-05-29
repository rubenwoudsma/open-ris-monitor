from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any


COMPACT_DOCUMENT_TYPE_LABELS: dict[str, str] = {
    "agenda": "Agenda",
    "amendment": "Amendement",
    "announcement": "Mededeling",
    "answer": "Beantwoording",
    "attachment": "Bijlage",
    "commitment": "Toezegging",
    "decision": "Besluit",
    "incoming_document": "Ingekomen stuk",
    "invitation": "Uitnodiging",
    "memo_or_advice": "Memo of advies",
    "minutes_or_summary": "Notulen, verslag of resumé",
    "motion": "Motie",
    "objection_or_response": "Bezwaar, klacht of zienswijze",
    "other": "Overig",
    "policy_or_plan": "Beleid, plan of nota",
    "proposal": "Voorstel",
    "question": "Vraag",
    "report": "Rapportage of evaluatie",
    "request": "Verzoek of aanvullende gegevens",
    "notice": "Kennisgeving of ter kennisname",
    "unknown": "Onbekend",
}


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
    """Map GemeenteOplossingen source labels to compact analytical categories.

    The mapping intentionally keeps the original source value separate. The
    compact value is meant for filters, dashboards and quality reports. It is
    broader than the source labels, so many local RIS labels can be grouped
    without losing traceability.
    """
    if not source_type:
        return "unknown"

    value = source_type.strip().lower()
    if not value or value == "onbekend":
        return "unknown"

    if "agenda" in value:
        return "agenda"
    if "bijlage" in value:
        return "attachment"
    if "amendement" in value:
        return "amendment"
    if "motie" in value:
        return "motion"
    if "vraag" in value or "vragen" in value:
        return "question"
    if "raadsvoorstel" in value or "collegevoorstel" in value or "voorstel" in value:
        return "proposal"
    if "besluit" in value:
        return "decision"
    if "mededeling" in value:
        return "announcement"
    if "ingekomen" in value and not any(
        marker in value for marker in ["bezwaar", "klacht", "zienswijze", "verzoek", "vraag", "uitnodiging"]
    ):
        return "incoming_document"
    if "resum" in value or "verslag" in value or "notulen" in value:
        return "minutes_or_summary"
    if "beleidsnota" in value or "omgevingswet" in value or "vastgesteld plan" in value or "voorjaarsnota" in value or "bestemmingsplan" in value:
        return "policy_or_plan"
    if "rapport" in value or "rapportage" in value or "evaluatie" in value or "onderzoeksstuk" in value or "bevindingen" in value or "financiële overzichten" in value or "overzicht stand" in value:
        return "report"
    if "kennisgeving" in value or "stukken ter kennisname" in value or "document ter kennisname" in value:
        return "notice"
    if "advies" in value or "memo" in value:
        return "memo_or_advice"
    if "beantwoording" in value or "antwoord" in value:
        return "answer"
    if "toezegging" in value:
        return "commitment"
    if "uitnodiging" in value:
        return "invitation"
    if "verzoek" in value or "aanvullende gegevens" in value:
        return "request"
    if "bezwaarschrift" in value or "zienswijze" in value or "klacht" in value:
        return "objection_or_response"
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
    unknown_source_types: list[dict[str, Any]] = []
    for source_type, count in sorted(source_counter.items(), key=lambda item: (-item[1], item[0])):
        normalized = normalize_document_type(None if source_type == "Onbekend" else source_type)
        mappings[source_type] = {
            "count": count,
            "normalized_document_type": normalized,
            "normalized_document_type_label": COMPACT_DOCUMENT_TYPE_LABELS.get(normalized, normalized),
        }
        if normalized == "unknown":
            unknown_source_types.append({"document_type": source_type, "count": count})

    unknown_count = normalized_counter.get("unknown", 0)
    unknown_percentage = round((unknown_count / len(documents)) * 100, 2) if documents else 0.0

    return {
        "generated_at": _utc_now(),
        "documents_total": len(documents),
        "source_document_type_count": len(source_counter),
        "normalized_document_type_count": len(normalized_counter),
        "unknown_document_type_count": unknown_count,
        "unknown_document_type_percentage": unknown_percentage,
        "source_document_types": [
            {
                "document_type": key,
                "count": value,
                "normalized_document_type": mappings[key]["normalized_document_type"],
                "normalized_document_type_label": mappings[key]["normalized_document_type_label"],
            }
            for key, value in sorted(source_counter.items(), key=lambda item: (-item[1], item[0]))
        ],
        "normalized_document_types": [
            {
                "normalized_document_type": key,
                "normalized_document_type_label": COMPACT_DOCUMENT_TYPE_LABELS.get(key, key),
                "count": value,
            }
            for key, value in sorted(normalized_counter.items(), key=lambda item: (-item[1], item[0]))
        ],
        "unknown_source_document_types": unknown_source_types,
        "mapping": mappings,
        "notes": [
            "The source document_type value is kept for traceability.",
            "The normalized_document_type proposal is intended for future viewer filters and quality reports.",
            "Unknown should be reserved for genuinely missing or explicitly unknown source values.",
            "This report is still analytical; adding normalized_document_type to the canonical Document model should be handled in a separate issue.",
        ],
    }
