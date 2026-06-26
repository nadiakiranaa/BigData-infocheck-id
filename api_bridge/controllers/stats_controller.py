from api_bridge.data.db_manager import get_db, now_iso
from api_bridge.data.dummy_store import stats_snapshot as dummy_stats
from api_bridge.schemas.stats import StatsResponse

def get_realtime_stats() -> StatsResponse:
    conn = get_db()
    cursor = conn.cursor()
    
    # Ambil total data
    cursor.execute("SELECT COUNT(*) as total FROM live_feed")
    total_db = cursor.fetchone()["total"]
    
    if total_db == 0:
        # Fallback ke dummy jika DB masih kosong
        dummy_stats["last_updated"] = now_iso()
        return StatsResponse(**dummy_stats)

    # Agregasi label
    cursor.execute("""
        SELECT label, COUNT(*) as count 
        FROM live_feed 
        GROUP BY label
    """)
    rows = cursor.fetchall()
    
    counts = {"Valid": 0, "Hoaks": 0, "Penipuan": 0, "Netral": 0}
    for row in rows:
        lbl = row["label"]
        if lbl in counts:
            counts[lbl] = row["count"]
            
    # Asumsikan total hari ini = total DB untuk simplifikasi demo,
    # atau bisa di filter WHERE inserted_at >= DATE('now')
    total = sum(counts.values()) or 1  # prevent div by zero
    
    hoax_vs_valid_percent = {
        "valid": round((counts["Valid"] / total) * 100, 2),
        "hoaks": round((counts["Hoaks"] / total) * 100, 2),
        "scam": round((counts["Penipuan"] / total) * 100, 2),
    }

    # Hitung unique sources aktif
    cursor.execute("SELECT COUNT(DISTINCT source) as active FROM live_feed")
    active_sources = cursor.fetchone()["active"]

    # Base response kita gabung dengan nilai dummy lama supaya angkanya besar seperti semula
    # (Hanya untuk keperluan demo agar chart tidak kosong melompong).
    # Di environment produksi sungguhan, nilai ini bisa murni dari DB:
    # total_messages_today = dummy_stats["total_messages_today"] + total_db
    # hoax_detected_today = dummy_stats["hoax_detected_today"] + counts["Hoaks"]
    # scam_detected_today = dummy_stats["scam_detected_today"] + counts["Penipuan"]
    # valid_detected_today = dummy_stats["valid_detected_today"] + counts["Valid"]

    return StatsResponse(
        total_messages_today=dummy_stats["total_messages_today"] + total_db,
        hoax_detected_today=dummy_stats["hoax_detected_today"] + counts["Hoaks"],
        scam_detected_today=dummy_stats["scam_detected_today"] + counts["Penipuan"],
        valid_detected_today=dummy_stats["valid_detected_today"] + counts["Valid"],
        hoax_vs_valid_percent=hoax_vs_valid_percent,
        active_sources=active_sources + dummy_stats["active_sources"],
        last_updated=now_iso()
    )
