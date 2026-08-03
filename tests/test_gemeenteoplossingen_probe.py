from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from open_ris_monitor.diagnostics import gemeenteoplossingen_probe as probe_module


class ProbeResponse:
    def __init__(
        self,
        *,
        status_code: int = 200,
        content_type: str = "application/json",
        body: bytes = b'{"result":{"documents":[]}}',
        url: str = "https://example.test/api/v2/documents?limit=1&offset=0",
    ) -> None:
        self.status_code = status_code
        self.headers = {"Content-Type": content_type, "Server": "test-server"}
        self.content = body
        self.encoding = "utf-8"
        self.url = url
        self.history: list[Any] = []
        self.closed = False

    def iter_content(self, chunk_size: int = 512):
        yield self.content[:chunk_size]

    def close(self) -> None:
        self.closed = True


class ProbeSession:
    def __init__(self, response: ProbeResponse) -> None:
        self.response = response
        self.calls: list[dict[str, Any]] = []

    def get(self, url: str, **kwargs: Any) -> ProbeResponse:
        self.calls.append({"url": url, **kwargs})
        self.response.url = url
        return self.response


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def test_resolves_known_ids_and_builds_relation_probe_matrix(tmp_path: Path) -> None:
    _write_jsonl(tmp_path / "documents.jsonl", [{"source_id": "26380"}])
    _write_jsonl(tmp_path / "meetings.jsonl", [{"source_id": "1220"}])
    _write_jsonl(tmp_path / "meeting_items.jsonl", [{"source_id": "14668"}])

    ids = probe_module.resolve_probe_ids(tmp_path)
    matrix = probe_module.build_probe_matrix(ids, scope="full")
    names = {item["name"] for item in matrix}

    assert ids == {
        "document_id": "26380",
        "meeting_id": "1220",
        "meeting_item_id": "14668",
    }
    assert {
        "document_detail",
        "document_download_range",
        "meeting_documents",
        "meeting_items",
        "meeting_item_documents",
    }.issubset(names)


def test_download_probe_reads_only_one_bounded_chunk() -> None:
    response = ProbeResponse(content_type="application/pdf", body=b"x" * 2048)
    session = ProbeSession(response)

    result = probe_module.run_single_probe(
        session=session,  # type: ignore[arg-type]
        base_url="https://example.test/api/v2/",
        probe={
            "name": "document_download_range",
            "path": "documents/1/download",
            "download_probe": True,
        },
        user_agent_label="project",
        user_agent="OpenRISMonitor/test",
        timeout_seconds=5,
    )

    assert result["bytes_read"] == 512
    assert result["category"] == "ok_non_json"
    assert session.calls[0]["headers"]["Range"] == "bytes=0-0"
    assert session.calls[0]["stream"] is True
    assert response.closed is True


def test_probe_compares_project_and_browser_user_agents_without_harvest_fallback(
    tmp_path: Path, monkeypatch
) -> None:
    response = ProbeResponse()
    session = ProbeSession(response)
    monkeypatch.setattr(
        probe_module,
        "load_municipality_config",
        lambda _: {
            "source_system": {
                "base_url": "https://example.test/api/v2/",
                "user_agent": "OpenRISMonitor/test",
            }
        },
    )

    report = probe_module.run_probe(
        "huizen",
        public_dir=tmp_path,
        include_browser_user_agent=True,
        session=session,  # type: ignore[arg-type]
    )

    labels = {item["user_agent"] for item in report["results"]}
    assert labels == {"project", "browser_diagnostic"}
    assert report["diagnostic_only"] is True
    assert report["request_count"] == 14
    assert all(call["headers"]["Accept"] == "application/json" for call in session.calls)


def test_core_scope_is_bounded_and_skips_object_relation_probes(tmp_path: Path, monkeypatch) -> None:
    _write_jsonl(tmp_path / "documents.jsonl", [{"source_id": "26380"}])
    _write_jsonl(tmp_path / "meetings.jsonl", [{"source_id": "1220"}])
    _write_jsonl(tmp_path / "meeting_items.jsonl", [{"source_id": "14668"}])
    response = ProbeResponse()
    session = ProbeSession(response)
    monkeypatch.setattr(
        probe_module,
        "load_municipality_config",
        lambda _: {
            "source_system": {
                "base_url": "https://example.test/api/v2/",
                "user_agent": "OpenRISMonitor/test",
            }
        },
    )

    report = probe_module.run_probe(
        "huizen",
        public_dir=tmp_path,
        include_browser_user_agent=False,
        scope="core",
        session=session,  # type: ignore[arg-type]
    )

    assert report["scope"] == "core"
    assert report["request_count"] == 7
    assert "document_detail" not in {item["name"] for item in report["results"]}


def test_additional_base_url_is_explicit_and_diagnostic_only(tmp_path: Path, monkeypatch) -> None:
    response = ProbeResponse()
    session = ProbeSession(response)
    monkeypatch.setattr(
        probe_module,
        "load_municipality_config",
        lambda _: {
            "source_system": {
                "base_url": "https://example.test/api/v2/",
                "user_agent": "OpenRISMonitor/test",
            }
        },
    )

    report = probe_module.run_probe(
        "huizen",
        public_dir=tmp_path,
        include_browser_user_agent=False,
        scope="core",
        additional_base_urls=["https://example.test/api/v1/"],
        session=session,  # type: ignore[arg-type]
    )

    assert report["request_count"] == 14
    assert {item["base_url_label"] for item in report["results"]} == {
        "configured",
        "additional_1",
    }
    assert report["diagnostic_only"] is True


def test_html_404_probe_is_classified_as_access_control_page() -> None:
    response = ProbeResponse(
        status_code=404,
        content_type="text/html",
        body=b"<html>Toegang geweigerd: foutcode test</html>",
    )
    session = ProbeSession(response)

    result = probe_module.run_single_probe(
        session=session,  # type: ignore[arg-type]
        base_url="https://example.test/api/v2/",
        probe={"name": "documents", "path": "documents"},
        user_agent_label="project",
        user_agent="OpenRISMonitor/test",
        timeout_seconds=5,
    )

    assert result["category"] == "html_response"
