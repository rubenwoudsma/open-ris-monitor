"""Shared runtime configuration for bounded harvest profiles.

The profiles are intentionally small and explicit. They describe how a run
should behave operationally, without changing the public export contract.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Final


@dataclass(frozen=True)
class HarvestProfile:
    """Resolved defaults for one harvest strategy."""

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
    # Fast smoke-test profile. Keeps the latest-document behaviour intentionally
    # small so forks can check credentials and endpoint shape without producing a
    # large public dataset.
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
    # Public profile for GitHub Pages publication. Issue #69 observed that the
    # previous latest/250 profile capped documents too aggressively for a useful
    # document-first viewer. This profile now walks the full endpoint up to a
    # bounded public cap, while keeping exports compact and reviewable.
    "public": HarvestProfile(
        mode="full",
        limit=250,
        batch_size=100,
        max_documents=1000,
        include_relations=True,
        meeting_scan_limit=1000,
        meeting_session_batch_size=100,
        meeting_item_limit=5000,
    ),
    # Backfill profile for deliberate manual recovery or coverage expansion. It
    # is unbounded by default, so use it intentionally and inspect the artifact
    # before committing public output for a new municipality.
    "backfill": HarvestProfile(
        mode="full",
        limit=1000,
        batch_size=100,
        max_documents=None,
        include_relations=True,
        meeting_scan_limit=5000,
        meeting_session_batch_size=100,
        meeting_item_limit=None,
    ),
}

HARVEST_PROFILE_NAMES: Final[tuple[str, ...]] = tuple(HARVEST_PROFILES)
PROFILE_OPTION_KEYS: Final[frozenset[str]] = frozenset(asdict(LEGACY_DEFAULTS))


def resolve_harvest_options(
    profile_name: str | None,
    overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Resolve a harvest profile and apply explicit overrides.

    When no profile is selected, legacy CLI defaults are returned. Overrides are
    applied by key presence, so values such as ``None`` remain valid explicit
    overrides for unbounded backfill-style runs.
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
