"""Existing saved analyses retain their URLs after the numeric crop ID migration."""
import json

from climaraiz.storage import Database


def test_legacy_crop_ids_are_migrated_idempotently(tmp_path):
    database = Database(tmp_path / "legacy.sqlite3")
    database.initialize()
    with database.connect() as db:
        db.execute("DELETE FROM schema_version WHERE version=2")
        db.execute("INSERT INTO analyses(id,fingerprint,status,request_json,result_json,created_at,updated_at) VALUES(?,?,?,?,?,?,?)",
                   ("ana_legacy", "legacy-fingerprint", "completed", json.dumps({"crop_id": "black_beans"}),
                    json.dumps({"crop_id": "black_beans", "dates": []}), "2026-11-15", "2026-11-15"))
    database.initialize()
    database.initialize()
    row = database.analysis("ana_legacy")
    assert json.loads(row["request_json"])["crop_id"] == 2
    assert json.loads(row["result_json"])["crop_id"] == 2
    assert row["fingerprint"] == "legacy-fingerprint"
