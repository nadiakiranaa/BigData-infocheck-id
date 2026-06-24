from typing import Literal

from pydantic import BaseModel, Field


FeedLabel = Literal["Valid", "Hoaks", "Scam"]


class LiveFeedItem(BaseModel):
    id: str
    timestamp: str
    source: str
    source_type: Literal["Telegram", "RSS"]
    text_snippet: str
    label: FeedLabel
    confidence: float = Field(..., ge=0, le=100)
    topic: str
