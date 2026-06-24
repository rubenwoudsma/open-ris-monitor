"""Canonical organisation models for council context exports."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class OrganizationGroup:
    """Council organisation group, such as a fraction, committee or body."""

    id: str
    source_id: str
    municipality_slug: str
    source_system_id: str
    schema_version: str = "1.1.0"
    name: str | None = None
    type: str | None = None
    sort_order: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class OrganizationPerson:
    """Public council organisation actor."""

    id: str
    source_id: str
    municipality_slug: str
    source_system_id: str
    schema_version: str = "1.1.0"
    first_name: str | None = None
    last_name: str | None = None
    preposition: str | None = None
    display_name: str | None = None
    salutation: str | None = None
    email: str | None = None
    active: bool | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class OrganizationRole:
    """Role that can be assigned to a person through a position."""

    id: str
    source_id: str
    municipality_slug: str
    source_system_id: str
    schema_version: str = "1.1.0"
    name: str | None = None
    sort_order: int | None = None
    role_category: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class OrganizationPosition:
    """Position of a person in the council organisation."""

    id: str
    source_id: str
    municipality_slug: str
    source_system_id: str
    schema_version: str = "1.1.0"
    person_id: str | None = None
    person_source_id: str | None = None
    person_display_name: str | None = None
    role_id: str | None = None
    role_source_id: str | None = None
    role_name: str | None = None
    role_category: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    sort_order: int | None = None
    active: bool | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class OrganizationGroupMembership:
    """Grounded person-to-group membership from /groups/{groupId}/persons."""

    id: str
    group_id: str
    group_source_id: str
    person_id: str
    person_source_id: str
    municipality_slug: str
    source_system_id: str
    schema_version: str = "1.1.0"
    group_name: str | None = None
    group_type: str | None = None
    person_display_name: str | None = None
    active: bool | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
