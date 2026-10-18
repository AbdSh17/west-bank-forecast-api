"""Constants shared across the api_to_sqlite modules."""

from pathlib import Path
import os

from dotenv import load_dotenv

load_dotenv()

DB_PATH = Path("data/weather.db")

CITIES = [
    ("Ramallah", 31.90, 35.20),
    ("Nablus", 32.22, 35.26),
    ("Hebron", 31.53, 35.10),
    ("Jenin", 32.46, 35.30),
    ("Jericho", 31.86, 35.46),
]

DB_DIALECT = os.environ.get("DB_DIALECT", "sqlite")
MYSQL_HOST = os.environ.get("MYSQL_HOST", "localhost")
MYSQL_PORT = os.environ.get("MYSQL_PORT", "3306")
MYSQL_USER = os.environ.get("MYSQL_USER")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD")
MYSQL_DATABASE = os.environ.get("MYSQL_DATABASE", "weather")

MYSQL_POOL_SIZE = os.environ.get("MYSQL_POOL_SIZE", "5")

API_URL = "https://api.open-meteo.com/v1/forecast"
DAILY_VARIABLES = "temperature_2m_max,temperature_2m_min,precipitation_sum"
FORECAST_DAYS = 7
TIMEOUT_SECONDS = 10
