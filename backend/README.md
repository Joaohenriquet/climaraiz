# ClimaRaiz API

A local Python application for historical climate exploration and planting-window scenarios in **Campina Grande, Paraíba, Brazil**. Includes a browser dashboard, a FastAPI REST API, SQLite storage, a CSV importer, reproducible statistics, and automated tests. Code, API fields, documentation, and interface are in English.

## Run locally

From `climaraiz/backend/`, create an environment with Python 3.9 or newer:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[test]'
.venv/bin/python -m climaraiz serve
```

Open **http://127.0.0.1:8000**. Interactive OpenAPI documentation is at **/docs**, with the schema at **/openapi.json**.

In the existing Nasa workspace, dependencies are also available in `Nasa/.venv`. From `climaraiz/backend/`, start directly with:

```sh
../../.venv/bin/python -m climaraiz serve
```

The server binds to loopback, runs one worker, and needs no external API credentials or network calls. There is no live ZARC connection. This is a single-user local MVP, without authentication, a production job queue, or deployment configuration.

## Sources and daily preparation

`data/sources.json` identifies the supplied raw CSV files copied to `data/sources/`. Raw files are local inputs and are ignored by Git. On first startup, existing raw files are imported into `data/climaraiz.sqlite3` if needed. A **fresh Git clone also works without those raw files**: the server loads the versioned `data/climate_daily.csv` and `data/prepared_sources.json` bundle, verifies its SHA-256, validates the complete calendar and daily units, and rechecks the grid coordinates before importing. The prepared manifest retains the original source metadata and hashes; it explicitly reports that the original raw bytes were not reverified during prepared-bundle startup.

| Variable | Product | Input | Prepared daily data |
| --- | --- | --- | --- |
| Precipitation | M2T1NXFLX_5_12_4_PRECTOTCORR | Hourly, mm/hr | Sum of 24 one-hour intervals, mm/day |
| Mean air temperature at 2 m | M2SDNXSLV_5_12_4_T2MMEAN | Daily, °C | Daily mean, °C |

Both regional files cover 2000-01-01 through 2025-12-31: **9,497 days**. The rain source has **227,928 hourly records**. Input order is corrected before aggregation. The effective bounding box must match `[-35.625, -7, -35.625, -7]`; incompatible sources are retained with provenance but excluded from local analysis. No coordinates are rewritten to pretend a source is local.

Daily boundaries are **00:00–24:00 UTC**. Mid-hour timestamps label hourly average intervals; each rate is multiplied by one hour and summed. Taking the mean of the hourly rates would retain mm/hour and would not yield daily accumulated rain. Native kg/m²/s or mm/s inputs are not silently converted: export these CSVs in the expected units.

Missing or duplicate timestamps, fill markers, leap days, unit mismatches, negative precipitation, and source coordinates are checked. A missing hour makes that daily rain total unavailable, not zero. Monthly and annual statistics require complete daily coverage. Temperature may be negative in Celsius and is not rejected merely for that reason.

To replace sources, stop the server and run:

```sh
.venv/bin/python -m climaraiz import-data \
  --precipitation data/sources/YOUR_REGIONAL_HOURLY_RAIN.csv \
  --temperature data/sources/YOUR_DAILY_TEMPERATURE.csv
.venv/bin/python -m climaraiz export-daily --output data/climate_daily.csv
.venv/bin/python -m climaraiz export-bundle
```

The aligned daily CSV is provided in `data/climate_daily.csv`. `export-bundle` writes that CSV and its provenance manifest together; run it after changing the active sources to keep fresh-clone startup reproducible. Prepared bundles intentionally support only complete, aligned daily data; use the raw importer for incomplete sources. Importing the same data is idempotent. Reimporting replaces the active source for that variable atomically and clears the trend cache. Previous completed planting analyses retain their source snapshots and results. Update `data/sources.json` as well when changing input filenames. `CLIMARAIZ_DATA_DIR` can override the data directory.

## Planting windows

The following windows were explicitly supplied by the user as collected from ZARC. They are versioned in `climaraiz/config/crops.json`, used inclusively, and expanded into all 30 dates in each window:

| Crop | Rainfed planting window |
| --- | --- |
| 1 — Milho (corn) | April 21–May 20 |
| 2 — Feijão-preto (black beans, *Phaseolus vulgaris*) | April 21–May 20 |
| 3 — Girassol (sunflower) | April 11–May 10 |

The source is labelled **user supplied, not independently verified**. The application does not invent a publication identifier, soil class, cultivar group, official validity period, or insurance eligibility. Add those verified details before representing these dates as an official eligibility determination.

## Historical planting analysis

For every date in a window, the same month/day is replayed across the requested historical years. A `cycle_days` value is required and is a **user scenario**, not a validated cultivar duration. The last included day is `start + cycle_days - 1`; cycles may cross December. Incomplete cycles are excluded per variable and remain visible in `yearly_exposure` with missing-day counts.

Results include rainfall accumulated over the cycle, the longest run of days with rain **<1 mm/day**, mean temperature, highest/lowest **daily mean** temperature, optional days above a user-selected daily-mean threshold, and mean/median/P10/P90 across historical cycles. The 1 mm dry-day threshold is a descriptive convention, not a water-deficit or crop-risk threshold. P10/P90 are sample distribution quantiles, not confidence intervals or future success probabilities.

Optional phase definitions use inclusive zero-based offsets. They must be ordered, non-overlapping, and cover the cycle exactly. They are explicitly labelled user-defined scenarios. No default germination/flowering dates or agronomic heat/rain thresholds are invented.

**Exploratory climate-exposure levels are available** from historical event frequency. Favorable crop-success frequency and best planting date remain unavailable until agronomic profiles are validated. Raw exposure is fully functional and not disguised as a crop-risk model. There are no daily maximum/minimum temperature sources, yield forecasts, or soil-water balance calculations. Rainfall and temperature summaries are not yield or irrigation recommendations.

## API

All documented routes use `/api/v1`:

| Method | Route | Purpose |
| --- | --- | --- |
| GET | `/municipalities` | Search the configured municipality, with state and limit validation |
| GET | `/crops` | Three crops and versioned user-supplied windows |
| GET | `/data/status` | Source scope, units, hashes, quality, and availability |
| GET | `/climate/series` | Paginated daily, monthly, or annual local observations |
| GET | `/climate/trends` | Complete-year summaries, Theil–Sen, Mann–Kendall, Ljung–Box |
| POST | `/planting/analyses` | Persist and process a historical exposure scenario |
| GET | `/planting/analyses/{id}` | Status/progress or chronological date summaries |
| GET | `/planting/analyses/{id}/dates/{date}` | Detailed cycle and per-year results |
| GET | `/planting/analyses/{id}/dates/{date}/phases` | User-defined phase results or explicit unavailability |

Example:

```sh
curl 'http://127.0.0.1:8000/api/v1/climate/trends?municipality_id=2504009&start_year=2001&end_year=2025'
curl -X POST http://127.0.0.1:8000/api/v1/planting/analyses \
  -H 'Content-Type: application/json' \
  -d '{"municipality_id":2504009,"crop_id":1,"planting_year":2027,"cycle_days":120,"historical_period":{"start_year":2001,"end_year":2025}}'
```

POST returns HTTP 202 with a result URL. Identical requests reuse a fingerprint based on the request, source snapshots, window configuration, and model version. Processing runs in-process after the response; SQLite stores progress, results, and failures. An interrupted job is marked failed at restart and can be resubmitted. Run one worker; a durable external queue is required before scaling to multiple processes. Do not reimport sources while jobs are running.

Validation errors return HTTP 400 with `error.code`, `message`, `details`, and `request_id`. Missing entities return 404, incompatible data or ineligible dates return 422, and unfinished/failed analysis details return 409. Series responses limit pages to 10,000 observations, expose completeness, and serialize absent values as JSON `null`. Municipality IDs other than `2504009` are unsupported.

## Statistical methods

### Configured phase checks (daily-mean MVP)

Each crop exposes versioned `climate_checks` from the crop configuration. Corn uses a strict daily-mean `>33 °C` count in `pollination`; black beans use daily-mean `>30 °C` and `<12 °C` counts in `flowering`. These are explicitly **exploratory daily-mean scenarios**, not validated maximum/minimum temperature criteria. The sunflower temperature check reports the highest **daily mean** in `flowering` and is excluded from the combined assessment. All three crops check runs of **at least five consecutive days below 1 mm/day** in flowering. Whole-cycle gross-rainfall benchmarks are **500 mm for corn, 300 mm for black beans, and 500 mm for sunflower**, with no upper cutoff.

The rainfall targets are scenario benchmarks inspired by the linked agronomic references; they do **not** establish effective rainfall or crop water sufficiency. The five-day convention does not prove crop damage. Every configured rule includes its interpretation and `source_id`; the full source registry is returned by `GET /api/v1/crops` and saved with analyses. The corn daily-mean 33 °C proxy remains an explicitly exploratory scenario without a validated mean-temperature damage threshold.

Provide phase IDs matching each rule. Existing `phases` remain a non-overlapping partition of the cycle. Optional `check_windows` extend those fields with an optional `phase_id` and may overlap, allowing `pollination` within `flowering`. IDs must be unique across both lists; all inclusive zero-based offsets must fall inside the cycle. The reserved `cycle` window is automatically resolved to days `0..cycle_days-1`; if explicitly supplied, it must cover the complete cycle. No flowering or pollination dates are assumed when absent.

```json
{
  "crop_id": 1,
  "municipality_id": 2504009,
  "planting_year": 2027,
  "cycle_days": 120,
  "historical_period": {"start_year": 2001, "end_year": 2025},
  "check_windows": [
    {"id": "flowering", "name": "Illustrative flowering window", "start_day": 40, "end_day": 65},
    {"id": "pollination", "name": "Illustrative pollination window", "start_day": 45, "end_day": 55}
  ]
}
```

**The offsets above are syntax examples, not agronomic recommendations.** They must be replaced by the user's chosen scenario or reviewed cultivar parameters. Undefined windows return `PHASE_WINDOW_NOT_DEFINED`, a null summary and null frequency, never a fabricated zero. Incomplete phase-years are excluded independently for each check and listed explicitly.

For thermal counts, a historical event means **at least one daily mean strictly beyond the configured threshold** during the phase. Frequency is `100 × event_years / complete_phase_years`; annual results, units, full rule definitions and scenario windows are preserved. A year with ten qualifying days still counts once in the event-year numerator. Exactly 33 °C does not meet `>33`; exactly 12 °C does not meet `<12`.

Dry sequences and phase totals remain descriptive with a null event frequency when `min_consecutive_days`, `min_mm` and `max_mm` are null. A zero thermal count means no daily mean crossed the threshold, **not that no daily extreme occurred**. These checks are shown in each date's detail view and returned by the API. Overall crop-risk percentage, favorable frequency, and best-date ranking remain unavailable. Model and crop-configuration versions were incremented so old cached analyses are not reused as if they included these new calculations.

### Combined historical scenario assessment

Every planting date now includes **`scenario_assessment`**, returned both in the calendar and in the date detail. It is also visible in the planting-date table and selected-date panel. For each historical year, the evaluator combines all rules with `include_in_assessment: true`: a year meets the scenario only if **none of those checks reports its configured event**. It never sums event percentages, averages them, or counts the same year twice.

The denominator is the intersection of complete years for every included check. Missing required windows, unavailable sources, or included descriptive rules without an event definition block the combined percentage; they are not silently dropped. Missing observations exclude the affected year from the combined denominator, with reasons in `excluded_years`. If no common complete years remain, the percentage is null. A check with `include_in_assessment: false` does not affect the score. This matters for sunflower: its mean-temperature peak is descriptive, so the combined criterion checks are rainfall and dry-spell occurrence only.

```json
{
  "scenario_assessment": {
    "status": "available",
    "reason": null,
    "method": "all_included_checks_without_events",
    "evaluated_years": 25,
    "years_meeting_criteria": 10,
    "years_not_meeting_criteria": 15,
    "scenario_criteria_met_pct": 40,
    "excluded_years": [],
    "validation_status": "exploratory",
    "interpretation": "historical_scenario_criteria_match_not_crop_success_probability"
  }
}
```

The example above reproduces **April 25, 120 days, 2001–2025**, with the illustrative flowering window at days 40–65 and pollination at days 45–55. Ten years meet all three corn criteria; fifteen do not. Individual event frequencies are 60% below the cycle rainfall benchmark, 24% with the configured flowering dry spell, and 0% with the daily-mean heat event. The combined percentage is **40%**, not an average of the individual percentages. These windows are not validated cultivar phenology, and zero heat events do not rule out hot daily maxima.

The date-detail response includes `yearly_assessment` with each year's pass/fail status and failed checks. The calendar omits that detailed list to keep the response smaller while returning the identical percentage, numerator, denominator, configuration, and exclusions. Unavailable risk classifications return `risk_level: "not_supported"`. `favorable_frequency_pct`, `risk_percentage`, and `best_historical_date` remain null. The API now supplies exploratory low/moderate/high exposure bands, not crop-success probabilities. Comparisons across crops are not an agricultural risk ranking because their criteria differ.

The `/planting/analyses/{id}/dates/{date}/phases` route also includes `scenario_assessment` and `climate_checks` for each submitted phase, using checks explicitly linked through `check_windows[].phase_id`, or legacy exact-ID matches when no link is present. Phase cards can show `scenario_criteria_met_pct` with its numerator and denominator. No configured checks means an unavailable percentage, not low risk. Each phase returns its own `risk_level` and `risk_level_reason`; unavailable assessment returns `not_supported`, with the technical scenario reason. Existing analyses use their saved rule results and policy, without applying new configuration retroactively.

### Exploratory exposure classification

`exposure_frequency_pct = 100 × years_not_meeting_criteria / evaluated_years`.
The versioned `historical-exposure-v1` policy classifies unrounded frequency as
`low` up to and including 20%, `moderate` above 20% through 40%, and `high`
above 40%. `not_supported` means the assessment is unavailable, not zero risk.
These are ClimaRaiz MVP presentation bands inspired by ZARC frequency landmarks;
they are not official ZARC classes or locally validated crop-damage probabilities.
There is no new minimum historical sample-size filter; always show the evaluated
and excluded year counts. No confidence intervals or soil-water balance are added
by this classification.

`risk_level` is exposed on each date, its `historical_assessment`, and
`scenario_assessment`; the phase route exposes the corresponding per-phase
values at the phase root, `assessment`, and `scenario_assessment`. The scenario
object includes `years_with_events`, `risk_basis`, `classification_version` and
`classification_thresholds`. Both new and saved results receive the current,
explicitly versioned display classification from their historical event counts;
old observations and crop-check definitions are not modified.

For the reference corn example, whole-cycle exposure is 15/25 = 60% (`high`),
whereas a submitted flowering phase has 6/25 = 24% (`moderate`). Phase percentages
are never averaged into the cycle result. Severity summaries and check-specific
annual details remain in `climate_checks`; this release does not add a new
severity-weighted index or claim that events occurred on the same day.

For the front end, use **“Historical years meeting this scenario's criteria”** rather than “probability of success.” See [scenario assessment contract](docs/scenario_assessment.md) and [actual complete API examples](docs/api_examples.json).

Annual rain is the sum of complete daily totals. Annual temperature is the mean of all days, equivalent to a monthly mean weighted by days. Trend estimation uses the median pairwise slope (**Theil–Sen**) with a 95% slope interval, converted per decade. The original **Mann–Kendall** test includes its package's tie and continuity handling. Approximate **Ljung–Box** diagnostics inspect detrended annual residuals up to lags 1–3 with `model_df=0`. At least eight complete years are required for a trend. If residual dependence is detected, the original p-value is flagged as requiring adjustment; non-detection does not prove independence. No causal attribution or future extrapolation is implied.

For 2001–2025, the hourly-derived regional rain reproduces the earlier monthly reference: mean **956.3536 mm/year**, slope approximately **101.2366 mm/year per decade**, Mann–Kendall p approximately **0.0335614**. Temperature results depend on the selected period; the dashboard always displays its active interval.

## Tests

```sh
.venv/bin/python -m pytest -q
```

Tests use isolated temporary databases. They verify hourly integration versus rate averaging, missing hours, leap-day coverage, wrong units, duplicate timestamps, spatial mismatches, complete-year requirements, numerical reference trends, window boundaries, idempotent analysis creation, phase reconciliation, cross-year cycles, HTTP validation, OpenAPI, and static delivery. Scenario tests additionally verify joint conditions rather than percentage averaging, a common complete-year denominator, explicit exclusions, missing-window blocking, optional descriptive checks, strict thermal boundaries, and the 40% reference corn scenario. Integration tests use the regional raw CSVs when available or the versioned prepared bundle otherwise. Fresh-checkout tests verify startup without any raw CSV or existing database, hash mismatch detection, calendar gaps and rechecking of source scope.

The running-server smoke test checks all three crops, the 30-date calendars, combined percentages, common-year counts and detailed phases:

```sh
.venv/bin/python tests/smoke_server.py
```

Use `--base-url http://127.0.0.1:18765` to check an isolated server on another
port without connecting to the development server on port 8000.

## Layout

```text
backend/
  climaraiz/
    main.py           # API factory, lifecycle, error contracts, interface delivery
    ingestion.py      # Giovanni metadata, hourly/day completeness and source scope
    bundle.py         # Verified prepared daily bundle for fresh-clone startup
    climate.py        # Aggregation, annual statistics, trend cache
    planting.py       # Window expansion, scenarios, persistence and exposure
    scenario.py       # Joint criteria matching with common complete historical years
    storage.py        # Versioned SQLite schema and connection management
    models.py         # Strict request schemas
    config/crops.json # User-supplied planting windows
    static/           # Offline HTML/CSS/JavaScript dashboard
  data/               # Local source copies, SQLite database, aligned daily CSV
  tests/              # Isolated unit and HTTP integration tests
  pyproject.toml
```

## References

- NASA Giovanni CSV metadata and SHA-256 hashes are exposed in `/api/v1/data/status`.
- [NASA M2T1NXFLX](https://disc.gsfc.nasa.gov/datasets/M2T1NXFLX_5.12.4/summary)
- [NASA M2SDNXSLV](https://disc.gsfc.nasa.gov/datasets/M2SDNXSLV_5.12.4/summary)
- [SciPy Theil–Sen](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.theilslopes.html)
- [pyMannKendall](https://joss.theoj.org/papers/10.21105/joss.01556)
- [statsmodels Ljung–Box](https://www.statsmodels.org/stable/generated/statsmodels.stats.diagnostic.acorr_ljungbox.html)
- [FastAPI background tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/)

### Real-data classification examples

[Real-data validation](docs/real_data_validation.md) lists reproducible low,
moderate and high cases using unchanged regional daily observations and rules.
`tests/test_real_exposure.py` includes direct numerical reference tests and API
consistency checks for all three classes. All phase timings are illustrative
scenarios, not cultivar recommendations.


### Explicit links between check windows and phase cards (API 0.4.0)

Keep segment IDs such as `floracao` in `phases`. Use criterion IDs such as
`flowering` and `pollination` in `check_windows`, adding `phase_id: "floracao"`
to associate their results with that card. The linked window must be fully
inside the referenced segment. Invalid references or intervals return HTTP 400
(`INVALID_REQUEST`). Missing phase_id retains legacy exact-ID behavior; no
association is inferred by name or overlap. The overall calculation is unchanged.

See the [complete binding example and migration guide](docs/phase_window_bindings.md).
Create a new analysis with the linked request and use its returned ID: old
analyses retain their saved associations. Linking does not add missing crop
criteria, so unrelated phase cards can still return `not_supported`.


### Minimum criteria for every phase (API 0.5.0)

All three crops now support germination and filling dry spells (at least five
consecutive days below 1 mm/day) and pre-harvest wetness (at least six rainy days
>=1 mm in the final ten cycle days). These are exploratory meteorological
proxies, not validated crop-loss thresholds. Germination/filling windows must
span at least five days; the maturation check must use exactly the final ten
days. A longer maturation segment can link to that narrower check window.

Use the [complete JSON request](docs/requests/all_phase_analysis.json) to supply
and link all four phase cards. Change crop_id to 2 or 3 for beans or sunflower;
review timing for the desired cultivar rather than treating these offsets as
recommendations. From the backend directory:

```sh
curl -X POST http://127.0.0.1:8000/api/v1/planting/analyses \
  -H 'Content-Type: application/json' \
  --data-binary @docs/requests/all_phase_analysis.json
```

For April 25, the example gives 16% low germination exposure, 24% moderate
flowering exposure, 56% high filling exposure and 36% moderate pre-harvest
exposure. Corn's overall exposure becomes 88%; its criteria match is 12%.

For backward compatibility, the new windows are optional when absent, with
omissions listed in `scenario_assessment.omitted_optional_checks`. Once supplied,
the checks participate in the phase and overall score: invalid windows or
unavailable sources are not silently omitted. Supplying all windows produces a
full minimum-profile evaluation. Old saved analyses keep their old criteria.
Restart the server and POST a new request to use the new profile.
See [criteria, sources and limitations](docs/minimum_phase_criteria.md).
