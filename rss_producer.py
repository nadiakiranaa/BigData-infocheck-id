import time
import logging
from datetime import datetime
import feedparser
import requests
from kafka_helper import send_to_kafka, close_producer

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# List of Indonesian RSS Feeds for Economy, Politics, and Fact Checking
RSS_FEEDS = {
    # Berita Umum & Ekonomi
    "Detik Ekonomi": {"url": "https://finance.detik.com/rss", "category": "news"},
    "Antara Ekonomi": {"url": "https://www.antaranews.com/rss/ekonomi.xml", "category": "news"},
    "CNBC Indonesia": {"url": "https://www.cnbcindonesia.com/rss", "category": "news"},
    
    # Berita Politik
    "Detik News": {"url": "https://www.detik.com/news/rss", "category": "news"},
    "Antara Politik": {"url": "https://www.antaranews.com/rss/politik.xml", "category": "news"},
    "Tribun News": {"url": "https://www.tribunnews.com/rss", "category": "news"},
    
    # Cek Fakta / Hoaks (Ground Truth)
    "Liputan6 Cek Fakta": {"url": "https://feed.liputan6.com/rss/cek-fakta", "category": "fact-check"},
    "Turnbackhoax": {"url": "https://turnbackhoax.id/feed", "category": "fact-check"}
}

# In-memory cache to prevent duplicate ingestion of the same articles (keeps last 1000 URLs)
SENT_ARTICLES_CACHE = set()
MAX_CACHE_SIZE = 1000

def clean_cache():
    """
    Prevents cache from growing indefinitely by keeping only the most recent items.
    """
    global SENT_ARTICLES_CACHE
    if len(SENT_ARTICLES_CACHE) > MAX_CACHE_SIZE:
        # Convert to list, take the last 500 items, and turn back to set
        logger.info("Cleaning up sent articles cache...")
        SENT_ARTICLES_CACHE = set(list(SENT_ARTICLES_CACHE)[-500:])

def fetch_and_ingest():
    """
    Fetches articles from RSS feeds and sends new ones to Kafka.
    """
    logger.info("Starting polling RSS feeds...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    for source_name, feed_info in RSS_FEEDS.items():
        feed_url = feed_info["url"]
        category = feed_info["category"]
        try:
            logger.info(f"Parsing feed from: {source_name} (Category: {category})")
            
            # Fetch using requests to bypass python user-agent blocking by WAF
            response = requests.get(feed_url, headers=headers, timeout=15)
            if response.status_code != 200:
                logger.error(f"Failed to fetch feed {source_name}, HTTP status code: {response.status_code}")
                continue
                
            feed = feedparser.parse(response.content)
            
            # Check if parsing was successful
            if feed.bozo:
                logger.warning(f"Possible parsing issue with {source_name}, but continuing: {feed.bozo_exception}")

            new_articles_count = 0
            for entry in feed.entries:
                link = entry.get('link')
                if not link:
                    continue
                
                # Check for duplicates
                if link in SENT_ARTICLES_CACHE:
                    continue
                
                title = entry.get('title', '')
                description = entry.get('summary', entry.get('description', ''))
                
                # Parse publishing time, fall back to current time if unavailable
                published = entry.get('published', '')
                
                # Build normalized JSON payload
                payload = {
                    "source": source_name,
                    "category": category,
                    "title": title,
                    "link": link,
                    "description": description,
                    "published_at": published,
                    "ingested_at": datetime.utcnow().isoformat() + "Z"
                }
                
                # Send to Kafka topic 'rss-news'
                success = send_to_kafka('rss-news', payload)
                if success:
                    SENT_ARTICLES_CACHE.add(link)
                    new_articles_count += 1
            
            logger.info(f"Ingested {new_articles_count} new articles from {source_name}")
            
        except Exception as e:
            logger.error(f"Failed to fetch feed from {source_name}: {e}")
            
    clean_cache()

def main():
    logger.info("RSS Feed Kafka Ingestion service started.")
    try:
        while True:
            fetch_and_ingest()
            # Wait for 60 seconds before polling again
            logger.info("Sleeping for 60 seconds...")
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("Shutdown signal received. Stopping RSS producer...")
    finally:
        close_producer()

if __name__ == '__main__':
    main()
