# ClimaRaiz

Historical climate exploration and planting-window scenarios for Campina Grande, Brazil.

## Repository structure

- `backend/`: Python FastAPI application, climate data processing, tests and API documentation.
- `frontend/`: reserved for the standalone frontend application.

The backend currently also serves the existing browser dashboard from `backend/climaraiz/static/`.

## Run locally

From this repository root:

```sh
cd backend
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[test]'
.venv/bin/python -m climaraiz serve
```

Open http://127.0.0.1:8000 for the dashboard or http://127.0.0.1:8000/docs for the interactive API documentation. The versioned daily dataset is loaded automatically on first startup; raw CSV files and the local SQLite database are ignored by Git.

See [backend documentation](backend/README.md) for data preparation, API routes, scenario criteria and tests.
