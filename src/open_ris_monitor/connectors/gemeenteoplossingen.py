from __future__ import annotations

from typing import Any

import httpx

from open_ris_monitor.connectors.base import BaseConnector, ConnectorError, RawRecord


class GemeenteOplossingenConnector(BaseConnector):
    """Connector for GemeenteOplossingen RIS API endpoints.

    The exact endpoint mapping can differ per municipality and still needs to be
    validated for Huizen. This connector is intentionally defensive:

    - endpoint paths are configurable,
    - multiple common response shapes are accepted,
    - the connector returns raw records only,
    - normalisation is handled elsewhere.
    """

    DEFAULT_ENDPOINTS = {
        "meetings": "vergaderingen",
        "agenda_items": "agendapunten",
        "documents": "documenten",
    }

    def __init__(
        self,
        base_url: str,
        timeout_seconds: int = 30,
        endpoints: dict[str, str] | None = None,
    ) -> None:
        super().__init__(base_url)
        self.client = httpx.Client(timeout=timeout_seconds)
        self.endpoints = {**self.DEFAULT_ENDPOINTS, **(endpoints or {})}

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self.client.close()

    def _build_url(self, path: str) -> str:
        return f"{self.base_url}/{path.lstrip('/')}"

    def _get_json(self, path: str) -> Any:
        url = self._build_url(path)
        try:
            response = self.client.get(
                url,
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            raise ConnectorError(
                f"GemeenteOplossingen API returned HTTP "
                f"{exc.response.status_code} for {url}"
            ) from exc
        except httpx.HTTPError as exc:
            raise ConnectorError(f"Could not fetch {url}: {exc}") from exc
        except ValueError as exc:
            raise ConnectorError(f"Response from {url} is not valid JSON") from exc

    def _as_records(self, payload: Any, resource_name: str) -> list[RawRecord]:
        """Convert common API response shapes to a list of raw records."""
        if isinstance(payload, list):
            return self._ensure_record_list(payload, resource_name)

        if isinstance(payload, dict):
            for key in ("data", "items", "results", "value"):
                value = payload.get(key)
                if isinstance(value, list):
                    return self._ensure_record_list(value, resource_name)

            # Some APIs return a single object. Treat it as one record only when
            # it looks like a resource and not like a wrapper without records.
            if payload and not any(k in payload for k in ("data", "items", "results", "value")):
                return [payload]

        raise ConnectorError(
            f"Unexpected response shape for {resource_name}: {type(payload).__name__}"
        )

    def _ensure_record_list(self, records: list[Any], resource_name: str) -> list[RawRecord]:
        invalid_items = [item for item in records if not isinstance(item, dict)]
        if invalid_items:
            raise ConnectorError(
                f"Expected {resource_name} records to be objects, "
                f"but found {len(invalid_items)} invalid item(s)."
            )
        return records

    def fetch_meetings(self) -> list[RawRecord]:
        payload = self._get_json(self.endpoints["meetings"])
        return self._as_records(payload, "meetings")

    def fetch_agenda_items(self) -> list[RawRecord]:
        payload = self._get_json(self.endpoints["agenda_items"])
        return self._as_records(payload, "agenda_items")

    def fetch_documents(self) -> list[RawRecord]:
        payload = self._get_json(self.endpoints["documents"])
        return self._as_records(payload, "documents")

    def fetch_document_file(self, download_url: str) -> bytes:
        try:
            response = self.client.get(download_url)
            response.raise_for_status()
            return response.content
        except httpx.HTTPError as exc:
            raise ConnectorError(f"Could not download document {download_url}: {exc}") from exc
