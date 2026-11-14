# RR Squad Intelligence & Team Composition Platform

**Focus Franchise**: Rajasthan Royals (RR) · **Competition**: IPL 2027 RR scouting hackathon
**Primary Interface (initial)**: Streamlit · **Future Frontend**: Next.js (engines are frontend-agnostic)
**Status**: `[STATUS: GREENFIELD BASELINE — PHASE 0a COMPLETE / PHASE 0b OPEN (PARTIALLY_COMPLETE) / PHASES 1–10 PLANNED]`

> **Product version 2.2.0 (PVRE Dual-Mode Intelligence)**. Introduces **ENGINE 07 — PVRE
> (Player Verification & Research Engine)** featuring Mother Controller routing, Mode A (Existing
> RR Player Replacement Intelligence: Module A1 RR history + Module A2 2–3 year recent global window +
> Module A3 Replaceability Signals), Mode B (Verified Uncapped Candidate Domestic Career Intelligence),
> and mandatory `REVIEW_REQUIRED` safety gating. Integrates SICE 16 role-aware comparison dimensions
> (§8.4) with strict separation from the hackathon Top-10 uncapped candidate ranking. Establishes
> **Phase 4B** in `docs/PHASES.md` as the authoritative roadmap with 12 checkpoints and AC-24..AC-30.
> Reconciles database baseline to **33 entities** (including `player_season_stats` and `player_match_stats`),
> **7 specialised engines**, and **18 system agents**.
>
> **Product version 2.1.0 (remediated)**. This revision corrects the v2.0.0 schema defects
> (invalid `derived_features` expression UNIQUE constraint, missing partitioned-table
> foreign keys, soft delivery links, false-claim defaults, overs datatype), replaces the
> competition-level RR suspension flag with the franchise-level
> **`team_season_participation`** entity, splits membership into **three independent
> dimensions** (RR relationship · currency · season-bound versioned eligibility), gives
> PIRE deterministic tiers with contextual-attribute corroboration, gives CDCRE two
> capabilities (pre-identity candidate discovery + post-identity career retrieval), and adds
> two governing documents: **`docs/DATA_SOURCE_REGISTER.md`** and **`docs/DATA_DICTIONARY.md`**.
> Full change set: [`reports/DOCUMENTATION_REMEDIATION_AUDIT.md`](reports/DOCUMENTATION_REMEDIATION_AUDIT.md).

---

## 1. What This Product Is

The **RR Squad Intelligence & Team Composition Platform** turns a user-supplied player name
into a **verified, evidence-backed player intelligence report**, and evaluates teams the user
assembles. Its primary workflow:

1. A user creates a team.
2. The user enters a cricket player's name.
3. **CDCRE (capability 1)** performs **pre-identity candidate discovery** on the raw name.
4. The system **identifies** the player (Engine 01 — PIRE; deterministic tiers +
   contextual attribute corroboration; ambiguous → user clarification).
5. The system checks whether the player exists in the internal database.
6. Where necessary, authorised external research (provenance-tracked, tiered) verifies
   identity and cricket history.
7. The system determines RR representation (Engine 02 — TMVE) across **three independent
   dimensions**: RR relationship · current membership · season-bound, policy-versioned
   IPL eligibility.
8. It retrieves and analyses the complete career (CDCRE capability 2, four-state coverage).
9. It evaluates performance, contribution and role (Engine 04 — CPPAE, per
   `DATA_DICTIONARY.md`).
10. It presents the evidence-backed profile (Mother Intelligence Engine — MIE).
11. The user adds the player to a team composition (Team Builder Service).
12. The **Squad Intelligence Engine** (Engine 06 — SICE) evaluates the complete team.

The platform supports **all** of the following player populations, and it **never
automatically assumes that an unknown player is an uncapped player** (unknown =
`RR_RELATIONSHIP_UNKNOWN` / eligibility `NOT_ASSESSED` until independently verified):

- Existing RR players · Former RR players · Players who have never represented RR ·
  Domestic uncapped prospects · Players from other IPL franchises · International players ·
  Players whose identity or eligibility remains unverified.

**Hackathon objective**: identify the **Top 10 youngest eligible uncapped players RR should
consider backing for IPL 2027** (spec: `docs/PRD.md §4.3`) — with verified eligibility,
exact ages as of the evaluation date, role-aware reproducible ranking, and per-candidate
evidence dossiers.

---

## 2. Architecture at a Glance

A central **Mother Intelligence Engine (MIE)** orchestrates **seven specialised engines** and
support services, all reading a **33-entity normalised PostgreSQL core**. The MIE
never invents statistics or makes membership/eligibility decisions; it coordinates the
engines, merges their outputs, tracks verification status and source provenance, and returns
structured reports. Engines are **frontend-agnostic**: the initial UI is **Streamlit**, and
a future **Next.js** frontend reuses the same contracts.

```
┌────────────────────────────────────────────────────────────────────────────────┐
│  Presentation (Streamlit initial / Next.js future)                             │
│  Team Builder · Search · Verification · Career · Analytics · SICE · PVRE Views │
└───────────────────────────────────────┬────────────────────────────────────────┘
                                        ▼
┌────────────────────────────────────────────────────────────────────────────────┐
│  MOTHER INTELLIGENCE ENGINE (MIE) — orchestrates, merges, tracks               │
│  Sequence: candidate discovery → identity → membership → career                │
│           → performance → context → eligibility → PVRE research → SICE        │
└──┬──────┬──────┬──────┬──────┬──────┬──────┬───────────────────────────────────┘
   ▼      ▼      ▼      ▼      ▼      ▼      ▼
 PIRE   TMVE   CDCRE  CPPAE  CMIE   SICE   PVRE
 Eng01  Eng02  Eng03  Eng04  Eng05  Eng06  Eng07 (Mode A / Mode B / Review)
   └────┴────┴────┴────┴────┴────── Support Services A–E
   │
   ▼
 Central PostgreSQL 16 core (33 entities, normalised 3NF core)  ←  datasets/ (immutable)
```

### The seven specialised engines
| Engine | Name | Purpose |
|---|---|---|
| **ENGINE 01 — PIRE** | Player Identity Resolution | Resolve names to canonical player IDs; deterministic 4-tier waterfall with contextual attribute corroboration; never merges similar names; confidence only when calibrated. |
| **ENGINE 02 — TMVE** | Team Membership Verification | Three-dimension membership (relationship · currency · season-bound eligibility); verified appearances vs squad inclusion; negative-verification protocol; franchise participation model. |
| **ENGINE 03 — CDCRE** | Career Discovery & Competition Research | **Two capabilities**: `discover_candidates(raw_name)` (pre-identity) and `discover_career(player_id)` (post-identity); four-state coverage; provenance-tracked external research. |
| **ENGINE 04 — CPPAE** | Complete Player Performance Analytics | Batting / bowling / fielding / wicketkeeping / match contribution, governed by `DATA_DICTIONARY.md` (formulas, null rules, sample minimums, format tags). |
| **ENGINE 05 — CMIE** | Contextual Match Intelligence | Environmental & match conditions; five provenance tiers; weather ≠ pitch; no mental-state inference. |
| **ENGINE 06 — SICE** | Squad Intelligence & Composition | Role/depth/balance/duplication/gap analysis; 16-dimension replacement comparison (§8.4); labelled analytical recommendations; hackathon Top-10 ranking support. |
| **ENGINE 07 — PVRE** | Player Verification & Research Engine | Dual-mode player research & replacement intelligence: Mother Controller, Mode A (RR Replacement: RR history + 2–3 yr global window + Replaceability Signals), Mode B (Verified Uncapped Domestic Career Discovery), and mandatory `REVIEW_REQUIRED` safety gating. |

### The five support services
| Service | Name | Responsibility |
|---|---|---|
| **A** | Data Ingestion | Import CricSheet, Kaggle, HawkeyeStats, historical weather, official records, verified research; statuses per `DATA_SOURCE_REGISTER.md`. |
| **B** | Player Profile Generator | Standardised JSON/CSV exports from the central database (attribution embedded; confidentiality guard). |
| **C** | Source Verification & Provenance | URL, provider, timestamp, licence, tier, status, calibrated confidence, record ID. |
| **D** | Data Quality & Coverage | Missing data, duplicates, conflicts, invalid associations, innings↔delivery reconciliation, unavailable context. |
| **E** | Team Builder | User teams, add/remove, composition, roles, saved configurations. |

---

## 3. Historical Context (Rajasthan Royals)

- RR franchise participation analysis **begins with IPL 2008**; the first phase runs
  **2008–2015**.
- RR were **suspended for IPL 2016 and 2017** (a **franchise-specific** suspension; the IPL
  competition continued for all other teams) and returned in **2018**. This is modelled in
  **`team_season_participation`** (`RR × IPL 2016 = SUSPENDED`, `RR × IPL 2017 = SUSPENDED`),
  not as a competition-wide property.
- Post-return analysis covers **2018 onwards**; the primary window is **2018–2026**.
- **IPL 2027 is a future target season**: RR's 2027 participation row is `UNKNOWN` until
  authoritative squad/participation evidence is verified.

Membership is maintained as **three independent dimensions** (`player_membership_state` +
`player_eligibility`), with `CURRENT_RR_SQUAD` assigned **only** on verified current-season
squad evidence:

- **RR relationship**: `CURRENT_RR_SQUAD` · `HISTORICAL_RR_APPEARANCE` ·
  `HISTORICAL_RR_SQUAD_ONLY` · `PREVIOUSLY_ASSOCIATED` ·
  `NO_VERIFIED_RR_RELATIONSHIP` (only via TRD §4.5 requirements) · `RR_RELATIONSHIP_UNKNOWN`
- **Current status**: `CURRENT` · `NOT_CURRENT` · `UNKNOWN`
- **Eligibility (season-bound, policy-versioned)**: `VERIFIED_ELIGIBLE` ·
  `VERIFIED_NOT_ELIGIBLE` · `ELIGIBILITY_UNVERIFIED` · `NOT_ASSESSED`

---

## 4. What Changed (v2.0.0 → v2.1.0)

| Area | v2.0.0 (superseded) | v2.1.0 (current) |
|---|---|---|
| **Database DDL** | Table-level UNIQUE with `COALESCE(...)` expression (invalid in PostgreSQL); `deliveries` without FKs; soft `fielding_events.delivery_id`; false-claim defaults (`NOC DEFAULT TRUE`, `is_not_out DEFAULT TRUE`); decimal `overs_completed`; `runs_batter 0..6` cap | Unique **expression index** on `derived_features`; real FKs on partitioned `deliveries` (PG15+); composite `(delivery_id, season_year)` fielding FK; no-default/nullable unknowns; integer ball counts with derived over notation; overthrows allowed (DB findings DB-1…DB-13 resolved) |
| **Suspension model** | Competition-level `seasons.is_suspension` | Franchise-level **`team_season_participation`** (PARTICIPATING/SUSPENDED/NOT_ENTERED/UNKNOWN, evidence-bound) |
| **Membership model** | Six conflated classes | **Three independent dimensions** + versioned, season-bound **eligibility policies** |
| **PIRE** | "Biometric" corroboration; scores as calibrated | **Contextual attribute corroboration**; deterministic tiers; calibrated-only numeric confidence |
| **CDCRE** | Post-identity only (MIE circular dependency) | **Dual capability**: pre-identity `discover_candidates` + post-identity `discover_career` |
| **Entity count** | 27 | **31** (+ `team_season_participation`, `player_membership_state`, `player_eligibility`, `eligibility_policies`; `is_suspension` column removed) |
| **Metric governance** | Promised, not defined | **`docs/DATA_DICTIONARY.md`** (all B/W/F/M metrics, NOT_COMPUTABLE list incl. false shots) |
| **Data sources** | Generic descriptions; unqualified "open" claims | **`docs/DATA_SOURCE_REGISTER.md`** (verification statuses; local evidence 2026-11-10: 1,243/201/265/230, ODC-By, **no SMAT** locally; Kaggle/HawkeyeStats marked RESTRICTED/UNVERIFIED) |
| **Phase 0** | Marked COMPLETE (unsubstantiated) | Split: **0a documentation baseline COMPLETE** · **0b empirical data-source & licence audit OPEN / PARTIALLY_COMPLETE** |
| **Agent id** | `agent_cdcpre` | `agent_cdcre` (now 18 agents total, adding `agent_pvre` and `agent_doc_remediation`) |
| **Specialised Engines** | 6 engines | **7 specialised engines** (+ ENGINE 07 PVRE with Mode A & Mode B) |
| **Entity count** | 31 | **33 entities** (verified PostgreSQL core including `player_season_stats` and `player_match_stats`) |
| **Hackathon deliverable** | Not represented | **Top-10 youngest eligible uncapped candidates** spec + reproducible role-aware ranking methodology (PRD §4.3), strictly isolated from Mode A replacement comparisons |

Still **retained** from v1.0.0/v2.0.0: deterministic reproducibility, normalised core with
season partitioning, the immutable data lake, zero-fabrication, Super Over isolation, DLS
accounting, penalty-run exclusion, and ODC-By / CC-BY attribution. Auction valuation
(EAP/VORP), Monte Carlo, Playing XI / Impact Player optimizers remain **post-MVP
enhancements**.

---

## 5. Repository Layout

```
d:\New folder (2)\
├── .agents/teamwork/                    # Historical agent evidence (v1/v2 audits; preserved, not modified)
├── datasets/                            # [IMMUTABLE, UNTRACKED] Raw cricket datasets (see .gitignore)
│   ├── ipl_male_json/                   #   1,243 IPL match files (CricSheet JSON v1.3.0) + ODC-By LICENSE
│   ├── hnd_male_json/                   #   201 The Hundred match files
│   ├── icc_mens_cricket_world_cup_male_json/ # 265 ODI WC files (24 withheld by CricSheet policy)
│   └── icc_mens_t20_world_cup_male_json/     # 230 T20 WC files (29 withheld by CricSheet policy)
│   (local CricSheet lake holds 5,083 JSON files across 13 directories incl. 695 SMAT matches in datasets/sma_json/)
├── docs/                                # Authoritative documentation suite
│   ├── README.md                        #   Hub: pathways + traceability matrix
│   ├── PRD.md                           #   Requirements, workflow, PVRE dual-mode, Top-10 deliverable, AC-01…AC-30
│   ├── TRD.md                           #   MIE + 7 engine contracts (incl. PVRE), 5 support services, 33-entity DDL
│   ├── ARCHITECTURE.md                  #   14 Mermaid diagrams (DDL-mirrored ERD, PVRE flows) + 8 ADRs
│   ├── PHASES.md                        #   Phase 0a/0b + Phase 4B (PVRE) + 1–10 roadmap (MVP vs long-term)
│   ├── AGENTS.md                        #   18 agent contracts (`agent_pvre`, `agent_cdcre` etc.)
│   ├── AI_INSTRUCTIONS.md               #   Identity/membership/evidence mandates + domain rules R1..R22
│   ├── DATA_SOURCE_REGISTER.md          #   Source-to-field matrix, statuses, reconciliation, S1..S20
│   ├── DATA_DICTIONARY.md               #   Metric dictionary (B/W/F/M, R01..R06, D01..D16 + NOT_COMPUTABLE)
│   └── RANKING_SPEC.md                  #   Candidate ranking & replacement intelligence (RK-1.0.0, RE-1.0.0)
├── reports/DOCUMENTATION_REMEDIATION_AUDIT.md  # Remediation record + validation results + commit list
├── DOCUMENTATION_PRE_REMEDIATION_AUDIT.md       # Pre-remediation defect register with v2.2.0 supersession banner
├── PROJECT.md                           # Project charter (v2.2.0, supersedes the v1.0.0 spec)
└── README.md                            # This file
```

---

## 6. Documentation Suite

| Document | Purpose |
|---|---|
| [`docs/PRD.md`](docs/PRD.md) | Updated user experience (candidate-discovery-first workflow), PVRE dual-mode intelligence (Mode A replacement & Mode B uncapped), three-dimension membership, FR traceability, 11 Streamlit views, Top-10 hackathon spec, AC-01…AC-30. |
| [`docs/TRD.md`](docs/TRD.md) | MIE + 7 engine I/O contracts (incl. PVRE §9), SICE replacement comparison (§8.4), 5 support services, verified 33-entity DDL, negative-verification requirements, versioned eligibility policies, Streamlit requirements. |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Orchestration and data-flow: 14 Mermaid diagrams (DDL-mirrored 33-entity ERD, PVRE dual-mode flows), MIE/PIRE/TMVE/SICE/PVRE flows, 8 ADRs (incl. ADR-008). |
| [`docs/PHASES.md`](docs/PHASES.md) | Phase 0a/0b split + Phases 1–10 with objectives, subphases, dependencies, checkpoints, acceptance criteria, testing, status, and MVP split. |
| [`docs/AGENTS.md`](docs/AGENTS.md) | 18 specialised agent contracts mapped to MIE, the seven engines, support services, delivery & QA. |
| [`docs/AI_INSTRUCTIONS.md`](docs/AI_INSTRUCTIONS.md) | Identity, membership and evidence-verification mandates; domain rules; prohibitions; Streamlit standards. |
| [`docs/DATA_SOURCE_REGISTER.md`](docs/DATA_SOURCE_REGISTER.md) | Source-to-field mapping, verification statuses, match/delivery reconciliation plan, licence evidence. |
| [`docs/DATA_DICTIONARY.md`](docs/DATA_DICTIONARY.md) | Complete metric definitions (formula, numerator/denominator, source fields, null rules, samples, class). |
| [`docs/README.md`](docs/README.md) | Hub, reading pathways, cross-document traceability matrix, changelog. |

---

## 7. Installation & Execution (Planned)

The repository is at the **Greenfield Baseline** — no application code exists yet. The
following is the *planned* runbook; it is realised incrementally across Phases 1–9.

### 7.1 Prerequisites
- **Python** 3.11+ (engines, services, Streamlit app).
- **PostgreSQL 16+** (33-entity normalised core; partitioned-table FK support requires
  ≥ 15, target is 16).
- **Streamlit** (initial UI).
- **Git** for version control.

### 7.2 Planned Steps
1. **Database**: create the target database and apply the 33-entity DDL from
   [`docs/TRD.md §11`](docs/TRD.md#11-central-postgresql-16-database-schema-33-entities).
2. **Ingestion**: run the Phase 1 pipeline over `datasets/` into immutable staging
   (SHA-256 + quarantine; counts per `DATA_SOURCE_REGISTER.md §3`).
3. **Engines**: implement PIRE → TMVE → CDCRE → PVRE → CPPAE → CMIE → SICE and the MIE orchestrator
   (Phases 2–8).
4. **Streamlit app**: deliver the 11-view application consuming engine contracts (Phase 9).
5. **Run the Streamlit app** (planned):
   ```bash
   streamlit run app/streamlit/main.py
   ```

> No Streamlit deployment and no engine implementation are performed in this documentation
> remediation, per scope.

---

## 8. Current Implementation Status

```
========================================================================================
                 CURRENT STATUS: 100% GREENFIELD BASELINE (NO APPLICATION CODE)
========================================================================================
[STATUS: COMPLETE]            Phase 0a — Documentation baseline (suite + register + dictionary
                              + pre/post remediation audits)
[STATUS: OPEN / PARTIALLY_COMPLETE] Phase 0b — Empirical data-source & licence audit
                              (local evidence recorded 2026-11-10; external verification
                               of Kaggle/HawkeyeStats/Open-Meteo/official-record terms outstanding)
[STATUS: PLANNED]   Phase 1 — Historical Dataset Acquisition & Data Quality
[STATUS: PLANNED]   Phase 2 — Unified Database & Player Identity Resolution (33-entity DDL + PIRE)
[STATUS: PLANNED]   Phase 3 — TMVE (three dimensions + team_season_participation + policies)
[STATUS: PLANNED]   Phase 4 — CDCRE dual capability & external research
[STATUS: PLANNED - MVP] Phase 4B — PVRE Dual-Mode Research & Replacement Intelligence
[STATUS: PLANNED]   Phase 5 — CPPAE per DATA_DICTIONARY
[STATUS: PLANNED]   Phase 6 — CMIE provenance-tiered context
[STATUS: PLANNED]   Phase 7 — MIE + Player Profile Generation (Service B)
[STATUS: PLANNED]   Phase 8 — SICE + Team Builder (Service E)
[STATUS: PLANNED]   Phase 9 — Streamlit Application (11 views)
[STATUS: PLANNED]   Phase 10 — Hackathon Candidate Evaluation (Top-10) & Final Submission
========================================================================================
```

**Note for auditors & judges**: this repository is at an uncompromised **Greenfield
Baseline**. No application code exists. Phase 0b remains open; no dataset counts are
claimed beyond the locally verified figures in `DATA_SOURCE_REGISTER.md §3`.

---

## 9. Data Attribution & Licensing

### Data Sources & Trademarks
- **CricSheet (local `datasets/`)**: **ODC-By** — `LICENSE.txt` present and inspected in all
  four archives; attribution mandatory in all exports (verified locally 2026-11-10).
- **Open-Meteo historical weather**: **CC BY 4.0** (stated; terms to be re-verified at
  Phase 6) — labelled as macro-environmental context, never as direct pitch measurement.
- **Kaggle / HawkeyeStats**: **RESTRICTED / UNVERIFIED** — terms not yet evidenced; do not
  assume permissive reuse; see `DATA_SOURCE_REGISTER.md`.
- **BCCI / IPL / ESPNcricinfo / Cricbuzz**: fair-dealing & automated-access limits apply;
  per-claim provenance records required.
- **Proprietary hackathon dataset**: confidential; isolated from public outputs.
- **Trademarks**: "IPL", "BCCI", "Rajasthan Royals" and associated marks belong to their
  respective owners; used under hackathon fair-dealing for analytical research.

### Open-Source Software Libraries
The Phase 1A platform foundation utilizes the following open-source software packages under their respective permissive licenses:
- **supabase-py** (MIT License) — Official Python client library for Supabase PostgREST, Auth, and Storage.
- **pydantic** (MIT License) — Data validation and contract specification using Python type annotations.
- **pydantic-settings** (MIT License) — Typed application settings management and environment parsing.
- **python-dotenv** (BSD-3-Clause License) — Parsing of `.env` configuration files for local development.
- **psycopg2-binary** (LGPL-3.0 with OpenSSL exception) — PostgreSQL adapter for Python database connectivity.
- **pytest** (MIT License) — Modern Python testing framework.
- **pytest-asyncio** (Apache-2.0 License) — Asyncio runtime support for pytest test fixtures.
- **mypy** (MIT License) — Static type analysis and verification.
- **ruff** (MIT / Apache-2.0 License) — High-performance Python linter and code formatter.
- **hatchling** (MIT License) — Extensible build backend for PEP 517 / PEP 621 Python packaging.

---

## 10. Recommended Next Implementation Task

**Complete Phase 0b, then start Phase 1**: close the external-source licence/coverage
verification (Kaggle S6/S7, HawkeyeStats S8, Open-Meteo S9, official records S10–S12 —
dated evidence rows in `data_sources`), then deploy the Phase 1 ingestion pipeline over
`datasets/` (verified counts 1,243/201/265/230; SMAT gap recorded). The immediate schema
gate is the Phase 2 migration validation of the 33-entity DDL (partitioned `deliveries`
FKs, `derived_features` expression index, composite fielding link).
