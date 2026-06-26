"""
download_komdigi.py — Anggota 2 (Data Collection)
====================================================
Script untuk mendapatkan dataset hoaks terverifikasi resmi Komdigi.

ADA 2 CARA (pilih salah satu):

CARA 1 [DIREKOMENDASIKAN] — Download dari Kaggle (lebih lengkap, 15K+ artikel):
  1. Buka: https://kaggle.com/datasets/ireddragonicy/indonesian-hoax-news-dataset
  2. Download file 'indonesian_hoax_news.csv'
  3. Taruh di: dataset/komdigi/komdigi_hoaks_latest.csv
  4. Selesai! prepare_dataset.py akan otomatis membacanya.

CARA 2 [OTOMATIS] — Scraping dari turnbackhoax.id:
  python scripts/download_komdigi.py --scrape
  (Sama seperti scraper_kominfo.py yang sudah ada)

Hasil disimpan ke: dataset/komdigi/komdigi_hoaks_latest.csv
"""

import os
import json
import time
import logging
import requests
import pandas as pd
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# === KONFIGURASI ===
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "dataset", "komdigi")
OUTPUT_CSV = os.path.join(OUTPUT_DIR, "komdigi_hoaks_latest.csv")

API_BASE = "https://web.komdigi.go.id/api/v1/contents/category/berita-hoaks"
PAGE_SIZE = 12   # jumlah artikel per halaman (default API)
MAX_PAGES = 150  # maks 150 halaman ~ 1800 artikel terbaru (cukup untuk training)
MAX_WORKERS = 5  # paralel fetch untuk mempercepat

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://web.komdigi.go.id/",
    "Origin": "https://web.komdigi.go.id",
}


def clean_html(html_content: str) -> str:
    """Bersihkan HTML menjadi teks biasa menggunakan BeautifulSoup."""
    if not html_content:
        return ""
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        return soup.get_text(separator=" ", strip=True)
    except Exception:
        return str(html_content)


def fetch_page(page_num: int, session: requests.Session) -> list:
    """Fetch satu halaman dari API Komdigi."""
    params = {
        "page": page_num,
        "per_page": PAGE_SIZE,
        "sort": "published_at",
        "order": "desc"
    }
    try:
        resp = session.get(API_BASE, headers=HEADERS, params=params, timeout=20)
        if resp.status_code != 200:
            logger.warning(f"Halaman {page_num}: HTTP {resp.status_code}")
            return []

        data = resp.json()

        # Struktur API: {"data": {"data": [...], "total": N, ...}}
        items = data.get("data", {})
        if isinstance(items, dict):
            items = items.get("data", [])

        return items if isinstance(items, list) else []

    except Exception as e:
        logger.error(f"Gagal fetch halaman {page_num}: {e}")
        return []


def parse_article(item: dict) -> dict:
    """Ambil field yang relevan dari satu artikel."""
    # Bersihkan body HTML jika body_text tidak tersedia
    body_text = item.get("body_text", "")
    if not body_text:
        body_text = clean_html(item.get("body_html", "") or item.get("body", ""))

    return {
        "title": item.get("title", ""),
        "body_text": body_text,
        "published_at": item.get("published_at", ""),
        "category": item.get("category", "Klarifikasi Hoaks"),
        "tags": str(item.get("tags", "")),
        "topics": str(item.get("topics", "")),
        "url": item.get("url", ""),
        "label": "Hoaks",    # semua konten komdigi = hoaks terverifikasi pemerintah
        "source": "komdigi.go.id"
    }


def download_komdigi(max_pages: int = MAX_PAGES) -> pd.DataFrame:
    """
    Download semua artikel hoaks dari API Komdigi secara paralel.
    Mengembalikan DataFrame.
    """
    logger.info(f"Mulai download dari Komdigi API (maks {max_pages} halaman, ~{max_pages * PAGE_SIZE} artikel)...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    session = requests.Session()
    all_articles = []

    # Cek total halaman dari halaman pertama
    first_page = fetch_page(1, session)
    if not first_page:
        logger.error("Gagal fetch halaman pertama. Cek koneksi internet.")
        return pd.DataFrame()

    all_articles.extend([parse_article(a) for a in first_page])
    logger.info(f"Halaman 1: {len(first_page)} artikel")

    # Fetch paralel halaman 2 sampai max_pages
    pages_to_fetch = list(range(2, max_pages + 1))
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_page = {executor.submit(fetch_page, p, session): p for p in pages_to_fetch}
        for future in as_completed(future_to_page):
            page_num = future_to_page[future]
            try:
                items = future.result()
                if not items:
                    # Halaman kosong = sudah habis
                    continue
                all_articles.extend([parse_article(a) for a in items])
                if page_num % 10 == 0:
                    logger.info(f"Progress: halaman {page_num} selesai, total {len(all_articles)} artikel")
            except Exception as e:
                logger.error(f"Error halaman {page_num}: {e}")
            time.sleep(0.3)  # jeda kecil antar batch

    logger.info(f"Download selesai. Total artikel terkumpul: {len(all_articles)}")
    df = pd.DataFrame(all_articles)

    # Bersihkan: hapus duplikat & baris tanpa teks
    df = df.drop_duplicates(subset=["title"])
    df = df[df["body_text"].str.len() > 50]  # minimal 50 karakter
    df = df.dropna(subset=["body_text"])

    return df


def main():
    print("=" * 60)
    print("InfoCheck ID — Download Dataset Hoaks Komdigi (Anggota 2)")
    print("=" * 60)

    # Cek apakah sudah ada file sebelumnya
    if os.path.exists(OUTPUT_CSV):
        df_existing = pd.read_csv(OUTPUT_CSV)
        print(f"\n[INFO] File lama ditemukan: {len(df_existing)} artikel ({OUTPUT_CSV})")
        print("[INFO] Mendownload versi terbaru untuk meng-update...\n")

    df = download_komdigi(max_pages=MAX_PAGES)

    if df.empty:
        print("\n[ERROR] Tidak ada data yang berhasil didownload.")
        print("Kemungkinan penyebab:")
        print("  1. Tidak ada koneksi internet")
        print("  2. API Komdigi sedang down")
        print("  3. Struktur API berubah")
        return

    # Simpan ke CSV
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")

    print(f"\n{'='*60}")
    print(f"SELESAI! Ringkasan:")
    print(f"  Total artikel Hoaks : {len(df)}")
    print(f"  Disimpan ke        : {OUTPUT_CSV}")
    print(f"  Kolom tersedia     : {list(df.columns)}")
    print(f"\nDistribusi label:")
    print(df["label"].value_counts())
    print(f"\nContoh data:")
    print(df[["title", "body_text"]].head(3).to_string())
    print(f"\nSelanjutnya jalankan: python scripts/prepare_dataset.py")
    print(f"untuk menggabungkan dataset ini ke dataset training.")

    # Simpan juga metadata download
    meta = {
        "downloaded_at": datetime.now().isoformat(),
        "total_articles": len(df),
        "source": "web.komdigi.go.id",
        "label": "Hoaks"
    }
    meta_path = os.path.join(OUTPUT_DIR, "komdigi_meta.json")
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)
    logger.info(f"Metadata disimpan ke {meta_path}")


if __name__ == "__main__":
    main()
