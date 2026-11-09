# RR Squad Intelligence & Team Composition Platform
## Authoritative Engineering Documentation Suite & Navigation Hub

**Project**: RR Squad Intelligence & Team Composition Platform
**Competition**: IPL 2027 Hackathon (Rajasthan Royals scouting)
**Target Franchise**: Rajasthan Royals (RR)
**Document Suite Version**: 2.1.0-REMEDIATED
**Status**: `[STATUS: ACTIVE BASELINE - GREENFIELD IMPLEMENTATION TARGET]`
**Date**: November 2026
**Primary Authors**: Principal Software Architect, Sports Data Engineer, Cricket Analytics Researcher, Technical Documentation Engineer

> **Revision Note (v2.1.0, remediation)**: This suite now describes the remediated
> architecture: **31-entity PostgreSQL core**, the franchise-level
> **`team_season_participation`** model (replacing the competition-level suspension flag),
> **three-dimension membership + season-bound versioned eligibility** (replacing the
> conflated six-class taxonomy), PIRE **deterministic tiers with contextual attribute
> corroboration**, CDCRE **dual capabilities** (pre-identity candidate discovery +
> post-identity career retrieval), the `agent_cdcre` identifier, and two new governing
> documents: **`DATA_SOURCE_REGISTER.md`** and **`DATA_DICTIONARY.md`**. Phase 0 is split
> into **0a (COMPLETE)** and **0b (OPEN / PARTIALLY_COMPLETE)**.

---

## 1. Documentation Suite Overview & Purpose

This documentation suite is the definitive engineering blueprint for the **RR Squad
Intelligence & Team Composition Platform**. The platform:

- Identifies any cricket player from a user-supplied name (**PIRE**, deterministic tiers
  with contextual attribute corroboration).
- Verifies whether the player represented Rajasthan Royals across **three independent
  dimensions** (RR relationship · current status · season-bound, policy-versioned
  eligibility) via **TMVE**, with the RR 2016–2017 franchise suspension recorded in
  `team_season_participation` and IPL 2027 participation remaining unverified until
  authoritative evidence exists.
- Discovers the player's complete career across competitions with **four-state coverage
  tracking** and provenance-recorded external research (**CDCRE**, dual capability:
  pre-identity candidate discovery + post-identity career retrieval).
- Generates evidence-backed performance profiles (**CPPAE**, governed by
  `DATA_DICTIONARY.md`) and contextual match intelligence (**CMIE**, five provenance
  tiers).
- Builds user teams and evaluates the complete composition (**SICE** + **Team Builder
  Service**).
- Delivers a unified, provenance-traced player intelligence report (**MIE** +
  **Service B/C**).

The **initial product interface is Streamlit**; the analytical core is **frontend-agnostic**
so a future Next.js frontend can reuse the same engine contracts. Raw data lives in
`datasets/` (availability/licence evidence: `DATA_SOURCE_REGISTER.md §3`).

**The product must never automatically assume that an unknown player is uncapped** —
unknown players are `NOT_ASSESSED` (eligibility) / `RR_RELATIONSHIP_UNKNOWN` until
independently established.

```
+----------------------------------------------------------------------------------------------------+
|                        DOCUMENTATION SUITE ARCHITECTURAL MAP (REMediated)                          |
+----------------------------------------------------------------------------------------------------+
|   ROOT OVERVIEW & AUDIT INDEX                                                                      |
|   └── ../README.md (Product overview, architecture summary, status, v2.1.0 changes)                |
|                                                                                                    |
|   DOCUMENTATION HUB (You Are Here)                                                                 |
|   └── docs/README.md (Navigation hub, reading pathways, traceability matrix)                       |
|                                                                                                    |
|   BUSINESS & PRODUCT SPECIFICATION                                                                 |
|   └── docs/PRD.md (Personas, revised workflow, FRs with full traceability, 11 Streamlit views,     |
|                    hackathon Top-10 deliverable spec, MVP vs post-MVP, AC-01…AC-23)                |
|                                                                                                    |
|   TECHNICAL SPECIFICATION & DATA MODEL                                                             |
|   └── docs/TRD.md (MIE + 6 engine I/O contracts, 5 support services, 31-entity DDL,               |
|                    three-dimension membership, eligibility policies, Streamlit reqs,               |
|                    frontend-agnostic contracts)                                                    |
|                                                                                                    |
|   DATA GOVERNANCE SPECIFICATIONS                                                                    |
|   └── docs/DATA_SOURCE_REGISTER.md (source-to-field matrix, verification statuses,                |
|                    match/delivery reconciliation plan, licence evidence)                          |
|   └── docs/DATA_DICTIONARY.md (metric definitions: formula, numerator/denominator, null rules,    |
|                    sample minimums, observed/derived/model-inferred classes)                       |
|                                                                                                    |
|   SYSTEM ARCHITECTURE & VISUAL BLUEPRINTS                                                          |
|   └── docs/ARCHITECTURE.md (10 Mermaid diagrams: orchestration, MIE workflow, PIRE/TMVE flows,    |
|                    ingestion/provenance, analytics, 31-entity ERD (DDL-mirrored), SICE flow,       |
|                    Streamlit tier, evidence flow; ADR-001..007)                                    |
|                                                                                                    |
|   EXECUTION ROADMAP & VERIFICATION GATES                                                           |
|   └── docs/PHASES.md (Phase 0a/0b + Phases 1–10, dependencies, checkpoints, MVP vs long-term)     |
|                                                                                                    |
|   MULTI-AGENT OPERATING CONSTITUTION                                                               |
|   └── docs/AGENTS.md (16 agent contracts mapped to MIE, 6 engines, 5 services, delivery & QA)      |
|                                                                                                    |
|   ENGINEERING DIRECTIVES & STATISTICAL GUARDRAILS                                                  |
|   └── docs/AI_INSTRUCTIONS.md (identity, membership & evidence mandates; domain rules;             |
|                    prohibitions; Streamlit standards)                                             |
+----------------------------------------------------------------------------------------------------+
```

---

## 2. Core Documentation Index

| Document | Title & Subtitle | Primary Target Audience | Core Scope & Key Contents | Key Artifacts |
|---|---|---|---|---|
| [**`PRD.md`**](./PRD.md) | **Product Requirements Document**<br>*(Squad Intelligence & Team Composition)* | Franchise CEO, Head of Cricket Ops, Squad Strategists, Product Managers | Product vision, three-dimension membership/eligibility semantics, candidate-discovery-first workflow, FRs with full traceability (contract · architecture · phase · agent · AC), 11 Streamlit views, hackathon Top-10 deliverable spec (§4.3), scope partition, AC-01…AC-23 | Workflow diagram, FR traceability tables, acceptance matrix |
| [**`TRD.md`**](./TRD.md) | **Technical Requirements Document**<br>*(MIE + 6 Engines + 5 Services + 31-Entity DDL)* | Principal Architects, Data Engineers, Backend Engineers, DBA | MIE orchestration contract, engine I/O contracts (PIRE tiers · TMVE 3 dimensions · CDCRE dual capability · CPPAE · CMIE · SICE), support services, remediated 31-entity PostgreSQL 16 DDL (design decisions D1–D10), negative-verification requirements, versioned eligibility policies, Streamlit requirements, frontend-agnostic API surface | Engine contracts, 31-entity DDL, API table |
| [**`DATA_SOURCE_REGISTER.md`**](./DATA_SOURCE_REGISTER.md) | **Data Source Register**<br>*(Source-to-Field Mapping & Reconciliation)* | Data Engineers, DBA, Auditors | Six source families + official records, field-level mapping, statuses VERIFIED / PARTIALLY_VERIFIED / UNVERIFIED / UNAVAILABLE / RESTRICTED, join keys, match/delivery reconciliation plan, local verification log (2026-11-10) | Source matrix, reconciliation rules, verification log |
| [**`DATA_DICTIONARY.md`**](./DATA_DICTIONARY.md) | **Metric Data Dictionary**<br>*(CPPAE-Governed Metrics)* | Analysts, Backend Engineers, QA | B/W/F/M-series metrics: definition, formula, numerator/denominator, source fields, exclusions, format restrictions, phase rules, null handling, minimum samples, DQ validation, OBSERVED/DERIVED/MODEL_INFERRED class; explicit NOT_COMPUTABLE list | Metric tables, global conventions |
| [**`ARCHITECTURE.md`**](./ARCHITECTURE.md) | **System Architecture Specification**<br>*(10 Mermaid Diagrams + 7 ADRs)* | Solutions Architects, Tech Leads, Full-Stack & Data Engineers | Orchestration architecture, MIE end-to-end workflow (candidate-discovery-first), PIRE tier flow, TMVE three-dimension flow, ingestion/provenance, 31-entity ERD (DDL-mirrored; invalid TEAMS→SEASONS edge removed), SICE flow, Streamlit tier, evidence flow; ADR-001..007 | 10 Mermaid diagrams, 7 ADRs |
| [**`PHASES.md`**](./PHASES.md) | **Engineering Implementation Roadmap**<br>*(Phases 0a/0b to 10)* | Technical PMs, Engineering Leads, QA Engineers | Split Phase 0 (0a COMPLETE; 0b OPEN/PARTIALLY_COMPLETE — external licence verification outstanding), Phases 1–10 with objectives, subphases, inputs/outputs, dependencies, checkpoints, acceptance criteria, testing, status; MVP vs long-term split; risk register | Phase dependency graph, status matrix, risk register |
| [**`AGENTS.md`**](./AGENTS.md) | **Multi-Agent Operating Constitution**<br>*(16 Agent Contracts)* | AI System Engineers, Orchestrators, Tech Leads | One agent per engine (`agent_pire`, `agent_tmve`, `agent_cdcre`, `agent_cppae`, `agent_cmie`, `agent_sice`) + MIE + governance; five support-service agents; delivery/QA agents; conflict-resolution ladder | 16 agent contracts, escalation ladder |
| [**`AI_INSTRUCTIONS.md`**](./AI_INSTRUCTIONS.md) | **AI Architectural Principles & Domain Guardrails** | AI Agents, Engineers, Code Reviewers | Identity/membership/evidence mandates, three-dimension membership model, negative-verification rule, eligibility policy versioning, domain rules, prohibitions, Streamlit standards, licensing & confidentiality | Rule tables, prohibition list |

---

## 3. Stakeholder Reading Pathways

### Pathway 1: Franchise Leadership & Chief Executive (~25 min)
1. [`PRD.md §1 & §3`](./PRD.md#1-executive-summary--problem-statement) — product vision, historical
   context, hackathon alignment.
2. [`PRD.md §2`](./PRD.md#2-target-users--stakeholder-personas) — persona hierarchy.
3. [`PRD.md §4`](./PRD.md#4-user-workflow-primary--revised) — workflow; [`§4.3`](./PRD.md#43-use-case-3-hackathon-final-deliverable--top-10-youngest-eligible-uncapped-candidates)
   the Top-10 deliverable.
4. [`PHASES.md §1`](./PHASES.md#1-executive-roadmap-overview--dependency-graph) — roadmap, MVP
   split, Phase 0 status.
- **Decisions enabled**: squad-direction approval, risk tolerance for unverified players,
  verification-policy sign-off.

### Pathway 2: Lead Cricket Analyst & Squad Strategist (~45 min)
1. [`PRD.md §1.2–§1.3`](./PRD.md#1-executive-summary--problem-statement) — why naive team
   building fails; membership/eligibility semantics.
2. [`TRD.md §3–§8`](./TRD.md#3-engine-01--player-identity-resolution-engine-pire) — engine
   contracts (PIRE → SICE).
3. [`TRD.md §4`](./TRD.md#4-engine-02--team-membership-verification-engine-tmve) —
   three-dimension membership + negative-verification requirements.
4. [`DATA_DICTIONARY.md`](./DATA_DICTIONARY.md) — metric definitions and null/sample rules.
5. [`AI_INSTRUCTIONS.md §4`](./AI_INSTRUCTIONS.md#4-identity-membership--evidence-verification-mandates) —
   mandates and domain rules.
- **Decisions enabled**: team-composition strategy, candidate-vs-incumbent comparison policy,
  verification depth.

### Pathway 3: Principal Architect & Backend/Data Engineers (~60 min)
1. [`TRD.md §1–§2`](./TRD.md#1-system-overview--technical-architecture) — subsystems and MIE
   sequence.
2. [`TRD.md §10`](./TRD.md#10-central-postgresql-16-database-schema-31-entities) — 31-entity DDL
   and design decisions D1–D10.
3. [`ARCHITECTURE.md §2`](./ARCHITECTURE.md#2-system-architecture-diagrams) — all 10 diagrams.
4. [`ARCHITECTURE.md §3`](./ARCHITECTURE.md#3-architectural-decision-records-adrs) — ADR-001..007.
5. [`PHASES.md §3–§12`](./PHASES.md#3-phase-1--historical-dataset-acquisition--data-quality) —
   per-phase tasks and gates.
- **Decisions enabled**: schema migration sequencing, FK/partition validation, MIE routing,
  expression-index behaviour.

### Pathway 4: Data Engineers & ETL Pipeline Specialists (~50 min)
1. [`DATA_SOURCE_REGISTER.md`](./DATA_SOURCE_REGISTER.md) — source statuses, join keys,
   reconciliation, SMAT gap.
2. [`TRD.md §10`](./TRD.md#10-central-postgresql-16-database-schema-31-entities) — raw /
   normalised / derived separation; partitioned `deliveries` FKs.
3. [`ARCHITECTURE.md §2.5`](./ARCHITECTURE.md#25-diagram-5-data-ingestion--provenance-architecture) —
   ingestion/provenance diagram.
4. [`AI_INSTRUCTIONS.md §2 & §6`](./AI_INSTRUCTIONS.md#2-core-architectural-tenets) — immutable
   lake; confidentiality of the hackathon dataset.
- **Decisions enabled**: parser design, quarantine policy, coverage-state backfill, provenance
  record lifecycles.

### Pathway 5: Hackathon Judges & Technical Auditors (~40 min)
1. [`README.md`](../README.md) — product overview and current status.
2. [`docs/README.md`](./README.md) — this hub + traceability matrix (§4).
3. [`PRD.md §8`](./PRD.md#8-acceptance-criteria) — acceptance criteria AC-01…AC-23.
4. [`TRD.md §4 & §10`](./TRD.md#4-engine-02--team-membership-verification-engine-tmve) —
   membership model and schema integrity.
5. [`PHASES.md §1 & §13`](./PHASES.md#13-cross-phase-risk-assessment--mitigation) — roadmap,
   Phase 0 status, risk register.
6. [`AGENTS.md`](./AGENTS.md) & [`AI_INSTRUCTIONS.md`](./AI_INSTRUCTIONS.md) — constitution
   and guardrails.
7. [`reports/DOCUMENTATION_REMEDIATION_AUDIT.md`](../reports/DOCUMENTATION_REMEDIATION_AUDIT.md) —
   remediation record, defect resolutions, validation results, commit list.
- **Decisions enabled**: holistic scoring of domain rigor, evidence integrity, engineering
  maturity, and verification honesty.

---

## 4. Cross-Document Traceability Matrix (remediated feature set)

| Feature ID | Feature | Defining PRD Section | TRD Contract | Architecture Diagram | Implementation Phase | Responsible Agent |
|---|---|---|---|---|---|---|
| **F-E1** | Player Identity Resolution (PIRE) | [PRD §5.1](./PRD.md#51-player-identity-resolution-pire) | [TRD §3](./TRD.md#3-engine-01--player-identity-resolution-engine-pire) | [ARCH §2.3](./ARCHITECTURE.md#23-diagram-3-player-identity-resolution-pire-workflow--revised-terminology) | [Phase 2](./PHASES.md#4-phase-2--unified-database--player-identity-resolution) | `agent_pire` |
| **F-E2** | Team Membership Verification (3 dimensions) | [PRD §5.2](./PRD.md#52-team-membership-verification-tmve) | [TRD §4](./TRD.md#4-engine-02--team-membership-verification-engine-tmve) | [ARCH §2.4](./ARCHITECTURE.md#24-diagram-4-team-membership-verification-tmve--three-dimensions) | [Phase 3](./PHASES.md#5-phase-3--team-membership-verification-tmve) | `agent_tmve` |
| **F-E3** | Career Discovery & Coverage (CDCRE dual capability) | [PRD §5.3](./PRD.md#53-career-discovery--competition-research-cdcre) | [TRD §5](./TRD.md#5-engine-03--career-discovery--competition-research-engine-cdcre) | [ARCH §2.2](./ARCHITECTURE.md#22-diagram-2-mie-orchestration-workflow-revised--candidate-discovery-first) | [Phase 4](./PHASES.md#6-phase-4--career-discovery--external-research-cdcre) | `agent_cdcre` |
| **F-E4** | Performance Analytics (CPPAE) | [PRD §5.4](./PRD.md#54-complete-player-performance-analytics-cppae) | [TRD §6 + DATA_DICTIONARY](./DATA_DICTIONARY.md) | [ARCH §2.6](./ARCHITECTURE.md#26-diagram-6-performance-analytics--derived-feature-flow) | [Phase 5](./PHASES.md#7-phase-5--complete-player-performance-analytics-cppae) | `agent_cppae` |
| **F-E5** | Contextual Match Intelligence (CMIE) | [PRD §5.5](./PRD.md#55-contextual-match-intelligence-cmie) | [TRD §7](./TRD.md#7-engine-05--contextual-match-intelligence-engine-cmie) | [ARCH §2.6](./ARCHITECTURE.md#26-diagram-6-performance-analytics--derived-feature-flow) | [Phase 6](./PHASES.md#8-phase-6--contextual-match-intelligence-cmie) | `agent_cmie` |
| **F-E6** | Squad Intelligence & Composition (SICE) | [PRD §5.6](./PRD.md#56-squad-intelligence--composition-sice) | [TRD §8](./TRD.md#8-engine-06--squad-intelligence--composition-engine-sice) | [ARCH §2.8](./ARCHITECTURE.md#28-diagram-8-squad-intelligence--composition-sice-evaluation-flow) | [Phase 8](./PHASES.md#10-phase-8--squad-intelligence--composition-sice--service-e) | `agent_sice` |
| **F-O1** | MIE Orchestration & Unified Report | [PRD §4](./PRD.md#4-user-workflow-primary--revised) | [TRD §2](./TRD.md#2-mother-intelligence-engine-mie--central-orchestrator) | [ARCH §2.2 / §2.10](./ARCHITECTURE.md#210-diagram-10-evidence--verification-flow-mie--provenance) | [Phase 7](./PHASES.md#9-phase-7--player-profile-generation-mie--service-b) | `agent_mie_orchestration` |
| **F-S1** | Data Ingestion Service (A) | [PRD §5.7](./PRD.md#57-support-services) | [TRD §9.1 + REGISTER](./DATA_SOURCE_REGISTER.md) | [ARCH §2.5](./ARCHITECTURE.md#25-diagram-5-data-ingestion--provenance-architecture) | [Phase 1](./PHASES.md#3-phase-1--historical-dataset-acquisition--data-quality) | `agent_data_ingestion` |
| **F-S2** | Player Profile Generator (B) | [PRD §5.7](./PRD.md#57-support-services) | [TRD §9.2](./TRD.md#9-support-services) | [ARCH §2.1](./ARCHITECTURE.md#21-diagram-1-high-level-orchestration-architecture) | [Phase 7](./PHASES.md#9-phase-7--player-profile-generation-mie--service-b) | `agent_profile_generator` |
| **F-S3** | Source Verification & Provenance (C) | [PRD §5.7](./PRD.md#57-support-services) | [TRD §9.3](./TRD.md#9-support-services) | [ARCH §2.10](./ARCHITECTURE.md#210-diagram-10-evidence--verification-flow-mie--provenance) | [Phases 4, 7](./PHASES.md#6-phase-4--career-discovery--external-research-cdcre) | `agent_provenance` |
| **F-S4** | Data Quality & Coverage (D) | [PRD §5.7](./PRD.md#57-support-services) | [TRD §9.4](./TRD.md#9-support-services) | [ARCH §2.5](./ARCHITECTURE.md#25-diagram-5-data-ingestion--provenance-architecture) | [Phase 1 (all phases)](./PHASES.md#3-phase-1--historical-dataset-acquisition--data-quality) | `agent_data_quality` |
| **F-S5** | Team Builder Service (E) | [PRD §5.7](./PRD.md#57-support-services) | [TRD §9.5](./TRD.md#9-support-services) | [ARCH §2.8](./ARCHITECTURE.md#28-diagram-8-squad-intelligence--composition-sice-evaluation-flow) | [Phase 8](./PHASES.md#10-phase-8--squad-intelligence--composition-sice--service-e) | `agent_team_builder` |
| **F-U1** | Streamlit 11-View Application | [PRD §5.8 & §6](./PRD.md#6-streamlit-views-ui-requirements) | [TRD §12](./TRD.md#12-streamlit-presentation-requirements) | [ARCH §2.9](./ARCHITECTURE.md#29-diagram-9-streamlit-presentation-tier) | [Phase 9](./PHASES.md#11-phase-9--streamlit-application) | `agent_streamlit_app` |
| **F-H1** | Hackathon Top-10 Ranking Deliverable | [PRD §4.3 & §7](./PRD.md#43-use-case-3-hackathon-final-deliverable--top-10-youngest-eligible-uncapped-candidates) | [TRD §8 + `derived_features`](./TRD.md#8-engine-06--squad-intelligence--composition-engine-sice) | [ARCH §2.8](./ARCHITECTURE.md#28-diagram-8-squad-intelligence--composition-sice-evaluation-flow) | [Phase 10](./PHASES.md#12-phase-10--hackathon-candidate-evaluation--final-submission) | `agent_sice` |
| **F-D1** | 31-Entity PostgreSQL Core | [PRD §3.1](./PRD.md#31-strategic-product-objectives) | [TRD §10](./TRD.md#10-central-postgresql-16-database-schema-31-entities) | [ARCH §2.7](./ARCHITECTURE.md#27-diagram-7-central-database-entity-relationship-diagram-31-entities-ddl-mirrored) | [Phase 2](./PHASES.md#4-phase-2--unified-database--player-identity-resolution) | `agent_chief_architect` |

---

## 5. Architectural Principles & Cross-Cutting Guardrails

All engineering artefacts must abide by the tenets in
[`AI_INSTRUCTIONS.md`](./AI_INSTRUCTIONS.md):

1. **Deterministic reproducibility** for the query-driven path; versioned, seeded model
   configuration for the ranking (AC-18).
2. **Normalised 3NF 31-entity relational core** with canonical `player_id` everywhere
   (`derived_features` documented exception).
3. **Read-only immutable data lake** (`datasets/`); SHA-256 deduplication; quarantining.
4. **Zero statistical fabrication**; missing → `NULL`.
5. **Evidence & provenance first**: tiered verification records; CONFLICT → human review.
6. **Frontend-agnostic engines**: Streamlit now, Next.js later, same contracts.
7. **No LLM-dependence for correctness**: research flagged and review-gated.
8. **Identity**: never merge similar names; deterministic tiers; confidence only when
   calibrated; ambiguity → user clarification.
9. **Membership**: three independent dimensions; squad inclusion ≠ appearance; historical ≠
   current; negative membership only via TRD §4.5 requirements; RR 2016–17 suspension is a
   franchise participation state; 2027 UNKNOWN until evidenced.
10. **Eligibility**: season-bound, versioned, source-traceable policy; unknowns stay
    `NOT_ASSESSED`; unknown players are never auto-uncapped.
11. **Evidence verification**: dataset absence ≠ non-participation; weather ≠ pitch
    measurement; no mental-state inference; no fabricated injuries.

---

## 6. Document Maintenance & Status Markings

- Status markings use `[STATUS: PLANNED - GREENFIELD BASELINE]` uniformly; no application code
  exists.
- **Phase 0a (documentation baseline): COMPLETE. Phase 0b (empirical data-source & licence
  audit): OPEN / PARTIALLY_COMPLETE** (local evidence recorded; external-source verification
  outstanding — `PHASES.md §2.0b`).
- `PROJECT.md` is the current project charter (v2.1.0), with a prominent notice that it
  superseded the v1.0.0 specification.

---

## 7. Document Suite Changelog & Version Control

| Version | Release Date | Significant Changes | Gate Status |
|---|---|---|---|
| **1.0.0-PROD-SPEC** | November 2026 (early) | Initial suite: auction-war-room product, 7 modules + 1 subsystem, 20-entity schema, Next.js frontend, Phases 0–8, 14 agents. | SUPERSEDED |
| **2.0.0-ARCH-REVISION** | November 2026 (later) | Product re-centred as the **RR Squad Intelligence & Team Composition Platform**: MIE + 6 engines + 5 services; six-class membership; 27-entity schema; Streamlit initial frontend; Phases 0–10; 16 agents; strengthened guardrails; data directory corrected to `datasets/`. | SUPERSEDED (by 2.1.0) |
| **2.1.0-REMEDIATED** | November 2026 (this cycle) | DDL remediation (expression-unique index; partitioned `deliveries` FKs; composite fielding link; false-claim defaults removed; overs as integer balls; overthrows allowed); `team_season_participation` replaces `seasons.is_suspension`; three-dimension membership + versioned eligibility policies (31 entities); PIRE deterministic tiers + contextual-attribute terminology + calibrated-only confidence; CDCRE dual capabilities (circular dependency removed); `agent_cdcre`; new `DATA_SOURCE_REGISTER.md` (verification statuses; local evidence 2026-11-10; SMAT gap) and `DATA_DICTIONARY.md` (B/W/F/M-series + NOT_COMPUTABLE list); Phase 0 split (0a COMPLETE / 0b OPEN); PRD AC-01…AC-23 + hackathon Top-10 deliverable spec; PROJECT.md reconciled; ERD reconciled 1:1 to DDL (invalid TEAMS→SEASONS edge removed). | **APPROVED RE-REVISION** |
