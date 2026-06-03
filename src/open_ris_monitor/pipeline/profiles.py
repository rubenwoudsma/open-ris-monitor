"""Harvest profile definitions for bounded operational runs."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Final


@dataclass(frozen=True)
class HarvestProfile:
    """Resolved defaults for one bounded harvest strategy."""

    mode: str
    limit: int
    batch_size: int
    max_documents: int | None
    include_relations: bool
    meeting_scan_limit: int
    meeting_session_batch_size: int
    meeting_item_limit: int | None


LEGACY_DEFAULTS: Final[HarvestProfile] = HarvestProfile(
    mode="latest",
    limit=25,
    batch_size=100,
    max_documents=None,
    include_relations=False,
    meeting_scan_limit=250,
    meeting_session_batch_size=100,
    meeting_item_limit=1000,
)

HARVEST_PROFILES: Final[dict[str, HarvestProfile]] = {
    "quick": HarvestProfile(
        mode="latest",
        limit=10,
        batch_size=50,
        max_documents=None,
        include_relations=True,
        meeting_scan_limit=50,
        meeting_session_batch_size=50,
        meeting_item_limit=200,
    ),
    "public": HarvestProfile(
        mode="latest",
        limit=250,
        batch_size=100,
        max_documents=None,
        include_relations=True,
        meeting_scan_limit=250,
        meeting_session_batch_size=100,
        meeting_item_limit=1000,
    ),
    "backfill": HarvestProfile(
        mode="full",
        limit=1000,
        batch_size=100,
        max_documents=None,
        include_relations=True,
        meeting_scan_limit=1000,
        meeting_session_batch_size=100,
        meeting_item_limit=5000,
    ),
}

HARVEST_PROFILE_NAMES: Final[tuple[str, ...]] = tuple(HARVEST_PROFILES)
PROFILE_OPTION_KEYS: Final[frozenset[str]] = frozenset(asdict(LEGACY_DEFAULTS))


def resolve_harvest_options(
    profile_name: str | None,
    overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Resolve a harvest profile and apply explicit CLI overrides.

    When no profile is selected, the previous CLI defaults are returned.
    Overrides are applied by key presence, so values such as ``None`` are
    valid explicit overrides for unbounded backfill-style runs.
    """

    if profile_name is None:
        resolved = asdict(LEGACY_DEFAULTS)
    else:
        try:
            resolved = asdict(HARVEST_PROFILES[profile_name])
        except KeyError as exc:
            valid_names = ", ".join(HARVEST_PROFILE_NAMES)
            raise ValueError(
                f"Unknown harvest profile: {profile_name}. Valid profiles: {valid_names}"
            ) from exc

    for key, value in (overrides or {}).items():
        if key not in PROFILE_OPTION_KEYS:
            raise ValueError(f"Unknown harvest profile option: {key}")
        resolved[key] = value

    return resolved
