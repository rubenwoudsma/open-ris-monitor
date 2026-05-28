"""Command-line entry point for Open RIS Monitor harvests."""

from __future__ import annotations

import argparse
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

REPO_ROOT = Path(__file__).resolve().parents[3]


def load_municipality_config(slug: str) -> dict[str, Any]:
    """Load the municipality configuration by slug."""
    config_path = REPO_ROOT / "config" / "municipalities" / f"{slug}.yml"
    if not config_path.exists():
        raise FileNotFoundError(f"Municipality config not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as file:
        payload = yaml.safe_load(file)

    if not isinstance(payload, dict):
        raise ValueError(f"Expected YAML object in {config_path}")

    return payload


def parse_max_documents(value: int | str | None) -> int | None:
    """Interpret max document input values.

    GitHub Actions inputs are strings, while tests and direct Python calls may pass
    integers. A value of 0, an empty string, or None means "no explicit cap".
    """
    if value is None:
        return None

    if isinstance(value, str):
        value = value.strip()
        if value == "":
            return None
        parsed = int(value)
    else:
        parsed = int(value)

    if parsed == 0:
        return None
    if parsed < 0:
        raise ValueError("max_documents must be 0 or greater")
    return parsed


def _as_float(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    return float(value)


def build_connector(config: dict[str, Any]) -> GemeenteOplossingenConnector:
    source_system = config["source_system"]
    connector_name = source_system["connector"]

    if connector_name != "gemeenteoplossingen":
        raise ValueError(f"Unsupported connector: {connector_name}")

    return GemeenteOplossingenConnector(
        base_url=source_system["base_url"],
        timeout_seconds=int(source_system.get("timeout_seconds", 30)),
        request_delay_seconds=_as_float(source_system.get("request_delay_seconds"), 0.0),
    )


def run_harvest(
    *,
    municipality: str,
    mode: str,
    limit: int,
    batch_size: int,
    max_documents: int | None,
    enrich_checksums: bool,
    checksum_max_documents: int,
) -> HarvestRun:
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

    previous_versions_path = public_dir / "document_versions.jsonl"
    existing_versions = load_previous_versions(previous_versions_path)
    new_versions = []
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

    harvest_run = HarvestRun(
        id=f"harvest-{municipality}-{started_at.strftime('%Y%m%dT%H%M%SZ')}",
        municipality_id=municipality_config["id"],
        source_system_id=source_system_config["id"],
        started_at=started_at,
        finished_at=datetime.now(timezone.utc),
        status="success",
        documents_seen=len(raw_documents),
        documents_committed=0,
        documents_downloaded_temporarily=len(new_versions),
    )

    write_json(raw_dir / "documents.json", raw_documents)
    write_json(raw_dir / "harvest_run.json", harvest_run.model_dump(mode="json"))

    write_jsonl(public_dir / "documents.jsonl", documents)
    write_jsonl(public_dir / "harvest_runs.jsonl", [harvest_run])

    if enrich_checksums:
        write_jsonl(previous_versions_path, merged_versions)

    latest_payload = {
        "municipality": municipality,
        "municipality_id": municipality_config["id"],
        "source_system_id": source_system_config["id"],
        "harvest_run_id": harvest_run.id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "documents_seen": len(raw_documents),
        "documents_normalized": len(documents),
        "documents_versioned": len(new_versions),
        "checksums_enabled": enrich_checksums,
        "outputs": {
            "documents": "documents.jsonl",
            "harvest_runs": "harvest_runs.jsonl",
            "document_versions": "document_versions.jsonl" if enrich_checksums else None,
        },
    }
    write_json(public_dir / "latest.json", latest_payload)

    return harvest_run


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Open RIS Monitor harvest.")
    parser.add_argument("--municipality", default="huizen", help="Municipality config slug")
    parser.add_argument("--mode", choices=["latest", "full"], default="latest", help="Harvest mode")
    parser.add_argument("--limit", type=int, default=25, help="Number of latest documents to fetch")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size for full harvest")
    parser.add_argument(
        "--max-documents",
        default=None,
        help="Maximum documents for full harvest. Use 0 or omit for no explicit cap.",
    )
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
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    harvest_run = run_harvest(
        municipality=args.municipality,
        mode=args.mode,
        limit=args.limit,
        batch_size=args.batch_size,
        max_documents=parse_max_documents(args.max_documents),
        enrich_checksums=args.enrich_checksums,
        checksum_max_documents=args.checksum_max_documents,
    )
    print(
        f"Harvest {harvest_run.id} completed: "
        f"{harvest_run.documents_seen} documents seen, "
        f"{harvest_run.documents_downloaded_temporarily} documents downloaded temporarily."
    )


if __name__ == "__main__":
    main()
