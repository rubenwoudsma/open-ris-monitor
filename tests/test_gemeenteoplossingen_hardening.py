from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import requests

from open_ris_monitor.connectors.gemeenteoplossingen import (
    GemeenteOplossingenConnector,
    GemeenteOplossingenError,
    sanitize_url,
)
from open_ris_monitor.pipeline import run as pipeline_run


class Response:
    def __init__(
        self,
        *,
        status_code: int = 200,
        payload: Any = None,
        content_type: str = "application/json",
        body: bytes | None = None,
        url: str = "https://example.test/api/v2/documents?limit=1&offset=0",
        json_error: BaseException | None = None,
    ) -> None:
        self.status_code = status_code
        self.payload = payload
        self.headers = {"Content-Type": content_type}
        self.url = url
        self.encoding = "utf-8"
        self.history: tuple[Any, ...] = ()
        self.content = body if body is not None else json.dumps(payload).encode("utf-8")
        self.json_error = json_error

    def json(self) -> Any:
        if self.json_error is not None:
            raise self.json_error
        return self.payload


class Session:
    def __init__(self, responses: list[Response | BaseException]) -> None:
        self.responses = list(responses)
        self.calls: list[tuple[str, dict[str, Any] | None]] = []
        self.headers: dict[str, str] = {}

    def get(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        timeout: int = 30,
    ) -> Response:
        self.calls.append((url, params))
        response = self.responses.pop(0)
        if isinstance(response, BaseException):
            raise response
        return response


def connector_for(*responses: Response | BaseException, retry_attempts: int = 0) -> GemeenteOplossingenConnector:
    return GemeenteOplossingenConnector(
        "https://example.test/api/v2/",
        session=Session(list(responses)),  # type: ignore[arg-type]
        retry_attempts=retry_attempts,
        retry_backoff_seconds=0,
        sleep_func=lambda _: None,
    )


def test_normal_200_json_response_and_headers() -> None:
    session = Session(
        [Response(payload={"result": {"documents": [{"id": 1}]}})]
    )
    connector = GemeenteOplossingenConnector(
        "https://example.test/api/v2/",
        session=session,  # type: ignore[arg-type]
        retry_attempts=0,
    )

    assert connector.fetch_documents_page(limit=1, offset=0) == [{"id": 1}]
    assert session.headers["Accept"] == "application/json"
    assert session.headers["User-Agent"].startswith("OpenRISMonitor/")


def test_404_collection_is_diagnostic_and_not_retried_or_silently_fallbacked() -> None:
    session = Session(
        [
            Response(
                status_code=404,
                payload={"status": "ERROR", "code": 404, "messages": ["Not found"]},
            )
        ]
    )
    connector = GemeenteOplossingenConnector(
        "https://example.test/api/v2/",
        session=session,  # type: ignore[arg-type]
        retry_attempts=3,
    )

    with pytest.raises(GemeenteOplossingenError) as captured:
        connector.fetch_document_count()

    assert captured.value.category == "http_404"
    assert len(session.calls) == 1
    assert session.calls[0][0].endswith("/documents")


def test_base_url_trailing_slash_does_not_change_joined_endpoint() -> None:
    for base_url in ("https://example.test/api/v2", "https://example.test/api/v2/"):
        session = Session([Response(payload={"result": {"documents": []}})])
        connector = GemeenteOplossingenConnector(
            base_url,
            session=session,  # type: ignore[arg-type]
            retry_attempts=0,
        )
        connector.fetch_documents_page(limit=1, offset=0)
        assert session.calls[0][0] == "https://example.test/api/v2/documents"


def test_html_block_page_is_classified() -> None:
    connector = connector_for(
        Response(
            payload=None,
            content_type="text/html; charset=utf-8",
            body=b"<html><body>Toegang geweigerd: foutcode test</body></html>",
        )
    )

    with pytest.raises(GemeenteOplossingenError) as captured:
        connector.fetch_document_count()

    assert captured.value.category == "html_response"
    assert "Toegang geweigerd" in str(captured.value)




def test_404_html_block_page_is_not_treated_as_missing_resource() -> None:
    connector = connector_for(
        Response(
            status_code=404,
            payload=None,
            content_type="text/html; charset=utf-8",
            body=b"<html><body>Toegang geweigerd: foutcode test</body></html>",
            url="https://example.test/api/v2/meetings/123",
        )
    )

    with pytest.raises(GemeenteOplossingenError) as captured:
        connector.fetch_meeting(123)

    assert captured.value.category == "html_response"


def test_missing_result_envelope_keeps_endpoint_context() -> None:
    connector = connector_for(
        Response(payload={"status": "OK", "code": 200, "messages": []})
    )

    with pytest.raises(GemeenteOplossingenError) as captured:
        connector.fetch_document_count()

    assert captured.value.category == "unsupported_envelope"
    assert captured.value.url == "https://example.test/api/v2/documents?limit=1&offset=0"


def test_200_wrong_content_type_is_rejected() -> None:
    connector = connector_for(
        Response(payload={"result": {}}, content_type="text/plain")
    )

    with pytest.raises(GemeenteOplossingenError) as captured:
        connector.fetch_document_count()

    assert captured.value.category == "unexpected_content_type"


def test_malformed_json_is_rejected() -> None:
    connector = connector_for(
        Response(
            payload=None,
            body=b"{not valid json",
            json_error=ValueError("invalid JSON"),
        )
    )

    with pytest.raises(GemeenteOplossingenError) as captured:
        connector.fetch_document_count()

    assert captured.value.category == "malformed_json"


def test_timeout_and_connection_error_are_distinct() -> None:
    timeout_connector = connector_for(requests.Timeout("slow"))
    with pytest.raises(GemeenteOplossingenError) as timeout_error:
        timeout_connector.fetch_document_count()
    assert timeout_error.value.category == "timeout"

    connection_connector = connector_for(requests.ConnectionError("offline"))
    with pytest.raises(GemeenteOplossingenError) as connection_error:
        connection_connector.fetch_document_count()
    assert connection_error.value.category == "connection_error"


def test_result_model_envelope_is_supported() -> None:
    connector = connector_for(
        Response(payload={"status": "OK", "code": 200, "result": {"model": [{"id": 8}]}})
    )

    assert connector.fetch_documents_page(limit=1, offset=0) == [{"id": 8}]


@pytest.mark.parametrize("value", [None, True, -1, "not-a-number"])
def test_missing_or_invalid_total_count_fails(value: Any) -> None:
    result: dict[str, Any] = {"documents": []}
    if value is not None:
        result["totalCount"] = value
    connector = connector_for(Response(payload={"result": result}))

    with pytest.raises(GemeenteOplossingenError) as captured:
        connector.fetch_document_count()

    assert captured.value.category == "invalid_total_count"


def test_incomplete_document_pagination_fails() -> None:
    connector = connector_for(
        Response(payload={"result": {"totalCount": 2, "documents": [{"id": 1}]}}),
        Response(payload={"result": {"documents": [{"id": 1}]}}),
    )

    with pytest.raises(GemeenteOplossingenError) as captured:
        connector.fetch_all_documents(batch_size=2)

    assert captured.value.category == "incomplete_pagination"


def test_url_and_body_preview_sanitizing() -> None:
    unsafe = "https://user:pass@example.test/api?token=secret&limit=1#fragment"
    assert sanitize_url(unsafe) == "https://example.test/api?token=%5BREDACTED%5D&limit=1"

    connector = connector_for(
        Response(
            status_code=403,
            payload=None,
            content_type="text/html",
            body=b"token=very-secret password=hunter2",
            url="https://example.test/api/v2/documents?token=very-secret&limit=1",
        )
    )
    with pytest.raises(GemeenteOplossingenError) as captured:
        connector.fetch_document_count()
    message = str(captured.value)
    assert "very-secret" not in message
    assert "hunter2" not in message
    assert "[REDACTED]" in message


class PipelineConnector:
    request_delay_seconds = 0.0

    def __init__(self, documents: list[dict[str, Any]], preflight_error: Exception | None = None) -> None:
        self.documents = documents
        self.preflight_error = preflight_error
        self.fetch_called = False

    def preflight(self) -> list[dict[str, Any]]:
        if self.preflight_error:
            raise self.preflight_error
        return [{"endpoint": "documents", "status": "ok"}]

    def fetch_latest_documents(self, limit: int) -> list[dict[str, Any]]:
        self.fetch_called = True
        return self.documents[:limit]

    def fetch_all_documents(self, *, batch_size: int, max_documents: int | None):
        self.fetch_called = True
        return self.documents[:max_documents] if max_documents else self.documents

    def build_document_download_url(self, document_id: int | str) -> str:
        return f"https://example.test/documents/{document_id}/download"

    def download_document(self, document_id: int | str) -> bytes:
        return b""


def pipeline_config() -> dict[str, Any]:
    return {
        "municipality": {"id": "gm0406"},
        "source_system": {"id": "test-go", "connector": "gemeenteoplossingen", "base_url": "https://example.test/api/v2/"},
    }


def sample_document() -> dict[str, Any]:
    return {
        "id": 25892,
        "objectId": 43243,
        "confidential": 0,
        "description": "Openbaar document",
        "documentTypeLabel": "Overig",
        "fileName": "openbaar.pdf",
        "fileSize": 62118,
        "publicationDate": {
            "date": "2026-05-19 00:00:00.000000",
            "timezone": "Europe/Amsterdam",
            "timezone_type": 3,
        },
    }


def test_preflight_failure_leaves_existing_output_untouched(tmp_path: Path, monkeypatch) -> None:
    raw_dir = tmp_path / "raw"
    public_dir = tmp_path / "public"
    public_dir.mkdir()
    original = '{"id":"existing"}\n'
    (public_dir / "documents.jsonl").write_text(original, encoding="utf-8")
    connector = PipelineConnector(
        [sample_document()],
        preflight_error=GemeenteOplossingenError("blocked", category="http_404"),
    )
    monkeypatch.setattr(pipeline_run, "load_municipality_config", lambda _: pipeline_config())
    monkeypatch.setattr(pipeline_run, "build_connector", lambda _: connector)

    with pytest.raises(GemeenteOplossingenError, match="blocked"):
        pipeline_run.run_harvest(
            municipality="huizen",
            mode="latest",
            limit=1,
            batch_size=1,
            max_documents=None,
            enrich_checksums=False,
            checksum_max_documents=0,
            raw_dir=raw_dir,
            public_dir=public_dir,
        )

    assert connector.fetch_called is False
    assert (public_dir / "documents.jsonl").read_text(encoding="utf-8") == original
    assert not raw_dir.exists()


def test_zero_upstream_result_does_not_overwrite_existing_output(tmp_path: Path, monkeypatch) -> None:
    raw_dir = tmp_path / "raw"
    public_dir = tmp_path / "public"
    public_dir.mkdir()
    original = '{"id":"existing"}\n'
    (public_dir / "documents.jsonl").write_text(original, encoding="utf-8")
    connector = PipelineConnector([])
    monkeypatch.setattr(pipeline_run, "load_municipality_config", lambda _: pipeline_config())
    monkeypatch.setattr(pipeline_run, "build_connector", lambda _: connector)

    with pytest.raises(RuntimeError, match="zero documents"):
        pipeline_run.run_harvest(
            municipality="huizen",
            mode="latest",
            limit=1,
            batch_size=1,
            max_documents=None,
            enrich_checksums=False,
            checksum_max_documents=0,
            raw_dir=raw_dir,
            public_dir=public_dir,
            perform_preflight=False,
        )

    assert (public_dir / "documents.jsonl").read_text(encoding="utf-8") == original
    assert not raw_dir.exists()


def test_successful_mocked_end_to_end_harvest(tmp_path: Path, monkeypatch) -> None:
    raw_dir = tmp_path / "raw"
    public_dir = tmp_path / "public"
    connector = PipelineConnector([sample_document()])
    monkeypatch.setattr(pipeline_run, "load_municipality_config", lambda _: pipeline_config())
    monkeypatch.setattr(pipeline_run, "build_connector", lambda _: connector)

    harvest = pipeline_run.run_harvest(
        municipality="huizen",
        mode="latest",
        limit=1,
        batch_size=1,
        max_documents=None,
        enrich_checksums=False,
        checksum_max_documents=0,
        raw_dir=raw_dir,
        public_dir=public_dir,
    )

    assert harvest.status == "success"
    assert (raw_dir / "documents.json").exists()
    assert len((public_dir / "documents.jsonl").read_text(encoding="utf-8").splitlines()) == 1
    latest = json.loads((public_dir / "latest.json").read_text(encoding="utf-8"))
    assert latest["dataset_documents_total"] == 1
    assert latest["documents_seen_in_run"] == 1
