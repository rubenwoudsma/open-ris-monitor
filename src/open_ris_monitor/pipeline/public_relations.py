"""Helpers for keeping public relation exports aligned with public documents."""

from __future__ import annotations

from dataclasses import is_dataclass, replace
from typing import Any


def _to_dict(record: Any) -> dict[str, Any]:
    if hasattr(record, "to_dict") and callable(record.to_dict):
        value = record.to_dict()
        return value if isinstance(value, dict) else {}
    if hasattr(record, "model_dump") and callable(record.model_dump):
        value = record.model_dump(mode="json")
        return value if isinstance(value, dict) else {}
    if isinstance(record, dict):
        return record
    return {}


def _field(record: Any, name: str) -> Any:
    if isinstance(record, dict):
        return record.get(name)
    return getattr(record, name, None)


def _add_identifier(result: set[str], value: Any) -> None:
    if value is None:
        return
    text = str(value).strip()
    if text:
        result.add(text)


def _prefixed_identifier(value: Any, *, municipality_slug: str | None, entity: str) -> str | None:
    text = str(value).strip() if value is not None else ""
    if not text:
        return None
    if f"-{entity}-" in text:
        return text
    if municipality_slug:
        return f"{municipality_slug}-{entity}-{text}"
    return None


def _record_municipality_slug(record: Any) -> str | None:
    value = _field(record, "municipality_slug")
    return str(value).strip() if value is not None and str(value).strip() else None


def _replace_fields(record: Any, updates: dict[str, Any]) -> Any:
    """Return record with selected fields updated, preserving record type where safe."""
    if not updates:
        return record
    if isinstance(record, dict):
        updated = dict(record)
        updated.update(updates)
        return updated
    if is_dataclass(record):
        allowed = {name for name in getattr(record, "__dataclass_fields__", {})}
        safe_updates = {key: value for key, value in updates.items() if key in allowed}
        if safe_updates:
            return replace(record, **safe_updates)
    return record


def document_identifiers(document: Any) -> set[str]:
    """Return all stable identifiers that can refer to a public document."""
    result: set[str] = set()
    payload = _to_dict(document)
    municipality_slug = _record_municipality_slug(document)

    _add_identifier(result, _field(document, "id"))
    _add_identifier(result, _field(document, "source_id"))
    _add_identifier(result, _field(document, "source_object_id"))
    _add_identifier(result, payload.get("download_url"))
    _add_identifier(result, payload.get("source_url"))

    raw = payload.get("raw")
    if isinstance(raw, dict):
        _add_identifier(result, raw.get("id"))
        _add_identifier(result, raw.get("objectId"))
        _add_identifier(result, raw.get("object_id"))
        _add_identifier(result, raw.get("downloadUrl"))
        _add_identifier(result, raw.get("download_url"))

    source_id = _field(document, "source_id")
    source_object_id = _field(document, "source_object_id")
    document_id = _field(document, "id")
    if source_id is not None and isinstance(document_id, str) and "-document-" in document_id:
        prefix = document_id.rsplit("-document-", 1)[0]
        _add_identifier(result, f"{prefix}-document-{source_id}")
    if source_object_id is not None and isinstance(document_id, str) and "-document-" in document_id:
        prefix = document_id.rsplit("-document-", 1)[0]
        _add_identifier(result, f"{prefix}-document-{source_object_id}")
    _add_identifier(result, _prefixed_identifier(source_id, municipality_slug=municipality_slug, entity="document"))
    _add_identifier(result, _prefixed_identifier(source_object_id, municipality_slug=municipality_slug, entity="document"))
    return result


def relation_document_identifiers(relation: Any) -> set[str]:
    """Return document identifiers carried by a normalized relation record."""
    result: set[str] = set()
    payload = _to_dict(relation)
    municipality_slug = _record_municipality_slug(relation)

    _add_identifier(result, _field(relation, "document_id"))
    _add_identifier(result, _field(relation, "document_source_id"))
    _add_identifier(result, _field(relation, "document_object_id"))
    _add_identifier(result, payload.get("document_url"))
    _add_identifier(result, payload.get("download_url"))
    _add_identifier(result, payload.get("source_url"))

    document = payload.get("document")
    if isinstance(document, dict):
        _add_identifier(result, document.get("id"))
        _add_identifier(result, document.get("source_id"))
        _add_identifier(result, document.get("objectId"))
        _add_identifier(result, document.get("object_id"))
        _add_identifier(result, document.get("source_object_id"))
        _add_identifier(result, document.get("downloadUrl"))
        _add_identifier(result, document.get("download_url"))

    _add_identifier(
        result,
        _prefixed_identifier(_field(relation, "document_source_id"), municipality_slug=municipality_slug, entity="document"),
    )
    _add_identifier(
        result,
        _prefixed_identifier(_field(relation, "document_object_id"), municipality_slug=municipality_slug, entity="document"),
    )
    return result


def _meeting_identifiers(meeting: Any) -> set[str]:
    result: set[str] = set()
    municipality_slug = _record_municipality_slug(meeting)
    _add_identifier(result, _field(meeting, "id"))
    _add_identifier(result, _field(meeting, "source_id"))
    _add_identifier(result, _prefixed_identifier(_field(meeting, "source_id"), municipality_slug=municipality_slug, entity="meeting"))
    return result


def _relation_meeting_identifiers(relation: Any) -> set[str]:
    result: set[str] = set()
    municipality_slug = _record_municipality_slug(relation)
    _add_identifier(result, _field(relation, "meeting_id"))
    _add_identifier(result, _field(relation, "meeting_source_id"))
    _add_identifier(result, _prefixed_identifier(_field(relation, "meeting_source_id"), municipality_slug=municipality_slug, entity="meeting"))
    return result


def _meeting_item_identifiers(item: Any) -> set[str]:
    result: set[str] = set()
    municipality_slug = _record_municipality_slug(item)
    _add_identifier(result, _field(item, "id"))
    _add_identifier(result, _field(item, "source_id"))
    _add_identifier(result, _prefixed_identifier(_field(item, "source_id"), municipality_slug=municipality_slug, entity="meeting-item"))
    return result


def _relation_item_identifiers(relation: Any) -> set[str]:
    result: set[str] = set()
    municipality_slug = _record_municipality_slug(relation)
    _add_identifier(result, _field(relation, "meeting_item_id"))
    _add_identifier(result, _field(relation, "meeting_item_source_id"))
    _add_identifier(
        result,
        _prefixed_identifier(_field(relation, "meeting_item_source_id"), municipality_slug=municipality_slug, entity="meeting-item"),
    )
    return result


def _index_by_identifiers(records: list[Any], identifier_func: Any) -> dict[str, Any]:
    index: dict[str, Any] = {}
    for record in records:
        for identifier in identifier_func(record):
            index.setdefault(identifier, record)
    return index


def _canonical_document_update(relation: Any, document: Any) -> dict[str, Any]:
    document_id = _field(document, "id")
    document_source_id = _field(document, "source_id")
    document_object_id = _field(document, "source_object_id")
    updates: dict[str, Any] = {}
    if document_id is not None:
        updates["document_id"] = document_id
        updates.setdefault("source_id", document_id)
    if document_source_id is not None:
        updates["document_source_id"] = document_source_id
    if document_object_id is not None:
        updates["document_object_id"] = document_object_id
    return updates


def _canonical_meeting_update(meeting: Any) -> dict[str, Any]:
    updates: dict[str, Any] = {}
    if (meeting_id := _field(meeting, "id")) is not None:
        updates["meeting_id"] = meeting_id
        updates["target_id"] = meeting_id
    if (meeting_source_id := _field(meeting, "source_id")) is not None:
        updates["meeting_source_id"] = meeting_source_id
    return updates


def _canonical_item_update(item: Any) -> dict[str, Any]:
    updates: dict[str, Any] = {}
    if (item_id := _field(item, "id")) is not None:
        updates["meeting_item_id"] = item_id
        updates["target_id"] = item_id
    if (item_source_id := _field(item, "source_id")) is not None:
        updates["meeting_item_source_id"] = item_source_id
    if (meeting_id := _field(item, "meeting_id")) is not None:
        updates["meeting_id"] = meeting_id
    if (meeting_source_id := _field(item, "meeting_source_id")) is not None:
        updates["meeting_source_id"] = meeting_source_id
    return updates


def _matching_record(index: dict[str, Any], keys: set[str]) -> Any | None:
    for key in keys:
        record = index.get(key)
        if record is not None:
            return record
    return None


def _relation_matches_public_document(relation: Any, public_document_keys: set[str]) -> bool:
    return not relation_document_identifiers(relation).isdisjoint(public_document_keys)


def _normalized_meeting_document_relation(
    relation: Any,
    *,
    document_index: dict[str, Any],
    meeting_index: dict[str, Any],
) -> Any | None:
    document = _matching_record(document_index, relation_document_identifiers(relation))
    meeting = _matching_record(meeting_index, _relation_meeting_identifiers(relation))
    if document is None or meeting is None:
        return None
    updates = _canonical_document_update(relation, document)
    updates.update(_canonical_meeting_update(meeting))
    updates.setdefault("type", "document_to_meeting")
    return _replace_fields(relation, updates)


def _normalized_meeting_item_document_relation(
    relation: Any,
    *,
    document_index: dict[str, Any],
    meeting_index: dict[str, Any],
    item_index: dict[str, Any],
) -> Any | None:
    document = _matching_record(document_index, relation_document_identifiers(relation))
    item = _matching_record(item_index, _relation_item_identifiers(relation))
    if document is None or item is None:
        return None
    meeting = _matching_record(meeting_index, _relation_meeting_identifiers(relation))
    if meeting is None:
        meeting = _matching_record(meeting_index, {str(_field(item, "meeting_id"))})
    if meeting is None:
        return None
    updates = _canonical_document_update(relation, document)
    updates.update(_canonical_item_update(item))
    updates.update(_canonical_meeting_update(meeting))
    updates.setdefault("type", "document_to_agenda_item")
    return _replace_fields(relation, updates)


def filter_relation_exports_for_documents(
    normalized_relations: dict[str, list[Any]],
    documents: list[Any],
) -> tuple[dict[str, list[Any]], dict[str, int]]:
    """Filter public relation exports to the currently published document scope.

    This helper must never decide which documents are published. The caller passes
    the already selected public document export scope, and every document in that
    scope must remain available to the document-first viewer, including documents
    without meeting or agenda-item relations.

    The raw relation harvest may scan a broader, source-endpoint based meeting
    window. The static site consumes a bounded documents.jsonl export, so public
    relation exports should only include referentially complete relation records:

    * meeting_documents must point to a published document and meeting;
    * meeting_item_documents must point to a published document, agenda item and meeting;
    * meeting_items must point to a published meeting.

    Relations are also canonicalized back to the public IDs when a source_id,
    source_object_id or upstream URL was used to identify the document. Broken
    relation records are excluded; unrelated documents are not excluded from the
    document export by this helper.
    """
    public_document_keys: set[str] = set()
    for document in documents:
        public_document_keys.update(document_identifiers(document))

    raw_meetings = list(normalized_relations.get("meetings", []))
    raw_items = list(normalized_relations.get("meeting_items", []))
    raw_meeting_documents = list(normalized_relations.get("meeting_documents", []))
    raw_item_documents = list(normalized_relations.get("meeting_item_documents", []))

    document_index = _index_by_identifiers(documents, document_identifiers)
    meeting_index = _index_by_identifiers(raw_meetings, _meeting_identifiers)

    valid_items: list[Any] = []
    for item in raw_items:
        if _matching_record(meeting_index, {str(_field(item, "meeting_id")), str(_field(item, "meeting_source_id"))}) is not None:
            valid_items.append(item)
    item_index = _index_by_identifiers(valid_items, _meeting_item_identifiers)

    meeting_documents = [
        relation
        for relation in (
            _normalized_meeting_document_relation(
                relation,
                document_index=document_index,
                meeting_index=meeting_index,
            )
            for relation in raw_meeting_documents
            if _relation_matches_public_document(relation, public_document_keys)
        )
        if relation is not None
    ]

    meeting_item_documents = [
        relation
        for relation in (
            _normalized_meeting_item_document_relation(
                relation,
                document_index=document_index,
                meeting_index=meeting_index,
                item_index=item_index,
            )
            for relation in raw_item_documents
            if _relation_matches_public_document(relation, public_document_keys)
        )
        if relation is not None
    ]

    used_meeting_ids = {
        str(meeting_id)
        for relation in [*meeting_documents, *meeting_item_documents]
        if (meeting_id := _field(relation, "meeting_id")) is not None
    }
    used_item_ids = {
        str(item_id)
        for relation in meeting_item_documents
        if (item_id := _field(relation, "meeting_item_id")) is not None
    }

    meetings = [meeting for meeting in raw_meetings if str(_field(meeting, "id")) in used_meeting_ids]
    meeting_items = [item for item in valid_items if str(_field(item, "id")) in used_item_ids]

    related_document_keys: set[str] = set()
    for relation in [*meeting_documents, *meeting_item_documents]:
        related_document_keys.update(relation_document_identifiers(relation))

    documents_with_relations = sum(
        1
        for document in documents
        if not document_identifiers(document).isdisjoint(related_document_keys)
    )

    publication_summary = {
        # Documents are intentionally reported, not filtered. The document export
        # remains document-first: documents without public relations stay visible
        # in documents.jsonl and the Documenten tab.
        "documents_published": len(documents),
        "documents_with_published_relations": documents_with_relations,
        "raw_meetings_seen": len(raw_meetings),
        "raw_meeting_items_seen": len(raw_items),
        "raw_meeting_document_relations_seen": len(raw_meeting_documents),
        "raw_meeting_item_document_relations_seen": len(raw_item_documents),
        "published_meetings": len(meetings),
        "published_meeting_items": len(meeting_items),
        "published_meeting_document_relations": len(meeting_documents),
        "published_meeting_item_document_relations": len(meeting_item_documents),
        "dropped_meeting_items_without_public_meeting": len(raw_items) - len(valid_items),
        "dropped_meeting_document_relations": len(raw_meeting_documents) - len(meeting_documents),
        "dropped_meeting_item_document_relations": len(raw_item_documents) - len(meeting_item_documents),
    }

    return (
        {
            "meetings": meetings,
            "meeting_items": meeting_items,
            "meeting_documents": meeting_documents,
            "meeting_item_documents": meeting_item_documents,
        },
        publication_summary,
    )
