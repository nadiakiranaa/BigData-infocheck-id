import sqlite3
import os
from bs4 import BeautifulSoup

db_path = 'api_bridge/data/dashboard.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, text_snippet FROM live_feed")
    rows = cursor.fetchall()
    
    updated = 0
    for row in rows:
        id_val, text = row
        if text and '<' in text and '>' in text:
            cleaned = BeautifulSoup(text, "html.parser").get_text(separator=" ", strip=True)
            if cleaned != text:
                cursor.execute("UPDATE live_feed SET text_snippet = ? WHERE id = ?", (cleaned, id_val))
                updated += 1
                
    conn.commit()
    print(f"Berhasil membersihkan sisa tag HTML dari {updated} baris data.")
else:
    print("Database tidak ditemukan.")
