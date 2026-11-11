# Multi-Agent Operating Constitution

**Project Title**: RR Squad Intelligence & Team Composition Platform
**Event**: IPL 2027 Hackathon
**Target Franchise**: Rajasthan Royals (RR)
**Document Version**: 2.2.0
**Status**: `[STATUS: ACTIVE OPERATING CONSTITUTION - GREENFIELD BASELINE]`
**Date**: November 2026
**Primary Authors**: Principal Software Architect, Multi-Agent Systems Engineer, Cricket Data Lead

> **Revision Note (v2.2.0, PVRE Dual-Mode Research Agent)**: Introduces `agent_pvre` (Agent 08b:
> PVRE Agent — Engine 07) to Family 2 (Engine Specialists), increasing total agent count from 17
> to 18 agents. Defines Mother Controller responsibilities, Mode A replacement intelligence
> responsibilities (RR historical research + recent global performance 2–3 yr window + replaceability
> signals), Mode B uncapped candidate discovery responsibilities, mandatory `REVIEW_REQUIRED` safety
> handling, and strict authority boundaries with PIRE, TMVE, CDCRE, Eligibility Policy Service, CPPAE,
> CMIE, and SICE. Updates Agent 02 (MIE Orchestration), Agent 08 (SICE), Agent 15 (Documentation),
> and Agent 16 (Testing & QA). Reconciles all entity references to 33 entities.
>
> **Revision Note (v2.1.1, targeted remediation, retained for history)**: Aligned agent contracts to the v2.1.1
> architecture — the 33-entity schema (adds `ranking_configurations` + `ranking_runs`);
> TMVE owns Dimensions 1–2 only (eligibility Dimension 3 is the Eligibility Service,
> composed by MIE, TRD §4.4 Option B); SICE owns the versioned Top-10 method per
> [`RANKING_SPEC.md`](RANKING_SPEC.md) (`RK-1.0.0`) and stores every board in
> `ranking_runs`; ingestion handles the **The Hundred** archive as the `HUNDRED`
> format (`balls_per_over = 5`, derived metrics deferred — DATA_DICTIONARY §5);
> participation-window claims are model statements, not verified evidence (Priority E).
>
> **Revision Note (v2.0.0, retained for history)**: Agent responsibilities were re-mapped
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
|     08b PVRE Agent (Engine 07: dual-mode verification & replacement intelligence)                  |
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
- **Core Mission**: Govern the MIE orchestration model, the 33-entity schema, and
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
  orchestrate PVRE Mother Controller (Engine 07) and enforce deterministic routing waterfall;
  route ambiguous identity, conflicting attributes, or unverified eligibility to the mandatory
  `REVIEW_REQUIRED` safety pathway; assemble unified player and replacement reports.
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
- **Core Mission**: Verify RR representation via **Dimensions 1–2** (RR relationship ·
  current status), with franchise-level participation
  (`team_season_participation`: RR 2008–2015 · 2016–2017 SUSPENDED · 2018–2026 ·
  2027 UNKNOWN-until-evidenced) and the documented verification hierarchy.
  **v2.1.1 Option B**: Dimension 3 (season-bound, policy-versioned eligibility) is owned
  by the **Eligibility Service** (`agent_eligibility_policy`, a Service A–E extension),
  not by TMVE; **MIE composes all three** and never blends them into one label
  (TRD §4.4).
- **Responsibilities**: verify **actual appearances** (distinct from squad inclusion); identify
  RR seasons and other IPL teams; retention/auction/transfer/release facts; separate current
  from historical; negative membership **only** via TRD §4.5 requirements; trigger authorised
  research when internal records are insufficient; **v2.1.1 (Priority E)**: the
  participation-window model (2008–2015 · 2016–17 SUSPENDED · 2018–2026) is documentation,
  not evidence — each `team_season_participation` row seeds `PENDING`/`UNVERIFIED` and
  becomes `VERIFIED` only via a cited `verification_records` row
  (DDL `chk_tsp_verified_evidence`); local CricSheet fixture presence/absence is tier-4
  corroboration only.
- **Inputs**: `squad_memberships`, `player_team_history`, `team_season_participation`,
  `matches`, `verification_records`.
  **Outputs**: TMVE.Output (Dimensions 1–2 states, RR seasons, verified-appearance count,
  evidence, calibrated confidence only). Dimension 3 via
  `EligibilityService.assess` (see §Agent 04b below).
- **Guardrails**: `CURRENT_RR_SQUAD` only with verified current-season evidence; absence from
  one dataset never yields `NO_VERIFIED_RR_RELATIONSHIP` (use `RR_RELATIONSHIP_UNKNOWN`);
  unknown players are **never** auto-assumed uncapped (`NOT_ASSESSED` default).
- **Verification**: dimension-assignment fixtures; suspension assertion; appearance-vs-squad-
  list differential; negative-verification audit.

### Agent 04b: Eligibility Policy Service (v2.1.1, Option B)
- **Identifier**: `agent_eligibility_policy`
- **Core Mission**: Own **Dimension 3** — the season-bound, policy-versioned
  `VERIFIED_ELIGIBLE / VERIFIED_NOT_ELIGIBLE / ELIGIBILITY_UNVERIFIED / NOT_ASSESSED`
  assessment against the active `eligibility_policies` version for the target season
  (TRD §4.4 / §4.6). TMVE (Agent 04) owns Dimensions 1–2; MIE composes all three.
- **Responsibilities**: maintain versioned `eligibility_policies` (rule-source,
  effective/expiry, independently verified); write `player_eligibility` rows; enforce
  DDL CHECKs (`chk_eligibility_status_flag`); route `CONFLICT`/`UNVERIFIED` to
  human review; **never assume an unknown player is uncapped** (default `NOT_ASSESSED`).
- **Inputs**: `eligibility_policies`, `players`, `verification_records`. **Outputs**:
  `EligibilityService.assess` contract (TRD §4.4), `player_eligibility` rows.
- **Verification**: AC-09/AC-24 fixtures (policy-version reference; unknowns
  `NOT_ASSESSED`); eligibility status/flag CHECK enforcement.

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
- **Responsibilities**: all CPPAE metric families **as defined in
  [`DATA_DICTIONARY.md`](DATA_DICTIONARY.md)** (economy = `balls_per_over × runs /
  legal_balls`, never `10 ×`; balls faced = legal + no-balls, wides excluded; single
  three-group phase model); NULL-safe computation; no unverified statistics from
  incomplete data; no mental-state inference. **v2.1.1 (Priority B)**: The Hundred is the
  `HUNDRED` format (`competitions.balls_per_over = 5`, 100-ball innings, three-group phase
  boundaries per DATA_DICTIONARY §4.1/§5) — HUNDRED never inherits six-ball-over
  calculations; derived HUNDRED rate metrics are class `DEFERRED` until the
  `balls_per_over = 5` handling is validated (ingested/preserved as raw, no derived rate
  published).
- **Inputs**: scorecard tables, `player_awards`, `competitions.balls_per_over`.
  **Outputs**: CPPAE.Output + `derived_features` (status includes `DEFERRED`).
- **Verification**: statistical ground-truth tests; NULL-safety lint; format-tag assertions
  (HUNDRED vs six-ball-over separation test).

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
- **Core Mission**: Evaluate user-assembled teams (role distribution, depth, balance,
  duplication, gaps, combinations); perform **role-aware incumbent-vs-candidate replacement
  evaluations** consuming PVRE Mode A dossiers across 16 specified dimensions (TRD §8.4); and
  own the standalone **versioned Top-10 ranking method** ([`RANKING_SPEC.md`](RANKING_SPEC.md)
  `RK-1.0.0`).
- **Responsibilities**: squad intelligence analysis; execute role-aware comparisons between RR
  incumbents and verified uncapped candidates; evaluate overseas player constraints (max 8 squad /
  4 Playing XI); **label outputs as analytical recommendations, never official selections/auction
  decisions**; no recruitment probabilities unless a model is statistically validated and
  calibrated. Maintain strict separation between incumbent replacement evaluations and the
  standalone hackathon Top-10 uncapped ranking. Every evaluation and board is stored as a
  `ranking_runs` row keyed `(ranking_configurations, data_snapshot_sha256)`, ensuring bit-for-bit
  reproducibility (AC-18 / AC-30).
- **Inputs**: `user_teams`, PVRE Mode A replaceability dossiers, CPPAE/SICE-derived features,
  `ranking_configurations`, `ranking_runs`, `eligibility_policies`. **Outputs**: SICE.Output +
  stored `ranking_runs` records (replacement evaluations and Top-10 boards) + recommendation labels.
- **Verification**: SICE fixture tests; replacement comparison tests; recommendation-label
  assertion; ranking reproducibility test (same config + snapshot → identical stored board).

### Agent 08b: PVRE Agent (Engine 07)
- **Identifier**: `agent_pvre`
- **Core Mission**: Govern and implement the Player Verification & Research Engine (PVRE — Engine 07),
  orchestrating the Mother Controller, Mode A (Existing RR Player Replacement Intelligence), Mode B
  (Verified Uncapped Candidate Intelligence), the mandatory `REVIEW_REQUIRED` safety pathway, and
  standardised output contracts.
- **Responsibilities**:
  1. *Mother Controller execution*: accept inbound `PVRERequestContract` from MIE (sole cross-engine
     orchestrator), validate canonical identity (PIRE), verified RR relationship (TMVE), and
     IPL eligibility (Eligibility Policy Service), classify requests, and enforce deterministic
     7-step routing as an internal router within Engine 07.
  2. *Mode A execution (RR Replacement Intelligence)*: conduct dual-scope research investigating
     complete RR history (Module A1: appearances strictly separated from squad inclusion) and
     recent global performance across a configurable 2–3 year window in recognised leagues
     (Module A2: BBL, PSL, CPL, SA20, The Hundred, International, Indian domestic); synthesise
     trajectory into structured replaceability signals (`RETAIN_SIGNAL`, `MONITOR_SIGNAL`,
     `POTENTIALLY_REPLACEABLE`, `INSUFFICIENT_EVIDENCE`, `REVIEW_REQUIRED`) (Module A3); forward
     evidence dossiers to SICE for squad-level evaluation.
  3. *Mode B execution (Uncapped Candidate Discovery)*: execute complete domestic career discovery
     across Ranji Trophy, SMAT, VHT, Duleep, and age-group competitions; enforce independent
     affirmative verification under active `eligibility_policies` rules; register verified candidates
     in the uncapped pool; **never equate database absence with uncapped status**.
  4. *Mandatory `REVIEW_REQUIRED` safety handling*: intercept identity ambiguities, DOB conflicts,
     contradictory RR evidence, unverified eligibility, source discrepancies, or coverage gaps;
     compile complete structured review dossiers (`review_status`, `review_reason_codes`,
     `unresolved_claims`, `conflicting_source_ids`, `missing_evidence`, `recommended_manual_checks`);
     halt automated routing and block unverified candidates from entering the ranking pool.
  5. *Output contract compilation*: emit typed, versioned `PVREOutputContract` with all 26 mandatory
     fields per R2.7, full source provenance (`source_records`, `verification_records`), and explicit
     null/unavailable semantics.
- **Strict Authority Boundaries & Guardrails**:
  - PVRE coordinates but **never replaces** PIRE, TMVE, CDCRE, Eligibility Policy Service, CPPAE,
    CMIE, or SICE.
  - PVRE is **strictly prohibited from making final squad release, replace, or retention decisions**
    (owned by SICE and franchise leadership).
  - PVRE is **strictly prohibited from inventing statistics, appearances, or arbitrary replacement
    probabilities**.
  - PVRE is **strictly prohibited from inferring uncapped status from database absence**, or
    negative RR membership without meeting TRD §4.5 requirements.
  - PVRE **never overwrites conflicting evidence**; competing claims are preserved and flagged
    `REVIEW_REQUIRED`.
- **Inputs**: `PVRERequestContract`, canonical player identity, TMVE membership states, eligibility
  status, tournament scorecards, CPPAE/CMIE metrics, `verification_records`.
- **Outputs**: `PVREOutputContract`, replaceability assessment signals, structured review dossiers,
  populated `derived_features` rows.
- **Self-Verification**:
  - Automated tests covering all 4 routing branches (Mode A, Mode B, REVIEW_REQUIRED, OUT_OF_SCOPE).
  - Fixture assertions validating 2–3 year window boundary enforcement across global leagues.
  - Adversarial conflict injection verifying immediate `REVIEW_REQUIRED` interception.
  - Verification that no unverified player enters the uncapped pool (negative proof assertions).
- **Handoff Protocol**: Standard 5-component handoff (`Observation`, `Logic Chain`, `Caveats`,
  `Conclusion`, `Verification Method`) to MIE and SICE.

### Agent 09: Data Ingestion Agent (Service A)
- **Identifier**: `agent_data_ingestion`
- **Core Mission**: Ingest CricSheet (IPL, **The Hundred**, ODI WC, T20 WC), Kaggle,
  HawkeyeStats, historical weather, official records, and verified research into immutable
  staging with SHA-256 provenance and quarantining.
- **Responsibilities**: parsers for JSON v1.3.0 / YAML v0.94; manifests; quarantine without
  halting; **prohibited from mutating files in `datasets/`**. **v2.1.1 (Priority B)**:
  `datasets/hnd_male_json/` (201 files, ODC-By VERIFIED) ingests under
  `competition.format_tag = 'HUNDRED'`, `competitions.balls_per_over = 5`; wide/no-ball
  events stay delivery events (legal-ball counts are derived, never parsed from
  ball-notation strings); **derived HUNDRED rates remain `DEFERRED`** until Phase 5
  validation. **v2.1.1 (Priority I)**: HawkeyeStats acquisition is human-gated — the
  repository has **no licence** (checked 2026-11-11); no reuse is assumed until a licence
  decision is recorded.
- **Inputs**: `datasets/**`, external sources. **Outputs**: `source_records`, staging, DQ feeds.
- **Verification**: match-count reconciliation (1,243 / 201 / 265 / 230 per
  DATA_SOURCE_REGISTER); quarantine traceability; HUNDRED over-notation spot-checks.

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
- **Verification**: e2e per view; UI-side-analytics test (AC-22); static import
  architecture test (AC-23).

### Agent 15: Documentation Agent
- **Identifier**: `agent_documentation`
- **Core Mission**: Keep the full authoritative document suite consistent, cross-referenced,
  status-marked, and licence-correct across all seven specialised engines.
- **Responsibilities**: maintain cross-document consistency across `README/PRD/TRD/ARCHITECTURE/
  PHASES/AGENTS/AI_INSTRUCTIONS` and companion documents (`DATA_DICTIONARY`, `DATA_SOURCE_REGISTER`,
  `RANKING_SPEC`, `reports/DOCUMENTATION_REMEDIATION_AUDIT`); govern PVRE contracts, Phase 4B
  traceability, AC-01…AC-30 alignment, and 33-entity PostgreSQL schema consistency.
- **Guardrails**: no functional/business-logic changes; no architectural decisions without
  Chief Architect sign-off.
- **Verification**: markdown lint + link check; every PRD feature mapped to a PHASES phase;
  zero broken references across the 33-entity schema and 7-engine architecture.

### Agent 16: Testing & QA Agent
- **Identifier**: `agent_testing_qa`
- **Core Mission**: Design and execute the full test harness — unit, integration, statistical,
  e2e, and adversarial — across all acceptance criteria (AC-01 through AC-30).
- **Responsibilities**: full AC suite execution (AC-01…AC-30); PVRE test harness (Mode A fixtures,
  Mode B domestic career fixtures, adversarial `REVIEW_REQUIRED` collision suites); SICE
  replacement comparison tests; deterministic reproducibility assertions (`RK-1.0.0` ranking runs).
- **Verification**: 100% pass on the AC-01…AC-30 suite; zero auto-merges, zero fabricated stats,
  and zero uncalibrated probabilities.

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
