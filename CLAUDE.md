# MousseMate — Claude Code Guide

> Operational guide for AI-assisted development. For architecture, decisions, and roadmap see [ARCHITECTURE.md](ARCHITECTURE.md).

---

## Current phase: V2 — Bars referential

**V1 (core loop) and V3 (auth, social) are done**: JWT auth, follows (mates), likes (cheers), feed. Current work is the **bar referential**: a `bar` table sourced from OpenStreetMap, scoped to **Paris** for now.

> **TODO(scale):** the bar referential aims to become France-wide, then global. Anything bar-related (queries, sync, schema) should be written so that adding cities is a data change, not a code rewrite — but do not build multi-city UI/config until asked.

No PostGIS yet — plain float lat/lng columns.

---

## Starting the app (3 terminals)

```bash
docker compose up db -d                                              # terminal 1
cd backend && uv run uvicorn app.main:app --reload --port 8000      # terminal 2
cd frontend && npm run dev                                           # terminal 3
```

API: http://localhost:8000 · Swagger: http://localhost:8000/docs · Frontend: http://localhost:5173

---

## Backend

**Stack:** FastAPI · SQLAlchemy 2.0 · Alembic · pydantic-settings · Python 3.12 · uv

**Structure:**
```
backend/app/
├── main.py              # App entrypoint, CORS, router registration
├── core/
│   ├── config.py        # Pydantic settings (reads .env)
│   └── security.py      # Password hashing, JWT creation
├── db/session.py        # Engine, SessionLocal, Base, get_db()
├── models/              # SQLAlchemy ORM models: entry, user, user_follow, like, bar
├── schemas/             # Pydantic schemas: entry, user, bar
├── services/
│   ├── entry.py         # Entry CRUD + feed grouping
│   ├── analytics.py     # Stats logic
│   ├── user.py          # User CRUD
│   ├── follow.py        # Mates (follow) logic
│   ├── like.py          # Cheers (like) logic
│   ├── bar.py           # Bar search + OSM↔DB sync reconciliation
│   └── osm.py           # Overpass API client (network only, no DB)
├── api/
│   ├── router.py        # Aggregates all endpoint routers
│   ├── deps.py          # get_current_user dependency
│   ├── auth.py          # /auth/register, /auth/login, /auth/me
│   ├── entry.py         # Entry endpoints
│   ├── follow.py        # Mates endpoints
│   └── bar.py           # GET /bars search
└── (backend/scripts/)
    └── sync_osm_bars.py # OSM → DB bar sync (run manually)
```

**Conventions:**
- No business logic in routers — routers call services, services talk to the DB
- Schemas ≠ Models — Pydantic for I/O, SQLAlchemy for DB, never mix them
- Migrations via Alembic only — never `Base.metadata.create_all()` in production
- API is flat for now (no `/v1/` prefix) — do not add versioning unless asked
- `get_db()` is the only way to get a DB session in endpoints (FastAPI DI)

**Dependency management:**
```bash
uv add <package>         # runtime dependency
uv add --dev <package>   # dev dependency
uv sync                  # install from lockfile
```

**Migrations:**
```bash
cd backend
uv run alembic revision --autogenerate -m "describe the change"
uv run alembic upgrade head
```

---

## DB schema (current)

Table: `entry`

| Column | Type | Notes |
|---|---|---|
| id | integer | PK, auto-increment |
| user_id | integer | FK → user.id, required |
| name | string(255) | Optional (beer name) |
| type | string(100) | Required (style: IPA, Stout…) |
| volume | float | Required (mL) |
| drink_datetime | datetime | Required |
| bar_id | integer | FK → bar.id, required (id 1 = "Unknown bar" placeholder seeded by migration for pre-referential entries) |
| rating | float | Optional, 0.0–5.0 |
| notes | text | Optional |
| created_at | datetime | Server default |
| updated_at | datetime | Auto on update |

Table: `user` — id, username (unique), hashed_password, created_at
Table: `user_follow` — (follower_id, followed_id) composite PK, created_at
Table: `user_entry_like` — (user_id, entry_id) composite PK, created_at

Table: `bar` (OSM referential — see "Bar referential" below)

| Column | Type | Notes |
|---|---|---|
| id | integer | PK, auto-increment |
| osm_id | bigint | OSM element id |
| osm_type | string(10) | `node` / `way` / `relation` — unique with osm_id |
| name | string(255) | Required (unnamed OSM elements are skipped) |
| amenity | string(50) | `bar`, `pub`, `restaurant` |
| latitude / longitude | float | Required |
| address | string(500) | Optional (`addr:housenumber` + `addr:street`) |
| postcode | string(10) | Optional — arrondissement for Paris |
| city | string(100) | `"Paris"` for now — TODO(scale): France/global |
| is_closed | boolean | Default false — set by sync when bar disappears from OSM |
| created_at / updated_at | datetime | Same pattern as `entry` |

---

## Bar referential & OSM sync

- **Single source: OpenStreetMap** (Overpass API). Never scrape Google Maps; never store Google Places data.
- Scope: amenity `bar` / `pub` / `restaurant` inside the Paris admin boundary. **TODO(scale):** parameterize area by city/country for France-wide, then global coverage.
- Sync is a **reconciliation**, not a re-import (`backend/scripts/sync_osm_bars.py`, run with `uv run python scripts/sync_osm_bars.py` from `backend/`):
  - in OSM, not in DB → insert
  - in both → update name / amenity / address / postcode / lat / lng if changed; reopen if it was closed
  - in DB, not in OSM → `is_closed = true` (never delete — entries may reference the bar). This includes the migration-seeded "Unknown bar" placeholder: it closes on the first sync and disappears from the autocomplete, by design.
  - safety guard: abort without writing if OSM returns < 70% of the open bars currently in DB (protects against partial Overpass responses)
- Network code (Overpass client) lives in `services/osm.py`; DB reconciliation in `services/bar.py` — keep them separate so the sync logic is testable without network.

---

## Frontend

**Stack:** React 18 · Vite · TypeScript · Tailwind CSS · shadcn/ui

**Structure:**
```
frontend/src/
├── App.tsx              # Router setup
├── pages/
│   ├── Feed.tsx         # Main feed (own + mates' entries, grouped by venue)
│   ├── Login.tsx        # Login page
│   ├── Register.tsx     # Registration page
│   ├── Mates.tsx        # Follow / mates management
│   └── Profile.tsx      # User profile / stats
├── components/
│   ├── EntryForm.tsx    # Log entry form (fields)
│   ├── BarAutocomplete.tsx # Bar picker backed by GET /bars (debounced search)
│   ├── LogBeerModal.tsx # Modal wrapper around EntryForm
│   ├── EntryCard.tsx    # Single entry display (with Cheers button)
│   ├── VenueCard.tsx    # Venue grouping of entries in the feed
│   └── ProtectedRoute.tsx # Auth guard for routes
├── api/                 # Typed fetch wrappers (one file per resource)
├── hooks/               # Custom React hooks
└── types/               # TypeScript interfaces mirroring backend schemas
```

**Conventions:**
- Use shadcn/ui components — do not introduce other component libraries
- TypeScript strict mode — no `any`, no `// @ts-ignore`
- `src/types/` mirrors backend Pydantic schemas — keep them in sync manually when schemas change
- API calls go through `src/api/` wrappers, never inline `fetch` in components
- State lives in hooks or page-level components — avoid prop drilling more than 2 levels

---

## Python rules

**Linting & formatting:** ruff (replaces black + isort + flake8)
- Line length: 120
- Rules: E, F, I, UP, B (B008 ignored — FastAPI DI pattern)
- Runs on save via VS Code. Run manually: `cd backend && uv run ruff check . && uv run ruff format .`

**General:**
- Python 3.12+ — use modern syntax: `str | None` over `Optional[str]`, `list[str]` over `List[str]`
- **Pydantic collections: use `tuple[Model, ...]` not `list[Model]`** for any field or return type that holds a sequence of Pydantic models — in schemas, service signatures, and endpoint signatures. Internally you may build a `list` and `return tuple(...)` at the end.
- Use `from __future__ import annotations` in schema files for forward refs
- Prefer `pathlib.Path` over `os.path`
- f-strings over `.format()` or `%`
- `datetime.now(UTC).replace(tzinfo=None)` over `datetime.utcnow()` (deprecated in 3.12+) — import `UTC` from `datetime`

### Pandas

- Prefer `pd.read_sql` with SQLAlchemy engine over manual cursor iteration when loading data for analysis
- Use `dtype` hints on `read_sql` / `read_csv` — don't rely on pandas type inference
- Never use `df.iterrows()` — use vectorized operations or `df.to_dict("records")` to build output lists
- Prefer `query()` for readable filtering over boolean indexing chains
- Name DataFrames descriptively (`entries_df`, not `df`) when multiple frames coexist
- Return plain dicts/lists from service functions, not DataFrames — keep pandas internal to analytics layer
- **Column access: always use dotted notation.** Brackets are reserved for column creation or non-plain-string column names:
  ```python
  entries_df["new_col"] = entries_df.a + entries_df.b   # OK — creation
  entries_df[col_name] = entries_df[other_col_name]      # OK — variable name
  assert (entries_df.a == entries_df.b).all()            # OK — dotted read
  assert (entries_df["a"] == entries_df["b"]).all()      # NOT OK — brackets on plain string read
  ```

---

## Deployment (Railway)

Project `confident-ambition`: services **Backend** (root `/backend`, Dockerfile build), **frontend** (root `/frontend`, nixpacks + `vite preview`), **Postgres**. All in `us-west2` — keep API and DB in the same region.

- App: https://frontend-production-5ba2.up.railway.app · API: https://backend-production-43d3.up.railway.app
- **Backend boot lives in `backend/start.sh` (image CMD): migrations, then uvicorn.** Never set `startCommand` in railway.toml with `&&` chains — Railway execs it without a shell, only the first command runs, and the deploy "completes" with no server. This cost us a full day of debugging.
- Frontend env `VITE_API_BASE_URL` is baked at build time — changing it (or the backend domain) requires a frontend redeploy. Backend `ALLOWED_ORIGINS` must list the frontend URL (JSON array).
- Prod bar sync (idempotent): `cd backend && railway run --service Backend -- uv run python scripts/sync_osm_bars.py [--dry-run]`
- `railway up` (CLI deploys) fails with "prefix not found" while service root directories have a leading slash (`/backend`); use push-to-deploy (note: trigger can lag minutes behind the push).

## Environment

```bash
# backend/.env — never commit
DATABASE_URL=postgresql://moussemate:moussemate@127.0.0.1:5433/moussemate
ALLOWED_ORIGINS=["http://localhost:5173"]
DEBUG=true
```

DB is on host port **5433** (not 5432) to avoid conflict with a local Postgres instance.
