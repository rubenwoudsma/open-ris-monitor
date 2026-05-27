"""Command-line entry point for the milestone 1 metadata-only harvest."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from open_ris_monitor.connectors.gemeenteoplossingen import GemeenteOplossingenConnector
from open_ris_monitor.models.harvest_run import HarvestRun

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
    """Create the configured source connector.

    Milestone 1 only supports GemeenteOplossingen.
    """
    source_system = config["source_system"]
    connector_name = source_system["connector"]
    if connector_name != "gemeenteoplossingen":
        raise ValueError(f"Unsupported connector for milestone 1: {connector_name}")

    return GemeenteOplossingenConnector(base_url=source_system["base_url"])


def write_json(path: Path, payload: Any) -> None:
    """Write JSON with stable formatting."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2, sort_keys=True, default=str)
        file.write("\n")


def run_harvest(municipality: str, limit: int) -> HarvestRun:
    """Run a document-first, metadata-only harvest."""
    started_at = datetime.now(timezone.utc)
    config = load_municipality_config(municipality)
    connector = create_connector(config)

    documents = connector.fetch_latest_documents(limit=limit)

    raw_dir = REPO_ROOT / "data" / "raw" / "latest"
    write_json(raw_dir / "documents.json", documents)

    municipality_config = config["municipality"]
    source_system_config = config["source_system"]
    harvest_run = HarvestRun(
        id=f"harvest-{municipality}-{started_at.strftime('%Y%m%dT%H%M%SZ')}",
        municipality_id=municipality_config["id"],
        source_system_id=source_system_config["id"],
        started_at=started_at,
        finished_at=datetime.now(timezone.utc),
        status="success",
        documents_seen=len(documents),
    )
    write_json(raw_dir / "harvest_run.json", harvest_run.model_dump(mode="json"))

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
        f"{harvest_run.documents_seen} documents seen."
    )


if __name__ == "__main__":
    main()
