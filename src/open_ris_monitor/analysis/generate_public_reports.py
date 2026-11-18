from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from open_ris_monitor.analysis.document_identity import (
    analyze_document_identity,
    analyze_document_types,
)
from open_ris_monitor.analysis.unlinked_documents import (
    analyze_unlinked_documents,
)
from open_ris_monitor.analysis.meetings_without_documents import (
    analyze_meetings_without_documents,
)
from open_ris_monitor.analysis.dashboard import read_jsonl_optional, write_dashboard_summary
from open_ris_monitor.exporters.json_exporter import write_json
from open_ris_monitor.quality.report import write_quality_report


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

    # These are compact public exports, not serialized internal domain models.
    documents = read_jsonl(documents_path)
    meetings = read_jsonl_optional(public_dir / "meetings.jsonl")
    meeting_documents = read_jsonl_optional(public_dir / "meeting_documents.jsonl")
    meeting_item_documents = read_jsonl_optional(public_dir / "meeting_item_documents.jsonl")

    identity_report = analyze_document_identity(documents)
    type_report = analyze_document_types(documents)
    meetings_report = analyze_meetings_without_documents(
        meetings, meeting_documents, meeting_item_documents
    )
    unlinked_docs_report = analyze_unlinked_documents(
        documents, [meeting_documents, meeting_item_documents]
    )

    identity_path = quality_dir / "id_stability.json"
    type_path = quality_dir / "document_types.json"
    meetings_path = quality_dir / "meetings_without_documents.json"
    unlinked_docs_path = quality_dir / "unlinked_documents.json"

    write_json(identity_path, identity_report)
    write_json(type_path, type_report)
    write_json(meetings_path, meetings_report)
    write_json(unlinked_docs_path, unlinked_docs_report)

    quality_report = write_quality_report(public_dir)
    dashboard_report = write_dashboard_summary(public_dir)
    summary_path = quality_dir / "summary.json"
    dashboard_path = quality_dir / "dashboard.json"
    issues_path = quality_dir / "issues.jsonl"

    update_latest(
        public_dir,
        {
            "id_stability": "quality/id_stability.json",
            "document_types": "quality/document_types.json",
            "unlinked_documents": "quality/unlinked_documents.json",
            "meetings_without_documents": "quality/meetings_without_documents.json",
            "quality_summary": "quality/summary.json",
            "quality_issues": "quality/issues.jsonl",
            "dashboard": "quality/dashboard.json",
        },
    )

    return {
        "documents_total": len(documents),
        "id_stability": str(identity_path),
        "document_types": str(type_path),
        "unlinked_documents": str(unlinked_docs_path),
        "meetings_without_documents": str(meetings_path),
        "quality_summary": str(summary_path),
        "quality_issues": str(issues_path),
        "dashboard": str(dashboard_path),
        "dashboard_totals": dashboard_report["totals"],
        "quality_issues_count": len(quality_report["issues"]),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate public quality and analysis reports")
    parser.add_argument("--public-dir", default="data/public")
    args = parser.parse_args()

    result = generate_reports(Path(args.public_dir))
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
