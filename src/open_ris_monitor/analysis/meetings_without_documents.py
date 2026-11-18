from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from open_ris_monitor.exporters.json_exporter import write_json
from open_ris_monitor.models.reports import (
    MeetingsWithoutDocumentsReport,
    MeetingWithoutDocumentsFinding,
)


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    """Read JSONL records from path. Missing files are treated as empty."""
    if not path.exists():
        return []

    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            record = json.loads(stripped)
            if not isinstance(record, dict):
                raise ValueError(f"Expected JSON object in {path}")
            records.append(record)
    return records


def _parse_date(value: Any) -> date | None:
    if value is None:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def find_meetings_without_documents(
    meetings: Iterable[dict[str, Any]],
    meeting_documents: Iterable[dict[str, Any]],
    meeting_item_documents: Iterable[dict[str, Any]],
) -> list[MeetingWithoutDocumentsFinding]:
    """Find meetings that are not linked to any documents."""
    meetings_with_docs: set[str] = set()
    for relations in (meeting_documents, meeting_item_documents):
        for relation in relations:
            if relation.get("meeting_id"):
                meetings_with_docs.add(str(relation["meeting_id"]))

    findings: list[MeetingWithoutDocumentsFinding] = []
    for meeting in meetings:
        meeting_id = str(meeting["id"])
        if meeting_id not in meetings_with_docs:
            findings.append(
                MeetingWithoutDocumentsFinding(
                    meeting_id=meeting_id,
                    meeting_source_id=str(meeting.get("source_id") or meeting_id),
                    title=meeting.get("title") or meeting.get("description"),
                    date=_parse_date(meeting.get("date")),
                    dmu_name=meeting.get("dmu_name"),
                    url=meeting.get("url"),
                )
            )

    findings.sort(key=lambda f: f.date or date.min, reverse=True)
    return findings


def analyze_meetings_without_documents(
    meetings: list[dict[str, Any]],
    meeting_documents: list[dict[str, Any]],
    meeting_item_documents: list[dict[str, Any]],
) -> MeetingsWithoutDocumentsReport:
    """Generate a report of meetings without any document relations."""
    findings = find_meetings_without_documents(meetings, meeting_documents, meeting_item_documents)

    return MeetingsWithoutDocumentsReport(
        generated_at=datetime.now(timezone.utc),
        meetings_total=len(meetings),
        meetings_without_documents_count=len(findings),
        findings=findings,
    )


def main() -> None:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(description="Find meetings without any linked documents.")
    parser.add_argument("--public-dir", type=Path, default=Path("data/public"))
    args = parser.parse_args()

    public_dir = args.public_dir
    meetings = _read_jsonl(public_dir / "meetings.jsonl")
    meeting_documents = _read_jsonl(public_dir / "meeting_documents.jsonl")
    meeting_item_documents = _read_jsonl(public_dir / "meeting_item_documents.jsonl")

    report = analyze_meetings_without_documents(meetings, meeting_documents, meeting_item_documents)

    output_path = public_dir / "quality" / "meetings_without_documents.json"
    write_json(output_path, report)

    print(
        f"Report generated at {output_path}\n"
        f"Total meetings: {report.meetings_total}\n"
        f"Meetings without documents: {report.meetings_without_documents_count}"
    )


if __name__ == "__main__":
    main()
