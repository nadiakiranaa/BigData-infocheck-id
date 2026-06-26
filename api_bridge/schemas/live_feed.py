from typing import Literal, Optional

from pydantic import BaseModel, Field


FeedLabel = Literal["Valid", "Hoaks", "Scam", "Penipuan", "Netral", "Review"]


class LiveFeedItem(BaseModel):
    id: str
    timestamp: str
    source: str
    source_type: Literal["Telegram", "RSS", "Twitter"]
    text_snippet: str
    label: FeedLabel
    confidence: float = Field(..., ge=0, le=100)
    topic: str
    url: Optional[str] = None
