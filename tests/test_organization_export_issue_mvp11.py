from __future__ import annotations

from pathlib import Path
from typing import Any

from open_ris_monitor.connectors.gemeenteoplossingen import GemeenteOplossingenConnector
from open_ris_monitor.normalizers.organization import normalize_organization_harvest
from open_ris_monitor.pipeline import run as pipeline_run


class FakeResponse:
    def __init__(self, payload: dict[str, Any], url: str = "https://example.test") -> None:
        self._payload = payload
        self.url = url
        self.status_code = 200
        self.headers: dict[str, str] = {}

    def json(self) -> dict[str, Any]:
        return self._payload

    def raise_for_status(self) -> None:
        return None


class FakeSession:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def get(self, url: str, params: dict[str, Any] | None = None, timeout: int = 30) -> FakeResponse:
        params = params or {}
        self.calls.append((url, params))
        path = url.rstrip("/").split("/")[-1]
        if url.rstrip("/").endswith("groups/10/persons"):
            return FakeResponse({"result": {"persons": [{"id": 1, "firstName": "Ada", "lastName": "Lovelace"}]}})
        if path == "groups":
            return FakeResponse({"result": {"totalCount": 1, "groups": [{"id": 10, "name": "Fractie A", "type": "fractie"}]}})
        if path == "persons":
            return FakeResponse({"result": {"totalCount": 1, "persons": [{"id": 1, "firstName": "Ada", "lastName": "Lovelace", "email": "ada@example.test", "user": {"usermanagementId": 999}}]}})
        if path == "roles":
            return FakeResponse({"result": {"totalCount": 1, "roles": [{"id": 2, "name": "Raadslid"}]}})
        if path == "positions":
            return FakeResponse({"result": {"totalCount": 1, "positions": [{"id": 3, "personId": 1, "roleId": 2, "role": {"id": 2, "name": "Raadslid"}, "person": {"id": 1, "firstName": "Ada", "lastName": "Lovelace", "active": True}, "start_date": "2026-01-01"}]}})
        return FakeResponse({"result": {}})


def test_connector_fetches_public_organization_collections() -> None:
    connector = GemeenteOplossingenConnector(
        "https://example.test/api",
        session=FakeSession(),
        sleep_func=lambda _: None,
    )

    assert connector.fetch_all_groups() == [{"id": 10, "name": "Fractie A", "type": "fractie"}]
    assert connector.fetch_all_persons()[0]["email"] == "ada@example.test"
    assert connector.fetch_all_roles()[0]["name"] == "Raadslid"
    assert connector.fetch_all_positions()[0]["role"]["name"] == "Raadslid"
    assert connector.fetch_persons_by_group_id(10)[0]["lastName"] == "Lovelace"


def test_organization_normalization_keeps_public_fields_and_excludes_user_metadata() -> None:
    normalized = normalize_organization_harvest(
        {
            "groups": [{"id": 10, "name": "Fractie A", "type": "fractie", "sortorder": 1}],
            "persons": [
                {
                    "id": 1,
                    "firstName": "Ada",
                    "preposition": "van",
                    "lastName": "Lovelace",
                    "email": "ada@example.test",
                    "active": True,
                    "user": {"id": 99, "email": "internal@example.test", "usermanagementId": 999},
                }
            ],
            "roles": [{"id": 2, "name": "Fractievoorzitter", "sortOrder": 1}],
            "positions": [
                {
                    "id": 3,
                    "personId": 1,
                    "roleId": 2,
                    "person": {"id": 1, "firstName": "Ada", "preposition": "van", "lastName": "Lovelace", "active": True},
                    "role": {"id": 2, "name": "Fractievoorzitter"},
                    "start_date": "2026-01-01",
                }
            ],
            "group_memberships": {"10": [{"id": 1, "firstName": "Ada", "lastName": "Lovelace", "active": True}]},
        },
        municipality_slug="huizen",
        source_system_id="go-huizen",
    )

    person = normalized["organization_persons"][0].to_dict()
    assert person["display_name"] == "Ada van Lovelace"
    assert person["email"] == "ada@example.test"
    assert "user" not in person
    assert "usermanagementId" not in person
    position = normalized["organization_positions"][0].to_dict()
    assert position["role_category"] == "fractievoorzitter"
    membership = normalized["organization_group_memberships"][0].to_dict()
    assert membership["group_name"] == "Fractie A"


def test_public_organization_exports_are_written(tmp_path: Path, monkeypatch) -> None:
    calls: dict[str, list[dict[str, Any]]] = {}

    def fake_write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
        calls[path.name] = records

    monkeypatch.setattr(pipeline_run, "write_jsonl", fake_write_jsonl)
    outputs = pipeline_run._write_public_organization_exports(
        tmp_path,
        {
            "organization_groups": [{"id": "g1"}],
            "organization_persons": [{"id": "p1"}],
            "organization_roles": [{"id": "r1"}],
            "organization_positions": [{"id": "pos1"}],
            "organization_group_memberships": [{"id": "gm1"}],
        },
    )

    assert outputs == {
        "organization_groups": "organization_groups.jsonl",
        "organization_persons": "organization_persons.jsonl",
        "organization_roles": "organization_roles.jsonl",
        "organization_positions": "organization_positions.jsonl",
        "organization_group_memberships": "organization_group_memberships.jsonl",
    }
    assert calls["organization_persons.jsonl"] == [{"id": "p1"}]
