"""Poll active service alerts from the Zentryx REST API."""

from __future__ import annotations

import asyncio
import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class ApiAlertService:
    def __init__(
        self,
        *,
        base_url: str,
        route_id: str,
        vehicle_id: str | None = None,
        poll_interval_seconds: float = 5.0,
        request_timeout_seconds: float = 4.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.route_id = route_id
        self.vehicle_id = vehicle_id
        self.poll_interval_seconds = poll_interval_seconds
        self.request_timeout_seconds = request_timeout_seconds

    def _fetch_alerts(self):
        params = {"route_id": self.route_id}
        if self.vehicle_id:
            params["vehicle_id"] = self.vehicle_id
        url = f"{self.base_url}/v1/alerts?{urlencode(params)}"
        request = Request(url, headers={"Accept": "application/json"})
        with urlopen(request, timeout=self.request_timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
        alerts = payload.get("alerts") or []
        return alerts[0] if alerts else None

    async def stream(self):
        while True:
            try:
                yield await asyncio.to_thread(self._fetch_alerts)
            except (HTTPError, URLError, TimeoutError, ValueError, json.JSONDecodeError):
                # A network failure should not fabricate an all-clear state.
                pass
            await asyncio.sleep(self.poll_interval_seconds)
