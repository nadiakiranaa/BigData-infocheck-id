"""
InfoCheck ID — FastAPI Predict Endpoint (Anggota 3)
Merangkai: IndoBERT (klasifikasi) + similarity Komdigi (alasan) +
post-processing (confidence calibration, kategori isu, deepfake flag)
"""

import re
import time
import torch
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForSequenceClassification

from .komdigi_similarity import load_index, get_reason


# =========================================================
# SETUP — dijalankan sekali saat server start
# =========================================================

MODEL_DIR = "model/indobert-infocheck-final"
MAX_LENGTH = 256

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

print("Loading IndoBERT model...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_DIR)
model.to(device)
model.eval()

print("Loading Komdigi similarity index...")
komdigi_index = load_index()

print("Model & index siap. Server starting...")


# =========================================================
# POST-PROCESSING MODULES
# =========================================================

# --- 1. Kategori isu (rule-based keyword matching) ---
CATEGORY_KEYWORDS = {
    "ekonomi": [
        "ekonomi", "inflasi", "rupiah", "dollar", "bursa", "saham", "investasi",
        "pajak", "harga", "subsidi", "ekspor", "impor", "resesi", "pertumbuhan ekonomi",
        "bank", "kredit", "utang", "anggaran", "apbn", "bps", "statistik",
    ],
    "politik": [
        "presiden", "menteri", "dpr", "pemilu", "partai", "pilkada", "pilpres",
        "gubernur", "kebijakan", "pemerintah", "istana", "kabinet", "politik",
        "prabowo", "wakil presiden",
    ],
    "bansos": [
        "bansos", "bantuan sosial", "bantuan langsung", "blt", "subsidi bbm",
        "kartu sembako", "pkh", "bantuan presiden", "bantuan ekonomi", "dana bantuan",
    ],
    "kesehatan": [
        "vaksin", "covid", "rumah sakit", "obat", "penyakit", "virus", "kesehatan",
        "bpjs", "dokter",
    ],
}


def detect_categories(text):
    text_lower = text.lower()
    detected = []
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            detected.append(category)
    return detected if detected else ["umum"]


# --- 2. Deepfake / AI-generated text heuristic ---
VIRAL_PHRASES = [
    "sebarkan", "viral", "klik link", "buruan", "segera daftar",
    "jangan sampai ketinggalan", "100 orang tercepat", "terbatas",
    "sebelum dihapus", "wajib tahu", "forward", "teruskan pesan",
    "share sekarang", "info penting", "jangan diabaikan",
]

def detect_ai_generated(text):
    text_lower = text.lower()
    signals = 0

    if any(p in text_lower for p in VIRAL_PHRASES):
        signals += 1

    caps_words = re.findall(r'\b[A-Z]{4,}\b', text)
    if len(caps_words) >= 3:
        signals += 1

    if re.search(r'[!?]{2,}', text):
        signals += 1

    if re.search(r'(https?://|www\.|bit\.ly|t\.me)', text_lower) and any(p in text_lower for p in VIRAL_PHRASES):
        signals += 1

    return signals >= 2


# --- 3. Formal news style detector (heuristic) ---
FORMAL_INSTITUTIONS = [
    "bps", "badan pusat statistik", "bank indonesia", "kemenkeu", "kementerian",
    "dpr", "presiden", "gubernur", "menteri", "polri", "tni", "mahkamah",
    "kompas", "tempo", "antara", "detik", "cnn indonesia", "republika",
    "reuters", "bloomberg", "katadata", "bisnis.com",
    "persen", "kuartal", "semester", "triwulan", "laporan", "data menunjukkan",
    "berdasarkan data", "menurut laporan", "tercatat", "mencapai",
]

def is_formal_news_style(text):
    """
    Deteksi apakah teks bergaya berita formal / data resmi.
    Sinyal: kutipan institusi resmi, angka statistik, gaya jurnalistik.
    """
    text_lower = text.lower()
    formal_signals = sum(1 for inst in FORMAL_INSTITUTIONS if inst in text_lower)

    # Angka persentase / statistik
    has_stats = bool(re.search(r'\d+[,\.]\d+\s*%|\d+\s*persen|\bkuartal\b|\bsemester\b', text_lower))

    # Tidak ada pola hoaks (caps berlebihan, ajakan viral, tanda baca berulang)
    no_hoax_patterns = (
        len(re.findall(r'\b[A-Z]{4,}\b', text)) < 2
        and not re.search(r'[!?]{2,}', text)
        and not any(p in text_lower for p in VIRAL_PHRASES)
    )

    return (formal_signals >= 2 or has_stats) and no_hoax_patterns


# --- 4. Confidence calibration ---
def get_confidence_note(score, label):
    if label == "Mencurigakan":
        return "Skor berada di rentang ambigu. Disarankan verifikasi manual ke sumber terpercaya sebelum menyebarkan."
    if 40 <= score <= 60:
        return "Skor berada di rentang ambigu (40-60%). Disarankan verifikasi manual sebelum mengambil kesimpulan."
    return None


def get_recommendation(label):
    if label == "Hoaks":
        return (
            "PERINGATAN: Konten terindikasi kuat sebagai HOAKS. Jangan menyebarkan "
            "berita ini untuk menghentikan rantai disinformasi. Laporkan ke portal Aduan Konten Kominfo."
        )
    elif label == "Mencurigakan":
        return (
            "WASPADA: Informasi berada di zona abu-abu. Periksa kredibilitas sumber, "
            "cek media arus utama, dan hindari menyebarkan sebelum diverifikasi."
        )
    return "AMAN: Informasi tergolong valid. Tetap budayakan membaca berita secara kritis."


# --- Sentiment & Sensationalism Analysis ---
NEG_SENTIMENT_WORDS = [
    "buruk", "anjlok", "kolaps", "rugi", "krisis", "resesi", "utang", "korup",
    "korupsi", "sanksi", "tuduh", "menyesatkan", "rugi", "inflasi", "suku bunga naik",
    "jatuh", "sakit", "meninggal", "kematian", "darurat", "kriminal", "pencurian",
    "ditangkap", "tersangka", "palsu", "penipuan", "bahaya", "ancaman", "bohong",
]

POS_SENTIMENT_WORDS = [
    "tumbuh", "naik", "meningkat", "surplus", "baik", "sukses", "prestasi", "untung",
    "bantuan", "subsidi", "meresmikan", "pembangunan", "maju", "lulus", "menang",
    "semifinal", "berhasil", "stabil", "aman", "sehat", "pulih", "mengapresiasi",
]

SENSATIONAL_WORDS = [
    "waspada", "bahaya", "darurat", "mengerikan", "panik", "segera", "jangan diabaikan",
    "kritis", "ancaman", "viral", "hancur", "heboh", "gempar", "terbongkar", "rahasia",
    "terkuak", "terungkap", "mengejutkan", "kacau", "waspadalah",
]

def analyze_text_nlp(text):
    text_lower = text.lower()
    
    # Sentiment analysis
    neg_count = sum(1 for w in NEG_SENTIMENT_WORDS if w in text_lower)
    pos_count = sum(1 for w in POS_SENTIMENT_WORDS if w in text_lower)
    
    if neg_count > pos_count:
        sentiment = "Negatif"
    elif pos_count > neg_count:
        sentiment = "Positif"
    else:
        sentiment = "Netral"
        
    # Sensationalism detection (provocative tone)
    has_sensational_words = any(w in text_lower for w in SENSATIONAL_WORDS)
    has_caps = len(re.findall(r'\b[A-Z]{4,}\b', text)) >= 2
    has_exclamation = bool(re.search(r'[!?]{2,}', text))
    
    is_sensational = has_sensational_words or has_caps or has_exclamation
    
    return sentiment, is_sensational


# =========================================================
# CORE PREDICTION
# =========================================================

def predict_hoax_score(text):
    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        padding="max_length",
        max_length=MAX_LENGTH,
    ).to(device)

    with torch.no_grad():
        outputs = model(**inputs)
        # Temperature Scaling (T = 2.5) untuk mengkalibrasi probabilitas overconfident
        calibrated_logits = outputs.logits / 2.5
        probs = torch.softmax(calibrated_logits, dim=-1).cpu().numpy()[0]

    hoax_score = float(probs[1]) * 100
    return round(hoax_score, 2)


def predict_hoax_score_batch(texts):
    if not texts:
        return []
    inputs = tokenizer(
        texts,
        return_tensors="pt",
        truncation=True,
        padding=True,
        max_length=MAX_LENGTH,
    ).to(device)

    with torch.no_grad():
        outputs = model(**inputs)
        calibrated_logits = outputs.logits / 2.5
        probs = torch.softmax(calibrated_logits, dim=-1).cpu().numpy()

    scores = [round(float(p[1]) * 100, 2) for p in probs]
    return scores


def explain_hoax_score(text):
    # Bersihkan teks dasar dan cari semua token kata
    words = re.findall(r'\b\w+\b', text)
    if not words:
        return []

    # Batasi ke 25 kata pertama agar pemrosesan batch tetap cepat di CPU
    words = words[:25]
    base_score = predict_hoax_score(text)

    # Buat variasi teks dengan menghapus kata satu per satu (LIME-light perturbation)
    perturbed_texts = []
    for idx in range(len(words)):
        temp_words = words[:idx] + words[idx+1:]
        perturbed_texts.append(" ".join(temp_words))

    # Prediksi semua teks terganggu dalam satu batch forward pass (efisien)
    scores = predict_hoax_score_batch(perturbed_texts)

    importance_scores = []
    for idx, word in enumerate(words):
        # Kontribusi kata = skor_utama - skor_tanpa_kata
        # Jika penghapusan kata menurunkan skor hoaks, kata tersebut berkontribusi positif (sinyal hoaks)
        contribution = base_score - scores[idx]
        importance_scores.append({
            "word": word,
            "importance": round(contribution, 2)
        })

    return importance_scores


def score_to_label(score, text):
    """
    Konversi skor ke label dengan threshold adaptif.
    Teks bergaya berita formal mendapat threshold lebih ketat
    (model harus lebih yakin sebelum label Hoaks).
    """
    formal = is_formal_news_style(text)
    has_viral = detect_ai_generated(text)

    # Teks dengan sinyal viral kuat → threshold lebih longgar (mudah Hoaks)
    if has_viral:
        if score >= 60:
            return "Hoaks"
        elif score >= 30:
            return "Mencurigakan"
        return "Valid"

    # Teks bergaya berita formal → threshold ketat (butuh lebih yakin untuk Hoaks)
    if formal:
        if score >= 85:
            return "Hoaks"
        elif score >= 55:
            return "Mencurigakan"
        return "Valid"

    # Default threshold (teks umum/tidak jelas polanya)
    if score >= 75:
        return "Hoaks"
    elif score >= 45:
        return "Mencurigakan"
    return "Valid"


def build_reason(text, label, score):
    if label == "Valid":
        if is_formal_news_style(text):
            return "Teks bergaya berita/data resmi. Tidak ditemukan indikasi pola hoaks oleh model IndoBERT."
        return "Tidak ditemukan indikasi hoaks oleh model klasifikasi IndoBERT."

    reason = get_reason(text, komdigi_index)
    if "Tidak ditemukan" in reason:
        if label == "Mencurigakan":
            return (
                f"Model mendeteksi pola bahasa yang perlu diwaspadai (skor: {score:.1f}%). "
                "Tidak ditemukan kecocokan persis dengan database hoaks Komdigi. "
                "Disarankan verifikasi ke sumber berita terpercaya."
            )
        return (
            f"Model mendeteksi pola bahasa yang mirip konten hoaks (skor: {score:.1f}%). "
            "Tidak ditemukan kecocokan persis dengan database hoaks Komdigi."
        )
    return reason


# =========================================================
# FASTAPI APP
# =========================================================

app = FastAPI(
    title="InfoCheck ID - Hoax Detection API",
    description="API deteksi hoaks berita ekonomi & politik Indonesia berbasis IndoBERT + Komdigi similarity.",
    version="1.0.0",
)


class PredictRequest(BaseModel):
    text: str


class PredictResponse(BaseModel):
    score: float
    label: str
    reason: str
    category: list[str]
    ai_generated_flag: bool
    confidence_note: str | None
    is_formal_news: bool
    processing_time_ms: float
    recommendation: str
    sentiment: str
    is_sensational: bool
    model_version: str
    word_importance: list[dict]


class FeedbackRequest(BaseModel):
    text: str
    predicted_label: str
    correct_label: str
    note: str | None = None


@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "InfoCheck ID API is running",
        "endpoints": ["/predict", "/feedback", "/stats", "/health", "/docs"],
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "model": MODEL_DIR,
        "device": str(device),
    }


@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    start_time = time.time()
    text = req.text.strip()

    score = predict_hoax_score(text)
    formal = is_formal_news_style(text)
    label = score_to_label(score, text)
    reason = build_reason(text, label, score)
    category = detect_categories(text)
    ai_flag = detect_ai_generated(text)
    confidence_note = get_confidence_note(score, label)
    recommendation = get_recommendation(label)

    # Analisis NLP tambahan: Sentimen & Sensasionalisme (Pure NLP Features)
    sentiment, is_sensational = analyze_text_nlp(text)

    # Model Explainability (LIME-light word importance)
    word_importance = explain_hoax_score(text)

    # Log prediksi ke predictions_log.jsonl untuk statistik
    import json
    from datetime import datetime
    
    pred_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "text_preview": text[:100],
        "score": score,
        "label": label,
        "categories": category,
        "ai_generated_flag": ai_flag,
        "is_formal_news": formal
    }
    try:
        with open("predictions_log.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(pred_entry, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"Error logging prediction: {e}")

    processing_time_ms = round((time.time() - start_time) * 1000, 2)

    return PredictResponse(
        score=score,
        label=label,
        reason=reason,
        category=category,
        ai_generated_flag=ai_flag,
        confidence_note=confidence_note,
        is_formal_news=formal,
        processing_time_ms=processing_time_ms,
        recommendation=recommendation,
        sentiment=sentiment,
        is_sensational=is_sensational,
        model_version="IndoBERT-v2-calibrated",
        word_importance=word_importance,
    )


def check_and_trigger_retrain():
    """
    Memeriksa jumlah feedback di feedback_log.jsonl.
    Jika mencapai threshold, jalankan active_learning.py di background.
    """
    import os
    import subprocess
    
    if not os.path.exists("feedback_log.jsonl"):
        return
        
    try:
        with open("feedback_log.jsonl", "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
            
        # Set threshold rendah (misal 5) agar dosen/anggota lain mudah menguji saat demo.
        # Pada produksi sesungguhnya, batas ini diset ke 500.
        RETRAIN_THRESHOLD = 5
        if len(lines) >= RETRAIN_THRESHOLD:
            print(f"Active Learning Trigger: Feedback mencapai {len(lines)} data. Memulai retraining...")
            # Jalankan skrip retraining secara asynchronous
            subprocess.Popen(["python", "active_learning.py"])
    except Exception as e:
        print(f"Gagal memeriksa trigger active learning: {e}")


@app.post("/feedback")
def feedback(req: FeedbackRequest, background_tasks: BackgroundTasks):
    """
    Endpoint untuk menerima koreksi dari user.
    Data disimpan ke feedback_log.jsonl untuk active learning (retrain di masa depan).
    Jika jumlah feedback mencapai threshold, retraining model baseline dipicu secara otomatis.
    """
    import json
    from datetime import datetime

    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "text": req.text[:500],
        "predicted_label": req.predicted_label,
        "correct_label": req.correct_label,
        "note": req.note,
    }

    with open("feedback_log.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    # Jalankan background check untuk trigger retraining
    background_tasks.add_task(check_and_trigger_retrain)

    return {
        "status": "ok",
        "message": "Feedback diterima. Terima kasih, data ini akan digunakan untuk meningkatkan model.",
    }


@app.get("/stats")
def get_stats():
    """
    Endpoint untuk melihat statistik agregat dari hasil prediksi yang telah dilakukan.
    """
    import os
    import json

    total = 0
    labels = {"Hoaks": 0, "Mencurigakan": 0, "Valid": 0}
    categories = {}
    ai_generated_count = 0
    formal_news_count = 0
    scores_sum = 0.0

    if os.path.exists("predictions_log.jsonl"):
        try:
            with open("predictions_log.jsonl", "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    data = json.loads(line)
                    total += 1
                    
                    lbl = data.get("label", "Valid")
                    labels[lbl] = labels.get(lbl, 0) + 1
                    
                    for cat in data.get("categories", []):
                        categories[cat] = categories.get(cat, 0) + 1
                        
                    if data.get("ai_generated_flag", False):
                        ai_generated_count += 1
                    if data.get("is_formal_news", False):
                        formal_news_count += 1
                    scores_sum += data.get("score", 0.0)
        except Exception as e:
            return {"status": "error", "message": f"Gagal membaca log prediksi: {str(e)}"}

    avg_score = round(scores_sum / total, 2) if total > 0 else 0.0

    return {
        "total_predictions": total,
        "label_distribution": labels,
        "category_distribution": categories,
        "ai_generated_percentage": round((ai_generated_count / total * 100), 2) if total > 0 else 0.0,
        "formal_news_percentage": round((formal_news_count / total * 100), 2) if total > 0 else 0.0,
        "average_hoax_score": avg_score
    }


@app.post("/sync")
def sync_database():
    """
    Endpoint untuk menyinkronkan database hoaks offline dengan melakukan scraping
    artikel hoaks terbaru dari turnbackhoax.id, menambahkannya ke database komdigi,
    dan membangun kembali similarity index secara real-time.
    """
    import os
    import pandas as pd
    from .komdigi_similarity import build_index, KOMDIGI_CSV
    
    try:
        import requests
        from bs4 import BeautifulSoup
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        url = "https://turnbackhoax.id/"
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return {"status": "error", "message": f"Gagal menghubungi turnbackhoax.id: HTTP {response.status_code}"}
            
        soup = BeautifulSoup(response.content, 'html.parser')
        posts = soup.find_all('article')
        new_records = []
        
        for post in posts:
            title_tag = post.find('h2') or post.find('h3')
            title = title_tag.get_text(strip=True) if title_tag else ''
            
            link_tag = title_tag.find('a') if title_tag else None
            link = link_tag['href'] if link_tag else ''
            
            excerpt_tag = post.find('p')
            excerpt = excerpt_tag.get_text(strip=True) if excerpt_tag else ''
            
            if title:
                # Format agar sesuai kolom komdigi_hoaks.csv: title, body_text, category, url
                new_records.append({
                    "title": f"[SYNCED] {title}",
                    "body_text": excerpt if excerpt else title,
                    "category": "Umum",
                    "url": link
                })
                
        if not new_records:
            return {"status": "ok", "message": "Sinkronisasi selesai. Tidak ada berita baru ditemukan."}
            
        # Gabungkan dengan CSV komdigi_hoaks.csv yang ada
        if os.path.exists(KOMDIGI_CSV):
            df_existing = pd.read_csv(KOMDIGI_CSV)
            df_new = pd.DataFrame(new_records)
            
            df_combined = pd.concat([df_new, df_existing], ignore_index=True)
            df_combined = df_combined.drop_duplicates(subset=['title']).reset_index(drop=True)
            df_combined.to_csv(KOMDIGI_CSV, index=False)
            added_count = len(df_combined) - len(df_existing)
        else:
            df_new = pd.DataFrame(new_records)
            os.makedirs(os.path.dirname(KOMDIGI_CSV), exist_ok=True)
            df_new.to_csv(KOMDIGI_CSV, index=False)
            added_count = len(new_records)
            
        # Rebuild TF-IDF index secara dinamis dalam memori
        global komdigi_index
        komdigi_index = build_index()
        
        return {
            "status": "ok",
            "message": f"Sinkronisasi berhasil. Ditambahkan {added_count} artikel hoaks baru. Index similarity diperbarui.",
            "total_articles": len(pd.read_csv(KOMDIGI_CSV))
        }
    except Exception as e:
        return {"status": "error", "message": f"Gagal melakukan sinkronisasi: {str(e)}"}