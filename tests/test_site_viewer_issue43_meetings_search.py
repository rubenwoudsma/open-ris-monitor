from pathlib import Path


def read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_existing_documents_search_ui_is_preserved() -> None:
    index = read("site/index.html")
    for marker in [
        'id="viewer-controls"',
        'id="search-input"',
        'id="type-filter"',
        'id="sort-select"',
        'id="page-size-select"',
        'id="visible-documents-count"',
        'id="documents-table-body"',
        'id="document-detail"',
    ]:
        assert marker in index


def test_meetings_search_filter_ui_is_present_without_overlay_script() -> None:
    index = read("site/index.html")
    source = read("site/src/main.ts")
    build = read("site/assets/build/main.js")

    for marker in [
        'id="meetings-controls"',
        'id="meeting-search-input"',
        'id="meeting-sort-select"',
        'id="visible-meetings-count"',
        "Datum, nieuwste eerst",
        "date-asc",
    ]:
        assert marker in index

    for marker in [
        "meetingQuery",
        "meetingSortMode",
        "meetingSearchBlob",
        "filteredMeetings",
        "Geen vergaderingen gevonden voor deze zoekopdracht",
        "zichtbaar",
    ]:
        assert marker in source
        assert marker in build

    assert "assets/build/meetings-search.js" not in index
    assert "assets/meetings-search.css" not in index
    assert "MutationObserver" not in source
    assert "MutationObserver" not in build


def test_meeting_detail_view_remains_present() -> None:
    index = read("site/index.html")
    for marker in [
        'id="meeting-detail"',
        'id="meeting-detail-title"',
        'id="meeting-detail-body"',
        'id="clear-meeting-selection"',
        "Agendapunten en gekoppelde documenten",
        'id="meetings-table-body"',
    ]:
        assert marker in index


def test_meeting_details_button_rendering_is_still_present() -> None:
    combined = "\n".join(
        read(path)
        for path in [
            "site/src/main.ts",
            "site/assets/build/main.js",
            "site/index.html",
        ]
    )
    assert "Details" in combined


def test_document_list_selection_updates_document_deeplink() -> None:
    source = read("site/src/main.ts")
    build = read("site/assets/build/main.js")
    for content in [source, build]:
        assert "function focusDocumentFromDocumentList" in content
        assert "updateHash(documentHashFor(documentRecord))" in content
        assert "focusDocumentFromDocumentList(documentRecord)" in content


def test_footer_metadata_and_resource_links_are_separate_sections() -> None:
    styles = read("site/assets/styles.css")
    index = read("site/index.html")
    assert 'class="footer-metadata"' in index
    assert 'class="technical-metadata"' in index
    assert 'class="resource-links resource-links--inline"' in index
    assert ".footer-metadata { display: grid;" in styles
    assert ".technical-metadata { border-top:" in styles


def test_hidden_styling_is_still_guarded() -> None:
    styles = read("site/assets/styles.css")
    index = read("site/index.html")
    assert "[hidden]" in styles
    assert 'id="documents-view"' in index
    assert 'id="meetings-view"' in index
    assert "hidden" in index
