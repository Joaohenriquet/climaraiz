"""A clean checkout must start without private/local raw CSV paths or an existing DB."""
import hashlib
import json
from pathlib import Path
import shutil

from fastapi.testclient import TestClient
import pandas as pd
import pytest

from climaraiz.bundle import import_bundle
from climaraiz.errors import DomainError
from climaraiz.main import create_app
from climaraiz.storage import Database


@pytest.fixture
def clean_bundle(tmp_path):
    data = Path(__file__).resolve().parents[1] / "data"
    for name in ("sources.json", "prepared_sources.json", "climate_daily.csv"):
        shutil.copy2(data / name, tmp_path / name)
    return tmp_path


def test_clean_checkout_starts_and_calculates_without_raw_sources(clean_bundle):
    assert not (clean_bundle / "sources").exists()
    with TestClient(create_app(clean_bundle)) as client:
        status = client.get("/api/v1/data/status").json()
        assert all(v["status"] == "available" for v in status["variables"].values())
        assert status["variables"]["precipitation"]["source"]["import_mode"] == "verified_prepared_daily_bundle"
        assert status["variables"]["temperature_mean"]["source"]["daily_record_count"] == 9497
        trend = client.get("/api/v1/climate/trends?municipality_id=2504009").json()
        assert trend["indicators"]["precipitation"]["mean"] == pytest.approx(956.35358, abs=.0001)


def test_corrupted_prepared_bytes_are_rejected(clean_bundle):
    path = clean_bundle / "climate_daily.csv"
    path.write_text(path.read_text() + "\n")
    database = Database(clean_bundle / "test.sqlite3")
    database.initialize()
    with pytest.raises(DomainError) as error:
        import_bundle(database, clean_bundle / "prepared_sources.json")
    assert error.value.code == "PREPARED_BUNDLE_HASH_MISMATCH"
    assert database.source("precipitation") is None


def test_prepared_calendar_gap_rejected_even_with_updated_hash(clean_bundle):
    path = clean_bundle / "climate_daily.csv"
    table = pd.read_csv(path).drop(index=1)
    table.to_csv(path, index=False)
    metadata_path = clean_bundle / "prepared_sources.json"
    metadata = json.loads(metadata_path.read_text())
    metadata["data_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    metadata_path.write_text(json.dumps(metadata))
    database = Database(clean_bundle / "test.sqlite3")
    database.initialize()
    with pytest.raises(DomainError, match="calendar"):
        import_bundle(database, metadata_path)


def test_prepared_source_scope_is_rechecked_not_trusted(clean_bundle):
    path = clean_bundle / "prepared_sources.json"
    metadata = json.loads(path.read_text())
    metadata["sources"]["precipitation"]["actual_bbox"] = [-180, -90, 179.375, 90]
    metadata["sources"]["precipitation"]["usable_for_municipality"] = True
    path.write_text(json.dumps(metadata))
    database = Database(clean_bundle / "test.sqlite3")
    database.initialize()
    import_bundle(database, path)
    assert database.source("precipitation")["metadata"]["usable_for_municipality"] is False
