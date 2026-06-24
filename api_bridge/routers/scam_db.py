from fastapi import APIRouter, status

from api_bridge.controllers.scam_db_controller import (
    create_scam_record,
    delete_scam_record,
    list_scam_records,
    update_scam_record,
)
from api_bridge.schemas.scam_db import ScamRecord, ScamRecordCreate, ScamRecordUpdate


router = APIRouter()


@router.get("/scam-db", response_model=list[ScamRecord])
def read_scam_records():
    return list_scam_records()


@router.post("/scam-db", response_model=ScamRecord, status_code=status.HTTP_201_CREATED)
def add_scam_record(payload: ScamRecordCreate):
    return create_scam_record(payload)


@router.put("/scam-db/{record_id}", response_model=ScamRecord)
def edit_scam_record(record_id: str, payload: ScamRecordUpdate):
    return update_scam_record(record_id, payload)


@router.delete("/scam-db/{record_id}")
def remove_scam_record(record_id: str):
    return delete_scam_record(record_id)
