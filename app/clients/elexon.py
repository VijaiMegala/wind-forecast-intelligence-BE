from datetime import date, datetime
from typing import Any

import httpx

from app.models.generation import ActualGeneration, ForecastGeneration


class ElexonError(RuntimeError):
    """Raised when Elexon cannot provide a valid dataset response."""


class ElexonClient:
    def __init__(self, base_url: str, timeout_seconds: float = 60.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds

    async def _get(self, path: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(f"{self._base_url}{path}", params=params)
                response.raise_for_status()
                payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise ElexonError("Elexon data is temporarily unavailable") from exc

        if not isinstance(payload, list):
            raise ElexonError("Elexon returned an unexpected response")
        return payload

    async def get_actuals(
        self, date_from: date, date_to: date, fuel_type: str
    ) -> list[ActualGeneration]:
        payload = await self._get(
            "/datasets/FUELHH/stream",
            {
                "settlementDateFrom": date_from.isoformat(),
                "settlementDateTo": date_to.isoformat(),
                "fuelType": fuel_type,
            },
        )
        return [ActualGeneration.model_validate(item) for item in payload]

    async def get_forecasts(
        self, published_from: datetime, published_to: datetime
    ) -> list[ForecastGeneration]:
        payload = await self._get(
            "/datasets/WINDFOR/stream",
            {
                "publishDateTimeFrom": published_from.isoformat().replace("+00:00", "Z"),
                "publishDateTimeTo": published_to.isoformat().replace("+00:00", "Z"),
            },
        )
        return [ForecastGeneration.model_validate(item) for item in payload]
