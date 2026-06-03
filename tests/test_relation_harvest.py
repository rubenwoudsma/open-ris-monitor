from __future__ import annotations

from typing import Any

import pytest
import requests

from open_ris_monitor.pipeline.relations import (
    collect_raw_relation_harvest,
    extract_meeting_id_from_session,
    fetch_meeting_sessions,
    stable_unique,
)


class FakeRelationConnector:
    def __init__(self) -> None:
        self.session_pages = {
            0: [
                {"id": "s1", "container": {"meeting": {"id": 19}}},
                {"id": "s2", "container": {"meeting": {"id": 19}}},
            ],
            2: [
                {"id": "s3", "container": {"meeting": {"id": 20}}},
                {"id": "s4", "container": {"meeting": {"id": 404}}},
            ],
        }
        self.calls: list[tuple[str, Any]] = []

    def fetch_meeting_sessions_page(self, *, limit: int, offset: int) -> list[dict[str, Any]]:
        self.calls.append(("sessions", {"limit": limit, "offset": offset}))
        return self.session_pages.get(offset, [])[:limit]

    def fetch_meeting(self, meeting_id: int | str) -> dict[str, Any] | None:
        self.calls.append(("meeting", str(meeting_id)))
        if str(meeting_id) == "404":
            return None
        return {"id": int(meeting_id), "description": f"Meeting {meeting_id}"}

    def fetch_meeting_items(self, meeting_id: int | str) -> list[dict[str, Any]]:
        self.calls.append(("items", str(meeting_id)))
        return [
            {"id": f"{meeting_id}1", "description": f"Item {meeting_id}.1"},
            {"id": f"{meeting_id}2", "description": f"Item {meeting_id}.2"},
        ]

    def fetch_meeting_documents(self, meeting_id: int | str) -> list[dict[str, Any]]:
        self.calls.append(("meeting_documents", str(meeting_id)))
        return [{"id": f"d{meeting_id}", "description": "Agenda"}]

    def fetch_meeting_item_documents(self, meeting_item_id: int | str) -> list[dict[str, Any]]:
        self.calls.append(("item_documents", str(meeting_item_id)))
        return [{"id": f"doc-{meeting_item_id}", "description": "Bijlage"}]


def test_extract_meeting_id_from_session_uses_container_meeting_id() -> None:
    assert extract_meeting_id_from_session({"container": {"meeting": {"id": 19}}}) == "19"


def test_extract_meeting_id_from_session_ignores_missing_meeting() -> None:
    assert extract_meeting_id_from_session({"container": {}}) is None


def test_stable_unique_preserves_first_seen_order() -> None:
    assert stable_unique(["19", "20", "19", "21"]) == ["19", "20", "21"]


def test_fetch_meeting_sessions_uses_bounded_pagination() -> None:
    connector = FakeRelationConnector()

    sessions = fetch_meeting_sessions(connector, scan_limit=3, batch_size=2)

    assert [session["id"] for session in sessions] == ["s1", "s2", "s3"]
    assert connector.calls == [
        ("sessions", {"limit": 2, "offset": 0}),
        ("sessions", {"limit": 1, "offset": 2}),
    ]


def test_collect_raw_relation_harvest_collects_raw_records_and_skips_missing_meetings() -> None:
    connector = FakeRelationConnector()

    result = collect_raw_relation_harvest(
        connector,
        meeting_scan_limit=4,
        meeting_session_batch_size=2,
        meeting_item_limit=3,
    )

    assert result["candidate_meeting_ids"] == ["19", "20", "404"]
    assert result["skipped_meeting_ids"] == ["404"]
    assert result["relation_errors"] == []
    assert [meeting["id"] for meeting in result["meetings"]] == [19, 20]
    assert len(result["meeting_items"]) == 3
    assert len(result["meeting_documents"]) == 2
    assert len(result["meeting_item_documents"]) == 3
    assert result["summary"] == {
        "meeting_sessions_seen": 4,
        "candidate_meetings_seen": 3,
        "meetings_seen": 2,
        "meetings_skipped": 1,
        "relation_errors_seen": 0,
        "meeting_items_seen": 3,
        "meeting_document_relations_seen": 2,
        "meeting_item_document_relations_seen": 3,
    }


def test_collect_raw_relation_harvest_skips_transient_meeting_fetch_errors() -> None:
    class TimeoutRelationConnector(FakeRelationConnector):
        def fetch_meeting(self, meeting_id: int | str) -> dict[str, Any] | None:
            self.calls.append(("meeting", str(meeting_id)))
            if str(meeting_id) == "20":
                raise requests.ConnectTimeout("meeting timeout")
            return super().fetch_meeting(meeting_id)

    connector = TimeoutRelationConnector()

    result = collect_raw_relation_harvest(
        connector,
        meeting_scan_limit=4,
        meeting_session_batch_size=2,
        meeting_item_limit=3,
    )

    assert result["skipped_meeting_ids"] == ["20", "404"]
    assert [meeting["id"] for meeting in result["meetings"]] == [19]
    assert result["relation_errors"] == [
        {
            "scope": "meeting",
            "meeting_id": "20",
            "error": {"type": "ConnectTimeout", "message": "meeting timeout"},
        }
    ]
    assert result["summary"]["relation_errors_seen"] == 1


def test_collect_raw_relation_harvest_skips_transient_item_document_errors() -> None:
    class ItemDocumentTimeoutRelationConnector(FakeRelationConnector):
        def fetch_meeting_item_documents(self, meeting_item_id: int | str) -> list[dict[str, Any]]:
            self.calls.append(("item_documents", str(meeting_item_id)))
            if str(meeting_item_id) == "191":
                raise requests.ReadTimeout("item document timeout")
            return [{"id": f"doc-{meeting_item_id}", "description": "Bijlage"}]

    connector = ItemDocumentTimeoutRelationConnector()

    result = collect_raw_relation_harvest(
        connector,
        meeting_scan_limit=2,
        meeting_session_batch_size=2,
        meeting_item_limit=2,
    )

    assert len(result["meeting_items"]) == 2
    assert len(result["meeting_item_documents"]) == 1
    assert result["relation_errors"] == [
        {
            "scope": "meeting_item_documents",
            "meeting_id": "19",
            "meeting_item_id": "191",
            "error": {"type": "ReadTimeout", "message": "item document timeout"},
        }
    ]
    assert result["summary"]["relation_errors_seen"] == 1


def test_collect_raw_relation_harvest_validates_meeting_item_limit() -> None:
    connector = FakeRelationConnector()

    with pytest.raises(ValueError, match="meeting_item_limit"):
        collect_raw_relation_harvest(
            connector,
            meeting_scan_limit=1,
            meeting_item_limit=0,
        )
