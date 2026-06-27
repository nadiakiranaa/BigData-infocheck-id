from pydantic import BaseModel, Field


class LabelDistribution(BaseModel):
    valid: float = Field(..., ge=0, le=100)
    hoaks: float = Field(..., ge=0, le=100)
    scam: float = Field(..., ge=0, le=100)

class ChartPoint(BaseModel):
    label: str
    value: int


class StatsResponse(BaseModel):
    total_messages_today: int
    hoax_detected_today: int
    scam_detected_today: int
    valid_detected_today: int
    hoax_vs_valid_percent: LabelDistribution
    active_sources: int
    last_updated: str
    hourly_volume: list[ChartPoint]
    risk_scatter: list[ChartPoint]
