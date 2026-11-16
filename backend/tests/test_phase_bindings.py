"""Explicit window-to-segment binding without changing rule IDs or old scenarios."""
from copy import deepcopy

import pytest
from pydantic import ValidationError

from climaraiz.models import PlantingRequest


def bound_request():
    # Illustrative windows only; not validated cultivar development timings.
    return {'municipality_id': 2504009, 'crop_id': 1, 'planting_year': 2027,
            'cycle_days': 120, 'historical_period': {'start_year': 2001, 'end_year': 2025},
            'phases': [
                {'id': 'germinacao', 'name': 'Germinação', 'start_day': 0, 'end_day': 14},
                {'id': 'floracao', 'name': 'Floração', 'start_day': 15, 'end_day': 65},
                {'id': 'enchimento', 'name': 'Enchimento', 'start_day': 66, 'end_day': 99},
                {'id': 'maturacao', 'name': 'Maturação', 'start_day': 100, 'end_day': 119}],
            'check_windows': [
                {'id': 'flowering', 'phase_id': 'floracao', 'name': 'Dry-spell window', 'start_day': 40, 'end_day': 65},
                {'id': 'pollination', 'phase_id': 'floracao', 'name': 'Heat window', 'start_day': 45, 'end_day': 55}]}


@pytest.mark.parametrize('first,last', [(15, 65), (15, 15), (65, 65), (40, 60)])
def test_linked_window_can_touch_inclusive_phase_boundaries(first, last):
    body = bound_request()
    body['check_windows'][0].update(start_day=first, end_day=last)
    parsed = PlantingRequest.model_validate(body)
    assert parsed.check_windows[0].phase_id == 'floracao'


@pytest.mark.parametrize('change', ['unknown_phase', 'no_phases', 'starts_outside', 'ends_outside',
                                    'crosses_segments', 'invalid_id', 'phase_has_phase_id'])
def test_invalid_bindings_return_public_validation_error(client, change):
    body = bound_request()
    window = body['check_windows'][0]
    if change == 'unknown_phase':
        window['phase_id'] = 'missing'
    elif change == 'no_phases':
        body['phases'] = []
    elif change == 'starts_outside':
        window['start_day'] = 14
    elif change == 'ends_outside':
        window['end_day'] = 66
    elif change == 'crosses_segments':
        window.update(start_day=0, end_day=119)
    elif change == 'invalid_id':
        window['phase_id'] = 'invalid id!'
    else:
        body['phases'][0]['phase_id'] = 'floracao'
    with pytest.raises(ValidationError):
        PlantingRequest.model_validate(body)
    response = client.post('/api/v1/planting/analyses', json=body)
    assert response.status_code == 400
    assert response.json()['error']['code'] == 'INVALID_REQUEST'


def create(client, body):
    response = client.post('/api/v1/planting/analyses', json=body)
    assert response.status_code == 202, response.text
    return response.json()


def test_real_linked_phase_combines_windows_and_preserves_unbound_saved_analysis(client):
    linked = bound_request()
    unbound = deepcopy(linked)
    for window in unbound['check_windows']:
        window.pop('phase_id')
    original = create(client, unbound)
    created = create(client, linked)
    assert original['analysis_id'] != created['analysis_id']
    url = created['links']['result']
    calendar = client.get(url).json()
    detail = client.get(url + '/dates/2027-04-25').json()
    phases = client.get(url + '/dates/2027-04-25/phases').json()['phases']
    flowering = phases[1]
    assert detail['phases'] == phases
    assert flowering['id'] == 'floracao' and flowering['name'] == 'Floração'
    assert {c['phase'] for c in flowering['climate_checks']} == {'flowering', 'pollination'}
    assert {c['window']['phase_id'] for c in flowering['climate_checks']} == {'floracao'}
    assert flowering['risk_level'] == 'moderate'
    score = flowering['scenario_assessment']
    assert score['evaluated_years'] == 25 and score['years_with_events'] == 6
    assert score['exposure_frequency_pct'] == 24
    assert score['scenario_criteria_met_pct'] == 76
    assert len(score['yearly_assessment']) == 25
    for phase in (phases[0], phases[2], phases[3]):
        assert phase['risk_level'] == 'not_supported'
        assert phase['risk_level_reason'] == 'NO_CHECKS_INCLUDED'
    assert detail['scenario_assessment']['exposure_frequency_pct'] == 60
    assert detail['risk_level'] == 'high'
    row = next(row for row in calendar['dates'] if row['date'] == '2027-04-25')
    assert row['scenario_assessment']['exposure_frequency_pct'] == 60
    original_phases = client.get(original['links']['result'] + '/dates/2027-04-25/phases').json()['phases']
    assert all(p['risk_level'] == 'not_supported' for p in original_phases)
    assert client.get(original['links']['result']).json()['dates'][4]['scenario_assessment']['exposure_frequency_pct'] == 60
    assert create(client, linked)['reused'] is True


def test_linked_phase_uses_common_complete_years(client):
    with client.app.state.database.connect() as db:
        # Inside flowering, outside pollination: only the dry-spell check loses a year.
        db.execute("UPDATE climate_daily SET value=NULL WHERE source_id='precipitation' AND date='2024-06-25'")
    created = create(client, bound_request())
    phases = client.get(created['links']['result'] + '/dates/2027-04-25/phases').json()['phases']
    phase = phases[1]
    checks = {c['phase']: c for c in phase['climate_checks']}
    assert checks['flowering']['evaluated_years'] == 24
    assert checks['pollination']['evaluated_years'] == 25
    assert phase['scenario_assessment']['evaluated_years'] == 24
    assert [r['year'] for r in phase['scenario_assessment']['excluded_years']] == [2024]


def test_explicit_whole_cycle_binding_is_not_overwritten_by_automatic_window(client):
    body = bound_request()
    body['phases'] = [{'id': 'ciclo', 'name': 'Ciclo completo', 'start_day': 0, 'end_day': 119}]
    for window in body['check_windows']:
        window['phase_id'] = 'ciclo'
    body['check_windows'].append({'id': 'cycle', 'phase_id': 'ciclo', 'name': 'Cycle rainfall',
                                  'start_day': 0, 'end_day': 119})
    created = create(client, body)
    detail = client.get(created['links']['result'] + '/dates/2027-04-25').json()
    phase = detail['phases'][0]
    assert len(phase['climate_checks']) == 3
    cycle = next(check for check in phase['climate_checks'] if check['phase'] == 'cycle')
    assert cycle['window']['phase_id'] == 'ciclo'
    assert phase['scenario_assessment'] == detail['scenario_assessment']
