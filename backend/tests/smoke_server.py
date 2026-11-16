"""Exercise the running local server without driving or rendering a browser."""
import argparse
import json
from pathlib import Path
import time

import httpx


def main(base_url="http://127.0.0.1:8000"):
    with httpx.Client(base_url=base_url, timeout=30) as client:
        for path in ("/", "/health", "/static/app.js", "/static/styles.css", "/api/v1/data/status", "/openapi.json"):
            response = client.get(path)
            response.raise_for_status()
            print(f"GET {path}: {response.status_code}")
        status = client.get("/api/v1/data/status").json()
        assert all(s["status"] == "available" for s in status["variables"].values())
        for crop_id in (1, 2, 3):
            response = client.post("/api/v1/planting/analyses", json={
                "municipality_id": 2504009, "crop_id": crop_id, "planting_year": 2027,
                "cycle_days": 120, "historical_period": {"start_year": 2001, "end_year": 2025},
                "phases": [{"id": "first", "name": "First scenario segment", "start_day": 0, "end_day": 29},
                           {"id": "remaining", "name": "Remaining scenario segment", "start_day": 30, "end_day": 119}],
                "check_windows": [
                    {"id": "flowering", "phase_id": "remaining", "name": "Illustrative flowering", "start_day": 40, "end_day": 65},
                    {"id": "pollination", "phase_id": "remaining", "name": "Illustrative pollination", "start_day": 45, "end_day": 55}]})
            response.raise_for_status()
            path = response.json()["links"]["result"]
            for _ in range(100):
                result = client.get(path).json()
                if result["status"] in ("completed", "failed"):
                    break
                time.sleep(.1)
            assert result["status"] == "completed", result
            assert len(result["dates"]) == 30
            selected = result["dates"][0]
            assert all(row["scenario_assessment"]["status"] == "available" for row in result["dates"])
            assert selected["scenario_assessment"]["evaluated_years"] == 25
            assert selected["risk_level"] in ("low", "moderate", "high")
            assert selected["historical_assessment"]["risk_level"] == selected["risk_level"]
            assert selected["scenario_assessment"]["risk_level"] == selected["risk_level"]
            selected_detail = client.get(path + "/dates/" + selected["date"]).json()
            assert selected_detail["scenario_assessment"]["scenario_criteria_met_pct"] == selected["scenario_assessment"]["scenario_criteria_met_pct"]
            assert selected["historical_assessment"]["precipitation"]["evaluated_years"] == 25
            detail = client.get(path + "/dates/" + selected["date"] + "/phases").json()
            assert len(detail["phases"]) == 2
            assert detail["phases"][0]["risk_level"] == "not_supported"
            linked = detail["phases"][1]
            assert linked["scenario_assessment"]["status"] == "available"
            assert linked["risk_level"] in ("low", "moderate", "high")
            assert all(check["window"]["phase_id"] == "remaining" for check in linked["climate_checks"])
            assert detail["phases"] == selected_detail["phases"]
            print(f"{crop_id}: 30 dates, 25 common complete years, scenario matching and phase details verified")
        schema = client.get("/openapi.json").json()
        output = Path(__file__).resolve().parents[1] / "docs"
        output.mkdir(exist_ok=True)
        (output / "openapi.json").write_text(json.dumps(schema, indent=2))
        print("Saved docs/openapi.json")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    main(parser.parse_args().base_url)
