# MousseMate — Architecture & Decision Log

> This document is the single source of truth for MousseMate's technical decisions.
> It is maintained across sessions and should be kept in the root of the repository.
> Both human developers and AI assistants (Claude Code, Claude.ai) should refer to it before making architectural decisions.
> For day-to-day operational conventions (commands, code style, sync runbooks) see [CLAUDE.md](CLAUDE.md).

---

## 1. Project Overview

**MousseMate** is a private, friend-group web app — "Strava for beer".
Users log beer check-ins, get personal statistics, follow their mates, and see a shared feed of who's drinking what where.

**Not intended for commercial use.** Internal tool for a small group of friends.

**Live:** https://frontend-production-5ba2.up.railway.app (API: https://backend-production-43d3.up.railway.app)

---

## 2. Roadmap

### V1 — Core Loop ✅ *(shipped 2026-05)*
- Log a beer entry (name, type/style, volume, bar, rating, notes, timestamp)
- Personal stats dashboard: weekly/monthly counts, total liters, top styles, Plotly charts
- Responsive webapp (mobile-friendly in Chrome, no native app needed)

### V2 — Multi-user & Venues ✅ *(shipped 2026-06)*
- Authentication system (JWT: register, login, `/auth/me`)
- Venue system: entries grouped by (date, bar) in the feed
- Paris bar referential: OSM-sourced `bar` table powering autocomplete (went beyond the original "scrape listings" plan — see §6)
- pytest test suite for backend services (entries, analytics, auth, follows, venue grouping, bar sync)

### V3 — Social ✅ *(shipped 2026-05)*
- Mates system (follow/unfollow, user search)
- Shared feed: own + mates' entries, grouped by venue — covers the cross-friends venue view
- Cheers (likes) on entries

> V3 landed before the V2 bar referential — auth unblocked the social loop, venues came after.

### Ongoing — Bar referential scale-out
- The bar referential is Paris-only. Target: France-wide, then global.
- **Constraint:** adding cities must be a data change, not a code rewrite. Parameterize the Overpass area query and `city` column; no multi-city UI/config until asked.

### V4 — Geo & Analytics *(next)*
- GPS capture at entry time
- Heatmap of entry locations
- Spatial analytics (city trends, radius-based discovery)
- City/venue achievements (gamification)
- Decision pending: adopt PostGIS (currently plain float lat/lng — radius queries and heatmaps are where PostGIS starts paying for itself)

---

## 3. Technical Stack

| Layer | Technology | Rationale |
|---|---|---|
| Backend | **FastAPI** (Python 3.12) | Lightweight, async-native, modern. No need for Django's batteries for an API-only backend. |
| Database | **PostgreSQL 16** | Relational, reliable, PostGIS-ready for geo features in V4. |
| ORM | **SQLAlchemy 2.0** + **Alembic** | Standard Python ORM + migrations. |
| Auth | **JWT** (python-jose style, bcrypt hashing) | Stateless, simple for an SPA + API split. |
| Frontend | **React 18** + **Vite** + **TypeScript** | Fast dev experience, large ecosystem, transferable knowledge. |
| UI Components | **shadcn/ui** + **Tailwind CSS** | High quality, unstyled-by-default components. Avoids generic AI aesthetics. |
| Charts | **Plotly** (plotly.js-dist-min, factory pattern) | Interactive stats charts. |
| Bar data | **OpenStreetMap** via Overpass API | Single source for the bar referential. Never Google Maps/Places. |
| Containerization | **Docker Compose** | `db` + `db_test` + optional `api` container; backend & frontend run natively in dev. |
| Config | **pydantic-settings** | Type-safe environment variable management. |
| Python deps | **uv** | Modern package manager, replaces pip+venv. Faster, proper dependency resolution, manages Python versions. |
| Linting/Formatting | **ruff** | Single tool for both linting and formatting. Replaces black + isort + flake8. |
| Hosting | **Railway** | PaaS, low ops overhead. Backend (Dockerfile), frontend (nixpacks + `vite preview`), managed Postgres. |

---

## 4. Repository Structure

```
moussemate/
├── ARCHITECTURE.md          # This file
├── CLAUDE.md                # AI assistant operational guide
├── README.md
├── .env.example             # Environment variable template (never commit .env)
├── docker-compose.yml       # db (5433) + db_test (5434) + optional api container
├── .vscode/
│   └── settings.json        # Ruff formatter + Python interpreter (committed)
│
├── backend/
│   ├── Dockerfile           # Railway image; CMD = start.sh
│   ├── start.sh             # Prod boot: migrations, then uvicorn
│   ├── railway.toml
│   ├── pyproject.toml       # uv dependencies + ruff config
│   ├── uv.lock
│   ├── alembic/versions/    # Database migrations
│   ├── scripts/
│   │   └── sync_osm_bars.py # OSM → DB bar sync (run manually, idempotent)
│   └── app/
│       ├── main.py          # FastAPI app entrypoint, CORS, router registration
│       ├── core/
│       │   ├── config.py    # Pydantic settings (reads .env)
│       │   └── security.py  # Password hashing, JWT creation
│       ├── db/session.py    # Engine, SessionLocal, Base, get_db()
│       ├── models/          # entry, user, user_follow, like, bar
│       ├── schemas/         # entry, user, bar
│       ├── services/        # Business logic (no DB calls in routers)
│       │   ├── entry.py     # Entry CRUD + venue (feed) grouping
│       │   ├── analytics.py # Stats logic
│       │   ├── user.py      # User CRUD
│       │   ├── follow.py    # Mates logic
│       │   ├── like.py      # Cheers logic
│       │   ├── bar.py       # Bar search + OSM↔DB sync reconciliation
│       │   └── osm.py       # Overpass API client (network only, no DB)
│       ├── api/
│       │   ├── router.py    # Aggregates all endpoint routers
│       │   ├── deps.py      # get_current_user dependency
│       │   ├── auth.py      # /auth/*
│       │   ├── entry.py     # /entries, /entry/* (incl. cheers, stats)
│       │   ├── follow.py    # /users, /mates, /follow
│       │   └── bar.py       # GET /bars search
│       └── tests/           # pytest suite (real Postgres test DB on 5434)
│
└── frontend/
    ├── package.json / vite.config.ts / tailwind.config.ts / tsconfig.json
    └── src/
        ├── App.tsx          # Router setup
        ├── api/             # Typed fetch wrappers: auth, bars, entries, follow
        ├── components/
        │   ├── EntryForm.tsx        # Log entry form fields
        │   ├── BarAutocomplete.tsx  # Bar picker backed by GET /bars (debounced)
        │   ├── LogBeerModal.tsx     # Modal wrapper around EntryForm
        │   ├── EntryCard.tsx        # Single entry (with Cheers button)
        │   ├── VenueCard.tsx        # Venue grouping in the feed
        │   └── ProtectedRoute.tsx   # Auth guard
        ├── pages/
        │   ├── Feed.tsx     # Main feed (own + mates' entries, grouped by venue)
        │   ├── Login.tsx / Register.tsx
        │   ├── Mates.tsx    # Follow / mates management
        │   └── Profile.tsx  # Unified profile: beers list + stats (own or mate's)
        ├── hooks/           # Custom React hooks
        └── types/           # TypeScript interfaces mirroring backend schemas
```

---

## 5. Data Model

### `entry`

| Field | Type | Notes |
|---|---|---|
| id | integer | PK, auto-increment |
| user_id | integer | FK → `user.id`, required |
| name | string(255) | Optional (beer name) |
| type | string(100) | Required (style: IPA, Stout, Lager…) |
| volume | float | Required (mL) |
| drink_datetime | datetime | Required — stored naive UTC, serialized with `Z` suffix |
| bar_id | integer | FK → `bar.id`, required (id 1 = "Unknown bar" placeholder for pre-referential entries) |
| rating | float | Optional, 0.0–5.0 |
| notes | text | Optional free text |
| created_at | datetime | Auto, server-side |
| updated_at | datetime | Auto on update |

### `user`

id · username (unique) · hashed_password · created_at

### `user_follow`

(follower_id, followed_id) composite PK · created_at

### `user_entry_like` (Cheers)

(user_id, entry_id) composite PK · created_at

### `bar` (OSM referential)

| Field | Type | Notes |
|---|---|---|
| id | integer | PK, auto-increment |
| osm_id | bigint | OSM element id |
| osm_type | string(10) | `node` / `way` / `relation` — unique with osm_id |
| name | string(255) | Required (unnamed OSM elements are skipped) |
| amenity | string(50) | `bar`, `pub`, `restaurant` |
| latitude / longitude | float | Required — plain floats, no PostGIS yet |
| address | string(500) | Optional (`addr:housenumber` + `addr:street`) |
| postcode | string(10) | Optional — arrondissement for Paris |
| city | string(100) | `"Paris"` for now — scale-out target: France, then global |
| is_closed | boolean | Default false — set by sync when bar disappears from OSM; never deleted |
| created_at / updated_at | datetime | Same pattern as `entry` |

**Planned additions (V4):** GPS capture on entries (latitude/longitude at log time).

---

## 6. Bar Referential & OSM Sync

- **Single source: OpenStreetMap** (Overpass API). Never scrape Google Maps; never store Google Places data.
- Scope: amenity `bar` / `pub` / `restaurant` inside the Paris admin boundary.
- Sync (`backend/scripts/sync_osm_bars.py`) is a **reconciliation**, not a re-import:
  - in OSM, not in DB → insert
  - in both → update fields if changed; reopen if closed
  - in DB, not in OSM → `is_closed = true` (never delete — entries may reference the bar)
  - safety guard: abort without writing if OSM returns < 70% of the open bars currently in DB (protects against partial Overpass responses)
- Network code (`services/osm.py`) is separate from DB reconciliation (`services/bar.py`) so sync logic is testable without network.

---

## 7. API Design

Base path: `/api` (no version prefix — will add `/v1` when a breaking change requires it).

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/auth/register` | Create account |
| POST | `/auth/login` | Get JWT token |
| GET | `/auth/me` | Current user |
| GET | `/entries` | Feed: own + mates' entries, grouped by venue (date, bar) |
| POST | `/entry` | Log a new entry |
| GET | `/entry/{id}` | Get single entry |
| PATCH | `/entry/{id}` | Update an entry |
| DELETE | `/entry/{id}` | Delete an entry |
| GET | `/entry/stats/summary` | Stats summary (weekly/monthly, total liters, top styles) |
| POST | `/entry/{id}/cheer` | Cheer (like) an entry |
| DELETE | `/entry/{id}/cheer` | Remove a cheer |
| GET | `/users/search` | Search users by username |
| GET | `/users/{id}` | Public user profile |
| GET | `/mates` | List followed users |
| POST | `/follow/{user_id}` | Follow a user |
| DELETE | `/unfollow/{user_id}` | Unfollow a user |
| GET | `/bars` | Bar search (powers autocomplete) |

---

## 8. Environment Variables

```bash
# backend/.env (never commit — use .env.example as template)
# Use @127.0.0.1:5433 for local dev (Docker db is mapped to host port 5433)
# Use @db:5432 inside Docker Compose (api container)
DATABASE_URL=postgresql://moussemate:moussemate@127.0.0.1:5433/moussemate
ALLOWED_ORIGINS=["http://localhost:5173"]   # prod: must list the frontend URL (JSON array)
DEBUG=true
```

> **Note:** The db container is exposed on host port **5433** (not 5432) to avoid conflict with a local PostgreSQL installation. The test DB (`db_test`) is on **5434**.

---

## 9. Local Dev Setup

### First-time setup

```bash
cp .env.example backend/.env
docker compose up db -d
cd backend && uv sync && uv run alembic upgrade head
cd ../frontend && npm install
```

### Daily startup (three terminals)

```bash
docker compose up db -d                                          # terminal 1
cd backend && uv run uvicorn app.main:app --reload --port 8000  # terminal 2
cd frontend && npm run dev                                       # terminal 3
```

### Tests

```bash
docker compose up db_test -d
cd backend && uv run pytest
```

### Migrations

```bash
cd backend
uv run alembic revision --autogenerate -m "describe the change"
uv run alembic upgrade head
```

API: `http://localhost:8000` · Frontend: `http://localhost:5173` · Swagger: `http://localhost:8000/docs`

---

## 10. Key Conventions

- **No business logic in routers.** Routers call services; services talk to the DB.
- **Schemas ≠ Models.** Pydantic schemas for I/O, SQLAlchemy models for DB. Never mix.
- **Migrations via Alembic.** Never use `Base.metadata.create_all()` in production.
- **`.env` is never committed.** `.env.example` documents all required variables.
- **Frontend types mirror backend schemas.** Keep `src/types/` in sync manually for now (codegen in future).
- **Ruff for everything.** Line length 120. Rules: E, F, I, UP, B (B008 ignored — FastAPI DI pattern).
- Full operational conventions (tuple-over-list for Pydantic sequences, pandas rules, datetime handling…) live in [CLAUDE.md](CLAUDE.md).

---

## 11. Deployment (Railway)

Project `confident-ambition`, region `us-west2` (keep API and DB in the same region):

- **Backend** — root `/backend`, Dockerfile build. **Boot lives in `backend/start.sh` (image CMD): migrations, then uvicorn.** Never set `startCommand` in railway.toml with `&&` chains — Railway execs it without a shell.
- **frontend** — root `/frontend`, nixpacks + `vite preview`. `VITE_API_BASE_URL` is baked at build time — changing it requires a redeploy.
- **Postgres** — managed Railway instance.

Deploys are push-to-deploy (`railway up` fails while service roots have a leading slash). Prod bar sync: `cd backend && railway run --service Backend -- uv run python scripts/sync_osm_bars.py [--dry-run]`.

Escape hatch if Railway stops fitting: VPS (Hetzner/DigitalOcean).

---

## 12. Decision Log

| Date | Decision | Rationale |
|---|---|---|
| 2026-05-19 | FastAPI over Django | API-only backend, no templates needed, modern async support |
| 2026-05-19 | React over Angular | Lighter weight, better fit for small app, more transferable |
| 2026-05-19 | 2 containers (api + db) | DB always separate; frontend runs natively in dev |
| 2026-05-19 | Geo fields deferred to V4 | V2/V3 focus on users and social; geo added once core social loop is stable |
| 2026-05-19 | No auth in V1 | Faster to first working product; clean stub planned for V2 |
| 2026-05-19 | Named MousseMate | "Mousse" = beer foam (FR slang), "Mate" = social drinking buddy |
| 2026-05-19 | uv for Python deps | Modern standard, faster than pip, proper lockfile, developer already uses it |
| 2026-05-19 | ruff for linting + formatting | Single tool replaces black + isort + flake8; line-length 120 |
| 2026-05-19 | Docker db on host port 5433 | Avoid conflict with developer's local PostgreSQL already running on 5432 |
| 2026-05-19 | Commit .vscode/settings.json | Ensures consistent formatter and interpreter path for all contributors |
| 2026-05-22 | JWT auth (not server sessions) | Stateless, simple for SPA + API split |
| 2026-05-22 | pytest against a real Postgres test DB (port 5434) | Same engine as prod; no SQLite/mock divergence |
| 2026-05-22 | Railway over Render | First deploy attempt worked; free tier sufficient for friend group |
| 2026-06-11 | OSM (Overpass) as single bar data source | Open data, legal to store; never scrape Google Maps or store Places data |
| 2026-06-11 | `entry.bar` free text → non-null `bar_id` FK | Referential integrity; "Unknown bar" placeholder (id 1) absorbs pre-referential entries |
| 2026-06-11 | Bar sync = reconciliation, never delete | Entries reference bars; disappeared bars get `is_closed=true`; <70% guard against partial Overpass responses |
| 2026-06-11 | Datetimes stored naive UTC, serialized with `Z` | Single convention end-to-end; avoids tz-aware/naive mixing in SQLAlchemy |
| 2026-06-11 | No PostGIS yet — plain float lat/lng | Autocomplete needs no spatial queries; revisit at V4 (radius search, heatmaps) |
| 2026-06-12 | Prod boot via `start.sh` as image CMD | Railway execs `startCommand` without a shell — `&&` chains silently run only the first command |
