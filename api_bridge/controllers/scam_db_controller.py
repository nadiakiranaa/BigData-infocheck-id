from datetime import UTC, datetime
from uuid import uuid4

from fastapi import HTTPException, status

from api_bridge.data.dummy_store import scam_records
from api_bridge.schemas.scam_db import ScamRecord, ScamRecordCreate, ScamRecordUpdate


def _timestamp() -> str:
    return datetime.now(UTC).isoformat()


def _find_record_index(record_id: str) -> int:
    for index, record in enumerate(scam_records):
        if record["id"] == record_id:
            return index

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Scam record '{record_id}' not found.",
    )


def list_scam_records() -> list[ScamRecord]:
    return [ScamRecord(**record) for record in scam_records]


def create_scam_record(payload: ScamRecordCreate) -> ScamRecord:
    now = _timestamp()
    record = {
        "id": f"scam-{uuid4().hex[:8]}",
        **payload.model_dump(),
        "created_at": now,
        "updated_at": now,
    }
    scam_records.insert(0, record)
    return ScamRecord(**record)


def update_scam_record(record_id: str, payload: ScamRecordUpdate) -> ScamRecord:
    index = _find_record_index(record_id)
    stored = scam_records[index]
    updates = payload.model_dump(exclude_unset=True)
    stored.update(updates)
    stored["updated_at"] = _timestamp()
    scam_records[index] = stored
    return ScamRecord(**stored)


def delete_scam_record(record_id: str) -> dict[str, str]:
    index = _find_record_index(record_id)
    deleted_id = scam_records[index]["id"]
    del scam_records[index]
    return {"message": "Scam record deleted.", "id": deleted_id}
