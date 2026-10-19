"""The refresh endpoint: fetch the forecasts from Open-Meteo and store them."""

from fastapi import APIRouter, Depends, Response

from api_to_sqlite.api_docs import DATABASE_UNAVAILABLE
from api_to_sqlite.cities.dao import CityDAO
from api_to_sqlite.database import ConnectionManager
from api_to_sqlite.forecasts import service
from api_to_sqlite.forecasts.dao import ForecastDAO
from api_to_sqlite.forecasts.schemas import RefreshOut, RefreshResultOut

router = APIRouter(prefix="/v1/forecast-refreshes", tags=["forecasts"])


def _to_out(result: service.CityResult) -> RefreshResultOut:
    """Turn one service result into its JSON shape."""
    if result.error is None:
        return RefreshResultOut(city=result.city, status="stored", days=result.days)
    return RefreshResultOut(city=result.city, status="failed", error=result.error)


def _status_for(results: list[service.CityResult]) -> int:
    """200 when every city is stored, 502 when none is, 207 for a mix."""
    failed = sum(1 for result in results if result.error is not None)
    if failed == 0:
        return 200
    if failed == len(results):
        return 502
    return 207


@router.post(
    "",
    response_model_exclude_none=True,
    summary="Refresh the forecasts from Open-Meteo",
    responses={
        207: {
            "model": RefreshOut,
            "description": "Some cities were stored and some failed.",
        },
        502: {
            "model": RefreshOut,
            "description": "No city could be stored. Open-Meteo failed for all.",
        },
        **DATABASE_UNAVAILABLE,
    },
)
def create_refresh(
    response: Response,
    manager: ConnectionManager = Depends(ConnectionManager),
    cities: CityDAO = Depends(CityDAO),
    forecasts: ForecastDAO = Depends(ForecastDAO),
) -> RefreshOut:
    """Fetch every city from Open-Meteo, store the forecasts and report each city."""
    results = service.refresh(manager, cities, forecasts)
    response.status_code = _status_for(results)
    return RefreshOut(results=[_to_out(result) for result in results])
