"""Numerical regression of exposure classes against unmodified regional NASA data.

The 120-day cycle and phase offsets are test scenarios, not cultivar guidance.
These service-level tests do not mock climate observations or adjust thresholds.
"""
from datetime import date, timedelta
import json
from pathlib import Path

import pandas as pd
import pytest

from climaraiz.checks import evaluate_check
from climaraiz.models import ScenarioPhase
from climaraiz.scenario import assess_scenario

ROOT = Path(__file__).resolve().parents[1]
# Crop, planting date, scope, number of event years, expected exposure class.
CASES = [
    (1, '2027-04-21', 'overall', 14, 'high'),
    (1, '2027-04-21', 'flowering', 6, 'moderate'),
    (1, '2027-04-29', 'flowering', 5, 'low'),
    (1, '2027-04-21', 'pollination', 0, 'low'),
    (2, '2027-04-21', 'overall', 6, 'moderate'),
    (2, '2027-04-29', 'overall', 5, 'low'),
    (3, '2027-04-11', 'overall', 14, 'high'),
    (3, '2027-04-11', 'flowering', 8, 'moderate'),
    (3, '2027-04-29', 'flowering', 5, 'low'),
]


@pytest.fixture(scope='module')
def real_observations():
    data = pd.read_csv(ROOT / 'data/climate_daily.csv', parse_dates=['date']).set_index('date')
    assert len(data) == 9497
    assert data.precipitation_quality.eq('valid').all()
    assert data.temperature_quality.eq('valid').all()
    return data


@pytest.fixture(scope='module')
def real_configuration():
    return json.loads((ROOT / 'climaraiz/config/crops.json').read_text())


def independent_event_years(data, crop_id, planting_date, scope):
    """Reference calculation via rolling dry windows, independent of service checks.

    Benchmarks are deliberately explicit here so changing production rules alone
    cannot silently change the reference test's definition of an event.
    """
    events = []
    for year in range(2001, 2026):
        start = date(year, planting_date.month, planting_date.day)
        cycle = data.loc[str(start):str(start + timedelta(days=119))]
        flowering = data.loc[str(start + timedelta(days=40)):str(start + timedelta(days=65))]
        pollination = data.loc[str(start + timedelta(days=45)):str(start + timedelta(days=55))]
        assert len(cycle) == 120 and len(flowering) == 26 and len(pollination) == 11
        dry = (flowering.precipitation_mm.lt(1).astype(int).rolling(5).sum() == 5).any()
        heat = (pollination.temperature_mean_c.gt(33).any() if crop_id == 1
                else (flowering.temperature_mean_c.gt(30) | flowering.temperature_mean_c.lt(12)).any()
                if crop_id == 2 else False)
        if scope == 'overall':
            exposed = cycle.precipitation_mm.sum() < (300 if crop_id == 2 else 500) or dry or heat
        elif scope == 'flowering':
            exposed = dry or (heat if crop_id == 2 else False)
        else:
            assert crop_id == 1 and scope == 'pollination'
            exposed = heat
        if exposed:
            events.append(year)
    return events


@pytest.mark.parametrize('crop_id,day,scope,events,level', CASES,
                         ids=[f'crop{c}-{d}-{s}-{level}' for c, d, s, _, level in CASES])
def test_real_observations_produce_reference_classes(real_observations, real_configuration,
                                                    crop_id, day, scope, events, level):
    crop = next(c for c in real_configuration['crops'] if c['id'] == crop_id)
    frames = {
        'precipitation': real_observations[['precipitation_mm']].rename(columns={'precipitation_mm': 'value'}),
        'temperature_mean': real_observations[['temperature_mean_c']].rename(columns={'temperature_mean_c': 'value'})}
    windows = {key: ScenarioPhase(id=key, name=key, start_day=a, end_day=b)
               for key, a, b in [('cycle', 0, 119), ('flowering', 40, 65), ('pollination', 45, 55)]}
    checks = [evaluate_check(rule, windows, frames, date.fromisoformat(day), 2001, 2025)
              for rule in crop['climate_checks'] if scope == 'overall' or rule['phase'] == scope]
    score = assess_scenario(checks, 2001, 2025, real_configuration['assessment'])
    expected_years = independent_event_years(real_observations, crop_id, date.fromisoformat(day), scope)
    actual_years = [r['year'] for r in score['yearly_assessment'] if r['criteria_met'] is False]
    assert actual_years == expected_years
    assert len(expected_years) == events
    assert score['status'] == 'available'
    assert score['evaluated_years'] == 25
    assert score['excluded_years'] == []
    assert score['years_with_events'] == events
    assert score['exposure_frequency_pct'] == pytest.approx(100 * events / 25)
    assert score['scenario_criteria_met_pct'] == pytest.approx(100 * (25 - events) / 25)
    assert score['risk_level'] == level


@pytest.mark.parametrize('crop_id,day,events,level', [
    (1, '2027-04-21', 14, 'high'),
    (2, '2027-04-21', 6, 'moderate'),
    (2, '2027-04-29', 5, 'low')])
def test_real_classifications_are_consistent_across_api_routes(client, planting_request,
                                                              crop_id, day, events, level):
    planting_request.update(crop_id=crop_id, phases=[
        {'id': 'initial', 'name': 'Illustrative initial', 'start_day': 0, 'end_day': 39},
        {'id': 'flowering', 'name': 'Illustrative flowering', 'start_day': 40, 'end_day': 65},
        {'id': 'remaining', 'name': 'Illustrative remaining', 'start_day': 66, 'end_day': 119}],
        check_windows=[{'id': 'pollination', 'name': 'Illustrative pollination', 'start_day': 45, 'end_day': 55}])
    created = client.post('/api/v1/planting/analyses', json=planting_request)
    assert created.status_code == 202
    url = created.json()['links']['result']
    calendar = client.get(url).json()
    record = next(r for r in calendar['dates'] if r['date'] == day)
    detail = client.get(url + '/dates/' + day).json()
    for result in (record, detail):
        assert result['risk_level'] == level
        assert result['historical_assessment']['risk_level'] == level
        assert result['scenario_assessment']['risk_level'] == level
        assert result['scenario_assessment']['years_with_events'] == events
        assert result['scenario_assessment']['exposure_frequency_pct'] == 100 * events / 25
    phase_response = client.get(url + '/dates/' + day + '/phases')
    assert phase_response.status_code == 200
    assert phase_response.json()['phases'] == detail['phases']
    flowering = detail['phases'][1]
    assert flowering['risk_level'] == ('low' if day.endswith('04-29') else 'moderate')
    assert detail['phases'][0]['risk_level'] == 'not_supported'
