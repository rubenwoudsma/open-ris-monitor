from __future__ import annotations

from typing import Any

import httpx

from open_ris_monitor.connectors.base import BaseConnector


class GemeenteOplossingenConnector(BaseConnector):
    """Connector for GemeenteOplossingen RIS API endpoints.

    The exact endpoint mapping should be verified against the municipality-specific API.
    This class is intentionally conservative in the scaffold phase.
    """

    def __init__(self, base_url: str, timeout_seconds: int = 30) -> None:
        super().__init__(base_url)
        self.client = httpx.Client(timeout=timeout_seconds)

    def _get_json(self, path: str) -> Any:
        url = f"{self.base_url}/{path.lstrip('/')}"
        response = self.client.get(url)
        response.raise_for_status()
        return response.json()

    def fetch_meetings(self) -> list[dict[str, Any]]:
        # TODO: verify endpoint name for Huizen.
        data = self._get_json("vergaderingen")
        return data if isinstance(data, list) else data.get("data", [])

    def fetch_agenda_items(self) -> list[dict[str, Any]]:
        # TODO: verify endpoint name for Huizen.
        data = self._get_json("agendapunten")
        return data if isinstance(data, list) else data.get("data", [])

    def fetch_documents(self) -> list[dict[str, Any]]:
        # TODO: verify endpoint name for Huizen.
        data = self._get_json("documenten")
        return data if isinstance(data, list) else data.get("data", [])

    def fetch_document_file(self, download_url: str) -> bytes:
        response = self.client.get(download_url)
        response.raise_for_status()
        return response.content
