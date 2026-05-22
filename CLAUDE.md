# MousseMate — Claude Code Guide

> Operational guide for AI-assisted development. For architecture, decisions, and roadmap see [ARCHITECTURE.md](ARCHITECTURE.md).

---

## Current phase: V1

We are in **V1 — Core Loop**. Do not build toward V2 (geo) or V3 (auth, social) unless explicitly asked. No multi-user, no JWT, no PostGIS.

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
├── core/config.py       # Pydantic settings (reads .env)
├── db/session.py        # Engine, SessionLocal, Base, get_db()
├── models/entry.py      # SQLAlchemy ORM model
├── schemas/entry.py     # Pydantic schemas (EntryCreate, EntryUpdate, EntryRead, StatsSummary)
├── services/entry.py    # CRUD logic
├── services/analytics.py# Stats logic
└── api/
    ├── router.py        # Aggregates all endpoint routers
    └── entry.py         # Entry endpoints
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
| name | string(255) | Optional (beer name) |
| type | string(100) | Required (style: IPA, Stout…) |
| volume | float | Required (mL) |
| drink_datetime | datetime | Required |
| bar | text | Optional (venue name) |
| rating | float | Optional, 0.0–5.0 |
| notes | text | Optional |
| created_at | datetime | Server default |
| updated_at | datetime | Auto on update |

Geo fields (`latitude`, `longitude`, `city`) and `user_id` are **V2/V3** — not in schema yet.

---

## Frontend

**Stack:** React 18 · Vite · TypeScript · Tailwind CSS · shadcn/ui

**Structure:**
```
frontend/src/
├── App.tsx              # Router setup
├── pages/
│   ├── Beers.tsx        # My Beers list page
│   └── Stats.tsx        # Dashboard / stats
├── components/
│   ├── EntryForm.tsx    # Log entry form (fields)
│   └── LogBeerModal.tsx # Modal wrapper around EntryForm
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

## Environment

```bash
# backend/.env — never commit
DATABASE_URL=postgresql://moussemate:moussemate@127.0.0.1:5433/moussemate
ALLOWED_ORIGINS=["http://localhost:5173"]
DEBUG=true
```

DB is on host port **5433** (not 5432) to avoid conflict with a local Postgres instance.
