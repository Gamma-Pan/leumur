# Leumur — data to plots

A Svelte 5 / D3 interface and FastAPI backend for traceable Eurostat charts. Ask for annual nominal GDP, total population, or unemployment in a supported European country. The backend retrieves article context and dataset metadata, validates a constrained chart plan, fetches the actual observations, and returns data plus provenance. The model never supplies numerical observations or executable code.

## Run

Requires Python 3.12+, Docker Engine and Docker Compose. From the repository root:

```bash
bash scripts/setup.sh
docker compose exec -T backend python -m app.ingest --articles
```

The setup script creates a private ignored `.env` with a random PostgreSQL password, builds all services, and indexes curated dataset metadata. Article ingestion fetches the three live Statistics Explained articles. Use `docker compose ps` and `curl -s http://127.0.0.1:8000/api/health` to check readiness. The frontend development server listens on port 5173; the API listens on port 8000. Database ports are 55432 for PostgreSQL, 6379 for Redis, and 16333/16334 for Qdrant, bound to localhost.

If the embedding model download is blocked, this **explicit diagnostic fallback** runs the application with lexical retrieval:

```bash
EMBEDDING_BACKEND=lexical bash scripts/setup.sh
EMBEDDING_BACKEND=lexical docker compose exec -T backend python -m app.ingest --articles
```

The running backend inherits the mode when its container is created. To switch back, run setup without the override and re-ingest articles. Separate Qdrant indexes prevent mixing embedding modes. Re-ingestion invalidates cached charts. The lexical fallback is displayed as `lexical`, never described as semantic retrieval.

## LLM configuration

Without credentials the prototype uses deterministic interpretation of its narrow supported scope. Local semantic retrieval does not require an API key. For constrained LLM planning and OpenAI semantic embeddings, securely set `LLM_API_KEY` in the environment or private `.env`, then rerun setup and article ingestion. `LLM_MODEL` defaults to `gpt-4.1-mini`; `EMBEDDING_MODEL` defaults to `text-embedding-3-small`. Do not commit or print keys. OpenAI requests need HTTPS access to `api.openai.com`. The LLM integration is covered by mocked contract tests; a real provider call requires a usable key.

The plan schema permits only known dataset codes, countries, line/bar charts, and bounded year counts. A deterministic scope guard rejects unsupported real GDP, per-capita measures, growth, multiple countries, forecasts, and explicit date ranges. An LLM output must preserve the validated measure, country and interval; it may choose the chart type. This deliberately conservative prototype can be expanded after adding proper measure disambiguation.

## Data and interface

- Live data is fetched from Eurostat's Statistics API, decoded from JSON-stat and checked against fixed dimensions.
- Article context and dataset metadata are stored in PostgreSQL and indexed in Qdrant.
- Redis caches chart responses for an hour, with provenance timestamps retained.
- Charts support line/bar views, a data table, source details, missing-value gaps, raw observation flags and CSV export.
- Synthetic demo mode is opt-in and conspicuously labeled; live failures never fall back to invented values.
- Supported countries and dataset filters are returned by `GET /api/catalog`.

See [the Eurostat investigation](docs/eurostat-investigation.md) for tested requests and decoding details.

## Checks

```bash
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.txt
(cd backend && ../.venv/bin/python -m pytest -q)
(cd frontend && npm ci && npm run check && npm run build)
# With the app running and Chromium installed:
(cd frontend && npm run test:e2e)
```

Browser tests exercise live Greece GDP, chart/table switching, CSV export, unsupported measures and mobile demo labeling. Set `CHROMIUM_PATH` if Chromium is installed elsewhere. Docker image builds run frontend type checks and a production asset build; the Compose frontend serves Vite for development.

## Cloud environment

Use the existing checkout; each cloud task is already isolated. No worktree is needed. Docker builds and the backend use the environment's trusted CA bundle (`SSL_CERT_FILE`, defaulting to the system bundle) without disabling TLS verification. External HTTP requests inherit proxy settings; internal Qdrant requests explicitly bypass proxy environment variables. The CA is mounted as a BuildKit/runtime secret and is not baked into images.

Required domains are `ec.europa.eu` and `storage.googleapis.com`, plus the package/container registry presets. `api.openai.com` is needed only for the optional provider. In the current cloud instance the embedding artifact initially remained blocked, so functional validation used explicitly labeled lexical retrieval. Saving a draft domain requirement does not prove runtime access.

Named Docker volumes retain data across container restarts. Do not assume those volumes survive cloud environment publication/restoration; re-ingestion is reproducible. Stop with `docker compose stop`; `docker compose down -v` deletes database and model data.

This is a local development prototype, with no authentication or production deployment configured. Database schema creation uses SQLAlchemy `create_all` for the initial schema. Add Alembic migrations, scheduled ingestion, provider evaluations, request quotas and authentication before deployment. The unemployment article currently discusses monthly une_rt_m; the app uses the explicitly labeled annual companion une_rt_a. Population uses the article’s directly referenced demo_gind dataset.

The current scope does not include automatic SDMX discovery, multi-series charts, or general data uploads.
