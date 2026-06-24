"""Command-line entry point for Open RIS Monitor harvests."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from open_ris_monitor.connectors.gemeenteoplossingen import GemeenteOplossingenConnector
from open_ris_monitor.enrichers.checksum import (
    enrich_document_versions,
    load_previous_versions,
    merge_document_versions,
)
from open_ris_monitor.exporters.json_exporter import write_json, write_jsonl
from open_ris_monitor.models.harvest_run import HarvestRun
from open_ris_monitor.normalizers.gemeenteoplossingen import normalize_documents
from open_ris_monitor.normalizers.organization import normalize_organization_harvest
from open_ris_monitor.normalizers.relations import normalize_relation_harvest
from open_ris_monitor.pipeline.profiles import HARVEST_PROFILE_NAMES, resolve_harvest_options
from open_ris_monitor.pipeline.relations import collect_raw_relation_harvest

REPO_ROOT = Path(__file__).resolve().parents[3]


def load_municipality_config(slug: str) -> dict[str, Any]:
    """Load a municipality configuration file."""
    config_path = REPO_ROOT / "config" / "municipalities" / f"{slug}.yml"
    if not config_path.exists():
        raise FileNotFoundError(f"Municipality config not found: {config_path}")
    with config_path.open("r", encoding="utf-8") as file:
        payload = yaml.safe_load(file)
    if not isinstance(payload, dict):
        raise ValueError(f"Expected YAML object in {config_path}")
    return payload


def _as_float(value: Any, default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    return float(value)


def parse_max_documents(value: Any) -> int | None:
    """Parse max_documents from CLI or workflow input.

    Empty, None and 0 mean: no explicit max_documents limit.
    """
    if value is None or value == "":
        return None
    parsed = int(value)
    if parsed <= 0:
        return None
    return parsed


def build_connector(config: dict[str, Any]) -> GemeenteOplossingenConnector:
    """Build the configured source connector."""
    source_system = config["source_system"]
    connector_name = source_system["connector"]
    if connector_name != "gemeenteoplossingen":
        raise ValueError(f"Unsupported connector: {connector_name}")
    return GemeenteOplossingenConnector(
        base_url=source_system["base_url"],
        timeout_seconds=int(source_system.get("timeout_seconds", 30)),
        request_delay_seconds=_as_float(source_system.get("request_delay_seconds"), 0.0),
    )


def _to_public_dicts(records: list[Any]) -> list[dict[str, Any]]:
    """Convert canonical model records to plain dictionaries for JSONL export."""
    result: list[dict[str, Any]] = []
    for record in records:
        if hasattr(record, "to_dict"):
            result.append(record.to_dict())
        elif hasattr(record, "model_dump"):
            result.append(record.model_dump(mode="json"))
        elif isinstance(record, dict):
            result.append(record)
        else:
            raise TypeError(f"Cannot export relation record of type {type(record)!r}")
    return result


def _read_json(path: Path) -> dict[str, Any]:
    """Read a JSON object when it exists, otherwise return an empty object."""
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as file:
        payload = json.load(file)
    return payload if isinstance(payload, dict) else {}


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    """Read JSONL dictionaries when a public export already exists."""
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            stripped = line.strip()
            if not stripped:
                continue
            payload = json.loads(stripped)
            if isinstance(payload, dict):
                records.append(payload)
    return records


def _jsonl_count(path: Path) -> int:
    """Count non-empty records in an existing JSONL export."""
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8") as file:
        return sum(1 for line in file if line.strip())


def _record_to_dict(record: Any) -> dict[str, Any]:
    if isinstance(record, dict):
        return record
    if hasattr(record, "to_dict"):
        payload = record.to_dict()
    elif hasattr(record, "model_dump"):
        payload = record.model_dump(mode="json")
    else:
        raise TypeError(f"Cannot convert record of type {type(record)!r}")
    if not isinstance(payload, dict):
        raise TypeError(f"Expected record dictionary, got {type(payload)!r}")
    return payload


def _document_merge_key(record: dict[str, Any]) -> str:
    """Return a stable key for merging latest-run records into the dataset export."""
    source_system_id = str(record.get("source_system_id") or "")
    for key in ("source_id", "source_object_id", "id"):
        value = record.get(key)
        if value not in (None, ""):
            return f"{source_system_id}:{key}:{value}"
    return json.dumps(record, sort_keys=True, default=str)


def _merge_document_records(existing: list[dict[str, Any]], current: list[Any]) -> list[dict[str, Any]]:
    """Merge current harvest documents into the existing public dataset documents.

    Latest harvests are intentionally narrow. They should update or add records, not
    shrink the public dataset to only the latest-run slice.
    """
    merged: dict[str, dict[str, Any]] = {}
    order: list[str] = []

    for record in existing:
        key = _document_merge_key(record)
        if key not in merged:
            order.append(key)
        merged[key] = record

    for record in current:
        payload = _record_to_dict(record)
        key = _document_merge_key(payload)
        if key not in merged:
            order.append(key)
        merged[key] = payload

    return [merged[key] for key in order]


def _latest_full_backfill_at(
    *,
    mode: str,
    generated_at: str,
    previous_latest: dict[str, Any],
) -> str | None:
    """Return the latest reliable full backfill timestamp, without inventing one."""
    if mode == "full":
        return generated_at
    previous_full_backfill = previous_latest.get("last_full_backfill_at")
    if isinstance(previous_full_backfill, str) and previous_full_backfill:
        return previous_full_backfill
    if previous_latest.get("mode") == "full" and isinstance(previous_latest.get("generated_at"), str):
        return previous_latest["generated_at"]
    return None


def _write_public_relation_exports(
    public_dir: Path,
    normalized_relations: dict[str, list[Any]],
) -> dict[str, str]:
    """Write canonical relation exports and return latest.json output entries."""
    relation_outputs = {
        "meetings": "meetings.jsonl",
        "meeting_items": "meeting_items.jsonl",
        "meeting_documents": "meeting_documents.jsonl",
        "meeting_item_documents": "meeting_item_documents.jsonl",
    }
    write_jsonl(
        public_dir / relation_outputs["meetings"],
        _to_public_dicts(normalized_relations.get("meetings", [])),
    )
    write_jsonl(
        public_dir / relation_outputs["meeting_items"],
        _to_public_dicts(normalized_relations.get("meeting_items", [])),
    )
    write_jsonl(
        public_dir / relation_outputs["meeting_documents"],
        _to_public_dicts(normalized_relations.get("meeting_documents", [])),
    )
    write_jsonl(
        public_dir / relation_outputs["meeting_item_documents"],
        _to_public_dicts(normalized_relations.get("meeting_item_documents", [])),
    )
    return relation_outputs


def _build_latest_outputs(
    *,
    enrich_checksums: bool,
    relation_outputs: dict[str, str] | None = None,
) -> dict[str, str | None]:
    """Build the outputs block for latest.json."""
    outputs: dict[str, str | None] = {
        "documents": "documents.jsonl",
        "harvest_runs": "harvest_runs.jsonl",
        "document_versions": "document_versions.jsonl" if enrich_checksums else None,
    }
    if relation_outputs:
        outputs.update(relation_outputs)
    return outputs


def _dataset_totals(
    *,
    public_dir: Path,
    documents_total: int,
    normalized_relations: dict[str, list[Any]] | None,
) -> dict[str, int]:
    """Return public dataset-wide totals, using current or existing static exports."""
    if normalized_relations is None:
        meetings_total = _jsonl_count(public_dir / "meetings.jsonl")
        agenda_items_total = _jsonl_count(public_dir / "meeting_items.jsonl")
        meeting_document_relations_total = _jsonl_count(public_dir / "meeting_documents.jsonl")
        meeting_item_document_relations_total = _jsonl_count(
            public_dir / "meeting_item_documents.jsonl"
        )
    else:
        meetings_total = len(normalized_relations.get("meetings", []))
        agenda_items_total = len(normalized_relations.get("meeting_items", []))
        meeting_document_relations_total = len(normalized_relations.get("meeting_documents", []))
        meeting_item_document_relations_total = len(
            normalized_relations.get("meeting_item_documents", [])
        )

    return {
        "dataset_documents_total": documents_total,
        "dataset_meetings_total": meetings_total,
        "dataset_agenda_items_total": agenda_items_total,
        "dataset_document_relations_total": (
            meeting_document_relations_total + meeting_item_document_relations_total
        ),
    }


def _write_raw_relation_harvest(raw_dir: Path, relation_harvest: dict[str, Any]) -> None:
    """Write raw relation harvest artifacts for inspection."""
    write_json(raw_dir / "meetingsessions.json", relation_harvest["meeting_sessions"])
    write_json(raw_dir / "meeting_ids.json", relation_harvest["candidate_meeting_ids"])
    write_json(raw_dir / "meetings.json", relation_harvest["meetings"])
    write_json(raw_dir / "meeting_items.json", relation_harvest["meeting_items"])
    write_json(raw_dir / "meeting_documents.json", relation_harvest["meeting_documents"])
    write_json(raw_dir / "meeting_item_documents.json", relation_harvest["meeting_item_documents"])
    write_json(raw_dir / "relation_harvest_summary.json", relation_harvest["summary"])


def _collect_raw_organization_harvest(
    connector: GemeenteOplossingenConnector,
    *,
    batch_size: int = 100,
) -> dict[str, Any]:
    """Fetch public organisation endpoints for a low-cadence organisation export."""
    groups = connector.fetch_all_groups(batch_size=batch_size)
    group_memberships: dict[str, list[dict[str, Any]]] = {}
    for group in groups:
        group_id = group.get("id")
        if group_id in (None, ""):
            continue
        try:
            group_memberships[str(group_id)] = connector.fetch_persons_by_group_id(group_id)
        except Exception as exc:  # pragma: no cover - defensive around optional API relation
            group_memberships[str(group_id)] = []
            print(f"Waarschuwing: groepsleden voor groep {group_id} konden niet worden opgehaald: {exc}")

    persons = connector.fetch_all_persons(batch_size=batch_size)
    roles = connector.fetch_all_roles(batch_size=batch_size)
    positions = connector.fetch_all_positions(batch_size=batch_size)
    return {
        "groups": groups,
        "persons": persons,
        "roles": roles,
        "positions": positions,
        "group_memberships": group_memberships,
        "summary": {
            "groups_seen": len(groups),
            "persons_seen": len(persons),
            "roles_seen": len(roles),
            "positions_seen": len(positions),
            "group_memberships_seen": sum(len(records) for records in group_memberships.values()),
        },
    }


def _write_raw_organization_harvest(raw_dir: Path, organization_harvest: dict[str, Any]) -> None:
    """Write raw organisation harvest artifacts for inspection."""
    write_json(raw_dir / "organization_groups.json", organization_harvest["groups"])
    write_json(raw_dir / "organization_persons.json", organization_harvest["persons"])
    write_json(raw_dir / "organization_roles.json", organization_harvest["roles"])
    write_json(raw_dir / "organization_positions.json", organization_harvest["positions"])
    write_json(raw_dir / "organization_group_memberships.json", organization_harvest["group_memberships"])
    write_json(raw_dir / "organization_harvest_summary.json", organization_harvest["summary"])


def _write_public_organization_exports(
    public_dir: Path,
    normalized_organization: dict[str, list[Any]],
) -> dict[str, str]:
    """Write public organisation exports and return latest.json output entries."""
    organization_outputs = {
        "organization_groups": "organization_groups.jsonl",
        "organization_persons": "organization_persons.jsonl",
        "organization_roles": "organization_roles.jsonl",
        "organization_positions": "organization_positions.jsonl",
        "organization_group_memberships": "organization_group_memberships.jsonl",
    }
    for key, filename in organization_outputs.items():
        write_jsonl(public_dir / filename, _to_public_dicts(normalized_organization.get(key, [])))
    return organization_outputs


def _existing_public_organization_outputs(public_dir: Path) -> dict[str, str]:
    """Keep monthly organisation files discoverable during daily latest runs."""
    outputs = {
        "organization_groups": "organization_groups.jsonl",
        "organization_persons": "organization_persons.jsonl",
        "organization_roles": "organization_roles.jsonl",
        "organization_positions": "organization_positions.jsonl",
        "organization_group_memberships": "organization_group_memberships.jsonl",
    }
    return {key: filename for key, filename in outputs.items() if (public_dir / filename).exists()}


def run_harvest(
    *,
    municipality: str,
    mode: str,
    limit: int,
    batch_size: int,
    max_documents: int | None,
    enrich_checksums: bool,
    checksum_max_documents: int,
    include_relations: bool = False,
    meeting_scan_limit: int = 250,
    meeting_session_batch_size: int = 100,
    meeting_item_limit: int | None = 1000,
    include_organization: bool = False,
    organization_batch_size: int = 100,
) -> HarvestRun:
    """Run a metadata harvest and optional raw relation harvest."""
    started_at = datetime.now(timezone.utc)
    config = load_municipality_config(municipality)
    connector = build_connector(config)

    if mode == "latest":
        raw_documents = connector.fetch_latest_documents(limit=limit)
    elif mode == "full":
        raw_documents = connector.fetch_all_documents(
            batch_size=batch_size,
            max_documents=max_documents,
        )
    else:
        raise ValueError("mode must be 'latest' or 'full'")

    raw_dir = REPO_ROOT / "data" / "raw" / "latest"
    public_dir = REPO_ROOT / "data" / "public"
    latest_path = public_dir / "latest.json"
    previous_latest = _read_json(latest_path)
    municipality_config = config["municipality"]
    source_system_config = config["source_system"]
    retrieved_at = datetime.now(timezone.utc)

    documents = normalize_documents(
        raw_documents,
        municipality_id=municipality_config["id"],
        municipality_slug=municipality,
        source_system_id=source_system_config["id"],
        build_download_url=connector.build_document_download_url,
        retrieved_at=retrieved_at,
    )

    relation_harvest: dict[str, Any] | None = None
    normalized_relations: dict[str, list[Any]] | None = None
    organization_harvest: dict[str, Any] | None = None
    normalized_organization: dict[str, list[Any]] | None = None
    if include_relations:
        relation_harvest = collect_raw_relation_harvest(
            connector,
            meeting_scan_limit=meeting_scan_limit,
            meeting_session_batch_size=meeting_session_batch_size,
            meeting_item_limit=meeting_item_limit,
        )
        normalized_relations = normalize_relation_harvest(
            relation_harvest,
            municipality_slug=municipality,
            source_system_id=source_system_config["id"],
        )

    if include_organization:
        organization_harvest = _collect_raw_organization_harvest(
            connector,
            batch_size=organization_batch_size,
        )
        normalized_organization = normalize_organization_harvest(
            organization_harvest,
            municipality_slug=municipality,
            source_system_id=source_system_config["id"],
        )

    previous_versions_path = public_dir / "document_versions.jsonl"
    existing_versions = load_previous_versions(previous_versions_path)
    new_versions: list[Any] = []
    merged_versions: list[Any] = existing_versions

    if enrich_checksums:
        new_versions = enrich_document_versions(
            documents,
            download_document=lambda source_id: connector.download_document(source_id),
            retrieved_at=retrieved_at,
            max_documents=checksum_max_documents,
            previous_versions=existing_versions,
            request_delay_seconds=connector.request_delay_seconds,
        )
        merged_versions = merge_document_versions(existing_versions, new_versions)

    finished_at = datetime.now(timezone.utc)
    relation_summary = relation_harvest["summary"] if relation_harvest is not None else {}
    harvest_run = HarvestRun(
        id=f"harvest-{municipality}-{started_at.strftime('%Y%m%dT%H%M%SZ')}",
        municipality_id=municipality_config["id"],
        source_system_id=source_system_config["id"],
        started_at=started_at.isoformat(),
        finished_at=finished_at.isoformat(),
        status="success",
        mode=mode,
        batch_size=batch_size if mode == "full" else None,
        max_documents=max_documents if mode == "full" else None,
        meetings_seen=int(relation_summary.get("meetings_seen", 0)),
        agenda_items_seen=int(relation_summary.get("meeting_items_seen", 0)),
        documents_seen=len(raw_documents),
        documents_normalized=len(documents),
        documents_committed=0,
        documents_downloaded_temporarily=len(new_versions),
    )

    write_json(raw_dir / "documents.json", raw_documents)
    write_json(raw_dir / "harvest_run.json", harvest_run)
    if relation_harvest is not None:
        _write_raw_relation_harvest(raw_dir, relation_harvest)
    if organization_harvest is not None:
        _write_raw_organization_harvest(raw_dir, organization_harvest)

    documents_path = public_dir / "documents.jsonl"
    if mode == "latest":
        public_documents = _merge_document_records(_read_jsonl(documents_path), documents)
    else:
        public_documents = _to_public_dicts(documents)
    write_jsonl(documents_path, public_documents)
    write_jsonl(public_dir / "harvest_runs.jsonl", [harvest_run])
    if enrich_checksums:
        write_jsonl(previous_versions_path, merged_versions)

    relation_outputs: dict[str, str] = {}
    if normalized_relations is not None:
        relation_outputs = _write_public_relation_exports(public_dir, normalized_relations)

    organization_outputs: dict[str, str] = _existing_public_organization_outputs(public_dir)
    if normalized_organization is not None:
        organization_outputs = _write_public_organization_exports(public_dir, normalized_organization)

    generated_at = datetime.now(timezone.utc).isoformat()
    latest_payload = {
        "municipality": municipality,
        "municipality_id": municipality_config["id"],
        "source_system_id": source_system_config["id"],
        "harvest_run_id": harvest_run.id,
        "generated_at": generated_at,
        "mode": mode,
        "run_type": mode,
        "documents_seen": len(public_documents),
        "documents_normalized": len(public_documents),
        "documents_seen_in_run": len(raw_documents),
        "documents_normalized_in_run": len(documents),
        "documents_versioned": len(new_versions),
        "checksums_enabled": enrich_checksums,
        "relations_enabled": include_relations,
        "relations_summary": relation_summary,
        "organization_enabled": include_organization,
        "organization_summary": organization_harvest["summary"] if organization_harvest is not None else {},
        "last_full_backfill_at": _latest_full_backfill_at(
            mode=mode,
            generated_at=generated_at,
            previous_latest=previous_latest,
        ),
        **_dataset_totals(
            public_dir=public_dir,
            documents_total=len(public_documents),
            normalized_relations=normalized_relations,
        ),
        "outputs": _build_latest_outputs(
            enrich_checksums=enrich_checksums,
            relation_outputs={**relation_outputs, **organization_outputs},
        ),
    }
    write_json(latest_path, latest_payload)
    return harvest_run


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Run Open RIS Monitor harvest.")
    parser.add_argument("--municipality", default="huizen", help="Municipality config slug")
    parser.add_argument(
        "--profile",
        choices=HARVEST_PROFILE_NAMES,
        default=None,
        help="Bounded harvest profile. Explicit CLI options override profile defaults.",
    )
    parser.add_argument("--mode", choices=["latest", "full"], default=None, help="Harvest mode")
    parser.add_argument("--limit", type=int, default=None, help="Number of latest documents to fetch")
    parser.add_argument("--batch-size", type=int, default=None, help="Batch size for full harvest")
    parser.add_argument("--max-documents", default=None, help="Maximum documents for full harvest")
    parser.add_argument(
        "--enrich-checksums",
        action="store_true",
        help="Download selected documents temporarily and calculate SHA-256 checksums",
    )
    parser.add_argument(
        "--checksum-max-documents",
        type=int,
        default=50,
        help="Maximum documents to checksum per run",
    )
    parser.add_argument(
        "--include-relations",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Also collect raw meeting, meeting-item and document relation data",
    )
    parser.add_argument(
        "--meeting-scan-limit",
        type=int,
        default=None,
        help="Maximum number of meetingsession records to scan when relations are enabled",
    )
    parser.add_argument(
        "--meeting-session-batch-size",
        type=int,
        default=None,
        help="Batch size for meetingsession scanning when relations are enabled",
    )
    parser.add_argument(
        "--meeting-item-limit",
        default=None,
        help="Maximum number of meeting items to inspect when relations are enabled. Use 0 for no limit.",
    )
    parser.add_argument(
        "--include-organization",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Also collect public council organisation data. The backfill profile enables this by default.",
    )
    parser.add_argument(
        "--organization-batch-size",
        type=int,
        default=None,
        help="Batch size for organisation endpoint pagination.",
    )
    return parser.parse_args(argv)


def resolve_cli_harvest_options(args: argparse.Namespace) -> dict[str, Any]:
    """Resolve profile defaults and explicit CLI overrides into run_harvest options."""
    overrides: dict[str, Any] = {}
    if args.mode is not None:
        overrides["mode"] = args.mode
    if args.limit is not None:
        overrides["limit"] = args.limit
    if args.batch_size is not None:
        overrides["batch_size"] = args.batch_size
    if args.max_documents is not None:
        overrides["max_documents"] = parse_max_documents(args.max_documents)
    if args.include_relations is not None:
        overrides["include_relations"] = args.include_relations
    if args.meeting_scan_limit is not None:
        overrides["meeting_scan_limit"] = args.meeting_scan_limit
    if args.meeting_session_batch_size is not None:
        overrides["meeting_session_batch_size"] = args.meeting_session_batch_size
    if args.meeting_item_limit is not None:
        overrides["meeting_item_limit"] = parse_max_documents(args.meeting_item_limit)
    if args.include_organization is not None:
        overrides["include_organization"] = args.include_organization
    if args.organization_batch_size is not None:
        overrides["organization_batch_size"] = args.organization_batch_size
    return resolve_harvest_options(args.profile, overrides)


def main() -> None:
    """CLI entrypoint."""
    args = parse_args()
    harvest_options = resolve_cli_harvest_options(args)
    harvest_run = run_harvest(
        municipality=args.municipality,
        mode=harvest_options["mode"],
        limit=harvest_options["limit"],
        batch_size=harvest_options["batch_size"],
        max_documents=harvest_options["max_documents"],
        enrich_checksums=args.enrich_checksums,
        checksum_max_documents=args.checksum_max_documents,
        include_relations=harvest_options["include_relations"],
        meeting_scan_limit=harvest_options["meeting_scan_limit"],
        meeting_session_batch_size=harvest_options["meeting_session_batch_size"],
        meeting_item_limit=harvest_options["meeting_item_limit"],
        include_organization=harvest_options["include_organization"],
        organization_batch_size=harvest_options["organization_batch_size"],
    )
    print(
        f"Harvest {harvest_run.id} completed: "
        f"{harvest_run.documents_seen} documents seen, "
        f"{harvest_run.meetings_seen} meetings seen, "
        f"{harvest_run.agenda_items_seen} meeting items seen, "
        f"{harvest_run.documents_downloaded_temporarily} documents downloaded temporarily."
    )


if __name__ == "__main__":
    main()
