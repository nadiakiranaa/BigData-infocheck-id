import pandas as pd
import urllib.request
import os
import glob
from io import StringIO
import random

# Templates for Scam Data Augmentation
SCAM_TEMPLATES = [
    # APK/Malware
    "Paket anda telah tiba di gudang, silakan cek resi pengiriman anda melalui link berikut: {link} (J&T Express)",
    "Undangan pernikahan digital kami: silakan download file APK berikut untuk melihat detail acara pernikahan {nama1} & {nama2}",
    "SURAT TILANG ELEKTRONIK - Kendaraan anda terekam melanggar lampu merah. Bayar denda via link: {link}",
    "Tagihan listrik PLN anda bulan ini: Rp {nominal}. Segera bayar sebelum diputus. Download aplikasi cek tagihan: {link}",
    "Konfirmasi tagihan BPJS Kesehatan Anda untuk periode ini. Mohon unduh aplikasi BPJS mobile lewat link: {link} untuk verifikasi tagihan Anda.",
    # Impersonation
    "Bro, ini aku {nama1}. Nomor lama aku hilang. Lagi butuh dana darurat buat bayar RS, bisa transferin dulu {nominal} ke {bank} {rekening} a/n {nama2}?",
    "Mama minta tolong transfer dulu ya, mama lagi di RS dan dompet ketinggalan. Transfer ke {bank} {rekening} a/n {nama1}. Nanti mama ganti",
    "Halo ini {nama1}, akun lama saya di-hack. Tolong pinjam dulu {nominal} buat bayar tagihan mendesak. Transfer ke e-wallet {no_hp} ya, urgent!",
    # Fake CS Bank
    "INFO RESMI {bank}: Akun Anda akan diblokir dalam 24 jam karena aktivitas mencurigakan. Hubungi CS kami segera di {no_hp} untuk verifikasi",
    "Yth Nasabah {bank}, kartu ATM Anda terdeteksi digunakan di luar kota. Untuk keamanan segera hubungi {no_hp} dan sebutkan PIN Anda",
    "{bank} PRIORITAS: Anda terpilih upgrade kartu GOLD gratis! Konfirmasi data via link: {link} dan masukkan no rekening + PIN",
    "Pemberitahuan perubahan tarif transaksi bulanan {bank} menjadi Rp 150.000/bulan. Setuju/Tidak silakan klik: {link}",
    # Investasi Bodong / Pinjol
    "PROFIT HARIAN DIJAMIN! Titipkan dana Rp {nominal}, dapat return 30% per hari. Sudah 5000+ member aktif. Hubungi: {link}",
    "Pinjol legal cair 5 menit! Tanpa BI checking, tanpa agunan. Limit sampai {nominal}. Daftar sekarang: {link}",
    "Jasa joki pinjol aman terpercaya, pasti cair meskipun data busuk! Fee setelah cair. Minat chat WA: {no_hp}",
    # Tiket Palsu
    "JUAL TIKET {item}! Harga jauh di bawah pasaran. Stok terbatas! DM sekarang, bayar DP 50% via GoPay {no_hp}",
    "Jastip tiket {item}! Terpercaya sudah 100+ pembeli. DP {nominal} dulu ya kak, sisanya H-1 konser. WA: {no_hp}",
    # Olshop Fiktif
    "MURAH BANGET! {item} hanya {nominal}! Stok terbatas, transfer dulu ke {bank} {rekening} a/n Toko Gadget Murah. NO COD",
    "Flash sale cuci gudang {item} diskon 70% hanya hari ini! Hubungi admin fast respon lewat wa.me/{no_hp} (Toko Amanah)",
    # Giveaway Palsu
    "SELAMAT! Anda terpilih sebagai pemenang Gebyar {brand} 12.12! Hadiah {item} menanti. Klaim sebelum 24 jam: {link}",
    "Raffi Ahmad bagi-bagi uang Rp {nominal} untuk 100 orang! Daftar via link: {link} sebelum kuota habis!"
]

NEUTRAL_TEMPLATES = [
    # Promosi toko resmi / iklan legal
    "Promo akhir bulan {brand}! Diskon hingga 50% untuk semua produk. Belanja sekarang di aplikasi atau toko terdekat.",
    "Flash sale {item} di {brand} mulai jam 12 siang! Yuk segera checkout sebelum kehabisan.",
    "Hai kak! Ada promo spesial hari ini di toko kami. Cek katalog terbaru ya, banyak pilihan menarik!",
    "Nikmati cashback {nominal} untuk pembelian pertama di aplikasi {brand}. Berlaku sampai akhir bulan ini.",
    "{brand} menghadirkan program loyalitas baru! Kumpulkan poin dari setiap transaksi dan tukar dengan hadiah menarik.",
    "Dapatkan gratis ongkir tanpa minimum pembelian di {brand} hari ini saja!",
    "Weekend sale di {brand}! Hemat sampai 70% untuk kategori {item} pilihan.",
    # Ucapan dan sosial biasa
    "Selamat ulang tahun {nama1}! Semoga sehat selalu dan sukses di tahun ini.",
    "Selamat ya {nama1} atas pencapaiannya! Kerja keras selalu membuahkan hasil.",
    "Happy anniversary buat {nama1} dan keluarga, semoga selalu bahagia dan diberikan keberkahan.",
    "Met pagi semuanya! Semangat menjalani hari ini ya, jangan lupa sarapan dulu.",
    "Alhamdulillah hari ini cuaca cerah, cocok buat olahraga pagi. Selamat berakhir pekan!",
    # Konten media sosial biasa
    "Lagi macet di jalan tol Jakarta-Cikampek arah Bandung. Ada yang tau info terbaru?",
    "Rekomendasi restoran enak di {kota} dong, lagi mau liburan akhir pekan ini!",
    "Baru selesai nonton {item}, filmnya bagus banget. Recommended deh!",
    "Cuaca hari ini panas banget ya, jaga kesehatan teman-teman semua!",
    "Nongkrong di mana ya yang enak dan adem di {kota}? Rekomendasinya dong gaes!",
    "Baru nyoba {item} terbaru, kualitasnya lumayan bagus untuk harganya. Worth it deh.",
    "Ada yang punya rekomendasi kursus atau les online yang bagus untuk belajar programming?",
    "Lagi cari apartemen di {kota}, budget sekitar {nominal}/bulan. Ada yang tau listing bagus?",
    # Informasi transportasi / layanan publik
    "Info: Jadwal KRL Commuter Line hari Minggu berubah mulai pekan depan. Cek aplikasi KAI Access.",
    "Update lalu lintas: Tol {jalan} arah {kota} terpantau padat merayap pagi ini. Alternatif lewat {jalur_alt}.",
    "Mulai hari ini {brand} melayani rute baru {kota}-{kota2}. Pesan tiket sekarang!",
    "Pelabuhan Merak akan beroperasi 24 jam selama musim libur panjang bulan ini.",
    "Reminder: Perpanjang SIM dan STNK bisa dilakukan secara online di aplikasi Digital Korlantas Polri.",
    # Pengumuman dan informasi umum
    "Pengumuman: Kantor kami akan tutup pada tanggal 17 Agustus dalam rangka Hari Kemerdekaan RI.",
    "Reminder: Batas pembayaran PBB adalah akhir bulan ini. Bayar di kantor pos atau m-banking.",
    "Ujian nasional diganti dengan asesmen kompetensi minimum mulai tahun ini. Info detail ada di situs Kemdikbud.",
    "Pemerintah membuka pendaftaran beasiswa LPDP tahap 2 mulai bulan depan. Cek syaratnya di lpdp.kemenkeu.go.id.",
    "Lowongan CPNS 2026 dibuka bulan ini untuk formasi tenaga kesehatan, guru, dan teknis. Info di sscasn.bkn.go.id.",
    # Opini dan komentar netral
    "Menurut saya kebijakan ini perlu dikaji lebih lanjut sebelum diterapkan secara luas.",
    "Semua pihak harus duduk bersama untuk mencari solusi terbaik atas permasalahan ini.",
    "Harga bahan pokok memang naik, tapi semoga pemerintah bisa segera mengatasi hal ini.",
    "Saya rasa infrastruktur digital di daerah perlu terus ditingkatkan agar lebih merata.",
    "Penting banget buat generasi muda belajar literasi keuangan sejak dini.",
    "Debat soal kebijakan energi ini memang kompleks, ada trade-off antara ekonomi dan lingkungan.",
    "Kalau menurut saya, transparansi dalam proses lelang proyek pemerintah harus lebih ditingkatkan.",
    # Berita ringan / lifestyle
    "Tren gaya hidup sehat semakin populer di kalangan anak muda. Banyak kafe sekarang menyediakan menu vegan.",
    "Film {item} berhasil meraih penghargaan di festival internasional. Selamat buat tim produksinya!",
    "Tim nasional Indonesia U-23 berhasil lolos ke babak selanjutnya. Semangat Garuda!",
    "Musim hujan telah tiba di sebagian besar wilayah Jawa. Jangan lupa siapkan payung saat keluar rumah.",
    "Pameran seni internasional akan digelar di Jakarta bulan depan. Sayang banget kalau dilewatin.",
]

KOTA_LIST = ["Jakarta", "Bandung", "Surabaya", "Medan", "Yogyakarta", "Semarang", "Makassar", "Bali", "Palembang"]
JALAN_LIST = ["Jagorawi", "JORR", "Cipali", "Pantura", "Lingkar Luar"]
JALUR_ALT_LIST = ["Jalan Alternatif Sentul", "Jalan Poros Tengah", "Jalur Arteri", "Jalan Tol Dalam Kota"]
KOTA2_LIST = ["Surabaya", "Semarang", "Malang", "Yogyakarta", "Solo"]

BANKS = ["BCA", "Mandiri", "BRI", "BNI", "Danamon", "CIMB Niaga", "BSI"]
NOMINALS = ["500rb", "1jt", "1.5jt", "2jt", "3jt", "5jt", "10jt", "50jt"]
NAMES = ["Dani", "Siti", "Budi", "Sari", "Andi", "Dewi", "Eko", "Mega", "Rian", "Tono", "Joko", "Rini", "Ahmad"]
LINKS = [
    "bit.ly/cekpaket-jnt2026", "bit.ly/undangan-nikah-digital", "bit.ly/tilang-etle-2026", 
    "wa.me/6281299998888", "bit.ly/bri-upgrade-gold", "bit.ly/shopee-winner-resmi",
    "bit.ly/click-disini-update", "t.me/pinjol_cepat_cair", "bit.ly/tarif-bca-baru"
]
ITEMS = ["Coldplay Jakarta", "Taylor Swift SG", "Bruno Mars JKT", "iPhone 16 Pro Max", "iPad Pro M4", "Laptop Asus ROG"]
BRANDS = ["Shopee", "Tokopedia", "Lazada", "Gojek", "Grab", "Baim Wong"]

def generate_synthetic_scams(n=1500):
    """Generasi data penipuan sintetis berdasarkan template dengan random values"""
    random.seed(42)
    synthetic_data = []
    for _ in range(n):
        tpl = random.choice(SCAM_TEMPLATES)
        text = tpl.format(
            bank=random.choice(BANKS),
            nominal=random.choice(NOMINALS),
            nama1=random.choice(NAMES),
            nama2=random.choice([n for n in NAMES if n != NAMES]),
            rekening="".join([str(random.randint(0, 9)) for _ in range(10)]),
            no_hp="08" + "".join([str(random.randint(0, 9)) for _ in range(9)]),
            link=random.choice(LINKS),
            item=random.choice(ITEMS),
            brand=random.choice(BRANDS)
        )
        synthetic_data.append({"text": text, "final_label": "Penipuan"})
    return pd.DataFrame(synthetic_data)

def generate_synthetic_neutral(n=1500):
    """Generasi data Netral sintetis dari template konten sehari-hari"""
    random.seed(99)
    synthetic_data = []
    for _ in range(n):
        tpl = random.choice(NEUTRAL_TEMPLATES)
        text = tpl.replace("{kota}", random.choice(KOTA_LIST))\
                  .replace("{kota2}", random.choice(KOTA2_LIST))\
                  .replace("{jalan}", random.choice(JALAN_LIST))\
                  .replace("{jalur_alt}", random.choice(JALUR_ALT_LIST))\
                  .replace("{nama1}", random.choice(NAMES))\
                  .replace("{nominal}", random.choice(NOMINALS))\
                  .replace("{item}", random.choice(ITEMS))\
                  .replace("{brand}", random.choice(BRANDS))
        synthetic_data.append({"text": text, "final_label": "Netral"})
    return pd.DataFrame(synthetic_data)

def main():
    print("Mendownload dataset SMS Spam...")
    url = "https://raw.githubusercontent.com/Andikazidanef15/Sentiment-Analysis-on-Indonesian-SMS-Dataset/main/dataset_sms_spam_v1.csv"
    try:
        req = urllib.request.urlopen(url)
        csv_data = req.read().decode('utf-8')
        # Read SMS dataset
        df_sms = pd.read_csv(StringIO(csv_data))
    except Exception as e:
        print(f"Gagal download SMS Spam secara online: {e}. Menggunakan fallback lokal jika ada.")
        # fallback to local file if available
        if os.path.exists("dataset/dataset_sms_spam_v1.csv"):
            df_sms = pd.read_csv("dataset/dataset_sms_spam_v1.csv")
        else:
            df_sms = pd.DataFrame(columns=['Teks', 'label'])
    
    df_sms_final = pd.DataFrame(columns=['text', 'final_label'])
    if not df_sms.empty:
        # Filter SMS dataset:
        # label 0 = Normal → Valid
        # label 1 = Fraud  → Penipuan
        # label 2 = Promo  → Netral (sebelumnya dibuang, sekarang dipakai!)
        df_sms_filtered = df_sms[df_sms['label'].isin([0, 1, 2])].copy()

        def map_sms_label(x):
            if x == 0: return "Valid"
            if x == 1: return "Penipuan"
            return "Netral"  # label 2 = Promo

        df_sms_filtered['final_label'] = df_sms_filtered['label'].apply(map_sms_label)
        df_sms_filtered = df_sms_filtered.rename(columns={'Teks': 'text'})
        df_sms_final = df_sms_filtered[['text', 'final_label']]
        print(f"Berhasil memuat {len(df_sms_final)} baris data SMS (Valid, Penipuan & Netral).")

    # Read Kaggle Cleaned Datasets
    print("\nMemproses dataset berita Kaggle (Cleaned)...")
    kaggle_files = glob.glob(os.path.join("dataset", "kaggle", "Cleaned", "*.xlsx"))
    
    kaggle_dfs = []
    for file in kaggle_files:
        print(f"Membaca {os.path.basename(file)}...")
        df_k = pd.read_excel(file)
        
        # Make sure the columns exist
        text_col = 'text_new' if 'text_new' in df_k.columns else 'FullText'
        if text_col not in df_k.columns and 'Clean Narasi' in df_k.columns:
            text_col = 'Clean Narasi'
        label_col = 'hoax'
        
        # We need to map hoax: 0 -> Valid, 1 -> Hoax
        def map_kaggle_label(x):
            try:
                val = int(x)
                return "Hoax" if val == 1 else "Valid"
            except:
                return "Valid" # fallback
                
        df_temp = df_k[[text_col, label_col]].copy()
        df_temp['final_label'] = df_temp[label_col].apply(map_kaggle_label)
        df_temp = df_temp.rename(columns={text_col: 'text'})
        df_temp = df_temp[['text', 'final_label']]
        
        # drop na
        df_temp = df_temp.dropna()
        kaggle_dfs.append(df_temp)
        
    if kaggle_dfs:
        df_kaggle_all = pd.concat(kaggle_dfs, ignore_index=True)
        print(f"Berhasil memuat {len(df_kaggle_all)} baris data Berita Kaggle (Valid & Hoax).")
    else:
        df_kaggle_all = pd.DataFrame(columns=['text', 'final_label'])
        print("Dataset Kaggle tidak ditemukan.")

    # Generate Synthetic Penipuan Data
    print("\nMenggenerasi data penipuan sintetis (data augmentation)...")
    df_synthetic = generate_synthetic_scams(n=1500)
    print(f"Berhasil menggenerasi {len(df_synthetic)} data penipuan sintetis.")

    # Generate Synthetic Netral Data
    print("\nMenggenerasi data netral sintetis...")
    df_neutral = generate_synthetic_neutral(n=1000)
    print(f"Berhasil menggenerasi {len(df_neutral)} data netral sintetis.")

    # Combine All
    print("\nMenggabungkan dataset...")
    df_final = pd.concat([df_kaggle_all, df_sms_final, df_synthetic, df_neutral], ignore_index=True)
    df_final = df_final.dropna(subset=['text']).drop_duplicates(subset=['text'])
    
    # Save to CSV (Original Imbalanced)
    output_path = os.path.join("dataset", "final_dataset.csv")
    df_final.to_csv(output_path, index=False)
    print(f"\nSelesai! Dataset akhir (asli) disimpan di {output_path}")
    print("Distribusi Label Asli:")
    print(df_final['final_label'].value_counts())
    
    # --- UNDERSAMPLING (BALANCING) ---
    print("\nMembuat versi dataset seimbang (Balanced Dataset)...")
    # Cari jumlah data dari kelas yang paling sedikit
    min_count = df_final['final_label'].value_counts().min()
    
    # Ambil sampel sebanyak min_count untuk setiap kelas
    df_balanced = df_final.groupby('final_label').sample(n=min_count, random_state=42).reset_index(drop=True)
    
    # Simpan dataset yang sudah seimbang
    balanced_output_path = os.path.join("dataset", "final_dataset_balanced.csv")
    df_balanced.to_csv(balanced_output_path, index=False)
    
    print(f"Selesai! Dataset seimbang disimpan di {balanced_output_path}")
    print("Distribusi Label Balanced:")
    print(df_balanced['final_label'].value_counts())

if __name__ == "__main__":
    main()
