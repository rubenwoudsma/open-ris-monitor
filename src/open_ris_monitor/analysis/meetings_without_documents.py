from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from open_ris_monitor.exporters.json_exporter import write_json
from open_ris_monitor.models import Meeting
from open_ris_monitor.models.reports import (
    MeetingsWithoutDocumentsReport,
    MeetingWithoutDocumentsFinding,
)
from open_ris_monitor.models.relations import (
    MeetingDocumentRelation,
    MeetingItemDocumentRelation,
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
            records.append(json.loads(stripped))
    return records


def find_meetings_without_documents(
    meetings: Iterable[Meeting],
    meeting_documents: Iterable[MeetingDocumentRelation],
    meeting_item_documents: Iterable[MeetingItemDocumentRelation],
) -> list[MeetingWithoutDocumentsFinding]:
    """Find meetings that are not linked to any documents."""
    meetings_with_docs: set[str] = set()
    for rel in meeting_documents:
        meetings_with_docs.add(rel.meeting_id)
    for rel in meeting_item_documents:
        meetings_with_docs.add(rel.meeting_id)

    findings: list[MeetingWithoutDocumentsFinding] = []
    for meeting in meetings:
        if meeting.id not in meetings_with_docs:
            findings.append(
                MeetingWithoutDocumentsFinding(
                    meeting_id=meeting.id,
                    meeting_source_id=meeting.source_id,
                    title=meeting.title,
                    date=meeting.date,
                    dmu_name=meeting.dmu_name,
                    url=meeting.url,
                )
            )

    findings.sort(key=lambda f: f.date or date.min, reverse=True)
    return findings


def analyze_meetings_without_documents(
    meetings: list[Meeting],
    meeting_documents: list[MeetingDocumentRelation],
    meeting_item_documents: list[MeetingItemDocumentRelation],
) -> MeetingsWithoutDocumentsReport:
    """Generate a report of meetings without any document relations."""
    findings = find_meetings_without_documents(
        meetings, meeting_documents, meeting_item_documents
    )

    return MeetingsWithoutDocumentsReport(
        generated_at=datetime.now(timezone.utc),
        meetings_total=len(meetings),
        meetings_without_documents_count=len(findings),
        findings=findings,
    )


def main() -> None:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="Find meetings without any linked documents."
    )
    parser.add_argument(
        "--public-dir", type=Path, default=Path("data/public")
    )
    args = parser.parse_args()

    public_dir = args.public_dir
    meetings = [
        Meeting.model_validate(rec)
        for rec in _read_jsonl(public_dir / "meetings.jsonl")
    ]
    meeting_documents = [
        MeetingDocumentRelation.model_validate(rec)
        for rec in _read_jsonl(public_dir / "meeting_documents.jsonl")
    ]
    meeting_item_documents = [
        MeetingItemDocumentRelation.model_validate(rec)
        for rec in _read_jsonl(public_dir / "meeting_item_documents.jsonl")
    ]

    report = analyze_meetings_without_documents(
        meetings, meeting_documents, meeting_item_documents
    )

    output_path = public_dir / "quality" / "meetings_without_documents.json"
    write_json(output_path, report)

    print(
        f"Report generated at {output_path}\n"
        f"Total meetings: {report.meetings_total}\n"
        f"Meetings without documents: {report.meetings_without_documents_count}"
    )


if __name__ == "__main__":
    main()