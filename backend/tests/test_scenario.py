"""Joint annual assessment, completeness, boundaries, and numerical reference scenario."""
import pytest

from climaraiz.scenario import assess_scenario, classify_exposure, METHOD


def check(events, kind="heat_days", phase="flowering", included=True):
    return {"definition": {"type": kind, "include_in_assessment": included}, "phase": phase,
            "variable": "T2M_MEAN", "status": "available", "reason": None,
            "event_definition": "test_event", "yearly_results": [
                {"year": year, "status": "available" if event is not None else "incomplete",
                 "event_occurred": event, "missing_days": 1 if event is None else 0}
                for year, event in events.items()]}


def assess(checks, first=2020, last=2023):
    return assess_scenario(checks, first, last, {"method": METHOD})


def test_joint_conditions_are_not_average_of_percentages_or_double_counted():
    first = check({2020: False, 2021: True, 2022: False, 2023: True})
    second = check({2020: False, 2021: False, 2022: True, 2023: True}, kind="dry_spell")
    result = assess([first, second])
    assert result["scenario_criteria_met_pct"] == 25
    assert result["years_meeting_criteria"] == 1
    assert result["years_not_meeting_criteria"] == 3  # Both events in 2023 still count once.
    assert len(result["yearly_assessment"][-1]["failed_checks"]) == 2
    assert result["years_with_events"] == 3
    assert result["exposure_frequency_pct"] == 75
    assert result["risk_level"] == "high"


@pytest.mark.parametrize("event,percentage,matched", [(True, 0, 0), (False, 100, 1)])
def test_zero_and_full_match_are_available_values(event, percentage, matched):
    result = assess([check({2020: event})], last=2020)
    assert result["status"] == "available"
    assert result["scenario_criteria_met_pct"] == percentage
    assert result["years_meeting_criteria"] == matched


def test_only_common_complete_years_form_denominator():
    result = assess([check({2020: False, 2021: False, 2022: None}),
                     check({2020: None, 2021: False, 2022: True}, kind="dry_spell")], last=2022)
    assert result["evaluated_years"] == 1
    assert result["scenario_criteria_met_pct"] == 100
    assert result["exposure_frequency_pct"] == 0
    assert result["risk_level"] == "low"
    assert [r["year"] for r in result["excluded_years"]] == [2020, 2022]


def test_descriptive_checks_are_excluded_explicitly():
    optional = check({2020: True}, kind="temperature_mean_peak", included=False)
    optional["status"] = "unavailable"
    optional["reason"] = "SOURCE_UNAVAILABLE"
    result = assess([check({2020: False}), optional], last=2020)
    assert result["scenario_criteria_met_pct"] == 100
    assert len(result["included_checks"]) == 1


@pytest.mark.parametrize("reason", ["PHASE_WINDOW_NOT_DEFINED", "SOURCE_UNAVAILABLE", "THRESHOLD_NOT_DEFINED"])
def test_missing_required_check_never_silently_disappears(reason):
    missing = check({})
    missing.update(status="unavailable", reason=reason)
    result = assess([check({2020: False}), missing], last=2020)
    assert result["status"] == "unavailable" and result["scenario_criteria_met_pct"] is None
    assert result["blocking_checks"][0]["reason"] == reason


def test_no_common_years_or_undefined_events_are_unavailable():
    result = assess([check({2020: False, 2021: None}), check({2020: None, 2021: False})], last=2021)
    assert result["reason"] == "NO_COMMON_COMPLETE_YEARS"
    assert result["years_meeting_criteria"] is None
    descriptive = check({2020: None})
    descriptive.pop("event_definition")
    result = assess([descriptive], last=2020)
    assert result["reason"] == "REQUIRED_CHECK_UNAVAILABLE"
    assert result["blocking_checks"][0]["reason"] == "EVENT_NOT_DEFINED"


def test_no_rules_or_unsupported_method_cannot_return_100_percent():
    assert assess([])["reason"] == "NO_CHECKS_INCLUDED"
    assert assess_scenario([], 2020, 2023, {"method": "average_percentages"})["reason"] == "UNSUPPORTED_ASSESSMENT_METHOD"


def corn_windows():
    # Syntax and reference-test fixture only, not a validated cultivar calendar.
    return [{"id": "flowering", "name": "Illustrative flowering", "start_day": 40, "end_day": 65},
            {"id": "pollination", "name": "Illustrative pollination", "start_day": 45, "end_day": 55}]


def test_reference_corn_scenario_and_calendar_detail_consistency(client, planting_request):
    planting_request["check_windows"] = corn_windows()
    created = client.post("/api/v1/planting/analyses", json=planting_request).json()
    calendar = client.get(created["links"]["result"]).json()
    assert len(calendar["dates"]) == 30
    selected = next(r for r in calendar["dates"] if r["date"] == "2027-04-25")
    result = selected["scenario_assessment"]
    assert result["evaluated_years"] == 25 and result["years_meeting_criteria"] == 10
    assert result["years_not_meeting_criteria"] == 15 and result["scenario_criteria_met_pct"] == 40
    assert "yearly_assessment" not in result
    detail = client.get(created["links"]["result"] + "/dates/2027-04-25").json()
    assert len(detail["scenario_assessment"]["yearly_assessment"]) == 25
    assert detail["scenario_assessment"]["scenario_criteria_met_pct"] == result["scenario_criteria_met_pct"]
    assert detail["historical_assessment"]["risk_level"] == "high"
    assert detail["risk_level"] == "high"
    assert detail["scenario_assessment"]["exposure_frequency_pct"] == 60
    assert detail["historical_assessment"]["favorable_frequency_pct"] is None
    assert next(c for c in detail["climate_checks"] if c["phase"] == "cycle")["window"]["end_day"] == 119
    assert client.post("/api/v1/planting/analyses", json=planting_request).json()["reused"] is True


def test_missing_phase_blocks_score_but_automatic_cycle_check_still_runs(client, planting_request):
    created = client.post("/api/v1/planting/analyses", json=planting_request).json()
    result = client.get(created["links"]["result"]).json()
    for record in result["dates"]:
        assert record["scenario_assessment"]["scenario_criteria_met_pct"] is None
        assert record["scenario_assessment"]["reason"] == "REQUIRED_CHECK_UNAVAILABLE"
        assert record["risk_level"] == "not_supported"
        assert record["scenario_assessment"]["exposure_frequency_pct"] is None
        assert next(c for c in record["climate_checks"] if c["phase"] == "cycle")["status"] == "available"


def test_missing_rain_day_excludes_year_from_combined_denominator(client, planting_request):
    with client.app.state.database.connect() as db:
        db.execute("UPDATE climate_daily SET value=NULL WHERE source_id='precipitation' AND date='2024-06-10'")
    planting_request["check_windows"] = corn_windows()
    created = client.post("/api/v1/planting/analyses", json=planting_request).json()
    detail = client.get(created["links"]["result"] + "/dates/2027-04-25").json()
    result = detail["scenario_assessment"]
    assert result["evaluated_years"] == 24
    assert result["years_meeting_criteria"] == 10
    assert result["scenario_criteria_met_pct"] == pytest.approx(1000/24)
    assert [r["year"] for r in result["excluded_years"]] == [2024]


def test_cycle_window_cannot_be_shortened(client, planting_request):
    planting_request["check_windows"] = [{"id": "cycle", "name": "Wrong", "start_day": 1, "end_day": 119}]
    assert client.post("/api/v1/planting/analyses", json=planting_request).status_code == 400


@pytest.mark.parametrize("crop_id", [2, 3])
def test_other_crops_use_own_rules_and_exclude_descriptive_temperature(client, planting_request, crop_id):
    planting_request["crop_id"] = crop_id
    planting_request["check_windows"] = [corn_windows()[0]]
    created = client.post("/api/v1/planting/analyses", json=planting_request).json()
    result = client.get(created["links"]["result"]).json()
    assert result["status"] == "completed" and len(result["dates"]) == 30
    first = result["dates"][0]
    assert first["scenario_assessment"]["status"] == "available"
    rain = next(c for c in first["climate_checks"] if c["definition"]["type"] == "rainfall_total")
    assert rain["definition"]["min_mm"] == (300 if crop_id == 2 else 500)
    if crop_id == 2:
        heat = next(c for c in first["climate_checks"] if c["definition"]["type"] == "heat_days")
        assert heat["definition"]["threshold_c"] == 30
    else:
        assert len(first["scenario_assessment"]["included_checks"]) == 2


def test_phase_route_uses_only_saved_rules_for_that_phase(client, planting_request):
    planting_request['phases'] = [
        {'id': 'initial', 'name': 'Initial', 'start_day': 0, 'end_day': 39},
        {'id': 'flowering', 'name': 'Flowering', 'start_day': 40, 'end_day': 65},
        {'id': 'remaining', 'name': 'Remaining', 'start_day': 66, 'end_day': 119}]
    planting_request['check_windows'] = [corn_windows()[1]]
    created = client.post('/api/v1/planting/analyses', json=planting_request).json()
    url = created['links']['result'] + '/dates/2027-04-25'
    response = client.get(url + '/phases')
    assert response.status_code == 200
    phases = response.json()['phases']
    flowering = phases[1]
    score = flowering['scenario_assessment']
    assert score['evaluated_years'] == 25
    assert score['years_meeting_criteria'] == 19
    assert score['scenario_criteria_met_pct'] == 76
    assert len(flowering['climate_checks']) == 1
    assert flowering['climate_checks'][0]['definition']['type'] == 'dry_spell'
    assert flowering['risk_level'] == 'moderate'
    assert flowering['assessment']['risk_level'] == 'moderate'
    assert score['exposure_frequency_pct'] == 24
    assert score['years_with_events'] == 6
    assert phases[0]['risk_level'] == 'not_supported'
    assert flowering['risk_level_reason'] is None
    assert phases[0]['scenario_assessment']['reason'] == 'NO_CHECKS_INCLUDED'
    assert phases[0]['scenario_assessment']['scenario_criteria_met_pct'] is None
    assert 'assessment_message' not in phases[0]
    assert 'assessment_message' not in flowering
    detail = client.get(url).json()
    assert detail['phases'] == phases
    assert detail['scenario_assessment']['scenario_criteria_met_pct'] == 40
    # Existing saved analyses receive the new response fields without rewriting
    # observations or replacing their saved checks with the current configuration.
    client.app.state.planting.windows['assessment']['method'] = 'changed_after_processing'
    assert client.get(url + '/phases').json()['phases'] == phases


def test_phase_score_excludes_missing_year_and_cannot_borrow_cycle_rules(client, planting_request):
    with client.app.state.database.connect() as db:
        db.execute("UPDATE climate_daily SET value=NULL WHERE source_id='precipitation' AND date='2024-06-10'")
    planting_request['phases'] = [
        {'id': 'initial', 'name': 'Initial', 'start_day': 0, 'end_day': 39},
        {'id': 'flowering', 'name': 'Flowering', 'start_day': 40, 'end_day': 65},
        {'id': 'remaining', 'name': 'Remaining', 'start_day': 66, 'end_day': 119}]
    created = client.post('/api/v1/planting/analyses', json=planting_request).json()
    url = created['links']['result'] + '/dates/2027-04-25/phases'
    phases = client.get(url).json()['phases']
    score = phases[1]['scenario_assessment']
    assert score['status'] == 'available'  # Missing pollination blocks only the full cycle.
    assert score['evaluated_years'] == 24
    assert [r['year'] for r in score['excluded_years']] == [2024]
    assert phases[2]['scenario_assessment']['status'] == 'unavailable'


@pytest.mark.parametrize("events,level", [(0, "low"), (2000, "low"), (2001, "moderate"),
                                           (4000, "moderate"), (4001, "high"), (10000, "high")])
def test_exposure_classification_inclusive_boundaries(events, level):
    result = classify_exposure({"status": "available", "evaluated_years": 10000,
                                "years_not_meeting_criteria": events})
    assert result["risk_level"] == level
    assert result["exposure_frequency_pct"] == pytest.approx(events / 100)
    assert result["classification_version"] == "historical-exposure-v1"


def test_unavailable_or_empty_assessment_never_gets_low_classification():
    for assessment in [{"status": "unavailable"}, {"status": "available", "evaluated_years": 0},
                       {"status": "available", "evaluated_years": 25}]:
        result = classify_exposure(assessment)
        assert result["risk_level"] == "not_supported"
        assert result["exposure_frequency_pct"] is None
