from open_ris_monitor.pipeline.profiles import resolve_harvest_options


def test_quick_profile_is_bounded_and_relation_enabled() -> None:
    options = resolve_harvest_options("quick")

    assert options["mode"] == "latest"
    assert options["limit"] == 10
    assert options["include_relations"] is True
    assert options["meeting_scan_limit"] == 50
    assert options["meeting_session_batch_size"] == 50
    assert options["meeting_item_limit"] == 200


def test_public_profile_uses_full_bounded_publication_defaults() -> None:
    options = resolve_harvest_options("public")

    assert options["mode"] == "full"
    assert options["max_documents"] == 250
    assert options["include_relations"] is True
    assert options["meeting_scan_limit"] == 250
    assert options["meeting_item_limit"] == 1000


def test_backfill_profile_is_larger_but_still_relation_bounded() -> None:
    options = resolve_harvest_options("backfill")

    assert options["mode"] == "full"
    assert options["max_documents"] is None
    assert options["include_relations"] is True
    assert options["meeting_scan_limit"] == 1000
    assert options["meeting_item_limit"] == 5000


def test_no_profile_keeps_existing_cli_defaults() -> None:
    options = resolve_harvest_options(None)

    assert options["mode"] == "latest"
    assert options["limit"] == 25
    assert options["batch_size"] == 100
    assert options["max_documents"] is None
    assert options["include_relations"] is False


def test_explicit_overrides_win_over_profile_defaults() -> None:
    options = resolve_harvest_options(
        "public",
        {
            "mode": "latest",
            "limit": 42,
            "max_documents": None,
            "include_relations": False,
            "meeting_scan_limit": 12,
            "meeting_item_limit": 34,
        },
    )

    assert options["mode"] == "latest"
    assert options["limit"] == 42
    assert options["max_documents"] is None
    assert options["include_relations"] is False
    assert options["meeting_scan_limit"] == 12
    assert options["meeting_item_limit"] == 34
