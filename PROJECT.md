# Project: RR Squad Intelligence & Team Composition Platform (IPL 2027 RR Scouting Hackathon)

> ⚠️ **SUPERSEDED-V1 NOTICE**: This file previously carried the **v1.0.0** "Historical
> Performance Engine" specification (Next.js 15 / FastAPI / Redis presentation-and-service
> stack, 20-entity schema, F01–F25 auction-war-room feature inventory, `CricSheet/` data
> path). **That architecture is no longer the project architecture.** This file has been
> reconciled (v2.2.0) to the current charter. The superseded v1 content is preserved for
> audit at the end of this file under "Appendix A — Historical v1.0.0 Specification
> (superseded)". Authoritative current documents: `README.md`, `docs/PRD.md`,
> `docs/TRD.md`, `docs/ARCHITECTURE.md`, `docs/PHASES.md`, `docs/AGENTS.md`,
> `docs/AI_INSTRUCTIONS.md`, `docs/DATA_SOURCE_REGISTER.md`, `docs/DATA_DICTIONARY.md`, `docs/RANKING_SPEC.md`.

## Architecture (current, v2.2.0)
- **Streamlit-primary, frontend-agnostic engine layer**: Streamlit application (initial
  UI, 11 views) over typed, versioned engine contracts; a future Next.js frontend reuses
  the same contracts (no engine imports a UI framework).
- **Mother Intelligence Engine (MIE)**: central orchestrator — coordinates the seven
  specialised engines, merges verified outputs, tracks verification status and source
  provenance, returns structured reports. MIE never invents statistics, identities,
  memberships, or eligibility decisions.
- **Seven specialised engines**: PIRE (identity) · TMVE (membership verification) · CDCRE
  (career discovery, dual capability) · CPPAE (performance analytics) · CMIE (contextual
  match intelligence) · SICE (squad intelligence & composition) · PVRE (player verification & research engine).
- **Support services**: A. Data Ingestion · B. Player Profile Generator ·
  C. Source Verification & Provenance · D. Data Quality & Coverage · E. Team Builder.
- **Normalised 33-entity PostgreSQL 16 core** (3NF core; `derived_features` the single
  documented non-3NF exception; season-partitioned `deliveries` with enforced
  partitioned-table FKs on PG ≥ 15; includes `player_season_stats` and `player_match_stats`).
- **Ingestion & provenance pipeline**: immutable raw staging (SHA-256), quarantine
  handling, five-tier evidence provenance (`datasets/` local lake; Kaggle / HawkeyeStats /
  Open-Meteo / official records per `docs/DATA_SOURCE_REGISTER.md`).
- **Core engineering principles**:
  1. *Deterministic reproducibility* — deterministic query path; versioned, seeded model
     configuration; bit-for-bit reproducible rankings (AC-18).
  2. *Normalised 3NF relational core* — 33 entities, hard foreign keys, expression
     indexes, domain check constraints; no false-claim defaults.
  3. *Read-only immutable data lake* — `datasets/` is immutable; payloads staged with
     SHA-256 digests and quarantining.
  4. *Zero statistical fabrication* — missing → `NULL`; no invented players, memberships,
     injuries, or mental states; no cross-format stat mixing without documented
     normalisation.
  5. *Evidence-first membership & eligibility* — three independent dimensions (RR
     relationship · currency · season-bound versioned eligibility); franchise-level
     `team_season_participation` (RR 2016–17 suspended; 2027 UNKNOWN until evidenced);
     negative membership only via TRD §4.5 requirements.
  6. *Greenfield governance* — no application code exists; all planned features
     demarcated `[STATUS: PLANNED]`; Phase 0b (empirical source audit) remains open.

## Feature & Component Inventory (current)

| # | Component | Category | Description | Phase | Governing doc | Status |
|---|---|---|---|---|---|---|
| C1 | PIRE | Engine 01 | Deterministic 4-tier identity resolution + contextual attribute corroboration; calibrated-only confidence | 2 | TRD §3 | `[STATUS: PLANNED]` |
| C2 | TMVE | Engine 02 | Three-dimension membership (relationship / currency / season-bound eligibility) + negative-verification protocol | 3 | TRD §4 | `[STATUS: PLANNED]` |
| C3 | CDCRE (dual capability) | Engine 03 | `discover_candidates(raw_name)` pre-identity + `discover_career(player_id)` post-identity; four-state coverage | 4 | TRD §5 | `[STATUS: PLANNED]` |
| C4 | CPPAE | Engine 04 | Full performance profiles governed by `DATA_DICTIONARY.md` (B/W/F/M series, NOT_COMPUTABLE list) | 5 | TRD §6 + DATA_DICTIONARY | `[STATUS: PLANNED]` |
| C5 | CMIE | Engine 05 | Contextual conditions with 5 provenance tiers; weather ≠ pitch; ratings only with validated methodology | 6 | TRD §7 | `[STATUS: PLANNED]` |
| C6 | SICE | Engine 06 | Squad role/depth/balance analysis; 16-dimension replacement comparison (§8.4); labelled analytical recommendations; hackathon ranking support | 8 | TRD §8 | `[STATUS: PLANNED]` |
| C6b | PVRE | Engine 07 | Dual-mode player research & replacement intelligence (Mode A: RR replacement; Mode B: uncapped domestic discovery; REVIEW_REQUIRED safety) | 4B | TRD §9 | `[STATUS: PLANNED - MVP]` |
| C7 | MIE | Orchestrator | Candidate-discovery-first sequence; merges outputs; verification tracking; provenance assembly | 7 | TRD §2 | `[STATUS: PLANNED]` |
| C8 | Services A–E | Support | Ingestion · profile export · provenance · quality/coverage · team builder | 1/7/4/1/8 | TRD §10 | `[STATUS: PLANNED]` |
| C9 | 33-entity DDL | Data | Verified PostgreSQL 16 core (design decisions D1–D10 + entity reconciliation) | 2 | TRD §11 | `[STATUS: PLANNED]` |
| C10 | `team_season_participation` | Data | Franchise-season participation (PARTICIPATING/SUSPENDED/NOT_ENTERED/UNKNOWN, evidence-bound) | 3 | TRD D4 | `[STATUS: PLANNED]` |
| C11 | Eligibility policy model | Data | `eligibility_policies` (versioned, season-bound, source-traceable, effective-dated) + `player_eligibility` | 3 | TRD D5 | `[STATUS: PLANNED]` |
| C12 | DATA_SOURCE_REGISTER | Governance | Source-to-field mapping, verification statuses, match/delivery reconciliation, licence evidence | 0b | docs/DATA_SOURCE_REGISTER.md | `[STATUS: OPEN - external verification outstanding]` |
| C13 | DATA_DICTIONARY | Governance | Complete metric definitions (formula, numerator/denominator, null rules, samples, class) | 5 | docs/DATA_DICTIONARY.md | `[STATUS: COMPLETE]` |
| C14 | Streamlit application | UI | 11 required views; session-state discipline; UI separated from analytics | 9 | TRD §12, PRD §6 | `[STATUS: PLANNED]` |
| C15 | Hackathon Top-10 deliverable | Deliverable | Youngest eligible uncapped candidate board + reserves, reproducible role-aware ranking, evidence dossiers | 10 | PRD §4.3 | `[STATUS: PLANNED]` |
| C16 | Post-MVP enhancements | Deferred | EAP/VORP-WAR regression, Monte Carlo campaign simulation, Playing XI optimizer, Impact Player engine, Next.js frontend | — | PRD §7 | `[STATUS: POST-MVP]` |

## Roadmap
Phases 0a/0b → 1–4 → 4B (PVRE) → 5–10 per [`docs/PHASES.md`](docs/PHASES.md). **Phase 0a COMPLETE; Phase 0b
OPEN (PARTIALLY_COMPLETE)**; Phase 4B `[PLANNED - MVP]`; Phases 1–10 PLANNED.

## Repository Layout

```
d:\New folder (2)\
├── .agents/teamwork/                    # Historical agent evidence (v1/v2 audits) — preserved, not modified
├── datasets/                            # [IMMUTABLE, UNTRACKED] Raw cricket datasets (13 CricSheet archives, 5,083 JSON files, ODC-By)
│   ├── ipl_male_json/                   #   1,243 IPL match files (JSON v1.3.0) + LICENSE/README
│   ├── bbl_male_json/                   #   662 BBL match files
│   ├── sma_json/                        #   695 SMAT match files
│   ├── hnd_male_json/                   #   201 The Hundred match files
│   ├── icc_mens_cricket_world_cup_male_json/ # 265 ODI WC files (24 withheld, CricSheet policy)
│   └── icc_mens_t20_world_cup_male_json/     # 230 T20 WC files (29 withheld, CricSheet policy)
├── docs/                                # Authoritative documentation suite (10 documents)
│   ├── README.md · PRD.md · TRD.md · ARCHITECTURE.md · PHASES.md
│   ├── AGENTS.md · AI_INSTRUCTIONS.md
│   ├── DATA_SOURCE_REGISTER.md · DATA_DICTIONARY.md · RANKING_SPEC.md
├── reports/DOCUMENTATION_REMEDIATION_AUDIT.md
├── DOCUMENTATION_PRE_REMEDIATION_AUDIT.md
├── PROJECT.md                           # This charter (v2.2.0)
└── README.md                            # Project overview, status, change set
```

## Planned Implementation Layout (Phases 1–9)

```
d:\New folder (2)\
├── src/                                 # [PLANNED - Phase 2+] Engine & service implementations
│   ├── mie/                             #   Mother Intelligence Engine (orchestration, merge, verification status)
│   ├── pir/                             #   PIRE (4-tier resolver, alias registry, review queue)
│   ├── membership/                      #   TMVE (three dimensions, negative-verification, participation seeding)
│   ├── research/                        #   CDCRE dual capability + external research adapter (provenance-tracked)
│   ├── analytics/                       #   CPPAE per DATA_DICTIONARY (NULL-safe, format-tagged, sample-visible)
│   ├── context/                         #   CMIE (5 provenance tiers; weather/pitch separation)
│   ├── squad/                           #   SICE + ranking model configuration (versioned weights)
│   ├── pvre/                            #   PVRE Mother Controller, Mode A, Mode B, REVIEW_REQUIRED safety
│   ├── elt/                             #   Ingestion, SHA-256 staging, quarantine, reconciliation (Service D)
│   └── profile_gen/                     #   Service B exports (JSON/CSV, attribution, confidentiality guard)
├── migrations/                          # [PLANNED - Phase 2] V001__initial_33_entity_schema.sql, V002__*.sql
├── app/streamlit/                       # [PLANNED - Phase 9] 11-view Streamlit application (thin adapters only)
└── tests/                               # Unit, integration, statistical, adversarial, and architecture import tests
```

---

## Appendix A — Historical v1.0.0 Specification (superseded, preserved for audit)

The following is the superseded v1.0.0 specification. It is retained **for audit
continuity only** and must not be read as the current architecture.

### A.1 Superseded Architecture Statement
> Multi-Tier Analytical Architecture: Client Presentation (Next.js 15, Tailwind CSS 3.4,
> Apache ECharts 5.5, Recharts 2.12, React Flow 11.11) ↔ REST API & Service Layer
> (FastAPI, ASGI Uvicorn, Pydantic v2, Redis 7.2) ↔ Analytics & Tactical Simulation
> Engine (Python 3.13 / 3.11+, NumPy 1.26+, Pandas 2.2+, SciPy) ↔ Central Normalized
> Relational Core (PostgreSQL 16, 20 Discrete Entities, Declarative Partitioning) ↔
> Ingestion & Contextual Enrichment Pipeline (CricSheet JSON v1.3.0 / YAML v0.94 in
> `CricSheet/`, Kaggle Historicals, Open-Meteo Historical Weather, HawkeyeStats Tracking
> Telemetry). **Superseded by the MIE + 7 specialised engines + 5 services architecture over the
> 33-entity core with `datasets/` as the data path.**

### A.2 Superseded v1 Feature Inventory (F01–F25, all PLANNED, now re-mapped)
| # | Feature | v1 Category | v2.1.0 Disposition |
|---|---|---|---|
| F01 | Ball-by-Ball Context Valuation (TSR/TER) | Match Impact | Post-MVP analytics depth (CMIE/CPPAE); not in MVP |
| F02 | Win Probability Added (WPA) & xR | Match Impact | Post-MVP |
| F03 | Clutch Index & Leverage | Match Impact | Superseded by CMIE "measurable high-leverage contribution" (DATA_DICTIONARY M06); mental-state inference prohibited |
| F04 | Pitch & Ground Behavioral Profiling | Venue Profiling | CMIE pitch reporting (text preserved; ratings methodology-bound) |
| F05 | SMS Jaipur Fortress Engine | Venue Profiling | Post-MVP venue profiling (out of MVP scope) |
| F06 | Environmental & Dew Factor Correlation | Venue Profiling | CMIE weather-as-context (no dew-imputed pitch claims) |
| F07 | Batter vs Bowling Type Profiling | Tactical Matrix | CPPAE B14/B15 (style-class splits) |
| F08 | Head-to-Head Batter vs Bowler | Tactical Matrix | CPPAE B13/W10 (sample-visible) |
| F09 | Pitch Trajectory & Length | Tactical Matrix | Post-MVP (HawkeyeStats UNVERIFIED; third-party, not official Hawk-Eye) |
| F10 | Multi-Format Workload | Fatigue | Post-MVP (not in MVP; no unvalidated fatigue curves) |
| F11 | Schedule Congestion & Travel | Fatigue | Post-MVP |
| F12 | Injury & Availability | Fatigue | CMIE/CPPAE verified-only availability (`player_injuries`, `player_availability`); no unvalidated risk scores |
| F13 | Expected Auction Price (EAP) | Valuation | **Post-MVP** — no probabilities from unvalidated models (SICE guardrail) |
| F14 | VORP | Valuation | Post-MVP |
| F15 | Role Scarcity Multipliers | Valuation | Post-MVP |
| F16 | Playing XI Constraint Optimizer | Squad Simulation | Post-MVP |
| F17 | Impact Player Deployment | Squad Simulation | Post-MVP |
| F18 | Monte Carlo Tournament Simulator | Squad Simulation | Post-MVP (deterministic seed if implemented) |
| F19 | Cross-Competition Normalisation | Scouting | Prohibited without documented normalisation factors (NFR-04) |
| F20 | Diamond-in-the-Rough Filter | Scouting | Superseded by the **Top-10 youngest eligible uncapped deliverable** (PRD §4.3; transparent role-aware ranking, versioned weights) |
| F21 | Multi-Source Player Identity Resolution | Core Data | PIRE (deterministic tiers; `agent_pire`) |
| F22 | Multi-Format Ingestion Engine | Ingestion | Service A ingestion (JSON v1.3.0 local; YAML not present locally — `datasets/` are all JSON) |
| F23 | DLS Par & Revised Target Reconciler | Ingestion | CPPAE/CMIE DLS rules (DATA_DICTIONARY global conventions) |
| F24 | Super Over Isolation | Core Data | Enforced in DDL (`innings.is_super_over`) + DATA_DICTIONARY exclusions |
| F25 | Central 20-Entity Schema | Architecture | Superseded by the 33-entity remediated DDL (TRD §11) |
