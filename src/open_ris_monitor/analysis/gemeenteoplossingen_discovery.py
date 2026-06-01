from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import requests
import yaml

DEFAULT_ENDPOINTS = [
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

MEETING_HINTS = ("meeting", "vergadering", "session", "event", "calendar")
AGENDA_HINTS = ("agenda", "item", "agendapunt")


@dataclass
class EndpointProbe:
    endpoint: str
    url: str
    ok: bool
    status_code: int | None
    error: str | None
    response_shape: str | None
    top_level_keys: list[str]
    result_keys: list[str]
    sample_keys: list[str]
    sample_count: int | None


def load_config(municipality: str, config_dir: Path = Path("config/municipalities")) -> dict[str, Any]:
    config_path = config_dir / f"{municipality}.yml"
    if not config_path.exists():
        raise FileNotFoundError(f"Municipality config not found: {config_path}")
    with config_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Expected YAML object in {config_path}")
    return data


def get_base_url(config: dict[str, Any]) -> str:
    source = config.get("source") or config.get("source_system") or config.get("sourceSystem")
    if isinstance(source, dict) and source.get("base_url"):
        return str(source["base_url"]).rstrip("/") + "/"
    sources = config.get("sources")
    if isinstance(sources, list):
        for item in sources:
            if isinstance(item, dict) and item.get("base_url"):
                return str(item["base_url"]).rstrip("/") + "/"
    # Current project config uses source_systems in some iterations.
    source_systems = config.get("source_systems")
    if isinstance(source_systems, list):
        for item in source_systems:
            if isinstance(item, dict) and item.get("base_url"):
                return str(item["base_url"]).rstrip("/") + "/"
    if config.get("base_url"):
        return str(config["base_url"]).rstrip("/") + "/"
    raise KeyError("Could not find base_url in municipality config")


def classify_response_shape(payload: Any) -> str:
    if isinstance(payload, list):
        return "list"
    if not isinstance(payload, dict):
        return type(payload).__name__
    if isinstance(payload.get("result"), dict):
        result = payload["result"]
        list_keys = [key for key, value in result.items() if isinstance(value, list)]
        if list_keys:
            return "object.result.object_with_list"
        return "object.result.object"
    if isinstance(payload.get("data"), list):
        return "object.data.list"
    if isinstance(payload.get("items"), list):
        return "object.items.list"
    if isinstance(payload.get("results"), list):
        return "object.results.list"
    return "object"


def _list_from_payload(payload: Any) -> list[Any]:
    if isinstance(payload, list):
        return payload
    if not isinstance(payload, dict):
        return []
    result = payload.get("result")
    if isinstance(result, dict):
        # Prefer the first list in result. This handles result.documents and likely similar shapes.
        for value in result.values():
            if isinstance(value, list):
                return value
    for key in ("data", "items", "results", "value"):
        value = payload.get(key)
        if isinstance(value, list):
            return value
    return []


def summarize_payload(payload: Any, limit: int) -> tuple[str, list[str], list[str], list[str], int | None]:
    response_shape = classify_response_shape(payload)
    top_level_keys = list(payload.keys()) if isinstance(payload, dict) else []
    result = payload.get("result") if isinstance(payload, dict) else None
    result_keys = list(result.keys()) if isinstance(result, dict) else []
    records = _list_from_payload(payload)
    sample_count = len(records) if records is not None else None
    sample_keys: list[str] = []
    if records:
        first = records[0]
        if isinstance(first, dict):
            sample_keys = list(first.keys())[:50]
    return response_shape, top_level_keys, result_keys, sample_keys, sample_count


def probe_endpoint(base_url: str, endpoint: str, *, limit: int = 3, timeout_seconds: int = 30) -> EndpointProbe:
    url = base_url.rstrip("/") + "/" + endpoint.lstrip("/")
    params = {"limit": limit, "offset": 0}
    try:
        response = requests.get(url, params=params, timeout=timeout_seconds)
        status_code = response.status_code
        if not response.ok:
            return EndpointProbe(
                endpoint=endpoint,
                url=response.url,
                ok=False,
                status_code=status_code,
                error=f"HTTP {status_code}",
                response_shape=None,
                top_level_keys=[],
                result_keys=[],
                sample_keys=[],
                sample_count=None,
            )
        payload = response.json()
        response_shape, top_level_keys, result_keys, sample_keys, sample_count = summarize_payload(payload, limit)
        return EndpointProbe(
            endpoint=endpoint,
            url=response.url,
            ok=True,
            status_code=status_code,
            error=None,
            response_shape=response_shape,
            top_level_keys=top_level_keys,
            result_keys=result_keys,
            sample_keys=sample_keys,
            sample_count=sample_count,
        )
    except Exception as exc:  # noqa: BLE001, discovery should record failures, not crash.
        return EndpointProbe(
            endpoint=endpoint,
            url=url,
            ok=False,
            status_code=None,
            error=str(exc),
            response_shape=None,
            top_level_keys=[],
            result_keys=[],
            sample_keys=[],
            sample_count=None,
        )


def _looks_like(keys: Iterable[str], hints: Iterable[str]) -> bool:
    haystack = " ".join(keys).lower()
    return any(hint.lower() in haystack for hint in hints)


def summarize_probes(probes: list[EndpointProbe]) -> dict[str, Any]:
    working = [probe.endpoint for probe in probes if probe.ok]
    likely_meeting: list[str] = []
    likely_agenda: list[str] = []
    for probe in probes:
        keys = [probe.endpoint, *probe.top_level_keys, *probe.result_keys, *probe.sample_keys]
        if probe.ok and _looks_like(keys, MEETING_HINTS):
            likely_meeting.append(probe.endpoint)
        if probe.ok and _looks_like(keys, AGENDA_HINTS):
            likely_agenda.append(probe.endpoint)
    return {
        "working_endpoints": working,
        "working_endpoint_count": len(working),
        "likely_meeting_endpoints": likely_meeting,
        "likely_agenda_endpoints": likely_agenda,
    }


def discover_endpoints(
    *,
    municipality: str,
    endpoints: list[str] | None = None,
    limit: int = 3,
    output_path: Path = Path("data/public/quality/gemeenteoplossingen_endpoint_discovery.json"),
) -> dict[str, Any]:
    config = load_config(municipality)
    base_url = get_base_url(config)
    endpoint_list = endpoints or DEFAULT_ENDPOINTS
    probes = [probe_endpoint(base_url, endpoint, limit=limit) for endpoint in endpoint_list]
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "municipality": municipality,
        "base_url": base_url,
        "limit": limit,
        "summary": summarize_probes(probes),
        "probes": [asdict(probe) for probe in probes],
        "notes": [
            "HTTP 404 or 403 responses are expected for unsupported endpoint candidates.",
            "This report is discovery output and should be reviewed before implementing canonical Meeting or AgendaItem models.",
            "The documents endpoint is included as a known baseline endpoint.",
        ],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    return report


def parse_endpoints(value: str | None) -> list[str] | None:
    if not value:
        return None
    endpoints = [item.strip() for item in value.split(",") if item.strip()]
    return endpoints or None


def main() -> None:
    parser = argparse.ArgumentParser(description="Discover GemeenteOplossingen RIS API endpoints")
    parser.add_argument("--municipality", default="huizen")
    parser.add_argument("--limit", type=int, default=3)
    parser.add_argument("--endpoints", default="", help="Comma-separated endpoint candidates. Leave empty for defaults.")
    parser.add_argument(
        "--output",
        default="data/public/quality/gemeenteoplossingen_endpoint_discovery.json",
        help="Output JSON report path.",
    )
    args = parser.parse_args()
    report = discover_endpoints(
        municipality=args.municipality,
        endpoints=parse_endpoints(args.endpoints),
        limit=args.limit,
        output_path=Path(args.output),
    )
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
