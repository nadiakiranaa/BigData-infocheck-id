from fastapi import HTTPException, UploadFile, status

from api_bridge.schemas.ocr import OcrTestResponse
from api_bridge.services.ocr_service import simulate_ocr_and_classify


async def test_ocr(file: UploadFile) -> OcrTestResponse:
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only image uploads are supported.",
        )

    return await simulate_ocr_and_classify(file)
