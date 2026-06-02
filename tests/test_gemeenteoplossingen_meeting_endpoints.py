from __future__ import annotations

import requests

from open_ris_monitor.connectors.gemeenteoplossingen import GemeenteOplossingenConnector


class FakeResponse:
    def __init__(self, payload: dict | None = None, status_code: int = 200) -> None:
        self.payload = payload or {}
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            error = requests.HTTPError(f"HTTP {self.status_code}")
            error.response = self
            raise error

    def json(self) -> dict:
        return self.payload


class FakeSession:
    def __init__(self, responses: dict[str, FakeResponse]) -> None:
        self.responses = responses
        self.calls: list[tuple[str, dict | None]] = []

    def get(self, url: str, params: dict | None = None, timeout: int = 30) -> FakeResponse:
        self.calls.append((url, params))
        return self.responses[url]


def test_fetch_meeting_sessions_page_calls_meetingsessions_endpoint() -> None:
    session = FakeSession(
        {
            "https://example.test/api/v2/meetingsessions": FakeResponse(
                {"result": {"meetingsessions": [{"id": 1}, {"id": 2}]}}
            )
        }
    )
    connector = GemeenteOplossingenConnector("https://example.test/api/v2/", session=session)

    records = connector.fetch_meeting_sessions_page(limit=25, offset=50)

    assert records == [{"id": 1}, {"id": 2}]
    assert session.calls == [
        ("https://example.test/api/v2/meetingsessions", {"limit": 25, "offset": 50})
    ]


def test_fetch_meeting_returns_meeting_from_wrapped_result() -> None:
    session = FakeSession(
        {
            "https://example.test/api/v2/meetings/19": FakeResponse(
                {"result": {"meeting": {"id": 19, "description": "Raadsvergadering"}}}
            )
        }
    )
    connector = GemeenteOplossingenConnector("https://example.test/api/v2/", session=session)

    assert connector.fetch_meeting(19) == {"id": 19, "description": "Raadsvergadering"}


def test_fetch_meeting_returns_none_for_404() -> None:
    session = FakeSession(
        {"https://example.test/api/v2/meetings/404": FakeResponse(status_code=404)}
    )
    connector = GemeenteOplossingenConnector("https://example.test/api/v2/", session=session)

    assert connector.fetch_meeting(404) is None


def test_fetch_meeting_items_calls_nested_endpoint() -> None:
    session = FakeSession(
        {
            "https://example.test/api/v2/meetings/19/meetingitems": FakeResponse(
                {"result": {"meetingitems": [{"id": 101, "description": "Opening"}]}}
            )
        }
    )
    connector = GemeenteOplossingenConnector("https://example.test/api/v2/", session=session)

    assert connector.fetch_meeting_items(19) == [{"id": 101, "description": "Opening"}]


def test_fetch_meeting_documents_calls_nested_endpoint() -> None:
    session = FakeSession(
        {
            "https://example.test/api/v2/meetings/19/documents": FakeResponse(
                {"result": {"documents": [{"id": 201, "description": "Agenda"}]}}
            )
        }
    )
    connector = GemeenteOplossingenConnector("https://example.test/api/v2/", session=session)

    assert connector.fetch_meeting_documents(19) == [{"id": 201, "description": "Agenda"}]


def test_fetch_meeting_item_documents_calls_meetingitem_documents_endpoint() -> None:
    session = FakeSession(
        {
            "https://example.test/api/v2/meetingitems/101/documents": FakeResponse(
                {"result": {"documents": [{"id": 301, "description": "Bijlage"}]}}
            )
        }
    )
    connector = GemeenteOplossingenConnector("https://example.test/api/v2/", session=session)

    assert connector.fetch_meeting_item_documents(101) == [{"id": 301, "description": "Bijlage"}]


def test_fetch_meeting_sessions_validates_limit_and_offset() -> None:
    connector = GemeenteOplossingenConnector("https://example.test/api/v2/")

    try:
        connector.fetch_meeting_sessions_page(limit=0, offset=0)
    except ValueError as error:
        assert "limit" in str(error)
    else:
        raise AssertionError("Expected ValueError for invalid limit")

    try:
        connector.fetch_meeting_sessions_page(limit=1, offset=-1)
    except ValueError as error:
        assert "offset" in str(error)
    else:
        raise AssertionError("Expected ValueError for invalid offset")
