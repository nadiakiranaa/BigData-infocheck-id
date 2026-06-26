import sqlite3
import os
import threading
from datetime import datetime, UTC

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "dashboard.db")

# Thread-local storage for database connections
_local = threading.local()

def get_db():
    """Mendapatkan koneksi SQLite yang thread-safe."""
    if not hasattr(_local, "conn"):
        _local.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _local.conn.row_factory = sqlite3.Row
    return _local.conn

def init_db():
    """Inisialisasi tabel database saat aplikasi mulai."""
    conn = get_db()
    cursor = conn.cursor()
    
    # Buat tabel live_feed jika belum ada
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS live_feed (
            id TEXT PRIMARY KEY,
            timestamp TEXT,
            source TEXT,
            source_type TEXT,
            text_snippet TEXT,
            label TEXT,
            confidence REAL,
            topic TEXT,
            url TEXT,
            inserted_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()

def now_iso() -> str:
    """Helper untuk format waktu seragam."""
    return datetime.now(UTC).isoformat()
