from typing import Literal

from pydantic import BaseModel, Field


ScamIdentifierType = Literal["bank_account", "phone_number"]
ScamStatus = Literal["active", "under_review", "resolved"]


class ScamRecordBase(BaseModel):
    identifier_type: ScamIdentifierType
    identifier_value: str = Field(..., min_length=5, max_length=64)
    owner_name: str = Field(..., min_length=2, max_length=120)
    source: str = Field(..., min_length=2, max_length=120)
    report_count: int = Field(default=1, ge=0)
    status: ScamStatus = "active"
    notes: str | None = Field(default=None, max_length=500)


class ScamRecordCreate(ScamRecordBase):
    pass


class ScamRecordUpdate(BaseModel):
    identifier_type: ScamIdentifierType | None = None
    identifier_value: str | None = Field(default=None, min_length=5, max_length=64)
    owner_name: str | None = Field(default=None, min_length=2, max_length=120)
    source: str | None = Field(default=None, min_length=2, max_length=120)
    report_count: int | None = Field(default=None, ge=0)
    status: ScamStatus | None = None
    notes: str | None = Field(default=None, max_length=500)


class ScamRecord(ScamRecordBase):
    id: str
    created_at: str
    updated_at: str
