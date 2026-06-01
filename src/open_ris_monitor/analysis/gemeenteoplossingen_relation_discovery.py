from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
import yaml


@dataclass
class ProbeResult:
    path: str
    url: str
    ok: bool
    status_code: int | None
    error: str | None
    response_shape: str | None
    result_keys: list[str]
    sample_keys: list[str]
    sample_count: int | None
    sample_ids: list[int | str]


def classify_payload(payload: Any) -> tuple[str | None, list[str], list[str], int | None, list[int | str]]:
    if not isinstance(payload, dict):
        return type(payload).__name__, [], [], None, []

    result = payload.get("result")
    if isinstance(result, dict):
        result_keys = list(result.keys())
        list_values = [(key, value) for key, value in result.items() if isinstance(value, list)]
        if list_values:
            _, values = max(list_values, key=lambda item: len(item[1]))
            sample = values[0] if values and isinstance(values[0], dict) else {}
            sample_ids = [item.get("id") for item in values if isinstance(item, dict) and item.get("id") is not None]
            return (
                "object.result.object_with_list",
                result_keys,
                list(sample.keys()) if isinstance(sample, dict) else [],
                len(values),
                sample_ids[:10],
            )
        return "object.result.object", result_keys, list(result.keys()), None, [result.get("id")] if result.get("id") is not None else []

    if isinstance(result, list):
        sample = result[0] if result and isinstance(result[0], dict) else {}
        sample_ids = [item.get("id") for item in result if isinstance(item, dict) and item.get("id") is not None]
        return "object.result.list", [], list(sample.keys()) if isinstance(sample, dict) else [], len(result), sample_ids[:10]

    return "object", [], list(payload.keys()), None, []


class RelationDiscoveryClient:
    def __init__(self, base_url: str, timeout_seconds: int = 30) -> None:
        self.base_url = base_url.rstrip("/") + "/"
        self.timeout_seconds = timeout_seconds
        self.session = requests.Session()

    def get(self, path: str, params: dict[str, Any] | None = None) -> ProbeResult:
        path = path.lstrip("/")
        url = self.base_url + path
        try:
            response = self.session.get(url, params=params, timeout=self.timeout_seconds)
            status_code = response.status_code
            response.raise_for_status()
            payload = response.json()
            shape, result_keys, sample_keys, sample_count, sample_ids = classify_payload(payload)
            return ProbeResult(
                path=path,
                url=response.url,
                ok=True,
                status_code=status_code,
                error=None,
                response_shape=shape,
                result_keys=result_keys,
                sample_keys=sample_keys,
                sample_count=sample_count,
                sample_ids=sample_ids,
            )
        except Exception as exc:  # noqa: BLE001 - discovery should report rather than crash
            status_code = getattr(getattr(exc, "response", None), "status_code", None)
            return ProbeResult(
                path=path,
                url=url,
                ok=False,
                status_code=status_code,
                error=str(exc),
                response_shape=None,
                result_keys=[],
                sample_keys=[],
                sample_count=None,
                sample_ids=[],
            )

    def get_payload(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        response = self.session.get(self.base_url + path.lstrip("/"), params=params, timeout=self.timeout_seconds)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError(f"Expected object response for {path}")
        return payload


def list_from_result(payload: dict[str, Any], preferred_key: str) -> list[dict[str, Any]]:
    result = payload.get("result")
    if not isinstance(result, dict):
        return []
    value = result.get(preferred_key)
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    for candidate in result.values():
        if isinstance(candidate, list):
            return [item for item in candidate if isinstance(item, dict)]
    return []


def load_config(path: Path, municipality: str) -> dict[str, Any]:
    config_path = path / "config" / "municipalities" / f"{municipality}.yml"
    with config_path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def discover_relations(
    *,
    base_url: str,
    municipality: str,
    meeting_limit: int,
    item_limit: int,
) -> dict[str, Any]:
    client = RelationDiscoveryClient(base_url)
    probes: list[ProbeResult] = []

    meetings_payload = client.get_payload("meetings", params={"limit": meeting_limit, "offset": 0})
    meetings = list_from_result(meetings_payload, "meetings")
    meeting_ids = [meeting.get("id") for meeting in meetings if meeting.get("id") is not None]

    probes.append(client.get("meetings", params={"limit": meeting_limit, "offset": 0}))
    probes.append(client.get("dmus", params={"limit": 10, "offset": 0}))
    probes.append(client.get("events", params={"limit": meeting_limit, "offset": 0}))
    probes.append(client.get("meetingsessions", params={"limit": meeting_limit, "offset": 0}))

    meeting_item_ids: list[int | str] = []
    for meeting_id in meeting_ids[:meeting_limit]:
        probes.append(client.get(f"meetings/{meeting_id}"))
        probes.append(client.get(f"meetings/{meeting_id}/documents", params={"limit": item_limit, "offset": 0}))
        meeting_items_probe = client.get(f"meetings/{meeting_id}/meetingitems", params={"limit": item_limit, "offset": 0})
        probes.append(meeting_items_probe)

        try:
            items_payload = client.get_payload(f"meetings/{meeting_id}/meetingitems", params={"limit": item_limit, "offset": 0})
            items = list_from_result(items_payload, "meetingitems")
            meeting_item_ids.extend([item.get("id") for item in items if item.get("id") is not None])
        except Exception:
            pass

    for meeting_item_id in meeting_item_ids[:item_limit]:
        probes.append(client.get(f"meetingitems/{meeting_item_id}"))
        probes.append(client.get(f"meetingitems/{meeting_item_id}/documents", params={"limit": item_limit, "offset": 0}))

    working_paths = [probe.path for probe in probes if probe.ok]

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "municipality": municipality,
        "base_url": base_url,
        "meeting_limit": meeting_limit,
        "item_limit": item_limit,
        "summary": {
            "sampled_meeting_ids": meeting_ids[:meeting_limit],
            "sampled_meeting_item_ids": meeting_item_ids[:item_limit],
            "working_path_count": len(working_paths),
            "working_paths": working_paths,
            "meeting_items_discovered": len(meeting_item_ids),
        },
        "probes": [asdict(probe) for probe in probes],
        "notes": [
            "This report uses documented nested routes and a small number of sampled meetings.",
            "Review sample_keys before implementing canonical Meeting and AgendaItem models.",
            "A 200 response with zero sample_count can still be a valid relationship endpoint for meetings without documents or items.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--municipality", default="huizen")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--meeting-limit", type=int, default=3)
    parser.add_argument("--item-limit", type=int, default=5)
    parser.add_argument("--output", default="data/public/quality/gemeenteoplossingen_relation_discovery.json")
    args = parser.parse_args()

    repo_root = Path(args.repo_root)
    config = load_config(repo_root, args.municipality)
    source = config["source"] if "source" in config else config["source_system"]
    base_url = source["base_url"]

    report = discover_relations(
        base_url=base_url,
        municipality=args.municipality,
        meeting_limit=args.meeting_limit,
        item_limit=args.item_limit,
    )

    output_path = repo_root / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
