from pathlib import Path


def test_existing_documents_search_ui_is_preserved() -> None:
    index = Path("site/index.html").read_text(encoding="utf-8")
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


def test_meetings_search_filter_ui_is_present() -> None:
    index = Path("site/index.html").read_text(encoding="utf-8")
    source = Path("site/src/meetings-search.ts").read_text(encoding="utf-8")
    build = Path("site/assets/build/meetings-search.js").read_text(encoding="utf-8")
    for marker in [
        'id="meetings-controls"',
        'id="meeting-search-input"',
        'id="meeting-sort-select"',
        'id="visible-meetings-count"',
        'assets/build/meetings-search.js',
    ]:
        assert marker in index
    for marker in [
        "applyMeetingFilters",
        "Datum, nieuwste eerst",
        "date-asc",
        "zichtbaar",
        "Geen vergaderingen gevonden voor deze zoekopdracht",
    ]:
        assert marker in source or marker in index
    assert "applyMeetingFilters" in build


def test_meeting_detail_view_remains_present() -> None:
    index = Path("site/index.html").read_text(encoding="utf-8")
    for marker in [
        'id="meeting-detail"',
        'id="meeting-detail-title"',
        'id="meeting-detail-body"',
        'id="clear-meeting-selection"',
        "Agendapunten en gekoppelde documenten",
        "Details",
        'id="meetings-table-body"',
    ]:
        assert marker in index


def test_hidden_styling_is_still_guarded() -> None:
    styles = Path("site/assets/styles.css").read_text(encoding="utf-8")
    index = Path("site/index.html").read_text(encoding="utf-8")
    assert "[hidden]" in styles
    assert 'id="documents-view"' in index
    assert 'id="meetings-view"' in index
    assert "hidden" in index
