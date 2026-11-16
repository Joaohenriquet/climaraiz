"""Minimum phase exposure: boundaries, real data and all-card API responses."""
from copy import deepcopy
from datetime import date
import json
from pathlib import Path

import pandas as pd
import pytest

from climaraiz.checks import evaluate_check
from climaraiz.models import ScenarioPhase
from climaraiz.scenario import assess_scenario

ROOT = Path(__file__).resolve().parents[1]
WET_RULE = {'type': 'rainy_days', 'phase': 'maturation', 'variable': 'PRECTOTCORR',
            'rain_at_least_mm': 1, 'min_days': 6, 'window_days': 10,
            'ends_at_cycle_end': True, 'include_in_assessment': True}


def wet_check(values, first=0, last=9, cycle=10, planting=date(2027, 1, 1)):
    index = pd.date_range(date(2020, planting.month, planting.day), periods=len(values))
    window = ScenarioPhase(id='maturation', name='Pre-harvest', start_day=first, end_day=last)
    return evaluate_check(WET_RULE, {'maturation': window},
                          {'precipitation': pd.DataFrame({'value': values}, index=index)},
                          planting, 2020, 2020, cycle_days=cycle)


@pytest.mark.parametrize('values,event,count', [
    ([1, 0, 1, 0, 1, 0, 1, 0, 1, .999], False, 5),
    ([1, 0, 1, 0, 1, 0, 1, 0, 1, 1], True, 6),
    ([1, 1, 1, 0, 1, 0, 1, 0, 1, 1], True, 7),
    ([0] * 10, False, 0)])
def test_rainy_days_counts_nonconsecutive_days_with_inclusive_boundaries(values, event, count):
    check = wet_check(values)
    assert check['status'] == 'available' and check['unit'] == 'days'
    assert check['yearly_results'][0]['value'] == count
    assert check['yearly_results'][0]['event_occurred'] is event


def test_missing_day_is_excluded_not_counted_as_dry():
    check = wet_check([1] * 9 + [None])
    assert check['reason'] == 'NO_COMPLETE_PHASE_YEARS'
    assert check['excluded_years'] == [{'year': 2020, 'missing_days': 1}]
    assert check['yearly_results'][0]['event_occurred'] is None


@pytest.mark.parametrize('first,last,cycle,reason', [
    (0, 8, 10, 'WINDOW_DURATION_MISMATCH'),
    (0, 19, 20, 'WINDOW_DURATION_MISMATCH'),
    (0, 9, 20, 'WINDOW_NOT_AT_CYCLE_END'),
    (0, 9, None, 'CYCLE_DURATION_REQUIRED')])
def test_preharvest_window_must_be_exactly_the_final_ten_days(first, last, cycle, reason):
    check = wet_check([1] * 20, first, last, cycle)
    assert check['status'] == 'unavailable' and check['reason'] == reason


def test_preharvest_window_can_cross_december():
    check = wet_check([1] * 6 + [0] * 4, planting=date(2027, 12, 25))
    row = check['yearly_results'][0]
    assert row['historical_end'] == '2021-01-03'
    assert row['event_occurred'] is True


@pytest.mark.parametrize('phase', ['germination', 'grain_filling'])
def test_new_dry_checks_require_five_observable_days(phase):
    rule = {'type': 'dry_spell', 'phase': phase, 'variable': 'PRECTOTCORR',
            'rain_below_mm': 1, 'min_consecutive_days': 5, 'min_window_days': 5}
    window = ScenarioPhase(id=phase, name=phase, start_day=0, end_day=3)
    result = evaluate_check(rule, {phase: window}, {}, date(2027, 1, 1), 2020, 2020)
    assert result['reason'] == 'WINDOW_TOO_SHORT'


def test_only_absent_optional_windows_are_omitted():
    optional = {'definition': {'type': 'rainy_days', 'include_in_assessment': True,
                              'optional_when_window_missing': True},
                'phase': 'maturation', 'variable': 'PRECTOTCORR', 'status': 'unavailable',
                'reason': 'PHASE_WINDOW_NOT_DEFINED'}
    policy = {'method': 'all_included_checks_without_events'}
    result = assess_scenario([optional], 2001, 2025, policy)
    assert result['risk_level'] == 'not_supported'
    assert result['omitted_optional_checks'][0]['phase'] == 'maturation'
    for reason in ['SOURCE_UNAVAILABLE', 'WINDOW_DURATION_MISMATCH', 'WINDOW_NOT_AT_CYCLE_END']:
        bad = deepcopy(optional)
        bad['reason'] = reason
        result = assess_scenario([bad], 2001, 2025, policy)
        assert result['reason'] == 'REQUIRED_CHECK_UNAVAILABLE'
        assert result['omitted_optional_checks'] == []


def longest_dry(series):
    # Independent rolling calculation rather than the production run counter.
    return any(series.lt(1).astype(int).rolling(5).sum().eq(5))


@pytest.mark.parametrize('crop_id', [1, 2, 3])
def test_all_four_phase_cards_classify_real_data_and_match_independent_years(client, crop_id):
    body = json.loads((ROOT / 'docs/requests/all_phase_analysis.json').read_text())
    body['crop_id'] = crop_id
    created = client.post('/api/v1/planting/analyses', json=body)
    assert created.status_code == 202
    url = created.json()['links']['result']
    day = '2027-04-25'  # Inside all three supplied planting windows.
    response = client.get(url + '/dates/' + day)
    assert response.status_code == 200
    detail = response.json()
    phases = detail['phases']
    assert len(phases) == 4
    assert all(p['risk_level'] in ('low', 'moderate', 'high') for p in phases)
    assert all(p['scenario_assessment']['evaluated_years'] == 25 for p in phases)
    assert detail['scenario_assessment']['omitted_optional_checks'] == []
    data = pd.read_csv(ROOT / 'data/climate_daily.csv', parse_dates=['date']).set_index('date')
    expected = {p['id']: [] for p in phases}
    reference_counts = {'germinacao': 4, 'floracao': 6, 'enchimento': 14, 'maturacao': 9}
    all_events = []
    for year in range(2001, 2026):
        start = pd.Timestamp(year=year, month=4, day=25)
        def segment(a, b):
            return data.loc[start + pd.Timedelta(days=a):start + pd.Timedelta(days=b)]
        dry_flowering = longest_dry(segment(40, 65).precipitation_mm)
        hot = (segment(45, 55).temperature_mean_c.gt(33).any() if crop_id == 1
               else (segment(40, 65).temperature_mean_c.gt(30) |
                     segment(40, 65).temperature_mean_c.lt(12)).any() if crop_id == 2 else False)
        events = {
            'germinacao': longest_dry(segment(0, 14).precipitation_mm),
            'floracao': dry_flowering or hot,
            'enchimento': longest_dry(segment(66, 99).precipitation_mm),
            'maturacao': segment(110, 119).precipitation_mm.ge(1).sum() >= 6}
        for key, occurred in events.items():
            if occurred:
                expected[key].append(year)
        if any(events.values()) or segment(0, 119).precipitation_mm.sum() < (300 if crop_id == 2 else 500):
            all_events.append(year)
    for phase in phases:
        score = phase['scenario_assessment']
        actual = [r['year'] for r in score['yearly_assessment'] if r['criteria_met'] is False]
        assert actual == expected[phase['id']]
        assert len(actual) == reference_counts[phase['id']]
        assert score['exposure_frequency_pct'] == 100 * len(actual) / 25
        assert phase['assessment']['risk_level'] == phase['risk_level']
    overall = detail['scenario_assessment']
    assert [r['year'] for r in overall['yearly_assessment'] if r['criteria_met'] is False] == all_events
    summary = next(row for row in client.get(url).json()['dates'] if row['date'] == day)
    assert summary['risk_level'] == detail['risk_level']
    assert summary['scenario_assessment']['exposure_frequency_pct'] == overall['exposure_frequency_pct']
    assert client.get(url + '/dates/' + day + '/phases').json()['phases'] == phases
    print(crop_id, [(p['id'], p['risk_level'], p['scenario_assessment']['exposure_frequency_pct']) for p in phases])
