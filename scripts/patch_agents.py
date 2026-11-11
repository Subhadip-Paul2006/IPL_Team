import os

with open('docs/AGENTS.md', 'r', encoding='utf-8') as f:
    text = f.read().replace('\r\n', '\n')

# 1. Update version header
old_hdr = '''**Document Version**: 2.1.1-TARGETED-REMEDIATION
**Status**: `[STATUS: ACTIVE OPERATING CONSTITUTION - GREENFIELD BASELINE]`
**Date**: November 2026
**Primary Authors**: Principal Software Architect, Multi-Agent Systems Engineer, Cricket Data Lead

> **Revision Note (v2.1.1, targeted remediation)**: Aligned agent contracts to the v2.1.1'''

new_hdr = '''**Document Version**: 2.2.0
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
> **Revision Note (v2.1.1, targeted remediation, retained for history)**: Aligned agent contracts to the v2.1.1'''

assert old_hdr in text
text = text.replace(old_hdr, new_hdr)

# 2. Update Hierarchy Box in Section 1
old_hierarchy = '''|   FAMILY 2: ENGINE SPECIALISTS (one per specialised engine)                                        |
|     03 PIRE Agent (identity resolution) · 04 TMVE Agent (membership) · 05 CDCRE Agent (career)     |
|     06 CPPAE Agent (performance) · 07 CMIE Agent (context) · 08 SICE Agent (squad)                 |'''

new_hierarchy = '''|   FAMILY 2: ENGINE SPECIALISTS (one per specialised engine)                                        |
|     03 PIRE Agent (identity resolution) · 04 TMVE Agent (membership) · 05 CDCRE Agent (career)     |
|     06 CPPAE Agent (performance) · 07 CMIE Agent (context) · 08 SICE Agent (squad)                 |
|     08b PVRE Agent (Engine 07: dual-mode verification & replacement intelligence)                  |'''

assert old_hierarchy in text
text = text.replace(old_hierarchy, new_hierarchy)

# 3. Update Agent 02 (MIE Orchestrator)
old_a02 = '''- **Responsibilities**: define engine I/O contracts; enforce "MIE never invents statistics";
  route ambiguous identity / CONFLICT membership to human review; assemble unified reports.'''

new_a02 = '''- **Responsibilities**: define engine I/O contracts; enforce "MIE never invents statistics";
  orchestrate PVRE Mother Controller (Engine 07) and enforce deterministic routing waterfall;
  route ambiguous identity, conflicting attributes, or unverified eligibility to the mandatory
  `REVIEW_REQUIRED` safety pathway; assemble unified player and replacement reports.'''

assert old_a02 in text
text = text.replace(old_a02, new_a02)

# 4. Update Agent 08 (SICE) and Insert Agent 08b (PVRE)
old_a08_block = '''### Agent 08: SICE Agent (Engine 06)
- **Identifier**: `agent_sice`
- **Core Mission**: Evaluate user-assembled teams: role distribution, depth, balance,
  duplication, gaps, comparisons, replacements, combinations, and recommendations; and
  own the **versioned Top-10 ranking method** (Use Case 3).
- **Responsibilities**: squad intelligence analysis; **label outputs as analytical
  recommendations, never official selections/auction decisions**; no recruitment probabilities
  unless a model is statistically validated and calibrated. **v2.1.1 (Priority F)**: SICE is
  the owner of [`RANKING_SPEC.md`](RANKING_SPEC.md) config `RK-1.0.0` — the deterministic
  three-level ordering (age → consistency → career avg B05) over a within-role relevance
  gate, with documented total-order tiebreakers (seed = 0). Every board is stored as a
  `ranking_runs` row keyed `(ranking_configurations, data_snapshot_sha256)`, so identical
  inputs reproduce exactly one board (AC-18 / AC-25). SICE composes the board into the
  Squad Intelligence Report; it does not re-derive the method inline.
- **Inputs**: `user_teams`, CPPAE/SICE-derived features, `ranking_configurations`,
  `ranking_runs`, `eligibility_policies`. **Outputs**: SICE.Output + the stored
  `ranking_runs` board (Top-10 + reserves) + recommendation labels.
- **Verification**: SICE fixture tests; recommendation-label assertion; ranking
  reproducibility test (same config + snapshot → identical stored board; re-run is a no-op).

### Agent 09: Data Ingestion Agent (Service A)'''

new_a08_and_pvre = '''### Agent 08: SICE Agent (Engine 06)
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
  1. *Mother Controller execution*: accept player requests, orchestrate pre-identity discovery
     (CDCRE), resolve canonical identity (PIRE), retrieve verified RR relationship (TMVE), assess
     IPL eligibility (Eligibility Policy Service), classify requests, and enforce deterministic
     7-step routing.
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
  5. *Output contract compilation*: emit typed, versioned `PVREOutputContract` with 23 minimum
     fields, full source provenance (`source_records`, `verification_records`), and explicit
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

### Agent 09: Data Ingestion Agent (Service A)'''

assert old_a08_block in text
text = text.replace(old_a08_block, new_a08_and_pvre)

# 5. Update Agent 15 and 16
old_a15_a16 = '''### Agent 15: Documentation Agent
- **Identifier**: `agent_documentation`
- **Core Mission**: Keep the seven documents consistent and cross-referenced, status-marked, and
  licence-correct.
- **Responsibilities**: consistency across `README/PRD/TRD/ARCHITECTURE/PHASES/AGENTS/
  AI_INSTRUCTIONS` **plus the v2.1.1 companion set** (`DATA_DICTIONARY`,
  `DATA_SOURCE_REGISTER`, `RANKING_SPEC`, `reports/DOCUMENTATION_REMEDIATION_AUDIT`);
  traceability; status markings; attribution embedding; the DDL parse gate
  (sqlglot) and `git diff --check` on every docs commit.
- **Guardrails**: no functional/business-logic changes; no architectural decisions without
  Chief Architect sign-off.
- **Verification**: markdown lint + link check; every PRD feature mapped to a PHASES phase.

### Agent 16: Testing & QA Agent
- **Identifier**: `agent_testing_qa`
- **Core Mission**: Design and execute the full test harness — unit, integration, statistical,
  e2e, and adversarial — across all acceptance criteria.
- **Responsibilities**: AC-01…AC-14 coverage; deterministic-reproducibility assertions;
  adversarial edge cases (UNVERIFIED fixtures, collision fixtures, suspension check).
- **Verification**: 100% pass on the MVP AC suite; coverage thresholds.'''

new_a15_a16 = '''### Agent 15: Documentation Agent
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
  and zero uncalibrated probabilities.'''

assert old_a15_a16 in text
text = text.replace(old_a15_a16, new_a15_a16)

with open('docs/AGENTS.md', 'w', encoding='utf-8', newline='\n') as f:
    f.write(text)

print('docs/AGENTS.md successfully updated and written!')
