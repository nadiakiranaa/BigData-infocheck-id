"""
InfoCheck ID — NLP & Model Klasifikasi (Anggota 3)
Step 1: Load dataset gabungan
Step 2: EDA (Exploratory Data Analysis)
Step 3: Baseline model — TF-IDF + Logistic Regression
"""

import pandas as pd
import re
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
    print("STEP 1: Loading dataset...")
    print("=" * 60)

    df_hoax = pd.read_excel('dataset/kaggle/Cleaned/dataset_turnbackhoax_10_cleaned.xlsx')
    df_hoax = df_hoax[['Clean Narasi', 'hoax']].rename(columns={'Clean Narasi': 'text'})

    df_cnn = pd.read_excel('dataset/kaggle/Cleaned/dataset_cnn_10k_cleaned.xlsx')
    df_cnn = df_cnn[['text_new', 'hoax']].rename(columns={'text_new': 'text'})

    df_kompas = pd.read_excel('dataset/kaggle/Cleaned/dataset_kompas_4k_cleaned.xlsx')
    df_kompas = df_kompas[['text_new', 'hoax']].rename(columns={'text_new': 'text'})

    df_tempo = pd.read_excel('dataset/kaggle/Cleaned/dataset_tempo_6k_cleaned.xlsx')
    df_tempo = df_tempo[['text_new', 'hoax']].rename(columns={'text_new': 'text'})

    df_komdigi = pd.read_csv('dataset/komdigi/komdigi_hoaks.csv')
    df_komdigi = df_komdigi[['body_text']].rename(columns={'body_text': 'text'})
    df_komdigi['hoax'] = 1

    df_all = pd.concat([df_hoax, df_cnn, df_kompas, df_tempo, df_komdigi], ignore_index=True)
    df_all = df_all.dropna(subset=['text'])
    df_all = df_all.drop_duplicates(subset=['text'])
    df_all['hoax'] = df_all['hoax'].astype(int)

    print(f"Total baris setelah cleaning: {len(df_all)}")
    print("\nDistribusi label (0=valid, 1=hoaks):")
    print(df_all['hoax'].value_counts())
    print("\nProporsi:")
    print(df_all['hoax'].value_counts(normalize=True))

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

    print("\nContoh teks HOAKS (label=1):")
    for t in df[df['hoax'] == 1]['text'].head(2):
        print("-", str(t)[:200], "...\n")

    print("Contoh teks VALID (label=0):")
    for t in df[df['hoax'] == 0]['text'].head(2):
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
    print("STEP 3: Baseline Model - TF-IDF + Logistic Regression")
    print("=" * 60)

    df['text_clean'] = df['text'].apply(clean_text)

    X_train, X_test, y_train, y_test = train_test_split(
        df['text_clean'], df['hoax'],
        test_size=0.2, random_state=42, stratify=df['hoax']
    )

    print(f"\nTrain size: {len(X_train)}, Test size: {len(X_test)}")

    # TF-IDF vectorization
    vectorizer = TfidfVectorizer(max_features=10000, ngram_range=(1, 2))
    X_train_tfidf = vectorizer.fit_transform(X_train)
    X_test_tfidf = vectorizer.transform(X_test)

    # Logistic Regression
    model = LogisticRegression(max_iter=1000, class_weight='balanced')
    model.fit(X_train_tfidf, y_train)

    # Evaluation
    y_pred = model.predict(X_test_tfidf)

    print("\n--- Hasil Evaluasi Baseline ---")
    print(f"Accuracy : {accuracy_score(y_test, y_pred):.4f}")
    print(f"F1-score : {f1_score(y_test, y_pred):.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=['Valid', 'Hoaks']))
    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, y_pred))

    # Save model & vectorizer for later use / comparison table
    with open('baseline_model.pkl', 'wb') as f:
        pickle.dump({'model': model, 'vectorizer': vectorizer}, f)
    print("\nModel baseline disimpan ke 'baseline_model.pkl'")

    return model, vectorizer


# =========================================================
# MAIN
# =========================================================
if __name__ == "__main__":
    df = load_dataset()
    df = eda(df)
    model, vectorizer = baseline_model(df)

    print("\n" + "=" * 60)
    print("SELESAI. Selanjutnya: fine-tuning IndoBERT (lihat tahap berikutnya).")
    print("=" * 60)