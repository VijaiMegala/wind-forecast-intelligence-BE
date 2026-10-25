import asyncio
from datetime import date, datetime, time
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, HTTPException, Query

from app.clients.elexon import ElexonClient, ElexonError
from app.core.config import settings
from app.models.generation import (
    AnalysisFilters,
    AnalysisResponse,
    MetadataResponse,
    ResourceOption,
)
from app.services.analysis import build_analysis

router = APIRouter(prefix="/generation", tags=["generation"])
client = ElexonClient(settings.elexon_base_url)

RESOURCES = [
    ResourceOption(
        value="WIND",
        label="Wind",
        actual_dataset="FUELHH",
        forecast_dataset="WINDFOR",
    )
]


@router.get("/metadata", response_model=MetadataResponse)
async def get_metadata() -> MetadataResponse:
    return MetadataResponse(resources=RESOURCES, default_timezone="Europe/London")


@router.get("/analysis", response_model=AnalysisResponse)
async def get_analysis(
    delivery_date_from: date = Query(default=date(2026, 1, 1)),
    delivery_date_to: date = Query(default=date(2026, 1, 31)),
    forecast_publish_from: datetime = Query(default=datetime.fromisoformat("2025-12-01T00:00+00:00")),
    forecast_publish_to: datetime = Query(default=datetime.fromisoformat("2026-01-31T23:59+00:00")),
    fuel_type: str = Query(default="WIND", min_length=1, max_length=24),
    decision_cutoff: time = Query(default=time(11, 0)),
    timezone_name: str = Query(default="Europe/London", alias="timezone"),
) -> AnalysisResponse:
    if delivery_date_from > delivery_date_to:
        raise HTTPException(422, "delivery_date_from must be on or before delivery_date_to")
    if (delivery_date_to - delivery_date_from).days > 62:
        raise HTTPException(422, "delivery date range cannot exceed 63 days")
    if forecast_publish_from.tzinfo is None or forecast_publish_to.tzinfo is None:
        raise HTTPException(422, "forecast publication timestamps must include a timezone")
    if forecast_publish_from > forecast_publish_to:
        raise HTTPException(422, "forecast_publish_from must be before forecast_publish_to")
    if fuel_type.upper() not in {resource.value for resource in RESOURCES}:
        raise HTTPException(422, "This resource does not yet have a compatible forecast dataset")
    try:
        ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError as exc:
        raise HTTPException(422, "Unknown timezone") from exc

    try:
        actuals, forecasts = await asyncio.gather(
            client.get_actuals(delivery_date_from, delivery_date_to, fuel_type.upper()),
            client.get_forecasts(forecast_publish_from, forecast_publish_to),
        )
    except ElexonError as exc:
        raise HTTPException(502, str(exc)) from exc

    points, metrics, unmatched = build_analysis(
        actuals, forecasts, delivery_date_from, delivery_date_to, decision_cutoff, timezone_name
    )
    return AnalysisResponse(
        filters=AnalysisFilters(
            delivery_date_from=delivery_date_from,
            delivery_date_to=delivery_date_to,
            forecast_publish_from=forecast_publish_from,
            forecast_publish_to=forecast_publish_to,
            fuel_type=fuel_type.upper(),
            decision_cutoff=decision_cutoff,
            timezone=timezone_name,
        ),
        metrics=metrics,
        points=points,
        unmatched_actuals=unmatched,
    )
