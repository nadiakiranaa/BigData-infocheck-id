"""
api_client.py
Modul penghubung antara Bot Telegram (Anggota 4) dengan predict_api.py (Anggota 3).
Tugas:
  - Mengirim teks ke endpoint /predict
  - Mengirim gambar (screenshot) ke endpoint /predict-image
  - Mengambil isi artikel dari link berita (karena predict_api.py hanya menerima teks mentah)
"""

import os
import re
import base64
import logging

import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Ganti via environment variable kalau predict_api.py jalan di host/port lain
API_BASE_URL = os.environ.get("INFOCHECK_API_URL", "http://localhost:8000")
REQUEST_TIMEOUT = 30  # detik — IndoBERT + OCR Gemini butuh waktu lebih lama dari API biasa

URL_PATTERN = re.compile(r"^https?://\S+$")


def is_url(text: str) -> bool:
    """Cek apakah pesan user adalah sebuah link, bukan teks berita biasa."""
    return bool(URL_PATTERN.match(text.strip()))


def fetch_article_text(url: str, max_chars: int = 5000) -> str:
    """
    Ambil isi artikel dari sebuah link berita.
    predict_api.py hanya menerima teks mentah (field 'text'), jadi kalau
    user paste link, kita perlu ekstrak isi halamannya dulu di sisi bot.
    """
    try:
        resp = requests.get(
            url,
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0 (InfoCheckID-Bot)"},
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        paragraphs = soup.find_all("p")
        article_text = " ".join(p.get_text(strip=True) for p in paragraphs)

        if not article_text:
            article_text = soup.get_text(separator=" ", strip=True)

        return article_text[:max_chars].strip()
    except requests.exceptions.RequestException as e:
        logger.error(f"Gagal mengambil artikel dari {url}: {e}")
        return ""


def predict_text(text: str) -> dict:
    """Kirim teks/isi artikel ke endpoint POST /predict."""
    try:
        resp = requests.post(
            f"{API_BASE_URL}/predict",
            json={"text": text},
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Gagal memanggil /predict: {e}")
        return {"error": str(e)}


def predict_image(image_bytes: bytes) -> dict:
    """Kirim screenshot (bytes mentah dari Telegram) ke endpoint POST /predict-image."""
    try:
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")
        resp = requests.post(
            f"{API_BASE_URL}/predict-image",
            json={"image_base64": image_b64},
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Gagal memanggil /predict-image: {e}")
        return {"error": str(e)}
