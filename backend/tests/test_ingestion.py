"""Boundary tests for units, hourly integration, source scope, and missing hours."""
import csv
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from climaraiz.errors import DomainError
from climaraiz.ingestion import read_giovanni


def write_hourly(path, missing=False, duplicate=False, bbox="-35.625,-7,-35.625,-7", unit="mm/hr"):
    times = list(pd.date_range("2020-02-29 00:30", periods=24, freq="h"))
    if missing:
        times.pop(7)
    if duplicate:
        times.append(times[0])
    with Path(path).open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerows([
            ["Title:", "Hourly precipitation"], ["User Start Date:", "2020-02-29T00:00:00Z"],
            ["User End Date:", "2020-02-29T23:59:59Z"], ["Data Bounding Box:", bbox],
            ["URL to Reproduce Results:", f"https://example.test/#data=M2T1NXFLX_5_12_4_PRECTOTCORR(units%3D{unit})"],
            ["Fill Value (value):", "1000000000000000"], [],
            ["time", "mean_M2T1NXFLX_5_12_4_PRECTOTCORR"]])
        for time in reversed(times):
            writer.writerow([str(time), 2])


def test_hourly_sum_is_not_daily_mean_and_handles_leap_day(tmp_path):
    path = tmp_path / "rain.csv"
    write_hourly(path)
    frame, info = read_giovanni(path, "precipitation")
    assert len(frame) == 1
    assert frame.iloc[0].value == 48  # 2 mm/h for 24 hours, not 2 mm/day.
    assert frame.iloc[0].valid_count == 24
    assert info["input_was_sorted"] is False
    assert info["usable_for_municipality"] is True
    assert info["daily_boundary"] == "UTC 00:00–24:00"


def test_missing_hour_is_unavailable_not_understated_total(tmp_path):
    path = tmp_path / "rain.csv"
    write_hourly(path, missing=True)
    frame, info = read_giovanni(path, "precipitation")
    assert pd.isna(frame.iloc[0].value)
    assert frame.iloc[0].quality_status == "incomplete"
    assert info["missing_timestamps"] == 1


@pytest.mark.parametrize("unit", ["mm/s", "kg/m^2/s"])
def test_units_cannot_be_silently_misread(tmp_path, unit):
    path = tmp_path / "rain.csv"
    write_hourly(path, unit=unit)
    with pytest.raises(DomainError, match="unit"):
        read_giovanni(path, "precipitation")


def test_duplicate_hour_rejected(tmp_path):
    path = tmp_path / "rain.csv"
    write_hourly(path, duplicate=True)
    with pytest.raises(DomainError, match="unique"):
        read_giovanni(path, "precipitation")


def test_global_source_never_becomes_local(tmp_path):
    path = tmp_path / "rain.csv"
    write_hourly(path, bbox="-180,-90,179.375,90")
    _, info = read_giovanni(path, "precipitation")
    assert info["scope"] == "global"
    assert info["usable_for_municipality"] is False
