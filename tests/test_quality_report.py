from __future__ import annotations

import json
from pathlib import Path

from open_ris_monitor.analysis.generate_public_reports import generate_reports
from open_ris_monitor.quality.report import build_quality_report, write_quality_report


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("
".join(json.dumps(row) for row in rows) + "
", encoding="utf-8")


def test_build_quality_report_counts_and_coverage(tmp_path: Path) -> None:
    public_dir = tmp_path / "data" / "public"
    public_dir.mkdir(parents=True)

    _write_jsonl(
        public_dir / "documents.jsonl",
        [
            {"id": "doc-1", "document_type": "Raadsvoorstel", "normalized_document_type": "proposal"},
            {"id": "doc-2", "document_type": "Bijlage", "normalized_document_type": "attachment"},
        ],
    )
    _write_jsonl(public_dir / "document_versions.jsonl", [{"id": "v-1"}])
    _write_jsonl(public_dir / "harvest_runs.jsonl", [{"id": "run-1", "status": "success", "started_at": "2026-06-01T10:00:00Z"}])
    _write_jsonl(public_dir / "meetings.jsonl", [{"id": "meeting-1"}])
    _write_jsonl(public_dir / "meeting_items.jsonl", [{"id": "item-1", "meeting_id": "meeting-1"}])
    _write_jsonl(public_dir / "meeting_documents.jsonl", [{"id": "rel-1", "meeting_id": "meeting-1", "document_id": "doc-1"}])
    _write_jsonl(public_dir / "meeting_item_documents.jsonl", [{"id": "rel-2", "meeting_item_id": "item-1", "document_id": "doc-2"}])

    summary = build_quality_report(public_dir)

    assert summary["counts"]["documents"] == 2
    assert summary["coverage"]["documents_with_relations"] == 2
    assert summary["integrity"]["orphan_meeting_document_relations"] == 0
    assert summary["integrity"]["orphan_meeting_item_document_relations"] == 0
    assert summary["document_types"]["unknown_count"] == 0
    assert summary["harvest"]["latest_run_status"] == "success"


def test_write_quality_report_creates_files(tmp_path: Path) -> None:
    public_dir = tmp_path / "data" / "public"
    public_dir.mkdir(parents=True)

    _write_jsonl(public_dir / "documents.jsonl", [{"id": "doc-1", "document_type": "Raadsvoorstel", "normalized_document_type": "proposal"}])
    _write_jsonl(public_dir / "harvest_runs.jsonl", [{"id": "run-1", "status": "success", "started_at": "2026-06-01T10:00:00Z"}])

    summary = write_quality_report(public_dir)

    quality_dir = public_dir / "quality"
    assert (quality_dir / "summary.json").exists()
    assert (quality_dir / "issues.jsonl").exists()
    assert summary["counts"]["documents"] == 1


def test_generate_reports_writes_all_outputs(tmp_path: Path) -> None:
    public_dir = tmp_path / "data" / "public"
    public_dir.mkdir(parents=True)

    _write_jsonl(public_dir / "documents.jsonl", [{"id": "doc-1", "document_type": "Raadsvoorstel", "normalized_document_type": "proposal"}])
    _write_jsonl(public_dir / "harvest_runs.jsonl", [{"id": "run-1", "status": "success", "started_at": "2026-06-01T10:00:00Z"}])
    (public_dir / "latest.json").write_text(json.dumps({"outputs": {}}), encoding="utf-8")

    result = generate_reports(public_dir)

    quality_dir = public_dir / "quality"
    assert (quality_dir / "id_stability.json").exists()
    assert (quality_dir / "document_types.json").exists()
    assert (quality_dir / "summary.json").exists()
    assert (quality_dir / "issues.jsonl").exists()
    assert result["quality_issues_count"] >= 0
