"""Normalizers for public council organisation data."""

from __future__ import annotations

from datetime import date
from html import unescape
import re
from typing import Any, Iterable, TypeVar

from open_ris_monitor.models.organization import (
    OrganizationGroup,
    OrganizationGroupMembership,
    OrganizationPerson,
    OrganizationPosition,
    OrganizationRole,
)

T = TypeVar("T")
_TAG_RE = re.compile(r"<[^>]+>")
_WHITESPACE_RE = re.compile(r"\s+")


def _as_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _strip_html(value: Any) -> str | None:
    text = _as_text(value)
    if text is None:
        return None
    text = unescape(_TAG_RE.sub(" ", text))
    text = _WHITESPACE_RE.sub(" ", text).strip()
    return text or None


def _as_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _as_bool_or_none(value: Any) -> bool | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value != 0
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"1", "true", "yes", "ja"}:
            return True
        if lowered in {"0", "false", "no", "nee"}:
            return False
    return bool(value)


def _stable_unique(records: Iterable[T], key_fn: callable) -> list[T]:
    seen: set[str] = set()
    result: list[T] = []
    for record in records:
        key = str(key_fn(record))
        if key not in seen:
            seen.add(key)
            result.append(record)
    return result


def _display_name(person: dict[str, Any]) -> str | None:
    first = _strip_html(person.get("firstName") or person.get("first_name"))
    preposition = _strip_html(person.get("preposition") or person.get("preposition"))
    last = _strip_html(person.get("lastName") or person.get("last_name"))
    parts = [part for part in [first, preposition, last] if part]
    return " ".join(parts) or last or first


def _role_category(role_name: str | None) -> str | None:
    name = (role_name or "").lower()
    if "burgemeester" in name:
        return "burgemeester"
    if "griff" in name:
        return "griffie"
    if "fractievoorzitter" in name:
        return "fractievoorzitter"
    if "raadslid" in name or "raads" in name:
        return "raadslid"
    if "commissie" in name:
        return "commissielid"
    return None


def _is_active_position(source_active: bool | None, end_date: str | None) -> bool | None:
    if source_active is False:
        return False
    if end_date:
        try:
            return date.fromisoformat(end_date[:10]) >= date.today()
        except ValueError:
            return source_active
    return source_active if source_active is not None else True


def normalize_group(
    raw: dict[str, Any],
    *,
    municipality_slug: str,
    source_system_id: str,
) -> OrganizationGroup | None:
    source_id = _as_text(raw.get("id") or raw.get("source_id"))
    if not source_id:
        return None
    return OrganizationGroup(
        id=f"{municipality_slug}-group-{source_id}",
        source_id=source_id,
        municipality_slug=municipality_slug,
        source_system_id=source_system_id,
        name=_strip_html(raw.get("name")),
        type=_as_text(raw.get("type")),
        sort_order=_as_int(raw.get("sortOrder") or raw.get("sortorder") or raw.get("sort_order")),
    )


def normalize_person(
    raw: dict[str, Any],
    *,
    municipality_slug: str,
    source_system_id: str,
) -> OrganizationPerson | None:
    source_id = _as_text(raw.get("id") or raw.get("source_id"))
    if not source_id:
        return None
    return OrganizationPerson(
        id=f"{municipality_slug}-person-{source_id}",
        source_id=source_id,
        municipality_slug=municipality_slug,
        source_system_id=source_system_id,
        first_name=_strip_html(raw.get("firstName") or raw.get("first_name")),
        last_name=_strip_html(raw.get("lastName") or raw.get("last_name")),
        preposition=_strip_html(raw.get("preposition")),
        display_name=_display_name(raw),
        salutation=_strip_html(raw.get("salutation")),
        email=_as_text(raw.get("email")),
        active=_as_bool_or_none(raw.get("active")),
    )


def normalize_role(
    raw: dict[str, Any],
    *,
    municipality_slug: str,
    source_system_id: str,
) -> OrganizationRole | None:
    source_id = _as_text(raw.get("id") or raw.get("source_id"))
    if not source_id:
        return None
    name = _strip_html(raw.get("name"))
    return OrganizationRole(
        id=f"{municipality_slug}-role-{source_id}",
        source_id=source_id,
        municipality_slug=municipality_slug,
        source_system_id=source_system_id,
        name=name,
        sort_order=_as_int(raw.get("sortOrder") or raw.get("sortorder") or raw.get("sort_order")),
        role_category=_role_category(name),
    )


def normalize_position(
    raw: dict[str, Any],
    *,
    municipality_slug: str,
    source_system_id: str,
) -> OrganizationPosition | None:
    source_id = _as_text(raw.get("id") or raw.get("source_id"))
    if not source_id:
        return None
    person = raw.get("person") if isinstance(raw.get("person"), dict) else {}
    role = raw.get("role") if isinstance(raw.get("role"), dict) else {}
    person_source_id = _as_text(raw.get("personId") or raw.get("person_id") or person.get("id"))
    role_source_id = _as_text(raw.get("roleId") or raw.get("role_id") or role.get("id"))
    role_name = _strip_html(role.get("name") or raw.get("role_name"))
    end_date = _as_text(raw.get("end_date") or raw.get("endDate"))
    source_active = _as_bool_or_none(person.get("active") if person else raw.get("active"))

    return OrganizationPosition(
        id=f"{municipality_slug}-position-{source_id}",
        source_id=source_id,
        municipality_slug=municipality_slug,
        source_system_id=source_system_id,
        person_id=f"{municipality_slug}-person-{person_source_id}" if person_source_id else None,
        person_source_id=person_source_id,
        person_display_name=_display_name(person) if person else _strip_html(raw.get("person_display_name")),
        role_id=f"{municipality_slug}-role-{role_source_id}" if role_source_id else None,
        role_source_id=role_source_id,
        role_name=role_name,
        role_category=_role_category(role_name),
        start_date=_as_text(raw.get("start_date") or raw.get("startDate")),
        end_date=end_date,
        sort_order=_as_int(raw.get("sortOrder") or raw.get("sortorder") or raw.get("sort_order")),
        active=_is_active_position(source_active, end_date),
    )


def normalize_group_membership(
    raw: dict[str, Any],
    *,
    group: OrganizationGroup,
    municipality_slug: str,
    source_system_id: str,
) -> OrganizationGroupMembership | None:
    person_source_id = _as_text(raw.get("id") or raw.get("source_id"))
    if not person_source_id:
        return None
    person_id = f"{municipality_slug}-person-{person_source_id}"
    return OrganizationGroupMembership(
        id=f"{group.id}-person-{person_source_id}",
        group_id=group.id,
        group_source_id=group.source_id,
        person_id=person_id,
        person_source_id=person_source_id,
        municipality_slug=municipality_slug,
        source_system_id=source_system_id,
        group_name=group.name,
        group_type=group.type,
        person_display_name=_display_name(raw),
        active=_as_bool_or_none(raw.get("active")),
    )


def normalize_organization_harvest(
    organization_harvest: dict[str, Any],
    *,
    municipality_slug: str,
    source_system_id: str,
) -> dict[str, list[Any]]:
    groups = _stable_unique(
        [
            record
            for raw in organization_harvest.get("groups", [])
            if (record := normalize_group(raw, municipality_slug=municipality_slug, source_system_id=source_system_id)) is not None
        ],
        lambda record: record.id,
    )
    persons = _stable_unique(
        [
            record
            for raw in organization_harvest.get("persons", [])
            if (record := normalize_person(raw, municipality_slug=municipality_slug, source_system_id=source_system_id)) is not None
        ],
        lambda record: record.id,
    )
    roles = _stable_unique(
        [
            record
            for raw in organization_harvest.get("roles", [])
            if (record := normalize_role(raw, municipality_slug=municipality_slug, source_system_id=source_system_id)) is not None
        ],
        lambda record: record.id,
    )
    positions = _stable_unique(
        [
            record
            for raw in organization_harvest.get("positions", [])
            if (record := normalize_position(raw, municipality_slug=municipality_slug, source_system_id=source_system_id)) is not None
        ],
        lambda record: record.id,
    )
    groups_by_source_id = {group.source_id: group for group in groups}
    memberships = _stable_unique(
        [
            record
            for group_source_id, raw_members in organization_harvest.get("group_memberships", {}).items()
            for raw in raw_members
            if (group := groups_by_source_id.get(str(group_source_id))) is not None
            if (record := normalize_group_membership(raw, group=group, municipality_slug=municipality_slug, source_system_id=source_system_id)) is not None
        ],
        lambda record: record.id,
    )
    return {
        "organization_groups": groups,
        "organization_persons": persons,
        "organization_roles": roles,
        "organization_positions": positions,
        "organization_group_memberships": memberships,
    }
