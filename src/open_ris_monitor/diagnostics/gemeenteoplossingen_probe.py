"""Bounded incident probe for GemeenteOplossingen API routing and access control.

This command is diagnostic only. It compares normal project requests with a common
browser-like User-Agent, but never uses that browser identity for harvesting and does
not attempt to bypass authentication, WAF challenges or other access controls.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from collections.abc import Iterable
from typing import Any
from urllib.parse import urljoin

import requests

from open_ris_monitor.connectors.gemeenteoplossingen import (
    DEFAULT_USER_AGENT,
    _safe_body_preview,
    sanitize_url,
)
from open_ris_monitor.pipeline.run import load_municipality_config

BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0 Safari/537.36"
)
SAFE_RESPONSE_HEADERS = (
    "Content-Type",
    "Content-Length",
    "Location",
    "Retry-After",
    "Server",
    "Via",
    "X-Cache",
    "X-Request-Id",
    "CF-Ray",
)


def _first_source_id(path: Path, *keys: str) -> str | None:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as source:
        for line in source:
            if not line.strip():
                continue
            payload = json.loads(line)
            if not isinstance(payload, dict):
                continue
            for key in keys:
                value = payload.get(key)
                if value not in (None, ""):
                    return str(value)
    return None


def resolve_probe_ids(public_dir: Path) -> dict[str, str | None]:
    """Resolve known-good source identifiers from the current public exports."""
    return {
        "document_id": _first_source_id(
            public_dir / "documents.jsonl", "source_id", "document_source_id"
        ),
        "meeting_id": _first_source_id(
            public_dir / "meetings.jsonl", "source_id", "meeting_source_id"
        ),
        "meeting_item_id": _first_source_id(
            public_dir / "meeting_items.jsonl", "source_id", "meeting_item_source_id"
        ),
    }


def build_probe_matrix(
    ids: dict[str, str | None],
    *,
    scope: str = "full",
) -> list[dict[str, Any]]:
    if scope not in {"core", "full"}:
        raise ValueError("scope must be 'core' or 'full'")
    probes: list[dict[str, Any]] = [
        {"name": "api_root", "path": ""},
        {"name": "documents", "path": "documents"},
        {"name": "documents_trailing_slash", "path": "documents/"},
        {
            "name": "documents_page",
            "path": "documents",
            "params": {"limit": 1, "offset": 0},
        },
        {
            "name": "meetings_page",
            "path": "meetings",
            "params": {"limit": 1, "offset": 0},
        },
        {
            "name": "events_page",
            "path": "events",
            "params": {"limit": 1, "offset": 0},
        },
        {
            "name": "groups_page",
            "path": "groups",
            "params": {"limit": 1, "offset": 0},
        },
    ]
    if scope == "core":
        return probes

    document_id = ids.get("document_id")
    meeting_id = ids.get("meeting_id")
    meeting_item_id = ids.get("meeting_item_id")
    if document_id:
        probes.extend(
            [
                {"name": "document_detail", "path": f"documents/{document_id}"},
                {
                    "name": "document_download_range",
                    "path": f"documents/{document_id}/download",
                    "download_probe": True,
                },
            ]
        )
    if meeting_id:
        probes.extend(
            [
                {
                    "name": "meeting_documents",
                    "path": f"meetings/{meeting_id}/documents",
                    "params": {"limit": 1, "offset": 0},
                },
                {
                    "name": "meeting_items",
                    "path": f"meetings/{meeting_id}/meetingitems",
                    "params": {"limit": 1, "offset": 0},
                },
            ]
        )
    if meeting_item_id:
        probes.append(
            {
                "name": "meeting_item_documents",
                "path": f"meetingitems/{meeting_item_id}/documents",
                "params": {"limit": 1, "offset": 0},
            }
        )
    return probes


def _category(status_code: int | None, content_type: str | None, preview: str) -> str:
    if status_code is None:
        return "network_error"
    media_type = (content_type or "").split(";", 1)[0].strip().lower()
    if "html" in media_type or preview.lower().startswith(
        ("<!doctype html", "<html", "toegang geweigerd")
    ):
        return "html_response"
    if status_code >= 400:
        return f"http_{status_code}"
    if media_type == "application/json" or media_type.endswith("+json"):
        return "ok_json"
    return "ok_non_json"


def _safe_headers(response: requests.Response) -> dict[str, str]:
    return {
        key: value
        for key in SAFE_RESPONSE_HEADERS
        if (value := response.headers.get(key)) is not None
    }


def _history(response: requests.Response) -> list[dict[str, Any]]:
    return [
        {
            "status_code": item.status_code,
            "url": sanitize_url(item.url),
            "location": sanitize_url(item.headers.get("Location", "")),
        }
        for item in response.history
    ]


def run_single_probe(
    *,
    session: requests.Session,
    base_url: str,
    probe: dict[str, Any],
    user_agent_label: str,
    user_agent: str,
    timeout_seconds: float,
) -> dict[str, Any]:
    url = urljoin(base_url.rstrip("/") + "/", str(probe["path"]).lstrip("/"))
    headers = {"Accept": "application/json", "User-Agent": user_agent}
    download_probe = bool(probe.get("download_probe"))
    if download_probe:
        headers["Range"] = "bytes=0-0"
    result: dict[str, Any] = {
        "name": probe["name"],
        "path": probe["path"],
        "user_agent": user_agent_label,
        "request_url": sanitize_url(url),
        "base_url": sanitize_url(base_url),
        "request_params": probe.get("params") or {},
        "download_probe": download_probe,
    }
    try:
        response = session.get(
            url,
            params=probe.get("params"),
            headers=headers,
            timeout=timeout_seconds,
            allow_redirects=True,
            stream=download_probe,
        )
        content_type = response.headers.get("Content-Type")
        if download_probe:
            chunk = next(response.iter_content(chunk_size=512), b"")
            result["bytes_read"] = len(chunk)
            media_type = (content_type or "").split(";", 1)[0].strip().lower()
            if response.status_code >= 400 or "html" in media_type or media_type.startswith("text/"):
                encoding = getattr(response, "encoding", None) or "utf-8"
                preview = " ".join(chunk.decode(encoding, errors="replace").split())[:320]
            else:
                preview = ""
            response.close()
        else:
            preview = _safe_body_preview(response)
        result.update(
            {
                "status_code": response.status_code,
                "final_url": sanitize_url(response.url),
                "content_type": content_type,
                "category": _category(response.status_code, content_type, preview),
                "redirect_history": _history(response),
                "response_headers": _safe_headers(response),
                "body_preview": preview or None,
            }
        )
    except requests.Timeout:
        result.update({"category": "timeout", "error": "request timed out"})
    except requests.ConnectionError:
        result.update({"category": "connection_error", "error": "connection failed"})
    except requests.RequestException as exc:
        result.update({"category": "network_error", "error": type(exc).__name__})
    return result


def run_probe(
    municipality: str,
    *,
    public_dir: Path = Path("data/public"),
    timeout_seconds: float = 15.0,
    include_browser_user_agent: bool = True,
    scope: str = "full",
    additional_base_urls: Iterable[str] = (),
    session: requests.Session | None = None,
) -> dict[str, Any]:
    config = load_municipality_config(municipality)
    source_system = config["source_system"]
    configured_base_url = str(source_system["base_url"]).rstrip("/") + "/"
    base_urls = [("configured", configured_base_url)]
    for index, value in enumerate(additional_base_urls, start=1):
        base_urls.append((f"additional_{index}", str(value).rstrip("/") + "/"))
    ids = resolve_probe_ids(public_dir)
    probes = build_probe_matrix(ids, scope=scope)
    agents = [("project", str(source_system.get("user_agent") or DEFAULT_USER_AGENT))]
    if include_browser_user_agent:
        agents.append(("browser_diagnostic", BROWSER_USER_AGENT))
    client = session or requests.Session()
    results: list[dict[str, Any]] = []
    for base_url_label, base_url in base_urls:
        for label, agent in agents:
            for probe in probes:
                result = run_single_probe(
                    session=client,
                    base_url=base_url,
                    probe=probe,
                    user_agent_label=label,
                    user_agent=agent,
                    timeout_seconds=timeout_seconds,
                )
                result["base_url_label"] = base_url_label
                results.append(result)
    return {
        "municipality": municipality,
        "base_url": sanitize_url(configured_base_url),
        "base_urls": [
            {"label": label, "url": sanitize_url(base_url)} for label, base_url in base_urls
        ],
        "scope": scope,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "known_ids": ids,
        "request_count": len(results),
        "diagnostic_only": True,
        "results": results,
    }


def _summary_markdown(report: dict[str, Any]) -> str:
    lines = [
        "## GemeenteOplossingen incident probe",
        "",
        f"Configured base URL: `{report['base_url']}`  ",
        f"Scope: `{report['scope']}`  ",
        f"Requests: `{report['request_count']}`  ",
        "The browser-like User-Agent is used only for bounded diagnosis, never for harvesting.",
        "",
        "| Base | Probe | User-Agent | HTTP | Category | Content-Type |",
        "| --- | --- | --- | ---: | --- | --- |",
    ]
    for item in report["results"]:
        lines.append(
            f"| `{item['base_url_label']}` | `{item['name']}` | `{item['user_agent']}` | "
            f"{item.get('status_code', '')} | `{item.get('category', '')}` | "
            f"`{item.get('content_type') or ''}` |"
        )
    return "\n".join(lines) + "\n"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a bounded upstream incident probe.")
    parser.add_argument("--municipality", default="huizen")
    parser.add_argument("--public-dir", type=Path, default=Path("data/public"))
    parser.add_argument("--output", type=Path, default=Path("data/diagnostics/probe.json"))
    parser.add_argument("--summary", type=Path, default=None)
    parser.add_argument("--timeout-seconds", type=float, default=15.0)
    parser.add_argument("--scope", choices=("core", "full"), default="full")
    parser.add_argument(
        "--additional-base-url",
        action="append",
        default=[],
        help="Optional known API base variant to compare. This is diagnostic only.",
    )
    parser.add_argument(
        "--include-browser-user-agent",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    report = run_probe(
        args.municipality,
        public_dir=args.public_dir,
        timeout_seconds=args.timeout_seconds,
        include_browser_user_agent=args.include_browser_user_agent,
        scope=args.scope,
        additional_base_urls=args.additional_base_url,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary_path = args.summary
    if summary_path is None and os.environ.get("GITHUB_STEP_SUMMARY"):
        summary_path = Path(os.environ["GITHUB_STEP_SUMMARY"])
    if summary_path is not None:
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        with summary_path.open("a", encoding="utf-8") as summary:
            summary.write(_summary_markdown(report))
    for item in report["results"]:
        print(
            "probe base={base} name={name} ua={user_agent} status={status} category={category} "
            "content_type={content_type} final_url={final_url}".format(
                base=item.get("base_url_label", "configured"),
                name=item["name"],
                user_agent=item["user_agent"],
                status=item.get("status_code", ""),
                category=item.get("category", ""),
                content_type=item.get("content_type", ""),
                final_url=item.get("final_url", item.get("request_url", "")),
            )
        )


if __name__ == "__main__":
    main()
