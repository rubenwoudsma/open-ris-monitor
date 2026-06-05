import os
import json
import pytest
from open_ris_monitor.exporters.validate_exports import validate_jsonl_file

@pytest.fixture
def setup_temp_files(tmp_path):
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": ["id", "schema_version"],
        "properties": {
            "id": {"type": "string"},
            "schema_version": {"type": "string"}
        }
    }
    schema_file = tmp_path / "test.schema.json"
    schema_file.write_text(json.dumps(schema))
    return tmp_path, schema_file

def test_validate_valid_jsonl(setup_temp_files):
    tmp_path, schema_file = setup_temp_files
    jsonl_file = tmp_path / "valid.jsonl"
    jsonl_file.write_text('{"id": "1", "schema_version": "1.0.0"}\n{"id": "2", "schema_version": "1.0.0"}\n')
    
    assert validate_jsonl_file(str(jsonl_file), str(schema_file)) is True

def test_validate_empty_jsonl(setup_temp_files):
    tmp_path, schema_file = setup_temp_files
    jsonl_file = tmp_path / "empty.jsonl"
    jsonl_file.write_text('')
    
    assert validate_jsonl_file(str(jsonl_file), str(schema_file)) is False

def test_validate_invalid_schema_jsonl(setup_temp_files):
    tmp_path, schema_file = setup_temp_files
    jsonl_file = tmp_path / "invalid.jsonl"
    jsonl_file.write_text('{"id": "1"}\n')  # schema_version ontbreekt
    
    assert validate_jsonl_file(str(jsonl_file), str(schema_file)) is False
