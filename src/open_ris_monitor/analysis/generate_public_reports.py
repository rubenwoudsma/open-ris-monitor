from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from open_ris_monitor.analysis.document_identity import (
    analyze_document_identity,
    analyze_document_types,
)
from open_ris_monitor.exporters.json_exporter import write_json


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if not path.exists():
        raise FileNotFoundError(f"JSONL file not found: {path}")

    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            text = line.strip()
            if not text:
                continue
            record = json.loads(text)
            if not isinstance(record, dict):
                raise ValueError(f"Expected JSON object on line {line_number} in {path}")
            records.append(record)
    return records


def update_latest(public_dir: Path, outputs: dict[str, str]) -> None:
    latest_path = public_dir / "latest.json"
    if not latest_path.exists():
        return

    with latest_path.open("r", encoding="utf-8") as handle:
        latest = json.load(handle)

    if not isinstance(latest, dict):
        return

    latest_outputs = latest.setdefault("outputs", {})
    if isinstance(latest_outputs, dict):
        latest_outputs.update(outputs)

    write_json(latest_path, latest)


def generate_reports(public_dir: Path) -> dict[str, Any]:
    documents_path = public_dir / "documents.jsonl"
    quality_dir = public_dir / "quality"
    quality_dir.mkdir(parents=True, exist_ok=True)

    documents = read_jsonl(documents_path)
    identity_report = analyze_document_identity(documents)
    type_report = analyze_document_types(documents)

    identity_path = quality_dir / "id_stability.json"
    type_path = quality_dir / "document_types.json"

    write_json(identity_path, identity_report)
    write_json(type_path, type_report)

    update_latest(
        public_dir,
        {
            "id_stability": "quality/id_stability.json",
            "document_types": "quality/document_types.json",
        },
    )

    return {
        "documents_total": len(documents),
        "id_stability": str(identity_path),
        "document_types": str(type_path),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate public quality and analysis reports")
    parser.add_argument("--public-dir", default="data/public")
    args = parser.parse_args()

    result = generate_reports(Path(args.public_dir))
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
