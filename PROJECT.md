# Project: Rajasthan Royals Squad Intelligence & Historical Performance Engine (IPL 2027 Auction Scouting Hackathon)

## Architecture
- **Multi-Tier Analytical Architecture**: Client Presentation (Next.js 15, Tailwind CSS 3.4, Apache ECharts 5.5, Recharts 2.12, React Flow 11.11) <-> REST API & Service Layer (FastAPI, ASGI Uvicorn, Pydantic v2, Redis 7.2) <-> Analytics & Tactical Simulation Engine (Python 3.13 / 3.11+, NumPy 1.26+, Pandas 2.2+, SciPy) <-> Central Normalized Relational Core (PostgreSQL 16, 20 Discrete Entities, Declarative Partitioning) <-> Ingestion & Contextual Enrichment Pipeline (CricSheet JSON v1.3.0 / YAML v0.94, Kaggle Historicals, Open-Meteo Historical Weather, HawkeyeStats Tracking Telemetry).
- **Core Engineering Principles**:
  1. *Deterministic Reproducibility*: Every metric, feature vector, and valuation is bit-for-bit reproducible from raw source payloads with SHA-256 cryptographic digests and explicit pseudo-random generator seeds (`seed=42`).
  2. *Strict 3NF Relational Core*: Central PostgreSQL 16 schema enforces Third Normal Form across 20 entities with hard foreign keys, composite unique constraints, and domain check constraints.
  3. *Read-Only Immutable Data Lake*: The raw data directory (`CricSheet/`) is strictly read-only; all payloads pass through SHA-256 hashing into a staging lake with quarantine handling.
  4. *Zero Statistical Fabrication*: Missing metrics evaluate strictly to `NULL`. The system never imputes missing values as zero, never fabricates fictitious player records, and never confuses bowling style with delivery variation.
  5. *Domain-Specific Cricket Integrity*: Super Overs are segregated from career aggregates, DLS revised targets are normalized against match overs, penalty runs are excluded from bowler charges, and Hawkeye post-shot coordinates are never conflated with fielder coordinates.
  6. *Greenfield Baseline Governance*: The repository is at a 100% Greenfield Baseline where Phase 0 establishes the complete technical specification before application code is written. Planned features are rigorously demarcated with `[STATUS: PLANNED]`.

---

## Feature Inventory

| # | Feature | Category | Description | Assigned Milestone | Source Reference | Status |
|---|---------|----------|-------------|-------------------|------------------|--------|
| F01 | Ball-by-Ball Context Valuation | Match Impact | True Strike Rate (TSR) & True Economy Rate (TER) normalized against tournament phase pars (Powerplay, Middle 1, Middle 2, Death). | M1, M2 | PRD §4.1, TRD §6.1 | `[STATUS: PLANNED]` |
| F02 | Win Probability Added (WPA) & xR | Match Impact | Delivery-by-delivery state-space Win Probability model evaluating delta WP and Expected Runs (xR) based on score, balls remaining, wickets in hand, and required run rate. | M1, M2 | PRD §4.1, TRD §6.2 | `[STATUS: PLANNED]` |
| F03 | Clutch Index & Leverage Analysis | Match Impact | High-pressure leverage quantification filtering deliveries where Leverage Index (LI) > 1.5 to measure performance under acute match strain. | M1, M2 | PRD §4.1, TRD §6.3 | `[STATUS: PLANNED]` |
| F04 | Pitch & Ground Behavioral Profiling | Venue Profiling | Boundary geometry modeling (straight vs square dimensions), pitch soil taxonomy (red-soil bounce vs black-soil low-skid), and boundary-running coefficient. | M1, M2 | PRD §4.2, TRD §6.4 | `[STATUS: PLANNED]` |
| F05 | SMS Jaipur Fortress Engine | Venue Profiling | Sawai Mansingh Stadium home ground intelligence: large outfield dynamics (68–78m boundaries), running-between-wickets premium, and April–May diurnal temperature drops. | M1, M2 | PRD §1.2, TRD §6.4 | `[STATUS: PLANNED]` |
| F06 | Environmental & Dew Factor Correlation | Venue Profiling | Open-Meteo historical macro-meteorological integration (ambient temperature, relative humidity, dew point) modeling 2nd-innings dew impact on bowling grip and boundary ease. | M1, M2 | PRD §4.2, TRD §6.5 | `[STATUS: PLANNED]` |
| F07 | Batter vs Bowling Type Profiling | Tactical Matrix | Granular batting proficiency matrix evaluated against 6 distinct bowling archetypes (Right-Arm Fast, Left-Arm Fast, Off-Spin, Slow Left-Arm Orthodox, Leg-Break Googly, Left-Arm Wrist Spin). | M1, M2 | PRD §4.3, TRD §6.6 | `[STATUS: PLANNED]` |
| F08 | Head-to-Head Batter vs Bowler Matrix | Tactical Matrix | Pairwise historical matchup matrices between individual batters and bowlers with dismissal lineage, dot-ball percentage, and false-shot frequency. | M1, M2 | PRD §4.3, TRD §6.6 | `[STATUS: PLANNED]` |
| F09 | Pitch Trajectory & Length Vulnerability | Tactical Matrix | Hawkeye delivery tracking telemetry integration projecting pitch release speed, landing length zones (Yorker, Full, Good, Short, Bouncer), and batter dismissal heatmaps. | M1, M2 | PRD §4.3, TRD §6.7 | `[STATUS: PLANNED]` |
| F10 | Multi-Format Workload Engine | Workload & Fatigue | Cumulative bowling overs and spells logged across IPL, Syed Mushtaq Ali Trophy, ICC T20 World Cups, ODI World Cups, and The Hundred to monitor physical accumulation. | M1, M2 | PRD §4.4, TRD §6.8 | `[STATUS: PLANNED]` |
| F11 | Schedule Congestion & Travel Strain | Workload & Fatigue | Empirical fatigue decay curves modeling performance degradation resulting from compressed rest intervals (<48 hours) and multi-city transits across India. | M1, M2 | PRD §4.4, TRD §6.8 | `[STATUS: PLANNED]` |
| F12 | Injury History & Availability Logging | Workload & Fatigue | Historical injury records, downtime durations, recurrence risk flags, and international duty NOC calendar availability restrictions for overseas players. | M1, M2 | PRD §4.4, TRD §2.16 | `[STATUS: PLANNED]` |
| F13 | Expected Auction Price (EAP) Modeling | Auction Valuation | Elastic net and random forest regression models estimating the clearing auction price at the IPL 2027 Mega-Auction based on player age, role scarcity, and 3-year performance. | M1, M2 | PRD §4.5, TRD §6.9 | `[STATUS: PLANNED]` |
| F14 | Value Over Replacement Player (VORP) | Auction Valuation | T20 sabermetric adaptation quantifying runs and wickets contributed relative to a freely available domestic replacement player benchmark (baseline replacement index). | M1, M2 | PRD §4.5, TRD §6.9 | `[STATUS: PLANNED]` |
| F15 | Role Scarcity & Premium Multipliers | Auction Valuation | Dynamic valuation adjustments reflecting structural marketplace scarcity for high-demand tactical archetypes (Indian pace bowling all-rounders, elite death-overs finishers). | M1, M2 | PRD §4.5, TRD §6.9 | `[STATUS: PLANNED]` |
| F16 | Playing XI Constraint Optimizer | Squad Simulation | Constraint-satisfaction integer programming optimizer selecting the optimal starting XI under strict IPL regulations (maximum 4 overseas, minimum 1 wicketkeeper, minimum 5 bowlers). | M1, M2 | PRD §4.6, TRD §6.10 | `[STATUS: PLANNED]` |
| F17 | Impact Player Deployment Engine | Squad Simulation | Tactical decision model evaluating match state and pitch conditions to recommend the optimal 12th-man substitution from the nominated 5-player bench. | M1, M2 | PRD §4.6, TRD §6.10 | `[STATUS: PLANNED]` |
| F18 | Monte Carlo Tournament Simulator | Squad Simulation | 10,000-iteration tournament campaign engine projecting playoff qualification probability, net run rate distributions, and title odds under alternative auction acquisition rosters. | M1, M2 | PRD §4.6, TRD §6.10 | `[STATUS: PLANNED]` |
| F19 | Cross-Competition Normalisation | Talent Scouting | Equivalency modeling calibrating raw statistics from domestic competitions (Syed Mushtaq Ali, Ranji Trophy, U-19 World Cup, The Hundred) to the IPL difficulty tier. | M1, M2 | PRD §4.7, TRD §6.11 | `[STATUS: PLANNED]` |
| F20 | Diamond-in-the-Rough Scouting Filter | Talent Scouting | Algorithmic filter detecting high-upside domestic Indian talent (age <= 24, base auction bracket <= ₹50 Lakh) exhibiting elite isolated micro-skills (death economy, boundary percentage). | M1, M2 | PRD §4.7, TRD §6.11 | `[STATUS: PLANNED]` |
| F21 | Multi-Source Player Identity Resolution | Core Data | 4-tier waterfall identity resolution engine disambiguating aliases and names across providers, anchored by CricSheet unique hex hashes (`people.csv` registry). | M1, M2 | PRD §4.8, TRD §3 | `[STATUS: PLANNED]` |
| F22 | Multi-Format Ingestion Engine | Data Ingestion | High-throughput streaming loaders parsing CricSheet JSON v1.3.0 and legacy YAML v0.94 payloads with cryptographic SHA-256 deduplication and quarantine handling. | M2 | TRD §1.1, ARCH §2.2 | `[STATUS: PLANNED]` |
| F23 | DLS Par & Revised Target Reconciler | Data Ingestion | Interrupted match normalization reconciling rain-curtailed deliveries and adjusted target scores against Duckworth-Lewis-Stern par calculations. | M1, M2 | PRD §5.1, TRD §4.2 | `[STATUS: PLANNED]` |
| F24 | Super Over Isolation & Accounting | Core Data | Structural isolation of Super Over balls into dedicated extra innings records (`innings_type='SUPER_OVER'`), preventing distortion of regular 20-over career metrics. | M1, M2 | PRD §5.1, TRD §2.8 | `[STATUS: PLANNED]` |
| F25 | Central 20-Entity PostgreSQL Schema | Architecture | Enterprise 3NF relational schema encompassing 20 discrete entities with declarative seasonal partitioning on deliveries, domain check constraints, and composite indexes. | M2 | TRD §2, ARCH §2.7 | `[STATUS: PLANNED]` |

---

## Milestones

| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| **M1** | Product, Process & Agent Specifications | Author `docs/PRD.md`, `docs/PHASES.md`, `docs/AGENTS.md`, and `docs/AI_INSTRUCTIONS.md` establishing the complete business and governance baseline. | Workspace Inspection & Audit | **COMPLETE** |
| **M2** | Technical Architecture & Database Schema | Author `docs/TRD.md` (20-entity DDL) and `docs/ARCHITECTURE.md` (10 syntactically valid Mermaid diagrams). | M1 Complete | **COMPLETE** |
| **M3** | Repository Overview & Navigation Hub | Author root `README.md`, documentation hub `docs/README.md`, and root `PROJECT.md` synchronizing all specifications and cross-document links. | M1, M2 Complete | **IN_PROGRESS** |
| **M4** | Verification, Audit & Final Report | Multi-Agent review, empirical validation of links and diagrams, forensic audit verification, and executive handoff. | M1, M2, M3 Complete | **PLANNED** |

---

## Code Layout

```
d:\New folder (2)\
├── .agents/                                # Multi-Agent Framework & Working Memory
│   └── teamwork/                           # Agent working directories, plans, handoffs, dispatches
│       ├── orchestrator_1/                 # Master orchestrator tracking state & milestone gates
│       ├── worker_m1/                      # Milestone 1 specification artifacts
│       ├── worker_m2/                      # Milestone 2 technical architecture artifacts
│       └── worker_m3/                      # Milestone 3 root overview & documentation hub artifacts
├── CricSheet/                              # [IMMUTABLE READ-ONLY CACHE] Raw Cricket Datasets
│   ├── hnd_json/                           # The Hundred Ball-by-Ball Match Payloads (JSON v1.3.0)
│   ├── icc_mens_cricket_world_cup/         # ICC ODI World Cup Historical Payloads (YAML v0.94)
│   ├── icc_mens_t20_world_cup_json/        # ICC Men's T20 World Cup Payloads (JSON v1.3.0)
│   ├── ipl_json/                           # Indian Premier League 2008–2026 Payloads (JSON v1.3.0)
│   └── sma/                                # Syed Mushtaq Ali Trophy Domestic Payloads (YAML v0.94)
├── docs/                                   # Authoritative Engineering Documentation Suite
│   ├── README.md                           # Documentation Hub, Reading Pathways & Traceability Matrix
│   ├── PRD.md                              # Product Requirements Document (IPL 2027 Scouting Spec)
│   ├── TRD.md                              # Technical Requirements Document & 20-Entity PostgreSQL DDL
│   ├── ARCHITECTURE.md                     # System Architecture Specification (10 Mermaid Diagrams)
│   ├── PHASES.md                           # 9-Phase Engineering Implementation Roadmap (Phases 0 to 8)
│   ├── AGENTS.md                           # Multi-Agent Operating Constitution (14 AI Engineering Agents)
│   └── AI_INSTRUCTIONS.md                  # AI Architectural Principles, Coding Standards & Domain Guardrails
├── PROJECT.md                              # Root Project Definition, Feature Inventory & Milestone Matrix
└── README.md                               # Project Root Overview, Architecture & Evaluation Index
```

### Planned Implementation Layout (Phases 1 to 8)
When implementation code generation commences in subsequent phases, the application codebase will be organized into the following standardized subdirectories:

```
d:\New folder (2)\
├── backend/                                # [PLANNED - Phase 1+] FastAPI Application & Analytics Engine
│   ├── app/
│   │   ├── api/                            # REST Endpoints (v1/players, v1/scouting, v1/matches)
│   │   ├── core/                           # Configuration, Redis client, database session pooling
│   │   ├── models/                         # SQLAlchemy 2.0 ORM & Pydantic v2 domain schemas
│   │   ├── services/                       # Business logic (PIR waterfall, VORP, WPA, EAP regression)
│   │   └── simulation/                     # Monte Carlo tournament simulator & Playing XI optimizer
│   ├── db/
│   │   ├── migrations/                     # Alembic / Flyway declarative SQL migrations (V001__*.sql)
│   │   └── seeds/                          # Venue geometry seeds, reference pars, and competition tiers
│   ├── ingestion/                          # High-throughput ELT loaders (CricSheet, Weather, Hawkeye)
│   └── tests/                              # Unit, integration, and statistical invariant test suites
├── frontend/                               # [PLANNED - Phase 8] Next.js 15 Web Application
│   ├── src/
│   │   ├── app/                            # Next.js App Router (layout, page routes, loading states)
│   │   ├── components/                     # Tailwind UI components, ECharts spray charts, Recharts
│   │   ├── hooks/                          # React Query / SWR data fetching hooks
│   │   ├── lib/                            # API client, mathematical utilities, formatting helpers
│   │   └── types/                          # TypeScript 5.3 strict interfaces and domain types
│   ├── public/                             # Static assets, team crests, stadium boundary svgs
│   └── tests/                              # Vitest & Playwright end-to-end integration tests
└── scripts/                                # [PLANNED - Phase 1+] DevOps, validation & utility CLI tools
```
