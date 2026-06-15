from __future__ import annotations

import json
from pathlib import Path

from open_ris_monitor.quality.report import build_quality_report


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def test_quality_report_exposes_relation_and_metadata_diagnostics(tmp_path: Path) -> None:
    public_dir = tmp_path
    _write_jsonl(
        public_dir / "documents.jsonl",
        [
            {
                "id": "doc-1",
                "normalized_document_type": "proposal",
                "download_url": "https://example.invalid/doc-1.pdf",
                "file_size_bytes": 100,
            },
            {"id": "doc-2", "normalized_document_type": "unknown"},
        ],
    )
    _write_jsonl(public_dir / "harvest_runs.jsonl", [{"id": "run-1", "status": "success", "documents_seen": 2}])
    _write_jsonl(public_dir / "meetings.jsonl", [{"id": "meeting-1"}])
    _write_jsonl(public_dir / "meeting_items.jsonl", [{"id": "item-1", "meeting_id": "meeting-1"}])
    _write_jsonl(public_dir / "meeting_documents.jsonl", [{"meeting_id": "meeting-1", "document_id": "doc-1"}])
    _write_jsonl(
        public_dir / "meeting_item_documents.jsonl",
        [{"meeting_item_id": "item-1", "document_id": "doc-1"}],
    )
    (public_dir / "latest.json").write_text(
        json.dumps(
            {
                "documents_seen": 2,
                "relations_publication_summary": {
                    "raw_meeting_document_relations_seen": 3,
                    "raw_meeting_item_document_relations_seen": 4,
                },
            }
        ),
        encoding="utf-8",
    )

    report = build_quality_report(public_dir)

    assert report["document_metadata"]["documents_with_file_url"] == 1
    assert report["document_metadata"]["documents_with_file_size"] == 1
    assert report["export_diagnostics"]["documents_published"] == 2
    assert report["export_diagnostics"]["dropped_meeting_document_relations"] == 2
    assert report["export_diagnostics"]["dropped_meeting_item_document_relations"] == 3
    assert report["coverage"]["documents_with_relations"] == 1
