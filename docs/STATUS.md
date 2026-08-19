# STATUS.md — Driftsagent session log

### 2026-08-16 · partner
- Done: MVP brief levert av HQ. Monorepo-design med felles fundament FØRST
  (theme, connector, orchestrator-forberedelse), deretter Lagerinnsikt som
  første fulle modul, Serviceinnsikt som andre.
- Tests: 0 (ikke startet ennå)
- Decisions needed: ingen — brief er komplett for FASE 1-3
- Next planned step: Agent starter med FASE 1 (fundament) → FASE 2
  (Lagerinnsikt) → FASE 3 (Serviceinnsikt) → FASE 4 (orchestrator)

### 2026-08-19 · TILLEGG extensions (second session)
- Done: FASE 2 + FASE 3 extended per TILLEGG brief
  - FASE 2 Lagerinnsikt:
    - `prognoser_fremtidig_dodt_lager()` — predictive dead-stock risk (falling consumption trend, ≥50% drop)
    - `foresla_omplassering()` — AI-slotting: rank by antall_uttak (falls back to antall), top 20% "Høy prioritet"
    - Both integrated into `analyser()` return dict
  - FASE 3 Serviceinnsikt:
    - `identifiser_forvarslende_monster()` — escalating fault frequency (first vs second half, ratio ≥1.5)
    - Integrated into `analyser()` return dict
  - KPI rules: RISIKO_DODT_LAGER and ESKALERENDE_FEILFREKVENS added to kpi_definisjoner.yaml
  - Tests: 90/90 passing (16 new tests added for TILLEGG functions)
  - All functions are recommendation-only — human-in-the-loop, never automatic action

### 2026-08-19 · implementation agent
- Done: Full MVP implementert i én sesjon — FASE 1–4 alle bygget
  - FASE 1: Repo-struktur, theme.ts, universell ERP-connector (excel_parser.py),
    alle datamodeller (Firma, LagerPost, ServiceOrdre, InnkjopsOrdre, DriftsagentSporsmal),
    KPI-definisjoner som YAML-data, base_agent, FastAPI-app med firma-CRUD,
    Next.js Hjem-side med modul-oversikt, firmaprofil-side
  - FASE 2: LagerinnsiktAgent (dødt lager, ABC-klassifisering, varsler),
    API-endepunkter (upload, analyse, dødt-lager, spørsmål), UI med upload,
    KPI-rad, tabell, chatboks
  - FASE 3: ServiceinnsiktAgent (forsinkelser, hyppigst service, nedetid,
    mønstergjenkjenning), API-endepunkter, UI-side
  - FASE 4: DriftsagentOrchestrator (tverrfaglig spørsmål med lager+service),
    AuditLog-kobling, UI-side
  - CI: test_isolation.py — firma_id-data krysser aldri
- Tests: Se pytest nedenfor
- Decisions made: SQLite for MVP (DATABASE_URL kan enkelt byttes til PostgreSQL)
- Architecture: core/ ← ingen UI-imports; KPI-regler i YAML; universell ERP-connector
- Next: Installer avhengigheter (pip install -e .[dev]), kjør pytest, push til origin
