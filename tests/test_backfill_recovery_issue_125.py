from open_ris_monitor.core.config import resolve_harvest_options
from open_ris_monitor.models.harvest_run import HarvestRun
from open_ris_monitor.pipeline.run import _merge_harvest_run_records


def _harvest_run(run_id: str, *, status: str = "success") -> HarvestRun:
    return HarvestRun(
        id=run_id,
        municipality_id="gm0406",
        source_system_id="huizen-gemeenteoplossingen",
        started_at="2026-08-13T13:10:07+00:00",
        finished_at="2026-08-13T13:44:41+00:00",
        status=status,
        mode="full",
        meetings_seen=529,
        agenda_items_seen=5000,
        documents_seen=7425,
        documents_normalized=7425,
    )


def test_backfill_profiles_do_not_cap_meeting_items() -> None:
    for profile in ("backfill", "full"):
        options = resolve_harvest_options(profile)

        assert options["mode"] == "full"
        assert options["max_documents"] is None
        assert options["meeting_item_limit"] is None


def test_harvest_run_merge_preserves_existing_history_and_appends_current_run() -> None:
    existing = [
        _harvest_run("harvest-huizen-20260716T055737Z").to_dict(),
        _harvest_run("harvest-huizen-20260813T093742Z").to_dict(),
    ]
    current = _harvest_run("harvest-huizen-20260813T131007Z")

    merged = _merge_harvest_run_records(existing, current)

    assert [record["id"] for record in merged] == [
        "harvest-huizen-20260716T055737Z",
        "harvest-huizen-20260813T093742Z",
        "harvest-huizen-20260813T131007Z",
    ]


def test_harvest_run_merge_replaces_same_run_id_without_duplicate() -> None:
    run_id = "harvest-huizen-20260813T131007Z"
    existing = [_harvest_run(run_id, status="running").to_dict()]
    current = _harvest_run(run_id, status="success")

    merged = _merge_harvest_run_records(existing, current)

    assert len(merged) == 1
    assert merged[0]["id"] == run_id
    assert merged[0]["status"] == "success"
