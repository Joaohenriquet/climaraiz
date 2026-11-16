"""Capture actual API examples against an isolated copy of the local database."""
import json
from pathlib import Path
import shutil
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient
from climaraiz.main import create_app
from climaraiz.settings import DATABASE_PATH


def main():
    examples = []
    with tempfile.TemporaryDirectory() as folder:
        target = Path(folder)
        shutil.copy2(DATABASE_PATH, target / "climaraiz.sqlite3")
        with TestClient(create_app(target)) as client:
            def capture(method, url, body=None):
                response = client.request(method, url, json=body) if body is not None else client.request(method, url)
                entry = {"method": method, "url": url, "status_code": response.status_code,
                         "response": response.json()}
                if body is not None:
                    entry["request"] = body
                examples.append(entry)
                return entry["response"]

            for url in ["/health", "/api/v1/municipalities?search=campina&state=PB&limit=20",
                        "/api/v1/crops", "/api/v1/data/status",
                        "/api/v1/climate/series?municipality_id=2504009&variable=precipitation&aggregation=daily&start_year=2001&end_year=2025&limit=2",
                        "/api/v1/climate/trends?municipality_id=2504009&start_year=2001&end_year=2025"]:
                capture("GET", url)
            body = json.loads((Path(__file__).parent / "requests/all_phase_analysis.json").read_text())
            created = capture("POST", "/api/v1/planting/analyses", body)
            url = created["links"]["result"]
            capture("GET", url)
            detail = capture("GET", url + "/dates/2027-04-25")
            capture("GET", url + "/dates/2027-04-25/phases")
            capture("GET", "/api/v1/planting/analyses/nonexistent")
    output = {"note": "Actual responses. Phase offsets are illustrative scenarios, not validated cultivar parameters. GET collections contain full returned values.",
              "examples": examples}
    (Path(__file__).parent / "api_examples.json").write_text(json.dumps(output, ensure_ascii=False, allow_nan=False, indent=2))
    print(json.dumps({"analysis_id": created["analysis_id"], "detail": detail["historical_assessment"],
                      "scenario_assessment": detail["scenario_assessment"],
                      "checks": [{k:v for k,v in c.items() if k not in ("yearly_results", "definition", "window", "limitation")} for c in detail["climate_checks"]]}, indent=2))


if __name__ == "__main__":
    main()
