"""Isolated databases built from the supplied regional sources."""
import json
from pathlib import Path
import shutil

from fastapi.testclient import TestClient
import pytest

from climaraiz.ingestion import import_source
from climaraiz.main import create_app
from climaraiz.storage import Database
from climaraiz.bundle import import_bundle


@pytest.fixture(scope="session")
def reference_database(tmp_path_factory):
    path = tmp_path_factory.mktemp("reference") / "climaraiz.sqlite3"
    database = Database(path)
    database.initialize()
    data = Path(__file__).resolve().parents[1] / "data"
    manifest = json.loads((data / "sources.json").read_text())
    missing = []
    for variable, source in manifest.items():
        if (data / source).exists():
            import_source(database, data / source, variable)
        else:
            missing.append(variable)
    if missing:
        import_bundle(database, data / "prepared_sources.json", missing)
    return path


@pytest.fixture
def client(tmp_path, reference_database):
    shutil.copy2(reference_database, tmp_path / "climaraiz.sqlite3")
    app = create_app(tmp_path)
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def planting_request():
    return {"municipality_id": 2504009, "crop_id": 1, "planting_year": 2027,
            "cycle_days": 120, "historical_period": {"start_year": 2001, "end_year": 2025}}
