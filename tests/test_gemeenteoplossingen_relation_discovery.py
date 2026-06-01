from open_ris_monitor.analysis.gemeenteoplossingen_relation_discovery import classify_payload, list_from_result


def test_classify_payload_with_result_collection() -> None:
    payload = {
        "status": "OK",
        "code": 200,
        "result": {
            "offset": 0,
            "limit": 1,
            "count": 1,
            "totalCount": 1,
            "meetings": [{"id": 123, "description": "Raad", "date": "2026-01-01"}],
        },
    }

    shape, result_keys, sample_keys, sample_count, sample_ids = classify_payload(payload)

    assert shape == "object.result.object_with_list"
    assert "meetings" in result_keys
    assert "description" in sample_keys
    assert sample_count == 1
    assert sample_ids == [123]


def test_list_from_result_prefers_named_collection() -> None:
    payload = {"result": {"meetings": [{"id": 1}], "other": [{"id": 2}]}}
    assert list_from_result(payload, "meetings") == [{"id": 1}]
