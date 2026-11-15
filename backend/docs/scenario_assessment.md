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
- The phases route continues to return the submitted partition's per-phase exposure. Overlapping check results remain in `climate_checks` on calendar/date responses.

For April 25 in the example above, the scenario has 25 common complete years and 10 matching years: `scenario_criteria_met_pct` is **40**. Detailed yearly entries contain `year`, `status`, `criteria_met`, and `failed_checks`. A year failing two checks counts once among `years_not_meeting_criteria`.

## Formula and missing data

`100 × years_meeting_criteria / evaluated_years`

`evaluated_years` includes only years complete in **all** included checks. For instance, if one check has 25 complete years and another has 24, the score uses the 24 common years, not different denominators. `excluded_years` records year, affected check and missing-day count. Per-check frequencies can retain different denominators; they are not averaged into the combined result.

If a required phase or source is unavailable, the combined response has `status: unavailable`, `reason: REQUIRED_CHECK_UNAVAILABLE`, null counts/percentage, and explanatory `blocking_checks`. Missing windows are not reported as zero exposure. If observations exist but there are no common complete years, reason is `NO_COMMON_COMPLETE_YEARS`. A descriptive check deliberately included without an event definition blocks the result with `EVENT_NOT_DEFINED`. No included checks returns `NO_CHECKS_INCLUDED`.

## Frontend wording

Display `scenario_criteria_met_pct` alongside its numerator, denominator and exclusions. Label it **Historical scenario criteria match**. Display unavailable rather than 0% for missing windows/data. Show individual conditions and sources on the selected-date panel. Do not present this value as `favorable_frequency_pct`, rename it to crop-loss probability, infer risk bands, or compare different crop definitions as equivalent risk scores.
