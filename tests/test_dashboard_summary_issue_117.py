from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from open_ris_monitor.analysis.dashboard import build_dashboard_summary, write_dashboard_summary
from open_ris_monitor.analysis.generate_public_reports import generate_reports


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def test_dashboard_summary_counts_years_types_coverage_and_freshness(tmp_path: Path) -> None:
    public_dir = tmp_path / "data" / "public"
    public_dir.mkdir(parents=True)
    (public_dir / "latest.json").write_text(
        json.dumps(
            {
                "municipality_id": "huizen",
                "generated_at": "2026-06-20T12:00:00+00:00",
                "profile": "public",
            }
        ),
        encoding="utf-8",
    )
    _write_jsonl(
        public_dir / "documents.jsonl",
        [
            {
                "id": "doc-1",
                "publication_date": "2026-01-10",
                "document_type": "Raadsvoorstel",
                "file_size_bytes": 120_000,
            },
            {
                "id": "doc-2",
                "publication_date": "2025-12-01",
                "normalized_document_type_label": "Bijlage",
                "file_size_bytes": 2_000_000,
            },
            {"id": "doc-3", "publication_date": "2026-02-01", "document_type": "Raadsvoorstel"},
        ],
    )
    _write_jsonl(public_dir / "document_versions.jsonl", [{"id": "version-1"}])
    _write_jsonl(public_dir / "meetings.jsonl", [{"id": "meeting-1", "date": "2026-01-15"}])
    _write_jsonl(public_dir / "meeting_items.jsonl", [{"id": "item-1", "meeting_id": "meeting-1", "meeting_date": "2026-01-15"}])
    _write_jsonl(public_dir / "meeting_documents.jsonl", [{"id": "rel-1", "meeting_id": "meeting-1", "document_id": "doc-1"}])
    _write_jsonl(public_dir / "meeting_item_documents.jsonl", [{"id": "rel-2", "meeting_item_id": "item-1", "document_id": "doc-2"}])
    _write_jsonl(public_dir / "organization_groups.jsonl", [{"id": "group-1"}])
    _write_jsonl(public_dir / "organization_persons.jsonl", [{"id": "person-1"}])
    _write_jsonl(public_dir / "organization_roles.jsonl", [{"id": "role-1"}])
    _write_jsonl(public_dir / "organization_positions.jsonl", [{"id": "position-1"}])

    dashboard = build_dashboard_summary(
        public_dir,
        now=datetime(2026, 6, 21, 12, 0, tzinfo=timezone.utc),
    )

    assert dashboard["municipality_id"] == "huizen"
    assert dashboard["profile"] == "public"
    assert dashboard["totals"]["documents"] == 3
    assert dashboard["totals"]["linked_documents"] == 2
    assert dashboard["totals"]["unlinked_documents"] == 1
    assert dashboard["coverage"]["documents_with_any_meeting_context_ratio"] == 0.6667
    assert dashboard["freshness"]["age_days"] == 1
    assert dashboard["freshness"]["status"] == "fresh"
    assert dashboard["documents_by_year"] == [
        {"year": "2025", "count": 1},
        {"year": "2026", "count": 2},
    ]
    assert dashboard["documents_by_type"][0] == {"document_type": "Raadsvoorstel", "count": 2}
    assert dashboard["document_file_size"]["known_count"] == 2
    assert dashboard["document_file_size"]["unknown_count"] == 1
    assert dashboard["totals"]["organization_positions"] == 1


def test_dashboard_summary_handles_missing_optional_exports(tmp_path: Path) -> None:
    public_dir = tmp_path / "data" / "public"
    public_dir.mkdir(parents=True)
    (public_dir / "latest.json").write_text(json.dumps({"generated_at": "2026-06-01T00:00:00+00:00"}), encoding="utf-8")
    _write_jsonl(public_dir / "documents.jsonl", [{"id": "doc-1", "publication_date": "2026-01-01"}])

    dashboard = build_dashboard_summary(public_dir, now=datetime(2026, 6, 20, tzinfo=timezone.utc))

    assert dashboard["totals"]["documents"] == 1
    assert dashboard["totals"]["meetings"] == 0
    assert dashboard["totals"]["organization_groups"] == 0
    assert dashboard["freshness"]["status"] == "stale"


def test_write_dashboard_summary_and_generate_reports_update_latest(tmp_path: Path) -> None:
    public_dir = tmp_path / "data" / "public"
    public_dir.mkdir(parents=True)
    (public_dir / "latest.json").write_text(json.dumps({"outputs": {}, "generated_at": "2026-06-01T00:00:00+00:00"}), encoding="utf-8")
    _write_jsonl(public_dir / "documents.jsonl", [{"id": "doc-1", "publication_date": "2026-01-01", "document_type": "Motie"}])
    _write_jsonl(public_dir / "harvest_runs.jsonl", [{"id": "run-1", "status": "success", "started_at": "2026-06-01T00:00:00+00:00"}])

    dashboard = write_dashboard_summary(public_dir)
    result = generate_reports(public_dir)
    latest = json.loads((public_dir / "latest.json").read_text(encoding="utf-8"))

    assert (public_dir / "quality" / "dashboard.json").exists()
    assert dashboard["totals"]["documents"] == 1
    assert result["dashboard_totals"]["documents"] == 1
    assert latest["outputs"]["dashboard"] == "quality/dashboard.json"
