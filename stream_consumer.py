# stream_consumer.py
# InfoCheck ID — Big Data Kafka Stream Consumer (Anggota 4)
# Mengonsumsi data dari topic Kafka, memanggil API NLP (Anggota 3), 
# dan mengirimkan hasil analisis kembali ke topic baru 'analyzed-news'.

import json
import logging
import requests
from kafka import KafkaConsumer, KafkaProducer

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Konfigurasi Kafka
BOOTSTRAP_SERVERS = ['localhost:9092']
INPUT_TOPICS = ['rss-news', 'telegram-messages']
OUTPUT_TOPIC = 'analyzed-news'

# Konfigurasi API NLP (Anggota 3)
API_URL = "http://localhost:8000/predict"

def main():
    logger.info("Memulai Kafka Stream Consumer...")
    
    # 1. Inisialisasi Consumer untuk membaca data streaming dari produsen
    try:
        consumer = KafkaConsumer(
            *INPUT_TOPICS,
            bootstrap_servers=BOOTSTRAP_SERVERS,
            auto_offset_reset='latest',
            enable_auto_commit=True,
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )
        logger.info(f"Consumer terhubung ke topik input: {INPUT_TOPICS}")
    except Exception as e:
        logger.error(f"Gagal menginisialisasi Kafka Consumer: {e}")
        return

    # 2. Inisialisasi Producer untuk mengirimkan hasil analisis ke topic output
    try:
        producer = KafkaProducer(
            bootstrap_servers=BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        logger.info(f"Producer sukses terhubung untuk mengirim ke topik: '{OUTPUT_TOPIC}'")
    except Exception as e:
        logger.error(f"Gagal menginisialisasi Kafka Producer: {e}")
        return

    logger.info("Menunggu pesan masuk dari Kafka stream...")
    
    # 3. Loop utama pembacaan stream
    for message in consumer:
        try:
            payload = message.value
            logger.info(f"Menerima pesan dari topic '{message.topic}'")
            
            # Tentukan kolom teks berdasarkan sumber data (RSS vs Telegram)
            text_to_analyze = ""
            if 'message' in payload:
                text_to_analyze = payload['message']  # Dari Telegram
            elif 'description' in payload:
                text_to_analyze = payload['description']  # Dari RSS
            elif 'title' in payload:
                text_to_analyze = payload['title']  # Fallback RSS title
                
            if not text_to_analyze.strip():
                logger.warning("Pesan kosong, melewati analisis.")
                continue
                
            # 4. Kirim teks ke API Deteksi Hoaks (Anggota 3)
            logger.info(f"Mengirim teks untuk dianalisis: '{text_to_analyze[:60]}...'")
            response = requests.post(API_URL, json={"text": text_to_analyze}, timeout=15)
            
            if response.status_code == 200:
                nlp_results = response.json()
                logger.info(f"Analisis Sukses: Label={nlp_results['label']} (Skor: {nlp_results['score']}%)")
                
                # 5. Gabungkan data asli dari produsen dengan hasil analisis NLP
                enriched_payload = {
                    "original_data": payload,
                    "source_topic": message.topic,
                    "analysis": {
                        "score": nlp_results['score'],
                        "label": nlp_results['label'],
                        "reason": nlp_results['reason'],
                        "category": nlp_results['category'],
                        "sentiment": nlp_results['sentiment'],
                        "is_sensational": nlp_results['is_sensational'],
                        "ai_generated_flag": nlp_results['ai_generated_flag'],
                        "processing_time_ms": nlp_results['processing_time_ms'],
                        "recommendation": nlp_results['recommendation']
                    }
                }
                
                # 6. Kirim data hasil analisis kembali ke Kafka (untuk divisualisasikan Anggota 5)
                producer.send(OUTPUT_TOPIC, value=enriched_payload)
                producer.flush()
                logger.info(f"Berhasil mempublikasikan data teranalisis ke topic '{OUTPUT_TOPIC}'")
            else:
                logger.warning(f"Gagal memanggil API NLP: Status {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error memproses pesan streaming: {e}")
            continue

if __name__ == '__main__':
    main()
