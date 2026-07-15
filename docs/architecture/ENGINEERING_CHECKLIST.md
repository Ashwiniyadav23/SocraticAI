# Engineering Checklist

*Note: No feature should be merged unless every checklist item passes. This checklist enforces the principles established in Architecture Freeze v1.0.*

## Mandatory Pull Request Checklist

### 1. Architecture Compliance
- [ ] Does this PR strictly adhere to `ARCHITECTURE_FREEZE_v1.0.md`?
- [ ] Are all new prompts registered centrally via POS (No hardcoded prompts)?
- [ ] Does LangGraph routing remain centralized in the Decision Engine (ADES)?
- [ ] Are architectural changes (if any) documented via a new ADR in `ADR_INDEX.md`?

### 2. Requirements Compliance
- [ ] **PRD Compliance**: Does this change fulfill the user story or product requirement?
- [ ] **TRD Compliance**: Does the implementation match the Technical Requirements Document?
- [ ] **ABS Compliance**: Does this align with the Astra Behavior Specifications (e.g., Never give the direct answer)?

### 3. Testing
- [ ] **Unit Tests**: Have unit tests been added/updated for all new core logic (minimum 85% coverage)?
- [ ] **Integration Tests**: Do the modules integrate seamlessly within the LangGraph state?
- [ ] **Prompt Tests**: If a prompt was added/updated, has it been evaluated against golden datasets for regressions?
- [ ] **Behavior Tests**: Are the `Meta Learning` and `Decision Engine` modules successfully detecting and routing appropriately based on the new code?

### 4. Quality & Security
- [ ] **Security Tests**: Are inputs validated? Are prompt injection protections maintained via the Guardrails?
- [ ] **Performance Tests**: Does this change negatively impact the time-to-first-token latency? Are async DB writes used appropriately to prevent blocking?

### 5. Deployment & Maintenance
- [ ] **Documentation**: Have inline docstrings, API schemas, and relevant README files been updated?
- [ ] **Migration Safety**: If DB schemas were changed, is an Alembic migration script included, and is it safe to run on production without data loss?
