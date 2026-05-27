from datetime import datetime, timezone

from open_ris_monitor.models.harvest_run import HarvestRun


def test_harvest_run_model() -> None:
    run = HarvestRun(
        id="harvest-test",
        municipality_id="gm0406",
        source_system_id="huizen-gemeenteoplossingen",
        started_at=datetime.now(timezone.utc),
        status="success",
    )

    assert run.meetings_seen == 0
    assert run.status == "success"
