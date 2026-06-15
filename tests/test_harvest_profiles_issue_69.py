from __future__ import annotations

from open_ris_monitor.core.config import resolve_harvest_options


def test_public_profile_builds_more_than_latest_250_document_scope() -> None:
    options = resolve_harvest_options("public")

    assert options["mode"] == "full"
    assert options["max_documents"] is not None
    assert options["max_documents"] > 250
    assert options["include_relations"] is True
    assert options["meeting_scan_limit"] >= options["max_documents"]
    assert options["meeting_item_limit"] is not None
    assert options["meeting_item_limit"] >= options["meeting_scan_limit"]


def test_quick_profile_remains_small_latest_smoke_test() -> None:
    options = resolve_harvest_options("quick")

    assert options["mode"] == "latest"
    assert options["limit"] <= 25
    assert options["max_documents"] is None
    assert options["include_relations"] is True


def test_backfill_profile_is_full_and_unbounded_by_default() -> None:
    options = resolve_harvest_options("backfill")

    assert options["mode"] == "full"
    assert options["max_documents"] is None
    assert options["include_relations"] is True
    assert options["meeting_item_limit"] is None


def test_explicit_profile_overrides_still_win() -> None:
    options = resolve_harvest_options(
        "public",
        {"max_documents": 275, "meeting_scan_limit": 300},
    )

    assert options["mode"] == "full"
    assert options["max_documents"] == 275
    assert options["meeting_scan_limit"] == 300
