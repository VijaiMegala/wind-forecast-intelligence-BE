from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone
import math
from zoneinfo import ZoneInfo

from app.models.generation import (
    AccuracyMetrics,
    ActualGeneration,
    AnalysisPoint,
    ForecastGeneration,
)


def decision_deadline(
    delivery_time: datetime, cutoff: time, timezone_name: str
) -> datetime:
    market_timezone = ZoneInfo(timezone_name)
    local_delivery_date = delivery_time.astimezone(market_timezone).date()
    local_deadline = datetime.combine(
        local_delivery_date - timedelta(days=1), cutoff, tzinfo=market_timezone
    )
    return local_deadline.astimezone(timezone.utc)


def build_analysis(
    actuals: list[ActualGeneration],
    forecasts: list[ForecastGeneration],
    delivery_from: date,
    delivery_to: date,
    cutoff: time,
    timezone_name: str,
) -> tuple[list[AnalysisPoint], AccuracyMetrics, int]:
    forecasts_by_start: dict[datetime, list[ForecastGeneration]] = defaultdict(list)
    for forecast in forecasts:
        forecasts_by_start[forecast.start_time].append(forecast)

    points: list[AnalysisPoint] = []
    unmatched = 0
    market_timezone = ZoneInfo(timezone_name)
    for actual in sorted(actuals, key=lambda item: item.start_time):
        target_date = actual.start_time.astimezone(market_timezone).date()
        if not delivery_from <= target_date <= delivery_to:
            continue
        deadline = decision_deadline(actual.start_time, cutoff, timezone_name)
        eligible = [
            forecast
            for forecast in forecasts_by_start.get(actual.start_time, [])
            if forecast.publish_time <= deadline
        ]
        if not eligible:
            unmatched += 1
            continue
        latest = max(eligible, key=lambda item: item.publish_time)
        error = latest.generation - actual.generation
        percentage_error = (
            abs(error) / actual.generation * 100 if actual.generation else None
        )
        points.append(
            AnalysisPoint(
                start_time=actual.start_time,
                settlement_period=actual.settlement_period,
                forecast_publish_time=latest.publish_time,
                forecast_mw=latest.generation,
                actual_mw=actual.generation,
                error_mw=round(error, 2),
                absolute_error_mw=round(abs(error), 2),
                absolute_percentage_error=(
                    round(percentage_error, 2) if percentage_error is not None else None
                ),
            )
        )

    if not points:
        return points, AccuracyMetrics(
            observations=0, mae_mw=0, rmse_mw=0, bias_mw=0, mape_percent=None
        ), unmatched

    errors = [point.error_mw for point in points]
    percentage_errors = [
        point.absolute_percentage_error
        for point in points
        if point.absolute_percentage_error is not None
    ]
    count = len(points)
    metrics = AccuracyMetrics(
        observations=count,
        mae_mw=round(sum(abs(error) for error in errors) / count, 2),
        rmse_mw=round(math.sqrt(sum(error**2 for error in errors) / count), 2),
        bias_mw=round(sum(errors) / count, 2),
        mape_percent=(
            round(sum(percentage_errors) / len(percentage_errors), 2)
            if percentage_errors
            else None
        ),
    )
    return points, metrics, unmatched
