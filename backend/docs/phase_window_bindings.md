# Linking check windows to cycle segments

## Problem and resulting behavior

`phases` partitions the user-selected cycle into display/analysis segments.
`check_windows` identifies the intervals used by configured crop criteria.
Those are different concepts: a segment can have an arbitrary ID such as
`floracao`, while checks still select `flowering` and `pollination` rules.
Previously phase summaries required equal IDs, so valid overall checks could
coexist with `NO_CHECKS_INCLUDED` on every phase card.

API 0.4.0 adds optional `phase_id` to **check windows only**. It references a
submitted phase without changing the check window ID, the crop rules, their
thresholds, or their evaluation intervals. Multiple overlapping windows can
link to the same phase. Response `climate_checks[].phase` remains the criterion
window ID; `climate_checks[].window.phase_id` records the segment association.

## Complete example

`POST /api/v1/planting/analyses`:

```json
{
  "municipality_id": 2504009,
  "crop_id": 1,
  "planting_year": 2027,
  "cycle_days": 120,
  "historical_period": {"start_year": 2001, "end_year": 2025},
  "phases": [
    {"id": "germinacao", "name": "Germinação", "start_day": 0, "end_day": 14},
    {"id": "floracao", "name": "Floração", "start_day": 15, "end_day": 65},
    {"id": "enchimento", "name": "Enchimento", "start_day": 66, "end_day": 99},
    {"id": "maturacao", "name": "Maturação", "start_day": 100, "end_day": 119}
  ],
  "check_windows": [
    {"id": "flowering", "phase_id": "floracao", "name": "Dry-spell window", "start_day": 40, "end_day": 65},
    {"id": "pollination", "phase_id": "floracao", "name": "Heat window", "start_day": 45, "end_day": 55}
  ]
}
```

These offsets are illustrative user scenarios, not validated cultivar dates.
They intentionally distinguish the 15–65 segment from its narrower check
windows. Linking windows does not evaluate each criterion across the entire
segment, nor does it prove all possible risks in that segment were assessed.

After POST returns HTTP 202, poll its result URL until completed. Use the new
`analysis_id` for `/dates/2027-04-25` and `/dates/2027-04-25/phases`.
For the unchanged regional 2001–2025 dataset:

- Overall: 15/25 event years, 60% exposure, `risk_level: high`.
- `floracao`: 6/25 event years across its two linked windows, 24% exposure,
  76% criteria match, `risk_level: moderate`.
- Germination, grain filling and maturation: `not_supported` with
  `risk_level_reason: NO_CHECKS_INCLUDED`; their new optional criteria have no windows in this legacy example.

Each year is counted once even if both checks fail. A linked phase uses only
common complete years in its included checks, with exclusions preserved. The
whole-cycle rainfall benchmark remains an overall check and is not attributed
to a shorter segment. Overall assessment is still computed independently from
all included criteria, never by averaging card percentages. Exposure levels
remain exploratory, not crop-loss probabilities or official ZARC classes.

## Validation

Invalid links return HTTP 400 with `error.code: INVALID_REQUEST`:

- `phase_id` must reference an existing entry in the same request's `phases`.
- The full inclusive interval must lie inside that phase; touching either
  boundary is valid. Partial overlap or crossing segments is rejected.
- Supplying `phase_id` without submitted phases is rejected.
- `phase_id` is not a supported property of a phase itself.

Existing constraints remain: phases cover the complete cycle without gaps or
overlap; check windows can overlap but remain within the cycle; window and phase
IDs are unique across both arrays. The reserved `cycle` window must span the
whole cycle. If explicitly linked to a whole-cycle segment, its association is
preserved rather than overwritten by automatic window resolution.

## Compatibility and migration

Without `phase_id` (or with null), legacy exact-ID association is preserved:
a check whose window ID equals a submitted phase ID contributes to that phase.
There is no inferred association from Portuguese names, matching dates or
geometric overlap. Unbound separate windows can still contribute to the overall
assessment without contributing to any phase card.

Bindings are persisted in the saved request, resolved windows and check results.
Bindings were introduced in model `historical-exposure-v5-phase-bindings`;
API 0.5.0 uses `historical-exposure-v6-minimum-phase-criteria`. A new request with
bindings produces a new analysis ID. Repeating that same request reuses it.
Previously completed analyses are not rewritten or silently rebound: the old
ID retains its old windows and missing-association result. Submit the updated
request and use its new ID. Renaming display segments is not required.

## Verification

`tests/test_phase_bindings.py` covers inclusive boundaries, unknown/missing
phases, crossing intervals, public HTTP validation, real-data combined phase
results, common-year exclusions, persisted old/new analyses, request reuse and
explicit whole-cycle associations. Existing exact-ID scenarios remain covered
by the full suite. `tests/smoke_server.py` also checks explicit bindings for all
three crops against a running HTTP server. Actual request/response examples are
in [api_examples.json](api_examples.json).


For all four cards to classify under API 0.5.0, use the
[complete minimum-profile request](requests/all_phase_analysis.json). The example
above deliberately retains its original limited window set.
