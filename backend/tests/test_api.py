"""HTTP contracts, persistent analysis results, and scientific reference checks."""
import json

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient


def test_catalog_and_windows(client):
    assert client.get("/api/v1/municipalities?search=CAMPINA&state=pb").json()["data"][0]["id"] == 2504009
    assert client.get("/api/v1/municipalities?search=missing").json()["data"] == []
    assert client.get("/api/v1/municipalities?limit=0").status_code == 400
    crops = client.get("/api/v1/crops").json()["data"]
    assert [(c["id"], c["name"]) for c in crops] == [(1, "Milho"), (2, "Feijão-preto"), (3, "Girassol")]
    assert crops[0]["planting_window"]["start_month_day"] == "04-21"
    assert crops[2]["planting_window"]["end_month_day"] == "05-10"
    assert all(c["agronomic_profile_status"] == "not_validated" for c in crops)


def test_daily_coverage_and_pagination(client):
    response = client.get("/api/v1/climate/series?municipality_id=2504009&variable=precipitation&aggregation=daily&start_year=2000&end_year=2025&limit=2")
    result = response.json()
    assert response.status_code == 200
    assert result["pagination"]["total"] == 9497
    assert result["pagination"]["next_offset"] == 2
    assert len(result["series"]) == 2
    assert result["series"][0]["date"] == "2000-01-01"
    assert result["source"]["usable_for_municipality"] is True
    assert "X-Request-ID" in response.headers


def test_annual_reference_trends_and_repeatable_cache(client):
    url = "/api/v1/climate/trends?municipality_id=2504009&start_year=2001&end_year=2025"
    result = client.get(url).json()
    rain = result["indicators"]["precipitation"]
    assert rain["mean"] == pytest.approx(956.35358, abs=.0001)
    assert rain["trend"]["slope_per_decade"] == pytest.approx(101.23662, abs=.0001)
    assert rain["significance"]["p_value"] == pytest.approx(.0335614117, abs=1e-9)
    assert rain["complete_years"] == 25
    assert result == client.get(url).json()


def test_missing_day_never_produces_complete_annual_rain(client):
    with client.app.state.database.connect() as db:
        db.execute("UPDATE climate_daily SET value=NULL,quality_status='incomplete' WHERE source_id='precipitation' AND date='2020-02-29'")
    result = client.get("/api/v1/climate/series?municipality_id=2504009&variable=precipitation&aggregation=annual&start_year=2020&end_year=2020").json()
    record = result["series"][0]
    assert record["value"] is None
    assert record["valid_days"] == 365 and record["expected_days"] == 366
    assert record["quality_status"] == "incomplete"


def test_wrong_scope_is_rejected_on_local_routes(client):
    with client.app.state.database.connect() as db:
        row = db.execute("SELECT metadata_json FROM sources WHERE id='precipitation'").fetchone()
        info = json.loads(row[0])
        info["usable_for_municipality"] = False
        db.execute("UPDATE sources SET metadata_json=? WHERE id='precipitation'", (json.dumps(info),))
    response = client.get("/api/v1/climate/series?municipality_id=2504009&variable=precipitation")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "SOURCE_AREA_MISMATCH"


def test_unknown_municipality_and_unprovided_tmax(client):
    assert client.get("/api/v1/climate/trends?municipality_id=1").status_code == 404
    result = client.get("/api/v1/climate/series?municipality_id=2504009&variable=temperature_max").json()
    assert result["status"] == "unavailable"
    assert client.get("/api/v1/climate/trends?municipality_id=2504009&start_year=2025&end_year=2000").status_code == 400


def test_analysis_evaluates_every_date_and_reuses_result(client, planting_request):
    response = client.post("/api/v1/planting/analyses", json=planting_request)
    assert response.status_code == 202
    analysis_id = response.json()["analysis_id"]
    result = client.get(f"/api/v1/planting/analyses/{analysis_id}").json()
    assert result["status"] == "completed"
    assert len(result["dates"]) == 30
    assert result["dates"][0]["date"] == "2027-04-21"
    assert result["dates"][-1]["date"] == "2027-05-20"
    assert result["best_historical_date"] is None
    assert result["dates"][0]["historical_assessment"]["risk_level"] == "not_supported"
    assessment = result["dates"][0]["historical_assessment"]
    assert assessment["precipitation"]["evaluated_years"] == 25
    assert client.post("/api/v1/planting/analyses", json=planting_request).json()["reused"] is True
    invalid = client.get(f"/api/v1/planting/analyses/{analysis_id}/dates/2027-05-21")
    assert invalid.status_code == 422
    assert invalid.json()["error"]["code"] == "PLANTING_DATE_NOT_ELIGIBLE"


def test_phase_intervals_are_inclusive_and_reconcile(client, planting_request):
    planting_request["phases"] = [{"id": "early", "name": "Early scenario", "start_day": 0, "end_day": 29},
                                 {"id": "later", "name": "Later scenario", "start_day": 30, "end_day": 119}]
    identifier = client.post("/api/v1/planting/analyses", json=planting_request).json()["analysis_id"]
    detail = client.get(f"/api/v1/planting/analyses/{identifier}/dates/2027-04-21").json()
    phases = client.get(f"/api/v1/planting/analyses/{identifier}/dates/2027-04-21/phases").json()
    assert phases["status"] == "available_as_user_scenario"
    for i, whole in enumerate(detail["yearly_exposure"]):
        parts = [phase["yearly_exposure"][i] for phase in phases["phases"]]
        assert sum(p["days"] for p in parts) == 120
        assert sum(p["precipitation"]["total_mm"] for p in parts) == pytest.approx(whole["precipitation"]["total_mm"])
        weighted = sum(p["temperature_mean"]["mean_c"]*p["days"] for p in parts)/120
        assert weighted == pytest.approx(whole["temperature_mean"]["mean_c"])


def test_cross_year_cycles_exclude_incomplete_last_year(client, planting_request):
    planting_request["cycle_days"] = 365
    planting_request["historical_period"] = {"start_year": 2024, "end_year": 2025}
    identifier = client.post("/api/v1/planting/analyses", json=planting_request).json()["analysis_id"]
    result = client.get(f"/api/v1/planting/analyses/{identifier}/dates/2027-04-21").json()
    assert result["historical_assessment"]["temperature_mean"]["evaluated_years"] == 1
    assert result["yearly_exposure"][1]["temperature_mean"]["status"] == "incomplete"
    assert result["yearly_exposure"][0]["historical_end"] == "2025-04-20"


def test_phase_gaps_and_missing_cycle_are_invalid(client, planting_request):
    planting_request["phases"] = [{"id": "gap", "name": "Invalid", "start_day": 1, "end_day": 119}]
    assert client.post("/api/v1/planting/analyses", json=planting_request).status_code == 400


@pytest.mark.parametrize("crop_id", ["corn", "1", True, 1.5, 0])
def test_crop_ids_require_positive_integers(client, planting_request, crop_id):
    planting_request["crop_id"] = crop_id
    assert client.post("/api/v1/planting/analyses", json=planting_request).status_code == 400


def test_unknown_numeric_crop_is_not_found(client, planting_request):
    planting_request["crop_id"] = 99
    response = client.post("/api/v1/planting/analyses", json=planting_request)
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "CROP_NOT_FOUND"
    planting_request.pop("cycle_days")
    assert client.post("/api/v1/planting/analyses", json=planting_request).status_code == 400


def test_ui_and_openapi_are_served(client):
    assert client.get("/").status_code == 200
    assert client.get("/static/app.js").status_code == 200
    schema = client.get("/openapi.json").json()
    assert "/api/v1/planting/analyses/{analysis_id}/dates/{planting_date}/phases" in schema["paths"]
    assert client.get("/api/v1/planting/analyses/missing").status_code == 404


def test_internal_errors_use_safe_contract(client, monkeypatch):
    def fail(*args):
        raise RuntimeError("Internal database credential must not be returned")
    monkeypatch.setattr(client.app.state.climate, "trends", fail)
    # A second transport disables re-raising server exceptions for this failure contract.
    transport = TestClient(client.app, raise_server_exceptions=False)
    response = transport.get("/api/v1/climate/trends?municipality_id=2504009")
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "INTERNAL_ERROR"
    assert response.json()["error"]["request_id"]
    assert "credential" not in response.text
