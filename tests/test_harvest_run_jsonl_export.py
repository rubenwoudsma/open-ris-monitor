import json
from pathlib import Path

from open_ris_monitor.exporters.json_exporter import write_jsonl
from open_ris_monitor.models.harvest_run import HarvestRun


def test_write_jsonl_serializes_harvest_run_as_json_object(tmp_path: Path) -> None:
    harvest_run = HarvestRun(
        id="harvest-huizen-20260609T183009Z",
        municipality_id="gm0406",
        source_system_id="huizen-gemeenteoplossingen",
        started_at="2026-06-09T18:30:09+00:00",
        finished_at="2026-06-09T18:37:09+00:00",
        status="success",
        mode="latest",
        meetings_seen=203,
        agenda_items_seen=1000,
        documents_seen=250,
        documents_normalized=250,
    )

    output = tmp_path / "harvest_runs.jsonl"
    write_jsonl(output, [harvest_run])

    line = output.read_text(encoding="utf-8").strip()
    record = json.loads(line)

    assert isinstance(record, dict)
    assert record["id"] == "harvest-huizen-20260609T183009Z"
    assert record["status"] == "success"
    assert record["documents_seen"] == 250
    assert not line.startswith('"HarvestRun(')
