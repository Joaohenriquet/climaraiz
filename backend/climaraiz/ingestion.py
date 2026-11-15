"""Read Giovanni metadata and validate temporal/spatial resolution before aggregation."""
import csv
from datetime import datetime, timezone
import hashlib
from io import StringIO
import json
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

import numpy as np
import pandas as pd

from .errors import DomainError
from .settings import EXPECTED_DATA_BBOX


def read_giovanni(path, variable):
    raw = Path(path).read_bytes()
    lines = raw.decode("utf-8-sig").splitlines()
    start = next((i for i, line in enumerate(lines) if line.split(",")[0].strip() == "time"), None)
    if start is None:
        raise DomainError("INVALID_SOURCE", "The Giovanni time header is missing.")
    metadata = {}
    for line in lines[:start]:
        if line.strip():
            parts = next(csv.reader([line]))
            metadata[parts[0].strip().rstrip(":")] = ",".join(parts[1:]).strip()
    table = pd.read_csv(StringIO("\n".join(lines[start:])), skipinitialspace=True)
    table.columns = table.columns.str.strip()
    if len(table.columns) != 2:
        raise DomainError("INVALID_SOURCE", "Exactly one data variable is required.")
    url = urlparse(metadata.get("URL to Reproduce Results", ""))
    data_parameter = unquote(parse_qs(url.fragment or url.query).get("data", [""])[0])
    expected = {"precipitation": ("M2T1NXFLX_5_12_4_PRECTOTCORR", "mm/hr"),
                "temperature_mean": ("M2SDNXSLV_5_12_4_T2MMEAN", "C")}
    product, unit = expected[variable]
    if f"{product}(units={unit})" not in data_parameter or table.columns[1] != "mean_" + product:
        raise DomainError("SOURCE_UNIT_MISMATCH", "The selected product or exported unit is incompatible.",
                          details={"expected_product": product, "expected_unit": unit})
    timestamps = pd.to_datetime(table.time, errors="raise", utc=True)
    if timestamps.isna().any() or timestamps.duplicated().any():
        raise DomainError("DUPLICATE_OR_MISSING_DATE", "Source timestamps must be unique and present.")
    if timestamps.empty:
        raise DomainError("INVALID_SOURCE", "The source has no observations.")
    was_sorted = timestamps.is_monotonic_increasing
    values = pd.to_numeric(table.iloc[:, 1], errors="raise")
    fill_key = next((key for key in metadata if key.startswith("Fill Value")), None)
    fill = float(metadata[fill_key]) if fill_key else 1e15
    invalid = ~np.isfinite(values) | values.eq(fill)
    if variable == "precipitation":
        invalid |= values.lt(0)
    series = pd.Series(values.mask(invalid).to_numpy(), index=pd.DatetimeIndex(timestamps), name="value").sort_index()
    start_date = pd.Timestamp(metadata["User Start Date"])
    end_date = pd.Timestamp(metadata["User End Date"])
    if start_date.tzinfo is None or end_date.tzinfo is None:
        raise DomainError("INVALID_SOURCE", "Declared bounds must identify UTC.")
    if variable == "precipitation":
        # Hourly averages are labelled at interval midpoints. Each value covers one hour.
        expected_index = pd.date_range(start_date.normalize() + pd.Timedelta(minutes=30),
                                       end_date.normalize() + pd.Timedelta(hours=23, minutes=30), freq="h")
        expected_count = 24
    else:
        expected_index = pd.date_range(start_date.normalize(), end_date.normalize(), freq="D")
        expected_count = 1
    if len(series.index.difference(expected_index)):
        raise DomainError("INVALID_TIME_GRID", "Timestamps do not match the expected UTC source grid.")
    missing_timestamps = len(expected_index.difference(series.index))
    series = series.reindex(expected_index)
    counts = series.resample("D").count()
    if variable == "precipitation":
        # mm/hour × one hour, then sum all 24 hourly intervals. Never average as mm/day.
        daily = series.resample("D").sum(min_count=24)
    else:
        daily = series.resample("D").mean()
    frame = pd.DataFrame({"value": daily, "valid_count": counts})
    frame["expected_count"] = expected_count
    frame["quality_status"] = np.where(counts.eq(expected_count), "valid", "incomplete")
    frame.loc[~counts.eq(expected_count), "value"] = np.nan
    try:
        bbox = tuple(float(part) for part in metadata["Data Bounding Box"].split(","))
    except (KeyError, ValueError):
        bbox = ()
    spatial_match = len(bbox) == 4 and np.allclose(bbox, EXPECTED_DATA_BBOX, atol=1e-8, rtol=0)
    coverage_scope = "regional_grid_cell" if spatial_match else "global" if len(bbox) == 4 and bbox[2]-bbox[0] > 300 else "other_area"
    source_hash = hashlib.sha256(raw).hexdigest()
    info = {"provider": "NASA", "dataset": "MERRA-2 / Giovanni", "product": product,
            "original_filename": Path(path).name, "sha256": source_hash, "metadata": metadata,
            "source_unit": unit, "daily_unit": "mm/day" if variable == "precipitation" else "degC",
            "source_resolution": "hourly" if expected_count == 24 else "daily",
            "daily_boundary": "UTC 00:00–24:00", "timezone": "UTC",
            "actual_bbox": list(bbox), "expected_local_bbox": list(EXPECTED_DATA_BBOX),
            "scope": coverage_scope, "usable_for_municipality": bool(spatial_match),
            "raw_record_count": len(table), "input_was_sorted": bool(was_sorted),
            "invalid_values": int(invalid.sum()), "missing_timestamps": missing_timestamps,
            "daily_record_count": len(frame), "incomplete_days": int((counts != expected_count).sum()),
            "start_date": str(frame.index.min().date()), "end_date": str(frame.index.max().date()),
            "aggregation_method": "sum of 24 hourly rates multiplied by one hour" if expected_count == 24 else "daily mean as exported"}
    return frame, info


def import_source(database, path, variable):
    frame, info = read_giovanni(path, variable)
    return persist_daily_source(database, frame, info, variable)


def persist_daily_source(database, frame, info, variable):
    """Atomically replace one active source and invalidate statistics derived from it."""
    source_id = variable  # One active source per variable; old analyses retain full snapshots.
    now = datetime.now(timezone.utc).isoformat()
    records = [(source_id, str(day.date()), None if pd.isna(row.value) else float(row.value),
                int(row.valid_count), int(row.expected_count), row.quality_status) for day, row in frame.iterrows()]
    with database.connect() as db:
        db.execute("DELETE FROM sources WHERE id=?", (source_id,))
        db.execute("INSERT INTO sources VALUES(?,?,?,?,?)", (source_id, variable, info["sha256"], json.dumps(info), now))
        db.executemany("INSERT INTO climate_daily VALUES(?,?,?,?,?,?)", records)
        db.execute("DELETE FROM trend_cache")
    return info
