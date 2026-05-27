from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from open_ris_monitor.connectors.gemeenteoplossingen import GemeenteOplossingenConnector


def load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2, default=str)
        file.write("\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run RIS harvest pipeline.")
    parser.add_argument("--config", required=True, help="Path to municipality YAML config.")
    args = parser.parse_args()

    config_path = Path(args.config)
    config = load_config(config_path)

    municipality = config["municipality"]
    source_system = config["source_system"]
    slug = municipality["slug"]

    if source_system["connector"] != "gemeenteoplossingen":
        raise ValueError(f"Unsupported connector: {source_system['connector']}")

    connector = GemeenteOplossingenConnector(base_url=source_system["base_url"])

    # Scaffold implementation. Endpoint names may need to be adjusted after source inspection.
    meetings = connector.fetch_meetings()
    agenda_items = connector.fetch_agenda_items()
    documents = connector.fetch_documents()

    raw_dir = Path("data/raw/latest") / slug
    write_json(raw_dir / "meetings.json", meetings)
    write_json(raw_dir / "agenda_items.json", agenda_items)
    write_json(raw_dir / "documents.json", documents)

    public_dir = Path("data/public")
    latest = {
        "municipality": municipality,
        "source_system": source_system,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "counts": {
            "meetings_raw": len(meetings),
            "agenda_items_raw": len(agenda_items),
            "documents_raw": len(documents),
        },
        "status": "raw_harvest_completed",
    }
    write_json(public_dir / "latest.json", latest)

    print(json.dumps(latest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
