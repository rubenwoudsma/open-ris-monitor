from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
import yaml

DEFAULT_BASE_URL = "https://ris.gemeenteraadhuizen.nl/api/v2/"


def load_config(municipality: str) -> dict[str, Any]:
    config_path = Path("config") / "municipalities" / f"{municipality}.yml"
    if not config_path.exists():
        raise FileNotFoundError(f"Municipality config not found: {config_path}")
    with config_path.open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}
    if not isinstance(loaded, dict):
        raise ValueError(f"Expected mapping in {config_path}")
    return loaded


def get_nested(config: dict[str, Any], *keys: str, default: Any = None) -> Any:
    current: Any = config
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def get_base_url(config: dict[str, Any]) -> str:
    candidates = [
        get_nested(config, "source", "base_url"),
        get_nested(config, "source_system", "base_url"),
        get_nested(config, "source", "api_base_url"),
        get_nested(config, "source_system", "api_base_url"),
        get_nested(config, "municipality", "source", "base_url"),
        get_nested(config, "municipality", "source_system", "base_url"),
        config.get("base_url") if isinstance(config, dict) else None,
    ]
    for candidate in candidates:
        if isinstance(candidate, str) and candidate.strip():
            return candidate.rstrip("/") + "/"
    return DEFAULT_BASE_URL


def parse_ids(value: str | None) -> list[int]:
    if not value or not value.strip():
        return []
    ids: list[int] = []
    for part in value.split(","):
        stripped = part.strip()
        if not stripped:
            continue
        try:
            ids.append(int(stripped))
        except ValueError as exc:
            raise ValueError(f"Invalid meeting id {stripped!r}. Use comma-separated integers.") from exc
    return ids


def result_object(payload: dict[str, Any]) -> dict[str, Any]:
    result = payload.get("result", {})
    return result if isinstance(result, dict) else {}


def first_list_from_result(result: dict[str, Any]) -> list[Any]:
    for value in result.values():
        if isinstance(value, list):
            return value
    return []


def classify_response(payload: Any) -> str:
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


def extract_sample_ids(items: list[Any]) -> list[int]:
    ids: list[int] = []
    for item in items:
        if isinstance(item, dict) and "id" in item:
            try:
                ids.append(int(item["id"]))
            except (TypeError, ValueError):
                continue
    return ids


def probe(session: requests.Session, base_url: str, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    url = base_url.rstrip("/") + "/" + path.lstrip("/")
    try:
        response = session.get(url, params=params, timeout=30)
        status_code = response.status_code
        response.raise_for_status()
        payload = response.json()
        result = result_object(payload) if isinstance(payload, dict) else {}
        sample_items = first_list_from_result(result)
        sample = sample_items[0] if sample_items and isinstance(sample_items[0], dict) else None
        return {
            "path": path,
            "url": response.url,
            "ok": True,
            "status_code": status_code,
            "error": None,
            "response_shape": classify_response(payload),
            "result_keys": list(result.keys()),
            "sample_keys": list(sample.keys()) if sample else [],
            "sample_count": len(sample_items),
            "sample_ids": extract_sample_ids(sample_items),
            "total_count": result.get("totalCount"),
            "sample_records": sample_items[:3] if sample_items else [],
        }
    except requests.HTTPError as exc:
        return {
            "path": path,
            "url": getattr(exc.response, "url", url),
            "ok": False,
            "status_code": getattr(exc.response, "status_code", None),
            "error": f"HTTP {getattr(exc.response, 'status_code', 'unknown')}",
            "response_shape": None,
            "result_keys": [],
            "sample_keys": [],
            "sample_count": None,
            "sample_ids": [],
            "total_count": None,
            "sample_records": [],
        }
    except Exception as exc:  # pragma: no cover - defensive for workflow diagnostics
        return {
            "path": path,
            "url": url,
            "ok": False,
            "status_code": None,
            "error": str(exc),
            "response_shape": None,
            "result_keys": [],
            "sample_keys": [],
            "sample_count": None,
            "sample_ids": [],
            "total_count": None,
            "sample_records": [],
        }


def discover_relations(
    *,
    municipality: str,
    base_url: str,
    meeting_limit: int,
    item_limit: int,
    meeting_ids: list[int] | None = None,
) -> dict[str, Any]:
    session = requests.Session()
    meeting_ids = meeting_ids or []

    probes: list[dict[str, Any]] = []

    meetings_probe = probe(session, base_url, "meetings", {"limit": meeting_limit, "offset": 0})
    probes.append(meetings_probe)
    probes.append(probe(session, base_url, "dmus", {"limit": 10, "offset": 0}))
    probes.append(probe(session, base_url, "events", {"limit": 3, "offset": 0}))
    probes.append(probe(session, base_url, "meetingsessions", {"limit": 3, "offset": 0}))

    if meeting_ids:
        sampled_meeting_ids = meeting_ids
        meeting_selection_source = "manual"
    else:
        sampled_meeting_ids = meetings_probe.get("sample_ids", [])
        meeting_selection_source = "meetings_endpoint_sample"

    sampled_meeting_item_ids: list[int] = []
    populated_meetings: list[dict[str, Any]] = []

    for meeting_id in sampled_meeting_ids:
        meeting_detail = probe(session, base_url, f"meetings/{meeting_id}")
        meeting_documents = probe(
            session,
            base_url,
            f"meetings/{meeting_id}/documents",
            {"limit": item_limit, "offset": 0},
        )
        meeting_items = probe(
            session,
            base_url,
            f"meetings/{meeting_id}/meetingitems",
            {"limit": item_limit, "offset": 0},
        )

        probes.extend([meeting_detail, meeting_documents, meeting_items])

        item_ids = meeting_items.get("sample_ids", []) or []
        doc_ids = meeting_documents.get("sample_ids", []) or []
        sampled_meeting_item_ids.extend(item_ids)

        if item_ids or doc_ids:
            populated_meetings.append(
                {
                    "meeting_id": meeting_id,
                    "meetingitems_count": meeting_items.get("sample_count", 0),
                    "meetingitems_total_count": meeting_items.get("total_count"),
                    "documents_count": meeting_documents.get("sample_count", 0),
                    "documents_total_count": meeting_documents.get("total_count"),
                    "sample_meetingitem_ids": item_ids,
                    "sample_document_ids": doc_ids,
                    "sample_meetingitem_keys": meeting_items.get("sample_keys", []),
                    "sample_document_keys": meeting_documents.get("sample_keys", []),
                }
            )

    # Probe a few meeting item detail and document relation endpoints when found.
    for meeting_item_id in sampled_meeting_item_ids[:item_limit]:
        probes.append(probe(session, base_url, f"meetingitems/{meeting_item_id}"))
        probes.append(
            probe(
                session,
                base_url,
                f"meetingitems/{meeting_item_id}/documents",
                {"limit": item_limit, "offset": 0},
            )
        )

    working_paths = [entry["path"] for entry in probes if entry.get("ok")]

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "municipality": municipality,
        "base_url": base_url,
        "meeting_limit": meeting_limit,
        "item_limit": item_limit,
        "manual_meeting_ids": meeting_ids,
        "summary": {
            "meeting_selection_source": meeting_selection_source,
            "sampled_meeting_ids": sampled_meeting_ids,
            "sampled_meeting_item_ids": sampled_meeting_item_ids,
            "working_path_count": len(working_paths),
            "working_paths": working_paths,
            "meeting_items_discovered": len(sampled_meeting_item_ids),
            "populated_meeting_count": len(populated_meetings),
            "populated_meetings": populated_meetings,
        },
        "probes": probes,
        "notes": [
            "This report uses documented nested routes and a small number of sampled meetings.",
            "Manual meeting IDs can be supplied to probe known meetings with likely agenda items or documents.",
            "A 200 response with zero sample_count can still be a valid relationship endpoint for meetings without documents or items.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Discover GemeenteOplossingen meeting relation endpoints.")
    parser.add_argument("--municipality", default="huizen")
    parser.add_argument("--meeting-limit", type=int, default=3)
    parser.add_argument("--item-limit", type=int, default=5)
    parser.add_argument("--meeting-ids", default="")
    parser.add_argument(
        "--output",
        default="data/public/quality/gemeenteoplossingen_relation_discovery.json",
    )
    args = parser.parse_args()

    config = load_config(args.municipality)
    base_url = get_base_url(config)
    manual_ids = parse_ids(args.meeting_ids)

    report = discover_relations(
        municipality=args.municipality,
        base_url=base_url,
        meeting_limit=args.meeting_limit,
        item_limit=args.item_limit,
        meeting_ids=manual_ids,
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote relation discovery report to {output_path}")


if __name__ == "__main__":
    main()
