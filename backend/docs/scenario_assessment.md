# Historical scenario criteria matching

The existing API routes are unchanged. This is an additional exploratory historical indicator, not a crop-risk class, a probability of loss/success, a forecast, or an official ZARC result.

## Configuration

`climaraiz/config/crops.json` now contains an `assessment` policy, rule-level `include_in_assessment` flags, and a source registry. Configuration and model versions are part of the analysis fingerprint. Changing thresholds or criteria creates a distinct analysis instead of reusing an old result. Existing saved results retain their old version; submit a new scenario to obtain this field.

| Crop | Whole-cycle rain benchmark | Flowering dry-spell event | Thermal event | Combined criteria |
| --- | --- | --- | --- | --- |
| 1 — Milho | Total <500 mm | At least 5 consecutive days <1 mm/day | At least one daily mean >33 °C in pollination | No event in any of these three checks |
| 2 — Feijão-preto | Total <300 mm | At least 5 consecutive days <1 mm/day | At least one daily mean >30 °C or <12 °C in flowering | No event in any of these four checks |
| 3 — Girassol | Total <500 mm | At least 5 consecutive days <1 mm/day | Highest daily mean is descriptive, not an event | No event in the two rainfall checks |

Rain exactly at the benchmark passes; there is no upper rainfall cutoff. Rain exactly 1 mm breaks a dry run. A run exactly five days triggers the dry-spell event. Temperature exactly at the configured threshold does not trigger a strict `>` or `<` event. The published water references do not make these gross-rainfall benchmarks equivalent to crop water balance. All are scenario criteria with explicit limitations.

## Request

`POST /api/v1/planting/analyses`, HTTP 202:

```json
{
  "municipality_id": 2504009,
  "crop_id": 1,
  "planting_year": 2027,
  "cycle_days": 120,
  "historical_period": {"start_year": 2001, "end_year": 2025},
  "check_windows": [
    {"id": "flowering", "name": "Illustrative flowering", "start_day": 40, "end_day": 65},
    {"id": "pollination", "name": "Illustrative pollination", "start_day": 45, "end_day": 55}
  ]
}
```

The offsets are illustrative user scenarios, **not agronomic recommendations**. The server automatically resolves `cycle` to inclusive offsets 0–119. Flowering and pollination must be supplied as `check_windows` or compatible `phases`; the server does not invent their timing. `check_windows` may overlap. Existing `phases` still partition the cycle. A supplied `cycle` ID must cover the complete duration or request validation returns HTTP 400.

## Calendar and detail

- `GET /api/v1/planting/analyses/{id}` returns `dates[].scenario_assessment` for all 30 dates.
- `GET /api/v1/planting/analyses/{id}/dates/{date}` includes the same summary plus `yearly_assessment`.
- `GET /api/v1/crops` returns the assessment policy and source registry.
- The phases route continues to return the submitted partition's per-phase exposure. Overlapping check results remain in `climate_checks` on calendar/date responses and also appear in explicitly linked phase cards.

For April 25 in the example above, the scenario has 25 common complete years and 10 matching years: `scenario_criteria_met_pct` is **40**. Detailed yearly entries contain `year`, `status`, `criteria_met`, and `failed_checks`. A year failing two checks counts once among `years_not_meeting_criteria`.

## Formula and missing data

`100 × years_meeting_criteria / evaluated_years`

`evaluated_years` includes only years complete in **all** included checks. For instance, if one check has 25 complete years and another has 24, the score uses the 24 common years, not different denominators. `excluded_years` records year, affected check and missing-day count. Per-check frequencies can retain different denominators; they are not averaged into the combined result.

If a required phase or source is unavailable, the combined response has `status: unavailable`, `reason: REQUIRED_CHECK_UNAVAILABLE`, null counts/percentage, and explanatory `blocking_checks`. Missing windows are not reported as zero exposure. If observations exist but there are no common complete years, reason is `NO_COMMON_COMPLETE_YEARS`. A descriptive check deliberately included without an event definition blocks the result with `EVENT_NOT_DEFINED`. No included checks returns `NO_CHECKS_INCLUDED`.

## Frontend wording

Display `scenario_criteria_met_pct` alongside its numerator, denominator and exclusions. Label it **Historical scenario criteria match**. Display unavailable rather than 0% for missing windows/data. Show individual conditions and sources on the selected-date panel. Do not present this value as `favorable_frequency_pct`, rename it to crop-loss probability, invent additional risk bands, or compare different crop definitions as equivalent risk scores.

## Phase cards

`GET /api/v1/planting/analyses/{id}/dates/{date}/phases` now returns
`climate_checks`, `scenario_assessment`, `risk_level` and `risk_level_reason`
inside each phase. The date-detail route exposes the identical phase objects.
Checks explicitly linked by `check_windows[].phase_id` participate in that segment. Without a link, legacy exact matching of check-window and phase IDs is preserved.
A whole-cycle rain benchmark is not applied to shorter phases, and a nested
pollination window is not silently relabeled as flowering. Phase names are
presentation labels; matching uses IDs. Checks for windows submitted only in
`check_windows` remain in the date's `climate_checks`. Separate windows appear
in phase cards when explicitly linked; no phase partition is invented.

The percentage uses common complete years for the included phase checks.
For the reference corn scenario, a submitted `flowering` phase at days 40–65
has 19 of 25 years without the configured dry-spell event, or 76%, whereas
the full-cycle criteria match remains 40%. These are different assessments.

```json
{
  "id": "flowering",
  "risk_level": "moderate",
  "risk_level_reason": null,
  "scenario_assessment": {
    "status": "available",
    "evaluated_years": 25,
    "years_meeting_criteria": 19,
    "scenario_criteria_met_pct": 76,
    "exposure_frequency_pct": 24,
    "years_with_events": 6,
    "risk_level": "moderate"
  }
}
```

Show “76% of historical years met the phase criteria” on the card. Exposure is `low` for frequencies up to 20%, `moderate` above 20% through
40%, and `high` above 40%. These are exploratory MVP bands, not official
agricultural risk categories. A phase without included checks returns
`NO_CHECKS_INCLUDED` and a null percentage, not 100% or low risk. Missing data
follows the same exclusion and blocking policies as the full-cycle assessment.

Phase summaries are derived on retrieval from the analysis's saved check
results and assessment configuration, so previously completed scenario
analyses also expose these fields without resubmission. Older analyses without
a saved assessment policy remain unavailable; current rules are never applied
retroactively to their stored results.


Unavailable risk classifications use `risk_level: "not_supported"`, including
previously saved analyses. No separate `assessment_message` is returned.
The frontend can translate this value to its preferred unavailable-analysis copy.
Technical reasons remain in `scenario_assessment.reason` and `blocking_checks`.


## Exposure bands: historical-exposure-v1

Classification uses `100 * years_not_meeting_criteria / evaluated_years`, with
no rounding before comparison. Each year counts once even if several included
checks fail. `years_with_events` equals `years_not_meeting_criteria`; it is null
when unavailable. `risk_basis` is `historical_configured_event_frequency`.
`classification_thresholds` exposes `low_max_pct: 20` and `moderate_max_pct: 40`.
Unavailable, missing-window and empty-common-calendar results always return
`risk_level: not_supported` and null frequency. No additional sample-size cutoff
is imposed, so the sample size and exclusions must accompany the display.

The date root and `historical_assessment.risk_level` mirror the combined scenario
classification. The phase root and `assessment.risk_level` mirror that phase's
classification. No phase percentages are averaged to produce the cycle class.

The reference cycle is high exposure (15/25 = 60%); flowering is moderate
exposure (6/25 = 24%). These empirical counts do not establish probability of
crop loss, official planting eligibility, severity, or a forecast. The 20/40
bands are a product convention inspired by the frequency landmarks described
in the [MAPA rural insurance guide](https://www.gov.br/agricultura/pt-br/assuntos/riscos-seguro/seguro-rural/guia-do-seguro-rural-2022-2-ed.pdf),
not a replacement for its water-balance and crop-specific methodology.

Classifications are derived on retrieval for already saved results as well.
Their check definitions, observations and yearly results remain unchanged;
`classification_version` identifies the display policy applied now. Older
results without assessment counts remain not_supported. Existing client code
that assumed risk_level was always null/not_supported must now handle
low, moderate and high as exploratory exposure categories.


## Explicit phase associations (API 0.4.0)

See [window-to-phase bindings](phase_window_bindings.md) for the full request,
validation rules, numerical example and migration instructions. `phase_id`
links a criterion window to a submitted segment while preserving their distinct
IDs and intervals. Previously saved scenarios are not silently reassigned.
