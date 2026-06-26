import pandas as pd
import urllib.request
import os
import glob
from io import StringIO
import random

# =====================================================================
# SYNTHETIC DATA TEMPLATES
# =====================================================================
SCAM_TEMPLATES = [
    "Paket anda telah tiba di gudang, silakan cek resi pengiriman anda melalui link berikut: {link} (J&T Express)",
    "Bro, ini aku {nama1}. Nomor lama aku hilang. Lagi butuh dana darurat buat bayar RS, bisa transferin dulu {nominal} ke {bank} {rekening} a/n {nama2}?",
    "INFO RESMI {bank}: Akun Anda akan diblokir dalam 24 jam karena aktivitas mencurigakan. Hubungi CS kami segera di {no_hp} untuk verifikasi",
    "PROFIT HARIAN DIJAMIN! Titipkan dana Rp {nominal}, dapat return 30% per hari. Sudah 5000+ member aktif. Hubungi: {link}",
    "JUAL TIKET {item}! Harga jauh di bawah pasaran. Stok terbatas! DM sekarang, bayar DP 50% via GoPay {no_hp}",
    "SELAMAT! Anda terpilih sebagai pemenang Gebyar {brand} 12.12! Hadiah {item} menanti. Klaim sebelum 24 jam: {link}",
]

NEUTRAL_TEMPLATES = [
    "Promo akhir bulan {brand}! Diskon hingga 50% untuk semua produk. Belanja sekarang di aplikasi atau toko terdekat.",
    "Selamat ulang tahun {nama1}! Semoga sehat selalu dan sukses di tahun ini.",
    "Lagi macet di jalan tol Jakarta-Cikampek arah Bandung. Ada yang tau info terbaru?",
    "Info: Jadwal KRL Commuter Line hari Minggu berubah mulai pekan depan. Cek aplikasi KAI Access.",
    "Pengumuman: Kantor kami akan tutup pada tanggal 17 Agustus dalam rangka Hari Kemerdekaan RI.",
    "Menurut saya kebijakan ini perlu dikaji lebih lanjut sebelum diterapkan secara luas.",
]

KOTA_LIST = ["Jakarta", "Bandung", "Surabaya", "Medan", "Yogyakarta"]
JALAN_LIST = ["Jagorawi", "JORR", "Cipali", "Pantura"]
JALUR_ALT_LIST = ["Jalan Alternatif Sentul", "Jalan Tol Dalam Kota"]
KOTA2_LIST = ["Surabaya", "Semarang", "Malang"]
BANKS = ["BCA", "Mandiri", "BRI", "BNI", "BSI"]
NOMINALS = ["500rb", "1jt", "2jt", "5jt", "10jt"]
NAMES = ["Dani", "Siti", "Budi", "Sari", "Andi", "Dewi"]
LINKS = ["bit.ly/cekpaket-jnt2026", "wa.me/6281299998888", "bit.ly/shopee-winner-resmi"]
ITEMS = ["Coldplay Jakarta", "Taylor Swift SG", "iPhone 16 Pro Max"]
BRANDS = ["Shopee", "Tokopedia", "Lazada", "Gojek", "Grab"]

def generate_synthetic_scams(n=3000):
    random.seed(42)
    data = []
    for _ in range(n):
        tpl = random.choice(SCAM_TEMPLATES)
        text = tpl.format(
            bank=random.choice(BANKS), nominal=random.choice(NOMINALS),
            nama1=random.choice(NAMES), nama2=random.choice([n for n in NAMES if n != NAMES]),
            rekening="".join([str(random.randint(0, 9)) for _ in range(10)]),
            no_hp="08" + "".join([str(random.randint(0, 9)) for _ in range(9)]),
            link=random.choice(LINKS), item=random.choice(ITEMS), brand=random.choice(BRANDS)
        )
        data.append({"text": text, "label_raw": "Penipuan", "source": "synthetic_scam"})
    return pd.DataFrame(data)

def generate_synthetic_neutral(n=3000):
    random.seed(99)
    data = []
    for _ in range(n):
        tpl = random.choice(NEUTRAL_TEMPLATES)
        text = tpl.replace("{kota}", random.choice(KOTA_LIST)).replace("{nama1}", random.choice(NAMES))\
                  .replace("{nominal}", random.choice(NOMINALS)).replace("{item}", random.choice(ITEMS))\
                  .replace("{brand}", random.choice(BRANDS))
        data.append({"text": text, "label_raw": "Netral", "source": "synthetic_neutral"})
    return pd.DataFrame(data)

# =====================================================================
# DATA LAKEHOUSE: BRONZE LAYER (RAW DATA)
# =====================================================================
def process_bronze():
    print("\n" + "="*50)
    print("Mengeksekusi BRONZE LAYER (Raw Data Extraction)")
    print("="*50)
    
    os.makedirs("dataset/lakehouse/bronze", exist_ok=True)
    
    # 1. SMS Spam
    url = "https://raw.githubusercontent.com/Andikazidanef15/Sentiment-Analysis-on-Indonesian-SMS-Dataset/main/dataset_sms_spam_v1.csv"
    try:
        req = urllib.request.urlopen(url)
        df_sms = pd.read_csv(StringIO(req.read().decode('utf-8')))
    except Exception:
        df_sms = pd.read_csv("dataset/dataset_sms_spam_v1.csv") if os.path.exists("dataset/dataset_sms_spam_v1.csv") else pd.DataFrame()
    
    if not df_sms.empty:
        df_sms['source'] = 'sms_spam_v1'
        df_sms.to_parquet("dataset/lakehouse/bronze/sms_data.parquet", index=False)
        print("[OK] Disimpan ke Bronze: sms_data.parquet")

    # 2. Kaggle Cleaned
    kaggle_files = glob.glob(os.path.join("dataset", "kaggle", "Cleaned", "*.xlsx"))
    kaggle_dfs = []
    for file in kaggle_files:
        df_k = pd.read_excel(file)
        df_k['source'] = f"kaggle_{os.path.basename(file)}"
        kaggle_dfs.append(df_k)
    
    if kaggle_dfs:
        pd.concat(kaggle_dfs).astype(str).to_parquet("dataset/lakehouse/bronze/kaggle_data.parquet", index=False)
        print("[OK] Disimpan ke Bronze: kaggle_data.parquet")

    # 3. Synthetic Data
    df_syn = pd.concat([generate_synthetic_scams(3000), generate_synthetic_neutral(3000)])
    df_syn.to_parquet("dataset/lakehouse/bronze/synthetic_data.parquet", index=False)
    print("[OK] Disimpan ke Bronze: synthetic_data.parquet")
    
    # 4. Komdigi (Opsional)
    komdigi_path = os.path.join("dataset", "komdigi", "komdigi_hoaks_latest.csv")
    if os.path.exists(komdigi_path):
        df_k = pd.read_csv(komdigi_path)
        df_k['source'] = 'komdigi_api'
        df_k.to_parquet("dataset/lakehouse/bronze/komdigi_data.parquet", index=False)
        print("[OK] Disimpan ke Bronze: komdigi_data.parquet")

    # 5. Vijayandika Turnbackhoax
    raw_dir = os.path.join("dataset", "kaggle", "RAW")
    csv_files = glob.glob(os.path.join(raw_dir, "turnbackhoax.csv")) + glob.glob(os.path.join(raw_dir, "vijayandika*.csv"))
    dfs_v = []
    for fpath in csv_files:
        try:
            df_v = pd.read_csv(fpath, encoding='utf-8', on_bad_lines='skip')
            df_v['source'] = f"vijayandika_{os.path.basename(fpath)}"
            dfs_v.append(df_v)
        except:
            pass
    if dfs_v:
        pd.concat(dfs_v).astype(str).to_parquet("dataset/lakehouse/bronze/vijayandika_data.parquet", index=False)
        print("[OK] Disimpan ke Bronze: vijayandika_data.parquet")

    # 6. OCR Screenshot (Opsional)
    import json
    ocr_path = os.path.join("dataset", "ocr_results.json")
    if os.path.exists(ocr_path):
        with open(ocr_path, 'r', encoding='utf-8') as f:
            ocr_data = json.load(f)
        
        rows = []
        for item in ocr_data:
            text = item.get('text', '').strip()
            kategori = item.get('kategori', '').upper()
            if text and kategori == 'PENIPUAN':
                rows.append({'text': text, 'final_label': 'Penipuan', 'source': 'ocr_screenshot'})
        
        if rows:
            df_ocr = pd.DataFrame(rows)
            df_ocr.to_parquet("dataset/lakehouse/bronze/ocr_data.parquet", index=False)
            print("[OK] Disimpan ke Bronze: ocr_data.parquet")


# =====================================================================
# DATA LAKEHOUSE: SILVER LAYER (CLEANED & STANDARDIZED)
# =====================================================================
def process_silver():
    print("\n" + "="*50)
    print("Mengeksekusi SILVER LAYER (Data Cleaning & Standardization)")
    print("="*50)
    
    os.makedirs("dataset/lakehouse/silver", exist_ok=True)
    
    all_cleaned_dfs = []
    
    # 1. Clean SMS
    if os.path.exists("dataset/lakehouse/bronze/sms_data.parquet"):
        df = pd.read_parquet("dataset/lakehouse/bronze/sms_data.parquet")
        # label 0=Normal (Netral), 1=Penipuan, 2=Promo (Netral)
        # Kita ubah 0 menjadi Netral (sebelumnya Valid), agar Valid KHUSUS untuk Berita Fakta
        label_map = {0: "Netral", 1: "Penipuan", 2: "Netral"}
        if 'label' in df.columns:
            df['final_label'] = df['label'].map(label_map)
            df = df.rename(columns={'Teks': 'text'})
            all_cleaned_dfs.append(df[['text', 'final_label', 'source']].dropna())
            print("[OK] Memproses Silver: SMS Data")

    # 2. Clean Kaggle
    if os.path.exists("dataset/lakehouse/bronze/kaggle_data.parquet"):
        df = pd.read_parquet("dataset/lakehouse/bronze/kaggle_data.parquet")
        # Gabungkan kolom teks yang terpisah akibat pd.concat
        text_cols = [c for c in ['text_new', 'Clean Narasi', 'FullText'] if c in df.columns]
        if text_cols:
            df['text'] = df[text_cols].bfill(axis=1).iloc[:, 0]
            
            def map_kaggle_label(x):
                try:
                    return "Hoaks" if int(float(x)) == 1 else "Valid"
                except:
                    return "Valid"
            df['final_label'] = df['hoax'].apply(map_kaggle_label)
            all_cleaned_dfs.append(df[['text', 'final_label', 'source']].dropna())
            print("[OK] Memproses Silver: Kaggle Data")
            
    # 3. Clean Synthetic
    if os.path.exists("dataset/lakehouse/bronze/synthetic_data.parquet"):
        df = pd.read_parquet("dataset/lakehouse/bronze/synthetic_data.parquet")
        df['final_label'] = df['label_raw']
        all_cleaned_dfs.append(df[['text', 'final_label', 'source']].dropna())
        print("[OK] Memproses Silver: Synthetic Data")
        
    # 4. Clean Komdigi
    if os.path.exists("dataset/lakehouse/bronze/komdigi_data.parquet"):
        df = pd.read_parquet("dataset/lakehouse/bronze/komdigi_data.parquet")
        df['text'] = df.apply(lambda r: f"{r.get('title', '')}. {r.get('body_text', '')}".strip(), axis=1)
        df['final_label'] = 'Hoaks'
        all_cleaned_dfs.append(df[['text', 'final_label', 'source']].dropna())
        print("[OK] Memproses Silver: Komdigi Data")

    # 5. Clean Vijayandika
    if os.path.exists("dataset/lakehouse/bronze/vijayandika_data.parquet"):
        df = pd.read_parquet("dataset/lakehouse/bronze/vijayandika_data.parquet")
        text_col = None
        for candidate in ['content', 'narasi', 'text', 'body', 'judul', 'title', 'Narasi', 'Content']:
            if candidate in df.columns: text_col = candidate; break
        if not text_col: text_col = df.columns[0]
        
        df = df.rename(columns={text_col: 'text'})
        df['final_label'] = 'Hoaks'
        if 'source' not in df.columns:
             df['source'] = 'vijayandika'
        all_cleaned_dfs.append(df[['text', 'final_label', 'source']].dropna())
        print("[OK] Memproses Silver: Vijayandika Data")
        
    # 6. Clean OCR
    if os.path.exists("dataset/lakehouse/bronze/ocr_data.parquet"):
        df = pd.read_parquet("dataset/lakehouse/bronze/ocr_data.parquet")
        # Label sudah 'Penipuan' dari proses bronze
        all_cleaned_dfs.append(df[['text', 'final_label', 'source']].dropna())
        print("[OK] Memproses Silver: OCR Data")

    # Gabungkan semua data bersih
    df_silver = pd.concat(all_cleaned_dfs, ignore_index=True)
    df_silver['text'] = df_silver['text'].astype(str)
    
    # Cleaning tahap akhir (drop duplikat & data terlalu pendek)
    df_silver = df_silver.drop_duplicates(subset=['text'])
    df_silver = df_silver[df_silver['text'].str.len() > 30]
    
    # Save to Silver Layer
    df_silver.to_parquet("dataset/lakehouse/silver/cleaned_dataset.parquet", index=False)
    print(f"\n[OK] Total Baris Silver Layer: {len(df_silver)}")
    print("Distribusi Label:")
    print(df_silver['final_label'].value_counts())

# =====================================================================
# DATA LAKEHOUSE: GOLD LAYER (BUSINESS-READY / BALANCED)
# =====================================================================
def process_gold():
    print("\n" + "="*50)
    print("Mengeksekusi GOLD LAYER (Aggregation & Balancing)")
    print("="*50)
    
    os.makedirs("dataset/lakehouse/gold", exist_ok=True)
    
    df_silver = pd.read_parquet("dataset/lakehouse/silver/cleaned_dataset.parquet")
    
    TARGET_PER_CLASS = 3000
    balanced_parts = []

    for label, group in df_silver.groupby('final_label'):
        n_available = len(group)
        if n_available >= TARGET_PER_CLASS:
            # Undersampling
            sampled = group.sample(n=TARGET_PER_CLASS, random_state=42)
        else:
            # Oversampling
            sampled = group.sample(n=TARGET_PER_CLASS, replace=True, random_state=42)
        balanced_parts.append(sampled)

    df_gold = pd.concat(balanced_parts, ignore_index=True).sample(frac=1, random_state=42).reset_index(drop=True)
    
    # Save to Gold Layer
    df_gold.to_parquet("dataset/lakehouse/gold/final_dataset_balanced.parquet", index=False)
    
    # Also save as CSV as a fallback for backwards compatibility if needed
    df_gold.to_csv("dataset/final_dataset_balanced.csv", index=False)
    
    print("[OK] Berhasil menyimpan Gold Layer Data (Parquet & CSV Fallback)")
    print(f"\nTotal dataset gold (ready for training): {len(df_gold)} baris")
    print("Distribusi Kelas:")
    print(df_gold['final_label'].value_counts())

if __name__ == "__main__":
    print("Memulai Pembangunan Data Lakehouse (Medallion Architecture)...")
    process_bronze()
    process_silver()
    process_gold()
    print("\n=======================================================")
    print("Data Lakehouse sukses dibangun! Silakan periksa folder dataset/lakehouse/")
    print("=======================================================")
