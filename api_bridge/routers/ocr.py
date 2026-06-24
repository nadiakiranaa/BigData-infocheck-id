from fastapi import APIRouter, HTTPException, Request, status

from api_bridge.controllers.ocr_controller import test_ocr
from api_bridge.schemas.ocr import OcrTestResponse


router = APIRouter()


@router.post("/test-ocr", response_model=OcrTestResponse)
async def analyze_uploaded_image(request: Request):
    try:
        form = await request.form()
    except AssertionError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="python-multipart is required for file uploads. Install it with: pip install python-multipart",
        ) from exc

    file = form.get("file")
    if not hasattr(file, "filename") or not hasattr(file, "read"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Upload field 'file' is required.",
        )

    return await test_ocr(file)
