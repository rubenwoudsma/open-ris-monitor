"""Exercise the installed workflow summary command's report handling."""

from __future__ import annotations

import json
from pathlib import Path

from open_ris_monitor.ci.publish_summary import generate_summary


def test_generate_summary_with_all_reports(tmp_path: Path) -> None:
    """Test summary generation with all expected report files present."""
    # Arrange
    public_dir = tmp_path / "public"
    quality_dir = public_dir / "quality"
    quality_dir.mkdir(parents=True)
    summary_file = tmp_path / "summary.md"

    dashboard_data = {"totals": {"documents": 1000, "meetings": 100, "meeting_items": 500}}
    (quality_dir / "dashboard.json").write_text(json.dumps(dashboard_data), encoding="utf-8")

    unlinked_data = {"unlinked_documents_count": 50, "documents_total": 1000}
    (quality_dir / "unlinked_documents.json").write_text(
        json.dumps(unlinked_data), encoding="utf-8"
    )

    meetings_no_docs_data = {"meetings_without_documents_count": 2, "meetings_total": 100}
    (quality_dir / "meetings_without_documents.json").write_text(
        json.dumps(meetings_no_docs_data), encoding="utf-8"
    )

    # Act
    generate_summary(public_dir, summary_file)

    # Assert
    content = summary_file.read_text(encoding="utf-8")
    assert "## Data Quality Report" in content
    assert "| Documents | 1000 |" in content
    assert "| Meetings | 100 |" in content
    assert "| Agenda Items | 500 |" in content
    assert "| Unlinked Documents | 50 (5.00%) |" in content
    assert "| Meetings without Documents | 2 (2.00%) |" in content


def test_generate_summary_with_missing_reports(tmp_path: Path) -> None:
    """Test summary generation when report files are missing."""
    # Arrange
    public_dir = tmp_path / "nonexistent"
    summary_file = tmp_path / "summary.md"

    # Act
    generate_summary(public_dir, summary_file)

    # Assert
    content = summary_file.read_text(encoding="utf-8")
    assert "Quality reports not found" in content


def test_generate_summary_with_partial_reports(tmp_path: Path) -> None:
    """Test summary generation with only some report files present."""
    # Arrange
    public_dir = tmp_path / "public"
    quality_dir = public_dir / "quality"
    quality_dir.mkdir(parents=True)
    summary_file = tmp_path / "summary.md"

    dashboard_data = {"totals": {"documents": 1000}}
    (quality_dir / "dashboard.json").write_text(json.dumps(dashboard_data), encoding="utf-8")

    # Act
    generate_summary(public_dir, summary_file)

    # Assert
    content = summary_file.read_text(encoding="utf-8")
    assert "## Data Quality Report" in content
    assert "| Documents | 1000 |" in content
    assert "| Unlinked Documents | Not available |" in content
    assert "| Meetings without Documents | Not available |" in content
