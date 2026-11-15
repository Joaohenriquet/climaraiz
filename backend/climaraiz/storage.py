"""Versioned SQLite persistence using short-lived, thread-local connections."""
from contextlib import contextmanager
import json
from pathlib import Path
import sqlite3


class Database:
    def __init__(self, path):
        self.path = Path(path)

    @contextmanager
    def connect(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(str(self.path), timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def initialize(self):
        with self.connect() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.executescript("""
            CREATE TABLE IF NOT EXISTS schema_version(version INTEGER PRIMARY KEY);
            INSERT OR IGNORE INTO schema_version VALUES(1);
            CREATE TABLE IF NOT EXISTS sources(
              id TEXT PRIMARY KEY, variable TEXT NOT NULL, source_hash TEXT NOT NULL,
              metadata_json TEXT NOT NULL, imported_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS climate_daily(
              source_id TEXT NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
              date TEXT NOT NULL, value REAL, valid_count INTEGER NOT NULL,
              expected_count INTEGER NOT NULL, quality_status TEXT NOT NULL,
              PRIMARY KEY(source_id,date));
            CREATE INDEX IF NOT EXISTS climate_by_date ON climate_daily(date,source_id);
            CREATE TABLE IF NOT EXISTS analyses(
              id TEXT PRIMARY KEY, fingerprint TEXT NOT NULL UNIQUE, status TEXT NOT NULL,
              request_json TEXT NOT NULL, result_json TEXT, error_json TEXT,
              progress REAL NOT NULL DEFAULT 0, created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS trend_cache(
              cache_key TEXT PRIMARY KEY, result_json TEXT NOT NULL);
            """)
            if db.execute("SELECT 1 FROM schema_version WHERE version=2").fetchone() is None:
                # Keep existing analysis URLs usable after the crop-ID contract change.
                legacy_ids = {"corn": 1, "black_beans": 2, "sunflower": 3}
                for row in db.execute("SELECT id,request_json,result_json FROM analyses").fetchall():
                    request = json.loads(row["request_json"])
                    result = json.loads(row["result_json"]) if row["result_json"] else None
                    if request.get("crop_id") in legacy_ids:
                        request["crop_id"] = legacy_ids[request["crop_id"]]
                    if result and result.get("crop_id") in legacy_ids:
                        result["crop_id"] = legacy_ids[result["crop_id"]]
                    db.execute("UPDATE analyses SET request_json=?,result_json=? WHERE id=?",
                               (json.dumps(request), json.dumps(result) if result is not None else None, row["id"]))
                db.execute("INSERT INTO schema_version VALUES(2)")

    def source(self, variable):
        with self.connect() as db:
            row = db.execute("SELECT * FROM sources WHERE variable=?", (variable,)).fetchone()
        if row is None:
            return None
        return {**dict(row), "metadata": json.loads(row["metadata_json"])}

    def analysis(self, analysis_id):
        with self.connect() as db:
            row = db.execute("SELECT * FROM analyses WHERE id=?", (analysis_id,)).fetchone()
        return dict(row) if row else None
