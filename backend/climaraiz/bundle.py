"""Reproducible startup from the complete, versioned daily data and provenance bundle."""
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .climate import ClimateService
from .errors import DomainError
from .ingestion import persist_daily_source
from .settings import EXPECTED_DATA_BBOX

COLUMNS = {"precipitation": ("precipitation_mm", "precipitation_quality", "mm/day", 24),
           "temperature_mean": ("temperature_mean_c", "temperature_quality", "degC", 1)}


def export_bundle(database, directory):
    """Export a complete daily CSV together with source snapshots and its SHA-256."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    climate = ClimateService(database)
    sources, tables = {}, []
    for variable, (column, quality, _, _) in COLUMNS.items():
        frame, sources[variable] = climate.daily(variable)
        if not frame.quality_status.eq("valid").all() or frame.value.isna().any():
            raise DomainError("INCOMPLETE_PREPARED_BUNDLE", "Prepared bundles require complete daily sources; use the raw CSV importer for incomplete data.")
        tables.append(frame[["value", "quality_status"]].rename(columns={"value": column, "quality_status": quality}))
    if not tables[0].index.equals(tables[1].index):
        raise DomainError("INCOMPLETE_PREPARED_BUNDLE", "Prepared sources must cover the same daily calendar.")
    joined = tables[0].join(tables[1]).rename_axis("date")
    data_path = directory / "climate_daily.csv"
    joined.to_csv(data_path)
    manifest = {"schema_version": 1, "data_file": data_path.name,
                "data_sha256": hashlib.sha256(data_path.read_bytes()).hexdigest(), "sources": sources}
    (directory / "prepared_sources.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+"\n")
    return manifest


def import_bundle(database, manifest_path, variables=None):
    """Verify prepared bytes, coverage, units and scope before importing missing sources."""
    manifest_path = Path(manifest_path)
    manifest = json.loads(manifest_path.read_text())
    if manifest.get("schema_version") != 1:
        raise DomainError("INVALID_PREPARED_BUNDLE", "Unsupported prepared bundle schema.")
    data_path = manifest_path.parent / manifest["data_file"]
    if data_path.resolve().parent != manifest_path.parent.resolve():
        raise DomainError("INVALID_PREPARED_BUNDLE", "The prepared CSV must be beside its manifest.")
    raw = data_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != manifest["data_sha256"]:
        raise DomainError("PREPARED_BUNDLE_HASH_MISMATCH", "The prepared daily CSV differs from its recorded SHA-256.")
    table = pd.read_csv(data_path, parse_dates=["date"]).set_index("date")
    if table.empty or table.index.hasnans or not table.index.is_unique or not table.index.is_monotonic_increasing:
        raise DomainError("INVALID_PREPARED_BUNDLE", "Prepared daily dates must be present, sorted and unique.")
    expected = pd.date_range(table.index.min().normalize(), table.index.max().normalize(), freq="D")
    if not table.index.equals(expected.rename("date")):
        raise DomainError("INVALID_PREPARED_BUNDLE", "Prepared dates must form a complete midnight-based daily calendar.")
    prepared = []
    for variable in variables if variables is not None else COLUMNS:
        column, quality, unit, samples = COLUMNS[variable]
        info = dict(manifest["sources"][variable])
        values = pd.to_numeric(table[column], errors="raise")
        if (not np.isfinite(values).all() or not table[quality].eq("valid").all()
                or (variable == "precipitation" and values.lt(0).any())):
            raise DomainError("INVALID_PREPARED_BUNDLE", "Prepared data must be complete, finite and marked valid.")
        if (info["daily_unit"] != unit or info["daily_record_count"] != len(table)
                or info["start_date"] != str(table.index.min().date())
                or info["end_date"] != str(table.index.max().date())):
            raise DomainError("INVALID_PREPARED_BUNDLE", "Prepared source coverage or daily units do not match the CSV.")
        bbox = info.get("actual_bbox", [])
        info["usable_for_municipality"] = len(bbox) == 4 and bool(np.allclose(bbox, EXPECTED_DATA_BBOX, atol=1e-8, rtol=0))
        info["import_mode"] = "verified_prepared_daily_bundle"
        info["prepared_csv_sha256"] = manifest["data_sha256"]
        info["raw_bytes_reverified_at_startup"] = False
        frame = pd.DataFrame({"value": values, "valid_count": samples, "expected_count": samples,
                              "quality_status": "valid"}, index=table.index)
        prepared.append((variable, frame, info))
    # Validate every requested source before writing any of them.
    for variable, frame, info in prepared:
        persist_daily_source(database, frame, info, variable)
    return [info for _, _, info in prepared]
