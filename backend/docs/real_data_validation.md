# Real-data exposure regression tests

`tests/test_real_exposure.py` exercises the check evaluator and joint classifier
with the actual versioned regional MERRA-2 daily dataset. No precipitation or
temperature observations are mocked, thresholds are unchanged, and the test does
not use the developer's active analysis database. The data are reanalysis, not
local weather-station observations or measured crop losses.

All reference scenarios use historical start years **2001–2025**, a **120-day**
cycle, flowering offsets **40–65**, and corn pollination offsets **45–55**.
These are illustrative scenario parameters, not validated cultivar phenology.
The year 2027 identifies the requested planting calendar, not a weather forecast.

| Crop | Planting date | Scope | Event years / complete years | Exposure | Classification |
| --- | --- | --- | --- | --- | --- |
| Milho | 2027-04-21 | Complete cycle | 14 / 25 | 56% | high |
| Milho | 2027-04-21 | Flowering | 6 / 25 | 24% | moderate |
| Milho | 2027-04-29 | Flowering | 5 / 25 | 20% | low |
| Milho | 2027-04-21 | Pollination | 0 / 25 | 0% | low |
| Feijão-preto | 2027-04-21 | Complete cycle | 6 / 25 | 24% | moderate |
| Feijão-preto | 2027-04-29 | Complete cycle | 5 / 25 | 20% | low |
| Girassol | 2027-04-11 | Complete cycle | 14 / 25 | 56% | high |
| Girassol | 2027-04-11 | Flowering | 8 / 25 | 32% | moderate |
| Girassol | 2027-04-29 | Flowering | 5 / 25 | 20% | low |

The direct numerical tests check every event year against an independent pandas
reference calculation. That reference uses rolling five-day rainfall windows,
explicit cycle rainfall benchmarks (500/300/500 mm), and explicit daily-mean
thermal thresholds, without calling the production dry-spell/event evaluator.
Expected counts and classes are fixed regressions, not dynamically taken from
the same function under test. A data or rule change therefore requires reviewing
the numerical references rather than silently accepting different values.

Three API integration cases verify low/moderate/high cycle results across the
calendar and date-detail responses, plus consistency with the phases endpoint.
They also verify that phases without criteria remain `not_supported` rather than
being classified as low exposure. The existing suite separately covers missing
data, common-year denominators, classification boundaries and unavailable rules.

Run from `backend/`, after preparing the environment described in the README:

```sh
.venv/bin/python -m pytest tests/test_real_exposure.py -v
.venv/bin/python -m pytest -q
```

The levels describe the frequency of configured historical exposures, not crop
loss probability, official ZARC classes, or evidence that one cultivar will yield
more than another. Zero events in the pollination mean-temperature check does
not rule out daily maximum-temperature extremes.
