"""Joint historical criteria matching with a common, explicit yearly denominator."""

METHOD = "all_included_checks_without_events"


def assess_scenario(checks, start_year, end_year, configuration):
    included = [check for check in checks if check["definition"].get("include_in_assessment") is True]
    result = {"status": "unavailable", "reason": None, "method": configuration.get("method"),
              "evaluated_years": 0, "years_meeting_criteria": None, "years_not_meeting_criteria": None,
              "scenario_criteria_met_pct": None, "excluded_years": [], "yearly_assessment": [],
              "included_checks": [{"type": check["definition"]["type"], "phase": check["phase"],
                                   "variable": check["variable"]} for check in included],
              "blocking_checks": [], "validation_status": "exploratory",
              "interpretation": "historical_scenario_criteria_match_not_crop_success_probability"}
    if configuration.get("method") != METHOD:
        result["reason"] = "UNSUPPORTED_ASSESSMENT_METHOD"
        return result
    if not included:
        result["reason"] = "NO_CHECKS_INCLUDED"
        return result
    for check in included:
        if check["status"] != "available" and check["reason"] != "NO_COMPLETE_PHASE_YEARS":
            result["blocking_checks"].append({"type": check["definition"]["type"],
                "phase": check["phase"], "reason": check["reason"]})
        elif check["status"] == "available" and "event_definition" not in check:
            result["blocking_checks"].append({"type": check["definition"]["type"],
                "phase": check["phase"], "reason": "EVENT_NOT_DEFINED"})
    if result["blocking_checks"]:
        result["reason"] = "REQUIRED_CHECK_UNAVAILABLE"
        return result
    indexed = [{row["year"]: row for row in check["yearly_results"]} for check in included]
    matched = evaluated = 0
    for year in range(start_year, end_year+1):
        reasons, failures = [], []
        for check, rows in zip(included, indexed):
            row = rows.get(year)
            identity = {"type": check["definition"]["type"], "phase": check["phase"]}
            if row is None or row["status"] != "available" or row.get("event_occurred") is None:
                reasons.append({**identity, "reason": "MISSING_OR_INCOMPLETE_CHECK_YEAR",
                                "missing_days": row.get("missing_days") if row else None})
            elif row["event_occurred"] is True:
                failures.append(identity)
        if reasons:
            result["excluded_years"].append({"year": year, "reasons": reasons})
            result["yearly_assessment"].append({"year": year, "status": "excluded", "criteria_met": None})
            continue
        evaluated += 1
        matched += int(not failures)
        result["yearly_assessment"].append({"year": year, "status": "evaluated", "criteria_met": not failures,
                                           "failed_checks": failures})
    if not evaluated:
        result["reason"] = "NO_COMMON_COMPLETE_YEARS"
        return result
    result.update(status="available", reason=None, evaluated_years=evaluated,
                  years_meeting_criteria=matched, years_not_meeting_criteria=evaluated-matched,
                  scenario_criteria_met_pct=100*matched/evaluated)
    return result
