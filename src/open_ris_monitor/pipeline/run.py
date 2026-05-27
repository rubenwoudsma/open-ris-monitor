"""Command-line entry point for the metadata-only document harvest."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from open_ris_monitor.connectors.gemeenteoplossingen import GemeenteOplossingenConnector
from open_ris_monitor.exporters.json_exporter import write_json, write_jsonl
from open_ris_monitor.models.harvest_run import HarvestRun
from open_ris_monitor.normalizers.gemeenteoplossingen import normalize_documents

REPO_ROOT = Path(__file__).resolve().parents[3]


def load_municipality_config(slug: str) -> dict[str, Any]:
    """Load a municipality YAML config from config/municipalities."""
    config_path = REPO_ROOT / "config" / "municipalities" / f"{slug}.yml"
    if not config_path.exists():
        raise FileNotFoundError(f"Municipality config not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as file:
        payload = yaml.safe_load(file)

    if not isinstance(payload, dict):
        raise ValueError(f"Expected YAML object in {config_path}")

    return payload


def create_connector(config: dict[str, Any]) -> GemeenteOplossingenConnector:
    """Create the configured source connector."""
    source_system = config["source_system"]
    connector_name = source_system["connector"]

    if connector_name != "gemeenteoplossingen":
        raise ValueError(f"Unsupported connector for this MVP: {connector_name}")

    return GemeenteOplossingenConnector(base_url=source_system["base_url"])


def run_harvest(municipality: str, limit: int) -> HarvestRun:
    """Run a document-first, metadata-only harvest and public export."""
    started_at = datetime.now(timezone.utc)
    config = load_municipality_config(municipality)
    connector = create_connector(config)

    raw_documents = connector.fetch_latest_documents(limit=limit)
    retrieved_at = datetime.now(timezone.utc)

    municipality_config = config["municipality"]
    source_system_config = config["source_system"]
    municipality_id = municipality_config["id"]
    source_system_id = source_system_config["id"]

    documents = normalize_documents(
        raw_documents,
        municipality_id=municipality_id,
        source_system_id=source_system_id,
        connector=connector,
        retrieved_at=retrieved_at,
    )

    harvest_run = HarvestRun(
        id=f"harvest-{municipality}-{started_at.strftime('%Y%m%dT%H%M%SZ')}",
        municipality_id=municipality_id,
        source_system_id=source_system_id,
        started_at=started_at,
        finished_at=datetime.now(timezone.utc),
        status="success",
        documents_seen=len(raw_documents),
        documents_normalized=len(documents),
    )

    raw_dir = REPO_ROOT / "data" / "raw" / "latest"
    public_dir = REPO_ROOT / "data" / "public"

    write_json(raw_dir / "documents.json", raw_documents)
    write_json(raw_dir / "harvest_run.json", harvest_run)

    write_jsonl(public_dir / "documents.jsonl", documents)
    write_jsonl(public_dir / "harvest_runs.jsonl", [harvest_run])
    write_json(
        public_dir / "latest.json",
        {
            "municipality": municipality,
            "municipality_id": municipality_id,
            "source_system_id": source_system_id,
            "harvest_run_id": harvest_run.id,
            "generated_at": harvest_run.finished_at,
            "documents_seen": harvest_run.documents_seen,
            "documents_normalized": harvest_run.documents_normalized,
            "outputs": {
                "documents": "documents.jsonl",
                "harvest_runs": "harvest_runs.jsonl",
            },
        },
    )

    return harvest_run


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Run Open RIS Monitor harvest.")
    parser.add_argument("--municipality", default="huizen", help="Municipality config slug")
    parser.add_argument("--limit", type=int, default=500, help="Number of latest documents to fetch")
    return parser.parse_args()


def main() -> None:
    """Run the command-line harvester."""
    args = parse_args()
    harvest_run = run_harvest(municipality=args.municipality, limit=args.limit)
    print(
        f"Harvest {harvest_run.id} completed: "
        f"{harvest_run.documents_seen} documents seen, "
        f"{harvest_run.documents_normalized} documents normalized."
    )


if __name__ == "__main__":
    main()
