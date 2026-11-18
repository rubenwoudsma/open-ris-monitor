"""Generate report schemas; compact JSONL export schemas are maintained explicitly."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from pydantic import BaseModel

from open_ris_monitor.models.reports import (
    MeetingsWithoutDocumentsReport,
    UnlinkedDocumentsReport,
)

# Public JSONL records are projections of internal models, not model dumps.
# Generating their existing contracts from internal models would change the API.
SCHEMA_MAPPING: dict[str, type[BaseModel]] = {
    "meetings_without_documents.schema.json": MeetingsWithoutDocumentsReport,
    "unlinked_documents.schema.json": UnlinkedDocumentsReport,
}


def generate_schemas(schema_dir: Path) -> None:
    """Generate schemas for the two public quality reports."""
    schema_dir.mkdir(parents=True, exist_ok=True)

    for filename, model in SCHEMA_MAPPING.items():
        output_path = schema_dir / filename
        print(f"Generating {output_path}...")

        schema = model.model_json_schema()

        output_path.write_text(
            json.dumps(schema, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


def main() -> None:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(description="Generate public quality-report JSON schemas.")
    parser.add_argument("--schema-dir", type=Path, default=Path("schemas"))
    args = parser.parse_args()
    generate_schemas(args.schema_dir)
    print("\nAll schemas generated successfully.")


if __name__ == "__main__":
    main()
