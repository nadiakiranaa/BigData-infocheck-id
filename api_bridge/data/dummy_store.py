from datetime import UTC, datetime


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


stats_snapshot = {
    "total_messages_today": 128430,
    "hoax_detected_today": 2918,
    "scam_detected_today": 743,
    "valid_detected_today": 124769,
    "hoax_vs_valid_percent": {
        "valid": 97.15,
        "hoaks": 2.27,
        "scam": 0.58,
    },
    "active_sources": 12,
    "last_updated": now_iso(),
}

live_feed_items = [
    {
        "id": "feed-1001",
        "timestamp": "2026-06-24T09:47:12+07:00",
        "source": "Telegram - CekFakta",
        "source_type": "Telegram",
        "text_snippet": "Klaim bantuan presiden Rp5 juta melalui tautan formulir tidak resmi.",
        "label": "Scam",
        "confidence": 97.2,
        "topic": "bansos",
    },
    {
        "id": "feed-1002",
        "timestamp": "2026-06-24T09:46:38+07:00",
        "source": "RSS - TurnBackHoax",
        "source_type": "RSS",
        "text_snippet": "Narasi lama tentang penculikan anak kembali beredar dengan lokasi baru.",
        "label": "Hoaks",
        "confidence": 94.5,
        "topic": "politik",
    },
    {
        "id": "feed-1003",
        "timestamp": "2026-06-24T09:45:21+07:00",
        "source": "Telegram - Kompas.com",
        "source_type": "Telegram",
        "text_snippet": "Artikel resmi mengenai kebijakan bantuan sosial dan kanal pengaduan.",
        "label": "Valid",
        "confidence": 91.1,
        "topic": "ekonomi",
    },
    {
        "id": "feed-1004",
        "timestamp": "2026-06-24T09:44:59+07:00",
        "source": "RSS - Detik News",
        "source_type": "RSS",
        "text_snippet": "Pesan investasi cepat untung membawa nama lembaga negara dan dompet digital.",
        "label": "Scam",
        "confidence": 88.4,
        "topic": "investasi",
    },
]

scam_records = [
    {
        "id": "scam-001",
        "identifier_type": "bank_account",
        "identifier_value": "0147829931",
        "owner_name": "PT Bantuan Digital Nusantara",
        "source": "Telegram public report",
        "report_count": 42,
        "status": "active",
        "notes": "Dipakai untuk klaim bansos palsu.",
        "created_at": "2026-06-20T08:10:00+07:00",
        "updated_at": "2026-06-24T09:10:00+07:00",
    },
    {
        "id": "scam-002",
        "identifier_type": "phone_number",
        "identifier_value": "+6281212349988",
        "owner_name": "Admin Investasi Prioritas",
        "source": "RSS incident enrichment",
        "report_count": 18,
        "status": "under_review",
        "notes": "Terkait promosi kripto palsu.",
        "created_at": "2026-06-22T11:35:00+07:00",
        "updated_at": "2026-06-24T08:55:00+07:00",
    },
]
