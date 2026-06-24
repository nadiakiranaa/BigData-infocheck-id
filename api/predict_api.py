import os
import re
import json
import joblib
import logging
import base64
from io import BytesIO
from PIL import Image
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Safe imports for Deep Learning libraries (fallback to ML Klasik if not installed)
try:
    import torch
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    DL_AVAILABLE = True
except ImportError:
    DL_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("torch/transformers tidak terinstal. Sistem akan berjalan dalam mode fallback (TF-IDF Baseline Only).")

# Import OCR Engine
try:
    from .ocr_engine import analyze_screenshot
except ImportError:
    try:
        from ocr_engine import analyze_screenshot
    except ImportError:
        analyze_screenshot = None

# =========================================================
# CONFIGURATION & LOAD MODELS
# =========================================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(BASE_DIR, "model", "indobert-infocheck-final")
BASELINE_DIR = os.path.join(BASE_DIR, "baseline_model.pkl")

# Global variables for models
indobert_tokenizer = None
indobert_model = None
indobert_num_labels = 4
baseline_data = None


def load_models():
    global indobert_tokenizer, indobert_model, indobert_num_labels, baseline_data

    # Load Baseline Model (TF-IDF + LR)
    if os.path.exists(BASELINE_DIR):
        try:
            baseline_data = joblib.load(BASELINE_DIR)
            logger.info("Baseline TF-IDF model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load baseline model: {e}")
    else:
        logger.warning(f"Baseline model not found at {BASELINE_DIR}")

    # Load IndoBERT Model
    if os.path.exists(MODEL_DIR):
        if not DL_AVAILABLE:
            logger.warning("IndoBERT model ditemukan tapi library PyTorch tidak ada. Melewati loading IndoBERT.")
        else:
            try:
                # Fallback check for num_labels in config
                config_path = os.path.join(MODEL_DIR, "config.json")
                if os.path.exists(config_path):
                    with open(config_path, "r") as f:
                        cfg = json.load(f)
                        indobert_num_labels = cfg.get("num_labels")
                        if indobert_num_labels is None:
                            id2label = cfg.get("id2label", {})
                            indobert_num_labels = len(id2label) if id2label else 4

                indobert_tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
                indobert_model = AutoModelForSequenceClassification.from_pretrained(
                    MODEL_DIR,
                    num_labels=indobert_num_labels,
                    ignore_mismatched_sizes=True
                )
                indobert_model.eval()
                logger.info(f"IndoBERT model loaded successfully with {indobert_num_labels} labels.")
            except Exception as e:
                logger.error(f"Failed to load IndoBERT model: {e}")
    else:
        logger.warning(f"IndoBERT model not found at {MODEL_DIR}")

# Call loader
load_models()

# =========================================================
# HELPER FUNCTIONS
# =========================================================

def extract_scam_entities_from_text(text):
    """Ekstrak nomor HP dan rekening dari teks secara otomatis."""
    entities = {}
    hp_matches = re.findall(r'\b(?:08|628|\+628)\d{8,11}\b', text)
    if hp_matches:
        entities["nomor_hp"] = hp_matches
    rek_matches = re.findall(r'\b\d{10,16}\b', text)
    if rek_matches:
        entities["rekening"] = rek_matches
    links = re.findall(r'(https?://[^\s]+|bit\.ly/[^\s]+|wa\.me/[^\s]+|t\.me/[^\s]+)', text)
    if links:
        entities["links"] = links
    return entities

def get_recommendation(label):
    if label == "Valid":
        return "Informasi ini aman. Anda bisa membagikannya kepada orang lain."
    elif label == "Hoaks":
        return (
            "STOP! Informasi ini terindikasi sebagai hoaks. "
            "Jangan sebarkan ke grup keluarga atau media sosial."
        )
    elif label == "Penipuan":
        return (
            "AWAS PENIPUAN: Konten ini terdeteksi sebagai modus penipuan digital. "
            "Jangan transfer uang, jangan klik link, dan jangan berikan data pribadi. "
            "Laporkan ke cekrekening.id atau hubungi 110 (Bareskrim)."
        )
    elif label == "Netral":
        return "NETRAL: Konten ini tidak mengandung indikasi hoaks maupun penipuan. Bisa berupa opini, promosi legal, atau informasi umum biasa."
    return ""

def predict_hybrid(text):
    """
    Prediksi Hybrid: IndoBERT (DL) + TF-IDF (ML Klasik)
    Mendukung 4 Kelas: Valid, Hoaks, Penipuan, Netral.
    """
    bl_scores = {"Valid": 0.0, "Hoaks": 0.0, "Penipuan": 0.0, "Netral": 0.0}
    if baseline_data is not None:
        try:
            bl_model = baseline_data["model"]
            bl_vectorizer = baseline_data["vectorizer"]
            text_clean = re.sub(r'http\S+|www\.\S+', ' ', text.lower())
            text_clean = re.sub(r'[^a-z0-9\s]', ' ', text_clean).strip()
            X = bl_vectorizer.transform([text_clean])
            probs = bl_model.predict_proba(X)[0]
            classes = bl_model.classes_
            class_to_label = {0: "Valid", 1: "Hoaks", 2: "Penipuan", 3: "Netral"}
            for i, c in enumerate(classes):
                lbl = class_to_label.get(int(c), f"class_{c}")
                bl_scores[lbl] = round(float(probs[i]) * 100, 2)
        except Exception as e:
            logger.error(f"Baseline error: {e}")

    indobert_scores = {"Valid": 0.0, "Hoaks": 0.0, "Penipuan": 0.0, "Netral": 0.0}
    if DL_AVAILABLE and indobert_model is not None and indobert_tokenizer is not None:
        try:
            inputs = indobert_tokenizer(text, return_tensors="pt", truncation=True, max_length=256)
            with torch.no_grad():
                outputs = indobert_model(**inputs)
                probs = torch.nn.functional.softmax(outputs.logits, dim=-1)[0].tolist()
            
            # Map index ke label (berdasarkan urutan di Colab)
            id2label = {0: "Valid", 1: "Hoaks", 2: "Penipuan", 3: "Netral"}
            for i, p in enumerate(probs):
                if i in id2label:
                    indobert_scores[id2label[i]] = round(p * 100, 2)
        except Exception as e:
            logger.error(f"IndoBERT error: {e}")

    # === HEURISTIC BOOST (untuk Mode Fallback TF-IDF) ===
    # Tandai jika ada kata kunci Hoaks yang sangat kuat (untuk override IndoBERT)
    hoaks_keywords = ["sebarkan", "viralkan", "bagikan", "kiamat", "tanda kiamat",
                      "dihapus pemerintah", "breaking news", "jangan ketinggalan",
                      "sebelum dihapus", "terbakar habis", "kerusuhan massa"]
    formal_keywords = ["kementerian", "melaporkan", "mengumumkan", "resmi", "apbn",
                       "kominfo", "presiden menyatakan", "bps", "bank indonesia"]
    text_lower_check = text.lower()
    hoaks_keyword_detected = any(word in text_lower_check for word in hoaks_keywords)
    if hoaks_keyword_detected:
        bl_scores["Hoaks"] = bl_scores.get("Hoaks", 0) + 30.0  # Boost lebih besar
    elif any(word in text_lower_check for word in formal_keywords):
        bl_scores["Valid"] = bl_scores.get("Valid", 0) + 8.0
    # === END HEURISTIC BOOST ===

    # Prioritas: Penipuan (IndoBERT) > Hoaks (Keyword/Baseline) > IndoBERT lainnya
    if indobert_scores.get("Penipuan", 0) > 55.0:
        final_label = "Penipuan"
        final_scores = {
            "Valid":    round(indobert_scores.get("Valid", 0), 2),
            "Hoaks":    round(bl_scores.get("Hoaks", 0) * 0.3, 2),
            "Penipuan": round(indobert_scores.get("Penipuan", 0), 2),
            "Netral":   round(bl_scores.get("Netral", 0) * 0.2, 2),
        }
    elif hoaks_keyword_detected and bl_scores.get("Hoaks", 0) > 35.0:
        # Override: Jika keyword hoaks provokatif ditemukan dan baseline setuju, paksa Hoaks
        final_label = "Hoaks"
        final_scores = {
            "Valid":    round(bl_scores.get("Valid", 0) * 0.2, 2),
            "Hoaks":    round(bl_scores.get("Hoaks", 0), 2),
            "Penipuan": round(bl_scores.get("Penipuan", 0) * 0.3, 2),
            "Netral":   round(bl_scores.get("Netral", 0) * 0.2, 2),
        }
    elif bl_scores.get("Hoaks", 0) > 55.0:
        final_label = "Hoaks"
        final_scores = {
            "Valid":    round(bl_scores.get("Valid", 0), 2),
            "Hoaks":    round(bl_scores.get("Hoaks", 0), 2),
            "Penipuan": round(indobert_scores.get("Penipuan", 0) * 0.3, 2),
            "Netral":   round(bl_scores.get("Netral", 0) * 0.2, 2),
        }
    else:
        # Tidak ada yang dominan — ambil max dari kedua model
        all_scores = {
            "Valid":    max(indobert_scores.get("Valid", 0), bl_scores.get("Valid", 0)),
            "Hoaks":    max(indobert_scores.get("Hoaks", 0), bl_scores.get("Hoaks", 0)),
            "Penipuan": max(indobert_scores.get("Penipuan", 0), bl_scores.get("Penipuan", 0)),
            "Netral":   max(indobert_scores.get("Netral", 0), bl_scores.get("Netral", 0)),
        }
        final_label = max(all_scores, key=all_scores.get)
        final_scores = {k: round(v, 2) for k, v in all_scores.items()}

    return final_label, final_scores, indobert_scores, bl_scores


# =========================================================
# FASTAPI APP
# =========================================================

app = FastAPI(
    title="InfoCheck ID - V2",
    description="API deteksi hoaks & penipuan hibrida (IndoBERT + TF-IDF) dengan fitur OCR Gemini.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class PredictTextRequest(BaseModel):
    text: str

class PredictImageRequest(BaseModel):
    image_base64: str

# Endpoints
@app.post("/predict")
def predict_text(req: PredictTextRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Teks tidak boleh kosong")

    final_label, final_scores, indobert_scores, bl_scores = predict_hybrid(req.text)
    entities = extract_scam_entities_from_text(req.text)

    # Log prediksi
    log_data = {
        "text": req.text,
        "label": final_label,
        "scores": final_scores
    }
    with open(os.path.join(BASE_DIR, "predictions_log.jsonl"), "a") as f:
        f.write(json.dumps(log_data) + "\n")

    return {
        "label": final_label,
        "score": final_scores[final_label],
        "all_scores": final_scores,
        "indobert_scores": indobert_scores,
        "baseline_scores": bl_scores,
        "recommendation": get_recommendation(final_label),
        "scam_entities": entities
    }

@app.post("/predict-image")
def predict_image(req: PredictImageRequest):
    if not analyze_screenshot:
        raise HTTPException(status_code=500, detail="Modul OCR tidak tersedia.")
    
    try:
        image_data = base64.b64decode(req.image_base64)
        img = Image.open(BytesIO(image_data))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Format base64 gambar tidak valid: {e}")

    # Panggil Gemini OCR
    ocr_result = analyze_screenshot(img)
    
    # Ambil teks dari OCR
    extracted_text = ocr_result.get("text", "")
    gemini_label = ocr_result.get("kategori", "VALID").capitalize()
    
# [TAMBAHAN Anggota 4] Cegah teks error dari OCR (misal Gemini overload/gagal)
    # ikut diklasifikasi sebagai konten asli — ini bisa menghasilkan label
    # Hoaks/Penipuan yang menyesatkan padahal isinya cuma pesan error teknis.
    if extracted_text.startswith("Gagal memproses gambar"):
        raise HTTPException(
            status_code=503,
            detail=f"OCR gagal memproses gambar: {ocr_result.get('alasan', 'Layanan OCR sedang tidak tersedia, coba lagi nanti.')}"
        )

    # Jalankan model hybrid pada teks yang diekstrak
    hybrid_label, final_scores, indobert_scores, bl_scores = predict_hybrid(extracted_text)
    
    # Gabungkan entitas
    entities = ocr_result.get("entitas_penipu", {})
    text_entities = extract_scam_entities_from_text(extracted_text)
    if not entities.get("nomor_hp") and text_entities.get("nomor_hp"):
        entities["nomor_hp"] = text_entities["nomor_hp"][0]

    # Prioritaskan label penipuan dari Gemini OCR karena Gemini bisa melihat konteks visual
    final_label = gemini_label if gemini_label == "Penipuan" else hybrid_label

    return {
        "extracted_text": extracted_text,
        "label": final_label,
        "ocr_label": gemini_label,
        "hybrid_label": hybrid_label,
        "score": final_scores.get(final_label, 90.0),
        "all_scores": final_scores,
        "recommendation": get_recommendation(final_label),
        "scam_entities": entities,
        "ocr_reason": ocr_result.get("alasan", "")
    }

@app.get("/stats")
def get_stats():
    labels = {"Hoaks": 0, "Penipuan": 0, "Valid": 0, "Netral": 0}
    total = 0
    try:
        log_path = os.path.join(BASE_DIR, "predictions_log.jsonl")
        if os.path.exists(log_path):
            with open(log_path, "r") as f:
                for line in f:
                    data = json.loads(line)
                    lbl = data.get("label", "Valid")
                    if lbl in labels:
                        labels[lbl] += 1
                    total += 1
    except Exception as e:
        pass
    return {"total_predictions": total, "labels": labels}

@app.get("/")
def read_root():
    return {"message": "InfoCheck ID V2 API is running (4 Classes + OCR Support)"}
