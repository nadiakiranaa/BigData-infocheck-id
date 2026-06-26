"""
InfoCheck ID — NLP & Model Klasifikasi (Anggota 3)
Step 1: Load dataset gabungan (4-kelas)
Step 2: EDA (Exploratory Data Analysis)
Step 3: Baseline model — TF-IDF + Logistic Regression (4-Kelas)
"""

import pandas as pd
import re
import os
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, f1_score
import pickle


# =========================================================
# STEP 1: LOAD DATASET
# =========================================================
def load_dataset():
    print("=" * 60)
    print("STEP 1: Loading 4-class dataset...")
    print("=" * 60)

    dataset_path = "dataset/lakehouse/gold/final_dataset_balanced.parquet"
    if not os.path.exists(dataset_path):
        # Fallback for old architecture
        dataset_path = "dataset/final_dataset_balanced.csv"
        if not os.path.exists(dataset_path):
            print(f"Error: Dataset {dataset_path} tidak ditemukan.")
            print("Jalankan 'python scripts/prepare_dataset.py' terlebih dahulu.")
            return

    print("Memuat dataset...")
    if dataset_path.endswith('.parquet'):
        df_all = pd.read_parquet(dataset_path)
    else:
        df_all = pd.read_csv(dataset_path)
    df_all = df_all.dropna(subset=['text'])
    # drop_duplicates DIHAPUS karena Gold layer sudah bersih (Silver layer) 
    # dan duplikat di sini adalah hasil OVERSAMPLING yang disengaja.

    # Map label ke numerik: Valid -> 0, Hoaks -> 1, Penipuan -> 2, Netral -> 3
    def map_label(x):
        x_str = str(x).strip().lower()
        if x_str == 'valid':    return 0
        elif x_str in ['hoax', 'hoaks']: return 1
        elif x_str == 'penipuan': return 2
        elif x_str == 'netral': return 3
        return 0  # fallback

    df_all['label_num'] = df_all['final_label'].apply(map_label)

    print(f"Total baris setelah cleaning: {len(df_all)}")
    print("\nDistribusi label numerik (0=Valid, 1=Hoaks, 2=Penipuan, 3=Netral):")
    print(df_all['label_num'].value_counts())
    print("\nProporsi:")
    print(df_all['label_num'].value_counts(normalize=True))

    return df_all


# =========================================================
# STEP 2: EDA (Exploratory Data Analysis)
# =========================================================
def eda(df):
    print("\n" + "=" * 60)
    print("STEP 2: EDA - Exploratory Data Analysis")
    print("=" * 60)

    df['text_length'] = df['text'].astype(str).apply(len)
    print("\nStatistik panjang teks (karakter):")
    print(df['text_length'].describe())

    print("\nContoh teks VALID (label=0):")
    for t in df[df['label_num'] == 0]['text'].head(2):
        print("-", str(t)[:200], "...\n")

    print("Contoh teks HOAKS (label=1):")
    for t in df[df['label_num'] == 1]['text'].head(2):
        print("-", str(t)[:200], "...\n")

    print("Contoh teks PENIPUAN (label=2):")
    for t in df[df['label_num'] == 2]['text'].head(2):
        print("-", str(t)[:200], "...\n")

    print("Contoh teks NETRAL (label=3):")
    for t in df[df['label_num'] == 3]['text'].head(2):
        print("-", str(t)[:200], "...\n")

    return df


# =========================================================
# TEXT CLEANING (basic preprocessing)
# =========================================================
def clean_text(text):
    text = str(text).lower()
    text = re.sub(r'http\S+|www\.\S+', ' ', text)        # hapus URL
    text = re.sub(r'<.*?>', ' ', text)                    # hapus tag HTML
    text = re.sub(r'[^a-z0-9\s]', ' ', text)              # hapus karakter non-alfanumerik
    text = re.sub(r'\s+', ' ', text).strip()              # hapus spasi berlebih
    return text


# =========================================================
# STEP 3: BASELINE MODEL - TF-IDF + Logistic Regression
# =========================================================
def baseline_model(df):
    print("\n" + "=" * 60)
    print("STEP 3: Baseline Model - TF-IDF + Logistic Regression (4-Kelas)")
    print("=" * 60)

    df['text_clean'] = df['text'].apply(clean_text)

    X_train, X_test, y_train, y_test = train_test_split(
        df['text_clean'], df['label_num'],
        test_size=0.2, random_state=42, stratify=df['label_num']
    )

    print(f"\nTrain size: {len(X_train)}, Test size: {len(X_test)}")

    # TF-IDF vectorization
    vectorizer = TfidfVectorizer(max_features=10000, ngram_range=(1, 2))
    X_train_tfidf = vectorizer.fit_transform(X_train)
    X_test_tfidf = vectorizer.transform(X_test)

    # Logistic Regression (Multinomial 3-Class)
    # multi_class deprecated in sklearn >= 1.5, lbfgs handles multinomial by default
    model = LogisticRegression(max_iter=1000, class_weight='balanced', solver='lbfgs')
    model.fit(X_train_tfidf, y_train)

    # Evaluation
    y_pred = model.predict(X_test_tfidf)

    print("\n--- Hasil Evaluasi Baseline ---")
    print(f"Accuracy : {accuracy_score(y_test, y_pred):.4f}")
    print(f"\nF1-score (weighted): {f1_score(y_test, y_pred, average='weighted'):.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=['Valid', 'Hoaks', 'Penipuan', 'Netral']))
    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, y_pred))

    # Save model & vectorizer
    with open('baseline_model.pkl', 'wb') as f:
        pickle.dump({'model': model, 'vectorizer': vectorizer}, f)
    print("\nModel baseline 4-kelas disimpan ke 'baseline_model.pkl'")

    return model, vectorizer


# =========================================================
# MAIN
# =========================================================
if __name__ == "__main__":
    df = load_dataset()
    df = eda(df)
    model, vectorizer = baseline_model(df)

    print("\n" + "=" * 60)
    print("SELESAI. Model baseline berhasil di-upgrade ke 4-kelas.")
    print("=" * 60)