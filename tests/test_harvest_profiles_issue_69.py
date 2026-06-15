from __future__ import annotations

from open_ris_monitor.core.config import resolve_harvest_options


def test_issue_69_public_profile_stays_bounded_latest_publication_default() -> None:
    options = resolve_harvest_options("public")

    assert options["mode"] == "latest"
    assert options["limit"] == 250
    assert options["max_documents"] is None
    assert options["include_relations"] is True
    assert options["meeting_scan_limit"] == 250
    assert options["meeting_item_limit"] == 1000


def test_issue_69_backfill_profile_is_the_full_coverage_profile() -> None:
    options = resolve_harvest_options("backfill")

    assert options["mode"] == "full"
    assert options["max_documents"] is None
    assert options["include_relations"] is True
    assert options["meeting_scan_limit"] == 1000
    assert options["meeting_item_limit"] == 5000


def test_issue_69_explicit_public_overrides_can_expand_document_scope() -> None:
    options = resolve_harvest_options(
        "public",
        {"mode": "full", "max_documents": 1000, "meeting_scan_limit": 1000},
    )

    assert options["mode"] == "full"
    assert options["max_documents"] == 1000
    assert options["meeting_scan_limit"] == 1000
    assert options["include_relations"] is True
