"""Configured phase checks: descriptive exposure, never an implicit crop-risk score."""
from datetime import date, timedelta

import numpy as np
import pandas as pd


def _longest_run(flags):
    current = longest = 0
    for flag in flags:
        current = current + 1 if flag else 0
        longest = max(longest, current)
    return longest


def evaluate_check(rule, windows, frames, planting_date, start_year, end_year):
    kind, variable = rule["type"], rule["variable"]
    unit = "days" if kind in ("heat_days", "cold_days", "dry_spell") else "mm" if kind == "rainfall_total" else "degC"
    result = {"definition": dict(rule), "phase": rule["phase"], "variable": variable, "unit": unit,
              "status": "unavailable", "reason": None, "summary": None, "yearly_results": [],
              "evaluated_years": 0, "excluded_years": [], "event_years": None,
              "historical_event_frequency_pct": None, "risk_percentage": None,
              "interpretation": "descriptive_or_exploratory_exposure_not_crop_loss_probability"}
    phase = windows.get(rule["phase"])
    if phase is None:
        result["reason"] = "PHASE_WINDOW_NOT_DEFINED"
        return result
    result["window"] = phase.model_dump()
    expected_variable = {"heat_days": "T2M_MEAN", "cold_days": "T2M_MEAN",
                         "temperature_mean_peak": "T2M_MEAN", "dry_spell": "PRECTOTCORR",
                         "rainfall_total": "PRECTOTCORR"}.get(kind)
    if expected_variable is None or variable != expected_variable:
        result["reason"] = "UNSUPPORTED_CHECK_OR_VARIABLE"
        return result
    source_variable = "temperature_mean" if variable == "T2M_MEAN" else "precipitation"
    frame = frames.get(source_variable)
    if frame is None:
        result["reason"] = "SOURCE_UNAVAILABLE"
        return result
    if kind in ("heat_days", "cold_days") and rule.get("threshold_c") is None:
        result["reason"] = "THRESHOLD_NOT_DEFINED"
        return result
    if kind == "dry_spell" and rule.get("rain_below_mm") is None:
        result["reason"] = "THRESHOLD_NOT_DEFINED"
        return result
    event_defined = kind in ("heat_days", "cold_days") or (
        kind == "dry_spell" and rule.get("min_consecutive_days") is not None) or (
        kind == "rainfall_total" and any(rule.get(key) is not None for key in ("min_mm", "max_mm")))
    if event_defined:
        result["event_definition"] = {
            "heat_days": "at_least_one_daily_mean_strictly_above_threshold",
            "cold_days": "at_least_one_daily_mean_strictly_below_threshold",
            "dry_spell": "longest_dry_spell_at_least_min_consecutive_days",
            "rainfall_total": "phase_total_strictly_outside_configured_bounds"}.get(kind)
    if variable == "T2M_MEAN":
        result["limitation"] = "Daily means may miss daily maximum/minimum threshold crossings. Zero does not imply absence of extreme heat or cold."
    values, events = [], []
    for year in range(start_year, end_year+1):
        origin = date(year, planting_date.month, planting_date.day)
        first, last = origin + timedelta(days=phase.start_day), origin + timedelta(days=phase.end_day)
        series = frame.value.reindex(pd.date_range(first, last, freq="D"))
        missing = int(series.isna().sum())
        if missing:
            result["excluded_years"].append({"year": year, "missing_days": missing})
            result["yearly_results"].append({"year": year, "status": "incomplete", "value": None,
                "event_occurred": None, "missing_days": missing})
            continue
        event = None
        if kind == "heat_days":
            value = int((series > rule["threshold_c"]).sum())
            event = value > 0
        elif kind == "cold_days":
            value = int((series < rule["threshold_c"]).sum())
            event = value > 0
        elif kind == "dry_spell":
            value = _longest_run(series < rule["rain_below_mm"])
            if event_defined:
                event = value >= rule["min_consecutive_days"]
        elif kind == "rainfall_total":
            value = float(series.sum())
            if event_defined:
                event = ((rule.get("min_mm") is not None and value < rule["min_mm"]) or
                         (rule.get("max_mm") is not None and value > rule["max_mm"]))
        else:
            value = float(series.max())
        values.append(value)
        if event is not None:
            events.append(bool(event))
        result["yearly_results"].append({"year": year, "status": "available", "value": value,
            "event_occurred": bool(event) if event is not None else None,
            "historical_start": str(first), "historical_end": str(last), "days": len(series)})
    if not values:
        result["reason"] = "NO_COMPLETE_PHASE_YEARS"
        return result
    result.update(status="available", reason=None, evaluated_years=len(values),
        summary={"mean": float(np.mean(values)), "median": float(np.median(values)),
                 "minimum": float(np.min(values)), "maximum": float(np.max(values))})
    if event_defined:
        result["event_years"] = sum(events)
        result["historical_event_frequency_pct"] = 100*sum(events)/len(values)
    return result
