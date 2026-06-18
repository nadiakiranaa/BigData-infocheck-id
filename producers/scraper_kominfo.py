# scraper_kominfo.py
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from bs4 import BeautifulSoup
import json
import time
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_URL = "https://turnbackhoax.id"
OUTPUT_FILE = "dataset/turnbackhoax_data.json"

def scrape_page(page_num):
    url = f"{BASE_URL}/page/{page_num}/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            logger.warning(f"Page {page_num} returned status {response.status_code}")
            return []

        soup = BeautifulSoup(response.content, 'html.parser')
        articles = []

        # Ambil semua artikel di halaman
        posts = soup.find_all('article')
        for post in posts:
            try:
                title_tag = post.find('h2') or post.find('h3')
                title = title_tag.get_text(strip=True) if title_tag else ''

                link_tag = title_tag.find('a') if title_tag else None
                link = link_tag['href'] if link_tag else ''

                date_tag = post.find('time')
                date = date_tag['datetime'] if date_tag else ''

                excerpt_tag = post.find('p')
                excerpt = excerpt_tag.get_text(strip=True) if excerpt_tag else ''

                if title:
                    articles.append({
                        "title": title,
                        "link": link,
                        "date": date,
                        "excerpt": excerpt,
                        "label": "hoax",  # semua konten di turnbackhoax = hoaks terverifikasi
                        "source": "turnbackhoax.id",
                        "scraped_at": datetime.utcnow().isoformat() + "Z"
                    })
            except Exception as e:
                logger.error(f"Error parsing article: {e}")
                continue

        logger.info(f"Page {page_num}: {len(articles)} artikel ditemukan")
        return articles

    except Exception as e:
        logger.error(f"Gagal fetch page {page_num}: {e}")
        return []


def scrape_article_content(url):
    """Ambil full content artikel hoaks (opsional, untuk enrichment)"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.content, 'html.parser')

        content_div = soup.find('div', class_='entry-content') or soup.find('div', class_='post-content')
        if content_div:
            return content_div.get_text(separator=' ', strip=True)
        return ''
    except:
        return ''


def main():
    import os
    os.makedirs('dataset', exist_ok=True)

    all_articles = []
    max_pages = 30  # ~30 halaman = sekitar 300-400 artikel hoaks

    logger.info(f"Mulai scraping turnbackhoax.id ({max_pages} halaman)...")

    for page in range(1, max_pages + 1):
        articles = scrape_page(page)
        if not articles:
            logger.info(f"Tidak ada artikel di page {page}, berhenti.")
            break

        all_articles.extend(articles)
        time.sleep(2)  # jeda 2 detik antar halaman, hindari ban

    logger.info(f"Total artikel terkumpul: {len(all_articles)}")

    # Simpan ke JSON
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_articles, f, ensure_ascii=False, indent=2)

    logger.info(f"Data disimpan ke {OUTPUT_FILE}")

    # Simpan juga ke CSV untuk Anggota 3
    import csv
    csv_file = "dataset/turnbackhoax_data.csv"
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["title", "excerpt", "label", "source", "date", "link", "scraped_at"])
        writer.writeheader()
        writer.writerows(all_articles)

    logger.info(f"CSV disimpan ke {csv_file}")
    logger.info("Scraping selesai!")


if __name__ == '__main__':
    main()