# digital-surveyor

A web application that assesses whether removals vehicles can physically reach a UK property, by computing road width, approach gradient, and turning space from Ordnance Survey geometry and Environment Agency LiDAR elevation data.

Requires **Docker** and **Docker Compose**. Backend: **Python 3.10+**, **FastAPI**, **PostgreSQL 16 + PostGIS**. Frontend: **React 18**, **TypeScript**, **Vite**.

---

### Contents

- [What it does](#what-it-does)
- [Installation](#installation)
  - [Quick start with Docker](#quick-start-with-docker-recommended)
  - [Updating an existing clone](#updating-an-existing-clone)
  - [API keys](#api-keys)
  - [Development install](#development-install)
- [Quick Start](#quick-start)
- [Usage](#usage)
  - [Web UI](#web-ui)
  - [API](#api)
  - [Endpoints](#endpoints)
  - [Vehicle profiles](#vehicle-profiles)
- [How it works](#how-it-works)
  - [The assessment pipeline](#the-assessment-pipeline)
  - [Road width computation](#road-width-computation)
  - [Gradient analysis](#gradient-analysis)
  - [Turning space assessment](#turning-space-assessment)
  - [Scoring](#scoring)
  - [Graceful degradation](#graceful-degradation)
- [Configuration](#configuration)
  - [Environment variables](#environment-variables)
  - [LiDAR tiles](#lidar-tiles)
- [Running tests](#running-tests)
- [Troubleshooting](#troubleshooting)
- [Architecture](#architecture)
  - [Project structure](#project-structure)
  - [Data flow](#data-flow)
  - [Module reference](#module-reference)
  - [Design patterns](#design-patterns)
  - [Adding a new vehicle class](#adding-a-new-vehicle-class)
  - [Adding a new assessment check](#adding-a-new-assessment-check)
- [License](#license)

---


## What it does

Every removals company has sent an 18-tonne truck to a road it can't fit down. The driver arrives, discovers parked cars on both sides of a 3-metre terrace street, and calls the office. The job gets trans-shipped to a smaller van. Three trips instead of one. The customer is furious. The company eats the cost. Dispatchers currently eyeball Google Street View — which is often years out of date — or trust the customer's guess that "a big lorry should be fine."

**Digital Surveyor** replaces guesswork with geometry. Type a UK postcode and it pulls real surveyed road edges from Ordnance Survey MasterMap, computes perpendicular road widths from opposing kerb lines, reads 1m-resolution LiDAR elevation to calculate approach gradient, checks for turning space at dead-ends, and queries HERE for route restrictions like low bridges and weight limits. The result is a Green/Amber/Red access rating for each vehicle class.

```bash
curl -X POST "http://localhost:8000/api/v1/assessments/quick?postcode=BN2+1TJ"
```

```json
{
  "postcode": "BN2 1TJ",
  "latitude": 50.8225,
  "longitude": -0.1372,
  "overall_rating": "RED",
  "vehicle_assessments": [
    {
      "vehicle_name": "Luton Van 3.5t",
      "overall_rating": "GREEN",
      "checks": [
        { "name": "Road Width", "rating": "GREEN", "detail": "3.8m available, 2.75m vehicle width, 1.05m clearance" },
        { "name": "Gradient", "rating": "GREEN", "detail": "Max 2.1% gradient, mean 1.4%" },
        { "name": "Turning Space", "rating": "GREEN", "detail": "Not a dead-end — turning space not required" },
        { "name": "Route Restrictions", "rating": "GREEN", "detail": "No restrictions found on route" }
      ],
      "recommendation": "Access clear for Luton Van 3.5t — all checks passed"
    },
    {
      "vehicle_name": "Pantechnicon 18t",
      "overall_rating": "RED",
      "checks": [
        { "name": "Road Width", "rating": "RED", "detail": "3.8m available, 3.05m vehicle width, -0.25m clearance" },
        { "name": "Gradient", "rating": "GREEN", "detail": "Max 2.1% gradient, mean 1.4%" },
        { "name": "Turning Space", "rating": "GREEN", "detail": "Not a dead-end — turning space not required" },
        { "name": "Route Restrictions", "rating": "GREEN", "detail": "No restrictions found on route" }
      ],
      "recommendation": "Pantechnicon 18t CANNOT access this property — failed: Road Width"
    }
  ],
  "width_analysis": {
    "min_width_m": 3.8,
    "max_width_m": 5.1,
    "mean_width_m": 4.3,
    "pinch_points": [{ "location": [530421, 104312], "width_m": 3.8 }]
  },
  "geojson_overlays": {
    "roads": { "type": "FeatureCollection", "features": ["..."] },
    "buildings": { "type": "FeatureCollection", "features": ["..."] },
    "width_measurements": { "type": "FeatureCollection", "features": ["..."] }
  }
}
```

The response includes GeoJSON overlays for roads, buildings, and width measurement lines so the frontend can render everything on a map.


---


## Installation

### Prerequisites — Install Docker

You need **Docker** and **Docker Compose** (v2) installed before proceeding. If you don't have them:

| Platform | Install method |
|----------|---------------|
| **macOS** | Download [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop/) and run the installer. |
| **Windows** | Download [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/). Requires WSL 2 — the installer will prompt you to enable it. |
| **Linux (Ubuntu/Debian)** | `sudo apt update && sudo apt install docker.io docker-compose-v2` then `sudo usermod -aG docker $USER` (log out and back in). |
| **Linux (other)** | Follow the [official install guide](https://docs.docker.com/engine/install/). |

Verify your installation:

```bash
docker --version          # Docker 24+ recommended
docker compose version    # Compose v2.20+ recommended
```

> **Apple Silicon (M1/M2/M3/M4):** The development setup works natively on Apple Silicon Macs. The PostGIS database image runs under Rosetta 2 emulation automatically. In Docker Desktop, ensure **"Use Rosetta for x86_64/amd64 emulation on Apple Silicon"** is enabled (Settings → General — it's on by default).

### Quick start with Docker (recommended)

Clone the repository and start the full stack with one command. Docker handles Python, Node, and PostgreSQL — nothing else to install.

```bash
git clone https://github.com/hamza-xoho/digital-surveyor.git
cd digital-surveyor
cp .env.example .env      # Create your local config (edit API keys later)
docker compose watch
```

> **Important:** You must run `docker compose` from the **project root** (`digital-surveyor/`). Docker Compose auto-loads the `.env` file from the current directory — running it from elsewhere will fail with `Variable not set` errors.

The first run will **build** the backend and frontend images from source — this takes 2-5 minutes depending on your machine (longer on Apple Silicon due to PostGIS emulation). Subsequent starts are much faster. Wait for the database to initialise and migrations to run. Monitor with `docker compose logs -f backend`. When you see `Uvicorn running on http://0.0.0.0:8000`, the backend is ready.

Once running:

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | http://localhost:5173 | Web UI — postcode search + map |
| Backend API | http://localhost:8000 | REST API |
| Swagger docs | http://localhost:8000/docs | Interactive API explorer |
| Adminer | http://localhost:8080 | Database admin |
| Mailcatcher | http://localhost:1080 | Captured emails (development) |

### Updating an existing clone

If you've already cloned the repo and need to pull the latest changes:

```bash
cd digital-surveyor
git pull origin main
docker compose build --no-cache    # Rebuild images (required when dependencies change)
docker compose watch
```

The `--no-cache` flag ensures Docker picks up changes to `package.json`, `bun.lock`, or `pyproject.toml`. Without it, Docker's layer cache may serve stale dependencies. After one clean rebuild, subsequent `docker compose watch` runs will be fast again.

> **Tip:** If you have local uncommitted changes that conflict with the pull, stash them first: `git stash` → `git pull` → `git stash pop`.

### API keys

The assessment pipeline calls two external APIs. Without them the pipeline still runs but returns partial results (see [Graceful degradation](#graceful-degradation)).

| Key | Required | Source | Free tier |
|-----|----------|--------|-----------|
| `OS_API_KEY` | Yes — without it, no road geometry | [OS Data Hub](https://osdatahub.os.uk/) — sign up, create a project, enable OS Features API | 1,000 transactions/month |
| `HERE_API_KEY` | No — route restriction checks skipped without it | [HERE Developer](https://developer.here.com/) | 250K transactions/month |

Add them to `.env` in the project root:

```bash
# .env (already exists with defaults — add your keys)
OS_API_KEY=your_os_data_hub_key_here
HERE_API_KEY=your_here_api_key_here
```

Restart the stack after changing `.env`:

```bash
docker compose down && docker compose watch
```

### Development install

To run the backend and frontend outside Docker (for hot-reloading or debugging):

```bash
# Backend
cd backend
pip install -e ".[dev]"
fastapi dev app/main.py

# Frontend (in another terminal)
cd frontend
bun install
bun run dev
```

The backend requires a running PostgreSQL+PostGIS instance. The Docker Compose `db` service provides this — you can keep it running and stop only the `backend` and `frontend` containers:

```bash
docker compose stop backend frontend
```


---


## Quick Start

### Docker (recommended)

```bash
docker compose watch
```

Once the backend is ready, run an assessment:

```bash
curl -X POST "http://localhost:8000/api/v1/assessments/quick?postcode=BN3+3EL"
```

This returns a full Green/Amber/Red assessment for a wide suburban avenue in Hove — all three vehicle classes should come back GREEN.

### Web UI

Open http://localhost:5173, log in with `admin@digital-surveyor.dev` and the password from `FIRST_SUPERUSER_PASSWORD` in `.env` (default: `admin123456`), navigate to **Assessments**, and type a postcode.

### Demo postcodes

These postcodes cover the range of real-world scenarios:

| Postcode | Scenario | Expected result |
|----------|----------|-----------------|
| `BN3 3EL` | Wide suburban avenue, Hove | All GREEN |
| `BN2 1TJ` | Narrow Brighton terrace, parked cars both sides | Luton GREEN, 7.5t AMBER, 18t RED |
| `BN1 5FG` | Steep hill approach, Fiveways | Gradient AMBER for trucks |
| `RH16 3AS` | Suburban cul-de-sac, Haywards Heath | 18t AMBER (tight turning) |
| `RH10 1HZ` | Industrial estate, Crawley | All GREEN |
| `BN1 8YJ` | Narrow + steep + dead-end, Hanover | Luton AMBER, 7.5t RED, 18t RED |


---


## Usage

### Web UI

The assessments page is a split-pane layout: 70% interactive map, 30% controls and results. Enter a postcode in the search bar. The map centres on the location and draws GeoJSON overlays for roads, buildings, and width measurement lines. The results panel shows the overall rating and per-vehicle breakdowns. Click a vehicle to see its individual checks.

### API

All assessment endpoints are under `/api/v1/assessments`. The quick assessment endpoint requires no authentication and accepts a postcode as a query parameter.

```bash
# Full assessment — returns Green/Amber/Red per vehicle with GeoJSON
curl -X POST "http://localhost:8000/api/v1/assessments/quick?postcode=BN1+5FG"

# Raw geodata — returns OS MasterMap features around a postcode (for debugging)
curl "http://localhost:8000/api/v1/assessments/geodata/BN1%205FG"
```

### Endpoints

#### `POST /api/v1/assessments/quick?postcode={postcode}`

Run a full access assessment. No authentication required.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `postcode` | `string` (query, required) | UK postcode, e.g. `BN1 1AB`. Validated against UK postcode regex. |
| `vehicle_classes` | `list[string]` (query, optional) | Filter to specific vehicle classes, e.g. `?vehicle_classes=pantechnicon_18t` |

**Response** `200 OK`: Full assessment JSON (see [What it does](#what-it-does) for the complete response shape).

**Errors:**

| Status | Reason |
|--------|--------|
| `400` | Invalid postcode format or postcode not found |
| `502` | Upstream API failure (OS Features, HERE routing) |

#### `POST /api/v1/assessments/?postcode={postcode}`

Run a full assessment **and persist** the result for the authenticated user. Same parameters as `/quick`. Returns the assessment with an `id` and `created_at` field. Requires JWT authentication.

#### `GET /api/v1/assessments/geodata/{postcode}`

Returns raw OS MasterMap GeoJSON FeatureCollections (area and line features) around a postcode. Useful for debugging and verifying the OS API integration.

#### `GET /api/v1/assessments/`

List past saved assessments for the authenticated user. Requires JWT authentication. Returns `{ data: [...], count: N }`.

#### `GET /api/v1/assessments/{assessment_id}`

Get a specific saved assessment by ID. Returns the full stored results. Requires JWT authentication.

### Vehicle profiles

Three vehicle classes are assessed by default, loaded from `backend/app/data/vehicles.json`:

| Vehicle | Width | Height | Weight | Length | Turning radius | Mirror width |
|---------|-------|--------|--------|--------|----------------|-------------|
| **Luton Van 3.5t** | 2.25m | 3.2m | 3,500 kg | 6.7m | 6.7m | 0.25m |
| **Box Truck 7.5t** | 2.50m | 3.7m | 7,500 kg | 8.5m | 9.0m | 0.25m |
| **Pantechnicon 18t** | 2.55m | 4.0m | 18,000 kg | 11.0m | 12.8m | 0.25m |

Total vehicle width for fit calculations is `width_m + (2 * mirror_width_m)`. The Pantechnicon's total width is 3.05m.


---


## How it works

### The assessment pipeline

The core of Digital Surveyor is a 7-step async pipeline in `pipeline.py` that transforms a postcode into a scored access assessment.

```
UK Postcode (e.g. "BN2 1TJ")
     │
     ▼
STEP 1: GEOCODE (geocoding.py)
  postcodes.io → lat/lon + BNG easting/northing
     │
     ▼
STEP 2: FETCH OS FEATURES (os_features.py) — parallel
  ├─ TopographicArea → road polygons, building footprints
  └─ TopographicLine → kerb edges, road edge lines
     │
     ▼
STEP 3: LIDAR GRADIENT (lidar.py) — optional
  Environment Agency 1m DTM GeoTIFF → elevation profile along approach
     │
     ▼
STEP 4: ROAD WIDTH (width_analysis.py)
  Opposing kerb-edge pairs → perpendicular width samples → min/max/mean
     │
     ▼
STEP 5: TURNING SPACE (turning_analysis.py) — per vehicle
  Road area polygons near junction → merge → max inscribed circle radius
     │
     ▼
STEP 6: ROUTE RESTRICTIONS (here_routing.py) — parallel, per vehicle
  HERE Truck Routing API → low bridges, weight limits, width limits
     │
     ▼
STEP 7: SCORING (scoring.py) — per vehicle
  Aggregate all checks → Green/Amber/Red + confidence score
     │
     ├── All GREEN → "Access clear for [vehicle]"
     ├── Any AMBER → "Access possible with caution — concerns: [list]"
     └── Any RED → "[vehicle] CANNOT access — failed: [list]"
```

Steps 2a/2b run in parallel (OS area and line features). Step 6 runs in parallel across all vehicle classes. The pipeline takes 2-5 seconds on a warm cache, 5-15 seconds on a cold call (dominated by the OS Features API).


### Road width computation

This is the core geometric analysis. Given OS MasterMap TopographicLine features (surveyed kerb edges), the system computes the actual road width at multiple points.

**Step 1 — Find opposing edge pairs.** Convert all line features to Shapely LineStrings. Compute the bearing (0-180 degrees, undirected) of each line. Find pairs where: both bearings are within 15 degrees of each other (roughly parallel), midpoint separation is 2-15m (typical UK road width range), and line length is at least 3m (skip tiny fragments). Each line is used in at most one pair. The best match is the closest parallel line.

**Step 2 — Sample perpendicular widths.** For each edge pair, interpolate 20 evenly-spaced points along the left edge. For each point, find the nearest point on the right edge. The distance between them is the road width at that position. This produces 20 width measurements per edge pair.

**Step 3 — Identify pinch points.** Sort all width measurements. The narrowest 10% are flagged as pinch points with their BNG coordinates, so they can be shown on the map.

**Why perpendicular sampling instead of Hausdorff distance?** Hausdorff distance gives a single worst-case number but doesn't show *where* the road narrows. Perpendicular sampling produces a width profile along the road — the frontend can render each measurement as a line on the map, colour-coded by width.

All geometry uses British National Grid (EPSG:27700) coordinates in metres, via Shapely. No projection errors from working in lat/lon.


### Gradient analysis

Environment Agency LiDAR Digital Terrain Model tiles provide 1m-resolution elevation across England. The system reads GeoTIFF files with rasterio.

For a given approach path (currently simplified to a straight line from the property 100m north), it samples elevation at each coordinate and computes the gradient between consecutive points as `abs(elevation_diff / distance) * 100` (percent).

**Gradient classification** (per-vehicle thresholds):

| Vehicle | GREEN | AMBER | RED |
|---------|-------|-------|-----|
| Pantechnicon 18t | 0-5% | 5-8% | >8% |
| Box Truck 7.5t | 0-6% | 6-10% | >10% |
| Default (Luton etc.) | 0-8% | 8-12% | >12% |

Heavier vehicles get stricter thresholds. Thresholds are defined in `GRADIENT_THRESHOLDS` dict in `lidar.py`.

Steep segments (>5% gradient) are identified as contiguous runs and reported with start/end distances along the approach.


### Turning space assessment

At dead-ends, the system checks whether there's enough physical space to turn each vehicle.

**Step 1 — Find road polygons.** From the OS TopographicArea features, select polygons with `DescriptiveGroup` of "Road Or Track" within 30m of the junction point.

**Step 2 — Merge and compute.** Union all nearby road polygons into a single turning area. If the result is a MultiPolygon, use the largest component. Compute the maximum inscribed circle by sampling a 20x20 grid within the polygon's bounding box and finding the interior point furthest from any edge.

**Step 3 — Compare.** If the inscribed circle radius is greater than or equal to the vehicle's turning radius, the vehicle can turn. If not, it's RED.

| Vehicle | Turning radius |
|---------|---------------|
| Luton Van 3.5t | 6.7m |
| Box Truck 7.5t | 9.0m |
| Pantechnicon 18t | 12.8m |

The turning circle GeoJSON is included in the response so the frontend can overlay it on the map.


### Scoring

The scoring engine (`scoring.py`) aggregates four checks per vehicle into a single rating:

| Check | Source | GREEN | AMBER | RED |
|-------|--------|-------|-------|-----|
| **Road Width** | `width_analysis.py` | Clearance > 0.5m | Clearance 0-0.5m | Vehicle doesn't fit |
| **Gradient** | `lidar.py` | Below amber threshold | Between amber and red thresholds | Above red threshold (per vehicle) |
| **Turning Space** | `turning_analysis.py` | Inscribed radius >= turning radius | — | Inscribed radius < turning radius |
| **Route Restrictions** | `here_routing.py` | No restrictions on route | — | Height/weight/width limit on route |

The overall vehicle rating is the **worst** individual check. A confidence score (0.0-1.0) reflects what fraction of checks had actual data available versus defaulting to AMBER.


### Graceful degradation

Every external data source is optional. The pipeline never fails because a data source is missing — it degrades to AMBER ratings with explanatory messages.

| Missing data | Behaviour |
|-------------|-----------|
| `OS_API_KEY` not set | No features fetched. Width analysis returns 0. All width checks default to AMBER: "Width data unavailable — manual check recommended" |
| No LiDAR tile for area | Gradient check defaults to AMBER: "LiDAR data unavailable — gradient not assessed" |
| `HERE_API_KEY` not set | Route restrictions default to AMBER: "Routing check unavailable — check for low bridges manually" |
| HERE API unreachable | Route restrictions default to AMBER with error detail |
| Not a dead-end | Turning space check returns GREEN: "Not a dead-end — turning space not required" (counts as data available for confidence) |


---


## Configuration

### Environment variables

All configuration is via `.env` in the project root. Docker Compose injects these into the containers.

**Core settings:**

| Variable | Default | Description |
|----------|---------|-------------|
| `PROJECT_NAME` | `"Digital Surveyor"` | Shown in API docs and emails |
| `ENVIRONMENT` | `local` | `local`, `staging`, or `production`. Controls secret validation strictness |
| `SECRET_KEY` | `changethis` | JWT signing key. Generate with `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `FIRST_SUPERUSER` | `admin@digital-surveyor.dev` | Admin account email |
| `FIRST_SUPERUSER_PASSWORD` | `changethis` | Admin account password |
| `FRONTEND_HOST` | `http://localhost:5173` | Used for CORS and email links |
| `BACKEND_CORS_ORIGINS` | `http://localhost,http://localhost:5173` | Comma-separated allowed origins |

**Database:**

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_SERVER` | `localhost` | Hostname. Docker Compose overrides to `db` |
| `POSTGRES_PORT` | `5432` | Port |
| `POSTGRES_DB` | `digital_surveyor` | Database name |
| `POSTGRES_USER` | `digital_surveyor` | Database user |
| `POSTGRES_PASSWORD` | `changethis` | Database password |

**Geospatial APIs:**

| Variable | Default | Description |
|----------|---------|-------------|
| `OS_API_KEY` | `""` | Ordnance Survey Data Hub API key |
| `HERE_API_KEY` | `""` | HERE routing API key |
| `MAPILLARY_TOKEN` | `""` | Reserved for future street-level imagery integration |
| `LIDAR_TILES_PATH` | `/app/lidar-data` | Directory containing Environment Agency DTM GeoTIFFs |

**Email (optional):**

| Variable | Default | Description |
|----------|---------|-------------|
| `SMTP_HOST` | `""` | SMTP server. In development, Docker Compose points this at Mailcatcher |
| `SMTP_PORT` | `587` | SMTP port |
| `SMTP_TLS` | `True` | Use TLS |
| `SMTP_USER` | `""` | SMTP username |
| `SMTP_PASSWORD` | `""` | SMTP password |
| `EMAILS_FROM_EMAIL` | `info@example.com` | Sender address |

> **Note:** In development, the Docker Compose override automatically configures Mailcatcher as the SMTP server. All emails are captured at http://localhost:1080 — nothing leaves your machine.


### LiDAR tiles

Gradient analysis requires Environment Agency LiDAR DTM tiles. These are free but must be downloaded manually because they're large (50-200 MB per tile).

To find the tile for a specific area:

```bash
python lidar-data/download_tiles.py 530739 104456
```

Output:

```
Tile reference: TQ30
Expected filename: TQ30_DTM_1m.tif

Download instructions:
1. Go to https://environment.data.gov.uk/survey
2. Search for tile: TQ30
3. Select 'LIDAR Composite DTM 1m' dataset
4. Download the GeoTIFF for tile TQ30
5. Save as: lidar-data/TQ30_DTM_1m.tif
```

Place downloaded `.tif` files in the `lidar-data/` directory. The Docker Compose mounts this directory read-only into the backend container at `/app/lidar-data`.

The system checks for tiles using four filename patterns: `{REF}_DTM_1m.tif`, `{REF}_DTM_1M.tif`, `{ref}_dtm_1m.tif`, and `{REF}_DSM_1m.tif`. If no tile is found, gradient analysis is skipped gracefully.


---


## Running tests

All external APIs are mocked in tests — no API keys needed to run the test suite. The width analysis tests use synthetic Shapely geometries (parallel lines, converging lines) with known expected widths.

```bash
# Run all tests
cd backend
uv run pytest tests/ -v

# With coverage
uv run pytest --cov=app tests/

# Lint and format
uv run ruff check .
uv run ruff format .

# Type checking
uv run mypy app/

# Run a specific test file
uv run pytest tests/services/test_width_analysis.py -v

# Run a specific test
uv run pytest tests/services/test_width_analysis.py::TestVehicleFit::test_red_too_narrow -v

# Frontend E2E tests (requires Docker stack running)
docker compose run --rm playwright npx playwright test
```

Pre-commit hooks via `prek` run ruff, biome, and file checks automatically:

```bash
cd backend
uv run prek install -f    # Install hooks
uv run prek run --all-files  # Run manually
```


---


## Troubleshooting

### `Variable not set` errors on `docker compose watch`

You're running the command from the wrong directory, or `.env` doesn't exist.

```bash
cd digital-surveyor        # Must be in project root
cp .env.example .env       # Create .env if missing
docker compose watch
```

### `pull access denied for backend` / `pull access denied for frontend`

Docker is trying to pull images from Docker Hub instead of building locally. The `compose.override.yml` sets `pull_policy: build` for development. Make sure you're in the project root and haven't deleted `compose.override.yml`.

### `no matching manifest for linux/arm64/v8`

This happens on Apple Silicon Macs. The development override handles this by:
- Setting `platform: linux/amd64` on the PostGIS database (runs under Rosetta 2)
- Using `sj26/mailcatcher` instead of the unmaintained `schickling/mailcatcher`

Ensure Rosetta emulation is enabled in Docker Desktop: **Settings → General → "Use Rosetta for x86_64/amd64 emulation on Apple Silicon"**.

### Database healthcheck fails / backend hangs on startup

The backend waits for PostgreSQL to be healthy before running migrations. If the database is slow to start (common on first run with Rosetta emulation), wait 30-60 seconds and check logs:

```bash
docker compose logs db          # Check PostgreSQL is ready
docker compose logs prestart    # Check migrations ran
docker compose logs backend     # Check backend started
```

### `password authentication failed for user "digital_surveyor"`

PostgreSQL sets the password **only on first volume creation**. If you changed `POSTGRES_PASSWORD` in `.env` after the database was already initialised, the old password is baked into the volume. Fix by removing the volume and starting fresh:

```bash
docker compose down -v          # -v removes the database volume
docker compose watch            # Re-creates DB with current .env password
```

> ⚠️ This deletes all database data. In development that's fine — migrations and seed data will be re-applied automatically.

### `value is not a valid email address` on prestart

Pydantic's email validator (v2.1+) rejects `.local` as a reserved TLD. If your `.env` has `FIRST_SUPERUSER=admin@digital-surveyor.local`, update it:

```bash
# In .env, change:
FIRST_SUPERUSER=admin@digital-surveyor.dev
```

Then restart: `docker compose down && docker compose watch`.

### `Integrity check failed for tarball` during frontend build

Bun's lockfile stores tarball hashes per platform. If you generate `bun.lock` on macOS and Docker builds on Linux, platform-specific packages (e.g. `@biomejs/cli-darwin-arm64` vs `@biomejs/cli-linux-arm64`) will have different hashes. The Dockerfile uses `bun install --no-verify` to handle this automatically.

If you still see this error after pulling new changes, regenerate the lockfile:

```bash
rm -rf node_modules frontend/node_modules bun.lock
bun install
```

Then commit the new `bun.lock` and rebuild.

### `WARN: The "CI" variable is not set`

This warning is harmless — the `CI` variable is only used by the Playwright test service and can be ignored during normal development.


---


## Architecture

> This section is for developers who want to understand, extend, or contribute to the codebase.

### Project structure

```
digital-surveyor/
├── compose.yml                           # Production Docker Compose
├── compose.override.yml                  # Dev overrides (ports, hot-reload, Mailcatcher)
├── compose.traefik.yml                   # Traefik reverse proxy for production
├── .env                                  # All configuration (gitignored in production)
├── .env.example                          # Template with all env vars documented
│
├── backend/
│   ├── Dockerfile                        # Python 3.10+ with geo dependencies
│   ├── pyproject.toml                    # Dependencies: FastAPI, Shapely, rasterio, pyproj
│   ├── alembic.ini                       # Database migration config
│   │
│   ├── app/
│   │   ├── main.py                       # FastAPI app entry point
│   │   ├── models.py                     # SQLModel tables: User, VehicleProfile, Assessment, GeoCache
│   │   ├── crud.py                       # Database CRUD (users + assessments)
│   │   ├── errors.py                     # Domain exception hierarchy
│   │   │
│   │   ├── core/
│   │   │   ├── config.py                 # Pydantic Settings — all env vars validated here
│   │   │   ├── db.py                     # SQLModel engine and session
│   │   │   └── security.py               # JWT token creation, password hashing
│   │   │
│   │   ├── api/
│   │   │   ├── main.py                   # API router aggregation
│   │   │   ├── deps.py                   # Dependency injection (current user, DB session)
│   │   │   └── routes/
│   │   │       ├── assessments.py        # POST /quick, GET /geodata, GET /, GET /{id}
│   │   │       ├── vehicles.py           # Vehicle profile CRUD
│   │   │       ├── users.py              # User management
│   │   │       ├── login.py              # JWT auth endpoints
│   │   │       └── utils.py              # Health check + cache purge admin
│   │   │
│   │   ├── services/                     # Core business logic
│   │   │   ├── pipeline.py               # 7-step assessment orchestrator
│   │   │   ├── geocoding.py              # postcodes.io + BNG/WGS84 transforms (pyproj)
│   │   │   ├── os_features.py            # OS Features API WFS client
│   │   │   ├── width_analysis.py         # Road width from opposing kerb edges (Shapely)
│   │   │   ├── lidar.py                  # LiDAR tile lookup + gradient profiles (rasterio)
│   │   │   ├── turning_analysis.py       # Max inscribed circle in road polygons (Shapely)
│   │   │   ├── here_routing.py           # HERE Truck Routing v8 client
│   │   │   ├── scoring.py                # Green/Amber/Red aggregation per vehicle
│   │   │   ├── cache.py                  # Shared GeoCache read/write/purge helpers
│   │   │   └── vehicles.py               # Vehicle profile loader (JSON, cached)
│   │   │
│   │   ├── schemas/
│   │   │   ├── assessment.py             # Request/response Pydantic models
│   │   │   ├── vehicle.py                # Vehicle profile schemas
│   │   │   └── geodata.py                # BoundingBox helper
│   │   │
│   │   ├── data/
│   │   │   └── vehicles.json             # Default vehicle profiles (3 classes)
│   │   │
│   │   └── alembic/versions/             # Database migrations
│   │
│   └── tests/
│       ├── conftest.py                   # Test database fixtures
│       ├── services/
│       │   ├── test_width_analysis.py    # Width computation + vehicle fit + edge pairing
│       │   ├── test_geocoding.py         # Postcode validation + coordinate transforms
│       │   ├── test_scoring.py           # Rating aggregation + confidence
│       │   ├── test_lidar.py             # Gradient classification thresholds
│       │   ├── test_turning_analysis.py  # Inscribed circle + turning assessment
│       │   ├── test_vehicles.py          # Vehicle profile loading + filtering
│       │   └── test_errors.py            # Domain error hierarchy
│       ├── api/routes/
│       │   ├── test_assessments.py       # Assessment endpoint tests
│       │   ├── test_vehicles.py          # Vehicle endpoint tests
│       │   ├── test_login.py             # Auth flow tests
│       │   └── test_users.py             # User CRUD tests
│       ├── crud/
│       │   └── test_user.py              # Database layer tests
│       └── scripts/
│           └── test_backend_pre_start.py # Startup script tests
│
├── frontend/
│   ├── Dockerfile                        # Nginx serving built React app
│   ├── package.json                      # React 18, TanStack Router/Query, Leaflet
│   │
│   ├── src/
│   │   ├── routes/
│   │   │   ├── _layout/
│   │   │   │   ├── assessments.tsx       # Main assessment page (map + results panel)
│   │   │   │   ├── admin.tsx             # User management
│   │   │   │   └── settings.tsx          # User settings
│   │   │   ├── login.tsx                 # Login page
│   │   │   └── __root.tsx                # App shell
│   │   │
│   │   ├── hooks/
│   │   │   ├── useAssessment.ts          # Assessment mutation + types
│   │   │   ├── useVehicles.ts            # Vehicle profile queries
│   │   │   └── useAuth.ts               # Auth state management
│   │   │
│   │   ├── components/
│   │   │   ├── Assessment/               # PostcodeSearch, AssessmentPanel
│   │   │   ├── Map/                      # MapContainer (Leaflet + GeoJSON overlays)
│   │   │   ├── Admin/                    # User management components
│   │   │   └── ui/                       # shadcn/ui primitives
│   │   │
│   │   └── client/                       # Auto-generated API client from OpenAPI spec
│   │
│   └── tests/                            # Playwright E2E tests
│
├── lidar-data/
│   ├── download_tiles.py                 # Tile reference calculator + download instructions
│   └── *.tif                             # LiDAR GeoTIFFs (not committed — user downloads)
│
└── demo/
    ├── demo-addresses.json               # 6 test postcodes with expected results
    ├── pitch-deck.md                     # Business case for removals companies
    └── cached-responses/                 # Saved API responses for offline demos
```


### Data flow

```
POST /api/v1/assessments/quick?postcode=BN2+1TJ
 │
 ├─ Validate postcode regex (Pydantic schema)
 │
 └─► run_full_assessment(postcode) (pipeline.py)
      │
      ├─ 1. GEOCODE (geocoding.py)
      │     │  postcodes.io API → cache in GeoCache (30-day TTL)
      │     └─► { lat, lon, easting, northing }
      │
      ├─ 2. FETCH OS FEATURES (os_features.py) — asyncio.gather (parallel)
      │     ├─ TopographicArea WFS → cache in GeoCache (90-day TTL)
      │     │  └─► GeoJSON FeatureCollection (roads, buildings, paths, surfaces)
      │     └─ TopographicLine WFS → cache in GeoCache (90-day TTL)
      │        └─► GeoJSON FeatureCollection (kerb edges, road lines)
      │
      ├─ 3. LIDAR (lidar.py) — optional
      │     │  BNG coords → tile reference (e.g. TQ30) → file lookup
      │     │  rasterio windowed read → elevation samples
      │     └─► { max_gradient_pct, mean_gradient_pct, steep_segments[] }
      │
      ├─ 4. ROAD WIDTH (width_analysis.py)
      │     │  Line features → find_opposing_edge_pairs() → sample_perpendicular_widths()
      │     └─► { min_width_m, max_width_m, mean_width_m, pinch_points[], measurement_lines_geojson }
      │
      ├─ 5. TURNING SPACE (turning_analysis.py) — per vehicle
      │     │  Road polygons near junction → unary_union → max inscribed circle
      │     └─► { available_radius_m, required_radius_m, can_turn, turning_circle_geojson }
      │
      ├─ 6. ROUTE RESTRICTIONS (here_routing.py) — asyncio.gather (parallel, per vehicle)
      │     │  HERE Truck Router v8 → cache in GeoCache (7-day TTL)
      │     └─► { restrictions[], warnings[], rating }
      │
      └─ 7. SCORING (scoring.py) — per vehicle
            │  Aggregate 4 checks → worst = overall rating
            │  Confidence = data_available_count / 4
            └─► { overall_rating, checks[], recommendation, confidence }
```


### Module reference

#### `pipeline.py` — Assessment orchestrator

| Export | Purpose |
|--------|---------|
| `run_full_assessment(postcode, vehicle_classes?)` | Runs all 7 steps, returns complete assessment dict |

Coordinates all service modules. Handles parallelism with `asyncio.gather` for OS feature fetching (step 2) and HERE routing (step 6). Catches exceptions from individual steps and continues with partial data rather than failing the entire assessment.

#### `width_analysis.py` — Road width from kerb geometry

| Export | Purpose |
|--------|---------|
| `find_opposing_edge_pairs(features, bearing_tolerance, min_distance, max_distance)` | Pairs parallel kerb lines. Tolerance: 15 degrees, distance: 2-15m |
| `sample_perpendicular_widths(left, right, n_samples)` | 20 width measurements between two edges |
| `compute_road_widths(line_features_geojson)` | Main entry: features in → min/max/mean/pinch_points out |
| `check_vehicle_width_fit(road_width, vehicle_width, mirror_width, clearance_margin)` | Single vehicle fit check → GREEN/AMBER/RED |

**Why 15-degree bearing tolerance?** UK roads curve. Adjacent line segments on the same road can differ by 5-10 degrees. Tighter tolerance misses valid pairs on bends. Wider tolerance risks matching lines from different roads. 15 degrees was calibrated against Brighton terrace streets and suburban cul-de-sacs.

#### `geocoding.py` — Postcode to coordinates

| Export | Purpose |
|--------|---------|
| `geocode_postcode(postcode)` | Async. postcodes.io → lat/lon + BNG easting/northing |
| `latlng_to_bng(lat, lon)` | WGS84 → British National Grid (pyproj) |
| `bng_to_latlng(easting, northing)` | BNG → WGS84 (pyproj) |
| `validate_postcode(postcode)` | Regex check against UK postcode format |
| `normalise_postcode(postcode)` | Uppercase + single space normalisation |

#### `os_features.py` — Ordnance Survey WFS client

| Export | Purpose |
|--------|---------|
| `fetch_area_features(easting, northing, radius)` | TopographicArea polygons in 200m bbox. Filtered to: Road Or Track, Building, Path, General Surface |
| `fetch_line_features(easting, northing, radius)` | TopographicLine edges in 200m bbox. Filtered to: Road Or Track, Path |
| `get_features_wgs84(feature_collection)` | Transform BNG → WGS84 for frontend display |

Handles WFS pagination (100 features/page, max 10 pages). Caches results for 90 days — OS MasterMap changes infrequently.

#### `lidar.py` — Elevation and gradient

| Export | Purpose |
|--------|---------|
| `find_lidar_tile(easting, northing, tiles_dir)` | BNG → OS grid tile reference → file lookup |
| `get_elevation(easting, northing, tile_path)` | Single elevation reading from GeoTIFF |
| `get_gradient_profile(path_coords, tile_path, sample_interval)` | Elevation + gradient along a path |
| `classify_gradient(gradient_pct, vehicle_class)` | Gradient → GREEN/AMBER/RED with vehicle-specific thresholds |

Rasterio is optional — if not installed, gradient analysis is skipped with a clear error message.

#### `scoring.py` — Rating aggregation

| Export | Purpose |
|--------|---------|
| `score_vehicle_access(vehicle, width_result, gradient_result, turning_result, route_restrictions)` | Combines 4 checks into overall rating + confidence + recommendation text |

The overall rating is the worst individual check (RED > AMBER > GREEN). Confidence is `data_available_count / 4` — if 3 of 4 checks had real data, confidence is 0.75.

#### `here_routing.py` — Truck route restrictions

| Export | Purpose |
|--------|---------|
| `check_truck_restrictions(origin, destination, height, width, weight)` | HERE Truck Router v8 → route notices for restrictions |

Uses an origin point approximately 1km north of the target property. Parses route notices for height (low bridges), weight, and width restrictions. Cached for 7 days.

#### `turning_analysis.py` — Dead-end turning assessment

| Export | Purpose |
|--------|---------|
| `assess_turning_space(road_features, junction_point, turning_radius, search_radius)` | Can vehicle turn at this junction? |
| `compute_max_inscribed_circle_radius(polygon)` | Largest circle that fits inside a polygon (20x20 grid approximation) |

#### `cache.py` — Shared GeoCache helpers

| Export | Purpose |
|--------|---------|
| `get_cached(cache_key)` | Look up cached result from GeoCache table (TTL-aware) |
| `set_cached(cache_key, data, ttl_days)` | Store or update cached result with TTL |
| `purge_expired_cache()` | Delete all expired entries, returns count |

Used by geocoding (30-day TTL), os_features (90-day TTL), and here_routing (7-day TTL). Eliminates duplicated cache code.

#### `vehicles.py` — Vehicle profile loader

| Export | Purpose |
|--------|---------|
| `load_all_vehicles()` | Load from JSON, cached with `lru_cache` |
| `get_vehicles(vehicle_classes?)` | Get all or filter by class name |

Single source of truth for vehicle profiles. Used by pipeline and vehicles API route.

#### `errors.py` — Domain exception hierarchy

| Export | Purpose |
|--------|---------|
| `DigitalSurveyorError` | Base exception for all domain errors |
| `InvalidPostcodeError` | Postcode failed format validation |
| `PostcodeNotFoundError` | Postcode not found by geocoder |
| `ExternalAPIError` | External API returned an error |
| `LiDARTileNotFoundError` | No LiDAR tile covers the coordinates |
| `PipelineError` | Assessment pipeline unrecoverable error |


### Design patterns

| Pattern | Where | Why |
|---------|-------|-----|
| **Pipeline / Orchestrator** | `pipeline.py` | Coordinates 7 independent service calls with parallel execution and graceful fallbacks |
| **Graceful Degradation** | `scoring.py`, `pipeline.py` | Every external data source is optional. Missing data → AMBER default, never a crash |
| **Cache-Aside with TTL** | `cache.py`, all services | External API responses cached in PostgreSQL via shared `get_cached`/`set_cached` with per-source TTLs (30/90/7 days). Avoids redundant API calls and respects rate limits |
| **Domain Exception Hierarchy** | `errors.py`, routes | All domain errors inherit from `DigitalSurveyorError`. Routes catch specific subtypes. No bare `ValueError` or `Exception` for domain logic |
| **Adapter** | `geocoding.py`, `os_features.py`, `here_routing.py` | Each external API is wrapped behind a simple Python function. Swapping data sources means changing one module |
| **Async Parallelism** | `pipeline.py` steps 2 and 6 | `asyncio.gather` for independent API calls. OS area + line features fetched simultaneously. HERE routing for all vehicles fetched simultaneously |
| **BNG-native Geometry** | `width_analysis.py`, `turning_analysis.py` | All spatial computation in British National Grid metres. Avoids lat/lon projection distortion. WGS84 transform applied only for frontend display |


### Adding a new vehicle class

**1. Add the vehicle profile** (`backend/app/data/vehicles.json`):

```json
{
  "name": "Curtain-Sider 26t",
  "vehicle_class": "curtain_sider_26t",
  "width_m": 2.55,
  "length_m": 13.5,
  "height_m": 4.2,
  "weight_kg": 26000,
  "turning_radius_m": 14.5,
  "mirror_width_m": 0.30
}
```

**2. Add gradient threshold if needed** (`backend/app/services/lidar.py`):

```python
GRADIENT_THRESHOLDS: dict[str, dict[str, float]] = {
    "pantechnicon_18t": {"amber": 5.0, "red": 8.0},
    "truck_7_5t": {"amber": 6.0, "red": 10.0},
    "curtain_sider_26t": {"amber": 4.5, "red": 7.0},  # Add new entry
    "default": {"amber": 8.0, "red": 12.0},
}
```

**3. Add tests.**

No other modules need to change — the pipeline loads vehicles dynamically from `vehicles.json` and iterates over them. Width checks, turning checks, route restrictions, and scoring all use the vehicle dict's dimensions directly.


### Adding a new assessment check

To add a new check (e.g., parking restrictions, street-level imagery analysis):

**1. Create the service** (`backend/app/services/parking.py`):

```python
async def check_parking_restrictions(lat: float, lon: float) -> dict:
    # Call external API, return { "rating": "GREEN"|"AMBER"|"RED", "detail": "..." }
    ...
```

**2. Call it from the pipeline** (`backend/app/services/pipeline.py`):

```python
parking_result = await check_parking_restrictions(lat, lon)
```

**3. Add it to the scoring** (`backend/app/services/scoring.py`):

Add a new check block following the same pattern as the existing 4 checks. Increment `total_checks` from 4 to 5.

**4. Add tests.**

The scoring engine is check-agnostic — it collects a list of `{ name, rating, detail }` dicts and takes the worst. Adding a check is additive.


---


## License

MIT
