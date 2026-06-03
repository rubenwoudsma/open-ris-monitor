"""Helpers for keeping public relation exports aligned with public documents."""

from __future__ import annotations

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


def document_identifiers(document: Any) -> set[str]:
    """Return all stable identifiers that can refer to a public document."""

    result: set[str] = set()
    payload = _to_dict(document)

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
    document_id = _field(document, "id")
    if source_id is not None and isinstance(document_id, str) and "-document-" in document_id:
        prefix = document_id.rsplit("-document-", 1)[0]
        _add_identifier(result, f"{prefix}-document-{source_id}")

    return result


def relation_document_identifiers(relation: Any) -> set[str]:
    """Return document identifiers carried by a normalized relation record."""

    result: set[str] = set()
    payload = _to_dict(relation)

    _add_identifier(result, _field(relation, "document_id"))
    _add_identifier(result, _field(relation, "document_source_id"))
    _add_identifier(result, _field(relation, "document_object_id"))
    _add_identifier(result, payload.get("document_url"))
    _add_identifier(result, payload.get("download_url"))
    _add_identifier(result, payload.get("source_url"))

    document = payload.get("document")
    if isinstance(document, dict):
        _add_identifier(result, document.get("id"))
        _add_identifier(result, document.get("objectId"))
        _add_identifier(result, document.get("object_id"))
        _add_identifier(result, document.get("downloadUrl"))
        _add_identifier(result, document.get("download_url"))

    return result


def _relation_matches_public_document(relation: Any, public_document_keys: set[str]) -> bool:
    return not relation_document_identifiers(relation).isdisjoint(public_document_keys)


def filter_relation_exports_for_documents(
    normalized_relations: dict[str, list[Any]],
    documents: list[Any],
) -> tuple[dict[str, list[Any]], dict[str, int]]:
    """Filter public relation exports to the currently published documents.

    The raw relation harvest may scan a broader, source-endpoint based meeting
    window. The static site consumes a bounded documents.jsonl export, so public
    relation exports should only include relations that overlap with those
    documents. Related meetings and meeting items are then reduced to the subset
    referenced by the remaining relations.
    """

    public_document_keys: set[str] = set()
    for document in documents:
        public_document_keys.update(document_identifiers(document))

    raw_meetings = list(normalized_relations.get("meetings", []))
    raw_items = list(normalized_relations.get("meeting_items", []))
    raw_meeting_documents = list(normalized_relations.get("meeting_documents", []))
    raw_item_documents = list(normalized_relations.get("meeting_item_documents", []))

    meeting_documents = [
        relation
        for relation in raw_meeting_documents
        if _relation_matches_public_document(relation, public_document_keys)
    ]
    meeting_item_documents = [
        relation
        for relation in raw_item_documents
        if _relation_matches_public_document(relation, public_document_keys)
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
    meeting_items = [item for item in raw_items if str(_field(item, "id")) in used_item_ids]

    related_document_keys: set[str] = set()
    for relation in [*meeting_documents, *meeting_item_documents]:
        related_document_keys.update(relation_document_identifiers(relation))

    documents_with_relations = sum(
        1 for document in documents if not document_identifiers(document).isdisjoint(related_document_keys)
    )

    publication_summary = {
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
