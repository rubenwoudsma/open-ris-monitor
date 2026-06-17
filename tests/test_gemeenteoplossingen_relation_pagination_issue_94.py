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


class PagingSession:
    def __init__(self, pages: dict[tuple[str, int], list[dict]]) -> None:
        self.pages = pages
        self.calls: list[tuple[str, dict | None]] = []

    def get(self, url: str, params: dict | None = None, timeout: int = 30) -> FakeResponse:
        self.calls.append((url, params))
        offset = int((params or {}).get("offset", 0))
        records = self.pages.get((url, offset), [])
        if url.endswith("/meetingitems"):
            return FakeResponse({"result": {"meetingitems": records}})
        return FakeResponse({"result": {"documents": records}})


def test_fetch_meeting_documents_walks_all_relation_pages() -> None:
    session = PagingSession(
        {
            ("https://example.test/api/v2/meetings/19/documents", 0): [
                {"id": index} for index in range(100)
            ],
            ("https://example.test/api/v2/meetings/19/documents", 100): [{"id": 100}],
        }
    )
    connector = GemeenteOplossingenConnector("https://example.test/api/v2/", session=session)

    documents = connector.fetch_meeting_documents(19)

    assert len(documents) == 101
    assert documents[-1] == {"id": 100}
    assert session.calls == [
        ("https://example.test/api/v2/meetings/19/documents", {"limit": 100, "offset": 0}),
        ("https://example.test/api/v2/meetings/19/documents", {"limit": 100, "offset": 100}),
    ]


def test_fetch_meeting_item_documents_walks_all_relation_pages() -> None:
    session = PagingSession(
        {
            ("https://example.test/api/v2/meetingitems/101/documents", 0): [
                {"id": index} for index in range(100)
            ],
            ("https://example.test/api/v2/meetingitems/101/documents", 100): [{"id": 100}],
        }
    )
    connector = GemeenteOplossingenConnector("https://example.test/api/v2/", session=session)

    documents = connector.fetch_meeting_item_documents(101)

    assert len(documents) == 101
    assert documents[-1] == {"id": 100}


def test_fetch_meeting_items_walks_all_relation_pages() -> None:
    session = PagingSession(
        {
            ("https://example.test/api/v2/meetings/19/meetingitems", 0): [
                {"id": index} for index in range(100)
            ],
            ("https://example.test/api/v2/meetings/19/meetingitems", 100): [{"id": 100}],
        }
    )
    connector = GemeenteOplossingenConnector("https://example.test/api/v2/", session=session)

    items = connector.fetch_meeting_items(19)

    assert len(items) == 101
    assert items[-1] == {"id": 100}
