from __future__ import annotations

from dataclasses import dataclass

from open_ris_monitor.pipeline.public_relations import (
    document_identifiers,
    filter_relation_exports_for_documents,
    relation_document_identifiers,
)


@dataclass(frozen=True)
class Record:
    id: str
    source_id: str | None = None
    source_object_id: str | None = None
    meeting_id: str | None = None
    meeting_item_id: str | None = None
    document_id: str | None = None
    document_source_id: str | None = None
    document_object_id: str | None = None

    def to_dict(self):
        return self.__dict__.copy()


def test_document_identifiers_include_canonical_and_source_identifiers() -> None:
    document = {
        "id": "huizen-document-42",
        "source_id": "42",
        "source_object_id": "obj-42",
        "download_url": "https://example.test/documents/42/download",
        "raw": {"id": 42, "objectId": "obj-42-raw"},
    }

    assert document_identifiers(document) >= {
        "huizen-document-42",
        "42",
        "obj-42",
        "obj-42-raw",
        "https://example.test/documents/42/download",
    }


def test_relation_document_identifiers_include_canonical_and_source_identifiers() -> None:
    relation = Record(
        id="rel-1",
        document_id="huizen-document-42",
        document_source_id="42",
        document_object_id="obj-42",
    )

    assert relation_document_identifiers(relation) >= {
        "huizen-document-42",
        "42",
        "obj-42",
    }


def test_filter_relation_exports_keeps_only_relations_for_published_documents() -> None:
    documents = [
        {"id": "huizen-document-42", "source_id": "42", "source_object_id": "obj-42"},
        {"id": "huizen-document-43", "source_id": "43"},
    ]
    normalized_relations = {
        "meetings": [
            Record(id="huizen-meeting-1"),
            Record(id="huizen-meeting-2"),
        ],
        "meeting_items": [
            Record(id="huizen-meeting-item-10"),
            Record(id="huizen-meeting-item-20"),
        ],
        "meeting_documents": [
            Record(
                id="rel-meeting-1-doc-42",
                meeting_id="huizen-meeting-1",
                document_id="huizen-document-42",
                document_source_id="42",
            ),
            Record(
                id="rel-meeting-2-doc-999",
                meeting_id="huizen-meeting-2",
                document_id="huizen-document-999",
                document_source_id="999",
            ),
        ],
        "meeting_item_documents": [
            Record(
                id="rel-item-10-doc-43",
                meeting_id="huizen-meeting-1",
                meeting_item_id="huizen-meeting-item-10",
                document_id="huizen-document-43",
                document_source_id="43",
            ),
            Record(
                id="rel-item-20-doc-999",
                meeting_id="huizen-meeting-2",
                meeting_item_id="huizen-meeting-item-20",
                document_id="huizen-document-999",
                document_source_id="999",
            ),
        ],
    }

    filtered, summary = filter_relation_exports_for_documents(normalized_relations, documents)

    assert [record.id for record in filtered["meetings"]] == ["huizen-meeting-1"]
    assert [record.id for record in filtered["meeting_items"]] == ["huizen-meeting-item-10"]
    assert [record.id for record in filtered["meeting_documents"]] == ["rel-meeting-1-doc-42"]
    assert [record.id for record in filtered["meeting_item_documents"]] == ["rel-item-10-doc-43"]
    assert summary == {
        "documents_published": 2,
        "documents_with_published_relations": 2,
        "raw_meetings_seen": 2,
        "raw_meeting_items_seen": 2,
        "raw_meeting_document_relations_seen": 2,
        "raw_meeting_item_document_relations_seen": 2,
        "published_meetings": 1,
        "published_meeting_items": 1,
        "published_meeting_document_relations": 1,
        "published_meeting_item_document_relations": 1,
    }


def test_filter_relation_exports_can_match_by_source_object_id() -> None:
    documents = [{"id": "huizen-document-42", "source_id": "42", "source_object_id": "obj-42"}]
    normalized_relations = {
        "meetings": [Record(id="huizen-meeting-1")],
        "meeting_items": [],
        "meeting_documents": [
            Record(
                id="rel-meeting-1-doc-object",
                meeting_id="huizen-meeting-1",
                document_id="huizen-document-999",
                document_object_id="obj-42",
            )
        ],
        "meeting_item_documents": [],
    }

    filtered, summary = filter_relation_exports_for_documents(normalized_relations, documents)

    assert [record.id for record in filtered["meeting_documents"]] == ["rel-meeting-1-doc-object"]
    assert summary["documents_with_published_relations"] == 1
