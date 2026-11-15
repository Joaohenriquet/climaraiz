"""Local CLI: import CSV sources, export prepared daily data, or run the server."""
import argparse
import json
import logging

from .climate import ClimateService
from .ingestion import import_source
from .settings import DATA_DIR
from .storage import Database
from .bundle import export_bundle


def main():
    parser = argparse.ArgumentParser(description="ClimaRaiz local climate application")
    sub = parser.add_subparsers(dest="command", required=True)
    importer = sub.add_parser("import-data", help="Import the two Giovanni CSVs")
    importer.add_argument("--precipitation", required=True)
    importer.add_argument("--temperature", required=True)
    exporter = sub.add_parser("export-daily", help="Export aligned local daily observations")
    exporter.add_argument("--output", default=str(DATA_DIR / "climate_daily.csv"))
    sub.add_parser("export-bundle", help="Export complete daily data and provenance for fresh-clone startup")
    serve = sub.add_parser("serve", help="Start the local API and dashboard")
    serve.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    database = Database(DATA_DIR / "climaraiz.sqlite3")
    database.initialize()
    if args.command == "import-data":
        for variable, path in (("precipitation", args.precipitation), ("temperature_mean", args.temperature)):
            info = import_source(database, path, variable)
            print(json.dumps({"variable": variable, **info}, indent=2))
    elif args.command == "export-bundle":
        manifest = export_bundle(database, DATA_DIR)
        print(f"Exported prepared daily bundle with SHA-256 {manifest['data_sha256']}")
    elif args.command == "export-daily":
        climate = ClimateService(database)
        rain, _ = climate.daily("precipitation")
        temp, _ = climate.daily("temperature_mean")
        joined = rain[["value", "quality_status"]].rename(columns={"value": "precipitation_mm", "quality_status": "precipitation_quality"}).join(
            temp[["value", "quality_status"]].rename(columns={"value": "temperature_mean_c", "quality_status": "temperature_quality"}), how="outer")
        joined.index.name = "date"
        joined.to_csv(args.output)
        print(f"Exported {len(joined)} daily records to {args.output}")
    else:
        import uvicorn
        logging.basicConfig(level=logging.INFO)
        uvicorn.run("climaraiz.main:app", host="127.0.0.1", port=args.port, workers=1)


if __name__ == "__main__":
    main()
