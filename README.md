# Socratic Learning Companion — Backend (MVP / Phase 1)

FastAPI + PostgreSQL + Redis implementation of the P0 core loop from the PRD:
**Diagnostic Agent → Socratic Coach → Hint Ladder → Answer-Leak Guard → basic
Mastery check**, wrapped by a deterministic Orchestrator (not an LLM call) that
owns the Learner State Machine and Mode Selector, exactly as specified in
Section 11.5 of the PRD ("behavior is testable and not subject to LLM drift").

## What's implemented vs. what's stubbed

| PRD Section | Status |
|---|---|
| 8 — Learner State Machine | ✅ implemented in `app/state_machine.py` |
| 9 — Tutor Modes / Mode Selector | ✅ `app/mode_selector.py` + prompts in `app/agents/socratic_agent.py` |
| 10 — Hint Escalation Ladder | ✅ `app/hint_ladder.py` |
| 11.1 — Diagnostic Agent | ✅ `app/agents/diagnostic_agent.py` |
| 11.2 — Socratic Questioning Agent | ✅ `app/agents/socratic_agent.py` |
| 11.3 — Misconception Detection Agent | ✅ `app/agents/misconception_agent.py` |
| 11.4 — Mastery Assessment Agent | ✅ `app/agents/mastery_agent.py` (Section 14 rubric + weights) |
| 11.5 — Orchestrator | ✅ `app/orchestrator.py` |
| 11.6 — Answer-Leak Guard | ✅ `app/agents/answer_leak_guard.py` (rule-based + LLM classifier, 1 retry, template fallback) |
| 12 — Memory Architecture | ✅ Working/session memory in Redis, concept/profile memory in Postgres |
| 14 — Mastery Engine | ✅ weighted rubric, FR-04 gate (no MASTERED without transfer-task evidence) |
| 18 — DB Schema | ✅ all tables from Section 18 |
| 19 — APIs | ✅ core endpoints implemented (see below); rate limiting is **not** enforced in-app — see "Manual steps" |
| 21 NFR — Streaming | ✅ WebSocket streaming endpoint (`app/routers/ws_router.py`) in addition to the simple REST endpoint |
| Concept Graph as real vector DB (pgvector) | ⚠️ **Stubbed.** `memory_facts` table exists but retrieval is plain keyword lookup, not vector similarity. See "Stretch goals" below. |
| Voice (P2), Mentor real-time dashboard UI, retention scheduler cron | ⚠️ **Not built** — out of MVP/P0 scope per the PRD's own roadmap (Section 23, Phase 1). Data model support exists (`retention_due_at` field) but no scheduled job runs yet. |
| LMS integration, gamification | ❌ Explicitly "Won't Have" per PRD Section 6 |

## Why "no GPT-5.5"

The PRD assumes "existing LLM APIs only" on a limited budget (Section 2.1,
Constraint table in Section 4). Rather than hardcoding a specific paid
model, `app/llm_client.py` is a **model-agnostic OpenAI-compatible client**.
It works with any provider that implements the standard
`/chat/completions` API — including several with free tiers:

- **Groq** (fast, generous free tier, OpenAI-compatible) — recommended default
- **OpenRouter** (has multiple `:free` suffixed models)
- **Local Ollama** (fully free/offline, no API key required)
- Together.ai, Fireworks, etc. — anything OpenAI-wire-compatible

You choose the provider entirely via `.env` (`LLM_BASE_URL`, `LLM_MODEL`,
`LLM_API_KEY`) — **no code changes needed**. This also satisfies PRD Section
4's requirement that the design be "model-agnostic at the interface layer."

---

## 1. Packages you need to install

Everything is pinned in `requirements.txt`:

```
fastapi, uvicorn[standard], sqlalchemy, asyncpg, psycopg2-binary, alembic,
pydantic, pydantic-settings, redis, openai, python-jose[cryptography],
passlib[bcrypt], python-multipart, python-dotenv, tenacity, httpx
```

Install with:

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

You also need, **outside of pip**:
- **PostgreSQL 14+** running somewhere (local install or Docker)
- **Redis 6+** running somewhere (local install or Docker)
- Python 3.11+

The easiest path is Docker Compose (see below), which installs Postgres +
Redis for you — you'd still `pip install -r requirements.txt` locally if you
want to run the API outside its own container, or just let the `api` service
in `docker-compose.yml` build it for you.

---

## 2. Manual steps (things this code cannot do for you)

1. **Get a free LLM API key.**
   - Go to https://console.groq.com (or https://openrouter.ai, or install
     [Ollama](https://ollama.com) locally) and create a free API key.
   - This is a signup step on the provider's website — no code here can do
     it for you.

2. **Copy `.env.example` to `.env`** and fill in:
   - `LLM_API_KEY` with the key from step 1.
   - `LLM_BASE_URL` / `LLM_MODEL` if you're not using Groq's
     `llama-3.1-8b-instant` default (check the provider's docs for current
     free-tier model names — these change over time, so verify on the
     provider's site rather than trusting any hardcoded name here).
   - `JWT_SECRET` — generate one yourself, e.g. `openssl rand -hex 32`.

3. **Start Postgres + Redis.** Either:
   - `docker compose up -d postgres redis` (recommended), or
   - install/start them yourself and update `DATABASE_URL` /
     `SYNC_DATABASE_URL` / `REDIS_URL` in `.env` to point at them.

4. **Create the database tables.** Tables auto-create on app startup
   (`init_db()` in `app/database.py` calls `create_all`) — no manual
   migration needed for MVP. If you later want real migrations (recommended
   before production), you'll need to manually initialize Alembic:
   ```bash
   alembic init alembic
   # then configure alembic.ini / env.py to use SYNC_DATABASE_URL
   # and generate a first revision:
   alembic revision --autogenerate -m "init"
   alembic upgrade head
   ```
   This step is **not automated** — Alembic is in `requirements.txt` but
   not wired up, per the PRD's own note in Section 0 that this document
   hands off to sprint planning for exactly this kind of follow-up work.

5. **Seed at least one concept** (optional but recommended, gives the
   Misconception Agent something to check against):
   ```bash
   python seed_concepts.py
   ```

6. **Run the API:**
   ```bash
   uvicorn app.main:app --reload
   ```
   or via Docker:
   ```bash
   docker compose up --build
   ```
   Visit `http://localhost:8000/docs` for interactive Swagger UI.

7. **Register a user and try the loop:**
   ```bash
   curl -X POST localhost:8000/v1/auth/register -H "Content-Type: application/json" \
     -d '{"email":"student@example.com","password":"pass1234"}'

   curl -X POST localhost:8000/v1/auth/login \
     -d "username=student@example.com&password=pass1234"
   # copy the access_token from the response

   curl -X POST localhost:8000/v1/session -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" -d '{"concept_name":"Two Sum / Hash Maps"}'
   # copy the session id

   curl -X POST localhost:8000/v1/session/<session_id>/turn \
     -H "Authorization: Bearer <token>" -H "Content-Type: application/json" \
     -d '{"message":"I am stuck on Two Sum"}'
   ```

8. **Rate limiting (Section 19 table) is NOT implemented in-app.** The PRD
   specifies per-endpoint rate limits (e.g. 30/min/user on `/turn`). This is
   normally handled at an API gateway / reverse proxy layer (nginx, an AWS
   API Gateway, or a library like `slowapi`), which is an infra decision the
   PRD leaves to Engineering (Section 4). You'll need to add this manually
   before any public deployment.

9. **Create a mentor account manually** if you want to test the mentor
   endpoints — register with `"role": "mentor"` in the register payload
   (there's no self-serve upgrade flow, matching the PRD's "no co-teaching in
   real time in MVP" assumption in Section 2.5).

---

## 3. Project structure

```
app/
  main.py              FastAPI app, router registration, startup hook
  config.py            Settings (env-driven)
  database.py          Async SQLAlchemy engine/session, init_db()
  redis_client.py       Working/session memory (Section 12)
  models.py            All tables from Section 18
  schemas.py           Pydantic request/response models
  auth.py              JWT auth (register/login/current-user dependency)
  jwt_ws.py            Token decode helper for the WebSocket endpoint
  llm_client.py        Model-agnostic OpenAI-compatible client
  state_machine.py     Learner State Machine (Section 8)
  hint_ladder.py        Hint Escalation Ladder (Section 10)
  mode_selector.py      Tutor Mode selection (Section 9)
  orchestrator.py       Ties everything together per Section 11.5/11.6
  agents/
    diagnostic_agent.py
    socratic_agent.py
    misconception_agent.py
    mastery_agent.py
    answer_leak_guard.py
    heuristics.py        Non-LLM confidence/overload/curiosity signals
  routers/
    auth_router.py
    session_router.py     POST /v1/session, POST /turn, GET /state
    ws_router.py           WebSocket streaming version of /turn
    profile_router.py      GET /v1/profile/mastery
    reflection_router.py   POST /v1/reflection (triggers Mastery Agent)
    mentor_router.py       GET /v1/mentor/students, POST /v1/mentor/override
seed_concepts.py        Manual DB seed script
requirements.txt
docker-compose.yml
Dockerfile
.env.example
```

## 4. Endpoints implemented (maps to PRD Section 19)

| Endpoint | Method | Notes |
|---|---|---|
| `/v1/auth/register` | POST | not in original table, needed for auth |
| `/v1/auth/login` | POST | returns JWT |
| `/v1/session` | POST | start session for a concept |
| `/v1/session/{id}/turn` | POST | synchronous version |
| `/v1/ws/session/{id}/turn` | WS | streaming version, `?token=<jwt>` query param |
| `/v1/session/{id}/state` | GET | current state/mode/hint tier |
| `/v1/profile/mastery` | GET | mastery scores across concepts |
| `/v1/reflection` | POST | submit teach-back, triggers Mastery Agent |
| `/v1/mentor/students` | GET | mentor-only |
| `/v1/mentor/override` | POST | mentor-only, logged per Section 15 |

## 5. Known simplifications (be upfront about these)

- **No pgvector / real embeddings.** `memory_facts` retrieval is a flat
  lookup by `concept_id`, not vector similarity search. Fine for MVP scale
  (Section 2.1 says pgvector is an *available* option, not mandatory), but
  swap in `pgvector` + an embeddings call if the concept graph grows large.
- **Diagnostic Agent runs every turn**, not just once per topic. The PRD
  diagram (Section 11.6) shows it as the first step of every turn, so this
  matches the diagram, but it does cost one extra LLM call per turn — tune
  `MAX_AGENT_CALLS_PER_TURN` / cache diagnosis if cost becomes an issue.
- **`transfer_solved` / `coherent_teach_back` signals are not auto-detected**
  from free text in the main turn loop — they're currently only set `True`
  via the `/v1/reflection` mastery-check flow. Wiring a lightweight
  transfer-task detector into `orchestrator.py` is a good Phase 2 ticket.
- **Retention scheduling (7-day re-check, FR-07) has no cron job** — the
  `retention_due_at` column exists but nothing populates/checks it yet.
  Add a scheduled worker (Celery beat, APScheduler, or a cloud cron hitting
  a new `/v1/internal/retention-check` endpoint).
- **No cheating-detection heuristics beyond the basic stuck/hedge-word
  signals** (Section 15's "sudden jump in solution sophistication" pattern
  is not implemented — would need a diff against the student's own prior
  turns, a good Phase 2 addition to `heuristics.py`).

## 6. Stretch goals (Phase 2 per PRD Section 23)

- Cross-session memory beyond what `learner_profile`/`mastery` already store
- Real vector search (pgvector) for the concept graph
- Retention-check scheduler
- Rate limiting middleware
- Alembic migrations wired up
- Prompt-injection classifier on input (Section 15 mentions this explicitly —
  currently the Answer-Leak Guard is the only defense, which the PRD itself
  notes should hold regardless of injected instructions, but a dedicated
  input classifier would add defense-in-depth)
