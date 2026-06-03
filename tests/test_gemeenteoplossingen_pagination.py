from __future__ import annotations

from open_ris_monitor.connectors.gemeenteoplossingen import GemeenteOplossingenConnector


class FakeConnector(GemeenteOplossingenConnector):
    def __init__(self) -> None:
        super().__init__(base_url="https://example.test/api/v2/")
        self.pages: list[tuple[int, int]] = []
        self.meeting_session_pages: list[tuple[int, int]] = []

    def fetch_document_count(self) -> int:
        return 5

    def fetch_documents_page(self, *, limit: int, offset: int):
        self.pages.append((limit, offset))
        records = []
        for document_id in range(offset + 1, min(offset + limit, 5) + 1):
            records.append({"id": document_id, "description": f"Document {document_id}"})
        return records

    def fetch_meeting_session_count(self) -> int:
        return 9

    def fetch_meeting_sessions_page(self, *, limit: int, offset: int):
        self.meeting_session_pages.append((limit, offset))
        records = []
        for session_id in range(offset + 1, min(offset + limit, 9) + 1):
            records.append({"id": session_id, "container": {"meeting": {"id": session_id}}})
        return records


def test_fetch_all_documents_uses_pagination() -> None:
    connector = FakeConnector()

    documents = connector.fetch_all_documents(batch_size=2)

    assert [document["id"] for document in documents] == [1, 2, 3, 4, 5]
    assert connector.pages == [(2, 0), (2, 2), (1, 4)]


def test_fetch_all_documents_respects_max_documents() -> None:
    connector = FakeConnector()

    documents = connector.fetch_all_documents(batch_size=2, max_documents=3)

    assert [document["id"] for document in documents] == [1, 2, 3]
    assert connector.pages == [(2, 0), (1, 2)]


def test_fetch_latest_documents_uses_tail_offset() -> None:
    connector = FakeConnector()

    documents = connector.fetch_latest_documents(limit=2)

    assert [document["id"] for document in documents] == [4, 5]
    assert connector.pages == [(2, 3)]


def test_fetch_latest_meeting_sessions_uses_tail_offset() -> None:
    connector = FakeConnector()

    sessions = connector.fetch_latest_meeting_sessions(limit=3)

    assert [session["id"] for session in sessions] == [7, 8, 9]
    assert connector.meeting_session_pages == [(3, 6)]
