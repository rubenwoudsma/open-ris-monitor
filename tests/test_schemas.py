import os
import json
import pytest
from jsonschema import validate, ValidationError

def load_schema(filename):
    schema_path = os.path.join(os.path.dirname(__file__), '..', 'schemas', filename)
    with open(schema_path, 'r', encoding='utf-8') as f:
        return json.load(f)

@pytest.fixture
def doc_schema(): return load_schema('document.schema.json')

@pytest.fixture
def meeting_schema(): return load_schema('meeting.schema.json')

@pytest.fixture
def agenda_schema(): return load_schema('agenda_item.schema.json')

@pytest.fixture
def relation_schema(): return load_schema('relation.schema.json')

def test_valid_document(doc_schema):
    valid_doc = {
        "id": "doc_001",
        "schema_version": "1.0.0",
        "title": "Raadsvoorstel Afvalbeleid",
        "type": "Raadsvoorstel",
        "date": "2026-03-30",
        "url": "https://example.org/docs/afval.pdf",
        "text": "Inhoud van het voorstel..."
    }
    validate(instance=valid_doc, schema=doc_schema)

def test_invalid_document_missing_fields(doc_schema):
    invalid_doc = {
        "id": "doc_002",
        "schema_version": "1.0.0"
    }
    with pytest.raises(ValidationError):
        validate(instance=invalid_doc, schema=doc_schema)

def test_invalid_document_additional_property(doc_schema):
    invalid_doc = {
        "id": "doc_003",
        "schema_version": "1.0.0",
        "title": "Title",
        "url": "https://example.org/doc",
        "unexpected_field_abc": 123
    }
    with pytest.raises(ValidationError):
        validate(instance=invalid_doc, schema=doc_schema)

def test_valid_meeting(meeting_schema):
    valid_meeting = {
        "id": "meet_101",
        "schema_version": "1.0.0",
        "title": "Gemeenteraad Extraordinair",
        "date": "2026-04-15",
        "start_time": "19:30",
        "location": "Raadszaal",
        "url": "https://example.org/meetings/101"
    }
    validate(instance=valid_meeting, schema=meeting_schema)

def test_valid_relation(relation_schema):
    valid_rel = {
        "id": "rel_001",
        "schema_version": "1.0.0",
        "source_id": "doc_001",
        "target_id": "meet_101",
        "type": "document_to_meeting"
    }
    validate(instance=valid_rel, schema=relation_schema)

def test_invalid_relation_type(relation_schema):
    invalid_rel = {
        "id": "rel_002",
        "schema_version": "1.0.0",
        "source_id": "doc_001",
        "target_id": "meet_101",
        "type": "invalid_edge_type"
    }
    with pytest.raises(ValidationError):
        validate(instance=invalid_rel, schema=relation_schema)
