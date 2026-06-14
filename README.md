# InfoCheck ID — Data Pipeline & Ingestion Kafka

Dokumentasi ini menjelaskan arsitektur, instalasi, dan cara menjalankan pipeline data streaming real-time menggunakan **Apache Kafka** untuk proyek **InfoCheck ID**. Pipeline ini berfungsi untuk menyalurkan data berita RSS feed dan pesan Telegram ke broker Kafka.

---

## 🛠️ Persyaratan Sistem (Prerequisites)
1. **Java Development Kit (JDK)**: JDK 11 atau versi lebih tinggi (sudah terinstal).
2. **Python 3.13+**: Untuk menjalankan producer script.
3. **Apache Kafka 3.7.0**: Berlokasi di direktori proyek `./kafka_2.13-3.7.0`.

---

## ⚙️ Langkah Setup & Menjalankan Kafka

### 1. Menjalankan Zookeeper
Buka terminal PowerShell baru, masuk ke direktori Kafka, lalu jalankan:
```powershell
cd "c:\Users\ASUS\Downloads\BIG DATA SMT 4\FP BIGDATA\kafka_2.13-3.7.0"
.\bin\windows\zookeeper-server-start.bat .\config\zookeeper.properties
```

### 2. Menjalankan Kafka Server
Buka terminal PowerShell baru lainnya, masuk ke direktori Kafka, lalu jalankan:
```powershell
cd "c:\Users\ASUS\Downloads\BIG DATA SMT 4\FP BIGDATA\kafka_2.13-3.7.0"
.\bin\windows\kafka-server-start.bat .\config\server.properties
```

### 3. Membuat Topic Baru (Sudah Dibuat)
Jika ingin membuat ulang atau memeriksa topic, gunakan perintah:
```powershell
# Topic untuk RSS News Feed
.\bin\windows\kafka-topics.bat --create --topic rss-news --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1

# Topic untuk Telegram Messages
.\bin\windows\kafka-topics.bat --create --topic telegram-messages --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
```

Untuk melihat daftar topic yang tersedia:
```powershell
.\bin\windows\kafka-topics.bat --list --bootstrap-server localhost:9092
```

---

## 🐍 Setup Python & Ingestion

### 1. Instalasi Library Pendukung
Buka terminal di root direktori proyek (`FP BIGDATA`), lalu jalankan:
```powershell
pip install -r requirements.txt
```

### 2. Menjalankan RSS Feed Ingestion (Producer)
Menjalankan skrip python daemon yang akan melakukan polling ke RSS Feed berita umum, ekonomi, politik, dan portal cek fakta/klarifikasi hoaks (Detik, Kompas, Antara, CNBC Indonesia, Bisnis.com, Liputan6, Tempo, Turnbackhoax) setiap 60 detik secara otomatis:
```powershell
python rss_producer.py
```

Skrip ini akan secara otomatis menyaring artikel duplikat, menentukan kategori artikel (`news` atau `fact-check`), dan mengirimkan data JSON terstandardisasi ke Kafka topic `rss-news`.

---

## 🔗 Panduan Integrasi Telegram Scraper (Untuk Anggota 2)

Anggota 2 yang membuat scraping Telegram menggunakan **Telethon** dapat mengalirkan datanya langsung ke Kafka broker menggunakan modul helper yang sudah disediakan (`kafka_helper.py`).

### Contoh Integrasi di Kode Scraper Telegram:
```python
from kafka_helper import send_to_kafka

# Saat menerima pesan baru dari grup Telegram public yang dipantau:
def handle_new_telegram_message(event):
    message_text = event.message.message
    sender_id = event.message.sender_id
    date = event.message.date.isoformat()
    
    # Bungkus data dalam schema JSON standar
    payload = {
        "channel_name": "Grup Ekonomi Rakyat",
        "sender_id": str(sender_id),
        "message": message_text,
        "sent_at": date,
        "ingested_at": datetime.utcnow().isoformat() + "Z"
    }
    
    # Kirim ke Kafka topic 'telegram-messages'
    send_to_kafka('telegram-messages', payload)
```

---

## 📊 Referensi Skema JSON Data Output (Untuk Anggota 3 & 5)

Data yang mengalir di Kafka Broker memiliki format JSON terstandardisasi berikut:

### Topic: `rss-news`
```json
{
  "source": "Detik Ekonomi",
  "category": "news",
  "title": "Klaim Bantuan Sosial 2026 Melalui Link Pendaftaran Palsu",
  "link": "https://www.detik.com/ekonomi/berita/...",
  "description": "Beredar pesan hoaks bantuan mengatasnamakan pemerintah...",
  "published_at": "Sun, 14 Jun 2026 09:12:00 GMT",
  "ingested_at": "2026-06-14T09:47:00Z"
}
```

### Topic: `telegram-messages`
```json
{
  "channel_name": "Grup Berita Rakyat",
  "sender_id": "123456789",
  "message": "Dapatkan bantuan presiden Prabowo sebesar 5 juta rupiah sekarang juga dengan klik link ini!",
  "sent_at": "2026-06-14T09:46:12Z",
  "ingested_at": "2026-06-14T09:47:00Z"
}
```
