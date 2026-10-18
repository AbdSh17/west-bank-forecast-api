"""Fetch daily forecasts from the Open-Meteo API."""

import requests
from api_to_sqlite.openmeteo.exceptions import FetchError


from api_to_sqlite.config import (
    API_URL,
    DAILY_VARIABLES,
    FORECAST_DAYS,
    TIMEOUT_SECONDS,
)


def fetch_forecast(latitude: float, longitude: float) -> dict:
    """Request the daily forecast for one location and return the parsed JSON."""
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": DAILY_VARIABLES,
        "timezone": "auto",
        "forecast_days": FORECAST_DAYS,
    }
    try:
        response = requests.get(API_URL, params=params, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
        data = response.json()
    except requests.Timeout as error:
        raise FetchError(
            f"Request timed out after {TIMEOUT_SECONDS} seconds"
        ) from error
    except requests.ConnectionError as error:
        raise FetchError("Could not connect to the Open-Meteo API") from error
    except requests.HTTPError as error:
        raise FetchError(_http_error_message(error.response)) from error
    except ValueError as error:
        raise FetchError(
            "The API returned a response that is not valid JSON"
        ) from error
    except requests.RequestException as error:
        raise FetchError(f"Request failed: {error}") from error

    if "daily" not in data:
        raise FetchError("Unexpected response from the API: no daily data")
    return data


def _http_error_message(response: requests.Response) -> str:
    """Build a readable message from an HTTP error response."""
    try:
        reason = response.json().get("reason")
    except ValueError:
        reason = None
    if reason:
        return f"The API rejected the request: {reason}"
    return f"The API returned HTTP status {response.status_code}"
