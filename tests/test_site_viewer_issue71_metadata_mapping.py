from pathlib import Path


def read_viewer_source() -> str:
    return Path("site/src/main.ts").read_text(encoding="utf-8")


def extract_function(source: str, name: str) -> str:
    marker = f"function {name}"
    start = source.index(marker)
    next_start = source.find("\nfunction ", start + len(marker))
    if next_start == -1:
        return source[start:]
    return source[start:next_start]


def test_compact_type_label_prefers_human_readable_export_label() -> None:
    source = read_viewer_source()
    function = extract_function(source, "getCompactTypeLabel")

    label_position = function.index("documentRecord.normalized_document_type_label")
    normalized_type_position = function.index("documentRecord.normalized_document_type,")

    assert label_position < normalized_type_position
    assert "Bron:" not in function


def test_source_document_type_uses_source_metadata_not_compact_alias() -> None:
    source = read_viewer_source()
    function = extract_function(source, "getSourceDocumentType")

    assert "documentRecord.document_type" in function
    assert "documentTypeLabel" in function
    assert "documentRecord.type" not in function
    assert "sourceType === compactType" in function
    assert "sourceType === compactTypeLabel" in function


def test_document_size_prefers_public_file_size_bytes() -> None:
    source = read_viewer_source()
    function = extract_function(source, "getDocumentSize")

    assert "documentRecord.file_size_bytes" in function
    assert "documentRecord.size_bytes" in function
    assert function.index("documentRecord.file_size_bytes") < function.index("documentRecord.size_bytes")
    assert "fileSize" in function
