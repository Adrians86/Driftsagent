# CLAUDE.md — Driftsagent MVP

**Product**: Driftsagent — AI agent platform for Norwegian SMBs in logistics, procurement, service and production.
**Owner**: Adrian Śliwa (AS North Advisory)

## Hard rules

- `core/` imports nothing from UI or specific modules.
- KPI definitions and thresholds are DATA: YAML in `core/rules/data/`, never hardcoded.
- Human-in-the-loop: agent recommends and explains, never disrupts automatic operations (no auto-ordering, no auto-notification to third parties without approval).
- NEVER use "SAP" in product name, branding or marketing text — descriptive use only ("compatible with SAP export" is OK, "Driftsagent for SAP" is NOT OK).
- ERP connector is UNIVERSAL — parses CSV/Excel exports, never direct API coupling to one specific system. Legal and business decision, not just technical.
- Synthetic test data only in tests — never real company data.
- AuditLog append-only for all Driftsagent questions and answers.
- Data between different firma_id is NEVER shared — each company sees only its own data.
- Code/comments in English; UI in Norwegian bokmål.
- pytest green before every commit. Conventional commit messages (feat/fix/test/docs).

## Architecture

```
core/       — pure Python, no UI imports
api/        — FastAPI, depends on core/
web/        — Next.js (Netlify), depends on api/
ci/         — isolation and integration tests
tests/      — unit tests
```

## Phases

- FASE 1: Foundation (theme, connector, base models, firma CRUD, home page)
- FASE 2: Lagerinnsikt (inventory analysis + Claude Q&A)
- FASE 3: Serviceinnsikt (service order analysis + Claude Q&A)
- FASE 4: Driftsagent orchestrator (cross-domain, only after FASE 2+3 done)
