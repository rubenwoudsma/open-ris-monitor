from pathlib import Path

import yaml


def test_huizen_config_is_valid_yaml() -> None:
    config_path = Path("config/municipalities/huizen.yml")
    payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))

    assert payload["municipality"]["slug"] == "huizen"
    assert payload["source_system"]["connector"] == "gemeenteoplossingen"
    assert payload["source_system"]["base_url"].endswith("/api/v2/")
