# Implementation Roadmap v2.0

*Note: Do NOT allow implementation of a milestone unless all previous milestones are complete.*

---

## Milestone 1: Database & Memory Foundation (MAS)
**Goal:** Establish the foundational schemas and state tracking required for all higher-level engines.
- **Files:** `app/database.py`, `app/ai/memory/*.py`, alembic migrations.
- **Database Changes:** Create tables for `short_term_memory`, `working_memory`, `episodic_memory`, `semantic_memory`.
- **API Changes:** None (Internal state only).
- **Frontend Changes:** None.
- **Tests:** CRUD operations on memory tables, vector store embedding/retrieval mocks.
- **Acceptance Criteria:** Memory objects can be successfully hydrated into and flushed from a mock LangGraph state.
- **Definition of Done:** PR approved, 90% test coverage, schemas live in dev DB.
- **Dependencies:** None.
- **Risk Level:** Low.
- **Estimated Complexity:** Medium.
- **Estimated Duration:** 2 days.

---

## Milestone 2: Prompt Orchestration Service (POS)
**Goal:** Centralize all system prompts and remove hardcoded prompts from the codebase.
- **Files:** `app/ai/prompts/registry/*`, `app/ai/prompts/service.py`, `app/ai/prompts/guardrails.py`.
- **Database Changes:** (Optional) Add `prompts` and `prompt_versions` if using DB fallback, otherwise file-system YAML is sufficient.
- **API Changes:** Internal `PromptService.get(name, state)`.
- **Frontend Changes:** None.
- **Tests:** Template rendering, input schema validation, missing variable exceptions.
- **Acceptance Criteria:** Existing agents use `PromptService` instead of `PromptTemplate`.
- **Definition of Done:** All raw prompts removed from Python files.
- **Dependencies:** Milestone 1.
- **Risk Level:** Low.
- **Estimated Complexity:** Low.
- **Estimated Duration:** 1 day.

---

## Milestone 3: Context & Meta-Learning Core (LCES & MLS)
**Goal:** Implement the engines that detect the "Why" (Context) and the "How" (Behavior) of the student's learning session.
- **Files:** `app/ai/context/*.py`, `app/ai/meta_learning/*.py`.
- **Database Changes:** `session_contexts`, `meta_learning_events`.
- **API Changes:** Analytics/Dashboard endpoints for behavior events.
- **Frontend Changes:** None.
- **Tests:** Signal detection accuracy using golden datasets (mock chat transcripts).
- **Acceptance Criteria:** Context and Behavior signals are successfully appended to the internal state on test inputs.
- **Definition of Done:** Engines can reliably identify 5 defined behavior anti-patterns and 3 contexts.
- **Dependencies:** Milestone 2.
- **Risk Level:** Medium (LLM detection reliability).
- **Estimated Complexity:** High.
- **Estimated Duration:** 4 days.

---

## Milestone 4: Learning Mission Engine (LME)
**Goal:** Build the hierarchical progression system.
- **Files:** `app/ai/missions/*.py`.
- **Database Changes:** `learning_missions`, `mission_milestones`, `skills`.
- **API Changes:** `GET /api/v1/missions/{user_id}`, `POST /api/v1/missions`.
- **Frontend Changes:** Basic Mission Dashboard view.
- **Tests:** Generation of mission trees, state tracking of skill mastery.
- **Acceptance Criteria:** A user can request a mission, and a valid Milestone/Skill tree is persisted.
- **Definition of Done:** DB cascading works, API routes return accurate progress.
- **Dependencies:** Milestone 1.
- **Risk Level:** Medium.
- **Estimated Complexity:** Medium.
- **Estimated Duration:** 3 days.

---

## Milestone 5: AI Decision Engine (ADES) & Core Graph Update
**Goal:** Centralize the Tutor Graph's routing logic to utilize the newly built engines.
- **Files:** `app/ai/decision_engine/*.py`, `app/ai/graphs/tutor_graph.py`.
- **Database Changes:** `decision_logs`.
- **API Changes:** None.
- **Frontend Changes:** None.
- **Tests:** Deterministic routing tests ensuring that specific Context/Behavior states route to the correct Tutor Node.
- **Acceptance Criteria:** LangGraph conditional edges are replaced by the `DecisionEngineRouter`.
- **Definition of Done:** The graph executes end-to-end utilizing DNA, Context, and Behavior.
- **Dependencies:** Milestone 1, 2, 3, 4.
- **Risk Level:** High (Core logic rewrite).
- **Estimated Complexity:** High.
- **Estimated Duration:** 5 days.

---

## Milestone 6: Behavior-Aware RAG (BARS)
**Goal:** Implement personalized knowledge retrieval.
- **Files:** `app/ai/rag/*.py`.
- **Database Changes:** Vector store indices (pgvector/Pinecone).
- **API Changes:** `POST /api/v1/rag/ingest`.
- **Frontend Changes:** None.
- **Tests:** Re-ranking accuracy based on mock DNA profiles.
- **Acceptance Criteria:** Search results are ranked differently for a "Visual Learner" vs a "Textual Learner" using the same query.
- **Definition of Done:** BARS integrated into the Tutor Graph context gathering phase.
- **Dependencies:** Milestone 1 (Semantic Memory), Milestone 5.
- **Risk Level:** High.
- **Estimated Complexity:** High.
- **Estimated Duration:** 4 days.

---

## Milestone 7: AI Evaluation Framework (AEF)
**Goal:** Build the telemetry and metrics calculation background workers.
- **Files:** `app/analytics/evaluation/*.py`.
- **Database Changes:** `user_learning_metrics`, `evaluation_logs`.
- **API Changes:** `GET /api/v1/analytics/metrics`.
- **Frontend Changes:** Admin dashboard charts for Hint Effectiveness and Dependency Reduction.
- **Tests:** Formula calculation accuracy, LLM-as-a-judge consistency.
- **Acceptance Criteria:** End-of-session events successfully trigger async metric calculations that update the DB.
- **Definition of Done:** System can accurately output the Hint Effectiveness score over 10 mock sessions.
- **Dependencies:** Milestone 5.
- **Risk Level:** Low (Background process).
- **Estimated Complexity:** Medium.
- **Estimated Duration:** 3 days.
