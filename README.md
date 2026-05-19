# MousseMate 🍺

**Strava for beer.** Log your beer check-ins, track your drinking habits, and discover trends — breweries, styles, locations, and streaks.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI + SQLAlchemy + Alembic |
| Database | PostgreSQL 16 |
| Frontend | React 18 + Vite + Tailwind CSS |
| Package manager (backend) | uv |
| Containerization | Docker Compose |

---

## Local Development Setup

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- [uv](https://docs.astral.sh/uv/) installed (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- Node.js ≥ 18 + npm

---

### 1. Clone and configure environment

```bash
git clone https://github.com/your-org/moussemate.git
cd moussemate
cp .env.example backend/.env
```

Edit `backend/.env` if needed (defaults work for local Docker setup).

---

### 2. Start the database

```bash
docker compose up db -d
```

---

### 3. Run database migrations

```bash
cd backend
uv sync
uv run alembic upgrade head
cd ..
```

---

### 4. Start the API

```bash
# Option A — with Docker Compose (recommended)
docker compose up api

# Option B — directly with uv
cd backend
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

API is available at: http://localhost:8000  
Interactive docs: http://localhost:8000/docs

---

### 5. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend is available at: http://localhost:5173

---

### Daily startup (after first-time setup)

```bash
docker compose up db -d                                              # terminal 1
cd backend && uv run uvicorn app.main:app --reload --port 8000      # terminal 2
cd frontend && npm run dev                                           # terminal 3
```

`uv sync` and `npm install` are only needed again if dependencies changed.

---

## Project Structure

```
moussemate/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/   # Route handlers
│   │   ├── core/               # Config / settings
│   │   ├── db/                 # SQLAlchemy engine & session
│   │   ├── models/             # ORM models
│   │   ├── schemas/            # Pydantic schemas
│   │   └── services/           # Business logic
│   ├── alembic/                # DB migrations
│   └── pyproject.toml
├── frontend/
│   └── src/
│       ├── api/                # Typed API wrappers
│       ├── pages/              # Route-level components
│       ├── hooks/              # Custom React hooks
│       ├── components/         # Reusable UI components
│       └── types/              # TypeScript interfaces
├── docker-compose.yml
└── .env.example
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /health | Health check |
| POST | /api/v1/checkins | Log a new check-in |
| GET | /api/v1/checkins | List check-ins |
| GET | /api/v1/checkins/stats/summary | Get stats summary |
| GET | /api/v1/checkins/{id} | Get one check-in |
| PATCH | /api/v1/checkins/{id} | Update a check-in |
| DELETE | /api/v1/checkins/{id} | Delete a check-in |
