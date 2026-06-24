from typing import Literal

from pydantic import BaseModel, Field


class OcrTestResponse(BaseModel):
    filename: str
    content_type: str
    extracted_text: str
    classification: Literal["Scam", "Valid", "Review"]
    confidence: float = Field(..., ge=0, le=100)
    indicators: list[str]
    recommendation: str
