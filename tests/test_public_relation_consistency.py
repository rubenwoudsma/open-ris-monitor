from __future__ import annotations

import json

from open_ris_monitor.pipeline.public_relations import filter_relation_exports_for_documents


def _jsonl_roundtrip(records: list[dict[str, object]]) -> list[dict[str, object]]:
    payload = "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records)
    return [json.loads(line) for line in payload.splitlines()]


def test_public_relations_are_canonicalized_and_referentially_complete() -> None:
    documents = [
        {
            "id": "huizen-document-canonical-1",
            "source_id": "100",
            "source_object_id": "OBJ-100",
            "municipality_slug": "huizen",
            "raw": {"id": "100", "objectId": "OBJ-100"},
        }
    ]
    normalized_relations = {
        "meetings": [
            {"id": "huizen-meeting-M1", "source_id": "M1", "municipality_slug": "huizen"},
            {"id": "huizen-meeting-M2", "source_id": "M2", "municipality_slug": "huizen"},
        ],
        "meeting_items": [
            {
                "id": "huizen-meeting-item-I1",
                "source_id": "I1",
                "meeting_id": "huizen-meeting-M1",
                "meeting_source_id": "M1",
                "municipality_slug": "huizen",
            },
            {
                "id": "huizen-meeting-item-I2",
                "source_id": "I2",
                "meeting_id": "huizen-meeting-MISSING",
                "meeting_source_id": "MISSING",
                "municipality_slug": "huizen",
            },
        ],
        "meeting_documents": [
            {
                "id": "r1",
                "meeting_id": "huizen-meeting-M1",
                "meeting_source_id": "M1",
                "document_id": "wrong-document-id",
                "document_source_id": "100",
                "document_object_id": None,
                "municipality_slug": "huizen",
            },
            {
                "id": "r-orphan-meeting",
                "meeting_id": "huizen-meeting-MISSING",
                "meeting_source_id": "MISSING",
                "document_id": "huizen-document-canonical-1",
                "document_source_id": "100",
                "municipality_slug": "huizen",
            },
        ],
        "meeting_item_documents": [
            {
                "id": "ir1",
                "meeting_id": "huizen-meeting-M1",
                "meeting_source_id": "M1",
                "meeting_item_id": "huizen-meeting-item-I1",
                "meeting_item_source_id": "I1",
                "document_id": "wrong-document-id",
                "document_source_id": "unused",
                "document_object_id": "OBJ-100",
                "municipality_slug": "huizen",
            },
            {
                "id": "ir-orphan-item",
                "meeting_id": "huizen-meeting-M1",
                "meeting_source_id": "M1",
                "meeting_item_id": "huizen-meeting-item-MISSING",
                "meeting_item_source_id": "MISSING",
                "document_id": "huizen-document-canonical-1",
                "document_source_id": "100",
                "municipality_slug": "huizen",
            },
        ],
    }

    public_relations, summary = filter_relation_exports_for_documents(normalized_relations, documents)

    assert [record["id"] for record in public_relations["meetings"]] == ["huizen-meeting-M1"]
    assert [record["id"] for record in public_relations["meeting_items"]] == ["huizen-meeting-item-I1"]

    meeting_document = public_relations["meeting_documents"][0]
    assert meeting_document["document_id"] == "huizen-document-canonical-1"
    assert meeting_document["meeting_id"] == "huizen-meeting-M1"
    assert meeting_document["source_id"] == "huizen-document-canonical-1"
    assert meeting_document["target_id"] == "huizen-meeting-M1"

    item_document = public_relations["meeting_item_documents"][0]
    assert item_document["document_id"] == "huizen-document-canonical-1"
    assert item_document["meeting_id"] == "huizen-meeting-M1"
    assert item_document["meeting_item_id"] == "huizen-meeting-item-I1"
    assert item_document["source_id"] == "huizen-document-canonical-1"
    assert item_document["target_id"] == "huizen-meeting-item-I1"

    assert summary["published_meetings"] == 1
    assert summary["published_meeting_items"] == 1
    assert summary["published_meeting_document_relations"] == 1
    assert summary["published_meeting_item_document_relations"] == 1
    assert "dropped_meeting_document_relations" not in summary
    assert "dropped_meeting_item_document_relations" not in summary

    assert _jsonl_roundtrip(public_relations["meeting_documents"]) == public_relations["meeting_documents"]
    assert _jsonl_roundtrip(public_relations["meeting_item_documents"]) == public_relations["meeting_item_documents"]


def test_public_relation_filter_tolerates_empty_or_missing_source_fields() -> None:
    public_relations, summary = filter_relation_exports_for_documents(
        {
            "meetings": [{"id": "huizen-meeting-M1", "source_id": "M1"}],
            "meeting_items": [{"id": "huizen-meeting-item-I1", "meeting_id": "huizen-meeting-M1"}],
            "meeting_documents": [{"id": "broken", "document_id": None, "meeting_id": "huizen-meeting-M1"}],
            "meeting_item_documents": [{"id": "broken-item", "document": {}, "meeting_item_id": None}],
        },
        [{"id": "huizen-document-D1", "source_id": "D1"}],
    )

    assert public_relations["meetings"] == []
    assert public_relations["meeting_items"] == []
    assert public_relations["meeting_documents"] == []
    assert public_relations["meeting_item_documents"] == []
    assert summary["documents_published"] == 1
    assert summary["documents_with_published_relations"] == 0


def test_documents_without_relations_remain_in_public_document_scope() -> None:
    documents = [
        {"id": "huizen-document-linked", "source_id": "D1", "municipality_slug": "huizen"},
        {"id": "huizen-document-unrelated", "source_id": "D2", "municipality_slug": "huizen"},
    ]
    normalized_relations = {
        "meetings": [{"id": "huizen-meeting-M1", "source_id": "M1", "municipality_slug": "huizen"}],
        "meeting_items": [],
        "meeting_documents": [
            {
                "id": "r-linked",
                "meeting_id": "huizen-meeting-M1",
                "meeting_source_id": "M1",
                "document_id": "huizen-document-linked",
                "document_source_id": "D1",
                "municipality_slug": "huizen",
            }
        ],
        "meeting_item_documents": [],
    }

    public_relations, summary = filter_relation_exports_for_documents(normalized_relations, documents)

    assert summary["documents_published"] == 2
    assert summary["documents_with_published_relations"] == 1
    assert [document["id"] for document in documents] == [
        "huizen-document-linked",
        "huizen-document-unrelated",
    ]
    assert [relation["document_id"] for relation in public_relations["meeting_documents"]] == [
        "huizen-document-linked"
    ]


def test_broken_relations_are_dropped_without_dropping_documents_from_scope() -> None:
    documents = [
        {"id": "huizen-document-D1", "source_id": "D1", "municipality_slug": "huizen"},
        {"id": "huizen-document-D2", "source_id": "D2", "municipality_slug": "huizen"},
    ]
    normalized_relations = {
        "meetings": [{"id": "huizen-meeting-M1", "source_id": "M1", "municipality_slug": "huizen"}],
        "meeting_items": [],
        "meeting_documents": [
            {
                "id": "broken-missing-meeting",
                "meeting_id": "huizen-meeting-MISSING",
                "meeting_source_id": "MISSING",
                "document_id": "huizen-document-D1",
                "document_source_id": "D1",
                "municipality_slug": "huizen",
            },
            {
                "id": "broken-missing-document",
                "meeting_id": "huizen-meeting-M1",
                "meeting_source_id": "M1",
                "document_id": "huizen-document-MISSING",
                "document_source_id": "MISSING",
                "municipality_slug": "huizen",
            },
        ],
        "meeting_item_documents": [],
    }

    public_relations, summary = filter_relation_exports_for_documents(normalized_relations, documents)

    assert public_relations["meeting_documents"] == []
    assert summary["documents_published"] == 2
    assert summary["documents_with_published_relations"] == 0
    assert summary["published_meeting_document_relations"] == 0
