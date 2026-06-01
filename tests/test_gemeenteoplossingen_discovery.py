from open_ris_monitor.analysis.gemeenteoplossingen_discovery import classify_json_shape


def test_classify_gemeenteoplossingen_documents_shape() -> None:
    payload = {
        "result": {
            "totalCount": 1,
            "documents": [
                {
                    "id": 1,
                    "objectId": 2,
                    "description": "Example",
                }
            ],
        }
    }

    response_shape, result_keys, item_count, sample_keys = classify_json_shape(payload)

    assert response_shape == "object_with_result"
    assert "documents" in result_keys
    assert "totalCount" in result_keys
    assert item_count == 1
    assert sample_keys == ["description", "id", "objectId"]


def test_classify_plain_list_shape() -> None:
    payload = [{"id": 1, "name": "Example"}]

    response_shape, result_keys, item_count, sample_keys = classify_json_shape(payload)

    assert response_shape == "list"
    assert result_keys == []
    assert item_count == 1
    assert sample_keys == ["id", "name"]
