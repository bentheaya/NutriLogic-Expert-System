# NutriLogic Expert System

A **symbolic expert system** for personalised nutrition recommendations in Kenya. It combines SWI-Prolog inference (MOH 2025 Kenya Nutrient Profile Model rules) with a Django REST API and React UI.

> Recommendations are driven by the **condition or symptoms** you submit. Profile fields (age, weight, county, etc.) are stored for the account but are **not** yet used by the inference engine.

## Architecture

```
React (Vite)  →  Django REST + JWT  →  pyswip  →  SWI-Prolog (prolog/kb.pl)
                      ↓
                 SQLite / PostgreSQL  (users, profiles, recommendation history)
```

| Layer | Path | Role |
|-------|------|------|
| Frontend | `frontend/` | SPA dashboard |
| API | `backend/` | Auth, profile, history, gateway |
| Domain constants | `backend/nutrition/domain.py` | Shared vocab for validation |
| Services | `backend/nutrition/services.py` | Application orchestration |
| Bridge | `backend/nutrition/prolog_bridge.py` | Thread-safe Prolog adapter |
| Knowledge base | `prolog/kb.pl` | Facts + rules |

## Prerequisites

- Python 3.12+
- Node.js 20+
- [SWI-Prolog](https://www.swi-prolog.org/) (for live inference; API tests mock it)

```bash
# Debian/Ubuntu
sudo apt-get install swi-prolog
```

## Backend setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Optional: copy and edit env
cp .env.example .env

export DJANGO_DEBUG=True   # default; allows dev SECRET_KEY fallback
python manage.py migrate
python manage.py runserver
```

API base: `http://localhost:8000/api/`

### Important environment variables

| Variable | Notes |
|----------|--------|
| `DJANGO_SECRET_KEY` | **Required** when `DJANGO_DEBUG=False` |
| `DJANGO_DEBUG` | Default `True` for local dev |
| `DJANGO_ALLOWED_HOSTS` | Space-separated hosts |
| `DJANGO_CORS_ORIGINS` | Comma-separated browser origins |
| `DATABASE_URL` | Optional; enables PostgreSQL via `dj-database-url` |

## Frontend setup

```bash
cd frontend
npm install
# optional: export VITE_API_URL=http://localhost:8000/api
npm run dev
```

Dev server: `http://localhost:5173` (proxies `/api` → Django).

## Docker Compose Setup

Run the full stack (PostgreSQL + Django API with SWI-Prolog + React Frontend Nginx) with Docker Compose:

```bash
docker-compose up --build
```

- Frontend SPA: `http://localhost:80`
- Backend API: `http://localhost:8000/api/`
- Health Probe: `http://localhost:8000/api/health/`


## Key API routes

| Method | Path | Auth |
|--------|------|------|
| GET | `/api/health/` | Public |
| GET | `/api/foods/` | Public |
| POST | `/api/recommend/condition/` | Optional JWT (logs history) |
| POST | `/api/recommend/symptoms/` | Optional JWT (logs history) |
| POST | `/api/auth/register/` | Public |
| POST | `/api/auth/token/` | Public |
| POST | `/api/auth/token/refresh/` | Public |
| GET/PATCH | `/api/profile/` | Required |
| GET | `/api/history/` | Required |

## Tests

```bash
cd backend
source .venv/bin/activate
python manage.py test nutrition
```

Prolog integration tests skip automatically if SWI-Prolog / pyswip is unavailable.

## Production checklist

1. Set `DJANGO_DEBUG=False` and a strong `DJANGO_SECRET_KEY`
2. Configure `DJANGO_ALLOWED_HOSTS` and `DJANGO_CORS_ORIGINS`
3. Use PostgreSQL (`DATABASE_URL` or `DB_*`)
4. Run behind HTTPS (`DJANGO_SECURE_SSL_REDIRECT=True` by default when not debugging)
5. Prefer **one process / sync worker model** per Prolog engine (engine is process-local and query-locked)
6. Probe readiness via `GET /api/health/`

## Project docs

- Architecture audit: [`progress/architecture-audit.md`](progress/architecture-audit.md)
- Remediation log: [`progress/remediation-log.md`](progress/remediation-log.md)

## License

See [LICENSE](LICENSE).
