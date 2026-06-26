# PANDUAN MENJALANKAN SISTEM SECARA LENGKAP (END-TO-END)
**Proyek:** InfoCheck ID — Sistem Deteksi Hoaks & Penipuan Berbasis Big Data Real-Time

Dokumen ini berisi panduan berurutan untuk menjalankan seluruh komponen sistem dari Anggota 1 hingga Anggota 6. Sangat cocok digunakan untuk **persiapan demo**.

---

## 📋 PRASYARAT
Sebelum mulai, pastikan:
1. Kamu sudah punya Token Bot Telegram dari `@BotFather`.
2. Kamu sudah mengatur environment variable `TELEGRAM_BOT_TOKEN` atau mengisinya di dalam file `bot/telegram_bot.py`.
3. Kamu memiliki service Kafka dan Zookeeper yang bisa dijalankan (misalnya lewat Docker `docker-compose up -d`).

---

## 🧑‍💻 URUTAN MENJALANKAN SISTEM

Disarankan untuk membuka beberapa **Terminal terpisah** agar log dari setiap service bisa terlihat dengan jelas.

### STEP 1: Anggota 2 & 3 (Data Lakehouse & Model ML)
Tugas ini hanya perlu dijalankan **satu kali** di awal untuk menyiapkan data dan model AI.
```bash
# Di Terminal 1
python scripts/test_gemini.py       # (Opsional) OCR Screenshot menjadi teks
python scripts/prepare_dataset.py   # WAJIB 1: Bangun Data Lakehouse (Bronze -> Silver -> Gold)
python ml/nlp_baseline.py           # WAJIB 2: Update model AI agar mempelajari dataset Gold terbaru
```
*Hasil: Folder `dataset/lakehouse` terbangun, dan file model `baseline_model.pkl` serta `vectorizer.pkl` terbuat (akurasi ~98%).*

---

### STEP 2: Anggota 3 (Model Machine Learning & API)
Menjalankan otak AI dari sistem ini. Jika kamu tidak punya model IndoBERT (`.bin`), sistem akan otomatis memakai model Baseline (TF-IDF) yang akurasinya tetap bagus (97.7%).
```bash
# Di Terminal 2
cd api
python predict_api.py
```
*Hasil: AI menyala di `http://localhost:8000`. Biarkan terminal ini terbuka.*

---

### STEP 3: Anggota 1 (Infrastruktur Big Data - Kafka)
Memulai aliran data real-time. **PENTING: Pastikan aplikasi Docker Desktop sudah terbuka dan berjalan.**

```bash
# Di Terminal 3 (Nyalakan server Kafka terlebih dahulu)
docker-compose up -d

# Tunggu sekitar 10 detik agar Kafka siap, lalu jalankan Consumer:
python consumers/stream_consumer.py
```
*Hasil: Script akan stand-by menunggu pesan dari Telegram/RSS dan mengirim hasil analisis kembali ke Kafka (topic: `analyzed-news`). Biarkan terminal ini terbuka. (Jika error `NoBrokersAvailable`, berarti Docker-mu belum menyala).*

---

### STEP 4: Anggota 4 (Bot Telegram)
Antarmuka pengguna (user-facing). Juri atau pengguna bisa mengecek berita hoaks langsung dari HP.
```bash
# Di Terminal 4
python bot/telegram_bot.py
```
*Hasil: Bot Telegram InfoCheck ID aktif dan bisa merespons pesan teks/gambar. Biarkan terminal ini terbuka.*

---

### STEP 5: Anggota 5 (Dashboard & API Bridge)
Visualisasi data ke dalam web interaktif.
```bash
# Di Terminal 5 (Backend Dashboard)
python api_bridge/main.py
```
*Hasil: API Bridge menyala di `http://localhost:8001`.*

```bash
# Di Terminal 6 (Frontend Web UI)
cd frontend
npm run dev
```
*Hasil: Buka browser ke `http://localhost:5173`. Kamu akan melihat Dashboard InfoCheck ID.*

---

### STEP 6: Anggota 6 (Integrasi & Quality Assurance)
Sebagai integrator (Anggota 6), tugasmu adalah **mengetes aliran dari ujung ke ujung (End-to-End Test)** saat demo:

1. **Aksi:** Buka Telegram, kirim pesan hoaks ke bot (contoh: *"Bantuan presiden 5 juta klik link ini"*).
2. **Cek Bot (Anggota 4):** Bot harus membalas "🚨 HASIL DETEKSI: PENIPUAN".
3. **Cek AI (Anggota 3):** Di Terminal 2, kamu akan melihat log AI menerima request dan memberikan skor 90%+.
4. **Cek Kafka (Anggota 1):** Di Terminal 3, kamu akan melihat log bahwa pesan tersebut berhasil ditangkap dari stream dan diteruskan ke AI.
5. **Cek Dashboard (Anggota 5):** Di browser (`http://localhost:5173`), pada tabel "Live Feed", data berita yang baru saja kamu kirim di Telegram **harus muncul secara real-time** di layar.

🎉 **Jika semua 5 poin di atas terjadi, demo kalian sukses 100%!**
