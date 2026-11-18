"""Construct source connectors independently of harvest orchestration."""

from __future__ import annotations

from typing import Any

from open_ris_monitor.connectors.gemeenteoplossingen import GemeenteOplossingenConnector


def _as_float(value: Any, default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    return float(value)


def build_connector(config: dict[str, Any]) -> GemeenteOplossingenConnector:
    """Build the configured source connector."""
    source_system = config["source_system"]
    connector_name = source_system["connector"]
    if connector_name != "gemeenteoplossingen":
        raise ValueError(f"Unsupported connector: {connector_name}")
    return GemeenteOplossingenConnector(
        base_url=source_system["base_url"],
        timeout_seconds=int(source_system.get("timeout_seconds", 30)),
        request_delay_seconds=_as_float(source_system.get("request_delay_seconds"), 0.0),
        retry_attempts=int(source_system.get("retry_attempts", 3)),
        retry_backoff_seconds=_as_float(source_system.get("retry_backoff_seconds"), 1.0),
        max_retry_delay_seconds=_as_float(source_system.get("max_retry_delay_seconds"), 60.0),
        user_agent=str(source_system.get("user_agent") or "").strip()
        or "OpenRISMonitor/0.1 (+https://github.com/rubenwoudsma/open-ris-monitor)",
        allowed_redirect_hosts=source_system.get("allowed_redirect_hosts") or (),
    )
