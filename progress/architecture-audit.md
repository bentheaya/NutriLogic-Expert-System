# NutriLogic Expert System — Architecture Audit & Production Roadmap

**Author:** Senior engineering onboarding review  
**Date:** 2026-07-22  
**Scope:** Full codebase reverse-engineering (backend, frontend, Prolog KB)  
**Constraint:** Improve toward production-grade quality **without changing product functionality**

> [!NOTE]
> **Remediation & Verification Status (2026-07-22):** All P0, P1, and P2 findings detailed in this audit have been implemented, remediated, and fully verified (50/50 backend tests passing, ESLint clean, Vite build passing). See [remediation-log.md](file:///home/bentheaya/software/NutriLogic-Expert-System/progress/remediation-log.md) for full execution logs.

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Clean Architecture Breakdown](#2-clean-architecture-breakdown)
3. [Complete Data Flow](#3-complete-data-flow)
4. [Critical Problem Areas](#4-critical-problem-areas)
5. [Detailed Findings by Category](#5-detailed-findings-by-category)
6. [Refactoring Strategies](#6-refactoring-strategies)
7. [Production-Grade Improvement Plan](#7-production-grade-improvement-plan)
8. [Priority Matrix](#8-priority-matrix)
9. [Appendix: File Map](#9-appendix-file-map)

---

## 1. Executive Summary

NutriLogic is a **small, hybrid symbolic expert system** (~3.5k lines) for Kenyan nutrition recommendations. It pairs:

| Layer | Technology | Role |
|-------|------------|------|
| Presentation | React 19 + Vite | SPA UI, JWT session, forms |
| Application API | Django 6 + DRF + SimpleJWT | Auth, profile, history, gateway |
| Inference Engine | SWI-Prolog via `pyswip` | Meal rules, deficiency diagnosis |
| Knowledge Base | `prolog/kb.pl` | Foods, micronutrients, suitability rules |
| Persistence | SQLite (default) / optional PostgreSQL | Users, profiles, recommendation logs |

**What works today:** Clear separation between web shell and Prolog core; JWT auth; optional history logging; decent API tests with mocks; culturally relevant KB.

**What blocks production:** Hardcoded secrets and debug defaults, Prolog query injection surface, non-thread-safe inference singleton, personalization data collected but unused, enum/domain knowledge triplicated, no deployment/ops story, SPA routing/auth edge cases, and missing operational concerns (rate limits, logging, health checks, CI).

This is not a “massive” codebase by line count, but it has **concentrated architectural risk** at the Django↔Prolog boundary and a **product/architecture mismatch** (profile metrics and “neuro-symbolic” branding vs pure rule engine + unused fields).

---

## 2. Clean Architecture Breakdown

### 2.1 Logical System Context

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              Client Browser                              │
│  React SPA (Vite)                                                        │
│  ├── Pages (Dashboard, Foods, Recommend, Auth, Profile, History)         │
│  ├── AuthContext (JWT access in memory, refresh in localStorage)         │
│  └── nutrilogicApi.js (fetch wrapper)                                    │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │ HTTP JSON (REST)
                                │ Authorization: Bearer <access>
┌───────────────────────────────▼─────────────────────────────────────────┐
│                         Django REST API                                  │
│  nutrilogic/          (project settings, WSGI/ASGI, root URLs)           │
│  nutrition/                                                              │
│  ├── views.py         thin HTTP handlers                                 │
│  ├── serializers.py   request/response validation                        │
│  ├── models.py        UserProfile, HealthCondition, RecommendationLog    │
│  └── prolog_bridge.py adapter to SWI-Prolog                              │
│  DB: users + profiles + logs                                             │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │ consult + query (pyswip)
┌───────────────────────────────▼─────────────────────────────────────────┐
│                     SWI-Prolog Process (in-process)                      │
│  prolog/kb.pl                                                            │
│  ├── food/7, micronutrient/7 facts                                       │
│  ├── suitable_for/2, avoid_for/2                                         │
│  ├── diagnose_deficiency/2 → condition_for_deficiency/2                  │
│  └── recommend_meal/3, get_recommendation/3                              │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Recommended Layered View (as-is vs target)

| Layer | As-is | Target (no behavior change) |
|-------|--------|------------------------------|
| **UI** | React pages + components, state-based “router” | Same UX; add React Router + shared constants |
| **API / Controllers** | Function-based DRF views | Keep FBV or migrate to thin ViewSets; no business logic in views |
| **Application services** | **Missing** — views call bridge + ORM directly | `RecommendationService`, `ProfileService`, `FoodQueryService` |
| **Domain** | Scattered enums (FE, serializers, Prolog atoms) | Shared domain constants + validation catalog (Python source of truth for API) |
| **Inference port** | `prolog_bridge.py` (concrete) | Interface/protocol + `PrologInferenceAdapter` |
| **Persistence** | Django ORM models | Same models; add indexes, constraints, managers |
| **Infrastructure** | settings monolith, no Docker | env-based settings modules, container entrypoints, health |

### 2.3 Module Responsibilities (current)

#### Backend (`backend/`)

| Module | Responsibility | Coupling |
|--------|----------------|----------|
| `nutrilogic/settings.py` | Config, DB, CORS, JWT, DRF | Env + optional `dj_database_url` (not in requirements) |
| `nutrition/views.py` | All HTTP endpoints | Directly imports bridge + models |
| `nutrition/serializers.py` | Auth, profile, recommend payloads | Hardcodes condition/symptom vocab |
| `nutrition/models.py` | Profile, conditions, logs | Conditions never written via API |
| `nutrition/prolog_bridge.py` | Load KB once; run queries; map terms → dicts | Global singleton + f-string queries |
| `nutrition/tests.py` | Bridge (real Prolog) + API (mocked bridge) | Solid coverage for size |
| `prolog/kb.pl` | Facts + inference rules | Dual source of truth for domain terms |

#### Frontend (`frontend/src/`)

| Module | Responsibility |
|--------|----------------|
| `App.jsx` | Manual page switch (`useState`), auth gates |
| `context/AuthContext.jsx` | Login/logout, token refresh on mount |
| `api/nutrilogicApi.js` | All REST calls |
| `components/RecommendationForm.jsx` | Condition/symptom UI + results |
| `components/FoodList.jsx` | Load and table-render foods |
| `pages/*` | Thin page shells + auth forms |

### 2.4 Data Model (persistence)

```
User (Django auth)
  └── 1:1 UserProfile
        ├── age, weight_kg, height_cm, activity_level, county
        ├── 1:N HealthCondition (condition string)
        └── 1:N RecommendationLog
              ├── symptoms (JSON list)
              ├── condition (string)
              ├── recommendations (JSON list of meals)
              └── created_at
```

**Important:** Inference does **not** read `UserProfile` or `HealthCondition`. Personalization is effectively “condition or symptoms in the request body,” not user state.

### 2.5 Knowledge Model (Prolog)

| Predicate | Purpose |
|-----------|---------|
| `food/7` | Macro nutrients per 100g |
| `micronutrient/7` | Micro profile (subset of foods) |
| `suitable_for/2` | Food ↔ condition suitability |
| `avoid_for/2` | Hard exclusions (e.g. high-GI staples for T2D) |
| `diagnose_deficiency/2` | Symptom list → deficiency atom |
| `condition_for_deficiency/2` | Deficiency → recommendable condition |
| `recommend_meal/3` | Cartesian meal assembly + explanation string |
| `get_recommendation/3` | Diagnose then recommend (cut/fallback to healthy) |
| `recommend_bodybuilding_meal/3` | **Defined but not exposed via API** |
| `high_protein_food/1`, `muscle_building_food/1` | Supporting rules for bodybuilding path |

### 2.6 API Surface

| Method | Path | Auth | Side effects |
|--------|------|------|--------------|
| GET | `/api/foods/` | Public | None |
| GET | `/api/foods/<group>/` | Public | None |
| GET | `/api/foods/<food_name>/micronutrients/` | Public | None |
| POST | `/api/recommend/condition/` | Optional JWT | Log if authenticated |
| POST | `/api/recommend/symptoms/` | Optional JWT | Log if authenticated |
| POST | `/api/auth/register/` | Public | Creates User + Profile |
| POST | `/api/auth/token/` | Public | JWT pair |
| POST | `/api/auth/token/refresh/` | Public | New access (rotate refresh) |
| GET/PATCH | `/api/profile/` | Required | Update profile fields |
| GET | `/api/history/` | Required | Last 20 logs |

---

## 3. Complete Data Flow

### 3.1 Recommendation by Condition

```
User selects condition in RecommendationForm
        │
        ▼
recommendByCondition(condition, accessToken)
        │  POST /api/recommend/condition/  { condition }
        │  + Bearer token if logged in
        ▼
RecommendByConditionSerializer validates against CONDITION_CHOICES
        │
        ▼
prolog_bridge.recommend_meal(condition)
        │  builds: recommend_meal({condition}, Meal, Explanation)
        │  iterates solutions, caps at 5
        ▼
SWI-Prolog:
  for each staple in grains|tubers|legumes_grains suitable & not avoided
  for each protein in legumes|fish|meat|protein|nuts suitable
  for each vegetable suitable
  → meal(Staple, Protein, Vegetable) + explanation string
        │
        ▼
If request.user.is_authenticated:
  get_or_create UserProfile → RecommendationLog.create(...)
        │
        ▼
JSON { condition, recommendations: [{staple, protein, vegetable, explanation}] }
        │
        ▼
UI renders meal cards
```

### 3.2 Recommendation by Symptoms

```
User checks symptoms → POST { symptoms: [...] }
        │
        ▼
RecommendBySymptomsSerializer (VALID_SYMPTOMS)
        │
        ▼
prolog_bridge.get_recommendation(symptoms)
        │  get_recommendation([s1,s2,...], Meal, Explanation)
        ▼
Prolog:
  diagnose_deficiency → condition_for_deficiency → recommend_meal
  OR fallback recommend_meal(healthy, ...)  [cut]
        │
        ▼
Same logging + response path as condition flow
```

### 3.3 Food Catalog

```
FoodList mount → GET /api/foods/
  → prolog_bridge.get_foods()
  → food(Name, Group, Cal, Prot, Carbs, Fat, Fibre) for all facts
  → table render
```

Micronutrients and group filters follow the same pattern with path parameters passed into Prolog query strings.

### 3.4 Auth Session

```
Register → User + empty UserProfile
Login → TokenObtainPairView → { access, refresh }
AuthContext.login:
  localStorage[nutrilogic_refresh] = refresh
  memory accessToken = access
  user = decode JWT payload .username   ← see bug below
On reload:
  refreshAccessToken(stored refresh) → set access + user
Protected pages: App.jsx switches to Login if !user
```

### 3.5 Profile & History

```
GET/PATCH /api/profile/  → UserProfileSerializer (conditions nested read-only)
GET /api/history/        → last 20 RecommendationLog by -created_at
```

Profile fields **never re-enter** the recommendation pipeline.

---

## 4. Critical Problem Areas

These are the issues that most endanger correctness, security, or production readiness.

### P0 — Security & Correctness

| ID | Issue | Why it matters |
|----|--------|----------------|
| **C1** | **Default `SECRET_KEY` and `DEBUG=True`** in `settings.py` | Deploying without env vars ships insecure defaults |
| **C2** | **Prolog queries built with f-strings** (`group`, `food_name`, `condition`, symptoms list) | Even with DRF choice validation on some paths, path params for foods are unsanitized → injection / query malformation risk |
| **C3** | **JWT payload misread**: `payload.username` is not a default SimpleJWT claim | Navbar/Profile show `undefined` username; auth “user” object is unreliable |
| **C4** | **Global Prolog singleton without query locking** | `pyswip`/SWI-Prolog is generally **not thread-safe**; concurrent requests can corrupt engine state |
| **C5** | **`ROTATE_REFRESH_TOKENS=True` but `BLACKLIST_AFTER_ROTATION=False`** | Old refresh tokens remain valid after rotation → session fixation / multi-token risk |
| **C6** | **`DEFAULT_PERMISSION_CLASSES = AllowAny`** | Easy to add new endpoints that accidentally stay public |

### P1 — Architecture / Product Integrity

| ID | Issue | Why it matters |
|----|--------|----------------|
| **C7** | **Profile & HealthCondition unused by inference** | “Personalised” recommendations are not personalised; dead schema surface |
| **C8** | **Domain vocabulary triplicated** (FE lists, DRF serializers, Prolog atoms) | Drift causes silent empty results or FE/BE validation mismatch |
| **C9** | **No application/service layer** | Views own orchestration, logging, and bridge calls → hard to test and reuse |
| **C10** | **Bodybuilding KB orphaned** | Dead rules inflate maintenance and confuse “supported conditions” |
| **C11** | **Static knowledge only in Prolog** | Cannot query foods with SQL, admin-edit, or cache efficiently without consulting engine |

### P2 — Scalability & Ops

| ID | Issue | Why it matters |
|----|--------|----------------|
| **C12** | **Meal rule is O(staples × proteins × vegetables)** | KB growth makes inference expensive; Python only *stops reading* after 5 solutions (engine may still work hard depending on strategy) |
| **C13** | **No caching** of immutable food catalog | Every page load hits Prolog |
| **C14** | **No health/readiness, metrics, structured logging** | Cannot operate in k8s/cloud |
| **C15** | **`dj-database-url` used but not in `requirements.txt`** | `DATABASE_URL` path crashes at import time |
| **C16** | **No Docker/CI/deploy config, minimal README** | Non-reproducible environments |

### P3 — Maintainability / UX Platform

| ID | Issue | Why it matters |
|----|--------|----------------|
| **C17** | **State-based routing** (no React Router) | No deep links, broken browser history/share URLs |
| **C18** | **Duplicated API base URL + refresh fetch** in AuthContext vs nutrilogicApi | Two clients to keep in sync |
| **C19** | **No API versioning, pagination contracts, or OpenAPI** | Hard for multi-client evolution |
| **C20** | **HealthCondition has no write API**; conditions display-only | Incomplete feature surface |

---

## 5. Detailed Findings by Category

### 5.1 Bad Architecture Decisions

1. **Inference as a synchronous in-process library call inside the web worker**  
   Couples HTTP latency and process stability to SWI-Prolog native state. Multi-worker deploys multiply KB loads; multi-thread workers race the engine.

2. **Treating the knowledge base as the primary data store for foods**  
   Fine for a prototype expert system; poor for production APIs that need filtering, admin CRUD, pagination, and caching. Prefer: DB (or JSON fixtures) as system of record, Prolog as rule engine over asserted facts—or compile KB from DB at startup.

3. **Optional auth with side-effect logging inside the same endpoint**  
   Makes caching, rate limiting, and “anonymous vs user” contracts fuzzy. Prefer explicit “save to history” or always-auth for logged features—but **without changing behavior**, document and isolate the side effect in a service.

4. **Manual SPA navigation instead of a router**  
   Acceptable for a demo; not production UX.

5. **“Neuro-Symbolic” product framing without a neural component**  
   Architectural honesty issue: system is **symbolic-only**. Either rename messaging or plan a future ML scorer; do not imply dual engines exist.

6. **Collecting anthropometrics that never affect recommendations**  
   Creates false expectations and privacy surface (health data) without benefit.

### 5.2 Duplicate Logic

| Duplication | Locations | Risk |
|-------------|-----------|------|
| Condition enum | `RecommendationForm.jsx`, `RecommendByConditionSerializer`, Prolog `suitable_for` | Drift |
| Symptom enum | `RecommendationForm.jsx`, `RecommendBySymptomsSerializer`, Prolog `diagnose_deficiency` | Drift |
| Activity levels | `UserProfile.ACTIVITY_CHOICES`, `ProfilePage.jsx` | Drift |
| Password match check | Register page + `UserRegistrationSerializer` | Mild |
| Token refresh HTTP | `AuthContext.refreshAccessToken` vs `nutrilogicApi.refreshToken` | Divergence |
| BASE_URL | AuthContext + nutrilogicApi | Config drift |
| Recommendation logging | `recommend_by_condition` / `recommend_by_symptoms` nearly identical | Copy-paste bugs |
| Meal card rendering | `RecommendationForm.jsx` + `HistoryPage.jsx` | UI inconsistency |
| get_or_create profile | register, recommend×2, profile view | Inconsistent profile guarantees |

### 5.3 Performance Bottlenecks

1. **Full KB scan on every `/api/foods/`** via Prolog query — no cache, no ETag.
2. **Unconstrained meal search** before Python-side limit of 5.
3. **Micronutrient lookup** reopens query path per request with string interpolation.
4. **No DB indexes** on `RecommendationLog(profile, created_at)` (history path).
5. **SQLite default** under concurrent writes (recommendation logs) will lock.
6. **JWT decode on every render path is cheap**; real cost is cold `pyswip` import + `consult` per process (acceptable if once, painful if process churn).

### 5.4 Scalability Risks

| Risk | Detail |
|------|--------|
| Thread safety | Shared `_prolog` without per-query lock |
| Horizontal scale | Each worker loads full SWI-Prolog; memory multiplies |
| KB size | Combinatorial meal generation |
| State in process | Cannot share Prolog engine across pods without redesign |
| Auth token storage | Refresh in `localStorage` XSS-sensitive at scale of attack surface |
| History growth | Unbounded `RecommendationLog` table, only UI shows last 20 |
| CORS hardcoding | Must be reworked for real domains (config-only; no func change) |

### 5.5 Maintainability Issues

- Single flat `views.py` / one app for everything (OK at this size; will rot if features grow).
- No typed frontend; JSDoc only.
- README is one sentence — no runbook, env vars, Prolog install, or architecture.
- Leftover noise (`// testing` in Dashboard).
- Tests good for API, but no frontend tests; Prolog tests skip if SWI missing (CI must install SWI or gate explicitly).
- Incomplete dependency declaration (`psycopg2-binary` present, `dj-database-url` missing).
- Settings not split into `base` / `local` / `production`.
- Explanation strings built in Prolog with `atomic_list_concat` — hard to i18n or template.

---

## 6. Refactoring Strategies

Guiding rule: **preserve external API contracts and response shapes** unless versioning is introduced later.

### 6.1 Strategy A — Introduce a Service Layer (low risk, high clarity)

```
views.py  →  services/recommendations.py  →  ports/inference.py  →  adapters/prolog_bridge.py
          →  services/foods.py
          →  services/profiles.py
```

**Steps:**
1. Extract `log_recommendation(user, *, condition, symptoms, recommendations)` helper.
2. Move recommend orchestration out of views into `RecommendationService`.
3. Keep serializers and URLs unchanged.
4. Unit-test services with a fake inference adapter.

**Benefit:** Views become pure HTTP; Prolog becomes swappable; logging tested once.

### 6.2 Strategy B — Harden the Prolog Boundary (security + reliability)

1. **Whitelist all atoms** before query construction (groups, food names from a cached set).
2. Prefer `prolog.query` with bound variables if pyswip API allows, or escape via a strict atom regex `^[a-z][a-z0-9_]*$`.
3. Add a **threading.Lock** around every `prolog.query` (functionality identical, concurrency-safe).
4. Optional later: run SWI-Prolog as a **side process** (stdin/stdout or HTTP) so web workers stay pure Python — bigger change, same API.

### 6.3 Strategy C — Single Source of Truth for Domain Vocab (no behavior change)

1. Define Python constants: `CONDITIONS`, `SYMPTOMS`, `FOOD_GROUPS`, `ACTIVITY_LEVELS`.
2. Serializers import them; add a small public endpoint `GET /api/meta/vocabulary/` **only if** needed for FE—or generate a FE constants file in build.
3. Document that Prolog atoms **must** match these constants; add a test that loads KB and asserts every `suitable_for` condition is in the allowed set.

### 6.4 Strategy D — Cache Immutable Reads

1. `@lru_cache` or Django cache framework for `get_foods()` results (invalidate on process restart / version stamp).
2. Add `Cache-Control` headers for public food endpoints.
3. History remains uncached (user-specific).

### 6.5 Strategy E — Settings & Deploy Hygiene

1. Fail fast if `SECRET_KEY` missing when `DEBUG=False`.
2. Split settings; require `ALLOWED_HOSTS`, CORS origins from env.
3. Pin `dj-database-url` or remove the code path.
4. Add `Dockerfile` + `docker-compose` (web, db, optional prolog deps) without changing app logic.
5. Add `/api/health/` (DB ping + Prolog consult check).

### 6.6 Strategy F — Frontend Structural Cleanup

1. Adopt React Router with same pages (URLs map 1:1 to current page keys).
2. Single API client; AuthContext uses `refreshToken()` from `nutrilogicApi`.
3. Fix user display: either customize SimpleJWT claims to include `username`, or fetch `/api/profile/` after login (prefer profile fetch — already exists).
4. Extract shared `MealCard` component.
5. Shared constants module for conditions/symptoms (mirroring backend).

### 6.7 Strategy G — Data Model Hygiene (behavior-preserving)

1. Index `RecommendationLog(profile_id, -created_at)`.
2. Keep unused profile fields (functionality preserved) but document as “reserved for future personalization.”
3. Do **not** delete HealthCondition or bodybuilding rules without product decision; mark as unused in docs / tests that lock current API.

### 6.8 Strategy H — Inference Performance Without Changing Results

1. In Prolog, add `limit(5, recommend_meal(...))` or use `findall` + length cut **if** result ordering is stable and matches current “first 5 from engine” semantics — **verify with golden tests** before adopting.
2. Precompute suitability indexes as dynamic facts at consult time.
3. Ensure avoid rules and member checks are ordered for early fail.

> Any Prolog change must be guarded by snapshot tests of current meal sets for each condition/symptom fixture.

---

## 7. Production-Grade Improvement Plan

### Phase 0 — Safety Net (1–2 days)

- [ ] Export golden JSON fixtures for each condition + key symptom sets (current responses).
- [ ] Run full test suite in CI with SWI-Prolog installed.
- [ ] Add frontend lint in CI; document `VITE_API_URL`.
- [ ] Remove dead comments; expand README with architecture + env vars.

### Phase 1 — Production Security Baseline (no feature change)

- [ ] Require env-based `SECRET_KEY`; default `DEBUG=False` in production settings module.
- [ ] Harden CORS, `ALLOWED_HOSTS`, secure cookie flags if session auth remains.
- [ ] Atom validation / parameterized Prolog access.
- [ ] Fix JWT username display (custom claim **or** profile bootstrap).
- [ ] Enable token blacklist app if rotating refresh tokens, **or** disable rotation to match current capability.
- [ ] Rate-limit auth + recommend endpoints (e.g. DRF throttling).
- [ ] Add password validators already configured are fine; ensure registration uses them (call `validate_password`).

### Phase 2 — Structural Refactors

- [ ] Service layer + inference port.
- [ ] Query lock / process isolation for Prolog.
- [ ] Domain constants + drift tests against `kb.pl`.
- [ ] Deduplicate FE meal rendering + API client.
- [ ] React Router for deep links (same screens).

### Phase 3 — Performance & Scale Readiness

- [ ] Cache food list & micronutrients.
- [ ] DB indexes; PostgreSQL in compose for non-dev.
- [ ] Gunicorn/uvicorn deployment with known worker model (prefer **sync workers + process isolation** over multi-thread until Prolog is isolated).
- [ ] Structured logging (request id, latency, prolog query time).
- [ ] Health/readiness endpoints; basic metrics (Prometheus optional).

### Phase 4 — Ops & Quality Bar

- [ ] Docker images, non-root user, multi-stage frontend build served by nginx or WhiteNoise.
- [ ] OpenAPI schema (`drf-spectacular`) matching existing routes.
- [ ] Dependency pinning / lockfile for Python (`pip-tools` or `uv`).
- [ ] Backup strategy for PostgreSQL; retention policy for `RecommendationLog`.
- [ ] Privacy review: health-adjacent data in logs JSON; retention & access control.

### Explicitly Out of Scope for “No Functionality Change”

- Wiring profile age/BMI/activity into recommendations  
- Exposing bodybuilding endpoints  
- CRUD for HealthCondition  
- Adding neural/ML ranking  
- Changing meal selection algorithm or explanation text  

These are **product enhancements**, not production hardening.

---

## 8. Priority Matrix

| Priority | Item | Effort | Impact |
|----------|------|--------|--------|
| **P0** | Env secrets / production settings | S | Critical |
| **P0** | Prolog input sanitization + query lock | M | Critical |
| **P0** | Fix JWT user identity display | S | High (correctness) |
| **P0** | Refresh token rotation + blacklist consistency | S | High |
| **P1** | Service layer extraction | M | High maintainability |
| **P1** | Domain constant SSOT + KB drift tests | M | High |
| **P1** | Cache foods; DB indexes | S | Medium perf |
| **P1** | Add missing deps; health endpoint | S | Ops |
| **P2** | React Router + API client cleanup | M | Maintainability/UX platform |
| **P2** | Docker/CI/logging/throttling | M | Production ops |
| **P2** | OpenAPI + README runbook | S | Onboarding |
| **P3** | Prolog process isolation | L | Scale |
| **P3** | KB/DB dual-write design | L | Long-term architecture |

---

## 9. Appendix: File Map

```
NutriLogic-Expert-System/
├── README.md                          # Minimal project blurb
├── LICENSE
├── prolog/
│   └── kb.pl                          # Facts + inference rules (~292 LOC)
├── backend/
│   ├── manage.py
│   ├── requirements.txt               # Django, DRF, JWT, cors, pyswip, psycopg2
│   ├── nutrilogic/
│   │   ├── settings.py                # Config monolith
│   │   ├── urls.py                    # admin + api/
│   │   ├── wsgi.py / asgi.py
│   └── nutrition/
│       ├── models.py                  # Profile, HealthCondition, RecommendationLog
│       ├── views.py                   # All endpoints
│       ├── serializers.py
│       ├── prolog_bridge.py           # pyswip adapter
│       ├── urls.py
│       ├── admin.py
│       ├── tests.py                   # Main automated safety net
│       └── migrations/0001_initial.py
├── frontend/
│   ├── package.json                   # React 19, Vite 7 (no router)
│   ├── vite.config.js                 # Dev proxy /api → :8000
│   └── src/
│       ├── App.jsx                    # Manual page state
│       ├── api/nutrilogicApi.js
│       ├── context/AuthContext.jsx
│       ├── components/{Navbar,FoodList,RecommendationForm}.jsx
│       └── pages/{Dashboard,Foods,Recommend,Login,Register,Profile,History}.jsx
└── progress/
    └── architecture-audit.md          # This document
```

### LOC Snapshot (approx.)

| Area | LOC |
|------|-----|
| Prolog KB | ~290 |
| Backend Python | ~1,100 (excl. large tests) |
| Backend tests | ~480 |
| Frontend JS/JSX | ~900 |
| CSS | ~550 |
| **Total** | **~3,450** |

---

## Closing Assessment

NutriLogic is a **coherent academic/prototype expert system** with a clean conceptual split (React shell → Django gateway → Prolog reasoner). The main production gap is not missing features—it is **operational maturity and boundary hardening**:

1. Treat SWI-Prolog as an **untrusted-native, non-thread-safe subsystem** and wrap it accordingly.  
2. Stop scattering domain vocabulary across three layers.  
3. Make configuration fail-closed for production.  
4. Extract services so the HTTP layer cannot grow into a god-module.  
5. Keep product promises honest: either use profile data later, or document that recommendations are condition/symptom-driven only.

Executing Phases 0–3 above yields production-grade quality **without changing recommendation behavior or public API contracts**.

---

*End of audit.*
