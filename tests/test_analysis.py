from datetime import date, datetime, time

from app.models.generation import ActualGeneration, ForecastGeneration
from app.services.analysis import build_analysis


def utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def test_uses_latest_forecast_before_previous_day_cutoff() -> None:
    actual = ActualGeneration.model_validate(
        {
            "dataset": "FUELHH",
            "publishTime": "2026-01-02T12:30:00Z",
            "startTime": "2026-01-02T12:00:00Z",
            "settlementDate": "2026-01-02",
            "settlementPeriod": 25,
            "fuelType": "WIND",
            "generation": 100,
        }
    )
    forecasts = [
        ForecastGeneration(dataset="WINDFOR", publishTime=utc("2026-01-01T10:30:00Z"), startTime=actual.start_time, generation=90),
        ForecastGeneration(dataset="WINDFOR", publishTime=utc("2026-01-01T11:30:00Z"), startTime=actual.start_time, generation=110),
    ]
    points, metrics, unmatched = build_analysis(
        [actual], forecasts, date(2026, 1, 2), date(2026, 1, 2), time(11), "Europe/London"
    )
    assert points[0].forecast_mw == 90
    assert points[0].settlement_period == 25
    assert points[0].error_mw == -10
    assert metrics.mae_mw == 10
    assert unmatched == 0


def test_only_matches_identical_delivery_timestamp() -> None:
    actual = ActualGeneration.model_validate(
        {
            "dataset": "FUELHH",
            "publishTime": "2026-01-02T12:00:00Z",
            "startTime": "2026-01-02T11:30:00Z",
            "settlementDate": "2026-01-02",
            "settlementPeriod": 24,
            "fuelType": "WIND",
            "generation": 100,
        }
    )
    forecast = ForecastGeneration(
        dataset="WINDFOR", publishTime=utc("2026-01-01T10:00:00Z"),
        startTime=utc("2026-01-02T11:00:00Z"), generation=100,
    )
    points, metrics, unmatched = build_analysis(
        [actual], [forecast], date(2026, 1, 2), date(2026, 1, 2), time(11), "Europe/London"
    )
    assert points == []
    assert metrics.observations == 0
    assert unmatched == 1
