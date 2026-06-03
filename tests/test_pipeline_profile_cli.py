from open_ris_monitor.pipeline.run import parse_args, resolve_cli_harvest_options


def test_cli_profile_public_resolves_to_recent_public_defaults() -> None:
    args = parse_args(["--profile", "public"])
    options = resolve_cli_harvest_options(args)

    assert options["mode"] == "latest"
    assert options["limit"] == 250
    assert options["max_documents"] is None
    assert options["include_relations"] is True
    assert options["meeting_scan_limit"] == 250


def test_cli_explicit_options_override_profile() -> None:
    args = parse_args(
        [
            "--profile",
            "public",
            "--mode",
            "full",
            "--limit",
            "17",
            "--max-documents",
            "17",
            "--no-include-relations",
            "--meeting-scan-limit",
            "18",
            "--meeting-item-limit",
            "19",
        ]
    )
    options = resolve_cli_harvest_options(args)

    assert options["mode"] == "full"
    assert options["limit"] == 17
    assert options["max_documents"] == 17
    assert options["include_relations"] is False
    assert options["meeting_scan_limit"] == 18
    assert options["meeting_item_limit"] == 19


def test_cli_without_profile_keeps_legacy_defaults() -> None:
    args = parse_args([])
    options = resolve_cli_harvest_options(args)

    assert options["mode"] == "latest"
    assert options["limit"] == 25
    assert options["batch_size"] == 100
    assert options["include_relations"] is False
