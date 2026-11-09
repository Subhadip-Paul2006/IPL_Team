# Rajasthan Royals Squad Intelligence & Historical Performance Engine
## Authoritative Engineering Documentation Suite & Navigation Hub

**Project**: Rajasthan Royals Squad Intelligence & Historical Performance Engine  
**Competition**: IPL 2027 Auction Scouting Hackathon  
**Target Franchise**: Rajasthan Royals (RR)  
**Document Suite Version**: 1.0.0-PROD-SPEC  
**Status**: `[STATUS: ACTIVE BASELINE - GREENFIELD IMPLEMENTATION TARGET]`  
**Date**: November 2026  
**Primary Authors**: Principal Software Architect, Lead Cricket Data Scientist, Sports Analytics Specialist, Technical Product Manager  

---

## 1. Documentation Suite Overview & Purpose

Welcome to the central technical documentation suite for the **Rajasthan Royals Squad Intelligence & Historical Performance Engine**. This documentation repository serves as the definitive engineering blueprint, mathematical specification, and operational constitution for an enterprise sports analytics and decision-support platform designed specifically for the **IPL 2027 Mega-Auction**.

Ahead of the 2027 auction cycle, franchise front offices operate under stringent regulatory and competitive pressures: an **INR 120.00 Crore salary purse cap**, a strict roster ceiling of 25 players (maximum 8 overseas, maximum 4 overseas in any starting XI), modern **Impact Player** tactical substitution rules, and high-stakes bidding dynamics. Furthermore, the Rajasthan Royals face the specific strategic imperative of optimizing their squad for their home fortress—**Sawai Mansingh Stadium (SMS) in Jaipur**—characterized by expansive boundary dimensions, severe evening dew in April/May, and distinct red-soil/black-soil bounce dynamics.

To address these challenges, this documentation suite establishes a 100% greenfield engineering specification. Prior to writing application code or executing data migrations, every business requirement, database table, mathematical formula, architectural boundary, agent responsibility, and implementation phase has been specified in exhaustive, production-grade detail.

```
+----------------------------------------------------------------------------------------------------+
|                             DOCUMENTATION SUITE ARCHITECTURAL MAP                                  |
+----------------------------------------------------------------------------------------------------+
|                                                                                                    |
|   ROOT OVERVIEW & AUDIT INDEX                                                                      |
|   └── README.md (Project Root, Tech Stack, Repo Map, Installation, Greenfield Baseline)             |
|                                                                                                    |
|   DOCUMENTATION HUB (You Are Here)                                                                 |
|   └── docs/README.md (Master Navigation Hub, Stakeholder Reading Pathways, Traceability Matrix)   |
|                                                                                                    |
|   BUSINESS & PRODUCT SPECIFICATION                                                                 |
|   └── docs/PRD.md (Product Requirements: Personas, 7 Analytical Modules, NFRs, Acceptance Criteria)|
|                                                                                                    |
|   TECHNICAL SPECIFICATION & DATA MODEL                                                             |
|   └── docs/TRD.md (Technical Requirements: 20-Entity PostgreSQL 16 DDL, APIs, Cache, Security)     |
|                                                                                                    |
|   SYSTEM ARCHITECTURE & VISUAL BLUEPRINTS                                                          |
|   └── docs/ARCHITECTURE.md (System Architecture: 10 Validated Mermaid Diagrams, Data Flows, ERD)   |
|                                                                                                    |
|   EXECUTION ROADMAP & VERIFICATION GATES                                                           |
|   └── docs/PHASES.md (Implementation Roadmap: Phases 0 to 8, Verification Gates, Deliverables)     |
|                                                                                                    |
|   MULTI-AGENT OPERATING CONSTITUTION                                                               |
|   └── docs/AGENTS.md (Operating Constitution: 14 Specialised AI Engineering Agent Contracts)       |
|                                                                                                    |
|   ENGINEERING DIRECTIVES & STATISTICAL GUARDRAILS                                                  |
|   └── docs/AI_INSTRUCTIONS.md (Supreme Directives: Determinism, Zero Fabrication, Cricket Integrity)|
+----------------------------------------------------------------------------------------------------+
```

---

## 2. Core Documentation Index

The table below provides direct links, formal scopes, primary target audiences, and key architectural artifacts for all six core technical documents in `docs/`:

| Document | Title & Subtitle | Primary Target Audience | Core Scope & Key Contents | Key Artifacts |
|---|---|---|---|---|
| [**`PRD.md`**](./PRD.md) | **Product Requirements Document (PRD)**<br>*(IPL 2027 Auction Scouting Spec)* | Franchise CEO, Head of Cricket Ops, Auction Strategists, Product Managers | Problem statement, RR franchise mandate, SMS Jaipur characteristics, 5 stakeholder personas, 7 core analytical modules, 25 functional features, NFRs, MVP scope, and acceptance criteria. | 25 Feature Specs, Persona Decision Hierarchy, Acceptance Criteria Matrix |
| [**`TRD.md`**](./TRD.md) | **Technical Requirements Document (TRD)**<br>*(20-Entity Database Schema DDL)* | Principal Software Architects, Data Engineers, Backend Engineers, DBA | End-to-end technical architecture, complete PostgreSQL 16 3NF schema DDL across 20 entities, seasonal partitioning, 4-tier Player Identity Resolution (PIR), mathematical formulas for 12 advanced metrics, FastAPI endpoint contracts, Redis caching, and error handling. | 20-Entity PostgreSQL DDL, Metric Math Formats, REST API Contracts |
| [**`ARCHITECTURE.md`**](./ARCHITECTURE.md) | **System Architecture & Technical Design Specification**<br>*(10 Mermaid Diagrams)* | Solutions Architects, Technical Leads, Full-Stack Engineers, System Integrators | High-level distributed architecture, 10 syntactically validated Mermaid diagrams covering data ingestion, ELT staging, contextual enrichment, PIR waterfall, analytics feature flow, complete database ERD, player profile generation, auction simulation, and UI flow. | 10 Syntactically Valid Mermaid Diagrams, Component Interaction Flows |
| [**`PHASES.md`**](./PHASES.md) | **Engineering Implementation Roadmap**<br>*(Phases 0 to 8)* | Technical Project Managers, Engineering Leads, Scrum Masters, QA Engineers | 9-phase sequential implementation lifecycle (Phase 0: Research & Audit [Complete] to Phase 8: Submission [Planned]), entry/exit gates, task breakdowns, verification methods, milestone mapping, and deliverable catalogs. | Phase Progression Timeline, Verification Checklists, Milestone Status |
| [**`AGENTS.md`**](./AGENTS.md) | **Multi-Agent Operating Constitution**<br>*(14 Specialised AI Engineering Agents)* | AI System Engineers, Multi-Agent Orchestrators, Tech Leads | Federated governance for 14 specialized AI engineering agents: Chief Architect, Cricket Research, Data Source Audit, Acquisition, Normalisation, PIR Specialist, Contextual Enrichment, Cricket Statistics, Historical Performance, QA, Backend, Frontend, Documentation, and Testing. | 14 Agent Contracts, Input/Output Boundaries, 5-Component Handoff Protocol |
| [**`AI_INSTRUCTIONS.md`**](./AI_INSTRUCTIONS.md) | **AI Architectural Principles, Coding Standards & Domain Guardrails** | AI Agents, Backend Developers, Data Scientists, Code Reviewers | Supreme engineering directives: deterministic reproducibility, strict 3NF core, read-only immutable data lake, zero statistical fabrication, domain-specific cricket rules (Super Over isolation, DLS adjustments, no zero-imputation), and strict prohibitions. | Coding Standards, Google-Style Docstring Templates, Prohibited Actions |

---

## 3. Stakeholder Reading Pathways

To maximize analytical utility and ensure efficient navigation across diverse executive, technical, and evaluation roles, five customized reading pathways have been defined. Each pathway outlines an optimal reading sequence, section-by-section focus areas, key business and technical decisions enabled, and an estimated reading time.

```
                                  STAKEHOLDER READING PATHWAYS
┌───────────────────────────────┐  ┌───────────────────────────────┐  ┌───────────────────────────────┐
│     Pathway 1: Leadership     │  │   Pathway 2: Cricket Analyst  │  │   Pathway 3: Arch & Backend   │
│   • Franchise CEO & Owners    │  │   • Lead Cricket Data Analyst │  │   • Principal Architect       │
│   • Head of Cricket Ops       │  │   • Auction Bidding Strategist│  │   • Backend Engineers & DBA   │
│   Time: ~25 mins              │  │   Time: ~45 mins              │  │   Time: ~60 mins              │
└──────────────┬────────────────┘  └──────────────┬────────────────┘  └──────────────┬────────────────┘
               │                                  │                                  │
               ▼                                  ▼                                  ▼
┌───────────────────────────────┐  ┌───────────────────────────────┐  ┌───────────────────────────────┐
│ • PRD §1 (Executive Summary)  │  │ • PRD §1.2 (RR Mandate & SMS) │  │ • TRD §1 (System Architecture)│
│ • PRD §2 (Personas Hierarchy) │  │ • PRD §4 (7 Core Modules)     │  │ • TRD §2 (20-Entity SQL DDL)  │
│ • PRD §4.5 (Auction Valuation)│  │ • TRD §6 (Statistical Formulas)│ │ • ARCH §2 (10 Mermaid Diags)  │
│ • PRD §4.6 (Squad Optimizer)  │  │ • ARCH §2.9 (Valuation Flow)  │  │ • AI_INST §2-§4 (Standards)   │
│ • PHASES §1 (Executive Roadmap│  │ • AI_INST §4 (Cricket Rules)  │  │ • PHASES §2-§10 (Phases 0-8)  │
└───────────────────────────────┘  └───────────────────────────────┘  └───────────────────────────────┘

┌───────────────────────────────┐  ┌───────────────────────────────┐
│     Pathway 4: Data & ETL     │  │   Pathway 5: Judges & Auditors│
│   • Data Engineers            │  │   • Hackathon Evaluation Panel│
│   • ETL Pipeline Specialists  │  │   • Independent Tech Auditors │
│   Time: ~50 mins              │  │   Time: ~40 mins              │
└──────────────┬────────────────┘  └──────────────┬────────────────┘
               │                                  │
               ▼                                  ▼
┌───────────────────────────────┐  ┌───────────────────────────────┐
│ • TRD §1.1 & §2 (Relational)  │  │ • Root README.md (Overview)   │
│ • TRD §3 (PIR Waterfall)      │  │ • docs/README.md (This Hub)   │
│ • TRD §4 (ELT & Quarantine)   │  │ • PRD §1 & §4 (Features)      │
│ • ARCH §2.2-§2.5 (Ingest Flows│  │ • TRD §2 (Schema Integrity)   │
│ • AGENTS §2 (Data Agents)     │  │ • ARCH §2 (10 Architecture)  │
│ • AI_INST §2.3 (Data Lake)    │  │ • PHASES §1 & §11 (Milestones)│
└───────────────────────────────┘  └───────────────────────────────┘
```

---

### Pathway 1: Franchise Leadership & Chief Executive
- **Target Audience**: Franchise CEO, Board of Directors, Ownership Group, Head of Cricket Operations.
- **Primary Objective**: Understand auction purse risk mitigation, ROI optimization under the ₹120 Cr cap, regulatory roster compliance, and competitive differentiation at SMS Jaipur.
- **Recommended Reading Order**:
  1. [`docs/PRD.md §1`](./PRD.md#1-executive-summary--problem-statement): Executive Summary, IPL 2027 Mega-Auction Dynamics, and the Rajasthan Royals Mandate.
  2. [`docs/PRD.md §2`](./PRD.md#2-target-users--stakeholder-personas): Persona Hierarchy and Decision Matrix for Leadership.
  3. [`docs/PRD.md §4.5`](./PRD.md#module-5-auction-valuation--market-economics): Auction Valuation, Expected Auction Price (EAP), and Role Scarcity Multipliers.
  4. [`docs/PRD.md §4.6`](./PRD.md#module-6-squad-simulation--tactical-scenarios): Playing XI Optimization, Impact Player Rules, and Monte Carlo Tournament Simulation.
  5. [`docs/PHASES.md §1`](./PHASES.md#1-executive-roadmap-overview): Executive Roadmap Overview and Phase Status Matrix.
- **Key Decisions Enabled**: Purse allocation strategy by player tier, retention vs auction budget balance, risk tolerance for high-variance foreign match-winners, and final sign-off on analytical squad composition.
- **Estimated Reading Time**: 25 minutes.

---

### Pathway 2: Lead Cricket Analyst & Auction Strategist
- **Target Audience**: Lead Cricket Data Scientist, Auction War-Room Bidding Lead, Performance Analysts, Strategy Coaches.
- **Primary Objective**: Inspect the underlying mathematical formulations, tactical matchup structures, spatial pitch/boundary parameters, and player valuation mechanics.
- **Recommended Reading Order**:
  1. [`docs/PRD.md §1.2 & §1.3`](./PRD.md#12-franchise-context-the-rajasthan-royals-mandate): SMS Jaipur Fortress Dynamics and the Failure of Traditional Cricket Metrics.
  2. [`docs/PRD.md §4`](./PRD.md#4-comprehensive-functional-requirements-fr-01-to-fr-25): In-depth review of all 7 Analytical Modules (Match Impact, Venues, Matchups, Fatigue, Valuation, Simulation, Scouting).
  3. [`docs/TRD.md §6`](./TRD.md#6-statistical-computation-engine--mathematical-models): Mathematical specifications for True Strike Rate (TSR), True Economy Rate (TER), Win Probability Added (WPA), and T20 WAR.
  4. [`docs/ARCHITECTURE.md §2.8 & §2.9`](./ARCHITECTURE.md#28-diagram-8-player-profile-generation-workflow): Multi-Dimensional Player Profiling and Auction Candidate Valuation workflows.
  5. [`docs/AI_INSTRUCTIONS.md §4`](./AI_INSTRUCTIONS.md#5-strict-statistical-correctness--domain-rules): Cricket Domain Guardrails (Super Over segregation, DLS par reconciliation, missing value handling).
- **Key Decisions Enabled**: War-room bidding price ceilings, real-time tactical pivot recommendations during live auction bids, target player shortlists based on micro-skills, and venue-specific matchup game-plans.
- **Estimated Reading Time**: 45 minutes.

---

### Pathway 3: Principal Software Architect & Backend Engineers
- **Target Audience**: Principal Systems Architect, Backend Software Engineers, Database Administrators (DBA), DevOps Engineers.
- **Primary Objective**: Understand system architecture, end-to-end data flows, database normalization, relational integrity, API contracts, caching topology, and coding standards.
- **Recommended Reading Order**:
  1. [`docs/TRD.md §1`](./TRD.md#1-system-overview--technical-architecture): Architectural Subsystems, Technology Stack, and Component Topology.
  2. [`docs/TRD.md §2`](./TRD.md#2-central-normalised-postgresql-database-schema-postgresql-16): Central 20-Entity PostgreSQL 16 Normalized Schema DDL, Partitioning, and Constraints.
  3. [`docs/ARCHITECTURE.md §2.1, §2.3, §2.7`](./ARCHITECTURE.md#21-diagram-1-high-level-system-architecture): High-Level Architecture, ETL Pipeline, and Complete Relational Database ERD.
  4. [`docs/TRD.md §7`](./TRD.md#7-api-specification-fastapi-architecture): FastAPI Endpoint Specifications, Request/Response Payloads, and Redis Caching.
  5. [`docs/AI_INSTRUCTIONS.md §2 & §3`](./AI_INSTRUCTIONS.md#2-core-architectural-tenets): Core Architectural Tenets, Python Standards, Pydantic v2 validation, and Database Migrations.
  6. [`docs/PHASES.md §2-§10`](./PHASES.md#2-phase-0-research-schema-audit--greenfield-baseline-setup): Detailed technical task breakdowns for Phases 0 through 8.
- **Key Decisions Enabled**: Database schema migration sequencing, connection pooling sizing, query indexing optimization, Redis TTL policies, API gateway error contracts, and partition pruning strategies.
- **Estimated Reading Time**: 60 minutes.

---

### Pathway 4: Data Engineers & ETL Pipeline Specialists
- **Target Audience**: Cricket Data Engineers, Data Pipeline Developers, Integration Specialists.
- **Primary Objective**: Master the multi-format ingestion pipelines, quarantine staging lake, cryptographic deduplication, and the 4-tier Player Identity Resolution (PIR) waterfall.
- **Recommended Reading Order**:
  1. [`docs/TRD.md §1.1 & §2.18-§2.20`](./TRD.md#11-architectural-subsystems): Data Ingestion Engine, `data_sources`, `source_records`, and `derived_features` schemas.
  2. [`docs/TRD.md §3`](./TRD.md#3-player-identity-resolution-specification): 4-Tier Player Identity Resolution (PIR) Waterfall Architecture and CricSheet hex hash disambiguation.
  3. [`docs/TRD.md §4`](./TRD.md#4-match--delivery-reconciliation-specification): Streaming Ingestion, SHA-256 Deduplication, Pydantic Quarantine Gates, and Batch Execution.
  4. [`docs/ARCHITECTURE.md §2.2, §2.4, §2.5`](./ARCHITECTURE.md#22-diagram-2-data-ingestion-architecture): Ingestion Pipeline, Environmental Enrichment, and PIR Waterfall Mermaid Diagrams.
  5. [`docs/AGENTS.md §2 (Agents 03, 04, 05, 06, 07, 10)`](./AGENTS.md#agent-03-data-source-audit-agent): Operational contracts for Data Governance and Pipeline Agents.
  6. [`docs/AI_INSTRUCTIONS.md §2.3`](./AI_INSTRUCTIONS.md#23-read-only-immutable-data-lake-quarantine-lake-architecture): Read-Only Immutable Data Lake & Quarantine Lake Architecture.
- **Key Decisions Enabled**: Ingestion parser design for JSON v1.3.0 and YAML v0.94, SHA-256 staging deduplication logic, alias registry reconciliation rules, and Open-Meteo weather API polling and backfill routines.
- **Estimated Reading Time**: 50 minutes.

---

### Pathway 5: Hackathon Evaluation Judges & Technical Auditors
- **Target Audience**: Hackathon Technical Evaluation Panel, Forensic Code Auditors, Sports Analytics Researchers.
- **Primary Objective**: Evaluate engineering rigor, mathematical validity, architectural completeness, greenfield integrity, adherence to cricket rules, and verification reproducibility.
- **Recommended Reading Order**:
  1. [`README.md`](../README.md): Project Overview, Vision, Strategic Problem Statement, Technology Stack, and Greenfield Baseline status.
  2. [`docs/README.md`](./README.md): This Navigation Hub and the Cross-Document Traceability Matrix below.
  3. [`docs/PRD.md §1 & §8`](./PRD.md#1-executive-summary--problem-statement): Strategic Vision, Scope Boundaries, and Acceptance Criteria.
  4. [`docs/TRD.md §2 & §6`](./TRD.md#2-central-normalised-postgresql-database-schema-postgresql-16): Relational Data Integrity, 20-Entity DDL, and Advanced Metric Formulations.
  5. [`docs/ARCHITECTURE.md §2`](./ARCHITECTURE.md#2-complete-system-architecture-diagrams-10-mermaid-specifications): Inspection of all 10 Mermaid architectural diagrams.
  6. [`docs/PHASES.md §1 & §11`](./PHASES.md#1-executive-roadmap-overview): Verification Checklists, Phase Completion Criteria, and Risk Mitigations.
  7. [`docs/AGENTS.md`](./AGENTS.md) & [`docs/AI_INSTRUCTIONS.md`](./AI_INSTRUCTIONS.md): Multi-Agent Operating Constitution, Integrity Mandate, and Prohibited Actions.
- **Key Decisions Enabled**: Holistic scoring of technical architecture, data modeling completeness, domain accuracy, engineering maturity, and presentation quality.
- **Estimated Reading Time**: 40 minutes.

---

## 4. Cross-Document Traceability Matrix

The matrix below provides complete end-to-end traceability across the entire engineering specification. It maps every product feature (from **F01** to **F25**) to its defining section in the **PRD**, the corresponding database tables and endpoints in the **TRD**, the visual design in **ARCHITECTURE.md**, the implementation tasks in **PHASES.md**, and the responsible AI agent in **AGENTS.md**.

| Feature ID | Feature Name | Category | PRD Section | TRD Database Tables & Endpoints | Architecture Diagram | Implementation Phase | Responsible Agent |
|---|---|---|---|---|---|---|---|
| **F01** | Ball-by-Ball Context Valuation | Match Impact | [PRD §4.1](./PRD.md#module-1-match-impact-engine) | `deliveries`, `derived_features`<br>`GET /api/v1/players/{id}/true-metrics` | [ARCH §2.6](./ARCHITECTURE.md#26-diagram-6-player-analytics-workflow) | [Phase 4 (P4-T01)](./PHASES.md#6-phase-4-player-profiles--core-statistical-engine) | `agent_cricket_statistics` |
| **F02** | Win Probability Added (WPA) & xR | Match Impact | [PRD §4.1](./PRD.md#module-1-match-impact-engine) | `deliveries`, `derived_features`<br>`GET /api/v1/matches/{id}/wpa-timeline` | [ARCH §2.6](./ARCHITECTURE.md#26-diagram-6-player-analytics-workflow) | [Phase 4 (P4-T02)](./PHASES.md#6-phase-4-player-profiles--core-statistical-engine) | `agent_cricket_statistics` |
| **F03** | Clutch Index & Leverage Analysis | Match Impact | [PRD §4.1](./PRD.md#module-1-match-impact-engine) | `deliveries`, `derived_features`<br>`GET /api/v1/players/{id}/clutch-index` | [ARCH §2.6](./ARCHITECTURE.md#26-diagram-6-player-analytics-workflow) | [Phase 4 (P4-T03)](./PHASES.md#6-phase-4-player-profiles--core-statistical-engine) | `agent_cricket_statistics` |
| **F04** | Pitch & Ground Behavioral Profiling | Venue Profiling | [PRD §4.2](./PRD.md#module-2-venue-profiling--environmental-engine) | `venues`, `pitch_conditions`<br>`GET /api/v1/venues/{id}/profile` | [ARCH §2.4](./ARCHITECTURE.md#24-diagram-4-contextual-enrichment-architecture) | [Phase 3 (P3-T02)](./PHASES.md#5-phase-3-contextual--environmental-enrichment) | `agent_contextual_enrichment` |
| **F05** | SMS Jaipur Fortress Engine | Venue Profiling | [PRD §1.2 & §4.2](./PRD.md#12-franchise-context-the-rajasthan-royals-mandate) | `venues`, `pitch_conditions`, `derived_features`<br>`GET /api/v1/venues/sms-jaipur/fortress-analytics` | [ARCH §2.4](./ARCHITECTURE.md#24-diagram-4-contextual-enrichment-architecture) | [Phase 3 (P3-T02)](./PHASES.md#5-phase-3-contextual--environmental-enrichment) | `agent_cricket_research` |
| **F06** | Environmental & Dew Factor Correlation | Venue Profiling | [PRD §4.2](./PRD.md#module-2-venue-profiling--environmental-engine) | `weather_conditions`, `deliveries`<br>`GET /api/v1/venues/{id}/dew-impact` | [ARCH §2.4](./ARCHITECTURE.md#24-diagram-4-contextual-enrichment-architecture) | [Phase 3 (P3-T01)](./PHASES.md#5-phase-3-contextual--environmental-enrichment) | `agent_contextual_enrichment` |
| **F07** | Batter vs Bowling Type Profiling | Tactical Matrix | [PRD §4.3](./PRD.md#module-3-tactical-matchups--mechanics) | `deliveries`, `derived_features`<br>`GET /api/v1/players/{id}/bowling-type-matrix` | [ARCH §2.6](./ARCHITECTURE.md#26-diagram-6-player-analytics-workflow) | [Phase 5 (P5-T01)](./PHASES.md#7-phase-5-historical-performance-analysis--tactical-matchup-engine) | `agent_historical_performance` |
| **F08** | Head-to-Head Batter vs Bowler Matrix | Tactical Matrix | [PRD §4.3](./PRD.md#module-3-tactical-matchups--mechanics) | `deliveries`, `derived_features`<br>`GET /api/v1/matchups/head-to-head` | [ARCH §2.6](./ARCHITECTURE.md#26-diagram-6-player-analytics-workflow) | [Phase 5 (P5-T02)](./PHASES.md#7-phase-5-historical-performance-analysis--tactical-matchup-engine) | `agent_historical_performance` |
| **F09** | Pitch Trajectory & Length Vulnerability | Tactical Matrix | [PRD §4.3](./PRD.md#module-3-tactical-matchups--mechanics) | `deliveries` (Hawkeye telemetry)<br>`GET /api/v1/players/{id}/trajectory-heatmap` | [ARCH §2.4](./ARCHITECTURE.md#24-diagram-4-contextual-enrichment-architecture) | [Phase 5 (P5-T03)](./PHASES.md#7-phase-5-historical-performance-analysis--tactical-matchup-engine) | `agent_cricket_research` |
| **F10** | Multi-Format Workload Engine | Workload & Fatigue | [PRD §4.4](./PRD.md#module-4-workload-fatigue--injury-tracking) | `bowling_spell`, `derived_features`<br>`GET /api/v1/players/{id}/workload-summary` | [ARCH §2.6](./ARCHITECTURE.md#26-diagram-6-player-analytics-workflow) | [Phase 6 (P6-T01)](./PHASES.md#8-phase-6-squad-intelligence-fatigue--workload-engine) | `agent_historical_performance` |
| **F11** | Schedule Congestion & Travel Strain | Workload & Fatigue | [PRD §4.4](./PRD.md#module-4-workload-fatigue--injury-tracking) | `matches`, `venues`, `derived_features`<br>`GET /api/v1/players/{id}/fatigue-index` | [ARCH §2.6](./ARCHITECTURE.md#26-diagram-6-player-analytics-workflow) | [Phase 6 (P6-T02)](./PHASES.md#8-phase-6-squad-intelligence-fatigue--workload-engine) | `agent_historical_performance` |
| **F12** | Injury History & Availability Logging | Workload & Fatigue | [PRD §4.4](./PRD.md#module-4-workload-fatigue--injury-tracking) | `player_injuries`, `player_availability`<br>`GET /api/v1/players/{id}/availability` | [ARCH §2.7](./ARCHITECTURE.md#27-diagram-7-central-database-entity-relationship-diagram-erd-covering-all-20-entities) | [Phase 6 (P6-T03)](./PHASES.md#8-phase-6-squad-intelligence-fatigue--workload-engine) | `agent_backend_engineering` |
| **F13** | Expected Auction Price (EAP) Modeling | Auction Valuation | [PRD §4.5](./PRD.md#module-5-auction-valuation--market-economics) | `derived_features`<br>`POST /api/v1/scouting/predict-eap` | [ARCH §2.9](./ARCHITECTURE.md#29-diagram-9-candidate-evaluation--auction-scouting-workflow) | [Phase 7 (P7-T01)](./PHASES.md#9-phase-7-candidate-evaluation--auction-valuation-engine) | `agent_cricket_statistics` |
| **F14** | Value Over Replacement Player (VORP) | Auction Valuation | [PRD §4.5](./PRD.md#module-5-auction-valuation--market-economics) | `derived_features`<br>`GET /api/v1/players/{id}/vorp-rating` | [ARCH §2.9](./ARCHITECTURE.md#29-diagram-9-candidate-evaluation--auction-scouting-workflow) | [Phase 7 (P7-T02)](./PHASES.md#9-phase-7-candidate-evaluation--auction-valuation-engine) | `agent_cricket_statistics` |
| **F15** | Role Scarcity & Premium Multipliers | Auction Valuation | [PRD §4.5](./PRD.md#module-5-auction-valuation--market-economics) | `derived_features`<br>`GET /api/v1/scouting/role-scarcity` | [ARCH §2.9](./ARCHITECTURE.md#29-diagram-9-candidate-evaluation--auction-scouting-workflow) | [Phase 7 (P7-T03)](./PHASES.md#9-phase-7-candidate-evaluation--auction-valuation-engine) | `agent_backend_engineering` |
| **F16** | Playing XI Constraint Optimizer | Squad Simulation | [PRD §4.6](./PRD.md#module-6-squad-simulation--tactical-scenarios) | `squad_memberships`, `players`<br>`POST /api/v1/squad/optimize-playing-xi` | [ARCH §2.10](./ARCHITECTURE.md#210-diagram-10-dashboard-interaction--ui-component-architecture) | [Phase 8 (P8-T02)](./PHASES.md#10-phase-8-interactive-dashboard-simulation--final-submission) | `agent_backend_engineering` |
| **F17** | Impact Player Deployment Engine | Squad Simulation | [PRD §4.6](./PRD.md#module-6-squad-simulation--tactical-scenarios) | `deliveries`, `matches`<br>`POST /api/v1/squad/impact-player-strategy` | [ARCH §2.10](./ARCHITECTURE.md#210-diagram-10-dashboard-interaction--ui-component-architecture) | [Phase 8 (P8-T02)](./PHASES.md#10-phase-8-interactive-dashboard-simulation--final-submission) | `agent_cricket_research` |
| **F18** | Monte Carlo Tournament Simulator | Squad Simulation | [PRD §4.6](./PRD.md#module-6-squad-simulation--tactical-scenarios) | `derived_features`<br>`POST /api/v1/simulation/tournament-campaign` | [ARCH §2.9](./ARCHITECTURE.md#29-diagram-9-candidate-evaluation--auction-scouting-workflow) | [Phase 8 (P8-T03)](./PHASES.md#10-phase-8-interactive-dashboard-simulation--final-submission) | `agent_backend_engineering` |
| **F19** | Cross-Competition Normalisation | Talent Scouting | [PRD §4.7](./PRD.md#module-7-talent-scouting--normalisation) | `competitions`, `derived_features`<br>`GET /api/v1/scouting/competition-equivalencies` | [ARCH §2.6](./ARCHITECTURE.md#26-diagram-6-player-analytics-workflow) | [Phase 7 (P7-T04)](./PHASES.md#9-phase-7-candidate-evaluation--auction-valuation-engine) | `agent_cricket_statistics` |
| **F20** | Diamond-in-the-Rough Scouting Filter | Talent Scouting | [PRD §4.7](./PRD.md#module-7-talent-scouting--normalisation) | `players`, `derived_features`<br>`POST /api/v1/scouting/diamond-filter` | [ARCH §2.9](./ARCHITECTURE.md#29-diagram-9-candidate-evaluation--auction-scouting-workflow) | [Phase 7 (P7-T04)](./PHASES.md#9-phase-7-candidate-evaluation--auction-valuation-engine) | `agent_cricket_research` |
| **F21** | Multi-Source Player Identity Resolution | Core Data | [PRD §4.8](./PRD.md#module-8-core-data-ingestion--lineage) | `players`, `player_aliases`<br>`POST /api/v1/admin/resolve-player-identity` | [ARCH §2.5](./ARCHITECTURE.md#25-diagram-5-player-identity-resolution-workflow) | [Phase 2 (P2-T02)](./PHASES.md#4-phase-2-central-normalised-database-schema--player-identity-resolution) | `agent_player_identity_resolution` |
| **F22** | Multi-Format Ingestion Engine | Data Ingestion | [PRD §4.8](./PRD.md#module-8-core-data-ingestion--lineage) | `source_records`, `data_sources`<br>`POST /api/v1/admin/ingest-batch` | [ARCH §2.2 & §2.3](./ARCHITECTURE.md#22-diagram-2-data-ingestion-architecture) | [Phase 1 (P1-T01-03)](./PHASES.md#3-phase-1-raw-data-acquisition--quarantine-lake-staging) | `agent_dataset_acquisition` |
| **F23** | DLS Par & Revised Target Reconciler | Data Ingestion | [PRD §5.1](./PRD.md#module-8-core-data-ingestion--lineage) | `matches`, `innings`<br>`GET /api/v1/matches/{id}/dls-context` | [ARCH §2.3](./ARCHITECTURE.md#23-diagram-3-raw-to-normalized-data-pipeline) | [Phase 2 (P2-T01)](./PHASES.md#4-phase-2-central-normalised-database-schema--player-identity-resolution) | `agent_cricket_research` |
| **F24** | Super Over Isolation & Accounting | Core Data | [PRD §5.1](./PRD.md#module-8-core-data-ingestion--lineage) | `innings`, `deliveries`<br>`GET /api/v1/players/{id}/super-over-ledger` | [ARCH §2.3](./ARCHITECTURE.md#23-diagram-3-raw-to-normalized-data-pipeline) | [Phase 4 (P4-T01)](./PHASES.md#6-phase-4-player-profiles--core-statistical-engine) | `agent_cricket_statistics` |
| **F25** | Central 20-Entity PostgreSQL Schema | Architecture | [PRD §7.1](./PRD.md#7-scope-boundaries-mvp-scope-vs-out-of-scope) | 20 Schema Tables<br>`GET /api/v1/system/schema-status` | [ARCH §2.7](./ARCHITECTURE.md#27-diagram-7-central-database-entity-relationship-diagram-erd-covering-all-20-entities) | [Phase 2 (P2-T01)](./PHASES.md#4-phase-2-central-normalised-database-schema--player-identity-resolution) | `agent_chief_architect` |

---

## 5. Architectural Principles & Cross-Cutting Guardrails

All engineering artifacts and future application code must strictly abide by the five core architectural tenets defined in [`docs/AI_INSTRUCTIONS.md`](./AI_INSTRUCTIONS.md):

1. **Deterministic Reproducibility**:
   - Any analytical feature vector, probabilistic valuation, or simulation output must yield bit-for-bit identical results when executed with the same raw seeds and explicit configuration parameters (`seed=42`).
   - Pseudo-random number generators without fixed integer seeds are strictly prohibited.
2. **Strict Third Normal Form (3NF) Relational Core**:
   - Primary operational match, delivery, and player records reside in PostgreSQL 16 enforcing strict 3NF.
   - Declarative seasonal partitioning isolates the high-volume `deliveries` table (>250,000 deliveries across IPL history).
   - Precomputed analytical rollups are stored in `derived_features` or materialized views—never via unnormalized operational mutations.
3. **Read-Only Immutable Data Lake (Quarantine Architecture)**:
   - The raw data directory (`CricSheet/`) is strictly read-only.
   - All ingestion streams pass through SHA-256 cryptographic deduplication. Any malformed payload is quarantined in `stg_quarantine_log` without breaking pipeline execution.
4. **Zero Statistical Fabrication & No Zero-Imputation**:
   - Missing data evaluates to `NULL`. The system never imputes unknown values with `0.0`.
   - Never confuse bowling style with delivery variation.
   - Never interpret Hawk-Eye post-shot ball tracking coordinates as fielder coordinates.
5. **Domain-Specific Cricket Integrity**:
   - Super Overs are segregated into dedicated extra innings records (`innings_type='SUPER_OVER'`).
   - Rain-curtailed matches are reconciled against Duckworth-Lewis-Stern (DLS) revised targets.
   - Penalty runs are excluded from bowler charges.

---

## 6. Document Suite Changelog & Version Control

| Version | Release Date | Authoring Agents | Significant Changes & Additions | Gate Status |
|---|---|---|---|---|
| **1.0.0-PROD-SPEC** | November 2026 | `agent_chief_architect`<br>`agent_cricket_research`<br>`agent_backend_engineering`<br>`agent_documentation` | Initial establishment of the complete engineering documentation suite: Product Requirements Document (`PRD.md`), Technical Requirements Document & 20-Entity DDL (`TRD.md`), System Architecture Specification & 10 Mermaid Diagrams (`ARCHITECTURE.md`), 9-Phase Implementation Roadmap (`PHASES.md`), 14-Agent Operating Constitution (`AGENTS.md`), AI Architectural Directives (`AI_INSTRUCTIONS.md`), and Documentation Hub (`docs/README.md`). Repository certified at 100% Greenfield Baseline. | **APPROVED SPECIFICATION** |
