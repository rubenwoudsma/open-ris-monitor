"""Load municipality configuration without importing harvest orchestration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]


def load_municipality_config(slug: str) -> dict[str, Any]:
    """Load a municipality configuration file."""
    config_path = REPO_ROOT / "config" / "municipalities" / f"{slug}.yml"
    if not config_path.exists():
        raise FileNotFoundError(f"Municipality config not found: {config_path}")
    with config_path.open("r", encoding="utf-8") as file:
        payload = yaml.safe_load(file)
    if not isinstance(payload, dict):
        raise ValueError(f"Expected YAML object in {config_path}")
    return payload
