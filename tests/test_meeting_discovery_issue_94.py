from __future__ import annotations

import requests

from open_ris_monitor.connectors.gemeenteoplossingen import GemeenteOplossingenConnector


class FakeResponse:
    def __init__(self, payload: dict | None = None, status_code: int = 200) -> None:
        self.payload = payload or {}
        self.status_code = status_code
        self.headers: dict[str, str] = {}
        self.url = "https://example.test/response"

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            error = requests.HTTPError(f"HTTP {self.status_code}")
            error.response = self
            raise error

    def json(self) -> dict:
        return self.payload


class MeetingDiscoverySession:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict | None]] = []

    def get(self, url: str, params: dict | None = None, timeout: int = 30) -> FakeResponse:
        self.calls.append((url, params))
        assert "meetingsessions" not in url

        offset = int((params or {}).get("offset", 0))
        limit = int((params or {}).get("limit", 100))
        meetings = [
            {"id": 10, "date": "2026-06-01T19:30:00"},
            {"id": 11, "date": "2026-06-02T19:30:00"},
            {"id": 12, "date": "2026-06-03T19:30:00"},
        ]
        if params and params.get("date_from") == "2026-06-02":
            meetings = meetings[1:]
        page = meetings[offset : offset + limit]
        return FakeResponse({"result": {"totalCount": len(meetings), "meetings": page}})


def test_fetch_latest_meeting_sessions_uses_documented_meetings_endpoint() -> None:
    session = MeetingDiscoverySession()
    connector = GemeenteOplossingenConnector("https://example.test/api/v2/", session=session)

    sessions = connector.fetch_latest_meeting_sessions(2)

    assert [session["container"]["meeting"]["id"] for session in sessions] == [11, 12]
    assert session.calls == [
        ("https://example.test/api/v2/meetings", {"limit": 1, "offset": 0}),
        ("https://example.test/api/v2/meetings", {"limit": 2, "offset": 1}),
    ]


def test_fetch_all_meetings_supports_documented_date_filters() -> None:
    session = MeetingDiscoverySession()
    connector = GemeenteOplossingenConnector("https://example.test/api/v2/", session=session)

    meetings = connector.fetch_all_meetings(batch_size=1, date_from="2026-06-02")

    assert [meeting["id"] for meeting in meetings] == [11, 12]
    assert session.calls == [
        (
            "https://example.test/api/v2/meetings",
            {"limit": 1, "offset": 0, "date_from": "2026-06-02"},
        ),
        (
            "https://example.test/api/v2/meetings",
            {"limit": 1, "offset": 0, "date_from": "2026-06-02"},
        ),
        (
            "https://example.test/api/v2/meetings",
            {"limit": 1, "offset": 1, "date_from": "2026-06-02"},
        ),
    ]


def test_legacy_meeting_sessions_remain_explicit_fallback_only() -> None:
    class LegacySession:
        def __init__(self) -> None:
            self.calls: list[tuple[str, dict | None]] = []

        def get(self, url: str, params: dict | None = None, timeout: int = 30) -> FakeResponse:
            self.calls.append((url, params))
            return FakeResponse({"result": {"totalCount": 1, "meetingsessions": [{"id": 99}]}})

    session = LegacySession()
    connector = GemeenteOplossingenConnector("https://example.test/api/v2/", session=session)

    legacy_sessions = connector.fetch_latest_legacy_meeting_sessions(1)

    assert legacy_sessions == [{"id": 99}]
    assert session.calls == [
        ("https://example.test/api/v2/meetingsessions", {"limit": 1, "offset": 0}),
        ("https://example.test/api/v2/meetingsessions", {"limit": 1, "offset": 0}),
    ]
