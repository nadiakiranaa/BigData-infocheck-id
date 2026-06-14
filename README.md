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


# Dokumentasi Anggota 3 — Modul Klasifikasi NLP & API Deteksi Hoaks InfoCheck ID

Sistem deteksi hoaks berita ekonomi dan politik Indonesia berbasis IndoBERT v2 yang dipadukan dengan Komdigi Similarity Index dan sistem post-processing cerdas (kalibrasi confidence, klasifikasi kategori, status keaslian teks/deepfake, dan pendeteksi gaya berita resmi).

---

## 1. Persyaratan Sistem dan Instalasi

### Library yang Digunakan
Dependencies untuk modul NLP dan API tercantum di requirements.txt:
* **FastAPI** & **Uvicorn**: Framework web performa tinggi untuk membangun dan menjalankan endpoint API.
* **Pydantic**: Validasi tipe data request dan response.
* **Transformers** & **Torch**: Framework deep learning untuk memuat dan menjalankan model IndoBERT.
* **Pandas** & **Openpyxl**: Membaca dataset format Excel/CSV untuk pelatihan dan similarity index.
* **Scikit-learn**: Vektorisasi TF-IDF dan kalkulasi Cosine Similarity untuk baseline model dan pencarian kemiripan hoaks.
* **BeautifulSoup4** & **Requests**: Mengunduh dan mem-parsing halaman web secara otomatis untuk sinkronisasi database hoaks.

### Cara Setup Environment dan Instalasi
Jalankan perintah berikut di terminal Anda untuk menyiapkan environment dan mengunduh library yang dibutuhkan:

```bash
# 1. Masuk ke folder proyek
cd /Users/macbookprosilver/Downloads/BigData-infocheck-id

# 2. Aktifkan virtual environment yang sudah ada
source venv/bin/activate

# 3. Install semua dependencies
pip install -r requirements.txt
```

---

## 2. Arsitektur Deteksi Hoaks

Sistem menggunakan pendekatan hybrid yang menggabungkan kecerdasan Deep Learning (pemahaman semantik konteks) dengan Database Lookup (verifikasi hoaks yang sudah diklarifikasi pemerintah):

* **Model Utama: IndoBERT v2 (Fine-Tuned)**: Model klasifikasi utama dibangun menggunakan IndoBERT dengan optimalisasi berupa Class Weights (mengatasi class imbalance 2:1) dan Label Smoothing (0.1) (mencegah model overconfident pada data ambigu).
* **Modul Alasan: Similarity Komdigi Index**: Database lookup berisi 4.092 artikel hoaks terverifikasi Kominfo/Komdigi. Konteks input dicari kemiripannya menggunakan TF-IDF Vectorizer + Cosine Similarity.
* **Adaptive Threshold**: Mengubah batas penentuan label berdasarkan karakteristik teks. Teks dengan struktur data statistik resmi (is_formal_news) membutuhkan skor keyakinan model yang lebih tinggi (85%+) untuk dicap sebagai Hoaks guna menghindari false positive.
* **Kategori Isu (Multi-label)**: Menentukan topik teks berita secara otomatis (ekonomi, politik, bansos, kesehatan, umum) melalui pencocokan kata kunci.
* **Deepfake / AI-Generated Flag**: Detektor pola penyebaran viral (heuristik teks viral seperti kata "sebarkan", "klik link ini", tanda baca berulang !!!, dan penggunaan HURUF KAPITAL berlebihan).
* **Confidence Calibration**: Disclaimer peringatan otomatis pada output jika skor probabilitas bernilai ambigu (berkisar antara 40% - 60% atau label "Mencurigakan").
* **Model Explainability (LIME-light Word Importance)**: Pemetaan visual kata kunci kontributor skor hoaks. Sistem secara cerdas melakukan perturbasi teks (menghapus satu per satu kata dari teks input) dan memprediksi pengaruhnya secara paralel (batch forward pass) untuk menghitung kontribusi matematis tiap kata terhadap skor hoaks akhir tanpa menambah latensi.
* **Scraper Sync (Auto-update Database)**: Mekanisme sinkronisasi database secara real-time yang mengunduh klarifikasi hoaks terbaru dari turnbackhoax.id, memperbarui dataset offline, dan membangun kembali indeks similarity TF-IDF dalam memori secara dinamis tanpa perlu merestart server.
* **Stats Logging**: Setiap request prediksi dicatat otomatis ke log file predictions_log.jsonl untuk diolah menjadi statistik performa.
* **Active Learning (Automated Retraining Loop)**: Endpoint khusus bagi user untuk melaporkan kesalahan prediksi. Log disimpan di feedback_log.jsonl. Ketika jumlah feedback mencapai threshold (5 data untuk simulasi demo), sistem secara otomatis memicu skrip `active_learning.py` secara background untuk melatih ulang model baseline secara real-time, mengarsipkannya, dan menyuntikkan data baru ke pool dataset (`dataset/new_training_pool.csv`) untuk retraining IndoBERT di masa depan.
* **Analisis Sentimen (NLP)**: Menentukan sentimen teks (Negatif, Positif, atau Netral) secara leksikal.
* **Deteksi Sensasionalisme (NLP)**: Menandai teks yang memicu kepanikan emosional (is_sensational: true/false) berdasarkan kata kunci sensasional atau penulisan provokatif.

---

## 3. Hasil Evaluasi dan Performa Model

### 3.1 Perbandingan Performa Model (Tabel Evaluasi)

| Model | Accuracy (Test Set) | F1-Score (Test Set) | Karakteristik Utama | Status |
| :--- | :---: | :---: | :--- | :---: |
| **Baseline** (TF-IDF + Logistic Regression) | 97.84% | 96.81% | Ringan, cepat, sensitif terhadap keyword | Deprecated |
| **IndoBERT v1** (Tanpa Kalibrasi) | 99.30% | 99.12% | Akurasi tinggi di test-set, namun overfit parah di luar domain (prediksi Hoaks >97% untuk teks valid umum) | Deprecated |
| **IndoBERT v2** (Class Weights + Label Smoothing) | **99.56%** | **99.56%** | Sangat akurat, terkalibrasi dengan baik, dan toleran terhadap berita valid/formal | **Aktif & Siap Demo** |

### 3.2 Detail Evaluasi IndoBERT v2 (Test Set Hasil Training Aktual)

Berikut adalah metrik performa final dari model IndoBERT v2 yang diuji menggunakan Test Set (data tidak terlihat) dengan total 3.151 baris data:

```
              precision    recall  f1-score   support

       Valid     0.9952    0.9981    0.9967      2095
       Hoaks     0.9962    0.9905    0.9934      1056

    accuracy                         0.9956      3151
   macro avg     0.9957    0.9943    0.9950      3151
weighted avg     0.9956    0.9956    0.9956      3151
```

**Confusion Matrix:**
```
[[2091    4]
 [  10 1046]]
```

Analisis hasil:
* **True Positive (Valid)**: 2091 data valid diklasifikasikan dengan benar sebagai Valid.
* **True Negative (Hoaks)**: 1046 hoaks diklasifikasikan dengan benar sebagai Hoaks.
* **False Positive**: Hanya 4 data valid yang salah diklasifikasikan sebagai Hoaks (sangat rendah, membuktikan threshold adaptif formal news bekerja dengan sangat baik).
* **False Negative**: Hanya 10 data hoaks yang salah diklasifikasikan sebagai Valid.

---

## 4. Cara Menjalankan API Server

Jalankan perintah berikut untuk memulai server FastAPI:

```bash
# 1. Rebuild Komdigi Similarity Index (pastikan index diperbarui menggunakan NumPy 1.x)
python komdigi_similarity.py

# 2. Jalankan Server FastAPI menggunakan Uvicorn
uvicorn predict_api:app --reload --port 8000
```
Jika sukses, terminal akan menampilkan pesan:
`INFO: Uvicorn running on http://127.0.0.1:8000`

---

## 5. Detail Endpoint API (Dokumentasi Swagger)

Buka dokumentasi interaktif API di browser Anda: **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**

### 1️⃣ POST `/predict`
Endpoint utama untuk menganalisis teks berita.
* **Request Body (JSON):**
  ```json
  {
    "text": "Dapatkan bantuan presiden Prabowo sebesar 5 juta rupiah sekarang juga dengan klik link ini! Sebarkan sebelum dihapus!!!"
  }
  ```
* **Response Body (JSON):**
  ```json
  {
    "score": 97.61,
    "label": "Hoaks",
    "reason": "Model mendeteksi pola bahasa yang mirip konten hoaks (skor: 97.6%). Tidak ditemukan kecocokan persis dengan database hoaks Komdigi.",
    "category": [
      "politik",
      "bansos"
    ],
    "ai_generated_flag": true,
    "confidence_note": null,
    "is_formal_news": false,
    "processing_time_ms": 34.52,
    "recommendation": "PERINGATAN: Konten terindikasi kuat sebagai HOAKS. Jangan menyebarkan berita ini untuk menghentikan rantai disinformasi. Laporkan ke portal Aduan Konten Kominfo.",
    "sentiment": "Positif",
    "is_sensational": true,
    "model_version": "IndoBERT-v2-calibrated",
    "word_importance": [
      { "word": "Dapatkan", "importance": 0.15 },
      { "word": "bantuan", "importance": 4.12 },
      { "word": "presiden", "importance": 0.05 },
      { "word": "Prabowo", "importance": 1.25 },
      { "word": "sebesar", "importance": -0.02 },
      { "word": "5", "importance": 2.50 },
      { "word": "juta", "importance": 3.10 },
      { "word": "rupiah", "importance": 0.45 }
    ]
  }
  ```

### 2️⃣ POST `/feedback`
Menerima koreksi prediksi dari pengguna untuk proses perbaikan model (active learning).
* **Request Body (JSON):**
  ```json
  {
    "text": "Pertumbuhan ekonomi Indonesia tercatat 5,12 persen pada kuartal pertama 2026 menurut data Badan Pusat Statistik.",
    "predicted_label": "Hoaks",
    "correct_label": "Valid",
    "note": "Ini adalah berita valid dari rilis pers resmi BPS."
  }
  ```
* **Response Body (JSON):**
  ```json
  {
    "status": "ok",
    "message": "Feedback diterima. Terima kasih, data ini akan digunakan untuk meningkatkan model."
  }
  ```

### 3️⃣ GET `/stats`
Menyajikan data statistik agregat prediksi yang telah diproses oleh sistem untuk divisualisasikan oleh tim frontend (Anggota 5).
* **Response Body (JSON):**
  ```json
  {
    "total_predictions": 5,
    "label_distribution": {
      "Hoaks": 3,
      "Mencurigakan": 1,
      "Valid": 1
    },
    "category_distribution": {
      "politik": 2,
      "bansos": 1,
      "ekonomi": 2,
      "umum": 1
    },
    "ai_generated_percentage": 60.0,
    "formal_news_percentage": 20.0,
    "average_hoax_score": 79.8
  }
  ```

### 4️⃣ POST `/sync`
Menyinkronkan database hoaks offline lokal secara real-time dengan men-scrape rilis hoaks terbaru dari Turnbackhoax.id dan memperbarui indeks similarity TF-IDF dalam memori.
* **Response Body (JSON):**
  ```json
  {
    "status": "ok",
    "message": "Sinkronisasi berhasil. Ditambahkan 10 artikel hoaks baru. Index similarity diperbarui.",
    "total_articles": 4102
  }
  ```