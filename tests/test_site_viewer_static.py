from pathlib import Path


def test_site_uses_typescript_build_output() -> None:
    index = Path("site/index.html").read_text(encoding="utf-8")
    assert 'type="module"' in index
    assert "assets/build/main.js" in index


def test_typescript_data_layer_files_exist() -> None:
    expected = [
        "site/src/main.ts",
        "site/src/data/jsonl.ts",
        "site/src/data/types.ts",
        "site/src/data/loaders.ts",
        "site/src/data/relations.ts",
        "site/src/ui/format.ts",
    ]
    for path in expected:
        assert Path(path).exists(), path


def test_relation_indexes_are_named_in_relations_module() -> None:
    source = Path("site/src/data/relations.ts").read_text(encoding="utf-8")
    for name in [
        "documentsById",
        "meetingsById",
        "agendaItemsById",
        "meetingIdsByDocumentId",
        "agendaItemIdsByDocumentId",
        "documentIdsByMeetingId",
        "documentIdsByAgendaItemId",
        "agendaItemIdsByMeetingId",
    ]:
        assert name in source
