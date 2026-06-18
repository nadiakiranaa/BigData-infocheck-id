import json
import logging
from kafka import KafkaProducer

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Kafka configuration
BOOTSTRAP_SERVERS = ['localhost:9092']

_producer = None

def get_kafka_producer():
    """
    Returns a singleton KafkaProducer instance.
    Automatically serializes JSON objects to UTF-8 bytes.
    """
    global _producer
    if _producer is None:
        try:
            _producer = KafkaProducer(
                bootstrap_servers=BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                retries=5,
                acks='all'
            )
            logger.info("Kafka Producer successfully initialized.")
        except Exception as e:
            logger.error(f"Failed to initialize Kafka Producer: {e}")
            raise e
    return _producer

def send_to_kafka(topic, data):
    """
    Sends data (must be a JSON-serializable dict) to the specified Kafka topic.
    """
    try:
        producer = get_kafka_producer()
        future = producer.send(topic, value=data)
        
        # Block for synchronous sending (helps ensure message delivery in simple ingestion scripts)
        record_metadata = future.get(timeout=10)
        logger.info(f"Message sent successfully to topic '{record_metadata.topic}' (partition: {record_metadata.partition}, offset: {record_metadata.offset})")
        return True
    except Exception as e:
        logger.error(f"Error sending message to Kafka topic '{topic}': {e}")
        return False

def close_producer():
    """
    Flushes and closes the producer connection.
    """
    global _producer
    if _producer is not None:
        try:
            _producer.flush()
            _producer.close()
            logger.info("Kafka Producer connection closed.")
        except Exception as e:
            logger.error(f"Error closing Kafka Producer: {e}")
