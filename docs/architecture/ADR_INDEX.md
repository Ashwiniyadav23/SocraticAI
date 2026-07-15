# Architecture Decision Records (ADR) Index

*Note: Future architectural changes must be recorded here. No architectural changes should be made without an ADR.*

## Current ADRs

| ADR Number | Title | Status | Date |
| --- | --- | --- | --- |
| ADR-001 | Base Architecture Freeze v1.0 | **Accepted** | 2026-07-15 |
| ADR-002 | Move to Multi-Agent Architecture | *Draft* | TBD |
| ADR-003 | Switch Embedding Model | *Draft* | TBD |
| ADR-004 | Voice Provider Change | *Draft* | TBD |
| ADR-005 | Memory Schema Update | *Draft* | TBD |
| ADR-006 | Prompt Registry Version Upgrade | *Draft* | TBD |

---

## ADR Template

To create a new ADR, copy the format below and add it to the `docs/architecture/adrs/` folder. Update the index above.

```markdown
# ADR-[Number]: [Short, Descriptive Title]

**Status:** [Draft | Proposed | Accepted | Rejected | Superseded]  
**Date:** [YYYY-MM-DD]  
**Author(s):** [Name(s)]

## Context
[What is the technical or business problem that requires this architectural change? What are the driving forces? Why is this a problem now?]

## Decision
[What is the proposed change? What are we going to do? Be clear and specific.]

## Consequences
### Positive
- [Benefit 1]
- [Benefit 2]

### Negative
- [Drawback/Risk 1]
- [Drawback/Risk 2]

## Alternatives Considered
- **[Alternative 1]:** [Why it wasn't chosen]
- **[Alternative 2]:** [Why it wasn't chosen]

## Compliance & Integration Notes
[How does this impact the Architecture Freeze v1.0? What modules in the Dependency Graph are affected?]
```
