"""
InfoCheck ID — Modul Similarity-to-Komdigi (Anggota 3)
Mencari artikel hoaks terverifikasi Komdigi yang paling mirip dengan
teks input, untuk dijadikan "alasan" pada output prediksi.
"""

import re
import pickle
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


KOMDIGI_CSV = 'dataset/komdigi/komdigi_hoaks.csv'
INDEX_PATH = 'komdigi_index.pkl'


def clean_text(text):
    text = str(text).lower()
    text = re.sub(r'<.*?>', ' ', text)               # hapus tag HTML
    text = re.sub(r'http\S+|www\.\S+', ' ', text)    # hapus URL
    text = re.sub(r'&nbsp;|&amp;|&quot;', ' ', text) # hapus HTML entities umum
    text = re.sub(r'[^a-z0-9\s]', ' ', text)         # hapus karakter non-alfanumerik
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def build_index():
    """Bangun TF-IDF index dari database hoaks Komdigi. Jalankan sekali saja."""
    print("Loading database hoaks Komdigi...")
    df = pd.read_csv(KOMDIGI_CSV)

    # Gunakan title + excerpt/body_text untuk representasi tiap hoaks
    df['combined_text'] = (
        df['title'].fillna('') + ' ' + df['body_text'].fillna('')
    )
    df['combined_clean'] = df['combined_text'].apply(clean_text)

    df = df.dropna(subset=['combined_clean'])
    df = df[df['combined_clean'].str.len() > 0].reset_index(drop=True)

    print(f"Total artikel Komdigi: {len(df)}")

    vectorizer = TfidfVectorizer(max_features=20000, ngram_range=(1, 2))
    tfidf_matrix = vectorizer.fit_transform(df['combined_clean'])

    index_data = {
        'vectorizer': vectorizer,
        'tfidf_matrix': tfidf_matrix,
        'titles': df['title'].tolist(),
        'urls': df['url'].tolist() if 'url' in df.columns else [''] * len(df),
        'categories': df['category'].tolist() if 'category' in df.columns else [''] * len(df),
    }

    with open(INDEX_PATH, 'wb') as f:
        pickle.dump(index_data, f)

    print(f"Index tersimpan ke '{INDEX_PATH}'")
    return index_data


def load_index():
    with open(INDEX_PATH, 'rb') as f:
        return pickle.load(f)


def find_similar_komdigi(text, index_data=None, top_k=1, threshold=0.50):
    """
    Cari artikel hoaks Komdigi paling mirip dengan teks input.

    Returns:
        list of dict: [{'title': ..., 'url': ..., 'category': ..., 'similarity': ...}, ...]
        Kosong list kalau tidak ada yang melewati threshold.
    """
    if index_data is None:
        index_data = load_index()

    text_clean = clean_text(text)
    vectorizer = index_data['vectorizer']
    tfidf_matrix = index_data['tfidf_matrix']

    text_vec = vectorizer.transform([text_clean])
    similarities = cosine_similarity(text_vec, tfidf_matrix)[0]

    top_indices = similarities.argsort()[::-1][:top_k]

    results = []
    for idx in top_indices:
        score = float(similarities[idx])
        if score >= threshold:
            results.append({
                'title': index_data['titles'][idx],
                'url': index_data['urls'][idx],
                'category': index_data['categories'][idx],
                'similarity': round(score, 4),
            })

    return results


def get_reason(text, index_data=None, top_k=1, threshold=0.50):
    """
    Bangun string 'alasan' siap pakai untuk output API.

    Returns:
        str: alasan singkat
    """
    matches = find_similar_komdigi(text, index_data, top_k, threshold)

    if matches:
        best = matches[0]
        pct = round(best['similarity'] * 100, 1)
        return f"Mirip dengan hoaks terverifikasi Komdigi ({pct}%): \"{best['title']}\""

    return "Tidak ditemukan kecocokan dengan database hoaks Komdigi. Penilaian berdasarkan klasifikasi model."


if __name__ == "__main__":
    # Bangun index sekali
    index_data = build_index()

    # Contoh tes
    sample_texts = [
        "Dapatkan bantuan presiden Prabowo sebesar 5 juta rupiah sekarang juga dengan klik link ini!",
        "Pertumbuhan ekonomi Indonesia tercatat 5,12% pada kuartal pertama 2026 menurut data BPS.",
        "Akan terjadi pemadaman listrik global selama 9 hari mulai 18 Juli 2026 di seluruh dunia.",
    ]

    print("\n--- Tes pencarian similarity ---")
    for t in sample_texts:
        print(f"\nInput: {t[:80]}...")
        print("Alasan:", get_reason(t, index_data))