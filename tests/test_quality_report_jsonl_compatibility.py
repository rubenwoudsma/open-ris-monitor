from __future__ import annotations

import json
from pathlib import Path

import pytest

from open_ris_monitor.quality.report import build_quality_report, read_jsonl


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def test_read_jsonl_accepts_single_line_json_array_for_legacy_exports(tmp_path: Path) -> None:
    path = tmp_path / "harvest_runs.jsonl"
    path.write_text(
        json.dumps(
            [
                {"id": "run-1", "status": "success", "started_at": "2026-06-01T10:00:00Z"},
                {"id": "run-2", "status": "success", "started_at": "2026-06-02T10:00:00Z"},
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    records = read_jsonl(path)

    assert [record["id"] for record in records] == ["run-1", "run-2"]


def test_build_quality_report_accepts_array_encoded_harvest_runs(tmp_path: Path) -> None:
    public_dir = tmp_path / "data" / "public"
    public_dir.mkdir(parents=True)
    _write_jsonl(
        public_dir / "documents.jsonl",
        [{"id": "doc-1", "document_type": "Raadsvoorstel", "normalized_document_type": "proposal"}],
    )
    (public_dir / "harvest_runs.jsonl").write_text(
        json.dumps([{"id": "run-1", "status": "success", "started_at": "2026-06-01T10:00:00Z"}])
        + "\n",
        encoding="utf-8",
    )

    summary = build_quality_report(public_dir)

    assert summary["counts"]["harvest_runs"] == 1
    assert summary["harvest"]["latest_run_status"] == "success"


def test_read_jsonl_rejects_array_items_that_are_not_objects(tmp_path: Path) -> None:
    path = tmp_path / "broken.jsonl"
    path.write_text(json.dumps([{"id": "ok"}, "broken"]) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Expected JSON object in array item 2"):
        read_jsonl(path)
