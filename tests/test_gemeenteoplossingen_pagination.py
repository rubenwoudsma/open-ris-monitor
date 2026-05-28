from __future__ import annotations

from open_ris_monitor.connectors.gemeenteoplossingen import GemeenteOplossingenConnector


class FakeConnector(GemeenteOplossingenConnector):
    def __init__(self) -> None:
        super().__init__(base_url="https://example.test/api/v2/")
        self.pages: list[tuple[int, int]] = []

    def fetch_document_count(self) -> int:
        return 5

    def fetch_documents_page(self, *, limit: int, offset: int):
        self.pages.append((limit, offset))
        records = []
        for document_id in range(offset + 1, min(offset + limit, 5) + 1):
            records.append({"id": document_id, "description": f"Document {document_id}"})
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
