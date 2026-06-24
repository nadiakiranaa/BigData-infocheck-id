# active_learning.py
# InfoCheck ID — Active Learning & Automatic Retraining (Anggota 3)
# Skrip ini dipicu otomatis oleh API ketika jumlah feedback koreksi mencapai threshold.
# Skrip melatih ulang model baseline secara real-time dan menyimpan data baru
# ke dalam pool dataset untuk keperluan retrain model IndoBERT di masa depan.

import os
import json
import pandas as pd
import pickle
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from datetime import datetime

FEEDBACK_FILE = "feedback_log.jsonl"
ARCHIVE_FILE = "feedback_log_archived.jsonl"
TRAINING_POOL_CSV = "dataset/new_training_pool.csv"
BASELINE_MODEL_PATH = "baseline_model.pkl"

def clean_text(text):
    text = str(text).lower()
    text = re.sub(r'http\S+|www\.\S+', ' ', text)        # hapus URL
    text = re.sub(r'<.*?>', ' ', text)                    # hapus tag HTML
    text = re.sub(r'[^a-z0-9\s]', ' ', text)              # hapus karakter non-alfanumerik
    text = re.sub(r'\s+', ' ', text).strip()              # hapus spasi berlebih
    return text

def load_feedback_data():
    """Membaca data koreksi dari feedback_log.jsonl"""
    records = []
    if not os.path.exists(FEEDBACK_FILE):
        return []
        
    with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                correct_lbl = data.get("correct_label")
                
                # Petakan label koreksi ke 4-kelas:
                # Valid = 0, Hoaks = 1, Penipuan = 2, Netral = 3
                if correct_lbl == "Valid":
                    label_num = 0
                elif correct_lbl in ["Hoaks", "Hoax"]:
                    label_num = 1
                elif correct_lbl == "Penipuan":
                    label_num = 2
                elif correct_lbl == "Netral":
                    label_num = 3
                else:
                    continue  # Abaikan label tidak dikenal
                    
                records.append({
                    "text": clean_text(data.get("text")),
                    "label_num": label_num
                })
            except Exception as e:
                print(f"Gagal mem-parsing baris feedback: {e}")
                
    return records

def retrain_baseline(new_samples):
    """
    Melatih ulang model baseline (TF-IDF + Logistic Regression) dengan menyuntikkan
    data feedback baru ke dalam data latih asli untuk update performa seketika.
    """
    print("Memulai proses retraining model baseline...")
    
    try:
        df_new = pd.DataFrame(new_samples)
        
        # Skenario: Gabungkan dengan dataset balanced asli jika tersedia
        original_csv = "dataset/final_dataset_balanced.csv"
        if not os.path.exists(original_csv):
            original_csv = "dataset/final_dataset.csv"
            
        if os.path.exists(original_csv):
            df_orig = pd.read_csv(original_csv)
            # Map labels to numeric (4-kelas)
            def map_label(x):
                x_str = str(x).strip().lower()
                if x_str == 'valid':    return 0
                elif x_str in ['hoax', 'hoaks']: return 1
                elif x_str == 'penipuan': return 2
                elif x_str == 'netral': return 3
                return 0
            df_orig['label_num'] = df_orig['final_label'].apply(map_label)
            df_orig['text'] = df_orig['text'].apply(clean_text)
            df_orig = df_orig[['text', 'label_num']]
            df_train = pd.concat([df_orig, df_new], ignore_index=True)
        else:
            df_train = df_new

        df_train = df_train.dropna(subset=['text']).drop_duplicates(subset=['text'])
        
        # 2. Vektorisasi TF-IDF & Retrain
        vectorizer = TfidfVectorizer(max_features=10000, ngram_range=(1, 2))
        X_tfidf = vectorizer.fit_transform(df_train['text'])
        y = df_train['label_num'].astype(int)
        
        # Logistic Regression (Multinomial 3-Class)
        # multi_class deprecated in sklearn >= 1.5, lbfgs handles multinomial by default
        model = LogisticRegression(max_iter=1000, class_weight='balanced', solver='lbfgs')
        model.fit(X_tfidf, y)
        
        # 3. Simpan model baseline terupdate
        with open(BASELINE_MODEL_PATH, "wb") as f:
            pickle.dump({'model': model, 'vectorizer': vectorizer}, f)
            
        print(f"Model baseline berhasil diperbarui dengan {len(new_samples)} data feedback baru.")
        return True
    except Exception as e:
        print(f"Gagal melatih ulang model baseline: {e}")
        return False

def archive_and_pool(new_samples):
    """
    Arsipkan data feedback yang sudah diproses agar tidak dihitung ulang,
    dan simpan ke dalam CSV pool untuk training IndoBERT berikutnya.
    """
    try:
        df_new = pd.DataFrame(new_samples)
        
        # Tambahkan ke new_training_pool.csv
        if os.path.exists(TRAINING_POOL_CSV):
            df_existing = pd.read_csv(TRAINING_POOL_CSV)
            df_combined = pd.concat([df_existing, df_new], ignore_index=True)
            df_combined = df_combined.drop_duplicates(subset=['text']).reset_index(drop=True)
            df_combined.to_csv(TRAINING_POOL_CSV, index=False)
        else:
            os.makedirs(os.path.dirname(TRAINING_POOL_CSV), exist_ok=True)
            df_new.to_csv(TRAINING_POOL_CSV, index=False)
            
        # Pindahkan isi feedback_log.jsonl ke archive
        if os.path.exists(FEEDBACK_FILE):
            with open(FEEDBACK_FILE, "r", encoding="utf-8") as src:
                content = src.read()
            with open(ARCHIVE_FILE, "a", encoding="utf-8") as dest:
                dest.write(content)
                
            # Kosongkan file log utama untuk mereset counter threshold
            os.remove(FEEDBACK_FILE)
            
        print("Data feedback diarsipkan dan diakumulasikan ke pool training.")
    except Exception as e:
        print(f"Gagal mengarsipkan feedback: {e}")

def main():
    new_samples = load_feedback_data()
    if not new_samples:
        print("Tidak ada data feedback baru yang valid untuk dilatih.")
        return
        
    success = retrain_baseline(new_samples)
    if success:
        archive_and_pool(new_samples)
        print("Proses Active Learning selesai dengan sukses.")

if __name__ == "__main__":
    main()
