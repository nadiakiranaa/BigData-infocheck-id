import json
import logging
import threading
import uuid
from kafka import KafkaConsumer
from api_bridge.data.db_manager import get_db

logger = logging.getLogger(__name__)

# Kafka Config
KAFKA_BOOTSTRAP_SERVERS = ['localhost:9092']
KAFKA_TOPIC = 'analyzed-news'

_consumer_thread = None
_stop_event = threading.Event()

def consume_messages():
    """Background loop to consume Kafka messages and insert to SQLite."""
    try:
        consumer = KafkaConsumer(
            KAFKA_TOPIC,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            auto_offset_reset='latest',
            enable_auto_commit=True,
            api_version=(3, 3, 1),
            value_deserializer=lambda x: json.loads(x.decode('utf-8')),
            consumer_timeout_ms=1000
        )
        logger.info(f"API Bridge Kafka Consumer terhubung ke topik: {KAFKA_TOPIC}")
    except Exception as e:
        logger.warning(f"Gagal koneksi ke Kafka (mungkin Kafka mati). Data feed akan kosong. Error: {e}")
        return

    conn = get_db()

    while not _stop_event.is_set():
        try:
            for message in consumer:
                if _stop_event.is_set():
                    break
                
                payload = message.value
                analysis = payload.get("analysis", {})
                original = payload.get("original_data", {})
                
                # Extract fields
                # Default ID if not present
                msg_id = original.get("id") or original.get("tweet_id") or str(uuid.uuid4())
                timestamp = original.get("timestamp") or original.get("tweeted_at") or original.get("date") or original.get("pubDate", "")
                source_topic = payload.get("source_topic", "")
                
                # Menentukan source_type & source name
                source_type = "Telegram" if "telegram" in source_topic.lower() else ("Twitter" if "twitter" in source_topic.lower() else "RSS")
                source = original.get("source", source_topic)
                
                text_snippet = original.get("message") or original.get("description") or original.get("text") or original.get("title", "")
                # Potong jika terlalu panjang
                if len(text_snippet) > 150:
                    text_snippet = text_snippet[:147] + "..."
                    
                url = original.get("link") or original.get("url") or ""
                    
                label = analysis.get("label", "Valid")
                confidence = analysis.get("score", 0.0)
                topic = analysis.get("category") or original.get("category") or "umum"

                cursor = conn.cursor()
                try:
                    cursor.execute('''
                        INSERT OR IGNORE INTO live_feed 
                        (id, timestamp, source, source_type, text_snippet, label, confidence, topic, url)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (msg_id, timestamp, source, source_type, text_snippet, label, confidence, topic, url))
                    conn.commit()
                except Exception as e:
                    logger.error(f"DB Insert error: {e}")
                    
        except Exception as e:
            logger.error(f"Kafka consumer error: {e}")
            break

    consumer.close()
    logger.info("API Bridge Kafka Consumer berhenti.")


def start_kafka_consumer():
    """Start the Kafka consumer in a background thread."""
    global _consumer_thread
    if _consumer_thread is None or not _consumer_thread.is_alive():
        _stop_event.clear()
        _consumer_thread = threading.Thread(target=consume_messages, daemon=True)
        _consumer_thread.start()
        logger.info("Background thread untuk Kafka Consumer dimulai.")

def stop_kafka_consumer():
    """Stop the Kafka consumer."""
    global _consumer_thread
    if _consumer_thread is not None and _consumer_thread.is_alive():
        logger.info("Menghentikan Kafka Consumer...")
        _stop_event.set()
        _consumer_thread.join(timeout=2.0)
