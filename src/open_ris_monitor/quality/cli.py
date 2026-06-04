from __future__ import annotations

import argparse
import json
from pathlib import Path

from .report import write_quality_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate public quality reports")
    parser.add_argument("--public-dir", default="data/public")
    args = parser.parse_args(argv)

    result = write_quality_report(Path(args.public_dir))
    print(json.dumps({
        "documents_total": result["counts"]["documents"],
        "quality_output": "quality/summary.json",
        "issues_output": "quality/issues.jsonl",
        "latest_run_status": result["harvest"]["latest_run_status"],
    }, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
