# InfoCheck ID — Data Pipeline & Ingestion Kafka

Dokumentasi ini menjelaskan arsitektur, instalasi, dan cara menjalankan pipeline data streaming real-time menggunakan **Apache Kafka** untuk proyek **InfoCheck ID**.

---

## 🛠️ Persyaratan Sistem (Prerequisites)

1. **Java Development Kit (JDK)**: JDK 21 — download dari https://www.oracle.com/java/technologies/downloads/#jdk21-windows
2. **Python 3.13+**: Untuk menjalankan producer script
3. **Apache Kafka 3.7.0**: Download dari https://kafka.apache.org/downloads → Scala 2.13, extract ke `C:\kafka_2.13-3.7.0`

---

## ⚙️ Langkah Setup & Menjalankan Kafka

> ⚠️ **Penting**: Setiap kali membuka terminal PowerShell baru, wajib set Java PATH dulu:
> ```powershell
> $env:JAVA_HOME = "C:\Program Files\Java\jdk-21.0.11"
> $env:Path += ";$env:JAVA_HOME\bin"
> ```

### 1. Menjalankan Zookeeper (Terminal 1)

```powershell
$env:JAVA_HOME = "C:\Program Files\Java\jdk-21.0.11"
$env:Path += ";$env:JAVA_HOME\bin"
cd C:\kafka_2.13-3.7.0
.\bin\windows\zookeeper-server-start.bat .\config\zookeeper.properties
```

Tunggu hingga muncul: `binding to port 0.0.0.0/0.0.0.0:2181`

### 2. Menjalankan Kafka Server (Terminal 2)

```powershell
$env:JAVA_HOME = "C:\Program Files\Java\jdk-21.0.11"
$env:Path += ";$env:JAVA_HOME\bin"
$env:KAFKA_HEAP_OPTS = "-Xmx512M -Xms256M"
cd C:\kafka_2.13-3.7.0
.\bin\windows\kafka-server-start.bat .\config\server.properties
```

Tunggu hingga muncul: `[KafkaServer id=0] started`

### 3. Topic yang Digunakan

```powershell
# Cek topic yang sudah ada
.\bin\windows\kafka-topics.bat --list --bootstrap-server localhost:9092

# Jika perlu buat ulang:
.\bin\windows\kafka-topics.bat --create --topic rss-news --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
.\bin\windows\kafka-topics.bat --create --topic telegram-messages --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
```

---

## 🐍 Setup Python & Ingestion

### Instalasi Library

```powershell
pip install -r requirements.txt
```

`requirements.txt`:
```
kafka-python-ng==2.2.3
feedparser==6.0.11
requests==2.32.3
telethon==1.36.0
beautifulsoup4
```

### Menjalankan RSS Feed Producer — Anggota 1

```powershell
python rss_producer.py
```

Polling otomatis setiap 60 detik ke RSS feed: Detik, Kompas, Antara, CNBC Indonesia, Liputan6 CekFakta, Turnbackhoax. Data masuk ke topic `rss-news`.

### Menjalankan Telegram Producer — Anggota 2

```powershell
python telegram_producer.py
```

Pertama kali dijalankan akan minta login Telegram — masukkan nomor HP format `+62xxx` lalu kode OTP dari aplikasi Telegram. Session tersimpan otomatis di `infocheckid_session.session`, login berikutnya langsung jalan tanpa input ulang.

Channel yang dipantau: Turn Back Hoax, CekFakta, Kompas.com, DetikNews, CNBI Indonesia. Data masuk ke topic `telegram-messages`.

---

## 🔗 Panduan Integrasi Kafka (Untuk Semua Anggota)

Gunakan `kafka_helper.py` untuk kirim data ke Kafka dari script manapun:

```python
from kafka_helper import send_to_kafka

payload = {
    "channel_name": "Nama Channel",
    "message": "isi pesan",
    "sent_at": "2026-06-14T09:46:12Z",
    "ingested_at": "2026-06-14T09:47:00Z"
}

send_to_kafka('telegram-messages', payload)
```

---

## 📊 Skema JSON Data di Kafka

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
  "channel_name": "Turn Back Hoax",
  "sender_id": "123456789",
  "message": "Dapatkan bantuan presiden Prabowo sebesar 5 juta rupiah sekarang juga dengan klik link ini!",
  "sent_at": "2026-06-14T09:46:12Z",
  "ingested_at": "2026-06-14T09:47:00Z"
}
```

---

## 📦 Panduan Dataset — Anggota 3 (dari Anggota 2)

Dataset sudah tersedia di folder `dataset/` dalam repository.

### Struktur Folder

```
dataset/
├── kaggle/
│   └── Cleaned/
│       ├── dataset_turnbackhoax_10_cleaned.xlsx  ← HOAKS (~10.000 artikel)
│       ├── dataset_cnn_10k_cleaned.xlsx           ← VALID (~10.000 artikel)
│       ├── dataset_kompas_4k_cleaned.xlsx         ← VALID (~4.000 artikel)
│       └── dataset_tempo_6k_cleaned.xlsx          ← VALID (~6.000 artikel)
└── komdigi/
    └── komdigi_hoaks.csv                          ← HOAKS terbaru 2026 (~4.142 artikel)
```

### Mapping Kolom

| File | Kolom Teks | Kolom Label | Nilai |
|---|---|---|---|
| dataset_turnbackhoax_10_cleaned.xlsx | `Clean Narasi` | `hoax` | 1 = hoaks |
| dataset_cnn_10k_cleaned.xlsx | `text_new` | `hoax` | 0 = valid |
| dataset_kompas_4k_cleaned.xlsx | `text_new` | `hoax` | 0 = valid |
| dataset_tempo_6k_cleaned.xlsx | `text_new` | `hoax` | 0 = valid |
| komdigi_hoaks.csv | `body_text` | tambah manual | 1 = hoaks |

### Contoh Load Dataset di Python

```python
import pandas as pd

# Hoaks dari Turnbackhoax
df_hoax = pd.read_excel('dataset/kaggle/Cleaned/dataset_turnbackhoax_10_cleaned.xlsx')
df_hoax = df_hoax[['Clean Narasi', 'hoax']].rename(columns={'Clean Narasi': 'text'})

# Valid dari CNN
df_cnn = pd.read_excel('dataset/kaggle/Cleaned/dataset_cnn_10k_cleaned.xlsx')
df_cnn = df_cnn[['text_new', 'hoax']].rename(columns={'text_new': 'text'})

# Valid dari Kompas
df_kompas = pd.read_excel('dataset/kaggle/Cleaned/dataset_kompas_4k_cleaned.xlsx')
df_kompas = df_kompas[['text_new', 'hoax']].rename(columns={'text_new': 'text'})

# Valid dari Tempo
df_tempo = pd.read_excel('dataset/kaggle/Cleaned/dataset_tempo_6k_cleaned.xlsx')
df_tempo = df_tempo[['text_new', 'hoax']].rename(columns={'text_new': 'text'})

# Hoaks terbaru dari Komdigi 2026
df_komdigi = pd.read_csv('dataset/komdigi/komdigi_hoaks.csv')
df_komdigi = df_komdigi[['body_text']].rename(columns={'body_text': 'text'})
df_komdigi['hoax'] = 1

# Gabungkan semua
df_all = pd.concat([df_hoax, df_cnn, df_kompas, df_tempo, df_komdigi], ignore_index=True)
df_all = df_all.dropna(subset=['text'])

print(f"Total dataset: {len(df_all)} baris")
print(df_all['hoax'].value_counts())
```

### Distribusi Dataset

| Kategori | Jumlah | Sumber |
|---|---|---|
| Hoaks | ~14.142 | Turnbackhoax + Komdigi |
| Valid | ~20.000 | CNN + Kompas + Tempo |
| **Total** | **~34.142** | |