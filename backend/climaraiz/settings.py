"""Paths and supported location. No network access is required at runtime."""
import os
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = PACKAGE_DIR.parent
DATA_DIR = Path(os.environ.get("CLIMARAIZ_DATA_DIR", str(PROJECT_DIR / "data")))
DATABASE_PATH = DATA_DIR / "climaraiz.sqlite3"
MUNICIPALITY = {"id": 2504009, "name": "Campina Grande", "state": "PB", "latitude": -7.222,
                "longitude": -35.8731}
EXPECTED_DATA_BBOX = (-35.625, -7.0, -35.625, -7.0)
MODEL_VERSION = "historical-exposure-v6-minimum-phase-criteria"
