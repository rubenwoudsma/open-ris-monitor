from open_ris_monitor.analysis.gemeenteoplossingen_relation_discovery import parse_ids


def test_parse_ids_empty_value() -> None:
    assert parse_ids("") == []
    assert parse_ids("   ") == []


def test_parse_ids_comma_separated_values() -> None:
    assert parse_ids("42745, 40215,40074") == [42745, 40215, 40074]
