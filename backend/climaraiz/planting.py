"""Historical exposure, user-supplied planting windows, and durable analysis records."""
from datetime import date, datetime, timedelta, timezone
import hashlib
import json
import logging
import sqlite3

import numpy as np
import pandas as pd

from .climate import json_safe
from .checks import evaluate_check
from .models import ScenarioPhase
from .scenario import assess_scenario, classify_exposure
from .errors import DomainError
from .settings import MODEL_VERSION, MUNICIPALITY, PACKAGE_DIR

logger = logging.getLogger(__name__)


def now():
    return datetime.now(timezone.utc).isoformat()


def longest_run(flags):
    longest = current = 0
    for flag in flags:
        current = current + 1 if flag else 0
        longest = max(longest, current)
    return longest


def summary(values):
    if not values:
        return None
    return {"mean": float(np.mean(values)), "median": float(np.median(values)),
            "p10": float(np.quantile(values, .1)), "p90": float(np.quantile(values, .9)),
            "sample_count": len(values)}


class PlantingService:
    def __init__(self, database, climate):
        self.database, self.climate = database, climate
        self.windows = json.loads((PACKAGE_DIR / "config" / "crops.json").read_text())

    def crops(self):
        return [{**crop, "enabled": True, "agronomic_profile_status": "not_validated",
                 "planting_window": {"start_month_day": crop["window_start"], "end_month_day": crop["window_end"],
                                     "source_version": self.windows["version"],
                                     "verification_status": self.windows["verification_status"]}}
                for crop in self.windows["crops"]]

    def crop(self, crop_id):
        result = next((crop for crop in self.crops() if crop["id"] == crop_id), None)
        if result is None:
            raise DomainError("CROP_NOT_FOUND", "The crop was not found.", 404)
        return result

    def dates(self, crop_id, year):
        crop = self.crop(crop_id)
        start = date.fromisoformat(f"{year}-{crop['window_start']}")
        end = date.fromisoformat(f"{year}-{crop['window_end']}")
        return [start + timedelta(days=i) for i in range((end-start).days+1)]

    def create(self, request):
        if request.municipality_id != MUNICIPALITY["id"]:
            raise DomainError("MUNICIPALITY_NOT_FOUND", "The municipality was not found.", 404)
        temp, _ = self.climate.daily("temperature_mean")
        period = request.historical_period
        required = pd.date_range(f"{period.start_year}-01-01", f"{period.end_year}-12-31", freq="D")
        if temp.value.reindex(required).isna().any():
            raise DomainError("CLIMATE_DATA_INSUFFICIENT", "Complete local daily temperature is required for every requested historical year.")
        self.crop(request.crop_id)
        sources = {v: self.climate.availability(v) for v in ("temperature_mean", "precipitation")}
        payload = request.model_dump(mode="json")
        fingerprint = hashlib.sha256(json.dumps([payload, sources, self.windows, MODEL_VERSION], sort_keys=True).encode()).hexdigest()
        analysis_id = "ana_" + fingerprint[:24]
        with self.database.connect() as db:
            existing = db.execute("SELECT id,status FROM analyses WHERE fingerprint=?", (fingerprint,)).fetchone()
            if existing and existing["status"] != "failed":
                return existing["id"], False
            if existing:
                db.execute("DELETE FROM analyses WHERE fingerprint=?", (fingerprint,))
            created_at = now()
            try:
                db.execute("INSERT INTO analyses(id,fingerprint,status,request_json,created_at,updated_at) VALUES(?,?,?,?,?,?)",
                           (analysis_id, fingerprint, "processing", json.dumps(payload), created_at, created_at))
            except sqlite3.IntegrityError:
                return analysis_id, False
        return analysis_id, True

    def _interval(self, frames, start, end, threshold):
        index = pd.date_range(start, end, freq="D")
        record = {"historical_start": str(start), "historical_end": str(end), "days": len(index)}
        for variable, frame in frames.items():
            if frame is None:
                record[variable] = {"status": "unavailable", "reason": "SOURCE_AREA_MISMATCH_OR_NOT_IMPORTED"}
                continue
            values = frame.value.reindex(index)
            if values.isna().any():
                record[variable] = {"status": "incomplete", "missing_days": int(values.isna().sum())}
            elif variable == "temperature_mean":
                record[variable] = {"status": "available", "mean_c": float(values.mean()),
                                    "highest_daily_mean_c": float(values.max()), "lowest_daily_mean_c": float(values.min()),
                                    "days_daily_mean_at_or_above_threshold": int((values >= threshold).sum()) if threshold is not None else None}
            else:
                record[variable] = {"status": "available", "total_mm": float(values.sum()),
                                    "rain_days_ge_1mm": int((values >= 1).sum()),
                                    "longest_dry_spell_days_lt_1mm": longest_run(values < 1)}
        return record

    def _consolidate(self, records, threshold):
        temp = [r["temperature_mean"] for r in records if r["temperature_mean"]["status"] == "available"]
        rain = [r["precipitation"] for r in records if r["precipitation"]["status"] == "available"]
        return {"temperature_mean": {"status": "available" if temp else "unavailable",
                 "evaluated_years": len(temp), "mean_c": summary([r["mean_c"] for r in temp]),
                 "highest_daily_mean_c": summary([r["highest_daily_mean_c"] for r in temp]),
                 "days_at_or_above_threshold": summary([r["days_daily_mean_at_or_above_threshold"] for r in temp]) if threshold is not None else None},
                "precipitation": {"status": "available" if rain else "unavailable", "evaluated_years": len(rain),
                 "total_mm": summary([r["total_mm"] for r in rain]),
                 "longest_dry_spell_days": summary([r["longest_dry_spell_days_lt_1mm"] for r in rain])},
                "risk_level": "not_supported", "favorable_frequency_pct": None,
                "risk_status": "unavailable_without_validated_agronomic_profile"}

    def process(self, analysis_id, request):
        try:
            temp, _ = self.climate.daily("temperature_mean")
            rain_state = self.climate.availability("precipitation")
            rain = self.climate.daily("precipitation")[0] if rain_state["status"] == "available" else None
            frames = {"temperature_mean": temp, "precipitation": rain}
            sources = {v: self.climate.availability(v) for v in frames}
            candidate_dates = self.dates(request.crop_id, request.planting_year)
            crop_checks = self.crop(request.crop_id).get("climate_checks", [])
            check_windows = {p.id: p for p in [*request.phases, *request.check_windows]}
            check_windows["cycle"] = ScenarioPhase(id="cycle", name="Complete user-selected cycle",
                                                     start_day=0, end_day=request.cycle_days-1)
            results = []
            for number, planting_date in enumerate(candidate_dates):
                annual_records, phase_records = [], {p.id: [] for p in request.phases}
                for year in range(request.historical_period.start_year, request.historical_period.end_year+1):
                    start = date(year, planting_date.month, planting_date.day)
                    end = start + timedelta(days=request.cycle_days-1)
                    annual_records.append({"year": year, **self._interval(frames, start, end, request.daily_mean_threshold_c)})
                    for phase in request.phases:
                        phase_records[phase.id].append({"year": year, **self._interval(frames,
                            start + timedelta(days=phase.start_day), start + timedelta(days=phase.end_day), request.daily_mean_threshold_c)})
                assessment = self._consolidate(annual_records, request.daily_mean_threshold_c)
                if assessment["temperature_mean"]["evaluated_years"] == 0:
                    raise DomainError("CLIMATE_DATA_INSUFFICIENT", "No complete historical cycles were available.")
                phases = [{**p.model_dump(), "profile_status": "user_defined_scenario_not_validated",
                           "assessment": self._consolidate(phase_records[p.id], request.daily_mean_threshold_c),
                           "yearly_exposure": phase_records[p.id]} for p in request.phases]
                checks = [evaluate_check(rule, check_windows, frames, planting_date,
                    request.historical_period.start_year, request.historical_period.end_year) for rule in crop_checks]
                scenario = assess_scenario(checks, request.historical_period.start_year,
                                           request.historical_period.end_year, self.windows.get("assessment", {}))
                results.append({"date": planting_date.isoformat(),
                    "cycle": {"duration_days": request.cycle_days, "start_day": 0,
                              "last_day": request.cycle_days-1, "estimated_last_cycle_date": (planting_date + timedelta(days=request.cycle_days-1)).isoformat(),
                              "profile_status": "user_selected_scenario"},
                    "historical_assessment": assessment, "yearly_exposure": annual_records,
                    "climate_checks": checks, "scenario_assessment": scenario,
                    "phases_status": "available_as_user_scenario" if phases else "unavailable_without_phase_definitions", "phases": phases})
                with self.database.connect() as db:
                    db.execute("UPDATE analyses SET progress=?,updated_at=? WHERE id=?", ((number+1)/len(candidate_dates), now(), analysis_id))
            result = {"analysis_id": analysis_id, "status": "completed", "assessment_status": "climate_exposure_only",
                      "municipality_id": request.municipality_id, "crop_id": request.crop_id,
                      "planting_year": request.planting_year, "historical_period": request.historical_period.model_dump(),
                      "window": {"start_date": str(candidate_dates[0]), "end_date": str(candidate_dates[-1]),
                                 "source": self.windows["source"], "version": self.windows["version"],
                                 "verification_status": self.windows["verification_status"]},
                      "sources": sources, "model_version": MODEL_VERSION, "dates": results,
                      "best_historical_date": None, "ranking_status": "unavailable_without_validated_agronomic_profile",
                      "daily_mean_threshold_c": request.daily_mean_threshold_c,
                      "configured_climate_checks": crop_checks,
                      "assessment_configuration": self.windows.get("assessment", {}),
                      "check_sources": self.windows.get("sources", {}),
                      "resolved_check_windows": [p.model_dump() for p in check_windows.values()],
                      "check_windows": [p.model_dump() for p in request.check_windows],
                      "limitations": ["Historical exposure is not a forecast or an agricultural risk classification.",
                                      "Crop duration and optional phases are user-defined scenarios.",
                                      "Only spatially compatible sources contribute to local exposure.",
                                      "Dates have equal status; no unvalidated best planting date is selected.",
                                      "Incomplete cycles are excluded per variable and their missing days remain visible.",
                                      "Daily intervals use UTC, not local civil-day boundaries."]}
            result["limitations"].append("Configured thermal checks use daily means and exploratory thresholds, not daily maxima/minima or validated crop damage.")
            result["limitations"].append("The scenario percentage measures simultaneous historical criteria matching, not crop success, crop loss, official ZARC risk, or a forecast.")
            with self.database.connect() as db:
                db.execute("UPDATE analyses SET status='completed',result_json=?,progress=1,updated_at=? WHERE id=?",
                           (json.dumps(json_safe(result), allow_nan=False), now(), analysis_id))
        except Exception as error:
            logger.exception("Analysis failed", extra={"analysis_id": analysis_id})
            detail = {"code": error.code if isinstance(error, DomainError) else "PROCESSING_FAILED",
                      "message": error.message if isinstance(error, DomainError) else "The analysis failed. Check server logs."}
            with self.database.connect() as db:
                db.execute("UPDATE analyses SET status='failed',error_json=?,updated_at=? WHERE id=?", (json.dumps(detail), now(), analysis_id))

    def retrieve(self, analysis_id, include_details=False):
        row = self.database.analysis(analysis_id)
        if row is None:
            raise DomainError("ANALYSIS_NOT_FOUND", "The analysis was not found.", 404)
        if row["status"] != "completed":
            return {"analysis_id": analysis_id, "status": row["status"], "progress": row["progress"],
                    "error": json.loads(row["error_json"]) if row["error_json"] else None}
        result = json.loads(row["result_json"])
        # Derive phase summaries from the saved checks and policy, including for
        # existing analyses. Never apply today's configuration to an old result.
        period = result["historical_period"]
        for item in result["dates"]:
            overall = classify_exposure(item.get("scenario_assessment", {"status": "unavailable"}))
            item["scenario_assessment"] = overall
            item["risk_level"] = overall["risk_level"]
            item["historical_assessment"].update(
                risk_level=overall["risk_level"], risk_basis=overall["risk_basis"],
                exposure_frequency_pct=overall["exposure_frequency_pct"],
                risk_status="exploratory_exposure" if overall["risk_level"] != "not_supported" else "not_supported")
            for phase in item.get("phases", []):
                phase_checks = [check for check in item.get("climate_checks", [])
                                if check["phase"] == phase["id"]]
                policy = result.get("assessment_configuration", {})
                phase_scenario = assess_scenario(phase_checks, period["start_year"], period["end_year"], policy)
                phase["assessment"].update(
                    risk_level=phase_scenario["risk_level"], risk_basis=phase_scenario["risk_basis"],
                    exposure_frequency_pct=phase_scenario["exposure_frequency_pct"],
                    risk_status="exploratory_exposure" if phase_scenario["risk_level"] != "not_supported" else "not_supported")
                phase.update(climate_checks=phase_checks, scenario_assessment=phase_scenario,
                             risk_level=phase_scenario["risk_level"],
                             risk_level_reason=phase_scenario["reason"])
        if not include_details:
            result["dates"] = [{k: v for k, v in item.items() if k not in ("yearly_exposure", "phases")} for item in result["dates"]]
            for item in result["dates"]:
                if "scenario_assessment" in item:
                    item["scenario_assessment"].pop("yearly_assessment", None)
                item["climate_checks"] = [{k: v for k, v in check.items() if k != "yearly_results"}
                                          for check in item.get("climate_checks", [])]
        return result
