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


def test_render_documents_hides_file_metadata_columns_when_dataset_has_none() -> None:
    source = read_viewer_source()
    function = extract_function(source, "renderDocuments")

    assert "hasAnyDocumentFilenameMetadata(allDocuments)" in function
    assert "hasAnyDocumentSizeMetadata(allDocuments)" in function
    assert 'setTableColumnVisibility("Bestand", showFilenameColumn)' in function
    assert 'setTableColumnVisibility("Grootte", showSizeColumn)' in function
    assert "if (showFilenameColumn) row.appendChild" in function
    assert "if (showSizeColumn) row.appendChild" in function


def test_empty_state_colspan_follows_visible_columns() -> None:
    source = read_viewer_source()
    function = extract_function(source, "renderDocuments")

    assert "getVisibleDocumentColumnCount(showFilenameColumn, showSizeColumn)" in function
    assert "cell.colSpan = 7" not in function


def test_document_detail_omits_empty_file_metadata_rows() -> None:
    source = read_viewer_source()
    function = extract_function(source, "renderDocumentDetail")

    assert "const filename = getDocumentFilename(documentRecord)" in function
    assert 'if (filename) appendDefinition(meta, "Bestand", filename)' in function
    assert "const size = formatDocumentSize(documentRecord)" in function
    assert 'if (size !== "Geen bestandsgrootte beschikbaar") appendDefinition(meta, "Grootte", size)' in function
    assert 'appendDefinition(meta, "Bestand", text(getDocumentFilename' not in function
