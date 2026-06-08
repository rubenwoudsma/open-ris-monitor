from __future__ import annotations

import requests
import pytest

from open_ris_monitor.connectors.gemeenteoplossingen import GemeenteOplossingenConnector


class FakeResponse:
    def __init__(self, status_code: int, payload: dict | None = None) -> None:
        self.status_code = status_code
        self._payload = payload or {"result": {"documents": []}}
        self.headers: dict[str, str] = {}
        self.url = "https://example.test/api/v2/documents"
        self.content = b"payload"

    def json(self) -> dict:
        return self._payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            error = requests.HTTPError(f"HTTP {self.status_code}")
            error.response = self  # type: ignore[assignment]
            raise error


class FakeSession:
    def __init__(self, responses: list[FakeResponse | BaseException]) -> None:
        self.responses = responses
        self.calls = 0

    def get(self, *args, **kwargs):
        self.calls += 1
        response = self.responses.pop(0)
        if isinstance(response, BaseException):
            raise response
        return response


def test_retries_temporary_503_and_returns_json() -> None:
    session = FakeSession(
        [
            FakeResponse(503),
            FakeResponse(200, {"result": {"documents": [{"id": 1}]}}),
        ]
    )
    sleeps: list[float] = []
    connector = GemeenteOplossingenConnector(
        "https://example.test/api/v2/",
        session=session,  # type: ignore[arg-type]
        retry_attempts=2,
        retry_backoff_seconds=0.1,
        sleep_func=sleeps.append,
    )

    documents = connector.fetch_documents_page(limit=10, offset=0)

    assert documents == [{"id": 1}]
    assert session.calls == 2
    assert sleeps == [0.1]


def test_retries_timeout_and_then_succeeds() -> None:
    session = FakeSession(
        [
            requests.Timeout("slow upstream"),
            FakeResponse(200, {"result": {"totalCount": 7}}),
        ]
    )
    sleeps: list[float] = []
    connector = GemeenteOplossingenConnector(
        "https://example.test/api/v2/",
        session=session,  # type: ignore[arg-type]
        retry_attempts=2,
        retry_backoff_seconds=0.25,
        sleep_func=sleeps.append,
    )

    assert connector.fetch_document_count() == 7
    assert session.calls == 2
    assert sleeps == [0.25]


def test_does_not_retry_404_for_absent_resource() -> None:
    session = FakeSession([FakeResponse(404)])
    connector = GemeenteOplossingenConnector(
        "https://example.test/api/v2/",
        session=session,  # type: ignore[arg-type]
        retry_attempts=3,
        sleep_func=lambda _: None,
    )

    assert connector.fetch_meeting(123) is None
    assert session.calls == 1


def test_raises_after_retry_budget_is_exhausted() -> None:
    session = FakeSession([FakeResponse(503), FakeResponse(503)])
    connector = GemeenteOplossingenConnector(
        "https://example.test/api/v2/",
        session=session,  # type: ignore[arg-type]
        retry_attempts=1,
        retry_backoff_seconds=0,
        sleep_func=lambda _: None,
    )

    with pytest.raises(requests.HTTPError):
        connector.fetch_document_count()

    assert session.calls == 2


def test_retry_after_header_controls_delay() -> None:
    first = FakeResponse(429)
    first.headers["Retry-After"] = "3"
    session = FakeSession([first, FakeResponse(200, {"result": {"totalCount": 1}})])
    sleeps: list[float] = []
    connector = GemeenteOplossingenConnector(
        "https://example.test/api/v2/",
        session=session,  # type: ignore[arg-type]
        retry_attempts=2,
        retry_backoff_seconds=0.1,
        sleep_func=sleeps.append,
    )

    assert connector.fetch_document_count() == 1
    assert sleeps == [3.0]
