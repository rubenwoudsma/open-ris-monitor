from open_ris_monitor.analysis.gemeenteoplossingen_relation_discovery import (
    meeting_ids_from_meetingsessions,
    parse_ids,
)


def test_parse_ids_supports_empty_and_comma_separated_values() -> None:
    assert parse_ids("") == []
    assert parse_ids(" 19, 20,27 ") == [19, 20, 27]


def test_meeting_ids_from_meetingsessions_reads_container_meeting_ids() -> None:
    records = [
        {"id": 1, "container": {"meeting": {"id": 19}}},
        {"id": 2, "container": {"meeting": {"id": 20}}},
        {"id": 3, "container": {"meeting": {"id": 19}}},
        {"id": 4, "container": {}},
    ]
    assert meeting_ids_from_meetingsessions(records) == [19, 20]
