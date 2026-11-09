# RR Squad Intelligence & Team Composition Platform

**Focus Franchise**: Rajasthan Royals (RR) · **Competition**: IPL 2027 Hackathon
**Primary Interface (initial)**: Streamlit · **Future Frontend**: Next.js (engines are frontend-agnostic)
**Status**: `[STATUS: GREENFIELD BASELINE — PHASE 0 COMPLETE / PHASES 1–10 PLANNED]`

> **Product version 2.0.0 (architecture revision)**. This repository was re-centred from a
> historical auction-war-room analytics engine into the **RR Squad Intelligence & Team
> Composition Platform**. The full change set is summarised in §4 below and in
> [`docs/README.md §7`](docs/README.md#7-document-suite-changelog--version-control).

---

## 1. What This Product Is

The **RR Squad Intelligence & Team Composition Platform** turns a user-supplied player name
into a **verified, evidence-backed player intelligence report**, and evaluates teams the user
assembles. Its primary workflow is:

1. A user creates a team.
2. The user enters a cricket player's name.
3. The system **identifies** the player (Engine 01 — PIRE).
4. The system checks whether the player exists in the internal database.
5. Where necessary, the system performs **authorised external research** to discover and
   verify the player's identity and cricket history (Engine 03 — CDCRE).
6. The system determines whether the player has represented Rajasthan Royals
   (Engine 02 — TMVE).
7. It distinguishes **historical RR players from current RR squad members**.
8. It retrieves and analyses the player's cricket career (CDCRE).
9. It evaluates the player's performance, contribution and role
   (Engine 04 — CPPAE).
10. It presents an **evidence-backed player profile** (Mother Intelligence Engine — MIE).
11. The user adds the player to a team composition (Team Builder Service).
12. The **Squad Intelligence Engine** (Engine 06 — SICE) evaluates the complete team.

The platform supports **all** of the following player populations, and it **never automatically
assumes that an unknown player is an uncapped player** (unknown = `UNVERIFIED`):

- Existing RR players · Former RR players · Players who have never represented RR ·
  Domestic uncapped prospects · Players from other IPL franchises · International players ·
  Players whose identity or eligibility remains unverified.

---

## 2. Architecture at a Glance

A central **Mother Intelligence Engine (MIE)** orchestrates **six specialised engines** and
**five support services**, all reading a **27-entity 3NF PostgreSQL core**. The MIE never
invents statistics or makes unsupported membership decisions; it coordinates the engines,
merges their outputs, tracks verification status and source provenance, and returns structured
reports. Engines are **frontend-agnostic**: the initial UI is **Streamlit**, and a future
**Next.js** frontend reuses the same contracts.

```
┌────────────────────────────────────────────────────────────────────┐
│  Presentation (Streamlit initial / Next.js future)                  │
│  Team Builder · Search · Verification · Career · Analytics · SICE  │
└───────────────────────────────┬────────────────────────────────────┘
                                ▼
┌────────────────────────────────────────────────────────────────────┐
│  MOTHER INTELLIGENCE ENGINE (MIE) — orchestrates, merges, tracks  │
└──┬──────┬──────┬──────┬──────┬──────┬────────────────────────────┘
   ▼      ▼      ▼      ▼      ▼      ▼
 PIRE   TMVE   CDCRE  CPPAE  CMIE   SICE
 Eng01  Eng02  Eng03  Eng04  Eng05  Eng06
   └────┴────┴────┴────┴────┴────── Support Services A–E
   │
   ▼
 Central PostgreSQL 16 core (27 entities, 3NF)  ←  datasets/ (immutable)
```

### The six specialised engines
| Engine | Name | Purpose |
|---|---|---|
| **ENGINE 01 — PIRE** | Player Identity Resolution | Resolve a name to a canonical player ID (aliases, spelling, duplicates, DOB, disambiguation). |
| **ENGINE 02 — TMVE** | Team Membership Verification | Verify RR representation; six-class taxonomy; RR seasons vs current; verification hierarchy. |
| **ENGINE 03 — CDCRE** | Career Discovery & Competition Research | Complete career beyond RR; cross-competition coverage; external research; provenance. |
| **ENGINE 04 — CPPAE** | Complete Player Performance Analytics | Batting / bowling / fielding / wicketkeeping / match contribution, documented & format-aware. |
| **ENGINE 05 — CMIE** | Contextual Match Intelligence | Environmental & match conditions; five-tier provenance; weather ≠ pitch; no mental-state inference. |
| **ENGINE 06 — SICE** | Squad Intelligence & Composition | Role/depth/balance/duplication/gap analysis; comparisons; alternatives; evidence-backed recommendations. |

### The five support services
| Service | Name | Responsibility |
|---|---|---|
| **A** | Data Ingestion | Import CricSheet, Kaggle, HawkeyeStats, historical weather, official records, verified research. |
| **B** | Player Profile Generator | Standardised JSON/CSV exports from the central database. |
| **C** | Source Verification & Provenance | URL, provider, timestamp, licence, status, confidence, original record ID. |
| **D** | Data Quality & Coverage | Missing data, duplicates, conflicts, invalid associations, unavailable context. |
| **E** | Team Builder | User teams, add/remove, composition, roles, saved configurations. |

---

## 3. Historical Context (Rajasthan Royals)

- RR franchise membership analysis **begins with IPL 2008**; the first phase runs **2008–2015**.
- RR were **suspended for IPL 2016 and 2017** and returned in **2018**; the suspension period is
  represented separately (first-class state `seasons.is_suspension`), never filled with
  fabricated squad data.
- Post-return historical analysis covers **2018 onwards**; the primary post-return window is
  **2018–2026**.
- **IPL 2027 is a future target season**: it is treated as such until actual participation and
  squad records are verified.

The platform maintains **six separate membership classes** and assigns `CURRENT_SQUAD` **only**
with verified current-season squad evidence:

`CURRENT_SQUAD` · `HISTORICAL_RR_PLAYER` · `PREVIOUSLY_ASSOCIATED` · `NEVER_REPRESENTED_RR` ·
`UNVERIFIED` · `ELIGIBILITY_UNVERIFIED`

---

## 4. What Changed in This Revision (v1.0.0 → v2.0.0)

| Area | v1.0.0 (superseded) | v2.0.0 (current) |
|---|---|---|
| **Product centre** | Auction war-room (valuation, EAP/VORP, Monte Carlo) | Squad intelligence & team composition with verified identity / membership / career |
| **Orchestration** | Engines called directly by UI | **Mother Intelligence Engine (MIE)** central orchestrator |
| **Engines** | "7 analytical modules + 1 subsystem" | **6 specialised engines** (PIRE, TMVE, CDCRE, CPPAE, CMIE, SICE) + 5 services, each with I/O contracts |
| **Membership model** | Implicit (current squad assumed) | **Six-class taxonomy** + RR suspension + 2027-future + verified-evidence-only `CURRENT_SQUAD` |
| **Unknown players** | Treated as uncapped prospects | **Never assumed uncapped** → `UNVERIFIED` / `ELIGIBILITY_UNVERIFIED` |
| **Career coverage** | Presence/absence in dataset | **Four-state coverage** (verified / dataset-unavailable / not-established / confirmed-non-participation) |
| **Database** | 20 entities | **27 entities** (+ team history, wicketkeeping, awards, competition history, user teams, verification records) |
| **Primary UI** | Next.js 15 | **Streamlit** (initial); Next.js demoted to future, engine-agnostic |
| **Roadmap** | Phases 0–8 | **Phases 0–10** (membership engine, career discovery, Streamlit app, hackathon evaluation) |
| **Data location** | `CricSheet/` | `datasets/` |
| **Agent model** | 14 agents keyed to Next.js/FastAPI | **16 agents** mapped to MIE + 6 engines + 5 services + delivery/QA |
| **Guardrails** | 9 statistical commandments, 10 prohibitions | **12 domain rules, 14 prohibitions** incl. identity, membership & evidence mandates |

Still **retained** from v1.0.0 (now folded into the new architecture): deterministic
reproducibility, strict 3NF + partitioning, the immutable data lake, zero-fabrication,
Super Over isolation, DLS accounting, penalty-run exclusion, and ODC-By / CC BY 4.0
attribution. Auction valuation (EAP/VORP), Monte Carlo simulation, and the Playing XI / Impact
Player optimizers are **post-MVP enhancements**, not required for the hackathon submission.

---

## 5. Repository Layout

```
d:\New folder (2)\
├── .agents/teamwork/                    # Multi-agent working memory, plans, handoffs
├── datasets/                            # [IMMUTABLE] Raw cricket datasets (read-only)
│   ├── ipl_male_json/                   #   IPL 2008–2026 (JSON v1.3.0) + LICENSE/README
│   ├── icc_mens_t20_world_cup_male_json/  #   ICC T20 World Cup
│   ├── icc_mens_cricket_world_cup_male_json/ #  ICC ODI World Cup
│   └── hnd_male_json/                   #   The Hundred
├── docs/                                # Authoritative documentation suite (7 documents)
│   ├── README.md                        #   Documentation hub + reading pathways + traceability
│   ├── PRD.md                           #   Product requirements (workflow, FRs, views, ACs)
│   ├── TRD.md                           #   MIE + 6 engine contracts, 5 services, 27-entity DDL
│   ├── ARCHITECTURE.md                  #   10 Mermaid diagrams + 7 ADRs
│   ├── PHASES.md                        #   Phases 0–10 roadmap (MVP vs long-term)
│   ├── AGENTS.md                        #   16-agent operating constitution
│   └── AI_INSTRUCTIONS.md               #   Identity/membership/evidence mandates + domain rules
├── PROJECT.md                           # Legacy v1 project definition (retained for audit)
└── README.md                            # This file — product overview & current status
```

> Note: the v1.0.0 suite referenced a `CricSheet/` data directory. The data now lives in
> `datasets/` (git-ignored); all documentation has been updated to the new path.

---

## 6. Documentation Suite

| Document | Purpose |
|---|---|
| [`docs/PRD.md`](docs/PRD.md) | Updated user experience: workflow, personas, engine FRs, 11 Streamlit views, MVP scope, acceptance criteria. |
| [`docs/TRD.md`](docs/TRD.md) | All six engines + five services with documented I/O contracts; 27-entity DDL; membership taxonomy; Streamlit requirements. |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Orchestration and data-flow: 10 Mermaid diagrams, MIE workflow, PIRE/TMVE decision flows, 27-entity ERD, SICE flow, 7 ADRs. |
| [`docs/PHASES.md`](docs/PHASES.md) | Phases 0–10 with objectives, subphases, inputs/outputs, dependencies, checkpoints, acceptance criteria, testing, status, and the MVP split. |
| [`docs/AGENTS.md`](docs/AGENTS.md) | Specialised agent responsibilities mapped to MIE, the six engines, and the five services. |
| [`docs/AI_INSTRUCTIONS.md`](docs/AI_INSTRUCTIONS.md) | Enforces identity, membership, and evidence-verification guardrails (12 domain rules, 14 prohibitions). |
| [`docs/README.md`](docs/README.md) | Documentation hub, reading pathways, cross-document traceability matrix, changelog. |

---

## 7. Installation & Execution (Planned)

The repository is at the **Greenfield Baseline** — no application code exists yet. The
following is the *planned* runbook; it is realised incrementally across Phases 1–9.

### 7.1 Prerequisites
- **Python** 3.11+ (engines, services, Streamlit app).
- **PostgreSQL** 16+ (27-entity normalised core).
- **Streamlit** (initial UI).
- **Git** for version control.

### 7.2 Planned Steps
1. **Database**: create the target database and apply the 27-entity DDL from
   [`docs/TRD.md §10`](docs/TRD.md#10-central-normalised-postgresql-database-schema-27-entities).
2. **Ingestion**: run the Phase 1 ingestion pipeline over `datasets/` into immutable staging
   (SHA-256 + quarantine).
3. **Engines**: implement PIRE → TMVE → CDCRE → CPPAE → CMIE → SICE and the MIE orchestrator
   (Phases 2–8).
4. **Streamlit app**: deliver the 11-view application consuming engine contracts (Phase 9).
5. **Run the Streamlit app** (planned):
   ```bash
   streamlit run app/streamlit/main.py
   ```

> No Streamlit deployment and no engine implementation are performed in this documentation
> revision, per scope.

---

## 8. Current Implementation Status

```
========================================================================================
                      CURRENT STATUS: 100% GREENFIELD BASELINE
========================================================================================
[STATUS: COMPLETE]  Phase 0 — Documentation & Research Audit (all 7 docs + README)
[STATUS: PLANNED]   Phase 1 — Historical Dataset Acquisition & Data Quality
[STATUS: PLANNED]   Phase 2 — Unified Database & Player Identity Resolution (PIRE)
[STATUS: PLANNED]   Phase 3 — Team Membership Verification Engine (TMVE)
[STATUS: PLANNED]   Phase 4 — Career Discovery & External Research (CDCRE)
[STATUS: PLANNED]   Phase 5 — Complete Player Performance Analytics (CPPAE)
[STATUS: PLANNED]   Phase 6 — Contextual Match Intelligence (CMIE)
[STATUS: PLANNED]   Phase 7 — Player Profile Generation (MIE + Service B)
[STATUS: PLANNED]   Phase 8 — Squad Intelligence & Composition (SICE + Service E)
[STATUS: PLANNED]   Phase 9 — Streamlit Application
[STATUS: PLANNED]   Phase 10 — Hackathon Candidate Evaluation & Final Submission
========================================================================================
```

**Note for auditors & judges**: this repository is at an uncompromised **Greenfield Baseline**.
Phase 0 establishes the complete technical specification, engine contracts, relational schema,
and operating constitution *before* application code is written. All planned features remain
`[STATUS: PLANNED]`.

---

## 9. Data Attribution & Licensing

- **CricSheet** (in `datasets/`): **Open Data Commons Attribution License (ODC-By v1.0)** —
  attributed to [CricSheet.org](https://cricsheet.org) in all exports.
- **Open-Meteo historical weather**: **CC BY 4.0** — labelled as macro-environmental context,
  never as direct pitch-soil measurement.
- **Kaggle / HawkeyeStats**: open dataset / permissive research terms; provenance-tracked.
- **Proprietary hackathon dataset**: kept confidential and isolated from public outputs.
- **Trademarks**: "IPL", "BCCI", "Rajasthan Royals" and associated marks are the property of
  their respective owners; used under hackathon fair-dealing for analytical research.

---

## 10. Recommended Next Implementation Task

**Phase 2 — Unified Database & Player Identity Resolution**: deploy the 27-entity DDL and
implement the PIRE 4-tier resolution waterfall. This is the natural next step after the
Phase 1 ingestion baseline, because every downstream engine (TMVE, CDCRE, CPPAE, CMIE, SICE)
consumes canonical `player_id` values that PIRE produces.
