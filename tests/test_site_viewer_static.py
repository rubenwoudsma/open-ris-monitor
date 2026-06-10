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


def test_github_like_shell_layout_exists() -> None:
    index = Path("site/index.html").read_text(encoding="utf-8")
    styles = Path("site/assets/styles.css").read_text(encoding="utf-8")
    for marker in ["skip-link", "site-header__inner", "top-nav", "main-column"]:
        assert marker in index
    for marker in [".top-nav__link--active", "@media"]:
        assert marker in styles


def test_document_first_detail_view_exists() -> None:
    index = Path("site/index.html").read_text(encoding="utf-8")
    source = Path("site/src/main.ts").read_text(encoding="utf-8")
    styles = Path("site/assets/styles.css").read_text(encoding="utf-8")
    for marker in [
        "document-detail",
        "document-detail-title",
        "document-detail-body",
        "clear-document-selection",
        "Acties",
    ]:
        assert marker in index
    for marker in [
        "renderDocumentDetail",
        "relatedMeetingIds",
        "relatedAgendaItemIds",
        "relatedVersions",
        "selectDocument",
    ]:
        assert marker in source
    for marker in [".document-detail", ".relation-card", ".document-actions", ".is-selected"]:
        assert marker in styles


def test_document_metadata_fallbacks_are_visible() -> None:
    index = Path("site/index.html").read_text(encoding="utf-8")
    source = Path("site/src/main.ts").read_text(encoding="utf-8")
    styles = Path("site/assets/styles.css").read_text(encoding="utf-8")
    assert "data-quality-notice" in index
    for marker in [
        "Niet beschikbaar in export",
        "Geen bestandsmetadata",
        "Geen bestandsgrootte beschikbaar",
        "Metadata beperkt in huidige export",
        "Geen bruikbare documentkoppelingen",
    ]:
        assert marker in source
    for marker in [".quality-notice", ".metadata-notice"]:
        assert marker in styles


def test_compact_meeting_list_view_exists() -> None:
    index = Path("site/index.html").read_text(encoding="utf-8")
    source = Path("site/src/main.ts").read_text(encoding="utf-8")
    styles = Path("site/assets/styles.css").read_text(encoding="utf-8")
    for marker in [
        "nav-documents",
        "nav-meetings",
        "documents-view",
        "meetings-view",
        "meetings-table-body",
        "meetings-result-count",
        "Technische metadata en databestanden",
    ]:
        assert marker in index
    for marker in [
        "renderMeetings",
        "agendaItemIdsForMeeting",
        "linkedDocumentIdsForMeeting",
        "setActiveView",
    ]:
        assert marker in source
    for marker in [".meetings-table", ".technical-metadata", ".footer-metadata"]:
        assert marker in styles


def test_compact_layout_removes_sidebar_and_source_type_column() -> None:
    index = Path("site/index.html").read_text(encoding="utf-8")
    source = Path("site/src/main.ts").read_text(encoding="utf-8")
    assert 'class="sidebar"' not in index
    assert "Document-first overzicht" not in index
    assert "Bron type" not in index
    assert "source-type-asc" not in index
    assert 'appendDefinition(meta, "Bron type"' not in source
    assert "getVisibleDocumentColumnCount" in source


def test_meeting_detail_view_exists_without_new_route() -> None:
    index = Path("site/index.html").read_text(encoding="utf-8")
    source = Path("site/src/main.ts").read_text(encoding="utf-8")
    styles = Path("site/assets/styles.css").read_text(encoding="utf-8")
    for marker in [
        "meeting-detail",
        "meeting-detail-title",
        "meeting-detail-body",
        "clear-meeting-selection",
    ]:
        assert marker in index
    for marker in [
        "Agendapunten binnen deze vergadering",
        "Gekoppelde documenten bij de vergadering",
        "renderMeetingDetail",
        "selectMeeting",
        "clearMeetingSelection",
        "linkedDocumentIdsForAgendaItem",
        "createDocumentList",
        "Bekijk documentdetails",
    ]:
        assert marker in source
    for marker in [".meeting-detail", ".agenda-item-card", ".linked-document-list"]:
        assert marker in styles
    assert "meetingId" not in index
    assert "URLSearchParams" not in source
