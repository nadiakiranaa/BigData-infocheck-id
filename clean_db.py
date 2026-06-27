import sqlite3
import os

db_path = 'api_bridge/data/dashboard.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM live_feed WHERE source_type = 'RSS'")
    deleted = cursor.rowcount
    conn.commit()
    print(f"Berhasil menghapus {deleted} data lama RSS.")
else:
    print("Database tidak ditemukan.")
