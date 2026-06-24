"""
formatter.py
Mengubah response JSON dari predict_api.py menjadi pesan Telegram yang mudah dibaca.
Sengaja TIDAK memakai Markdown/HTML Telegram (asterisk, underscore, dll) karena
teks artikel/OCR sering mengandung karakter yang bisa merusak parsing Telegram.
"""

LABEL_EMOJI = {
    "Valid": "✅",
    "Hoaks": "⚠️",
    "Penipuan": "🚨",
    "Netral": "ℹ️",
}


def _error_message(result: dict) -> str:
    return (
        "❌ Gagal menghubungi server InfoCheck ID.\n"
        f"Detail: {result.get('error')}\n\n"
        "Pastikan predict_api.py sedang berjalan dan dapat diakses."
    )


def format_text_result(result: dict) -> str:
    if "error" in result:
        return _error_message(result)

    label = result.get("label", "Tidak diketahui")
    score = result.get("score", 0)
    emoji = LABEL_EMOJI.get(label, "❔")
    all_scores = result.get("all_scores", {})
    entities = result.get("scam_entities", {})
    recommendation = result.get("recommendation", "")

    lines = [
        f"{emoji} HASIL DETEKSI: {label.upper()}",
        f"Skor keyakinan: {score}%",
        "",
        "Rincian skor tiap kelas:",
    ]
    for lbl, val in all_scores.items():
        lines.append(f"  - {lbl}: {val}%")

    if entities:
        lines.append("")
        lines.append("Entitas mencurigakan terdeteksi:")
        if entities.get("nomor_hp"):
            lines.append(f"  Nomor HP: {', '.join(entities['nomor_hp'])}")
        if entities.get("rekening"):
            lines.append(f"  Nomor Rekening: {', '.join(entities['rekening'])}")
        if entities.get("links"):
            lines.append(f"  Link: {', '.join(entities['links'])}")

    lines.append("")
    lines.append(f"Alasan / Rekomendasi:\n{recommendation}")

    return "\n".join(lines)


def format_image_result(result: dict) -> str:
    if "error" in result:
        return _error_message(result)

    label = result.get("label", "Tidak diketahui")
    score = result.get("score", 0)
    emoji = LABEL_EMOJI.get(label, "❔")
    extracted_text = (result.get("extracted_text") or "").strip()
    ocr_reason = result.get("ocr_reason", "")
    recommendation = result.get("recommendation", "")

    lines = [
        f"{emoji} HASIL DETEKSI SCREENSHOT: {label.upper()}",
        f"Skor keyakinan: {score}%",
        "",
    ]

    if extracted_text:
        preview = extracted_text[:300] + ("..." if len(extracted_text) > 300 else "")
        lines.append(f"Teks terbaca dari gambar (OCR):\n\"{preview}\"")
        lines.append("")

    if ocr_reason:
        lines.append(f"Alasan deteksi (Gemini OCR):\n{ocr_reason}")
        lines.append("")

    lines.append(f"Rekomendasi:\n{recommendation}")

    return "\n".join(lines)
