# MousseMate — Architecture & Decision Log

> This document is the single source of truth for MousseMate's technical decisions.
> It is maintained across sessions and should be kept in the root of the repository.
> Both human developers and AI assistants (Claude Code, Claude.ai) should refer to it before making architectural decisions.

---

## 1. Project Overview

**MousseMate** is a private, friend-group web app — "Strava for beer".
Users log beer check-ins and get personal statistics. Future versions add geolocation features and a social layer.

**Not intended for commercial use.** Internal tool for a small group of friends.

---

## 2. Roadmap

### V1 — Core Loop
- Log a beer check-in (name, brewery, style, rating, notes, timestamp)
- Personal stats dashboard: weekly/monthly counts, streaks, favorite styles, top breweries
- Responsive webapp (mobile-friendly in Chrome, no native app needed)
- Single user (no auth yet)

### V2 — Geo
- Capture GPS coordinates at check-in time (groundwork laid in V1 schema)
- Heatmap of check-in locations
- City/venue achievements (gamification)

### V3 — Social
- Multi-user + authentication
- Friend graph
- Shared feed (see what friends are drinking)
- "Drinking together" feature (co-check-in)

---

## 3. Technical Stack

| Layer | Technology | Rationale |
|---|---|---|
| Backend | **FastAPI** (Python) | Lightweight, async-native, modern. No need for Django's batteries for an API-only backend. |
| Database | **PostgreSQL** | Relational, reliable, PostGIS-ready for geo features in V2. |
| ORM | **SQLAlchemy** + **Alembic** | Standard Python ORM + migrations. |
| Frontend | **React** + **Vite** | Fast dev experience, large ecosystem, transferable knowledge. |
| UI Components | **shadcn/ui** + **Tailwind CSS** | High quality, unstyled-by-default components. Avoids generic AI aesthetics. |
| Containerization | **Docker Compose** | Two containers: `api` + `db`. Frontend runs natively via Vite dev server locally. |
| Config | **pydantic-settings** | Type-safe environment variable management. |
| Python deps | **uv** | Modern package manager, replaces pip+venv. Faster, proper dependency resolution, manages Python versions. |
| Linting/Formatting | **ruff** | Single tool for both linting and formatting. Replaces black + isort + flake8. |

---

## 4. Repository Structure

```
moussemate/
├── ARCHITECTURE.md          # This file
├── README.md
├── .env.example             # Environment variable template (never commit .env)
├── .gitignore
├── docker-compose.yml       # Defines api + db containers
├── .vscode/
│   └── settings.json        # Ruff formatter + Python interpreter (committed)
│
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml       # uv dependencies + ruff config
│   ├── uv.lock              # Pinned dependency lockfile (committed)
│   ├── alembic/             # Database migrations
│   │   ├── env.py
│   │   └── versions/
│   └── app/
│       ├── main.py          # FastAPI app entrypoint, CORS, router registration
│       ├── core/
│       │   └── config.py    # Pydantic settings (reads from .env)
│       ├── db/
│       │   └── session.py   # SQLAlchemy engine, SessionLocal, Base, get_db()
│       ├── models/          # SQLAlchemy ORM models
│       │   └── checkin.py
│       ├── schemas/         # Pydantic request/response schemas
│       │   └── checkin.py
│       ├── services/        # Business logic (no DB calls in routers)
│       │   └── checkin.py
│       ├── api/
│       │   └── v1/
│       │       ├── router.py        # Aggregates all endpoint routers
│       │       └── endpoints/
│       │           └── checkins.py  # CRUD + stats endpoints
│       └── tests/
│
└── frontend/
    ├── index.html
    ├── package.json
    ├── vite.config.ts
    ├── tailwind.config.ts
    ├── tsconfig.json
    └── src/
        ├── main.tsx
        ├── App.tsx
        ├── api/             # Typed API client (fetch wrappers)
        ├── components/      # Reusable UI components
        ├── pages/           # Route-level page components
        │   ├── CheckIn.tsx  # Log a beer
        │   └── Stats.tsx    # Dashboard
        ├── hooks/           # Custom React hooks
        └── types/           # TypeScript interfaces mirroring backend schemas
```

---

## 5. Data Model

### CheckIn (V1, geo-ready for V2)

| Field | Type | Notes |
|---|---|---|
| id | integer | PK, auto-increment |
| beer_name | string | Required |
| brewery | string | Optional |
| style | string | Optional (IPA, Stout, Lager…) |
| rating | float | Optional, 0.0–5.0 |
| notes | text | Optional free text |
| latitude | float | Optional, for V2 geo |
| longitude | float | Optional, for V2 geo |
| venue | string | Optional, bar/place name |
| city | string | Optional |
| created_at | timestamp | Auto, server-side |
| updated_at | timestamp | Auto on update |

**V2 additions (not yet in schema):** `user_id` (FK), `co_checkin_ids` (social)

---

## 6. API Design

Base path: `/api/v1`

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/checkins` | Log a new beer |
| GET | `/checkins` | List check-ins (paginated) |
| GET | `/checkins/{id}` | Get single check-in |
| PATCH | `/checkins/{id}` | Update a check-in |
| DELETE | `/checkins/{id}` | Delete a check-in |
| GET | `/checkins/stats/summary` | Weekly/monthly stats |

---

## 7. Environment Variables

```bash
# backend/.env (never commit — use .env.example as template)
# Use @127.0.0.1:5433 for local dev (Docker db is mapped to host port 5433)
# Use @db:5432 inside Docker Compose (api container)
DATABASE_URL=postgresql://moussemate:moussemate@127.0.0.1:5433/moussemate
ALLOWED_ORIGINS=["http://localhost:5173"]
DEBUG=true
```

> **Note:** The db container is exposed on host port **5433** (not 5432) to avoid conflict with a local PostgreSQL installation that may already be running on 5432.

---

## 8. Local Dev Setup

### First-time setup

```bash
# 1. Copy env template
cp .env.example backend/.env

# 2. Start DB container
docker compose up db -d

# 3. Install backend dependencies and run migrations
cd backend
uv sync
uv run alembic upgrade head

# 4. Install frontend dependencies
cd ../frontend && npm install
```

### Daily startup (three terminals)

```bash
docker compose up db -d                                          # terminal 1
cd backend && uv run uvicorn app.main:app --reload --port 8000  # terminal 2
cd frontend && npm run dev                                       # terminal 3
```

### Adding a new migration

```bash
cd backend
uv run alembic revision --autogenerate -m "describe the change"
uv run alembic upgrade head
```

### Dependency management (backend)

```bash
uv add <package>        # add a runtime dependency
uv add --dev <package>  # add a dev dependency
```

API available at: `http://localhost:8000`
Frontend available at: `http://localhost:5173`
API docs (Swagger): `http://localhost:8000/docs`

---

## 9. Key Conventions

- **No business logic in routers.** Routers call services; services talk to the DB.
- **Schemas ≠ Models.** Pydantic schemas for I/O, SQLAlchemy models for DB. Never mix.
- **Migrations via Alembic.** Never use `Base.metadata.create_all()` in production.
- **`.env` is never committed.** `.env.example` documents all required variables.
- **API versioned from day 1** (`/api/v1/`) to avoid painful refactors later.
- **Frontend types mirror backend schemas.** Keep `src/types/` in sync manually for now (codegen in future).
- **Ruff for everything.** Line length 120. Rules: E, F, I, UP, B (B008 ignored — FastAPI DI pattern). Format + lint run automatically on save via VS Code.

---

## 10. Deployment (planned)

- **Target:** Render or Railway (PaaS, low ops overhead)
- **DB:** Managed PostgreSQL (provider's offering, not a container)
- **Frontend:** Static build served via CDN or same PaaS
- **Path:** Local Docker Compose → Render/Railway → VPS (Hetzner/DigitalOcean) if needed

---

## 11. Decision Log

| Date | Decision | Rationale |
|---|---|---|
| 2026-05-19 | FastAPI over Django | API-only backend, no templates needed, modern async support |
| 2026-05-19 | React over Angular | Lighter weight, better fit for small app, more transferable |
| 2026-05-19 | 2 containers (api + db) | DB always separate; frontend runs natively in dev |
| 2026-05-19 | Geo fields in V1 schema | Avoid migration pain when V2 geo features land |
| 2026-05-19 | No auth in V1 | Faster to first working product; clean stub planned for V2 |
| 2026-05-19 | Named MousseMate | "Mousse" = beer foam (FR slang), "Mate" = social drinking buddy |
| 2026-05-19 | uv for Python deps | Modern standard, faster than pip, proper lockfile, developer already uses it |
| 2026-05-19 | ruff for linting + formatting | Single tool replaces black + isort + flake8; line-length 120 |
| 2026-05-19 | Docker db on host port 5433 | Avoid conflict with developer's local PostgreSQL already running on 5432 |
| 2026-05-19 | Commit .vscode/settings.json | Ensures consistent formatter and interpreter path for all contributors |
