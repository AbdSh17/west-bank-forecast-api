"""The FastAPI app: startup, routers and error handlers."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from api_to_sqlite.health.router import router as health_router
from fastapi import FastAPI

from api_to_sqlite.database import ConnectionManager
from api_to_sqlite.errors import register_error_handlers
from api_to_sqlite.cities.router import router as cities_router

from api_to_sqlite.cities import service as city_service
from api_to_sqlite.cities.dao import CityDAO
from api_to_sqlite.forecasts.dao import ForecastDAO

from api_to_sqlite.forecasts.router import router as forecasts_router

from api_to_sqlite.reports.router import router as reports_router

from api_to_sqlite.forecasts.refresh_router import router as refresh_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Prepare the database at startup so a down database stops the server early."""
    cities = CityDAO()
    with ConnectionManager().connection() as conn:
        cities.create_schema(conn)
        ForecastDAO().create_schema(conn)
        city_service.seed_cities(conn, cities)
    yield


app = FastAPI(title="Weather API", lifespan=lifespan)
app.include_router(health_router)
app.include_router(cities_router)
app.include_router(forecasts_router)
app.include_router(reports_router)
app.include_router(refresh_router)

register_error_handlers(app)
