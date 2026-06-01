from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import requests
import yaml


DEFAULT_CANDIDATE_ENDPOINTS = [
    "documents",
    "meetings",
    "meeting",
    "meetingsessions",
    "sessions",
    "events",
    "calendar",
    "agendas",
    "agenda",
    "agendaItems",
    "agendaitems",
    "agenda-items",
    "items",
    "committees",
    "councils",
    "organizations",
]


@dataclass(frozen=True)
class EndpointProbe:
    endpoint: str
    url: str
    status_code: int | None
    ok: bool
    content_type: str | None
    response_shape: str
    result_keys: list[str]
    item_count: int | None
    sample_keys: list[str]
    error: str | None = None


def load_municipality_config(config_path: Path) -> dict[str, Any]:
    with config_path.open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}
    if not isinstance(loaded, dict):
        raise ValueError(f"Expected YAML object in {config_path}")
    return loaded


def extract_base_url(config: dict[str, Any]) -> str:
    source = config.get("source") or config.get("source_system") or config.get("source_systems")
    if isinstance(source, dict):
        base_url = source.get("base_url")
    elif isinstance(source, list) and source:
        first = source[0]
        base_url = first.get("base_url") if isinstance(first, dict) else None
    else:
        base_url = None

    if not base_url:
        # Current Huizen config used in earlier milestones stores the API under source_system.
        source_system = config.get("source_system", {})
        if isinstance(source_system, dict):
            base_url = source_system.get("base_url")

    if not base_url:
        raise ValueError("Could not find source base_url in municipality config")

    return str(base_url).rstrip("/") + "/"


def classify_json_shape(payload: Any) -> tuple[str, list[str], int | None, list[str]]:
    if isinstance(payload, list):
        sample = payload[0] if payload else None
        sample_keys = sorted(sample.keys()) if isinstance(sample, dict) else []
        return "list", [], len(payload), sample_keys

    if not isinstance(payload, dict):
        return type(payload).__name__, [], None, []

    result = payload.get("result")
    result_keys = sorted(result.keys()) if isinstance(result, dict) else []

    # GemeenteOplossingen documents endpoint uses result.documents.
    candidate_lists: list[Any] = []
    if isinstance(result, dict):
        for value in result.values():
            if isinstance(value, list):
                candidate_lists.append(value)
    for value in payload.values():
        if isinstance(value, list):
            candidate_lists.append(value)

    item_count = None
    sample_keys: list[str] = []
    if candidate_lists:
        first_list = candidate_lists[0]
        item_count = len(first_list)
        if first_list and isinstance(first_list[0], dict):
            sample_keys = sorted(first_list[0].keys())

    if isinstance(result, dict):
        return "object_with_result", result_keys, item_count, sample_keys
    return "object", sorted(payload.keys()), item_count, sample_keys


def probe_endpoint(
    *,
    base_url: str,
    endpoint: str,
    session: requests.Session,
    timeout_seconds: int,
    limit: int,
) -> EndpointProbe:
    url = urljoin(base_url, endpoint.lstrip("/"))
    try:
        response = session.get(url, params={"limit": limit, "offset": 0}, timeout=timeout_seconds)
        content_type = response.headers.get("content-type")
        if response.status_code >= 400:
            return EndpointProbe(
                endpoint=endpoint,
                url=response.url,
                status_code=response.status_code,
                ok=False,
                content_type=content_type,
                response_shape="error_status",
                result_keys=[],
                item_count=None,
                sample_keys=[],
                error=response.text[:300],
            )

        try:
            payload = response.json()
        except ValueError as exc:
            return EndpointProbe(
                endpoint=endpoint,
                url=response.url,
                status_code=response.status_code,
                ok=False,
                content_type=content_type,
                response_shape="non_json",
                result_keys=[],
                item_count=None,
                sample_keys=[],
                error=str(exc),
            )

        response_shape, result_keys, item_count, sample_keys = classify_json_shape(payload)
        return EndpointProbe(
            endpoint=endpoint,
            url=response.url,
            status_code=response.status_code,
            ok=True,
            content_type=content_type,
            response_shape=response_shape,
            result_keys=result_keys,
            item_count=item_count,
            sample_keys=sample_keys,
            error=None,
        )
    except requests.RequestException as exc:
        return EndpointProbe(
            endpoint=endpoint,
            url=url,
            status_code=None,
            ok=False,
            content_type=None,
            response_shape="request_exception",
            result_keys=[],
            item_count=None,
            sample_keys=[],
            error=str(exc),
        )


def run_discovery(
    *,
    config_path: Path,
    output_path: Path,
    endpoints: list[str] | None = None,
    timeout_seconds: int = 30,
    limit: int = 3,
) -> dict[str, Any]:
    config = load_municipality_config(config_path)
    base_url = extract_base_url(config)
    municipality = config.get("municipality", {}) if isinstance(config.get("municipality"), dict) else {}
    municipality_slug = municipality.get("slug") or config_path.stem

    session = requests.Session()
    endpoint_list = endpoints or DEFAULT_CANDIDATE_ENDPOINTS
    probes = [
        probe_endpoint(
            base_url=base_url,
            endpoint=endpoint,
            session=session,
            timeout_seconds=timeout_seconds,
            limit=limit,
        )
        for endpoint in endpoint_list
    ]

    likely_meeting_endpoints = [
        probe.endpoint
        for probe in probes
        if probe.ok
        and any(term in probe.endpoint.lower() for term in ["meeting", "session", "event", "calendar"])
    ]
    likely_agenda_endpoints = [
        probe.endpoint
        for probe in probes
        if probe.ok and any(term in probe.endpoint.lower() for term in ["agenda", "item"])
    ]

    report: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "municipality": municipality_slug,
        "base_url": base_url,
        "limit": limit,
        "summary": {
            "endpoints_tested": len(probes),
            "endpoints_ok": sum(1 for probe in probes if probe.ok),
            "likely_meeting_endpoints": likely_meeting_endpoints,
            "likely_agenda_endpoints": likely_agenda_endpoints,
        },
        "probes": [asdict(probe) for probe in probes],
        "notes": [
            "This is a discovery report, not a final connector contract.",
            "Endpoints that return HTTP 404/403 may still exist with different names or parameters.",
            "The next step is to inspect successful endpoint sample keys and define canonical Meeting and AgendaItem mappings.",
        ],
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Probe GemeenteOplossingen API endpoints for meetings and agenda items.")
    parser.add_argument("--municipality", default="huizen", help="Municipality config slug")
    parser.add_argument("--config-dir", default="config/municipalities", help="Directory containing municipality YAML configs")
    parser.add_argument("--output", default="data/public/quality/gemeenteoplossingen_endpoint_discovery.json")
    parser.add_argument("--limit", type=int, default=3)
    parser.add_argument("--timeout-seconds", type=int, default=30)
    parser.add_argument("--endpoints", default="", help="Optional comma-separated endpoint list")
    args = parser.parse_args()

    endpoints = [item.strip() for item in args.endpoints.split(",") if item.strip()] or None
    config_path = Path(args.config_dir) / f"{args.municipality}.yml"
    report = run_discovery(
        config_path=config_path,
        output_path=Path(args.output),
        endpoints=endpoints,
        timeout_seconds=args.timeout_seconds,
        limit=args.limit,
    )
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
