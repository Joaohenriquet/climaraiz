"""Mean-based exposure must not silently become an extreme-temperature risk score."""
from datetime import date

import pandas as pd
import pytest

from climaraiz.checks import evaluate_check
from climaraiz.models import ScenarioPhase


def windows(last=2):
    phase = ScenarioPhase(id="flowering", name="Test window", start_day=0, end_day=last)
    return {phase.id: phase}


def frame(year, values):
    return pd.DataFrame({"value": values}, index=pd.date_range(f"{year}-01-01", periods=len(values)))


def test_mean_heat_uses_strict_threshold_and_counts_years_once():
    data = pd.concat([frame(2020, [33, 34, 35]), frame(2021, [32, 33, 31])])
    rule = {"type": "heat_days", "phase": "flowering", "variable": "T2M_MEAN", "threshold_c": 33}
    result = evaluate_check(rule, windows(), {"temperature_mean": data}, date(2027, 1, 1), 2020, 2021)
    assert [r["value"] for r in result["yearly_results"]] == [2, 0]
    assert result["historical_event_frequency_pct"] == 50
    assert result["event_years"] == 1
    assert result["risk_percentage"] is None
    assert result["variable"] == "T2M_MEAN"
    assert "Zero does not imply" in result["limitation"]


def test_cold_uses_below_not_above_and_excludes_incomplete_year():
    data = pd.concat([frame(2020, [12, 11, 10]), frame(2021, [11, None, 13])])
    rule = {"type": "cold_days", "phase": "flowering", "variable": "T2M_MEAN", "threshold_c": 12}
    result = evaluate_check(rule, windows(), {"temperature_mean": data}, date(2027, 1, 1), 2020, 2021)
    assert result["summary"]["mean"] == 2
    assert result["evaluated_years"] == 1 and result["event_years"] == 1
    assert result["historical_event_frequency_pct"] == 100
    assert result["excluded_years"] == [{"year": 2021, "missing_days": 1}]
    assert result["yearly_results"][1]["value"] is None


def test_dry_spell_threshold_equality_breaks_run_without_inventing_event():
    rule = {"type": "dry_spell", "phase": "flowering", "variable": "PRECTOTCORR",
            "rain_below_mm": 1, "min_consecutive_days": None}
    data = frame(2020, [0, .9, 1, 0, 0])
    result = evaluate_check(rule, windows(4), {"precipitation": data}, date(2027, 1, 1), 2020, 2020)
    assert result["summary"]["maximum"] == 2
    assert result["historical_event_frequency_pct"] is None
    assert result["event_years"] is None
    rule["min_consecutive_days"] = 2
    result = evaluate_check(rule, windows(4), {"precipitation": data}, date(2027, 1, 1), 2020, 2020)
    assert result["historical_event_frequency_pct"] == 100


def test_rainfall_sum_has_no_implicit_risk():
    rule = {"type": "rainfall_total", "phase": "flowering", "variable": "PRECTOTCORR", "min_mm": None, "max_mm": None}
    result = evaluate_check(rule, windows(), {"precipitation": frame(2020, [15, 20, 10])}, date(2027, 1, 1), 2020, 2020)
    assert result["summary"]["mean"] == 45
    assert result["historical_event_frequency_pct"] is None


@pytest.mark.parametrize("total,event", [(499, True), (500, False), (501, False)])
def test_cycle_rainfall_benchmark_includes_equality_without_upper_cutoff(total, event):
    rule = {"type": "rainfall_total", "phase": "flowering", "variable": "PRECTOTCORR", "min_mm": 500, "max_mm": None}
    result = evaluate_check(rule, windows(0), {"precipitation": frame(2020, [total])}, date(2027, 1, 1), 2020, 2020)
    assert result["yearly_results"][0]["event_occurred"] is event


def test_missing_phase_or_variable_is_unavailable_not_zero():
    rule = {"type": "heat_days", "phase": "flowering", "variable": "T2M_MEAN", "threshold_c": 33}
    result = evaluate_check(rule, {}, {}, date(2027, 1, 1), 2020, 2020)
    assert result["reason"] == "PHASE_WINDOW_NOT_DEFINED" and result["summary"] is None
    result = evaluate_check(rule, windows(), {}, date(2027, 1, 1), 2020, 2020)
    assert result["reason"] == "SOURCE_UNAVAILABLE"
    rule["variable"] = "T2M_MAX"
    result = evaluate_check(rule, windows(), {"temperature_mean": frame(2020, [40, 40, 40])}, date(2027, 1, 1), 2020, 2020)
    assert result["reason"] == "UNSUPPORTED_CHECK_OR_VARIABLE"


def test_peak_is_highest_daily_mean():
    rule = {"type": "temperature_mean_peak", "phase": "flowering", "variable": "T2M_MEAN"}
    result = evaluate_check(rule, windows(), {"temperature_mean": frame(2020, [24, 26, 25])}, date(2027, 1, 1), 2020, 2020)
    assert result["summary"]["maximum"] == 26
    assert result["historical_event_frequency_pct"] is None


def test_real_api_exposes_configured_checks_and_overlapping_windows(client, planting_request):
    planting_request["check_windows"] = [
        {"id": "flowering", "name": "Illustrative flowering", "start_day": 0, "end_day": 20},
        {"id": "pollination", "name": "Illustrative pollination", "start_day": 5, "end_day": 10}]
    response = client.post("/api/v1/planting/analyses", json=planting_request)
    assert response.status_code == 202
    url = response.json()["links"]["result"]
    calendar = client.get(url).json()
    assert calendar["configured_climate_checks"][0]["variable"] == "T2M_MEAN"
    record = client.get(url + "/dates/2027-04-21").json()
    checks = record["climate_checks"]
    assert checks[0]["status"] == "available" and checks[0]["evaluated_years"] == 25
    assert checks[1]["status"] == "available" and checks[1]["historical_event_frequency_pct"] is not None
    assert checks[2]["status"] == "available" and checks[2]["phase"] == "cycle"
    assert record["scenario_assessment"]["status"] == "available"
    assert len(checks[0]["yearly_results"]) == 25
    assert "yearly_results" not in calendar["dates"][0]["climate_checks"][0]
    assert record["historical_assessment"]["risk_level"] == record["scenario_assessment"]["risk_level"]
    assert record["risk_level"] in ("low", "moderate", "high")


@pytest.mark.parametrize("window", [
    {"id": "flowering", "name": "Outside cycle", "start_day": 0, "end_day": 120},
    {"id": "flowering", "name": "Reversed", "start_day": 5, "end_day": 2}])
def test_invalid_check_window_rejected(client, planting_request, window):
    planting_request["check_windows"] = [window]
    assert client.post("/api/v1/planting/analyses", json=planting_request).status_code == 400
