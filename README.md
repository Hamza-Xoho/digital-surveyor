# Digital Surveyor

Automated vehicle access assessment for UK removals companies. Enter a UK postcode, get a Green/Amber/Red rating for whether each vehicle class can physically reach the property — computed from real Ordnance Survey geometry, Environment Agency LiDAR elevation, and HERE truck routing data.

**Backend:** Python 3.10+ / FastAPI / PostgreSQL 16 + PostGIS | **Frontend:** React 19 / TypeScript / Vite | **Infrastructure:** Docker Compose / Traefik

---

## Contents

- [What It Does](#what-it-does)
- [Quick Start](#quick-start)
- [API Keys](#api-keys)
- [Demo Postcodes](#demo-postcodes)
- [Usage](#usage)
  - [Web UI](#web-ui)
  - [API](#api)
  - [Endpoints](#endpoints)
  - [Vehicle Profiles](#vehicle-profiles)
- [How It Works](#how-it-works)
  - [Assessment Pipeline](#assessment-pipeline)
  - [Road Width Computation](#road-width-computation)
  - [Gradient Analysis](#gradient-analysis)
  - [Turning Space Assessment](#turning-space-assessment)
  - [Scoring](#scoring)
  - [Graceful Degradation](#graceful-degradation)
- [Configuration](#configuration)
  - [Environment Variables](#environment-variables)
  - [LiDAR Tiles](#lidar-tiles)
- [Running Tests](#running-tests)
- [Development](#development)
- [Troubleshooting](#troubleshooting)
- [Architecture](#architecture)
  - [Project Structure](#project-structure)
  - [Data Flow](#data-flow)
  - [Design Patterns](#design-patterns)
  - [Extending](#extending)
- [License](#license)

---

## What It Does

Every removals company has sent an 18-tonne truck to a road it can't fit down. The driver arrives, discovers parked cars on both sides of a 3-metre terrace street, and calls the office. The job gets trans-shipped to a smaller van — three trips instead of one, costing the company hundreds.

Digital Surveyor replaces guesswork with geometry:

1. **Postcode in** — geocode to exact coordinates via postcodes.io.
2. **OS MasterMap** — fetch surveyed road-edge geometry within 200m, compute actual road width from opposing kerb lines.
3. **LiDAR elevation** — read 1m-resolution terrain data, compute approach gradient.
4. **Turning space** — detect dead-ends, compute available turning radius from road polygon geometry.
5. **Route restrictions** — query HERE truck routing for low bridges, weight limits, width limits.
6. **Score** — aggregate all checks into Green/Amber/Red per vehicle class, with a confidence score.

```bash
curl -X POST "http://localhost:8000/api/v1/assessments/quick?postcode=BN2+1TJ"
```

```json
{
  "postcode": "BN2 1TJ",
  "overall_rating": "RED",
  "vehicle_assessments": [
    {
      "vehicle_name": "Luton Van 3.5t",
      "overall_rating": "GREEN",
      "checks": [
        { "name": "Road Width", "rating": "GREEN", "detail": "3.8m available, 2.75m vehicle width, 1.05m clearance" },
        { "name": "Gradient", "rating": "GREEN", "detail": "Max 2.1% gradient, mean 1.4%" },
        { "name": "Turning Space", "rating": "GREEN", "detail": "Not a dead-end" },
        { "name": "Route Restrictions", "rating": "GREEN", "detail": "No restrictions found" }
      ]
    },
    {
      "vehicle_name": "Pantechnicon 18t",
      "overall_rating": "RED",
      "checks": [
        { "name": "Road Width", "rating": "RED", "detail": "3.8m available, 3.05m vehicle width, -0.25m clearance" }
      ]
    }
  ]
}
```

The response includes GeoJSON overlays for roads, buildings, and width measurement lines so the frontend renders everything on an interactive map.

---

## Quick Start

### Prerequisites

You need **Docker** and **Docker Compose v2** installed:

| Platform | Install |
|----------|---------|
| **macOS** | [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop/) |
| **Windows** | [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/) (requires WSL 2) |
| **Linux** | `sudo apt install docker.io docker-compose-v2` then `sudo usermod -aG docker $USER` |

Verify:

```bash
docker --version          # Docker 24+ recommended
docker compose version    # Compose v2.20+ recommended
```

### Start the stack

```bash
git clone <your-repo-url>
cd digital-surveyor
cp .env.example .env
docker compose watch
```

> **Important:** Run `docker compose` from the project root where `.env` exists.

The first build takes 2-5 minutes. Watch for `Uvicorn running on http://0.0.0.0:8000` in the backend logs.

Once running:

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | http://localhost:5173 | Web UI |
| Backend API | http://localhost:8000 | REST API |
| Swagger Docs | http://localhost:8000/docs | Interactive API explorer |
| Adminer | http://localhost:8080 | Database admin |
| Mailcatcher | http://localhost:1080 | Captured emails (dev only) |

> **Apple Silicon (M1/M2/M3/M4):** Works natively. PostGIS runs under Rosetta 2 automatically. In Docker Desktop, ensure "Use Rosetta for x86_64/amd64 emulation on Apple Silicon" is enabled (Settings > General).

---

## API Keys

The assessment pipeline calls external APIs. Without them the pipeline still runs but returns partial results (see [Graceful Degradation](#graceful-degradation)).

| Key | Required? | Source | Free tier |
|-----|-----------|--------|-----------|
| `OS_API_KEY` | **Yes** — without it, no road geometry | [OS Data Hub](https://osdatahub.os.uk/) | 1,000 transactions/month |
| `HERE_API_KEY` | No — route restriction checks skipped | [HERE Developer](https://developer.here.com/) | 250K transactions/month |
| `MAPILLARY_TOKEN` | No — reserved for future use | [Mapillary](https://www.mapillary.com/developer) | Free |

Add them to `.env`:

```bash
OS_API_KEY=your_os_data_hub_key_here
HERE_API_KEY=your_here_api_key_here
```

Superusers can also configure API keys via the web UI: **Settings > API Keys**.

Restart after editing `.env`:

```bash
docker compose down && docker compose watch
```

---

## Demo Postcodes

| Postcode | Scenario | Expected |
|----------|----------|----------|
| `BN3 3EL` | Wide suburban avenue, Hove | All GREEN |
| `BN2 1TJ` | Narrow Brighton terrace | Luton GREEN, 7.5t AMBER, 18t RED |
| `BN1 5FG` | Steep hill approach, Fiveways | Gradient AMBER for trucks |
| `RH16 3AS` | Suburban cul-de-sac, Haywards Heath | 18t AMBER (tight turning) |
| `RH10 1HZ` | Industrial estate, Crawley | All GREEN |
| `BN1 8YJ` | Narrow + steep + dead-end, Hanover | Luton AMBER, 7.5t RED, 18t RED |

---

## Usage

### Web UI

Log in at http://localhost:5173 with `admin@digital-surveyor.dev` and the password from `FIRST_SUPERUSER_PASSWORD` in `.env` (default: `changethis`).

- **Dashboard** — Quick-action cards and API key status (superusers).
- **Assessments** — 70/30 split layout: interactive map + results panel. Enter a postcode, see overlaid road edges, buildings, and width measurements. Toggle between vehicle classes.
- **Settings** — Profile, password, API key wizard (superusers), account deletion.
- **Admin** — User management (superusers).

### API

```bash
# Quick assessment (no auth required)
curl -X POST "http://localhost:8000/api/v1/assessments/quick?postcode=BN1+5FG"

# Raw OS MasterMap geodata (debugging)
curl "http://localhost:8000/api/v1/assessments/geodata/BN1%205FG"
```

### Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/api/v1/assessments/quick?postcode={pc}` | None | Run assessment, return results |
| `POST` | `/api/v1/assessments/?postcode={pc}` | JWT | Run and persist assessment |
| `GET` | `/api/v1/assessments/` | JWT | List saved assessments |
| `GET` | `/api/v1/assessments/{id}` | JWT | Get saved assessment |
| `GET` | `/api/v1/assessments/geodata/{postcode}` | None | Raw OS MasterMap GeoJSON |
| `GET` | `/api/v1/vehicles/` | None | List vehicle profiles |
| `GET` | `/api/v1/settings/api-keys` | Superuser | API key status (masked) |
| `PUT` | `/api/v1/settings/api-keys` | Superuser | Update API keys |
| `POST` | `/api/v1/login/access-token` | None | OAuth2 login |
| `POST` | `/api/v1/users/signup` | None | Register |

Full interactive docs at http://localhost:8000/docs.

### Vehicle Profiles

| Vehicle | Width | Height | Weight | Turning Radius | Mirror Width |
|---------|-------|--------|--------|----------------|-------------|
| Luton Van 3.5t | 2.25m | 3.2m | 3,500 kg | 6.7m | 0.25m |
| Box Truck 7.5t | 2.50m | 3.7m | 7,500 kg | 9.0m | 0.25m |
| Pantechnicon 18t | 2.55m | 4.0m | 18,000 kg | 12.8m | 0.25m |

Total vehicle width for fit calculations: `width_m + (2 * mirror_width_m)`.

---

## How It Works

### Assessment Pipeline

```
UK Postcode (e.g. "BN2 1TJ")
  |
  v
1. GEOCODE (geocoding.py)
   postcodes.io -> lat/lon + BNG easting/northing
  |
  v
2. FETCH OS FEATURES (os_features.py) -- parallel
   TopographicArea -> road polygons, building footprints
   TopographicLine -> kerb edges, road edge lines
  |
  v
3. LIDAR GRADIENT (lidar.py) -- optional
   Environment Agency 1m DTM GeoTIFF -> elevation profile
  |
  v
4. ROAD WIDTH (width_analysis.py)
   Opposing kerb-edge pairs -> perpendicular width samples -> min/max/mean
  |
  v
5. TURNING SPACE (turning_analysis.py) -- per vehicle
   Road polygons near junction -> max inscribed circle radius
  |
  v
6. ROUTE RESTRICTIONS (here_routing.py) -- parallel, per vehicle
   HERE Truck Routing API -> low bridges, weight limits, width limits
  |
  v
7. SCORING (scoring.py) -- per vehicle
   Aggregate checks -> Green/Amber/Red + confidence score
```

Steps 2a/2b run in parallel via `asyncio.gather`. Step 6 runs in parallel across all vehicle classes. Pipeline takes 2-5 seconds cached, 5-15 seconds cold.

### Road Width Computation

1. **Find opposing edge pairs** — Convert OS MasterMap line features to Shapely LineStrings. Match pairs where bearings are within 15 degrees, midpoint separation is 2-15m, and line length exceeds 3m.
2. **Sample perpendicular widths** — Interpolate 20 points along one edge, find nearest points on the opposite edge, measure distances.
3. **Identify pinch points** — Flag the narrowest measurements with BNG coordinates for map rendering.

All geometry uses British National Grid (EPSG:27700) in metres. WGS84 transform applied only for frontend display.

### Gradient Analysis

LiDAR DTM tiles (1m resolution) from the Environment Agency. Elevation sampled along the approach path, gradient computed between consecutive points.

| Vehicle | GREEN | AMBER | RED |
|---------|-------|-------|-----|
| Pantechnicon 18t | 0-5% | 5-8% | >8% |
| Box Truck 7.5t | 0-6% | 6-10% | >10% |
| Default (Luton) | 0-8% | 8-12% | >12% |

### Turning Space Assessment

At dead-ends: select road polygons within 30m of the junction, union them, compute the maximum inscribed circle radius (20x20 grid approximation), compare against the vehicle's turning radius.

### Scoring

| Check | GREEN | AMBER | RED |
|-------|-------|-------|-----|
| Road Width | Clearance > 0.5m | 0-0.5m | Vehicle doesn't fit |
| Gradient | Below amber threshold | Between thresholds | Above red threshold |
| Turning | Radius sufficient | -- | Radius insufficient |
| Route Restrictions | None found | -- | Height/weight/width limit |

Overall rating = worst individual check. Confidence = fraction of checks with real data (0.0-1.0).

### Graceful Degradation

Every external data source is optional. Missing data never crashes the pipeline.

| Missing | Behaviour |
|---------|-----------|
| `OS_API_KEY` not set | Width defaults to AMBER |
| No LiDAR tile | Gradient defaults to AMBER |
| `HERE_API_KEY` not set | Route restrictions default to AMBER |
| HERE API unreachable | Route restrictions default to AMBER with error detail |
| Not a dead-end | Turning check returns GREEN |

---

## Configuration

### Environment Variables

All configuration via `.env` in the project root. See `.env.example` for the full list.

**Core:**

| Variable | Default | Description |
|----------|---------|-------------|
| `ENVIRONMENT` | `local` | `local` / `staging` / `production` |
| `SECRET_KEY` | `changethis` | JWT signing key |
| `FIRST_SUPERUSER` | `admin@digital-surveyor.dev` | Admin email |
| `FIRST_SUPERUSER_PASSWORD` | `changethis` | Admin password |

**Database:**

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_SERVER` | `localhost` | Docker overrides to `db` |
| `POSTGRES_PORT` | `5432` | |
| `POSTGRES_DB` | `digital_surveyor` | |
| `POSTGRES_USER` | `digital_surveyor` | |
| `POSTGRES_PASSWORD` | `changethis` | |

**Geospatial APIs:**

| Variable | Description |
|----------|-------------|
| `OS_API_KEY` | Ordnance Survey Data Hub |
| `HERE_API_KEY` | HERE truck routing |
| `MAPILLARY_TOKEN` | Reserved for future use |
| `LIDAR_TILES_PATH` | Default: `/app/lidar-data` |

### LiDAR Tiles

Gradient analysis requires Environment Agency DTM tiles (free, but large). To find the tile for an area:

```bash
python lidar-data/download_tiles.py 530739 104456
```

Download tiles from https://environment.data.gov.uk/survey and place `.tif` files in `lidar-data/`. Docker mounts this directory read-only.

---

## Running Tests

All external APIs are mocked — no API keys needed.

```bash
# Backend tests (with coverage)
cd backend
uv run pytest tests/ -v
uv run pytest --cov=app tests/

# Lint and format
uv run ruff check .
uv run ruff format .

# Type checking
uv run mypy app/

# Frontend E2E tests (requires Docker stack running)
docker compose run --rm playwright npx playwright test
```

---

## Development

### Outside Docker (hot-reload)

```bash
# Backend
cd backend
pip install -e ".[dev]"
fastapi dev app/main.py

# Frontend (separate terminal)
cd frontend
bun install
bun run dev
```

Keep the Docker `db` service running for PostgreSQL:

```bash
docker compose up db -d
```

### Pre-commit hooks

```bash
cd backend
uv run pre-commit install -f
uv run pre-commit run --all-files
```

### Regenerate API client

The frontend API client is auto-generated from the backend's OpenAPI schema:

```bash
./scripts/generate-client.sh
```

---

## Troubleshooting

### `Variable not set` errors

Run `docker compose` from the project root where `.env` exists:

```bash
cd digital-surveyor
cp .env.example .env
docker compose watch
```

### `pull access denied for backend`

Docker is trying to pull instead of build. Ensure `compose.override.yml` exists (sets `pull_policy: build`).

### `no matching manifest for linux/arm64/v8`

Apple Silicon: enable Rosetta in Docker Desktop (Settings > General).

### Database healthcheck fails

PostGIS can be slow on first start (especially under Rosetta). Wait 30-60 seconds:

```bash
docker compose logs db
docker compose logs backend
```

### `password authentication failed`

PostgreSQL sets the password only on first volume creation. If you changed `POSTGRES_PASSWORD` after initialisation:

```bash
docker compose down -v
docker compose watch
```

> Warning: `-v` removes the database volume and all data.

### `value is not a valid email address` on prestart

Pydantic rejects `.local` TLDs. Use `.dev` instead:

```bash
FIRST_SUPERUSER=admin@digital-surveyor.dev
```

---

## Architecture

### Project Structure

```
digital-surveyor/
├── compose.yml                    # Docker Compose (production)
├── compose.override.yml           # Dev overrides (ports, hot-reload, Mailcatcher)
├── compose.traefik.yml            # Traefik reverse proxy (production HTTPS)
├── .env.example                   # Configuration template
│
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── app/
│   │   ├── main.py                # FastAPI entry point
│   │   ├── models.py              # User, Assessment, GeoCache, VehicleProfile
│   │   ├── crud.py                # Database operations
│   │   ├── errors.py              # Domain exception hierarchy
│   │   ├── core/                  # Config, DB engine, JWT security
│   │   ├── api/routes/            # REST endpoints
│   │   ├── services/              # Business logic
│   │   │   ├── pipeline.py        # 7-step assessment orchestrator
│   │   │   ├── geocoding.py       # postcodes.io + CRS transforms
│   │   │   ├── os_features.py     # OS Features API WFS client
│   │   │   ├── width_analysis.py  # Road width from kerb geometry
│   │   │   ├── lidar.py           # LiDAR tile lookup + gradient
│   │   │   ├── turning_analysis.py # Dead-end turning assessment
│   │   │   ├── here_routing.py    # HERE truck routing
│   │   │   ├── scoring.py         # Green/Amber/Red aggregation
│   │   │   └── cache.py           # GeoCache TTL helpers
│   │   ├── schemas/               # Pydantic request/response models
│   │   └── data/vehicles.json     # Vehicle profiles
│   └── tests/                     # pytest (90% coverage threshold)
│
├── frontend/
│   ├── Dockerfile
│   ├── package.json               # React 19, TanStack Router/Query, Leaflet
│   ├── src/
│   │   ├── routes/                # File-based routing (TanStack Router)
│   │   ├── hooks/                 # useAssessment, useAuth, useApiKeys, useVehicles
│   │   ├── components/
│   │   │   ├── Assessment/        # PostcodeSearch, AssessmentPanel, VehicleCard
│   │   │   ├── Map/               # Leaflet + GeoJSON overlays
│   │   │   ├── UserSettings/      # API key wizard, profile, password
│   │   │   └── ui/                # shadcn/ui primitives (Radix + Tailwind)
│   │   └── client/                # Auto-generated API client (OpenAPI)
│   └── tests/                     # Playwright E2E
│
├── lidar-data/                    # LiDAR GeoTIFFs (user-downloaded, gitignored)
├── demo/                          # Demo addresses + pitch materials
└── scripts/                       # Client generation, test runners
```

### Data Flow

```
POST /api/v1/assessments/quick?postcode=BN2+1TJ
 |
 +-- Validate postcode (Pydantic)
 |
 +---> run_full_assessment(postcode)
        |
        +-- 1. Geocode          postcodes.io -> cache (30d TTL)
        +-- 2. OS Features      WFS API -> cache (90d TTL)     [parallel]
        +-- 3. LiDAR            GeoTIFF -> elevation profile    [optional]
        +-- 4. Road Width       Shapely geometry -> min/max/mean
        +-- 5. Turning Space    Road polygons -> inscribed circle
        +-- 6. Route Checks     HERE API -> cache (7d TTL)      [parallel]
        +-- 7. Scoring          Aggregate -> rating + confidence
```

### Design Patterns

| Pattern | Where | Purpose |
|---------|-------|---------|
| Pipeline / Orchestrator | `pipeline.py` | Coordinates 7 service calls with parallel execution and graceful fallbacks |
| Graceful Degradation | `scoring.py`, `pipeline.py` | Missing data produces AMBER defaults, never crashes |
| Cache-Aside with TTL | `cache.py` | PostgreSQL-backed cache with per-source TTLs (7/30/90 days) |
| Domain Exceptions | `errors.py` | All domain errors inherit from `DigitalSurveyorError` |
| Adapter | `geocoding.py`, `os_features.py`, `here_routing.py` | Each external API wrapped behind a single function |
| BNG-native Geometry | `width_analysis.py`, `turning_analysis.py` | All spatial maths in metres (EPSG:27700); WGS84 only for display |

### Extending

**Add a vehicle class:** Add an entry to `backend/app/data/vehicles.json` and optionally a gradient threshold in `lidar.py`. The pipeline loads vehicles dynamically.

**Add an assessment check:** Create a service module, call it from `pipeline.py`, add it to `scoring.py`. The scoring engine is check-agnostic — it takes a list of `{name, rating, detail}` dicts and picks the worst.

---

## License

[MIT](LICENSE)
