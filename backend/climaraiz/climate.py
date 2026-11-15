"""Daily queries, complete-period aggregation, and reproducible annual statistics."""
import hashlib
import json

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.diagnostic import acorr_ljungbox
import pymannkendall as mk

from .errors import DomainError
from .settings import MODEL_VERSION


def json_safe(value):
    """Convert scientific scalar types and nonfinite results into strict JSON values."""
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(v) for v in value]
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, float) and not np.isfinite(value):
        return None
    return value


class ClimateService:
    def __init__(self, database):
        self.database = database

    def availability(self, variable):
        source = self.database.source(variable)
        if source is None:
            return {"status": "unavailable", "reason": "SOURCE_NOT_IMPORTED", "source": None}
        info = source["metadata"]
        return {"status": "available" if info["usable_for_municipality"] else "unavailable",
                "reason": None if info["usable_for_municipality"] else "SOURCE_AREA_MISMATCH",
                "source": info}

    def daily(self, variable, require_local=True):
        state = self.availability(variable)
        if state["source"] is None:
            raise DomainError("SOURCE_NOT_IMPORTED", "This variable has not been imported.")
        if require_local and state["status"] != "available":
            raise DomainError("SOURCE_AREA_MISMATCH", "This source does not match the configured municipality grid cell.",
                              details={"variable": variable, "source": state["source"]})
        with self.database.connect() as db:
            rows = db.execute("SELECT date,value,valid_count,expected_count,quality_status FROM climate_daily WHERE source_id=? ORDER BY date", (variable,)).fetchall()
        frame = pd.DataFrame([dict(row) for row in rows])
        if frame.empty:
            raise DomainError("CLIMATE_DATA_INSUFFICIENT", "The source contains no daily data.")
        frame["date"] = pd.to_datetime(frame.date)
        return frame.set_index("date"), state["source"]

    def aggregate(self, variable, aggregation, start_year, end_year, require_local=True):
        if start_year > end_year:
            raise DomainError("INVALID_REQUEST", "start_year must not exceed end_year.", 400)
        frame, source = self.daily(variable, require_local)
        dates = pd.date_range(f"{start_year}-01-01", f"{end_year}-12-31", freq="D")
        values = frame.value.reindex(dates)
        if aggregation == "daily":
            result = pd.DataFrame({"value": values, "valid_days": values.notna().astype(int), "expected_days": 1})
        else:
            frequency = "MS" if aggregation == "monthly" else "YS"
            grouped = values.resample(frequency)
            counts = grouped.count()
            sums = grouped.sum(min_count=1)
            data = sums if variable == "precipitation" else grouped.mean()
            expected = pd.Series(1, index=dates).resample(frequency).sum()
            result = pd.DataFrame({"value": data.where(counts.eq(expected)), "valid_days": counts, "expected_days": expected})
        result["quality_status"] = np.where(result.valid_days.eq(result.expected_days), "valid", "incomplete")
        result.index.name = "date"
        return result, source

    def trends(self, start_year, end_year):
        if end_year < start_year:
            raise DomainError("INVALID_REQUEST", "start_year must not exceed end_year.", 400)
        versions = {v: self.availability(v) for v in ("precipitation", "temperature_mean")}
        key = hashlib.sha256(json.dumps([MODEL_VERSION, start_year, end_year, versions], sort_keys=True).encode()).hexdigest()
        with self.database.connect() as db:
            row = db.execute("SELECT result_json FROM trend_cache WHERE cache_key=?", (key,)).fetchone()
        if row:
            return json.loads(row["result_json"])
        indicators = {}
        for variable, state in versions.items():
            if state["status"] != "available":
                indicators[variable] = state
                continue
            frame, source = self.aggregate(variable, "annual", start_year, end_year)
            complete = frame.loc[frame.quality_status.eq("valid"), "value"]
            if len(complete) < 8:
                indicators[variable] = {"status": "unavailable", "reason": "AT_LEAST_8_COMPLETE_YEARS_REQUIRED", "complete_years": len(complete)}
                continue
            x = complete.index.year.to_numpy(float)
            y = complete.to_numpy(float)
            sen = stats.theilslopes(y, x, alpha=.95)
            test = mk.original_test(y)
            residuals = y - (sen.intercept + sen.slope*x)
            lag_results = []
            if np.std(residuals) > 1e-12:
                lb = acorr_ljungbox(residuals, lags=[1, 2, 3], model_df=0, return_df=True)
                lag_results = [{"lag_years": int(lag), "p_value": float(r.lb_pvalue)} for lag, r in lb.iterrows()]
            detected = any(r["p_value"] < .05 for r in lag_results)
            indicators[variable] = {
                "status": "available", "source": source, "complete_years": len(complete),
                "excluded_years": [int(d.year) for d in frame.index[frame.quality_status.ne("valid")]],
                "mean": float(y.mean()), "minimum": float(y.min()), "maximum": float(y.max()),
                "standard_deviation": float(y.std(ddof=1)),
                "minimum_year": int(x[y.argmin()]), "maximum_year": int(x[y.argmax()]),
                "unit": "mm/year" if variable == "precipitation" else "degC",
                "trend": {"method": "theil_sen", "slope_per_decade": sen.slope*10,
                          "confidence_interval_95": {"lower": sen.low_slope*10, "upper": sen.high_slope*10},
                          "unit": "mm/year per decade" if variable == "precipitation" else "degC/decade"},
                "significance": {"method": "mann_kendall_original", "p_value": test.p, "tau": test.Tau,
                                 "interpretation": "requires_autocorrelation_adjustment" if detected else "original_test_under_independence_assumption"},
                "autocorrelation": {"method": "ljung_box_on_sen_residuals", "approximate": True,
                                    "model_df": 0, "detected": detected, "lags": lag_results},
                "annual_series": [{"year": int(year), "value": float(value),
                                   "fitted": float(sen.intercept + sen.slope*year)} for year, value in zip(x, y)]}
        result = json_safe({"period": {"start_year": start_year, "end_year": end_year}, "indicators": indicators,
                            "model_version": MODEL_VERSION,
                            "limitations": ["No attribution or forecast is implied.", "Confidence intervals exclude source and spatial representativeness errors."]})
        with self.database.connect() as db:
            db.execute("INSERT OR REPLACE INTO trend_cache VALUES(?,?)", (key, json.dumps(result, allow_nan=False)))
        return result
