from pathlib import Path


def read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_organization_navigation_and_view_are_present() -> None:
    index = read("site/index.html")
    source = read("site/src/main.ts")
    build = read("site/assets/build/main.js")

    for marker in [
        'id="nav-organization"',
        'id="organization-view"',
        'id="organization-summary-cards"',
        'id="organization-groups-list"',
        'id="organization-role-filter"',
        'id="organization-positions-body"',
        "Raadsorganisatie",
    ]:
        assert marker in index

    for marker in [
        "renderOrganization",
        "organizationRoleFilter",
        "roleCategoryFromName",
        "personGroupsByPersonId",
        "organizationPositions",
    ]:
        assert marker in source
        assert marker in build


def test_organization_public_files_are_linked_as_technical_metadata() -> None:
    index = read("site/index.html")
    for filename in [
        "organization_groups.jsonl",
        "organization_persons.jsonl",
        "organization_roles.jsonl",
        "organization_positions.jsonl",
        "organization_group_memberships.jsonl",
    ]:
        assert filename in index


def test_organization_styling_exists() -> None:
    styles = read("site/assets/styles.css")
    for marker in [
        ".summary-card-grid",
        ".summary-card__number",
        ".organization-group-grid",
        ".organization-table",
    ]:
        assert marker in styles
