from api_bridge.data.db_manager import get_db
from api_bridge.schemas.live_feed import LiveFeedItem

def get_live_feed(limit: int = 25) -> list[LiveFeedItem]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, timestamp, source, source_type, text_snippet, label, confidence, topic, url 
        FROM live_feed 
        ORDER BY timestamp DESC 
        LIMIT ?
    ''', (limit,))
    
    rows = cursor.fetchall()
    
    # Jika database kosong, kembalikan list kosong
    if not rows:
        return []
        
    items = []
    for row in rows:
        items.append(LiveFeedItem(
            id=row["id"],
            timestamp=row["timestamp"],
            source=row["source"],
            source_type=row["source_type"],
            text_snippet=row["text_snippet"],
            label=row["label"],
            confidence=row["confidence"],
            topic=row["topic"],
            url=row["url"]
        ))
    return items
