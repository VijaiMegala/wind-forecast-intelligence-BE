from datetime import date, datetime, time

from pydantic import BaseModel, Field


class ActualGeneration(BaseModel):
    dataset: str
    publish_time: datetime = Field(alias="publishTime")
    start_time: datetime = Field(alias="startTime")
    settlement_date: date = Field(alias="settlementDate")
    settlement_period: int = Field(alias="settlementPeriod")
    fuel_type: str = Field(alias="fuelType")
    generation: float


class ForecastGeneration(BaseModel):
    dataset: str
    publish_time: datetime = Field(alias="publishTime")
    start_time: datetime = Field(alias="startTime")
    generation: float


class AnalysisPoint(BaseModel):
    start_time: datetime
    settlement_period: int
    forecast_publish_time: datetime
    forecast_mw: float
    actual_mw: float
    error_mw: float
    absolute_error_mw: float
    absolute_percentage_error: float | None


class AccuracyMetrics(BaseModel):
    observations: int
    mae_mw: float
    rmse_mw: float
    bias_mw: float
    mape_percent: float | None


class AnalysisFilters(BaseModel):
    delivery_date_from: date
    delivery_date_to: date
    forecast_publish_from: datetime
    forecast_publish_to: datetime
    fuel_type: str
    decision_cutoff: time
    timezone: str


class AnalysisResponse(BaseModel):
    filters: AnalysisFilters
    metrics: AccuracyMetrics
    points: list[AnalysisPoint]
    unmatched_actuals: int


class ResourceOption(BaseModel):
    value: str
    label: str
    actual_dataset: str
    forecast_dataset: str


class MetadataResponse(BaseModel):
    resources: list[ResourceOption]
    default_timezone: str
