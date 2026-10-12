"""Fetch daily forecasts from the Open-Meteo API."""

import requests

API_URL = "https://api.open-meteo.com/v1/forecast"
DAILY_VARIABLES = "temperature_2m_max,temperature_2m_min,precipitation_sum"
FORECAST_DAYS = 7
TIMEOUT_SECONDS = 10


def fetch_forecast(latitude: float, longitude: float) -> dict:
    """Request the daily forecast for one location and return the parsed JSON."""
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": DAILY_VARIABLES,
        "timezone": "auto",
        "forecast_days": FORECAST_DAYS,
    }
    response = requests.get(API_URL, params=params, timeout=TIMEOUT_SECONDS)
    response.raise_for_status()
    return response.json()
