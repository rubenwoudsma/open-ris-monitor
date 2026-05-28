from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from open_ris_monitor.connectors.gemeenteoplossingen import GemeenteOplossingenConnector
from open_ris_monitor.exporters.json_exporter import write_json, write_jsonl
from open_ris_monitor.models.harvest_run import HarvestRun
from open_ris_monitor.normalizers.gemeenteoplossingen import normalize_documents


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_config(municipality: str) -> dict[str, Any]:
    path = Path("config") / "municipalities" / f"{municipality}.yml"
    if not path.exists():
        raise FileNotFoundError(f"Municipality config not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def build_connector(config: dict[str, Any]) -> GemeenteOplossingenConnector:
    source = config["source_system"]
    harvest = config.get("harvest", {})
    return GemeenteOplossingenConnector(
        base_url=source["base_url"],
        timeout_seconds=int(harvest.get("timeout_seconds", 30)),
        request_delay_seconds=float(harvest.get("request_delay_seconds", 0.0)),
    )


def parse_max_documents(value: int) -> int | None:
    if value <= 0:
        return None
    return value


def run_harvest(
    *,
    municipality: str,
    mode: str,
    limit: int,
    batch_size: int,
    max_documents: int | None,
) -> None:
    if mode not in {"latest", "full"}:
        raise ValueError("mode must be 'latest' or 'full'")

    started_at = utc_now()
    started_token = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    config = load_config(municipality)
    municipality_config = config["municipality"]
    source_system = config["source_system"]

    municipality_id = municipality_config["id"]
    municipality_slug = municipality_config["slug"]
    source_system_id = source_system["id"]

    harvest_run = HarvestRun(
        id=f"harvest-{municipality_slug}-{started_token}",
        municipality_id=municipality_id,
        source_system_id=source_system_id,
        started_at=started_at,
        mode=mode,
        batch_size=batch_size if mode == "full" else None,
        max_documents=max_documents if mode == "full" else limit,
    )

    connector = build_connector(config)

    if mode == "full":
        raw_documents = connector.fetch_all_documents(
            batch_size=batch_size,
            max_documents=max_documents,
        )
    else:
        raw_documents = connector.fetch_latest_documents(limit=limit)

    retrieved_at = utc_now()
    documents = normalize_documents(
        raw_documents,
        municipality_id=municipality_id,
        municipality_slug=municipality_slug,
        source_system_id=source_system_id,
        build_download_url=connector.build_document_download_url,
        retrieved_at=retrieved_at,
    )

    harvest_run.documents_seen = len(raw_documents)
    harvest_run.documents_normalized = len(documents)
    harvest_run.status = "success"
    harvest_run.finished_at = utc_now()

    raw_dir = Path("data/raw/latest")
    public_dir = Path("data/public")

    write_json(raw_dir / "documents.json", raw_documents)
    write_json(raw_dir / "harvest_run.json", harvest_run.to_dict())

    write_jsonl(public_dir / "documents.jsonl", documents)
    write_jsonl(public_dir / "harvest_runs.jsonl", [harvest_run.to_dict()])
    write_json(
        public_dir / "latest.json",
        {
            "generated_at": harvest_run.finished_at,
            "harvest_run_id": harvest_run.id,
            "municipality": municipality_slug,
            "municipality_id": municipality_id,
            "source_system_id": source_system_id,
            "mode": mode,
            "limit": limit if mode == "latest" else None,
            "batch_size": batch_size if mode == "full" else None,
            "max_documents": max_documents if mode == "full" else None,
            "documents_seen": harvest_run.documents_seen,
            "documents_normalized": harvest_run.documents_normalized,
            "outputs": {
                "documents": "documents.jsonl",
                "harvest_runs": "harvest_runs.jsonl",
            },
        },
    )

    print(json.dumps(harvest_run.to_dict(), ensure_ascii=False, indent=2, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Open RIS Monitor harvest pipeline")
    parser.add_argument("--municipality", required=True)
    parser.add_argument("--mode", choices=["latest", "full"], default="latest")
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--batch-size", type=int, default=100)
    parser.add_argument("--max-documents", type=int, default=500)
    args = parser.parse_args()

    run_harvest(
        municipality=args.municipality,
        mode=args.mode,
        limit=args.limit,
        batch_size=args.batch_size,
        max_documents=parse_max_documents(args.max_documents),
    )


if __name__ == "__main__":
    main()
