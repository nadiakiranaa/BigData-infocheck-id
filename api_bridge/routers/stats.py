from fastapi import APIRouter

from api_bridge.controllers.stats_controller import get_realtime_stats
from api_bridge.schemas.stats import StatsResponse


router = APIRouter()


@router.get("/stats", response_model=StatsResponse)
def read_stats():
    return get_realtime_stats()
