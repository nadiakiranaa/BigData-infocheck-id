import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import random
import logging
from datetime import datetime, timedelta
from utils.kafka_helper import send_to_kafka, close_producer

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============================================================
# DATASET TWEET SIMULASI PENIPUAN & HOAKS INDONESIA (OFFLINE)
# Dataset ini dipakai karena Twitter/X API berbayar.
# Data diambil dari pola nyata penipuan yang beredar di Indonesia.
# ============================================================

SIMULATED_TWEETS = [
    # === PENIPUAN APK ===
    {
        "text": "Paket anda telah tiba di gudang, silakan cek resi pengiriman anda melalui link berikut: bit.ly/cekpaket-jnt2026 (J&T Express)",
        "label": "penipuan",
        "scam_type": "apk_malware",
        "entities": {"links": ["bit.ly/cekpaket-jnt2026"]},
        "username": "jnt_ekspres_id1247",
        "account_age_days": 3
    },
    {
        "text": "Undangan pernikahan digital kami: silakan download file APK berikut untuk melihat detail acara pernikahan Budi & Sari",
        "label": "penipuan",
        "scam_type": "apk_malware",
        "entities": {"links": []},
        "username": "undangan_digital_2026",
        "account_age_days": 1
    },
    {
        "text": "SURAT TILANG ELEKTRONIK - Kendaraan anda terekam melanggar lampu merah. Bayar denda via link: bit.ly/tilang-etle-2026",
        "label": "penipuan",
        "scam_type": "apk_malware",
        "entities": {"links": ["bit.ly/tilang-etle-2026"], "institutions": ["Kepolisian RI"]},
        "username": "info_tilang_etle",
        "account_age_days": 7
    },
    {
        "text": "Tagihan listrik PLN anda bulan ini: Rp 2.450.000. Segera bayar sebelum diputus. Download aplikasi cek tagihan: wa.me/628123456789",
        "label": "penipuan",
        "scam_type": "apk_malware",
        "entities": {"links": ["wa.me/628123456789"], "institutions": ["PLN"]},
        "username": "pln_tagihan_resmi",
        "account_age_days": 2
    },

    # === PENIPUAN IMPERSONASI ===
    {
        "text": "Bro, ini aku Dani. Nomor lama aku hilang. Lagi butuh dana darurat buat bayar RS, bisa transferin dulu 500rb ke BCA 1234567890 a/n Dani S?",
        "label": "penipuan",
        "scam_type": "impersonation",
        "entities": {"accounts": ["BCA 1234567890"], "phone_numbers": []},
        "username": "dani_s_baru2026",
        "account_age_days": 1
    },
    {
        "text": "Mama minta tolong transfer dulu ya, mama lagi di RS dan dompet ketinggalan. Transfer ke BRI 9876543210 a/n Siti R. Nanti mama ganti",
        "label": "penipuan",
        "scam_type": "impersonation",
        "entities": {"accounts": ["BRI 9876543210"]},
        "username": "mama_siti_r",
        "account_age_days": 0
    },

    # === PENIPUAN CS BANK PALSU ===
    {
        "text": "INFO RESMI BCA: Akun Anda akan diblokir dalam 24 jam karena aktivitas mencurigakan. Hubungi CS kami segera di 0812-9999-8888 untuk verifikasi",
        "label": "penipuan",
        "scam_type": "fake_cs_bank",
        "entities": {"phone_numbers": ["0812-9999-8888"], "institutions": ["BCA"]},
        "username": "bca_official_cs2026",
        "account_age_days": 5
    },
    {
        "text": "Yth Nasabah Mandiri, kartu ATM Anda terdeteksi digunakan di luar kota. Untuk keamanan segera hubungi 021-50123456 dan sebutkan PIN Anda",
        "label": "penipuan",
        "scam_type": "fake_cs_bank",
        "entities": {"phone_numbers": ["021-50123456"], "institutions": ["Mandiri"]},
        "username": "mandiri_security_alert",
        "account_age_days": 4
    },
    {
        "text": "BRI PRIORITAS: Anda terpilih upgrade kartu GOLD gratis! Konfirmasi data via link: bit.ly/bri-upgrade-gold dan masukkan no rekening + PIN",
        "label": "penipuan",
        "scam_type": "fake_cs_bank",
        "entities": {"links": ["bit.ly/bri-upgrade-gold"], "institutions": ["BRI"]},
        "username": "bri_prioritas_official",
        "account_age_days": 6
    },

    # === PENIPUAN INVESTASI BODONG ===
    {
        "text": "PROFIT HARIAN DIJAMIN! Titipkan dana Rp 1jt, dapat return 30% per hari. Sudah 5000+ member aktif. Hubungi: wa.me/6281234567890",
        "label": "penipuan",
        "scam_type": "investasi_bodong",
        "entities": {"links": ["wa.me/6281234567890"]},
        "username": "investasi_profit_daily",
        "account_age_days": 14
    },
    {
        "text": "Pinjol legal cair 5 menit! Tanpa BI checking, tanpa agunan. Limit sampai 50jt. Daftar sekarang: bit.ly/pinjol-cepat2026",
        "label": "penipuan",
        "scam_type": "pinjol_ilegal",
        "entities": {"links": ["bit.ly/pinjol-cepat2026"]},
        "username": "pinjol_legal_resmi",
        "account_age_days": 10
    },

    # === PENIPUAN TIKET KONSER ===
    {
        "text": "JUAL TIKET COLDPLAY JAKARTA! Harga jauh di bawah pasaran. Stok terbatas! DM sekarang, bayar DP 50% via GoPay 081299998888",
        "label": "penipuan",
        "scam_type": "tiket_palsu",
        "entities": {"phone_numbers": ["081299998888"]},
        "username": "tiket_konser_murah88",
        "account_age_days": 2
    },
    {
        "text": "Jastip tiket Taylor Swift Singapore! Terpercaya sudah 100+ pembeli. DP 300rb dulu ya kak, sisanya H-1 konser. WA: 082133334444",
        "label": "penipuan",
        "scam_type": "tiket_palsu",
        "entities": {"phone_numbers": ["082133334444"]},
        "username": "jastip_tiket_sg2026",
        "account_age_days": 8
    },

    # === PENIPUAN OLSHOP FIKTIF ===
    {
        "text": "MURAH BANGET! iPhone 16 Pro Max 512GB hanya 3.5jt! Stok terbatas, transfer dulu ke BCA 1122334455 a/n Toko Gadget Murah. NO COD",
        "label": "penipuan",
        "scam_type": "olshop_fiktif",
        "entities": {"accounts": ["BCA 1122334455"]},
        "username": "toko_gadget_murah_id",
        "account_age_days": 15
    },

    # === PENIPUAN GIVEAWAY PALSU ===
    {
        "text": "SELAMAT! Anda terpilih sebagai pemenang Gebyar Shopee 12.12! Hadiah iPhone 16 menanti. Klaim sebelum 24 jam: bit.ly/shopee-winner",
        "label": "penipuan",
        "scam_type": "giveaway_palsu",
        "entities": {"links": ["bit.ly/shopee-winner"], "institutions": ["Shopee"]},
        "username": "shopee_giveaway_resmi",
        "account_age_days": 3
    },
    {
        "text": "Raffi Ahmad bagi-bagi uang Rp 50jt untuk 100 orang! Daftar via link: bit.ly/raffi-giveaway2026 sebelum kuota habis!",
        "label": "penipuan",
        "scam_type": "giveaway_palsu",
        "entities": {"links": ["bit.ly/raffi-giveaway2026"]},
        "username": "raffi_ahmad_official2",
        "account_age_days": 1
    },

    # === HOAKS EKONOMI ===
    {
        "text": "BREAKING: Pemerintah akan membekukan semua rekening bank rakyat mulai besok untuk audit nasional! Segera tarik tunai uang Anda!",
        "label": "hoaks",
        "scam_type": "hoaks_ekonomi",
        "entities": {"institutions": ["Pemerintah", "Bank"]},
        "username": "berita_ekonomi_terkini",
        "account_age_days": 30
    },
    {
        "text": "VIRAL! Rupiah akan didevaluasi 50% minggu depan! Menteri Keuangan sudah tanda tangan SK-nya. Segera beli dolar sekarang!",
        "label": "hoaks",
        "scam_type": "hoaks_ekonomi",
        "entities": {"institutions": ["Kemenkeu"]},
        "username": "ekonomi_update_id",
        "account_age_days": 45
    },
    {
        "text": "FAKTA: BBM Pertamax akan GRATIS mulai 1 Juli 2026! Prabowo sudah tanda tangani PP-nya tadi malam. Share sebelum dihapus!",
        "label": "hoaks",
        "scam_type": "hoaks_kebijakan",
        "entities": {"institutions": ["Pertamina", "Pemerintah"]},
        "username": "info_kebijakan_ri",
        "account_age_days": 20
    },

    # === HOAKS POLITIK ===
    {
        "text": "VIDEO BOCOR: Presiden mengakui korupsi dana bansos triliunan di sidang tertutup DPR! Video ini segera akan dihapus pemerintah!",
        "label": "hoaks",
        "scam_type": "hoaks_politik",
        "entities": {"institutions": ["DPR", "Presiden"]},
        "username": "bocoran_sidang_dpr",
        "account_age_days": 7
    },
    {
        "text": "HEBOH! MK resmi batalkan hasil Pemilu 2024 dan putuskan Pemilu ulang digelar September 2026! Ini dokumen resminya!",
        "label": "hoaks",
        "scam_type": "hoaks_politik",
        "entities": {"institutions": ["MK", "KPU"]},
        "username": "update_politik_id",
        "account_age_days": 12
    },

    # === BERITA VALID ===
    {
        "text": "Bank Indonesia mempertahankan suku bunga acuan di level 5,75% dalam Rapat Dewan Gubernur bulan Juni 2026",
        "label": "valid",
        "scam_type": None,
        "entities": {"institutions": ["Bank Indonesia"]},
        "username": "bi_official",
        "account_age_days": 1825
    },
    {
        "text": "BPS: Inflasi Indonesia bulan Mei 2026 sebesar 3,08% (yoy), didorong oleh kenaikan harga cabai merah dan minyak goreng",
        "label": "valid",
        "scam_type": None,
        "entities": {"institutions": ["BPS"]},
        "username": "bps_statistics",
        "account_age_days": 2000
    },
    {
        "text": "Kominfo memblokir 1.247 situs judi online dan 389 konten penipuan digital sepanjang Januari-Mei 2026",
        "label": "valid",
        "scam_type": None,
        "entities": {"institutions": ["Kominfo"]},
        "username": "kominfo_ri_official",
        "account_age_days": 3000
    },
]

# Cache untuk hindari duplikat
SENT_TWEET_IDS = set()

def generate_tweet_id():
    """Generate fake tweet ID yang unik"""
    return f"tw_{int(time.time())}_{random.randint(1000, 9999)}"

def generate_fake_metrics():
    """Generate engagement metrics realistis"""
    return {
        "likes": random.randint(0, 500),
        "retweets": random.randint(0, 200),
        "replies": random.randint(0, 50),
        "views": random.randint(100, 50000)
    }

def generate_fake_timestamp():
    """Generate timestamp acak dalam 24 jam terakhir"""
    hours_ago = random.randint(0, 24)
    minutes_ago = random.randint(0, 59)
    tweet_time = datetime.utcnow() - timedelta(hours=hours_ago, minutes=minutes_ago)
    return tweet_time.isoformat() + "Z"

def simulate_and_send():
    """
    Ambil tweet simulasi secara acak dan kirim ke Kafka topic 'twitter-tweets'.
    Setiap batch kirim 3-7 tweet acak dari dataset.
    """
    global SENT_TWEET_IDS  # ← taruh di sini
    logger.info("Starting Twitter simulation batch...")

    # Ambil subset acak dari dataset (3-7 tweet per batch)
    batch_size = random.randint(3, 7)
    batch = random.sample(SIMULATED_TWEETS, min(batch_size, len(SIMULATED_TWEETS)))

    sent_count = 0
    for tweet_data in batch:
        tweet_id = generate_tweet_id()

        # Hindari duplikat dalam sesi yang sama
        if tweet_id in SENT_TWEET_IDS:
            continue

        payload = {
            "tweet_id": tweet_id,
            "source": "twitter_simulator",
            "category": "social_media",
            "username": tweet_data["username"],
            "text": tweet_data["text"],
            "label_ground_truth": tweet_data["label"],
            "scam_type": tweet_data["scam_type"],
            "entities": tweet_data["entities"],
            "account_age_days": tweet_data["account_age_days"],
            "metrics": generate_fake_metrics(),
            "tweeted_at": generate_fake_timestamp(),
            "ingested_at": datetime.utcnow().isoformat() + "Z"
        }

        success = send_to_kafka('twitter-tweets', payload)
        if success:
            SENT_TWEET_IDS.add(tweet_id)
            sent_count += 1
            logger.info(f"Sent tweet [{tweet_data['label'].upper()}] from @{tweet_data['username']}: {tweet_data['text'][:60]}...")

        # Jeda kecil antar tweet biar realistis
        time.sleep(random.uniform(0.3, 1.0))

    logger.info(f"Batch selesai: {sent_count} tweets terkirim ke topic 'twitter-tweets'")

    # Bersihkan cache kalau terlalu besar
    if len(SENT_TWEET_IDS) > 500:
        SENT_TWEET_IDS = set(list(SENT_TWEET_IDS)[-250:])

def main():
    logger.info("Twitter Simulator Producer started.")
    logger.info(f"Dataset: {len(SIMULATED_TWEETS)} tweet templates siap disimulasikan")
    logger.info("Mengirim data ke Kafka topic: 'twitter-tweets'")

    try:
        while True:
            simulate_and_send()
            # Interval 90 detik biar tidak terlalu cepat
            logger.info("Sleeping for 90 seconds...")
            time.sleep(90)
    except KeyboardInterrupt:
        logger.info("Shutdown signal received. Stopping Twitter simulator...")
    finally:
        close_producer()

if __name__ == '__main__':
    main()
