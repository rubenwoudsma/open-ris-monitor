from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
import yaml

DEFAULT_CONFIG_DIR = Path("config/municipalities")
DEFAULT_OUTPUT = Path("data/public/quality/gemeenteoplossingen_relation_discovery.json")


def parse_ids(value: str | None) -> list[int]:
    if not value:
        return []
    ids: list[int] = []
    for part in value.split(","):
        part = part.strip()
        if not part:
            continue
        ids.append(int(part))
    return ids


def classify_payload(payload: Any) -> str:
    if isinstance(payload, list):
        return "list"
    if not isinstance(payload, dict):
        return type(payload).__name__
    result = payload.get("result")
    if isinstance(result, dict):
        if any(isinstance(value, list) for value in result.values()):
            return "object.result.object_with_list"
        return "object.result.object"
    if isinstance(result, list):
        return "object.result.list"
    return "object"


def list_from_result(payload: dict[str, Any], preferred_key: str | None = None) -> list[dict[str, Any]]:
    result = payload.get("result")
    if isinstance(result, list):
        return [item for item in result if isinstance(item, dict)]
    if not isinstance(result, dict):
        return []
    if preferred_key and isinstance(result.get(preferred_key), list):
        return [item for item in result[preferred_key] if isinstance(item, dict)]
    for value in result.values():
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    return []


def result_total_count(payload: dict[str, Any]) -> str | None:
    result = payload.get("result")
    if isinstance(result, dict) and "totalCount" in result:
        return str(result.get("totalCount"))
    return None


def sample_keys(records: list[dict[str, Any]]) -> list[str]:
    if not records:
        return []
    return list(records[0].keys())


def sample_ids(records: list[dict[str, Any]]) -> list[Any]:
    ids: list[Any] = []
    for record in records:
        if "id" in record:
            ids.append(record["id"])
    return ids


def load_config(municipality: str) -> dict[str, Any]:
    config_path = DEFAULT_CONFIG_DIR / f"{municipality}.yml"
    with config_path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def base_url_from_config(config: dict[str, Any]) -> str:
    source = config.get("source") or config.get("source_system") or {}
    base_url = source.get("base_url") or config.get("base_url")
    if not base_url:
        raise ValueError("Could not find base_url in municipality config")
    return str(base_url).rstrip("/") + "/"


class DiscoveryClient:
    def __init__(self, base_url: str, timeout_seconds: int = 30) -> None:
        self.base_url = base_url.rstrip("/") + "/"
        self.session = requests.Session()
        self.timeout_seconds = timeout_seconds

    def get(self, path: str, params: dict[str, Any] | None = None) -> tuple[str, dict[str, Any] | None, str | None, int | None]:
        url = self.base_url + path.lstrip("/")
        try:
            response = self.session.get(url, params=params, timeout=self.timeout_seconds)
            status_code = response.status_code
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, dict):
                return response.url, None, f"Expected JSON object, got {type(payload).__name__}", status_code
            return response.url, payload, None, status_code
        except requests.HTTPError as exc:
            return getattr(exc.response, "url", url), None, f"HTTP {getattr(exc.response, 'status_code', 'unknown')}", getattr(exc.response, "status_code", None)
        except Exception as exc:  # pragma: no cover - defensive discovery code
            return url, None, str(exc), None


def make_probe(path: str, url: str, payload: dict[str, Any] | None, error: str | None, status_code: int | None, preferred_key: str | None = None, include_records: bool = False) -> dict[str, Any]:
    if payload is None:
        return {
            "path": path,
            "url": url,
            "ok": False,
            "status_code": status_code,
            "error": error,
            "response_shape": None,
            "result_keys": [],
            "sample_keys": [],
            "sample_count": None,
            "sample_ids": [],
            "total_count": None,
            "sample_records": [],
        }

    records = list_from_result(payload, preferred_key=preferred_key)
    result = payload.get("result")
    result_keys = list(result.keys()) if isinstance(result, dict) else []
    return {
        "path": path,
        "url": url,
        "ok": True,
        "status_code": status_code,
        "error": None,
        "response_shape": classify_payload(payload),
        "result_keys": result_keys,
        "sample_keys": sample_keys(records),
        "sample_count": len(records),
        "sample_ids": sample_ids(records),
        "total_count": result_total_count(payload),
        "sample_records": records[:3] if include_records else [],
    }


def probe(client: DiscoveryClient, path: str, params: dict[str, Any] | None = None, preferred_key: str | None = None, include_records: bool = False) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    url, payload, error, status_code = client.get(path, params=params)
    probe_result = make_probe(path, url, payload, error, status_code, preferred_key=preferred_key, include_records=include_records)
    records = list_from_result(payload, preferred_key=preferred_key) if payload else []
    return probe_result, records


def meeting_ids_from_meetingsessions(records: list[dict[str, Any]]) -> list[int]:
    ids: list[int] = []
    seen: set[int] = set()
    for record in records:
        container = record.get("container")
        if not isinstance(container, dict):
            continue
        meeting = container.get("meeting")
        if not isinstance(meeting, dict):
            continue
        meeting_id = meeting.get("id")
        if isinstance(meeting_id, int) and meeting_id not in seen:
            seen.add(meeting_id)
            ids.append(meeting_id)
    return ids


def unique_ints(values: list[Any]) -> list[int]:
    out: list[int] = []
    seen: set[int] = set()
    for value in values:
        if isinstance(value, int) and value not in seen:
            seen.add(value)
            out.append(value)
    return out


def discover_relations(
    municipality: str,
    meeting_limit: int,
    item_limit: int,
    meeting_ids: list[int],
    scan_limit: int,
) -> dict[str, Any]:
    config = load_config(municipality)
    base_url = base_url_from_config(config)
    client = DiscoveryClient(base_url)

    probes: list[dict[str, Any]] = []

    meetings_probe, meeting_records = probe(
        client,
        "meetings",
        params={"limit": meeting_limit, "offset": 0},
        preferred_key="meetings",
        include_records=True,
    )
    probes.append(meetings_probe)

    dmus_probe, _ = probe(client, "dmus", params={"limit": 10, "offset": 0}, preferred_key="dmus", include_records=True)
    probes.append(dmus_probe)

    events_probe, _ = probe(client, "events", params={"limit": 3, "offset": 0}, preferred_key="events", include_records=True)
    probes.append(events_probe)

    sessions_probe, session_records = probe(
        client,
        "meetingsessions",
        params={"limit": scan_limit, "offset": 0},
        preferred_key="meetingsessions",
        include_records=True,
    )
    probes.append(sessions_probe)

    recent_meeting_ids = unique_ints([record.get("id") for record in meeting_records])
    session_meeting_ids = meeting_ids_from_meetingsessions(session_records)

    if meeting_ids:
        selected_meeting_ids = meeting_ids
        selection_source = "manual"
    else:
        selected_meeting_ids = unique_ints(recent_meeting_ids + session_meeting_ids)[: max(meeting_limit, 1)]
        selection_source = "recent_meetings_plus_meetingsessions"

    populated_meetings: list[dict[str, Any]] = []
    discovered_item_ids: list[int] = []

    for meeting_id in selected_meeting_ids:
        meeting_detail_probe, _ = probe(client, f"meetings/{meeting_id}", include_records=True)
        probes.append(meeting_detail_probe)

        docs_probe, docs_records = probe(
            client,
            f"meetings/{meeting_id}/documents",
            params={"limit": item_limit, "offset": 0},
            preferred_key="documents",
            include_records=True,
        )
        probes.append(docs_probe)

        items_probe, item_records = probe(
            client,
            f"meetings/{meeting_id}/meetingitems",
            params={"limit": item_limit, "offset": 0},
            preferred_key="meetingitems",
            include_records=True,
        )
        probes.append(items_probe)

        item_ids = unique_ints([record.get("id") for record in item_records])
        discovered_item_ids.extend(item_ids)

        if docs_records or item_records:
            populated_meetings.append(
                {
                    "meeting_id": meeting_id,
                    "documents_count": len(docs_records),
                    "meetingitems_count": len(item_records),
                    "sample_document_ids": sample_ids(docs_records),
                    "sample_meetingitem_ids": item_ids,
                    "sample_meetingitem_keys": sample_keys(item_records),
                }
            )

    for item_id in unique_ints(discovered_item_ids)[:item_limit]:
        item_probe, _ = probe(client, f"meetingitems/{item_id}", include_records=True)
        probes.append(item_probe)
        item_docs_probe, _ = probe(
            client,
            f"meetingitems/{item_id}/documents",
            params={"limit": item_limit, "offset": 0},
            preferred_key="documents",
            include_records=True,
        )
        probes.append(item_docs_probe)

    working_paths = [entry["path"] for entry in probes if entry.get("ok")]

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "municipality": municipality,
        "base_url": base_url,
        "meeting_limit": meeting_limit,
        "item_limit": item_limit,
        "scan_limit": scan_limit,
        "manual_meeting_ids": meeting_ids,
        "summary": {
            "meeting_selection_source": selection_source,
            "sampled_meeting_ids": selected_meeting_ids,
            "recent_meeting_ids": recent_meeting_ids,
            "meetingsession_meeting_ids": session_meeting_ids[:25],
            "sampled_meeting_item_ids": unique_ints(discovered_item_ids),
            "working_path_count": len(working_paths),
            "working_paths": working_paths,
            "meeting_items_discovered": len(unique_ints(discovered_item_ids)),
            "populated_meeting_count": len(populated_meetings),
            "populated_meetings": populated_meetings,
        },
        "probes": probes,
        "notes": [
            "This report uses documented nested routes and a small number of sampled meetings.",
            "Manual meeting IDs can be supplied to probe known meetings with likely agenda items or documents.",
            "When manual IDs return 404 on /meetings/{id}, they are likely not meeting IDs.",
            "meetingsessions can expose historical meeting IDs through container.meeting.id.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Discover GemeenteOplossingen meeting relations.")
    parser.add_argument("--municipality", default="huizen")
    parser.add_argument("--meeting-limit", type=int, default=3)
    parser.add_argument("--item-limit", type=int, default=10)
    parser.add_argument("--meeting-ids", default="")
    parser.add_argument("--scan-limit", type=int, default=100)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    report = discover_relations(
        municipality=args.municipality,
        meeting_limit=args.meeting_limit,
        item_limit=args.item_limit,
        meeting_ids=parse_ids(args.meeting_ids),
        scan_limit=args.scan_limit,
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
