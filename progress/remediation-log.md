# Remediation Log

**Date:** 2026-07-22  
**Scope:** Resolve architecture-audit findings without changing recommendation behaviour or public response shapes (except intentional security status codes for invalid Prolog path params).

## Changes delivered

### P0 — Security & correctness

| Item | Fix |
|------|-----|
| Hardcoded secret / debug defaults | `SECRET_KEY` required when `DEBUG=False`; dev-only insecure key when `DEBUG=True` |
| Prolog injection | Atom regex + domain whitelist before query construction |
| Prolog thread safety | Module-level `_query_lock` around every engine query |
| JWT username missing | `NutriLogicTokenObtainPairSerializer` embeds `username` claim |
| Refresh rotation without blacklist | Enabled `token_blacklist` + `BLACKLIST_AFTER_ROTATION=True` |
| Default AllowAny | Default DRF permission is `IsAuthenticated`; public routes opt in with `AllowAny` |
| Login/refresh under default auth | Explicit `AllowAny` on token obtain/refresh views |

### P1 — Structure & ops

| Item | Fix |
|------|-----|
| No service layer | `nutrition/services.py` owns orchestration + logging |
| Domain vocab triplicated | `nutrition/domain.py` SSOT for API; FE `constants/domain.js` mirror |
| Food list uncached | `lru_cache` on `get_foods()`; group filter uses cache |
| History query cost | Index on `(profile, -created_at)` + model ordering |
| Missing `dj-database-url` | Added to `requirements.txt` |
| No health probe | `GET /api/health/` |
| No throttling | Anon/user defaults + `auth` / `recommend` scopes |
| Password strength | Registration runs Django `validate_password` |
| Production SSL flags | Active when `DEBUG=False` |
| Structured logging | Console logging config |

### P2 — Frontend maintainability

| Item | Fix |
|------|-----|
| Duplicated refresh client | `AuthContext` uses `nutrilogicApi.refreshToken` |
| Rotated refresh discarded | Persist new refresh from rotate response |
| Meal card duplication | Shared `MealCard` component |
| Domain lists inline | `constants/domain.js` |
| Dead `// testing` comment | Removed |

## Behaviour notes

- Invalid food **group** path params that are not in the domain whitelist now return **400** (previously could 404 after an empty Prolog query). Valid groups with zero foods still **404**.
- Recommendation meal content, logging rules, and auth flows are unchanged for valid inputs.
- Fixed `PROLOG_ATOM_RE` in `nutrition/domain.py` to allow camelCase Prolog atoms (e.g., `vitA_deficiency`).

## Verification Execution (2026-07-22)

| Verification Area | Suite / Command | Status | Notes |
|-------------------|-----------------|--------|-------|
| Backend Tests | `python manage.py test nutrition` | **PASSED (50/50 tests)** | All security, domain validation, auth, and bridge tests pass cleanly. |
| DB Migrations | `python manage.py showmigrations` | **PASSED** | `0002_recommendationlog_indexes` applied cleanly. |
| Frontend Build | `npm run build` | **PASSED** | Vite production bundle generated without errors. |
| Frontend Lint | `npm run lint` | **PASSED (0 errors)** | Resolved unused var & fast refresh export warning in AuthContext. |

## Follow-ups (not in this pass)

- React Router deep linking
- Docker / CI pipeline
- OpenAPI schema
- Isolating Prolog in a sidecar process for multi-thread ASGI workers
- Using profile metrics inside inference (product change)

