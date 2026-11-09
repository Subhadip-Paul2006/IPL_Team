# RR Squad Intelligence & Team Composition Platform
## Authoritative Engineering Documentation Suite & Navigation Hub

**Project**: RR Squad Intelligence & Team Composition Platform
**Competition**: IPL 2027 Hackathon
**Target Franchise**: Rajasthan Royals (RR)
**Document Suite Version**: 2.0.0-ARCH-REVISION
**Status**: `[STATUS: ACTIVE BASELINE - GREENFIELD IMPLEMENTATION TARGET]`
**Date**: November 2026
**Primary Authors**: Principal Software Architect, Sports Data Engineer, Cricket Analytics Researcher, Technical Documentation Engineer

> **Revision Note (v2.0.0)**: This suite was revised to describe the evolved product — the
> **RR Squad Intelligence & Team Composition Platform** — with the **Mother Intelligence
> Engine (MIE)** orchestrating **six specialised engines** and **five support services**,
> delivered initially through a **Streamlit** application. See the changelog (§7) for the full
> list of changes from v1.0.0.

---

## 1. Documentation Suite Overview & Purpose

This documentation suite is the definitive engineering blueprint for the **RR Squad Intelligence
& Team Composition Platform**. The platform:

- Identifies any cricket player from a user-supplied name (**PIRE**).
- Verifies whether the player represented Rajasthan Royals, distinguishing **historical RR
  players from current squad members** via a **six-class membership taxonomy** (**TMVE**),
  with the RR 2016–2017 suspension represented separately and IPL 2027 treated as a future
  target season.
- Discovers the player's complete career across competitions with **four-state coverage
  tracking** and provenance-recorded external research (**CDCRE**).
- Generates evidence-backed performance profiles (**CPPAE**) and contextual match intelligence
  (**CMIE**).
- Builds user teams and evaluates the complete composition (**SICE** + **Team Builder Service**).
- Delivers a unified, provenance-traced player intelligence report (**MIE** + **Service B/C**).

The **initial product interface is Streamlit**; the analytical core is **frontend-agnostic** so
a future Next.js frontend can reuse the same engine contracts. Raw data lives in `datasets/`.

Prior to writing application code, every requirement, engine contract, database table,
orchestration flow, agent responsibility, and implementation phase is specified in this suite.
**The product must never automatically assume that an unknown player is uncapped** — unknown
players are `UNVERIFIED` until established otherwise.

```
+----------------------------------------------------------------------------------------------------+
|                        DOCUMENTATION SUITE ARCHITECTURAL MAP (REVISED)                            |
+----------------------------------------------------------------------------------------------------+
|   ROOT OVERVIEW & AUDIT INDEX                                                                      |
|   └── ../README.md (Product overview, architecture summary, feature inventory, status)            |
|                                                                                                    |
|   DOCUMENTATION HUB (You Are Here)                                                                 |
|   └── docs/README.md (Navigation hub, reading pathways, traceability matrix)                       |
|                                                                                                    |
|   BUSINESS & PRODUCT SPECIFICATION                                                                 |
|   └── docs/PRD.md (Personas, user workflow, 6 engines + 5 services as FRs, 11 Streamlit views,    |
|                    MVP vs post-MVP scope, acceptance criteria)                                     |
|                                                                                                    |
|   TECHNICAL SPECIFICATION & DATA MODEL                                                             |
|   └── docs/TRD.md (MIE + 6 engine I/O contracts, 5 support services, 27-entity DDL,               |
|                    membership taxonomy, Streamlit requirements, frontend-agnostic contracts)       |
|                                                                                                    |
|   SYSTEM ARCHITECTURE & VISUAL BLUEPRINTS                                                          |
|   └── docs/ARCHITECTURE.md (10 Mermaid diagrams: orchestration, MIE workflow, PIRE/TMVE flows,    |
|                    ingestion/provenance, analytics, 27-entity ERD, SICE flow, Streamlit tier,     |
|                    evidence flow; ADR-001..007)                                                    |
|                                                                                                    |
|   EXECUTION ROADMAP & VERIFICATION GATES                                                           |
|   └── docs/PHASES.md (Phases 0–10, dependencies, checkpoints, MVP vs long-term split)              |
|                                                                                                    |
|   MULTI-AGENT OPERATING CONSTITUTION                                                               |
|   └── docs/AGENTS.md (16 agent contracts mapped to MIE, 6 engines, 5 services, delivery & QA)      |
|                                                                                                    |
|   ENGINEERING DIRECTIVES & STATISTICAL GUARDRAILS                                                  |
|   └── docs/AI_INSTRUCTIONS.md (Identity, membership & evidence mandates; 12 domain rules;          |
|                    14 prohibitions; Streamlit standards)                                           |
+----------------------------------------------------------------------------------------------------+
```

---

## 2. Core Documentation Index

| Document | Title & Subtitle | Primary Target Audience | Core Scope & Key Contents | Key Artifacts |
|---|---|---|---|---|
| [**`PRD.md`**](./PRD.md) | **Product Requirements Document**<br>*(Squad Intelligence & Team Composition)* | Franchise CEO, Head of Cricket Ops, Squad Strategists, Product Managers | Product vision, six-class membership semantics, user workflow, functional requirements by engine, 11 Streamlit views, MVP vs post-MVP scope, acceptance criteria AC-01…AC-14 | Workflow diagram, FR sets per engine, acceptance matrix |
| [**`TRD.md`**](./TRD.md) | **Technical Requirements Document**<br>*(MIE + 6 Engines + 5 Services + 27-Entity DDL)* | Principal Architects, Data Engineers, Backend Engineers, DBA | MIE orchestration contract, PIRE/TMVE/CDCRE/CPPAE/CMIE/SICE I/O contracts, support services, 27-entity PostgreSQL 16 DDL, membership taxonomy, Streamlit requirements, frontend-agnostic API surface | Engine I/O contracts, 27-entity DDL, API table |
| [**`ARCHITECTURE.md`**](./ARCHITECTURE.md) | **System Architecture Specification**<br>*(10 Mermaid Diagrams + 7 ADRs)* | Solutions Architects, Tech Leads, Full-Stack & Data Engineers | Orchestration architecture, MIE end-to-end workflow, PIRE/TMVE decision flows, ingestion/provenance, 27-entity ERD, SICE evaluation flow, Streamlit tier, evidence flow; ADR-001..007 | 10 Mermaid diagrams, 7 ADRs |
| [**`PHASES.md`**](./PHASES.md) | **Engineering Implementation Roadmap**<br>*(Phases 0 to 10)* | Technical PMs, Engineering Leads, QA Engineers | 11-phase lifecycle with objectives, subphases, inputs/outputs, dependencies, checkpoints, acceptance criteria, testing requirements, completion status; MVP vs long-term split; risk matrix | Phase dependency graph, status matrix, risk register |
| [**`AGENTS.md`**](./AGENTS.md) | **Multi-Agent Operating Constitution**<br>*(16 Agent Contracts)* | AI System Engineers, Orchestrators, Tech Leads | One agent per engine + MIE + governance; support-service agents; delivery/QA agents; conflict-resolution ladder | 16 agent contracts, escalation ladder |
| [**`AI_INSTRUCTIONS.md`**](./AI_INSTRUCTIONS.md) | **AI Architectural Principles & Domain Guardrails** | AI Agents, Engineers, Code Reviewers | Identity/membership/evidence mandates, 12 domain rules, 14 prohibited practices, Streamlit standards, licensing & confidentiality | Rule tables, prohibition list |

---

## 3. Stakeholder Reading Pathways

### Pathway 1: Franchise Leadership & Chief Executive (~25 min)
1. [`PRD.md §1 & §3`](./PRD.md#1-executive-summary--problem-statement) — product vision, historical
   context, hackathon alignment.
2. [`PRD.md §2`](./PRD.md#2-target-users--stakeholder-personas) — persona hierarchy.
3. [`PRD.md §4 & §5`](./PRD.md#4-user-workflow-primary) — user workflow and engine-level
   functional requirements.
4. [`PHASES.md §1`](./PHASES.md#1-executive-roadmap-overview--dependency-graph) — roadmap and MVP
   split.
- **Decisions enabled**: squad-direction approval, risk tolerance for unverified players,
  verification-policy sign-off.

### Pathway 2: Lead Cricket Analyst & Squad Strategist (~45 min)
1. [`PRD.md §1.2–§1.4`](./PRD.md#1-executive-summary--problem-statement) — why naive team building
   fails; membership semantics.
2. [`TRD.md §3–§8`](./TRD.md#3-engine-01--player-identity-resolution-engine-pire) — engine
   contracts (PIRE → SICE).
3. [`TRD.md §10`](./TRD.md#10-central-normalised-postgresql-database-schema-27-entities) — data
   model behind the analytics.
4. [`AI_INSTRUCTIONS.md §4–§5`](./AI_INSTRUCTIONS.md#4-identity-membership--evidence-verification-mandates) —
   identity/membership/evidence mandates and domain rules.
- **Decisions enabled**: team composition strategy, candidate-vs-incumbent comparison policy,
   verification depth.

### Pathway 3: Principal Architect & Backend/Data Engineers (~60 min)
1. [`TRD.md §1–§2`](./TRD.md#1-system-overview--technical-architecture) — subsystems and MIE.
2. [`TRD.md §10`](./TRD.md#10-central-normalised-postgresql-database-schema-27-entities) — 27-entity DDL.
3. [`ARCHITECTURE.md §2`](./ARCHITECTURE.md#2-system-architecture-diagrams) — all 10 diagrams.
4. [`ARCHITECTURE.md §3`](./ARCHITECTURE.md#3-architectural-decision-records-adrs) — ADR-001..007.
5. [`PHASES.md §3–§12`](./PHASES.md#3-phase-1--historical-dataset-acquisition-and-data-quality) —
   per-phase tasks and gates.
- **Decisions enabled**: schema sequencing, engine contract finalisation, MIE routing,
  partitioning strategy.

### Pathway 4: Data Engineers & ETL Pipeline Specialists (~50 min)
1. [`TRD.md §9`](./TRD.md#9-support-services) — ingestion, provenance, quality/coverage services.
2. [`TRD.md §10`](./TRD.md#10-central-normalised-postgresql-database-schema-27-entities) — raw /
   normalised / derived separation.
3. [`ARCHITECTURE.md §2.5 & §2.10`](./ARCHITECTURE.md#25-diagram-5-data-ingestion--provenance-architecture) —
   ingestion/provenance and evidence-flow diagrams.
4. [`AI_INSTRUCTIONS.md §2.3 & §6`](./AI_INSTRUCTIONS.md#23-read-only-immutable-data-lake) —
   immutable data lake; confidentiality of the hackathon dataset.
- **Decisions enabled**: parser design, quarantine policy, coverage-state backfill, provenance
  record lifecycles.

### Pathway 5: Hackathon Judges & Technical Auditors (~40 min)
1. [`../README.md`](../README.md) — product overview and current status.
2. [`docs/README.md`](./README.md) — this hub + traceability matrix (§4).
3. [`PRD.md §8`](./PRD.md#8-acceptance-criteria) — acceptance criteria AC-01…AC-14.
4. [`TRD.md §4 & §10`](./TRD.md#4-engine-02--team-membership-verification-engine-tmve) —
   membership taxonomy and schema integrity.
5. [`PHASES.md §1 & §13`](./PHASES.md#13-cross-phase-risk-assessment--mitigation) — roadmap,
   MVP split, risk register.
6. [`AGENTS.md`](./AGENTS.md) & [`AI_INSTRUCTIONS.md`](./AI_INSTRUCTIONS.md) — operating
   constitution and guardrails.
- **Decisions enabled**: holistic scoring of domain rigor, evidence integrity, and engineering
  maturity.

---

## 4. Cross-Document Traceability Matrix (Revised Feature Set)

| Feature ID | Feature | Defining PRD Section | TRD Contract | Architecture Diagram | Implementation Phase | Responsible Agent |
|---|---|---|---|---|---|---|
| **F-E1** | Player Identity Resolution (PIRE) | [PRD §5.1](./PRD.md#51-player-identity-resolution-pire) | [TRD §3](./TRD.md#3-engine-01--player-identity-resolution-engine-pire) | [ARCH §2.3](./ARCHITECTURE.md#23-diagram-3-player-identity-resolution-pire-workflow) | [Phase 2](./PHASES.md#4-phase-2--unified-database-and-player-identity-resolution) | `agent_pire` |
| **F-E2** | Team Membership Verification (TMVE) | [PRD §5.2](./PRD.md#52-team-membership-verification-tmve) | [TRD §4](./TRD.md#4-engine-02--team-membership-verification-engine-tmve) | [ARCH §2.4](./ARCHITECTURE.md#24-diagram-4-team-membership-verification-tmve-decision-flow) | [Phase 3](./PHASES.md#5-phase-3--team-membership-verification-engine) | `agent_tmve` |
| **F-E3** | Career Discovery & Coverage (CDCRE) | [PRD §5.3](./PRD.md#53-career-discovery--competition-research-cdcpre) | [TRD §5](./TRD.md#5-engine-03--career-discovery--competition-research-engine-cdcpre) | [ARCH §2.2](./ARCHITECTURE.md#22-diagram-2-mie-orchestration-workflow-end-to-end-player-intelligence) | [Phase 4](./PHASES.md#6-phase-4--career-discovery-and-external-research) | `agent_cdcpre` |
| **F-E4** | Performance Analytics (CPPAE) | [PRD §5.4](./PRD.md#54-complete-player-performance-analytics-cppae) | [TRD §6](./TRD.md#6-engine-04--complete-player-performance-analytics-engine-cppae) | [ARCH §2.6](./ARCHITECTURE.md#26-diagram-6-performance-analytics--derived-feature-flow) | [Phase 5](./PHASES.md#7-phase-5--complete-player-performance-analytics) | `agent_cppae` |
| **F-E5** | Contextual Match Intelligence (CMIE) | [PRD §5.5](./PRD.md#55-contextual-match-intelligence-cmie) | [TRD §7](./TRD.md#7-engine-05--contextual-match-intelligence-engine-cmie) | [ARCH §2.6](./ARCHITECTURE.md#26-diagram-6-performance-analytics--derived-feature-flow) | [Phase 6](./PHASES.md#8-phase-6--contextual-match-intelligence) | `agent_cmie` |
| **F-E6** | Squad Intelligence & Composition (SICE) | [PRD §5.6](./PRD.md#56-squad-intelligence--composition-sice) | [TRD §8](./TRD.md#8-engine-06--squad-intelligence--composition-engine-sice) | [ARCH §2.8](./ARCHITECTURE.md#28-diagram-8-squad-intelligence--composition-sice-evaluation-flow) | [Phase 8](./PHASES.md#10-phase-8--squad-intelligence-and-composition) | `agent_sice` |
| **F-O1** | MIE Orchestration & Unified Report | [PRD §4](./PRD.md#4-user-workflow-primary) | [TRD §2](./TRD.md#2-mother-intelligence-engine-mie--central-orchestrator) | [ARCH §2.2 & §2.10](./ARCHITECTURE.md#22-diagram-2-mie-orchestration-workflow-end-to-end-player-intelligence) | [Phase 7](./PHASES.md#9-phase-7--player-profile-generation) | `agent_mie_orchestration` |
| **F-S1** | Data Ingestion Service (A) | [PRD §5.7](./PRD.md#57-support-services) | [TRD §9.1](./TRD.md#9-support-services) | [ARCH §2.5](./ARCHITECTURE.md#25-diagram-5-data-ingestion--provenance-architecture) | [Phase 1](./PHASES.md#3-phase-1--historical-dataset-acquisition-and-data-quality) | `agent_data_ingestion` |
| **F-S2** | Player Profile Generator (B) | [PRD §5.7](./PRD.md#57-support-services) | [TRD §9.2](./TRD.md#9-support-services) | [ARCH §2.1](./ARCHITECTURE.md#21-diagram-1-high-level-orchestration-architecture) | [Phase 7](./PHASES.md#9-phase-7--player-profile-generation) | `agent_profile_generator` |
| **F-S3** | Source Verification & Provenance (C) | [PRD §5.7](./PRD.md#57-support-services) | [TRD §9.3](./TRD.md#9-support-services) | [ARCH §2.10](./ARCHITECTURE.md#210-diagram-10-evidence--verification-flow-mie--provenance) | [Phases 4, 7](./PHASES.md#6-phase-4--career-discovery-and-external-research) | `agent_provenance` |
| **F-S4** | Data Quality & Coverage (D) | [PRD §5.7](./PRD.md#57-support-services) | [TRD §9.4](./TRD.md#9-support-services) | [ARCH §2.5](./ARCHITECTURE.md#25-diagram-5-data-ingestion--provenance-architecture) | [Phase 1 (all phases)](./PHASES.md#3-phase-1--historical-dataset-acquisition-and-data-quality) | `agent_data_quality` |
| **F-S5** | Team Builder Service (E) | [PRD §5.7](./PRD.md#57-support-services) | [TRD §9.5](./TRD.md#9-support-services) | [ARCH §2.1 & §2.8](./ARCHITECTURE.md#21-diagram-1-high-level-orchestration-architecture) | [Phase 8](./PHASES.md#10-phase-8--squad-intelligence-and-composition) | `agent_team_builder` |
| **F-U1** | Streamlit 11-View Application | [PRD §5.8 & §6](./PRD.md#6-streamlit-views-ui-requirements) | [TRD §12](./TRD.md#12-streamlit-presentation-requirements) | [ARCH §2.9](./ARCHITECTURE.md#29-diagram-9-streamlit-presentation-tier) | [Phase 9](./PHASES.md#11-phase-9--streamlit-application) | `agent_streamlit_app` |
| **F-D1** | 27-Entity PostgreSQL Core | [PRD §3.1](./PRD.md#31-strategic-product-objectives) | [TRD §10](./TRD.md#10-central-normalised-postgresql-database-schema-27-entities) | [ARCH §2.7](./ARCHITECTURE.md#27-diagram-7-central-database-entity-relationship-diagram-27-entities) | [Phase 2](./PHASES.md#4-phase-2--unified-database-and-player-identity-resolution) | `agent_chief_architect` |

---

## 5. Architectural Principles & Cross-Cutting Guardrails

All engineering artefacts must abide by the tenets in [`AI_INSTRUCTIONS.md`](./AI_INSTRUCTIONS.md):

1. **Deterministic reproducibility** for the deterministic (query-driven) path.
2. **Strict 3NF 27-entity relational core** with canonical `player_id` everywhere.
3. **Read-only immutable data lake** (`datasets/`); SHA-256 deduplication; quarantining.
4. **Zero statistical fabrication**; missing → `NULL`.
5. **Evidence & provenance first**: every external claim is provenance-tracked; CONFLICT routes
   to human review.
6. **Frontend-agnostic engines**: Streamlit now, Next.js later, same contracts.
7. **No LLM-dependence for correctness**: research output is flagged and review-gated.
8. **Identity**: never merge similar names; ambiguity → user clarification.
9. **Membership**: six-class taxonomy; squad inclusion ≠ appearance; historical ≠ current;
   RR 2016–2017 suspension and 2027-future represented separately.
10. **Evidence verification**: absence ≠ non-participation; unknown ≠ uncapped; weather ≠
    pitch measurement; no mental-state inference; no fabricated injuries.

---

## 6. Document Maintenance & Status Markings

- Status markings use `[STATUS: COMPLETE]`, `[STATUS: PLANNED]`, and
  `[STATUS: PLANNED - GREENFIELD BASELINE]` consistently.
- The repository remains at the **Greenfield Baseline**: Phase 0 (documentation) complete;
  Phases 1–10 planned.
- Root `PROJECT.md` is a legacy project-definition file and is superseded by the root
  `README.md` for status; it is retained for audit continuity.

---

## 7. Document Suite Changelog & Version Control

| Version | Release Date | Significant Changes | Gate Status |
|---|---|---|---|
| **1.0.0-PROD-SPEC** | November 2026 (early) | Initial suite: auction-war-room product, 7 modules + 1 subsystem, 20-entity schema, Next.js frontend, Phases 0–8, 14 agents. | SUPERSEDED |
| **2.0.0-ARCH-REVISION** | November 2026 (later) | Product re-centred as **RR Squad Intelligence & Team Composition Platform**: MIE + 6 engines (PIRE/TMVE/CDCRE/CPPAE/CMIE/SICE) + 5 services; six-class membership taxonomy; four-state career coverage; RR 2016–2017 suspension + 2027-future handling; 27-entity schema; Streamlit initial frontend with frontend-agnostic engine contracts; Phases 0–10 with MVP split; 16 agent contracts; strengthened identity/membership/evidence guardrails (12 domain rules, 14 prohibitions); data directory corrected to `datasets/`. | **APPROVED REVISION** |
