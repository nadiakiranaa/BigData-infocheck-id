from fastapi import APIRouter, Query

from api_bridge.controllers.live_feed_controller import get_live_feed
from api_bridge.schemas.live_feed import LiveFeedItem


router = APIRouter()


@router.get("/live-feed", response_model=list[LiveFeedItem])
def read_live_feed(limit: int = Query(default=25, ge=1, le=100)):
    return get_live_feed(limit=limit)
