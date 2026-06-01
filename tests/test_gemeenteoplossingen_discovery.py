from open_ris_monitor.analysis.gemeenteoplossingen_discovery import (
    classify_response_shape,
    parse_endpoints,
    summarize_payload,
)


def test_classify_documents_response_shape() -> None:
    payload = {"result": {"totalCount": 1, "documents": [{"id": 1, "fileName": "x.pdf"}]}}
    assert classify_response_shape(payload) == "object.result.object_with_list"


def test_summarize_payload_extracts_sample_keys() -> None:
    payload = {"result": {"totalCount": 1, "documents": [{"id": 1, "fileName": "x.pdf"}]}}
    shape, top_level_keys, result_keys, sample_keys, sample_count = summarize_payload(payload, limit=3)
    assert shape == "object.result.object_with_list"
    assert "result" in top_level_keys
    assert "documents" in result_keys
    assert "id" in sample_keys
    assert sample_count == 1


def test_parse_endpoints() -> None:
    assert parse_endpoints("") is None
    assert parse_endpoints("meetings, agendaItems") == ["meetings", "agendaItems"]
