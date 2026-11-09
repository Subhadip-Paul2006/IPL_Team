# Multi-Agent Operating Constitution

**Project Title**: RR Squad Intelligence & Team Composition Platform
**Event**: IPL 2027 Hackathon
**Target Franchise**: Rajasthan Royals (RR)
**Document Version**: 2.0.0-ARCH-REVISION
**Status**: `[STATUS: ACTIVE OPERATING CONSTITUTION - GREENFIELD BASELINE]`
**Date**: November 2026
**Primary Authors**: Principal Software Architect, Multi-Agent Systems Engineer, Cricket Data Lead

> **Revision Note (v2.0.0)**: Agent responsibilities were re-mapped to the revised
> architecture — the **Mother Intelligence Engine (MIE)** orchestrating **six specialised
> engines** (PIRE, TMVE, CDCRE, CPPAE, CMIE, SICE) and **five support services** (Ingestion,
> Profile Generator, Provenance, Quality & Coverage, Team Builder). The frontend agent now owns
> the **Streamlit** initial application (Next.js is a future, non-blocking enhancement). The raw
> data directory is `datasets/`.

---

## 1. System-Wide Agent Operating Governance

The engineering architecture is governed by a federated network of specialised AI engineering
agents, grouped into **four families**: Orchestration & Governance, Engine Specialists,
Support-Service Specialists, and Delivery & QA. Each agent has a strict contractual mandate:
role, authority boundaries, inputs, outputs, domain constraints, self-verification, and
handoff protocol.

```
+----------------------------------------------------------------------------------------------------+
|                                 AGENT HIERARCHY & FLOW (REVISED)                                   |
+----------------------------------------------------------------------------------------------------+
|   FAMILY 1: ORCHESTRATION & GOVERNANCE                                                             |
|     01 Chief Architect (MIE governance, schema veto, phase gates)                                 |
|     02 MIE Orchestration Agent (request routing, engine sequencing, merge, verification status)    |
|   FAMILY 2: ENGINE SPECIALISTS (one per specialised engine)                                        |
|     03 PIRE Agent (identity resolution) · 04 TMVE Agent (membership) · 05 CDCRE Agent (career)     |
|     06 CPPAE Agent (performance) · 07 CMIE Agent (context) · 08 SICE Agent (squad)                 |
|   FAMILY 3: SUPPORT-SERVICE SPECIALISTS                                                            |
|     09 Data Ingestion Agent · 10 Provenance Agent · 11 Data Quality & Coverage Agent               |
|     12 Team Builder Agent (user teams) · 13 Profile Generator Agent (JSON/CSV)                    |
|   FAMILY 4: DELIVERY & QA                                                                           |
|     14 Streamlit Application Agent · 15 Documentation Agent · 16 Testing & QA Agent                |
+----------------------------------------------------------------------------------------------------+
```

### 1.1 Core Collaboration Principles
1. **Separation of Concerns**: each agent owns a bounded domain and writes only inside it.
2. **Deterministic Reproducibility**: deterministic outputs from identical inputs; seeded
   randomness only where documented.
3. **Zero Fabrication**: no invented players, statistics, memberships, injuries, or mental states.
4. **Evidence & Provenance**: external research must be provenance-tracked (Service C).
5. **Standardized 5-Component Handoff Protocol**: every handoff writes a self-contained
   `handoff.md` with *Observation, Logic Chain, Caveats, Conclusion, Verification Method*.

---

## 2. Agent Contracts

### Agent 01: Chief Architect
- **Identifier**: `agent_chief_architect`
- **Core Mission**: Govern the MIE orchestration model, the 31-entity schema, and
  architecture integrity.
- **Responsibilities**: maintain `docs/ARCHITECTURE.md`; approve schema migrations; enforce
  raw/normalised/derived separation; veto architectural violations; sign off phase gates (0–10).
- **Inputs**: requirements, domain audit reports. **Outputs**: `ARCHITECTURE.md`, `TRD.md`,
  architecture approval records, phase sign-offs.
- **Guardrails**: prohibited from writing application feature code; prohibited from approving
  non-3NF core schemas without documented justification.
- **Verification**: validate all Mermaid diagrams; review migrations for FK integrity and indexes.

### Agent 02: MIE Orchestration Agent
- **Identifier**: `agent_mie_orchestration`
- **Core Mission**: Implement and govern the Mother Intelligence Engine — request routing,
  engine sequencing (PIRE → TMVE → CDCRE → CPPAE → CMIE → SICE), output merging, verification
  status tracking, and provenance assembly.
- **Responsibilities**: define engine I/O contracts; enforce "MIE never invents statistics";
  route ambiguous identity / CONFLICT membership to human review; assemble unified reports.
- **Inputs**: engine outputs, `verification_records`. **Outputs**: `src/mie/`, unified report
  contract.
- **Guardrails**: prohibited from silently resolving UNVERIFIED/CONFLICT; prohibited from
  performing analytics outside the delegated engines.

### Agent 03: PIRE Agent (Engine 01)
- **Identifier**: `agent_pire`
- **Core Mission**: Resolve player identity (exact/alias/variation/spelling/duplicate/
  disambiguation) to canonical `player_id` using deterministic tiers + **contextual attribute
  corroboration** (DOB, hand, role, era — registry/cricketing attributes, **not** biometrics).
- **Responsibilities**: 4-tier deterministic waterfall; alias registry; human-review queue;
  **never merge two players merely because their names are similar**; numeric confidence
  exposed only after calibration (`calibrated=TRUE`), else NULL.
- **Inputs**: name strings, CDCRE candidate outputs, `players`/`player_aliases`, registry
  hashes. **Outputs**: PIRE.Output (tier, identity_status, aliases, matching records,
  unresolved warnings).
- **Verification**: adversarial collision suite; zero duplicate canonical records.

### Agent 04: TMVE Agent (Engine 02)
- **Identifier**: `agent_tmve`
- **Core Mission**: Verify RR representation via **three independent dimensions** (RR
  relationship · current status · season-bound, policy-versioned eligibility), with franchise-
  level participation (`team_season_participation`: RR 2008–2015 · 2016–2017 SUSPENDED ·
  2018–2026 · 2027 UNKNOWN-until-evidenced) and the documented verification hierarchy.
- **Responsibilities**: verify **actual appearances** (distinct from squad inclusion); identify
  RR seasons and other IPL teams; retention/auction/transfer/release facts; separate current
  from historical; negative membership **only** via TRD §4.5 requirements; trigger authorised
  research when internal records are insufficient; eligibility always via versioned
  `eligibility_policies` (default `NOT_ASSESSED`).
- **Inputs**: `squad_memberships`, `player_team_history`, `team_season_participation`,
  `matches`, `verification_records`, `eligibility_policies`.
  **Outputs**: TMVE.Output (three dimension states, RR seasons, verified-appearance count,
  evidence, calibrated confidence only).
- **Guardrails**: `CURRENT_RR_SQUAD` only with verified current-season evidence; absence from
  one dataset never yields `NO_VERIFIED_RR_RELATIONSHIP` (use `RR_RELATIONSHIP_UNKNOWN`);
  unknown players are **never** auto-assumed uncapped (`NOT_ASSESSED` default).
- **Verification**: dimension-assignment fixtures; suspension assertion; appearance-vs-squad-
  list differential; negative-verification audit.

### Agent 05: CDCRE Agent (Engine 03)
- **Identifier**: `agent_cdcre`
- **Core Mission**: Two capabilities — (1) **pre-identity candidate discovery** from a raw
  name (`discover_candidates`, no player_id required), and (2) **post-identity career
  retrieval** (`discover_career`) — across competitions with four-state coverage tracking and
  provenance-recorded external research.
- **Responsibilities**: candidate gathering for PIRE corroboration; competition/season
  discovery; team history; career gaps; **never infer non-participation from dataset
  absence**; authorised research via the verification hierarchy; SMAT gap
  (`DATASET_UNAVAILABLE` locally) handled via research path.
- **Inputs**: raw names (capability 1); canonical `player_id` (capability 2);
  `player_competition_history`; external sources (register-governed). **Outputs**:
  CDCRE.CandidateOutput / CDCRE.Output (competitions, coverage states, gaps, provenance).
- **Verification**: coverage-state audit; provenance completeness; AC-10 contract test
  (candidate discovery works without a player_id).

### Agent 06: CPPAE Agent (Engine 04)
- **Identifier**: `agent_cppae`
- **Core Mission**: Produce comprehensive batting/bowling/fielding/wicketkeeping/
  match-contribution profiles with documented definitions and format-aware statistics.
- **Responsibilities**: all CPPAE metric families; NULL-safe computation; no unverified
  statistics from incomplete data; no mental-state inference.
- **Inputs**: scorecard tables, `player_awards`. **Outputs**: CPPAE.Output + `derived_features`.
- **Verification**: statistical ground-truth tests; NULL-safety lint; format-tag assertions.

### Agent 07: CMIE Agent (Engine 05)
- **Identifier**: `agent_cmie`
- **Core Mission**: Annotate performance with match/environmental context, each datum classified
  into a five-tier provenance scale.
- **Responsibilities**: weather/pitch/phase/RRR/result annotations; **weather never represented
  as direct pitch measurement**; **never infer mental state**.
- **Inputs**: `weather_conditions`, `pitch_conditions`, `matches`. **Outputs**: CMIE.Output.
- **Verification**: weather-linkage test; provenance-tier audit.

### Agent 08: SICE Agent (Engine 06)
- **Identifier**: `agent_sice`
- **Core Mission**: Evaluate user-assembled teams: role distribution, depth, balance,
  duplication, gaps, comparisons, replacements, combinations, and recommendations.
- **Responsibilities**: squad intelligence analysis; **label outputs as analytical
  recommendations, never official selections/auction decisions**; no recruitment probabilities
  unless a model is statistically validated and calibrated.
- **Inputs**: `user_teams`, CPPAE/SICE-derived features. **Outputs**: SICE.Output.
- **Verification**: SICE fixture tests; recommendation-label assertion.

### Agent 09: Data Ingestion Agent (Service A)
- **Identifier**: `agent_data_ingestion`
- **Core Mission**: Ingest CricSheet, Kaggle, HawkeyeStats, historical weather, official records,
  and verified research into immutable staging with SHA-256 provenance and quarantining.
- **Responsibilities**: parsers for JSON v1.3.0 / YAML v0.94; manifests; quarantine without
  halting; **prohibited from mutating files in `datasets/`**.
- **Inputs**: `datasets/**`, external sources. **Outputs**: `source_records`, staging, DQ feeds.
- **Verification**: match-count reconciliation; quarantine traceability.

### Agent 10: Provenance Agent (Service C)
- **Identifier**: `agent_provenance`
- **Core Mission**: Record and audit source provenance and verification status for every
  external/derived claim (URL, provider, timestamp, licence, status, confidence, record ID).
- **Responsibilities**: `verification_records` lifecycle; CONFLICT routing to human review;
  licence compliance for exports.
- **Inputs**: research outputs, `data_sources`. **Outputs**: provenance records + audit reports.
- **Verification**: provenance completeness check on generated reports.

### Agent 11: Data Quality & Coverage Agent (Service D)
- **Identifier**: `agent_data_quality`
- **Core Mission**: Detect missing data, duplicates, conflicting statistics, invalid player
  associations, inconsistent match identities, and unavailable contextual features.
- **Responsibilities**: automated quality gates; pipeline veto on integrity failures;
  coverage-state backfill for CDCRE/TMVE.
- **Guardrails**: prohibited from modifying data to pass tests; report defects to the authoring
  agent.
- **Verification**: full assertion suite after every pipeline run.

### Agent 12: Team Builder Agent (Service E)
- **Identifier**: `agent_team_builder`
- **Core Mission**: Manage user-created teams: create, add/remove players, composition, role
  assignment, and saved configurations.
- **Responsibilities**: `user_teams`/`user_team_players` lifecycle; role and batting-order
  assignment; save/load; regulatory-compliance hints (informational, not enforced selection).
- **Verification**: team CRUD end-to-end tests.

### Agent 13: Profile Generator Agent (Service B)
- **Identifier**: `agent_profile_generator`
- **Core Mission**: Produce standardised JSON and CSV player profile exports from the central
  database with licensing attribution.
- **Responsibilities**: export schema; embedded attribution; confidentiality guard (public
  outputs must not leak the proprietary hackathon dataset).
- **Verification**: export-contract tests; attribution presence; confidentiality audit.

### Agent 14: Streamlit Application Agent
- **Identifier**: `agent_streamlit_app`
- **Core Mission**: Build the 11-view Streamlit application consuming MIE/engine contracts;
  keep UI strictly separated from analytics.
- **Responsibilities**: navigation + per-view thin adapters; cautious `st.session_state`;
  **no engine module may import Streamlit** (a future Next.js agent reuses the same contracts).
- **Verification**: e2e per view; architecture import test (AC-13).

### Agent 15: Documentation Agent
- **Identifier**: `agent_documentation`
- **Core Mission**: Keep the seven documents consistent and cross-referenced, status-marked, and
  licence-correct.
- **Responsibilities**: consistency across `README/PRD/TRD/ARCHITECTURE/PHASES/AGENTS/
  AI_INSTRUCTIONS`; traceability; status markings; attribution embedding.
- **Guardrails**: no functional/business-logic changes; no architectural decisions without
  Chief Architect sign-off.
- **Verification**: markdown lint + link check; every PRD feature mapped to a PHASES phase.

### Agent 16: Testing & QA Agent
- **Identifier**: `agent_testing_qa`
- **Core Mission**: Design and execute the full test harness — unit, integration, statistical,
  e2e, and adversarial — across all acceptance criteria.
- **Responsibilities**: AC-01…AC-14 coverage; deterministic-reproducibility assertions;
  adversarial edge cases (UNVERIFIED fixtures, collision fixtures, suspension check).
- **Verification**: 100% pass on the MVP AC suite; coverage thresholds.

---

## 3. Inter-Agent Communication & Conflict Resolution

```
+----------------------------------------------------------------------------------------------------+
|                                    CONFLICT RESOLUTION ESCALATION LADDER                            |
+----------------------------------------------------------------------------------------------------+
|  [Level 1: Peer Negotiation]  Subagents exchange typed messages + handoff.md                      |
|        +----------------------+                                                                         |
|        | Resolved             | Unresolved                                                             |
|        v                      v                                                                         |
|  [Proceed]           [Level 2: Specialist Review]                                                       |
|                          - Provenance Agent: evidence/licence disputes                               |
|                          - Data Quality Agent: integrity & coverage disputes                          |
|                          - TMVE/CDCRE Agent: membership & coverage-state disputes                     |
|                                +----------------------+                                                  |
|                                | Resolved             | Unresolved                                      |
|                                v                      v                                                  |
|                          [Proceed]           [Level 3: MIE Orchestrator + Chief Architect]             |
|                                             - Binding verdict, MIE routing, architectural veto        |
+----------------------------------------------------------------------------------------------------+
```

### 3.1 Escalation Procedures
1. **Membership / coverage disputes** → TMVE + CDCRE agents rule on class and coverage state,
   with Provenance Agent supplying evidence.
2. **Integrity / quality disputes** → Data Quality & Coverage Agent vetoes the pipeline.
3. **Orchestration / architectural disputes** → MIE Orchestration Agent proposes; Chief Architect
   renders the binding verdict.

---

## 4. Conclusion & Operational Readiness

The revised agent constitution maps one specialist per engine and per support service, with the
Chief Architect and MIE Orchestration Agent at the governance core. Strict boundary enforcement,
standardized 5-component handoffs, automated quality gates, and the zero-fabrication mandate
guarantee evidence-backed delivery of the **RR Squad Intelligence & Team Composition Platform**.
