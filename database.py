import sqlite3
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

DB_PATH = Path(__file__).resolve().parent.parent / "baugrundstueck.db"

class Database:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Inizializza la tabella SQLite per salvare annunci e bandi trovati."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS listings (
                    id TEXT PRIMARY KEY,
                    source TEXT NOT NULL,
                    category TEXT NOT NULL,
                    title TEXT NOT NULL,
                    price TEXT,
                    area_sqm TEXT,
                    location TEXT NOT NULL,
                    train_info TEXT,
                    link TEXT NOT NULL,
                    details TEXT,
                    first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notified INTEGER DEFAULT 0,
                    notified_at TIMESTAMP
                );
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_link ON listings(link);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_notified ON listings(notified);")
            conn.commit()

    @staticmethod
    def generate_id(link: str, title: str) -> str:
        """Genera un hash univoco a partire dall'URL e dal titolo."""
        unique_string = f"{link.strip()}::{title.strip()}"
        return hashlib.sha256(unique_string.encode("utf-8")).hexdigest()

    def exists(self, item_id: str) -> bool:
        """Verifica se l'annuncio o bando è già stato memorizzato nel database."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM listings WHERE id = ?", (item_id,))
            return cursor.fetchone() is not None

    def insert_listing(self, item: Dict[str, Any]) -> bool:
        """
        Inserisce un nuovo annuncio/bando.
        Restituisce True se inserito con successo, False se già presente.
        """
        item_id = item.get("id") or self.generate_id(item["link"], item["title"])
        if self.exists(item_id):
            return False

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO listings (
                    id, source, category, title, price, area_sqm,
                    location, train_info, link, details, first_seen_at, notified
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
            """, (
                item_id,
                item.get("source", "Unknown"),
                item.get("category", "Land"),
                item["title"],
                item.get("price", "N/D"),
                item.get("area_sqm", "N/D"),
                item.get("location", "N/D"),
                item.get("train_info", ""),
                item["link"],
                item.get("details", ""),
                datetime.utcnow().isoformat()
            ))
            conn.commit()
            return True

    def get_pending_notifications(self) -> List[Dict[str, Any]]:
        """Restituisce tutti gli elementi registrati ma non ancora notificati."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM listings WHERE notified = 0 ORDER BY first_seen_at ASC")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def mark_as_notified(self, item_id: str):
        """Contrassegna l'elemento come notificato con timestamp."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE listings 
                SET notified = 1, notified_at = ?
                WHERE id = ?
            """, (datetime.utcnow().isoformat(), item_id))
            conn.commit()
