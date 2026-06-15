from __future__ import annotations

from typing import Any

from open_ris_monitor.connectors.gemeenteoplossingen import GemeenteOplossingenConnector
from open_ris_monitor.pipeline.relations import collect_raw_relation_harvest


class FakeRelationConnector:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def fetch_meetings_page(self, *, limit: int, offset: int) -> list[dict[str, Any]]:
        self.calls.append(("meetings", {"limit": limit, "offset": offset}))
        if offset == 0:
            return [{"id": 10, "description": "Raadsvergadering"}]
        return []

    def fetch_latest_meetings(self, limit: int) -> list[dict[str, Any]]:
        self.calls.append(("latest_meetings", {"limit": limit}))
        return [{"id": 20, "description": "Laatste vergadering"}]

    def fetch_meeting_sessions_page(self, *, limit: int, offset: int) -> list[dict[str, Any]]:
        raise AssertionError("/meetingsessions must not be used for issue #69 relation harvest")

    def fetch_latest_meeting_sessions(self, limit: int) -> list[dict[str, Any]]:
        raise AssertionError("/meetingsessions must not be used for issue #69 relation harvest")

    def fetch_meeting(self, meeting_id: int | str) -> dict[str, Any] | None:
        raise AssertionError("meeting list records should be used directly")

    def fetch_meeting_items(self, meeting_id: int | str) -> list[dict[str, Any]]:
        self.calls.append(("meetingitems", {"meeting_id": meeting_id}))
        return [{"id": 100, "title": "Opening"}]

    def fetch_meeting_documents(self, meeting_id: int | str) -> list[dict[str, Any]]:
        self.calls.append(("meeting_documents", {"meeting_id": meeting_id}))
        return [{"id": 1000, "fileName": "agenda.pdf"}]

    def fetch_meeting_item_documents(self, meeting_item_id: int | str) -> list[dict[str, Any]]:
        self.calls.append(("meeting_item_documents", {"meeting_item_id": meeting_item_id}))
        return [{"id": 1001, "fileName": "voorstel.pdf"}]


def test_relation_harvest_uses_documented_meetings_endpoint_not_meetingsessions() -> None:
    connector = FakeRelationConnector()

    result = collect_raw_relation_harvest(
        connector,
        meeting_scan_limit=1,
        meeting_session_batch_size=100,
        meeting_item_limit=10,
        meeting_session_scan_mode="full",
    )

    assert result["meeting_scan_source"] == "meetings"
    assert result["meeting_sessions"] == []
    assert result["candidate_meeting_ids"] == ["10"]
    assert result["meetings"] == [{"id": 10, "description": "Raadsvergadering"}]
    assert result["meeting_items"] == [
        {"id": 100, "title": "Opening", "meeting_id": "10"}
    ]
    assert result["meeting_documents"] == [
        {"meeting_id": "10", "document": {"id": 1000, "fileName": "agenda.pdf"}}
    ]
    assert result["meeting_item_documents"] == [
        {
            "meeting_id": "10",
            "meeting_item_id": "100",
            "document": {"id": 1001, "fileName": "voorstel.pdf"},
        }
    ]
    assert ("meetings", {"limit": 1, "offset": 0}) in connector.calls


def test_latest_relation_harvest_uses_latest_meetings_not_latest_meetingsessions() -> None:
    connector = FakeRelationConnector()

    result = collect_raw_relation_harvest(
        connector,
        meeting_scan_limit=1,
        meeting_session_scan_mode="latest",
    )

    assert result["candidate_meeting_ids"] == ["20"]
    assert ("latest_meetings", {"limit": 1}) in connector.calls


class FakeResponse:
    def __init__(self, payload: dict[str, Any], *, url: str = "https://example.invalid") -> None:
        self._payload = payload
        self.status_code = 200
        self.url = url
        self.headers: dict[str, str] = {}

    def json(self) -> dict[str, Any]:
        return self._payload

    def raise_for_status(self) -> None:
        return None


class FakeSession:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any] | None]] = []

    def get(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        timeout: int | float | None = None,
    ) -> FakeResponse:
        self.calls.append((url, params))
        return FakeResponse(
            {"result": {"totalCount": 917, "meetings": [{"id": 1}] }},
            url=url,
        )


def test_gemeenteoplossingen_connector_fetches_documented_meetings_page() -> None:
    session = FakeSession()
    connector = GemeenteOplossingenConnector(
        "https://ris.example.invalid/api/v2/",
        session=session,  # type: ignore[arg-type]
    )

    assert connector.fetch_meetings_page(limit=100, offset=300) == [{"id": 1}]
    assert session.calls == [
        (
            "https://ris.example.invalid/api/v2/meetings",
            {"limit": 100, "offset": 300},
        )
    ]

class LegacyOnlyRelationConnector:
    def __init__(self) -> None:
        self.calls: list[tuple[str, Any]] = []

    def fetch_meeting_sessions_page(self, *, limit: int, offset: int) -> list[dict[str, Any]]:
        self.calls.append(("meetingsessions", {"limit": limit, "offset": offset}))
        sessions = [
            {"container": {"meeting": {"id": 10}}},
            {"container": {"meeting": {"id": 20}}},
        ]
        return sessions[offset : offset + limit]

    def fetch_latest_meeting_sessions(self, limit: int) -> list[dict[str, Any]]:
        self.calls.append(("latest_meetingsessions", limit))
        return [{"container": {"meeting": {"id": 20}}}]

    def fetch_meeting(self, meeting_id: int | str) -> dict[str, Any] | None:
        self.calls.append(("meeting", str(meeting_id)))
        return {"id": meeting_id, "description": f"Meeting {meeting_id}"}

    def fetch_meeting_items(self, meeting_id: int | str) -> list[dict[str, Any]]:
        self.calls.append(("meetingitems", str(meeting_id)))
        return [{"id": 100, "title": "Opening"}]

    def fetch_meeting_documents(self, meeting_id: int | str) -> list[dict[str, Any]]:
        self.calls.append(("meeting_documents", str(meeting_id)))
        return []

    def fetch_meeting_item_documents(self, meeting_item_id: int | str) -> list[dict[str, Any]]:
        self.calls.append(("meeting_item_documents", str(meeting_item_id)))
        return []


def test_relation_harvest_keeps_legacy_connector_fallback_for_existing_tests() -> None:
    connector = LegacyOnlyRelationConnector()

    result = collect_raw_relation_harvest(
        connector,
        meeting_scan_limit=2,
        meeting_session_batch_size=2,
        meeting_item_limit=1,
    )

    assert result["meeting_scan_source"] == "meetingsessions"
    assert result["candidate_meeting_ids"] == ["10", "20"]
    assert result["meetings"][0]["id"] == "10"
    assert ("meetingsessions", {"limit": 2, "offset": 0}) in connector.calls
