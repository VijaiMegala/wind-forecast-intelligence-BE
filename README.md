# Renewable Generation Intelligence API

> **Built by me** — Product design, planning, and application logic are my own.
> AI was used as an implementation assistant.

FastAPI proxy and analysis service for Elexon BMRS `FUELHH` actuals and
`WINDFOR` forecasts.

## Purpose

The backend converts raw Elexon generation data into a stable, validated API for
the GridSight frontend. It is more than a transparent proxy: it applies the
day-ahead decision cutoff, prevents hindsight, matches forecast and actual
delivery timestamps, and calculates forecast-accuracy metrics.

```text
Frontend request
      ↓
FastAPI route and validation
      ↓
Elexon client → FUELHH and WINDFOR
      ↓
Forecast selection and timestamp matching
      ↓
Accuracy metrics and typed response
```

## Prerequisites

- Python 3.12 or newer
- [uv](https://docs.astral.sh/uv/)
- Network access to `https://data.elexon.co.uk`

## Local development

```bash
uv sync --dev
uv run fastapi dev main.py
```

The API is available at `http://localhost:8000`.

- Swagger documentation: `http://localhost:8000/docs`
- OpenAPI schema: `http://localhost:8000/openapi.json`
- Health check: `http://localhost:8000/health`

## Configuration

Configuration is read from environment variables:

| Variable | Default | Purpose |
| --- | --- | --- |
| `ELEXON_BASE_URL` | `https://data.elexon.co.uk/bmrs/api/v1` | Elexon BMRS API base URL |
| `FRONTEND_ORIGINS` | `http://localhost:3000` | Comma-separated CORS origins |

Example:

```bash
ELEXON_BASE_URL=https://data.elexon.co.uk/bmrs/api/v1 \
FRONTEND_ORIGINS=http://localhost:3000 \
uv run fastapi dev main.py
```

Do not add a trailing slash to `ELEXON_BASE_URL` unless the deployment proxy
requires it; the client normalises the value internally.

## API endpoints

### `GET /health`

Returns a basic service health response:

```json
{"status": "ok"}
```

### `GET /api/v1/generation/metadata`

Returns resources currently supported by both an actual and compatible forecast
dataset. The frontend uses this response to populate its resource selector.

Wind currently maps to:

- Actual dataset: `FUELHH`
- Forecast dataset: `WINDFOR`
- Market timezone: `Europe/London`

### `GET /api/v1/generation/analysis`

Accepts:

| Parameter | Description |
| --- | --- |
| `delivery_date_from` | First delivery date to analyse |
| `delivery_date_to` | Last delivery date to analyse |
| `forecast_publish_from` | Beginning of the forecast publication window |
| `forecast_publish_to` | End of the forecast publication window |
| `fuel_type` | Resource identifier, currently `WIND` |
| `decision_cutoff` | Prior-day buying cutoff in market-local time |
| `timezone` | Market timezone, normally `Europe/London` |

It returns matched delivery points, selected forecast publication timestamps,
actual and forecast MW values, errors, settlement periods, and aggregate MAE,
RMSE, Bias, and MAPE.

## Analysis operation

For every actual generation record, the service:

1. Converts the delivery timestamp into the configured market timezone.
2. Builds the decision deadline using the previous day and configured cutoff.
3. Finds forecasts with the identical delivery timestamp.
4. Excludes forecasts published after the deadline.
5. Selects the most recently published eligible forecast.
6. Calculates signed, absolute, and percentage errors.
7. Aggregates all matched observations into accuracy metrics.

`WINDFOR` is hourly while `FUELHH` is half-hourly. The service intentionally
compares only identical timestamps instead of interpolating or attaching an
hourly forecast to an unrelated half-hour period.

## Implicit validation

The API validates:

- Delivery start is on or before delivery end.
- Delivery ranges do not exceed 63 days.
- Forecast publication timestamps include a timezone.
- Forecast publication start is before publication end.
- The timezone is valid.
- The selected resource has a compatible forecast dataset.
- Elexon responses are lists matching the expected typed models.
- Percentage errors are not calculated when actual generation is zero.

Upstream connection, HTTP, and response-decoding failures are returned as a
consistent `502` error without exposing internal exception details.

## Project structure

```text
main.py                         ASGI entry point
app/main.py                     FastAPI application and middleware
app/api/routes/generation.py    Request validation and API endpoints
app/clients/elexon.py           Elexon HTTP integration
app/core/config.py              Environment configuration
app/models/generation.py        Typed upstream and response contracts
app/services/analysis.py        Cutoff, matching, and metric logic
tests/test_analysis.py          Core no-hindsight and matching tests
```

## Verification

```bash
uv run pytest -q
```

The tests verify that the service selects the latest forecast published before
the decision deadline and does not match different delivery timestamps.

## Production operation

Set explicit CORS origins and run the ASGI application using the organisation's
standard process manager or container runtime. Ensure outbound HTTPS access to
Elexon is available and configure frontend deployments to use this service's
`/api/v1` base URL.
