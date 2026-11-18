"""Generate a GitHub Actions summary from published quality reports."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


def generate_summary(public_dir: Path, summary_path: Path) -> None:
    """Generate and write a markdown summary of quality reports."""
    quality_dir = public_dir / "quality"

    dashboard_path = quality_dir / "dashboard.json"
    unlinked_docs_path = quality_dir / "unlinked_documents.json"
    meetings_no_docs_path = quality_dir / "meetings_without_documents.json"

    summary_content = "\n## Data Quality Report\n\n"

    if not public_dir.exists() or not quality_dir.exists():
        summary_content += "Quality reports not found. The harvest may have failed before reports were generated.\n"
        with summary_path.open("a", encoding="utf-8") as summary_file:
            summary_file.write(summary_content)
        return

    if dashboard_path.exists():
        dashboard = json.loads(dashboard_path.read_text(encoding="utf-8"))
        totals = dashboard.get("totals", {})
        summary_content += "### Totals\n"
        summary_content += "| Entity | Count |\n"
        summary_content += "| --- | ---: |\n"
        summary_content += f"| Documents | {totals.get('documents', 'N/A')} |\n"
        summary_content += f"| Meetings | {totals.get('meetings', 'N/A')} |\n"
        summary_content += f"| Agenda Items | {totals.get('meeting_items', 'N/A')} |\n"
        summary_content += "\n"

    summary_content += "### Key Quality Metrics\n"
    summary_content += "| Metric | Value |\n"
    summary_content += "| --- | ---: |\n"

    if unlinked_docs_path.exists():
        unlinked = json.loads(unlinked_docs_path.read_text(encoding="utf-8"))
        count = unlinked.get("unlinked_documents_count")
        total = unlinked.get("documents_total", 0)
        if isinstance(count, int):
            percent = (count / total * 100) if total > 0 else 0
            summary_content += f"| Unlinked Documents | {count} ({percent:.2f}%) |\n"
        else:
            summary_content += f"| Unlinked Documents | {count or 'N/A'} |\n"
    else:
        summary_content += "| Unlinked Documents | Not available |\n"

    if meetings_no_docs_path.exists():
        meetings_no_docs = json.loads(meetings_no_docs_path.read_text(encoding="utf-8"))
        count = meetings_no_docs.get("meetings_without_documents_count")
        total = meetings_no_docs.get("meetings_total", 0)
        if isinstance(count, int):
            percent = (count / total * 100) if total > 0 else 0
            summary_content += f"| Meetings without Documents | {count} ({percent:.2f}%) |\n"
        else:
            summary_content += f"| Meetings without Documents | {count or 'N/A'} |\n"
    else:
        summary_content += "| Meetings without Documents | Not available |\n"

    with summary_path.open("a", encoding="utf-8") as summary_file:
        summary_file.write(summary_content)


def main() -> None:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="Generate GitHub Actions summary from quality reports."
    )
    parser.add_argument("--public-dir", type=Path, default=Path("data/public"))
    args = parser.parse_args()

    summary_path_str = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_path_str:
        print(
            "Error: GITHUB_STEP_SUMMARY environment variable not set. "
            "This script is intended to be run in GitHub Actions."
        )
        exit(1)

    generate_summary(args.public_dir, Path(summary_path_str))


if __name__ == "__main__":
    main()
