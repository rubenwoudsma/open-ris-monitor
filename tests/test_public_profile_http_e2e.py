from __future__ import annotations

import json
import shutil
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from open_ris_monitor.analysis.generate_public_reports import generate_reports
from open_ris_monitor.exporters.validate_exports import validate_jsonl_file
from open_ris_monitor.pipeline import run as pipeline_run
from open_ris_monitor.pipeline.harvest_safety import protect_public_outputs
from open_ris_monitor.pipeline.promote_staged import promote_staged_directories


DOCUMENT = {
    "id": 158,
    "objectId": 333,
    "confidential": 0,
    "fileName": "openbaar-document.pdf",
    "documentTypeLabel": "Raadsvoorstel",
    "description": "Openbaar document",
    "fileSize": 1024,
    "publicationDate": {
        "date": "2026-07-16 00:00:00.000000",
        "timezone": "Europe/Amsterdam",
        "timezone_type": 3,
    },
}
MEETING = {
    "id": 19,
    "confidential": 0,
    "date": "2026-07-16",
    "description": "Raadsvergadering",
    "dmu": {"id": 14, "name": "Raadsvergadering", "sortOrder": 0},
    "location": "Raadzaal",
    "startTime": "20:00",
}
MEETING_ITEM = {
    "id": 142,
    "confidential": False,
    "description": "Bespreekpunt",
    "meeting": MEETING,
    "meeting_id": "19",
    "number": "5.2",
    "sortOrder": 11,
    "title": "Openbaar agendapunt",
}


def _envelope(field: str, records: list[dict[str, Any]], *, counted: bool = False) -> bytes:
    result: dict[str, Any] = {field: records}
    if counted:
        result["totalCount"] = len(records)
    payload = {"status": "OK", "code": 200, "messages": [], "result": result}
    return json.dumps(payload).encode("utf-8")


class ApiHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    requests_seen: list[str] = []

    def do_GET(self) -> None:  # noqa: N802 [stdlib callback name]
        path = urlparse(self.path).path
        type(self).requests_seen.append(self.path)
        routes = {
            "/api/v2/documents": _envelope("documents", [DOCUMENT], counted=True),
            "/api/v2/meetings": _envelope("meetings", [MEETING], counted=True),
            "/api/v2/meetings/19/documents": _envelope("documents", [DOCUMENT]),
            "/api/v2/meetings/19/meetingitems": _envelope(
                "meetingitems", [MEETING_ITEM]
            ),
            "/api/v2/meetingitems/142/documents": _envelope("documents", [DOCUMENT]),
        }
        body = routes.get(path)
        if body is None:
            body = json.dumps(
                {
                    "status": "ERROR",
                    "code": 404,
                    "messages": ["Not found"],
                    "result": {},
                }
            ).encode("utf-8")
            self.send_response(404)
        else:
            self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:
        return


def _config(base_url: str) -> dict[str, Any]:
    return {
        "municipality": {"id": "gm0406"},
        "source_system": {
            "id": "huizen-gemeenteoplossingen",
            "connector": "gemeenteoplossingen",
            "base_url": base_url,
            "timeout_seconds": 5,
            "retry_attempts": 0,
        },
    }


def test_public_profile_http_harvest_validates_and_promotes_atomically(
    tmp_path: Path, monkeypatch
) -> None:
    ApiHandler.requests_seen = []
    server = ThreadingHTTPServer(("127.0.0.1", 0), ApiHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_port}/api/v2/"

    target_public = tmp_path / "data" / "public"
    target_raw = tmp_path / "data" / "raw" / "latest"
    staged_public = tmp_path / "stage" / "public"
    staged_raw = tmp_path / "stage" / "raw" / "latest"
    target_public.mkdir(parents=True)
    (target_public / "sentinel.txt").write_text("existing", encoding="utf-8")
    shutil.copytree(target_public, staged_public)

    monkeypatch.setattr(pipeline_run, "load_municipality_config", lambda _: _config(base_url))
    try:
        harvest = pipeline_run.run_harvest(
            municipality="huizen",
            mode="latest",
            limit=1,
            batch_size=1,
            max_documents=None,
            enrich_checksums=False,
            checksum_max_documents=0,
            include_relations=True,
            meeting_scan_limit=1,
            meeting_session_batch_size=1,
            meeting_item_limit=1,
            raw_dir=staged_raw,
            public_dir=staged_public,
        )
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()

    assert harvest.status == "success"
    assert any(path.startswith("/api/v2/documents?") for path in ApiHandler.requests_seen)
    assert "/api/v2/meetings/19/documents?limit=100&offset=0" in ApiHandler.requests_seen
    assert "/api/v2/meetingitems/142/documents?limit=100&offset=0" in ApiHandler.requests_seen

    protect_public_outputs(
        target_public,
        staged_public,
        profile="public",
    )
    report = generate_reports(staged_public)
    assert report["documents_total"] == 1

    schema_dir = pipeline_run.REPO_ROOT / "schemas"
    assert validate_jsonl_file(
        staged_public / "documents.jsonl",
        schema_dir / "document.schema.json",
    )
    assert validate_jsonl_file(
        staged_public / "meetings.jsonl",
        schema_dir / "meeting.schema.json",
    )

    promote_staged_directories(
        staged_public_dir=staged_public,
        target_public_dir=target_public,
        staged_raw_dir=staged_raw,
        target_raw_dir=target_raw,
    )

    assert (target_public / "sentinel.txt").read_text(encoding="utf-8") == "existing"
    assert (target_public / "documents.jsonl").exists()
    assert (target_public / "meeting_documents.jsonl").exists()
    assert (target_public / "meeting_item_documents.jsonl").exists()
    latest = json.loads((target_public / "latest.json").read_text(encoding="utf-8"))
    assert latest["dataset_documents_total"] == 1
    assert latest["dataset_document_relations_total"] == 2
    assert (target_raw / "documents.json").exists()
