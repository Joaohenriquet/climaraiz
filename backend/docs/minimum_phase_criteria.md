# Minimum phase criteria: active exploratory profile

Status: activated for all three crops in API 0.5.0 and model
`historical-exposure-v6-minimum-phase-criteria`. Saved analyses retain their
original check definitions and results.

## Scope and available inputs

ClimaRaiz currently has regional MERRA-2 daily accumulated rainfall and daily
mean air temperature at 2 m. It does not have measured seedbed moisture, soil
temperature, grain moisture, daily air temperature extremes or a crop water
balance. These outputs therefore describe meteorological exposure in
user-selected windows, not probability of germination, crop loss or disease.

## Minimum operational criteria

| Window ID | Minimum event | Evidence and interpretation |
| --- | --- | --- |
| `germination` | At least 5 consecutive days with daily rain <1 mm inside the supplied window | Generic dry-spell proxy; not a species-specific germination-failure threshold. |
| `grain_filling` | At least 5 consecutive days with daily rain <1 mm inside the supplied window | Proxy for a dry interval during a water-sensitive period, not proof of soil water deficit. |
| `maturation` | At least 6 days with daily rain >=1 mm in the last 10 days of the selected cycle | Late-cycle/pre-harvest wetness exposure, not risk throughout physiological maturation. |

The first two events use the same meteorological convention, not an assertion
that all crops or stages share the same sensitivity. Their durations are
user-selected windows; no default phase dates are inferred. A window shorter
than five days cannot support the full five-day dry-spell criterion and is
reported unavailable (`WINDOW_TOO_SHORT`).

The wet days need not be consecutive. The 10-day period must finish at inclusive
offset `cycle_days - 1` and fit entirely inside the linked late-cycle segment.
It is a user-selected pre-harvest scenario; the app cannot establish the true
physiological or harvest maturity from climate alone. Exactly 1 mm counts as a
wet day and breaks a <1 mm dry spell. Exactly 5 dry days or 6 wet days triggers
the respective event. All required observations must be present for each year.

## Crop-specific evidence

### Corn

Embrapa describes the importance of water availability during grain filling.
Soil moisture and temperature affect grain formation; rainfall alone does not
establish effective water supply.

A MAPA corn second-crop zoning document for Maranhão describes persistent rain
as 6 or more rainy days in the final ten-day period, associated with difficulty
in drying grain for harvest. This is a useful reference for the structure of a
minimum wetness indicator. It is not a local Campina Grande zoning validation.
The >=1 mm wet-day threshold in this proposal is an explicit ClimaRaiz
operational convention, not a threshold attributed to that document.

### Black beans (Phaseolus vulgaris)

Embrapa describes the grain-filling stage and the importance of harvesting at
appropriate maturity; rain after maturity can cause field losses. These sources
support assessing dry exposure during filling and wet exposure near harvest.
They do not establish the proposed 5-day or 6-of-10 thresholds as validated
black-bean damage limits. Those values would be an exploratory MVP convention.

### Sunflower

Embrapa reports that lack of water during achene filling affects filling and
weight. It also describes dry weather as desirable during harvest maturation,
with prolonged adverse conditions increasing operational and quality problems.
The proposed numerical dry/wet events are exploratory adaptations for this crop;
they are not validated sunflower loss thresholds. Temperature limits for oil
formation must not be transferred directly to daily-mean air data without
reviewing the source's variable and temporal definition.

## Implemented behavior and limits

- All three crop profiles now include germination and grain-filling dry-spell
  checks plus a `rainy_days` maturation check. Rules expose their meteorological
  source and agronomic rationale references through the crop source registry.
- The new three rules set `optional_when_window_missing: true`. Absent windows
  are explicitly listed in `scenario_assessment.omitted_optional_checks` and
  do not block the legacy overall score. Supplying a window activates its rule
  in both the linked phase and overall calculation. This is not a claim that
  an older partial request assessed every stage.
- Once a window is supplied, source absence, insufficient duration or misplaced
  pre-harvest timing blocks the included assessment rather than silently dropping
  its rule. Missing observations exclude the affected year from the common
  complete-year denominator. If no complete years remain, classification is
  `not_supported`, not low exposure.
- `WINDOW_DURATION_MISMATCH` identifies a maturation window not exactly ten days;
  `WINDOW_NOT_AT_CYCLE_END` identifies a ten-day window not at the cycle end.
  These are check-availability reasons returned in result JSON, not new request
  HTTP errors. Existing phase binding validations still return HTTP 400.
- Check windows link to segment cards using `phase_id`; IDs remain distinct.
  No phase dates or translations are inferred.
- The [complete request](requests/all_phase_analysis.json) supplies all windows
  for a 120-day illustrative scenario. With 2001–2025 data and April 25 planting,
  all three crops have germination 4/25 event years (16%, low), flowering 6/25
  (24%, moderate), filling 14/25 (56%, high), and pre-harvest wetness 9/25
  (36%, moderate). These match because the rain proxies are shared and no
  configured daily-mean thermal event occurs in this example, not because the
  crops are agronomically identical.
- Corn's complete-request overall exposure is 22/25 = 88% (high), with 12%
  criteria match. The legacy flowering/pollination-only example remains 60%
  exposure and 40% criteria match. Adding criteria changes what is evaluated;
  these are not interchangeable probabilities.
- Classification bands remain low <=20%, moderate >20% through 40%, high >40%,
  and not_supported when unavailable. No arbitrary minimum rainfall per phase,
  soil-water diagnosis or daily-maximum temperature thresholds were added.
- Tests cover exact thresholds, nonconsecutive wet days, missing days,
  unsuitable windows, cross-year periods, explicit bindings, optional-window
  omissions, independent real-data yearly references and API consistency for
  all four phase cards in all three crops.

Do not derive a fixed minimum rainfall per phase by dividing the cycle's
500/300/500 mm benchmarks by its duration. Do not diagnose waterlogging or
fungal disease from rainfall alone. Do not label dry weather after physiological
maturity as the same adverse event used during grain filling.

## Sources reviewed

- [Funceme: dry-spell definitions](https://www.funceme.br/?p=843): cites the
  five-consecutive-day, below-1-mm convention and notes alternative definitions.
- [Embrapa: corn physiology](https://www.alice.cnptia.embrapa.br/bitstream/doc/478760/1/Fisiologiamilho.pdf):
  physiological basis for moisture-sensitive grain filling.
- [MAPA: corn second-crop methodology, Maranhão](https://www.gov.br/agricultura/pt-br/assuntos/riscos-seguro/programa-nacional-de-zoneamento-agricola-de-risco-climatico/portarias/safra-vigente/maranhao/PORTN34.PDF/%40%40download/file):
  rainy-day frequency in the final ten-day period. The URL label and publication
  references are retained as retrieved; applicability here is methodological,
  not a claim of current local planting eligibility.
- [Embrapa: bean phenology](https://www.embrapa.br/web/agencia-de-informacao-tecnologica/cultivos/feijao/pre-producao/fenologia):
  grain-filling and maturation stages.
- [Embrapa: bean harvest, drying and storage](https://www.infoteca.cnptia.embrapa.br/infoteca/bitstream/doc/254606/1/CPAOCIR.TEC.1790.pdf):
  rain after maturity and field losses.
- [Embrapa: sunflower development](https://www.infoteca.cnptia.embrapa.br/bitstream/doc/445797/1/doc059.pdf):
  achene filling and harvest maturation, including dry-weather requirements.
