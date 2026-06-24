from fastapi import UploadFile

from api_bridge.schemas.ocr import OcrTestResponse


SCAM_KEYWORDS = [
    "klik",
    "bit.ly",
    "rekening",
    "transfer",
    "hadiah",
    "bantuan",
    "verifikasi",
    "otp",
    "investasi",
]


async def simulate_ocr_and_classify(file: UploadFile) -> OcrTestResponse:
    content = await file.read()
    file_size_kb = round(len(content) / 1024, 2)

    extracted_text = (
        "Selamat! Anda terpilih menerima bantuan Rp5.000.000. "
        "Klik bit.ly/claim-bansos dan verifikasi rekening sebelum pukul 18.00."
    )
    lowered = extracted_text.lower()
    indicators = [keyword for keyword in SCAM_KEYWORDS if keyword in lowered]
    is_scam = len(indicators) >= 3

    return OcrTestResponse(
        filename=file.filename or "uploaded-image",
        content_type=file.content_type or "application/octet-stream",
        extracted_text=extracted_text,
        classification="Scam" if is_scam else "Review",
        confidence=96.4 if is_scam else 61.5,
        indicators=[
            *indicators,
            f"file_size_kb={file_size_kb}",
        ],
        recommendation=(
            "Tandai sebagai penipuan, jangan klik tautan, dan masukkan indikator ke Scam DB."
            if is_scam
            else "Perlu review manual sebelum dipublikasikan sebagai temuan."
        ),
    )
