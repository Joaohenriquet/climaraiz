"""REST API and local browser interface for the ClimaRaiz MVP."""
from contextlib import asynccontextmanager
from datetime import date
import json
import logging
from pathlib import Path
import time
from typing import Literal, Optional
import unicodedata
import uuid

from fastapi import BackgroundTasks, FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .climate import ClimateService, json_safe
from .bundle import import_bundle
from . import __version__
from .errors import DomainError
from .ingestion import import_source
from .models import PlantingRequest
from .planting import PlantingService, now
from .settings import DATA_DIR, MODEL_VERSION, MUNICIPALITY, PACKAGE_DIR
from .storage import Database

logger = logging.getLogger("climaraiz")


def normalized(text):
    return "".join(c for c in unicodedata.normalize("NFKD", text.casefold()) if not unicodedata.combining(c))


def create_app(data_dir=None):
    directory = Path(data_dir) if data_dir else DATA_DIR
    database = Database(directory / "climaraiz.sqlite3")
    climate = ClimateService(database)
    planting = PlantingService(database, climate)

    @asynccontextmanager
    async def lifespan(app):
        database.initialize()
        # Single-worker local MVP: interrupted in-process jobs are not left 'processing'.
        with database.connect() as db:
            db.execute("UPDATE analyses SET status='failed',error_json=?,updated_at=? WHERE status='processing'",
                       (json.dumps({"code": "PROCESS_INTERRUPTED", "message": "The server restarted during this analysis. Submit it again."}), now()))
        manifest_path = directory / "sources.json"
        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text())
            missing_raw_sources = []
            for variable, relative_path in manifest.items():
                if database.source(variable) is None:
                    raw_path = directory / relative_path
                    if raw_path.exists():
                        import_source(database, raw_path, variable)
                    else:
                        missing_raw_sources.append(variable)
            if missing_raw_sources:
                import_bundle(database, directory / "prepared_sources.json", missing_raw_sources)
        yield

    app = FastAPI(title="ClimaRaiz API", version=__version__, lifespan=lifespan,
                  description="Historical climate exposure and user-supplied planting windows. No online ZARC integration, yield prediction, or unvalidated crop-risk scores.")
    app.state.database = database
    app.state.climate = climate
    app.state.planting = planting

    @app.middleware("http")
    async def trace_request(request: Request, call_next):
        request.state.request_id = uuid.uuid4().hex
        started = time.perf_counter()
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        logger.info(json.dumps({"request_id": request.state.request_id, "method": request.method,
                               "path": request.url.path, "status": response.status_code,
                               "duration_ms": round(1000*(time.perf_counter()-started), 2)}))
        return response

    @app.exception_handler(DomainError)
    async def domain_error(request, error):
        return JSONResponse(status_code=error.status, content=json_safe({"error": {
            "code": error.code, "message": error.message, "details": error.details,
            "request_id": getattr(request.state, "request_id", None)}}))

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, error):
        return JSONResponse(status_code=400, content={"error": {"code": "INVALID_REQUEST",
            "message": "Request validation failed.", "details": [{"field": ".".join(map(str, e["loc"])),
            "message": e["msg"]} for e in error.errors()], "request_id": getattr(request.state, "request_id", None)}})

    @app.exception_handler(Exception)
    async def internal_error(request, error):
        request_id = getattr(request.state, "request_id", None)
        logger.error("Unhandled request failure: request_id=%s", request_id, exc_info=error)
        return JSONResponse(status_code=500, content={"error": {"code": "INTERNAL_ERROR",
            "message": "An unexpected error occurred. Check the server logs with this request ID.",
            "details": {}, "request_id": request_id}})

    def check_municipality(municipality_id):
        if municipality_id != MUNICIPALITY["id"]:
            raise DomainError("MUNICIPALITY_NOT_FOUND", "Only Campina Grande is configured in this MVP.", 404)

    def check_period(start_year, end_year):
        if end_year < start_year or end_year-start_year > 99:
            raise DomainError("INVALID_REQUEST", "Use an ordered period of at most 100 years.", 400)

    @app.get("/health", tags=["System"])
    def health():
        return {"status": "ok", "model_version": MODEL_VERSION}

    @app.get("/api/v1/municipalities", tags=["Catalog"])
    def municipalities(search: str = Query(default="", max_length=100),
                       state: Optional[str] = Query(default=None, min_length=2, max_length=2),
                       limit: int = Query(default=20, ge=1, le=100)):
        found = normalized(search) in normalized(MUNICIPALITY["name"])
        found = found and (state is None or state.upper() == MUNICIPALITY["state"])
        return {"data": [MUNICIPALITY] if found else [], "limit": limit, "total": int(found)}

    @app.get("/api/v1/crops", tags=["Catalog"])
    def crops():
        return {"data": planting.crops(), "window_source": planting.windows["source"],
                "window_version": planting.windows["version"],
                "assessment": planting.windows.get("assessment", {}),
                "check_sources": planting.windows.get("sources", {})}

    @app.get("/api/v1/data/status", tags=["Climate"])
    def data_status():
        return {"municipality": MUNICIPALITY, "variables": {
            name: climate.availability(name) for name in ("precipitation", "temperature_mean")},
            "temperature_max": {"status": "unavailable", "reason": "NOT_PROVIDED"},
            "temperature_min": {"status": "unavailable", "reason": "NOT_PROVIDED"}}

    @app.get("/api/v1/climate/series", tags=["Climate"])
    def series(municipality_id: int, variable: Literal["precipitation", "temperature_mean", "temperature_max", "temperature_min"],
               aggregation: Literal["daily", "monthly", "annual"] = "annual",
               start_year: int = Query(default=2001, ge=1900, le=2100),
               end_year: int = Query(default=2025, ge=1900, le=2100),
               offset: int = Query(default=0, ge=0), limit: int = Query(default=1000, ge=1, le=10000)):
        check_municipality(municipality_id)
        check_period(start_year, end_year)
        if variable in ("temperature_max", "temperature_min"):
            return {"status": "unavailable", "reason": "DAILY_MAXIMUM_AND_MINIMUM_NOT_PROVIDED", "series": []}
        frame, source = climate.aggregate(variable, aggregation, start_year, end_year)
        records = [{"date": str(day.date()), "value": row.value, "valid_days": int(row.valid_days),
                    "expected_days": int(row.expected_days), "quality_status": row.quality_status}
                   for day, row in frame.iloc[offset:offset+limit].iterrows()]
        return json_safe({"status": "available", "municipality_id": municipality_id, "variable": variable,
                          "aggregation": aggregation, "unit": "degC" if variable == "temperature_mean" else
                          {"daily": "mm/day", "monthly": "mm/month", "annual": "mm/year"}[aggregation],
                          "source": source, "series": records, "pagination": {"total": len(frame), "offset": offset,
                          "limit": limit, "next_offset": offset+limit if offset+limit < len(frame) else None}})

    @app.get("/api/v1/climate/trends", tags=["Climate"])
    def trends(municipality_id: int, start_year: int = Query(default=2001, ge=1900, le=2100),
               end_year: int = Query(default=2025, ge=1900, le=2100)):
        check_municipality(municipality_id)
        check_period(start_year, end_year)
        return {"municipality_id": municipality_id, **climate.trends(start_year, end_year)}

    @app.post("/api/v1/planting/analyses", status_code=202, tags=["Planting"])
    def create_analysis(body: PlantingRequest, background_tasks: BackgroundTasks):
        analysis_id, created = planting.create(body)
        if created:
            background_tasks.add_task(planting.process, analysis_id, body)
        row = database.analysis(analysis_id)
        return {"analysis_id": analysis_id, "status": row["status"], "reused": not created,
                "links": {"result": f"/api/v1/planting/analyses/{analysis_id}"}}

    @app.get("/api/v1/planting/analyses/{analysis_id}", tags=["Planting"])
    def analysis(analysis_id: str):
        return planting.retrieve(analysis_id)

    def find_date(analysis_id, planting_date):
        result = planting.retrieve(analysis_id, include_details=True)
        if result["status"] == "processing":
            raise DomainError("ANALYSIS_PROCESSING", "The analysis is still processing.", 409)
        if result["status"] == "failed":
            raise DomainError("ANALYSIS_FAILED", "The analysis failed; submit it again.", 409, result.get("error"))
        record = next((r for r in result["dates"] if r["date"] == planting_date.isoformat()), None)
        if record is None:
            raise DomainError("PLANTING_DATE_NOT_ELIGIBLE", "This date is not in the analysis planting window.", 422)
        return result, record

    @app.get("/api/v1/planting/analyses/{analysis_id}/dates/{planting_date}", tags=["Planting"])
    def analysis_date(analysis_id: str, planting_date: date):
        result, record = find_date(analysis_id, planting_date)
        return {"analysis_id": analysis_id, "crop_id": result["crop_id"], **record}

    @app.get("/api/v1/planting/analyses/{analysis_id}/dates/{planting_date}/phases", tags=["Planting"])
    def phases(analysis_id: str, planting_date: date):
        _, record = find_date(analysis_id, planting_date)
        return {"analysis_id": analysis_id, "date": planting_date.isoformat(),
                "status": record["phases_status"], "phases": record["phases"]}

    @app.get("/", include_in_schema=False)
    def index():
        return FileResponse(PACKAGE_DIR / "static" / "index.html")

    app.mount("/static", StaticFiles(directory=PACKAGE_DIR / "static"), name="static")
    return app


app = create_app()
