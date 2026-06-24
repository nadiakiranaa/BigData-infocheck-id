from api_bridge.data.dummy_store import live_feed_items
from api_bridge.schemas.live_feed import LiveFeedItem


def get_live_feed(limit: int = 25) -> list[LiveFeedItem]:
    return [LiveFeedItem(**item) for item in live_feed_items[:limit]]
