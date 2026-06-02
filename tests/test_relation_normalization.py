from __future__ import annotations

from open_ris_monitor.normalizers.relations import (
    normalize_meeting,
    normalize_meeting_document_relation,
    normalize_meeting_document_relations,
    normalize_meeting_item,
    normalize_meeting_item_document_relation,
    normalize_meeting_item_document_relations,
    normalize_meeting_items,
    normalize_meetings,
    normalize_relation_harvest,
)


SOURCE_SYSTEM_ID = "gemeenteoplossingen"
MUNICIPALITY = "huizen"


def sample_meeting() -> dict:
    return {
        "confidential": 0,
        "date": "2018-07-05",
        "description": "<p>Raadsvergadering 05 Jul 2018</p>",
        "dmu": {"id": 14, "name": "Raadsvergadering", "sortOrder": 0},
        "id": 19,
        "location": "Raadzaal",
        "meetingLabel": None,
        "startTime": "20:00",
        "url": "/Vergaderingen/Raadsvergadering/2018/5-juli/20:00",
    }


def sample_meeting_item() -> dict:
    return {
        "confidential": False,
        "description": "",
        "id": 142,
        "isHeading": False,
        "location": "Raadzaal",
        "meeting": sample_meeting(),
        "meetingSession": 1,
        "meeting_id": "19",
        "number": "5.2.",
        "sortOrder": 11,
        "status": {"abbreviation": "", "description": "", "id": 10},
        "title": "Ingekomen stukken rubriek B, om preadvies in handen van het college",
    }


def sample_document(document_id: int = 158) -> dict:
    return {
        "confidential": 0,
        "description": "Verzoek tot wijziging bestemmingsplan BNI-locatie aan de Havenstraat",
        "documentTypeLabel": "Principeverzoek bestemmingsplanwijziging (Inkomend)",
        "fileName": "Verzoek tot wijziging bestemmingsplan.pdf",
        "fileSize": 103797698,
        "id": document_id,
        "isTabsignDocument": False,
        "objectId": 333,
        "publicationDate": {
            "date": "2018-07-05 00:00:00.000000",
            "timezone": "Europe/Berlin",
            "timezone_type": 3,
        },
    }


def test_normalize_meeting_strips_html_and_builds_stable_id() -> None:
    meeting = normalize_meeting(
        sample_meeting(),
        municipality_slug=MUNICIPALITY,
        source_system_id=SOURCE_SYSTEM_ID,
    )

    assert meeting is not None
    assert meeting.id == "huizen-meeting-19"
    assert meeting.source_id == "19"
    assert meeting.description == "Raadsvergadering 05 Jul 2018"
    assert meeting.date == "2018-07-05"
    assert meeting.start_time == "20:00"
    assert meeting.dmu_id == "14"
    assert meeting.dmu_name == "Raadsvergadering"
    assert meeting.dmu_sort_order == 0
    assert meeting.is_confidential is False


def test_normalize_meeting_skips_record_without_source_id() -> None:
    raw = sample_meeting()
    raw.pop("id")

    assert (
        normalize_meeting(raw, municipality_slug=MUNICIPALITY, source_system_id=SOURCE_SYSTEM_ID)
        is None
    )


def test_normalize_meeting_item_builds_meeting_reference() -> None:
    item = normalize_meeting_item(
        sample_meeting_item(),
        municipality_slug=MUNICIPALITY,
        source_system_id=SOURCE_SYSTEM_ID,
    )

    assert item is not None
    assert item.id == "huizen-meeting-item-142"
    assert item.source_id == "142"
    assert item.meeting_id == "huizen-meeting-19"
    assert item.meeting_source_id == "19"
    assert item.number == "5.2."
    assert item.sort_order == 11
    assert item.title == "Ingekomen stukken rubriek B, om preadvies in handen van het college"
    assert item.status_id == "10"
    assert item.is_heading is False
    assert item.is_confidential is False


def test_normalize_meeting_item_can_use_nested_meeting_id() -> None:
    raw = sample_meeting_item()
    raw.pop("meeting_id")

    item = normalize_meeting_item(
        raw,
        municipality_slug=MUNICIPALITY,
        source_system_id=SOURCE_SYSTEM_ID,
    )

    assert item is not None
    assert item.meeting_id == "huizen-meeting-19"


def test_normalize_meeting_document_relation_builds_document_reference() -> None:
    relation = normalize_meeting_document_relation(
        {"meeting_id": "19", "document": sample_document(3127)},
        municipality_slug=MUNICIPALITY,
        source_system_id=SOURCE_SYSTEM_ID,
    )

    assert relation is not None
    assert relation.id == "huizen-meeting-19-document-3127"
    assert relation.meeting_id == "huizen-meeting-19"
    assert relation.document_id == "huizen-document-3127"
    assert relation.document_source_id == "3127"
    assert relation.document_object_id == "333"
    assert relation.relation_type == "meeting_document"
    assert relation.source_path == "/meetings/19/documents"


def test_normalize_meeting_item_document_relation_builds_item_reference() -> None:
    relation = normalize_meeting_item_document_relation(
        {"meeting_id": "19", "meeting_item_id": "142", "document": sample_document(158)},
        municipality_slug=MUNICIPALITY,
        source_system_id=SOURCE_SYSTEM_ID,
    )

    assert relation is not None
    assert relation.id == "huizen-meeting-item-142-document-158"
    assert relation.meeting_id == "huizen-meeting-19"
    assert relation.meeting_item_id == "huizen-meeting-item-142"
    assert relation.document_id == "huizen-document-158"
    assert relation.relation_type == "meeting_item_document"
    assert relation.source_path == "/meetingitems/142/documents"


def test_deduplicates_meetings_and_items_by_stable_id() -> None:
    meetings = normalize_meetings(
        [sample_meeting(), sample_meeting()],
        municipality_slug=MUNICIPALITY,
        source_system_id=SOURCE_SYSTEM_ID,
    )
    items = normalize_meeting_items(
        [sample_meeting_item(), sample_meeting_item()],
        municipality_slug=MUNICIPALITY,
        source_system_id=SOURCE_SYSTEM_ID,
    )

    assert len(meetings) == 1
    assert len(items) == 1


def test_deduplicates_document_relations_by_stable_id() -> None:
    meeting_relations = normalize_meeting_document_relations(
        [
            {"meeting_id": "19", "document": sample_document(3127)},
            {"meeting_id": "19", "document": sample_document(3127)},
        ],
        municipality_slug=MUNICIPALITY,
        source_system_id=SOURCE_SYSTEM_ID,
    )
    item_relations = normalize_meeting_item_document_relations(
        [
            {"meeting_id": "19", "meeting_item_id": "142", "document": sample_document(158)},
            {"meeting_id": "19", "meeting_item_id": "142", "document": sample_document(158)},
        ],
        municipality_slug=MUNICIPALITY,
        source_system_id=SOURCE_SYSTEM_ID,
    )

    assert len(meeting_relations) == 1
    assert len(item_relations) == 1


def test_normalize_relation_harvest_returns_all_canonical_buckets() -> None:
    normalized = normalize_relation_harvest(
        {
            "meetings": [sample_meeting()],
            "meeting_items": [sample_meeting_item()],
            "meeting_documents": [{"meeting_id": "19", "document": sample_document(3127)}],
            "meeting_item_documents": [
                {"meeting_id": "19", "meeting_item_id": "142", "document": sample_document(158)}
            ],
        },
        municipality_slug=MUNICIPALITY,
        source_system_id=SOURCE_SYSTEM_ID,
    )

    assert [record.id for record in normalized["meetings"]] == ["huizen-meeting-19"]
    assert [record.id for record in normalized["meeting_items"]] == ["huizen-meeting-item-142"]
    assert [record.id for record in normalized["meeting_documents"]] == [
        "huizen-meeting-19-document-3127"
    ]
    assert [record.id for record in normalized["meeting_item_documents"]] == [
        "huizen-meeting-item-142-document-158"
    ]


def test_to_dict_returns_json_serializable_fields() -> None:
    meeting = normalize_meeting(
        sample_meeting(),
        municipality_slug=MUNICIPALITY,
        source_system_id=SOURCE_SYSTEM_ID,
    )

    assert meeting is not None
    assert meeting.to_dict()["id"] == "huizen-meeting-19"
    assert meeting.to_dict()["description"] == "Raadsvergadering 05 Jul 2018"
