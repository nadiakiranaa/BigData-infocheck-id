from api_bridge.data.dummy_store import now_iso, stats_snapshot
from api_bridge.schemas.stats import StatsResponse


def get_realtime_stats() -> StatsResponse:
    stats_snapshot["last_updated"] = now_iso()
    return StatsResponse(**stats_snapshot)
