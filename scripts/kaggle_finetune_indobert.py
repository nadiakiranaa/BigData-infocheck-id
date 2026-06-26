"""
=============================================================
InfoCheck ID V2 — IndoBERT 4-Kelas Fine-Tuning (Google Colab)
=============================================================
CARA PAKAI:
1. Buka Google Colab → New Notebook
2. Aktifkan GPU: Runtime > Change runtime type > T4 GPU
3. Copy-paste SELURUH isi file ini ke satu cell
4. Upload file 'final_dataset_balanced.parquet' dari folder dataset/lakehouse/gold ke Colab
5. Jalankan cell → tunggu ~15-20 menit
6. Download folder 'indobert-infocheck-final.zip' dari Files panel
7. Extract → taruh isinya di: model/indobert-infocheck-final/ di proyek lokal
=============================================================
"""

# =============================================
# INSTALL DEPENDENCIES (jalankan sekali)
# =============================================
import subprocess
subprocess.run(["pip", "install", "transformers", "accelerate", "scikit-learn", "-q"])

# =============================================
# IMPORT
# =============================================
import os
import pandas as pd
import numpy as np
import torch
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score, f1_score
from torch.utils.data import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
    EarlyStoppingCallback,
)
import warnings
warnings.filterwarnings("ignore")

print(f"GPU tersedia: {torch.cuda.is_available()}")
print(f"Device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'}")

# =============================================
# KONFIGURASI — PENTING: 4 KELAS
# =============================================
MODEL_NAME   = "indobenchmark/indobert-base-p2"
DATASET_PATH = "dataset/lakehouse/gold/final_dataset_balanced.parquet"
if not os.path.exists(DATASET_PATH):
    # Jika di Colab, biasanya file langsung di-upload ke root folder
    DATASET_PATH = "final_dataset_balanced.parquet"
OUTPUT_DIR   = "indobert-infocheck-final"

# ⚠️ LABEL MAPPING — HARUS KONSISTEN antara training dan inference
LABEL2ID = {"Valid": 0, "Hoaks": 1, "Penipuan": 2, "Netral": 3}
ID2LABEL  = {0: "Valid", 1: "Hoaks", 2: "Penipuan", 3: "Netral"}
NUM_LABELS = 4   # ← 4 kelas sekarang

MAX_LENGTH = 256
BATCH_SIZE = 16   # turunkan ke 8 jika OOM
EPOCHS     = 5
LR         = 2e-5

# =============================================
# STEP 1: LOAD DATASET
# =============================================
print("\n" + "="*50)
print("STEP 1: Load Dataset")
print("="*50)

df = pd.read_parquet(DATASET_PATH)
df = df.dropna(subset=["text"]).drop_duplicates(subset=["text"])
df["final_label"] = df["final_label"].str.strip()
df["final_label"] = df["final_label"].replace({"Hoax": "Hoaks"})  # normalize ejaan
df = df[df["final_label"].isin(LABEL2ID.keys())]
df["label"] = df["final_label"].map(LABEL2ID).astype(int)

print(f"Total baris: {len(df)}")
print("Distribusi label:")
print(df["final_label"].value_counts())

# Verifikasi: harus ada tepat 4 kelas
assert df["label"].nunique() == 4, f"ERROR: Hanya ada {df['label'].nunique()} kelas! Harus 4."
print("\n✅ Verifikasi: 4 kelas ditemukan (Valid, Hoaks, Penipuan, Netral)")

# Train 70% / Val 15% / Test 15%
df_train, df_temp = train_test_split(df, test_size=0.3, random_state=42, stratify=df["label"])
df_val, df_test   = train_test_split(df_temp, test_size=0.5, random_state=42, stratify=df_temp["label"])
print(f"\nTrain: {len(df_train)} | Val: {len(df_val)} | Test: {len(df_test)}")

# =============================================
# STEP 2: DATASET CLASS
# =============================================
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

class InfoCheckDataset(Dataset):
    def __init__(self, texts, labels):
        self.enc = tokenizer(
            list(texts), truncation=True,
            padding="max_length", max_length=MAX_LENGTH,
            return_tensors="pt"
        )
        self.labels = torch.tensor(list(labels), dtype=torch.long)

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        return {
            "input_ids":      self.enc["input_ids"][idx],
            "attention_mask": self.enc["attention_mask"][idx],
            "labels":         self.labels[idx],
        }

train_ds = InfoCheckDataset(df_train["text"].tolist(), df_train["label"].tolist())
val_ds   = InfoCheckDataset(df_val["text"].tolist(),   df_val["label"].tolist())
test_ds  = InfoCheckDataset(df_test["text"].tolist(),  df_test["label"].tolist())
print(f"\n✅ Dataset siap: {len(train_ds)} train | {len(val_ds)} val | {len(test_ds)} test")

# =============================================
# STEP 3: MODEL — NUM_LABELS = 4
# =============================================
print("\n" + "="*50)
print("STEP 3: Load IndoBERT Model (4 kelas)")
print("="*50)

model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_NAME,
    num_labels=NUM_LABELS,   # ← KUNCI: harus 4
    id2label=ID2LABEL,
    label2id=LABEL2ID,
    ignore_mismatched_sizes=True,
)
print(f"✅ Model '{MODEL_NAME}' loaded | Num labels: {model.config.num_labels}")

# =============================================
# STEP 4: TRAINING
# =============================================
def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=-1)
    return {
        "accuracy": accuracy_score(labels, preds),
        "f1":       f1_score(labels, preds, average="weighted"),
    }

args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    eval_strategy="epoch",
    save_strategy="epoch",
    num_train_epochs=EPOCHS,
    per_device_train_batch_size=BATCH_SIZE,
    per_device_eval_batch_size=BATCH_SIZE,
    learning_rate=LR,
    weight_decay=0.01,
    load_best_model_at_end=True,
    metric_for_best_model="f1",
    logging_steps=50,
    report_to="none",
    fp16=torch.cuda.is_available(),
)

trainer = Trainer(
    model=model,
    args=args,
    train_dataset=train_ds,
    eval_dataset=val_ds,
    processing_class=tokenizer,   # transformers v5+: tokenizer → processing_class
    compute_metrics=compute_metrics,
    callbacks=[EarlyStoppingCallback(early_stopping_patience=2)],
)

print("\n" + "="*50)
print("STEP 4: Training... (estimasi 15-20 menit di T4 GPU)")
print("="*50)
trainer.train()

# =============================================
# STEP 5: EVALUASI TEST SET
# =============================================
print("\n" + "="*50)
print("STEP 5: Evaluasi pada Test Set")
print("="*50)

preds_out   = trainer.predict(test_ds)
preds       = np.argmax(preds_out.predictions, axis=-1)
true_labels = df_test["label"].tolist()

print(f"Accuracy : {accuracy_score(true_labels, preds):.4f}")
print(f"F1 (weighted): {f1_score(true_labels, preds, average='weighted'):.4f}")
print("\nClassification Report:")
print(classification_report(true_labels, preds, target_names=["Valid", "Hoaks", "Penipuan", "Netral"]))

# =============================================
# STEP 6: SIMPAN & ZIP
# =============================================
print("\n" + "="*50)
print("STEP 6: Simpan Model")
print("="*50)

trainer.save_model(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)
print(f"✅ Model disimpan ke: {OUTPUT_DIR}/")

# Verifikasi config.json sudah benar
import json
with open(f"{OUTPUT_DIR}/config.json") as f:
    cfg = json.load(f)
print(f"\nVerifikasi config.json:")
print(f"  num_labels : {cfg.get('num_labels')}")
print(f"  id2label   : {cfg.get('id2label')}")
assert len(cfg.get("id2label", {})) == 4, "ERROR: jumlah label bukan 4!"
print("✅ config.json benar — terdapat 4 kelas")

# Zip untuk download
import shutil
zip_path = shutil.make_archive(OUTPUT_DIR, "zip", ".", OUTPUT_DIR)
print(f"\n✅ ZIP siap di-download: {zip_path}")
print("→ Klik kanan file ZIP di panel Files Colab → Download")
print("→ Extract → copy semua file ke: model/indobert-infocheck-final/")
