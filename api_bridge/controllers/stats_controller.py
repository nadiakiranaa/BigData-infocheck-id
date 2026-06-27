from api_bridge.data.db_manager import get_db, now_iso
from api_bridge.schemas.stats import StatsResponse, ChartPoint

def get_realtime_stats() -> StatsResponse:
    conn = get_db()
    cursor = conn.cursor()
    
    # Ambil total data
    cursor.execute("SELECT COUNT(*) as total FROM live_feed")
    total_db = cursor.fetchone()["total"]
    
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
            
    total = sum(counts.values()) or 1  # prevent div by zero
    
    hoax_vs_valid_percent = {
        "valid": round((counts["Valid"] / total) * 100, 2),
        "hoaks": round((counts["Hoaks"] / total) * 100, 2),
        "scam": round((counts["Penipuan"] / total) * 100, 2),
    }

    # Hitung unique sources aktif
    cursor.execute("SELECT COUNT(DISTINCT source) as active FROM live_feed")
    active_sources = cursor.fetchone()["active"]

    # Volume per jam
    cursor.execute("""
        SELECT substr(timestamp, 12, 2) as hour, COUNT(*) as count
        FROM live_feed
        WHERE timestamp IS NOT NULL
        GROUP BY hour
        ORDER BY hour ASC
    """)
    hourly_rows = cursor.fetchall()
    hourly_volume = [ChartPoint(label=row["hour"] if row["hour"] else "00", value=row["count"]) for row in hourly_rows]
    if not hourly_volume:
        hourly_volume = [ChartPoint(label="00", value=0)]

    # Risiko per sumber
    cursor.execute("""
        SELECT source, COUNT(*) as risk_count
        FROM live_feed
        WHERE label IN ('Hoaks', 'Penipuan')
        GROUP BY source
        ORDER BY risk_count DESC
        LIMIT 6
    """)
    risk_rows = cursor.fetchall()
    risk_scatter = [ChartPoint(label=row["source"] if row["source"] else "Unknown", value=row["risk_count"]) for row in risk_rows]
    if not risk_scatter:
        risk_scatter = [ChartPoint(label="None", value=0)]

    return StatsResponse(
        total_messages_today=total_db,
        hoax_detected_today=counts["Hoaks"],
        scam_detected_today=counts["Penipuan"],
        valid_detected_today=counts["Valid"],
        hoax_vs_valid_percent=hoax_vs_valid_percent,
        active_sources=active_sources,
        last_updated=now_iso(),
        hourly_volume=hourly_volume,
        risk_scatter=risk_scatter
    )
