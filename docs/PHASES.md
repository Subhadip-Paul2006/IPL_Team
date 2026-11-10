# Engineering Implementation Roadmap (Phases 0 to 10)

**Project Title**: RR Squad Intelligence & Team Composition Platform
**Event**: IPL 2027 Hackathon (Rajasthan Royals scouting)
**Target Franchise**: Rajasthan Royals (RR)
**Document Version**: 2.2.0
**Status**: `[STATUS: PHASE 0 PARTIALLY_COMPLETE (0a COMPLETE / 0b OPEN) · PHASES 1–10 PLANNED]`
**Date**: November 2026
**Primary Authors**: Principal Software Architect, Cricket Data Engineer, Systems Integration Engineer

> **Revision Note (v2.2.0, PVRE Dual-Mode Implementation Phase)**: Introduces **Phase 4B — PVRE
> Dual-Mode Player Verification & Research Engine** [PLANNED - MVP] into the authoritative
> implementation roadmap. Phase 4B governs the implementation of the Mother Controller,
> deterministic routing precedence, Mode A (Existing RR Player Replacement Intelligence: Module A1
> RR History, Module A2 Recent Global Performance across a configurable 2–3 year window, Module A3
> Replaceability Evidence Assessment with 5 analytical signal states), Mode B (Verified Uncapped
> Candidate Intelligence: complete domestic career discovery across Ranji, SMAT, VHT, Duleep, and
> age-groups), mandatory `REVIEW_REQUIRED` safety pathway, and SICE role-aware incumbent-vs-candidate
> replacement comparison. Reconciles database entity count to 33 entities everywhere. Adds 12 explicit
> checkpoints and maps Acceptance Criteria AC-24 through AC-30.
>
> **Revision Note (v2.1.0, remediation, retained for history)**: Phase 0 is **split** and its status corrected.
> The v2.0.0 "Phase 0 COMPLETE" claim bundled *documentation baseline completion* with
> *empirical data-source and licence verification* that the tracked repository did not
> support. Phase 0a (documentation baseline) is COMPLETE; Phase 0b (empirical data-source
> & licence audit) is **OPEN / PARTIALLY_COMPLETE**. Dataset counts are now anchored to the
> actual local lake (per `docs/DATA_SOURCE_REGISTER.md` §3: 4 directories, 1,939 match JSON
> files, **no SMAT**, ODC-By licence verified locally); superseded v1-era counts
> (2,822 incl. SMAT) are recorded as historical only.

---

## 1. Executive Roadmap Overview & Dependency Graph

```
+----------------------------------------------------------------------------------------------------+
|                          PHASE PROGRESSION & DEPENDENCY TIMELINE (REMEDIATED)                       |
+----------------------------------------------------------------------------------------------------+
| [PHASE 0a: DOCUMENTATION BASELINE]                (COMPLETE)                                       |
| [PHASE 0b: EMPIRICAL DATA-SOURCE & LICENCE AUDIT] (OPEN - PARTIALLY_COMPLETE: local evidence done;  |
|                                                external-source verification outstanding)            |
|       |                                                                                            |
|       v                                                                                            |
| [PHASE 1: HISTORICAL DATASET ACQUISITION & DATA QUALITY]  (PLANNED - MVP)                          |
|       |                                                                                            |
|       v                                                                                            |
| [PHASE 2: UNIFIED DATABASE & PIRE]  33-entity DDL, PIRE deterministic tiers  (PLANNED - MVP)        |
|       |                                                                                            |
|       v                                                                                            |
| [PHASE 3: TMVE - 3-DIMENSION MEMBERSHIP + team_season_participation + eligibility policies] (MVP)  |
|       |                                                                                            |
|       v                                                                                            |
| [PHASE 4: CDCRE DUAL CAPABILITY + AUTHORISED RESEARCH + PROVENANCE (Service C)]  (PLANNED - MVP)   |
|       |                                                                                            |
|       v                                                                                            |
| [PHASE 4B: PVRE DUAL-MODE RESEARCH & REPLACEMENT ENGINE] (PLANNED - MVP)                           |
|   - Mother Controller · Mode A (RR history + global form) · Mode B (uncapped) · REVIEW_REQUIRED    |
|       |                                                                                            |
|       v                                                                                            |
| [PHASE 5: CPPAE PER DATA_DICTIONARY]  (PLANNED - MVP)                                              |
|       |                                                                                            |
|       v                                                                                            |
| [PHASE 6: CMIE - 5 PROVENANCE TIERS, MEASURED/REPORTED SEPARATION]  (PLANNED - MVP ENHANCED)       |
|       |                                                                                            |
|       v                                                                                            |
| [PHASE 7: MIE ORCHESTRATION + PLAYER PROFILE GENERATION (Service B)]  (PLANNED - MVP)              |
|       |                                                                                            |
|       v                                                                                            |
| [PHASE 8: SICE + TEAM BUILDER (Service E)]  (PLANNED - MVP)                                        |
|       |                                                                                            |
|       v                                                                                            |
| [PHASE 9: STREAMLIT APPLICATION - 11 VIEWS]  (PLANNED - MVP)                                       |
|       |                                                                                            |
|       v                                                                                            |
| [PHASE 10: HACKATHON CANDIDATE EVALUATION (Top-10 ranking) & FINAL SUBMISSION]  (PLANNED)          |
+----------------------------------------------------------------------------------------------------+
```

**MVP vs Long-Term split**
- **Hackathon-minimum submission**: the Top-10 youngest eligible uncapped candidate board with
  reproducible ranking methodology and per-candidate evidence dossiers (PRD §4.3), plus the
  verification pipeline that supports it (Phases 1–4, 7, 10 minimum-depth execution).
- **MVP platform core (Phases 1–9)**: identity, membership, career, performance, context,
  profiles, squad composition, and the 11-view Streamlit application.
- **Post-MVP enhancements**: EAP regression, VORP/WAR, Monte Carlo campaign simulation,
  Playing XI optimizer, Impact Player engine, Next.js frontend.

### Consolidated Phase Status Matrix

| Phase # | Identifier | Target Scope | Status | Depends On |
|---|---|---|---|---|
| **0a** | Documentation baseline | All 7 core docs + PROJECT + README + register + dictionary + pre/post-audit reports | **COMPLETE** | — |
| **0b** | Empirical data-source & licence audit | Local dataset inventory (done 2026-11-10), licence verification of local archives (done), **external source licence/coverage verification (Kaggle S6/S7, HawkeyeStats S8, Open-Meteo S9, BCCI/ESPN S10–S12) — OUTSTANDING** | **OPEN / PARTIALLY_COMPLETE** | 0a |
| **1** | Historical Dataset Acquisition & Data Quality | Ingest `datasets/` (verified counts), SHA-256 manifests, quarantine, DQ/coverage baselines, SMAT gap recording | PLANNED | 0b |
| **2** | Unified Database & Player Identity Resolution | 33-entity DDL execution + migration validation, PIRE deterministic tiers | PLANNED | 1 |
| **3** | TMVE + Franchise Participation + Eligibility Policies | `team_season_participation` seeding (RR 2008–15/2016–17 suspended/2018–26; 2027 UNKNOWN), three-dimension states, versioned eligibility policies | PLANNED | 2 |
| **4** | CDCRE dual capability + external research | Candidate discovery + career retrieval; provenance (Service C); negative-verification protocol | PLANNED | 2, 3, 0b |
| **4B** | PVRE Dual-Mode Player Verification & Research Engine | Mother Controller routing, Mode A (RR history + recent global form 2–3 yr window + replaceability assessment), Mode B (full domestic career discovery + independent eligibility verification), mandatory `REVIEW_REQUIRED` safety pathway, SICE replacement comparison integration | PLANNED | 2, 3, 4 |
| **5** | Complete Player Performance Analytics | DATA_DICTIONARY-governed profiles (B/W/F/M), integer-ball bowling notation, derived_features persistence, scorecard reconciliation | PLANNED | 2 |
| **6** | CMIE provenance-tiered context | Weather/pitch separation, timezone + match-method fields, ratings only with methodology version | PLANNED | 5 |
| **7** | MIE + Profile Generator | Orchestration (candidate-discovery-first sequence), unified reports, JSON/CSV export | PLANNED | 3, 4, 5, 6 |
| **8** | SICE + Team Builder | Role/depth/balance analysis, comparisons, Team Builder service | PLANNED | 5, 7 |
| **9** | Streamlit application | 11 views, session-state discipline, import-architecture tests | PLANNED | 7, 8 |
| **10** | Hackathon evaluation & submission | Top-10 reproducible ranking + dossiers, AC-01…AC-30 execution, submission packaging | PLANNED | 9 |

---

## 2. Phase 0 — Documentation & Empirical Audit

### 2.0a Documentation Baseline — **COMPLETE**
Objectives: inspect the workspace; produce the authoritative documentation suite; reconcile
v1/v2 architecture.
- Subphases: repo inspection · suite authoring (PRD, TRD, ARCHITECTURE, PHASES, AGENTS,
  AI_INSTRUCTIONS, docs/README, README, PROJECT) · data-path correction (`datasets/`) ·
  v2.1.0 remediation (this cycle: DDL fixes, participation entity, 3-dimension membership,
  PIRE terminology, CDCRE dual capability, `agent_cdcre`, Phase 0 split, register +
  dictionary creation).
- Inputs: repository, `.agents/teamwork` evidence, local `datasets/`.
- Outputs: the 10 remediated/created docs + `reports/DOCUMENTATION_REMEDIATION_AUDIT.md`.
- **Depends on**: — · **Checkpoint**: all docs consistent at entity count 31, `agent_cdcre`,
  33-entity DDL passing the available SQL parse (see audit report §14 and TRD §11.5).
- **Acceptance**: cross-doc consistency (Part 17 list) verified; broken internal link count 0
  (audit report §12). **Testing**: link checker + sqlglot parse + consistency greps.
- **Status**: **COMPLETE** (as of this remediation commit).

### 2.0b Empirical Data-Source & Licence Audit — **OPEN (PARTIALLY_COMPLETE)**
Objectives: establish evidenced availability/licence status for **every** source in
`docs/DATA_SOURCE_REGISTER.md`.
- Subphases:
  1. **Local inventory (DONE 2026-11-10)**: 4 directories, counts 1,243/201/265/230
     (`DATA_SOURCE_REGISTER.md §3`), ODC-By LICENSE.txt inspected for all four, SMAT absent
     (recorded `UNAVAILABLE` locally), withheld-match notes recorded (ODI WC −24, T20 WC −29).
  2. **External licence/coverage verification (OUTSTANDING)**: Kaggle S6/S7 terms + actual
     columns; HawkeyeStats S8 repo licence + schema/units + that it is third-party, not
     official Hawk-Eye; Open-Meteo S9 current licence terms; BCCI/ESPN/Cricbuzz S10–S12
     access restrictions. Each produces a dated, evidence-linked `data_sources` row.
  3. **Kaggle 2007 quarantine rule validation**: confirm any 2007-labelled IPL records are
     pre-IPL/exhibition and route to quarantine.
- Inputs: register, external source terms-of-use pages (authorised inspection).
- Outputs: register rows upgraded from UNVERIFIED/RESTRICTED to VERIFIED/PARTIALLY_VERIFIED
  with `license_evidence`; the SMAT `UNAVAILABLE` status reconfirmed or superseded by an
  acquisition decision.
- **Depends on**: 0a · **Checkpoint**: every register source row has a `license_status` +
  dated evidence reference · **Acceptance**: Phase 1 may only start on the local-verified
  subset; external claims route through CDCRE research, not ingestion assumptions.
- **Testing**: register audit diff (no source row without dated evidence).
- **Status**: **PARTIALLY_COMPLETE / OPEN** — local evidence done; external verification
  outstanding.

> **Phase 0 as a whole is not marked complete.** The documentation baseline (0a) is complete;
> the empirical audit (0b) remains open. No dataset count is claimed beyond the locally
> verified figures; the superseded "2,822 files incl. SMAT" is historical only.

---

<a id="3-phase-1--historical-dataset-acquisition--data-quality"></a>
## 3. Phase 1 — Historical Dataset Acquisition & Data Quality `[PLANNED - MVP]`

- **Objectives**: fault-tolerant ingestion of `datasets/`; SHA-256 immutable staging;
  quarantine; Data Quality & Coverage baseline (Service D).
- **Subphases**: (1) checksum/manifest per dataset folder (counts 1,243/201/265/230; SMAT
  gap recorded, not fabricated) · (2) polymorphic parser (CricSheet JSON v1.3.0) ·
  (3) quarantine staging incl. the 2007-pre-IPL rule for any future Kaggle acquisition ·
  (4) DQ baseline (duplicates, conflicts, missing; innings↔delivery consistency checks).
- **Inputs**: `datasets/` (local, read-only), `DATA_SOURCE_REGISTER.md` statuses.
- **Outputs**: `src/ingestion/*`, manifest, `source_records`, DQ report.
- **Depends on**: 0b local-verified subset. **Checkpoints**: per-dataset count = register
  verified count; zero unhandled parser exceptions; DQ baseline report exists.
- **Acceptance**: AC-19 (count reconciliation vs register; quarantine assertion).
- **Testing**: parser unit tests, ingestion SQL counts, quarantine assertion.
- **Status**: PLANNED.

<a id="4-phase-2--unified-database--player-identity-resolution"></a>
## 4. Phase 2 — Unified Database & Player Identity Resolution `[PLANNED - MVP]`

- **Objectives**: execute the **33-entity** DDL (migration gates: expression index on
  `derived_features`; FKs on partitioned `deliveries` (PG15+ requirement; pre-15 fallback =
  Service D checks); composite `(delivery_id, season_year)` fielding link); PIRE with
  deterministic tiers + contextual attribute corroboration.
- **Subphases**: DDL migration + FK/partition validation · ELT raw→normalised · PIRE tier
  implementation · alias registry + review queue.
- **Inputs**: Phase 1 staging; CricSheet `people` hashes.
- **Outputs**: `migrations/V001__*.sql` (+ `V002__participation_membership.sql`),
  `src/pir/identity_resolver.py`, populated `players`/`player_aliases`.
- **Depends on**: Phase 1. **Checkpoints**: FK integrity zero orphans; PIRE fixture suite
  with zero auto-merges; no numeric confidence exposed without `calibrated=TRUE`.
- **Acceptance**: AC-01, AC-02, AC-15.
- **Testing**: adversarial collision suite; FK integrity queries; partition-pruning sanity.
- **Status**: PLANNED.

<a id="5-phase-3--team-membership-verification-tmve"></a>
## 5. Phase 3 — Team Membership Verification (TMVE) `[PLANNED - MVP]`

- **Objectives**: three-dimension membership (relationship · currency ·
  season-bound/policy-versioned eligibility); franchise participation seeding;
  negative-verification protocol (TRD §4.5); verification-hierarchy research hooks.
- **Subphases**: (1) seed `team_season_participation` (RR×IPL 2008–2015 PARTICIPATING/
  VERIFIED; 2016 & 2017 SUSPENDED/VERIFIED (BCCI suspension notice = tier-1 evidence);
  2018–2026 PARTICIPATING/VERIFIED; 2027 UNKNOWN until authoritative evidence) ·
  (2) populate `squad_memberships` + `player_team_history` for RR windows with
  verified-appearance counts · (3) author `eligibility_policies` v1 for the target season
  (BCCI/IPL rule reference, effective dates, verified) · (4) `player_membership_state`
  evaluation service + `NOT_ASSESSED` eligibility default · (5) negative-verification
  workflow (human-review gated).
- **Inputs**: Phase 2 registry; official records (Service C).
- **Outputs**: `src/membership/tmve.py`, populated participation/membership/eligibility
  tables, TMVE contract.
- **Depends on**: Phase 2. **Checkpoints**: every RR player row carries all three dimensions;
  suspension rows exist for RR only (IPL seasons for other teams unaffected); 2027 UNKNOWN.
- **Acceptance**: AC-04, AC-05, AC-06, AC-08, AC-09.
- **Testing**: per-dimension fixture tests; suspension assertions; negative-verification
  audit fixture.
- **Status**: PLANNED.

<a id="6-phase-4--career-discovery--external-research-cdcre"></a>
## 6. Phase 4 — Career Discovery & External Research (CDCRE) `[PLANNED - MVP]`

- **Objectives**: dual CDCRE capabilities; four-state coverage; authorised research with
  provenance (Service C); SMAT gap handling.
- **Subphases**: (1) `player_competition_history` population + coverage-state logic ·
  (2) career gap detection (incl. franchise suspension windows, dataset availability) ·
  (3) candidate discovery (pre-identity, raw-name) service · (4) external research
  integration per TRD §4.2 hierarchy → `verification_records` · (5) coverage/provenance
  report.
- **Inputs**: Phases 2/3; external sources (register-governed).
- **Outputs**: `src/research/cdcre.py`, populated coverage tables, provenance records.
- **Depends on**: Phases 2, 3, 0b (external licence status where used).
- **Checkpoints**: no dataset-absence reported as non-participation; candidate discovery
  works without a player_id (AC-10).
- **Acceptance**: AC-07, AC-10, AC-11.
- **Testing**: coverage-state audit on sampled players; provenance completeness; AC-10
  contract test.
- **Status**: PLANNED.

<a id="7-phase-4b--player-verification--research-engine-pvre-dual-mode"></a>
## 7. Phase 4B — PVRE Dual-Mode Player Verification & Research Engine `[PLANNED - MVP]`

- **Status**: `[STATUS: PLANNED - GREENFIELD BASELINE]`
- **Objective**: Implement and validate Engine 07 (PVRE), the specialised dual-mode research and
  verification engine orchestrated by MIE. PVRE equips Rajasthan Royals decision-makers with the
  intelligence required to evaluate whether an existing RR incumbent can be replaced by a younger,
  verified-eligible uncapped talent (Mode A), or to execute deep, multi-format domestic career
  discovery for uncapped prospects (Mode B). It enforces an inviolable, non-bypassable
  `REVIEW_REQUIRED` safety pathway whenever identity, membership, or eligibility evidence is
  conflicting or incomplete.
- **Scope**:
  1. Mother Controller lifecycle, request classification, and deterministic 7-step routing waterfall.
  2. Mode A: Module A1 (RR historical research, squad membership vs match appearances separation).
  3. Mode A: Module A2 (recent global performance research across 2–3 year configurable window in
     recognised leagues: BBL, PSL, CPL, SA20, The Hundred, International, and Indian domestic).
  4. Mode A: Module A3 (replaceability evidence assessment; analytical signals: `RETAIN_SIGNAL`,
     `MONITOR_SIGNAL`, `POTENTIALLY_REPLACEABLE`, `INSUFFICIENT_EVIDENCE`, `REVIEW_REQUIRED`).
  5. Mode B: Uncapped candidate career discovery across Ranji Trophy, SMAT, VHT, Duleep, and
     age-groups, with independent policy verification (absence is never proof of uncapped status).
  6. Mandatory `REVIEW_REQUIRED` safety state with structured review dossiers.
  7. Typed, versioned request and response contracts (`PVREOutputContract` with all 26 mandatory fields per R2.7).
  8. Downstream integration with SICE for 16-dimension role-aware incumbent-vs-candidate replacement
     comparisons.
- **Subphases**:
  - **4B.1 Mother Controller & Classification Engine**: Request ingestion, pre-identity discovery
    hook, PIRE identity resolution, TMVE membership retrieval, Eligibility Policy Service check,
    deterministic routing waterfall, and retry management.
  - **4B.2 Mode A RR Historical & Recent Global Research Modules**:
    * *Module A1 (RR History)*: Scorecard join vs squad membership, batting/bowling/fielding/keeping
      career tables, phase splits, role changes across 2008–2015 and 2018–2026.
    * *Module A2 (Recent Global Form)*: Multi-league connectors (BBL, PSL, CPL, SA20, The Hundred,
      Intl, Ranji, SMAT, VHT), 2–3 year configurable window, sample size tracking, format-tagged
      metrics, verified injury/availability integration.
  - **4B.3 Mode A Replaceability Evidence Assessment**: Signal synthesis algorithm generating
    `RETAIN_SIGNAL`, `MONITOR_SIGNAL`, `POTENTIALLY_REPLACEABLE`, `INSUFFICIENT_EVIDENCE`, or
    `REVIEW_REQUIRED` without arbitrary thresholds or fabricated release probabilities.
  - **4B.4 Mode B Uncapped Discovery & Policy Verification**: Domestic competition extractors,
    match-level aggregations, senior international cap verification, policy validation under active
    `eligibility_policies` version, and affirmative uncapped pool registration.
  - **4B.5 Mandatory `REVIEW_REQUIRED` Safety Pathway & Audit Dossier**: Interceptor for identity
    ambiguity, DOB conflicts, membership contradictions, unverified eligibility, source conflicts,
    and missing samples; compiles structured review dossiers and blocks automated pool entry.
  - **4B.6 SICE Replacement Integration**: Implementation of the 16-dimension role-aware comparison
    protocol and durable `ranking_runs` storage.
- **Inputs**:
  - Phase 1 staged datasets (`datasets/`).
  - Phase 2 canonical player registry (`players`, `player_aliases`).
  - Phase 3 three-dimension membership state (`player_membership_state`, `team_season_participation`).
  - Phase 3 active eligibility policy (`eligibility_policies`, `player_eligibility`).
  - Phase 4 CDCRE candidate discovery and career discovery capabilities.
- **Outputs**:
  - `src/pvre/mother_controller.py`: Mother Controller and classification router.
  - `src/pvre/mode_a/rr_history.py`: Module A1 RR historical performance analyzer.
  - `src/pvre/mode_a/global_performance.py`: Module A2 recent global performance research.
  - `src/pvre/mode_a/replaceability_assessor.py`: Module A3 replaceability signal generator.
  - `src/pvre/mode_b/uncapped_intelligence.py`: Mode B domestic discovery & verification engine.
  - `src/pvre/safety/review_handler.py`: Mandatory `REVIEW_REQUIRED` dossier generator.
  - `src/pvre/contracts.py`: Typed `PVRERequestContract` and `PVREOutputContract` models.
  - Populated `derived_features` rows (`feature_set_name = 'pvre_replacement_assessment'`).
  - Populated `verification_records` audit entries.
- **Dependencies**: Phase 2 (PIRE), Phase 3 (TMVE & Eligibility Service), Phase 4 (CDCRE),
  Phase 0b (External source verification).
- **Implementation Sequence**:
  1. Author Pydantic/dataclass contracts (`PVRERequestContract`, `PVREOutputContract`).
  2. Implement Mother Controller classification logic and routing waterfall.
  3. Implement Module A1 (RR history) with strict appearance vs squad membership separation.
  4. Implement Module A2 (Global form) with 2–3 year window boundary enforcement and multi-league
     format tagging.
  5. Implement Module A3 (Replaceability assessment) signal synthesis.
  6. Implement Mode B domestic discovery and affirmative policy verification.
  7. Implement `REVIEW_REQUIRED` safety interceptor and review dossier generation.
  8. Integrate PVRE output into SICE role-aware replacement comparison protocol.
  9. Execute comprehensive test suite covering all routing branches and edge cases.
- **Checkpoints (12 Explicit Verification Gates)**:
  1. *Mother Controller and classification*: Correctly dispatches requests to Mode A, Mode B,
     `REVIEW_REQUIRED`, or `OUT_OF_SCOPE` without guessing.
  2. *Existing RR association routing*: All players with `CURRENT_RR`, `HISTORICAL_RR_APPEARED`,
     or `HISTORICAL_RR_SQUAD_ONLY` deterministically enter Mode A.
  3. *RR historical research*: Scorecard appearances strictly separated from squad inclusion;
     zero batting/bowling stats credited for squad-only seasons.
  4. *Recent global performance research*: Accurately bounds performance to the 2–3 year
     configurable window; captures recognised leagues with visible sample sizes; format tags
     prevent cross-format contamination.
  5. *Replaceability evidence assessment*: Produces one of the 5 valid signal states with
     traceable component scores; generates zero standalone release decisions.
  6. *Uncapped candidate research*: Covers Ranji, SMAT, VHT, Duleep, and age-group matches without
     assuming uncapped status from database absence.
  7. *Eligibility verification*: Uncapped candidates carry verified affirmative proof under the
     active target-season policy; zero senior international caps.
  8. *`REVIEW_REQUIRED` handling*: Hard safety interceptor triggers on all ambiguous or conflicting
     fixtures, generating structured review dossiers and blocking candidate pool entry.
  9. *Shared output contract*: Contract validates all 26 mandatory fields per R2.7 with explicit null,
     unavailable, not-established, verified, and conflict semantics.
  10. *CPPAE/CMIE integration*: Performance metrics and contextual conditions seamlessly feed
      the PVRE research scope without introducing circular dependencies.
  11. *SICE incumbent-vs-candidate comparison*: SICE successfully compares incumbent dossiers and
      candidate profiles across 16 role-aware dimensions, emitting versioned analytical
      recommendations.
  12. *End-to-end acceptance tests*: Full test harness executes successfully across all PVRE
      acceptance criteria (AC-24 through AC-30).
- **Acceptance Criteria**: AC-24, AC-25, AC-26, AC-27, AC-28, AC-29, AC-30.
- **Explicit Test Scenarios (10 Mandatory Test Fixtures)**:
  1. *Verified RR Incumbent Scenario*: Input fixture Sanju Samson ($t_{\text{eval}} = \text{2026-11-01}$). PIRE resolves player ID; TMVE confirms `CURRENT_RR`; Module A1 analyzes RR seasons (2013–2015, 2018–2026); Module A2 assesses 2–3 yr global/international window; Module A3 emits `RETAIN_SIGNAL`. Profile forwarded to SICE. Assert: `route_status = 'ROUTED_RR_INCUMBENT'`, `replaceability_assessment = 'RETAIN_SIGNAL'`. Failure condition: conflating squad inclusion with match appearances or failing to bound recent window.
  2. *Historical RR Player Scenario*: Input fixture Ajinkya Rahane / Shane Watson / Squad-only alumnus. PIRE resolves player ID; TMVE confirms `HISTORICAL_RR_APPEARED` or `HISTORICAL_RR_SQUAD_ONLY`, currency `FORMER_RR`; Module A1 accurately isolates RR tenure; Module A2 analyzes recent global form outside RR; Module A3 emits analytical signal. Assert: `route_status = 'ROUTED_RR_INCUMBENT'`, `rr_relationship_state = 'HISTORICAL_RR_*'`. Failure condition: missing historical RR seasons or crediting batting/bowling statistics for squad-only alumni (`appearances = 0`).
  3. *Verified Uncapped Candidate Scenario*: Input fixture domestic T20 breakout performer (e.g. young SMAT star). PIRE resolves identity; TMVE confirms `NO_VERIFIED_RR_RELATIONSHIP`; Eligibility Policy Service verifies 0 international caps and target policy compliance; Module B retrieves domestic career across SMAT, VHT, Ranji; enters candidate pool. Assert: `route_status = 'ROUTED_UNCAPPED_CANDIDATE'`, `ipl_uncapped_eligibility = 'VERIFIED_ELIGIBLE'`. Failure condition: admitting candidate without affirmative policy verification.
  4. *Verified Capped Non-RR Player Scenario*: Input fixture Virat Kohli / Jasprit Bumrah. PIRE resolves identity; TMVE confirms `NO_VERIFIED_RR_RELATIONSHIP`; international caps verified; player is CAPPED; deterministically routes to `OUT_OF_SCOPE`. Assert: `route_status = 'ROUTED_OUT_OF_SCOPE'`, `player_capped_status = 'CAPPED'`, candidate pool entry blocked. Failure condition: permitting a capped player into Mode B uncapped candidate pool.
  5. *Unknown Player Absent from Database Scenario*: Input fixture newly registered domestic U-19 prospect absent from internal DB. Mother Controller triggers CDCRE candidate discovery (no player_id); defaults `player_capped_status = 'UNVERIFIED'`, `ipl_uncapped_eligibility = 'NOT_ASSESSED'`; routes to `REVIEW_REQUIRED`. Assert: `route_status = 'ROUTED_SAFETY_REVIEW'`, `review_status = 'REVIEW_REQUIRED'`, `review_reason_codes` contains `UNKNOWN_PLAYER_NOT_IN_DATABASE`. Failure condition: auto-assuming unknown player is uncapped.
  6. *Duplicate Identities Scenario*: Input fixture two distinct domestic players with identical names ("Amit Sharma"). PIRE detects ambiguous match with multiple candidate entities and distinct birth dates/state associations; Mother Controller halts automated processing; flags identity collision; compiles candidate dossiers. Assert: `route_status = 'ROUTED_SAFETY_REVIEW'`, `review_reason_codes` contains `COLLISION_MULTIPLE_IDENTITIES`. Failure condition: auto-merging distinct players or silently picking first match.
  7. *Conflicting DOB or Membership Evidence Scenario*: Input fixture passport DOB 2004-05-10 vs BCCI tournament roster DOB 2003-11-22. Provenance engine detects conflicting assertions across sources; flags `CONFLICT`; persists both claims in `verification_records`; routes immediately to `REVIEW_REQUIRED`. Assert: `route_status = 'ROUTED_SAFETY_REVIEW'`, `review_reason_codes` contains `CONFLICT_DOB_RECORD`. Failure condition: overwriting or silently averaging conflicting dates of birth.
  8. *Missing Domestic Datasets Scenario*: Input fixture player participated in SMAT 2020 or Vinoo Mankad 2022 (unindexed season in data lake). Domestic discovery detects unindexed seasons in data lake; flags `career_coverage_state = 'PARTIAL_COVERAGE'`; lists missing tournaments; evaluates metrics over available sample only. Assert: `career_coverage_state = 'PARTIAL_COVERAGE'`, `missing_competitions` populated. Failure condition: treating missing datasets as evidence of non-participation.
  9. *Conflicting External Sources Scenario*: Input fixture ESPNcricinfo reports 35 matches, BCCI scorecards verify 32. Provenance tracker flags statistical discrepancy across providers; marks `verification_status = 'CONFLICT'`; compiles review dossier with conflicting source IDs. Assert: `route_status = 'ROUTED_SAFETY_REVIEW'`, `review_reason_codes` contains `CONFLICTING_CAREER_STATISTICS`. Failure condition: silently adopting unverified third-party numbers over verified scorecards.
  10. *Incomplete Career Coverage Scenario*: Input fixture player debuted in 2018, but verified scorecards available only from 2022. System identifies truncated temporal coverage; sets `career_coverage_state = 'PARTIAL_COVERAGE'`; computes sample indicators; attaches `COVERAGE_LIMITED` flags; does not extrapolate. Assert: `career_coverage_state = 'PARTIAL_COVERAGE'`, sample indicators explicitly displayed. Failure condition: extrapolating or interpolating missing seasons.
- **Failure Conditions**:
  - Any unknown player automatically assumed to be uncapped.
  - Any squad-only player credited with match appearances or performance metrics.
  - Cross-format statistics merged without format tagging.
  - A standalone player release or retention decision made inside PVRE.
  - An ambiguous identity or conflicting DOB bypassing `REVIEW_REQUIRED`.
  - Top-10 hackathon ranking logic merged into incumbent replacement evaluation.
- **Data & Provenance Requirements**: Every external datum must link to a `source_records` row and
  a `verification_records` assertion with documented tier, provider, timestamp, and licence.
- **Completion Evidence**: Test execution reports demonstrating 100% pass rate on AC-24..AC-30,
  zero auto-merges, zero fabricated stats, and verified contract compliance.

---

<a id="8-phase-5--complete-player-performance-analytics-cppae"></a>
<a id="7-phase-5--complete-player-performance-analytics-cppae"></a>
## 8. Phase 5 — Complete Player Performance Analytics (CPPAE) `[PLANNED - MVP]`

- **Objectives**: DATA_DICTIONARY-governed batting/bowling/fielding/wicketkeeping/
  match-contribution profiles; integer-ball bowling notation; format tags; sample sizes.
- **Subphases**: metric implementation families B/W/F/M (dictionary §1–4) · `derived_features`
  persistence (unique expression index; `status` class) · reconciliation views
  (scorecard ↔ ball-level, Service D).
- **Inputs**: normalised scorecard tables.
- **Outputs**: `src/analytics/*`, populated `derived_features`, CPPAE contract.
- **Depends on**: Phase 2. **Checkpoints**: zero zero-imputed stats; every metric maps to a
  dictionary entry with all ten attributes; NOT_COMPUTABLE list enforced (false shots).
- **Acceptance**: AC-12, AC-13.
- **Testing**: statistical unit tests vs known scorecards; NULL-safety lint; dictionary
  completeness audit.
- **Status**: PLANNED.

<a id="9-phase-6--contextual-match-intelligence-cmie"></a>
<a id="8-phase-6--contextual-match-intelligence-cmie"></a>
## 9. Phase 6 — Contextual Match Intelligence (CMIE) `[PLANNED - MVP ENHANCED]`

- **Objectives**: 5-tier provenance conditions; weather-as-context discipline (timezone +
  match-method fields); pitch reporting preserved as text; numeric ratings only with a
  validated methodology version; no mental-state inference; injury/availability verified-only.
- **Subphases**: weather backfill (Open-Meteo, pending 0b licence confirmation) ·
  `pitch_conditions` reported-description + optional ratings · phase/RRR/target/result
  annotations · provenance-tier tagging.
- **Inputs**: matches, venues, weather, pitch records.
- **Outputs**: populated `weather_conditions`/`pitch_conditions`, CMIE contract.
- **Depends on**: Phases 2, 5 (and 0b for weather source status).
- **Checkpoints**: 100% of IPL night fixtures enriched or explicitly `UNKNOWN`; weather never
  labelled pitch; ratings require methodology version (AC-14).
- **Testing**: weather-linkage test; provenance-tier audit; default audit (no false-claim
  defaults survive, per TRD D8).
- **Status**: PLANNED.

<a id="10-phase-7--player-profile-generation-mie--service-b"></a>
<a id="9-phase-7--player-profile-generation-mie--service-b"></a>
## 10. Phase 7 — Player Profile Generation (MIE + Service B) `[PLANNED - MVP]`

- **Objectives**: MIE end-to-end orchestration (candidate-discovery-first sequence);
  PVRE Mother Controller routing (Mode A / Mode B / REVIEW_REQUIRED); unified
  provenance-traced reports; JSON/CSV export with attribution; Team Builder wiring
  to `user_teams`/`user_team_players`.
- **Subphases**: MIE routing/merge/verification-status assembly · ambiguity → user
  clarification path · Service B export + confidentiality guard · Service E wiring.
- **Inputs**: Phases 3–6 outputs; Phase 4B (PVRE) player research dossiers.
- **Outputs**: `src/mie/`, `src/profile_gen/`, export manifests.
- **Depends on**: Phases 3, 4, 4B, 5, 6. **Checkpoints**: `request_player_intelligence(name)`
  returns a complete report with all three membership dimensions + eligibility state;
  UNVERIFIED surfaces (never resolved silently).
- **Acceptance**: AC-03, AC-20.
- **Testing**: end-to-end orchestration tests; export-contract tests; engine-import
  independence (AC-23).
- **Status**: PLANNED.

<a id="11-phase-8--squad-intelligence--composition-sice--service-e"></a>
<a id="10-phase-8--squad-intelligence--composition-sice--service-e"></a>
## 11. Phase 8 — Squad Intelligence & Composition (SICE + Service E) `[PLANNED - MVP]`

- **Objectives**: team management + role-aware squad evaluation; SICE incumbent-vs-candidate
  replacement evaluation (§8.4) consuming PVRE Mode A replaceability assessments across 16
  dimensions; comparisons; labelled recommendations; no unvalidated probabilities; durable
  storage in `ranking_runs` (`run_type = 'REPLACEMENT_EVALUATION'`).
- **Subphases**: Team Builder CRUD/roles/saved configs · SICE role/duplication/gap
  analysis · replacement + combination evaluation · recommendation assembly.
- **Inputs**: Phase 7 profiles; Phase 4B (PVRE) replaceability assessments; `user_teams`.
- **Outputs**: `src/squad/*`, SICE contract, squad report.
- **Depends on**: Phases 4B, 5, 7. **Checkpoints**: saved team → complete report; labels
  `ANALYTICAL_RECOMMENDATION` (AC-17).
- **Acceptance**: AC-16, AC-17.
- **Testing**: SICE fixture tests; team CRUD tests.
- **Status**: PLANNED.

<a id="12-phase-9--streamlit-application"></a>
<a id="11-phase-9--streamlit-application"></a>
## 12. Phase 9 — Streamlit Application `[PLANNED - MVP]`

- **Objectives**: 11-view application on MIE/engine contracts; UI separated from analytics;
  cautious session state.
- **Subphases**: scaffold + navigation · per-view thin adapters · verification-report view
  (provenance + UNVERIFIED/CONFLICT listing) · Mermaid + link + architecture test gates
  (including the deferred Mermaid parser-validation gate).
- **Inputs**: MIE/engine/service contracts.
- **Outputs**: `app/streamlit/` + UI test suite.
- **Depends on**: Phases 7, 8. **Checkpoints**: all 11 views render; no engine imports
  Streamlit (AC-22/AC-23).
- **Acceptance**: AC-22, AC-23.
- **Testing**: e2e per view; import-architecture test.
- **Status**: PLANNED.

<a id="13-phase-10--hackathon-candidate-evaluation--final-submission"></a>
<a id="12-phase-10--hackathon-candidate-evaluation--final-submission"></a>
## 13. Phase 10 — Hackathon Candidate Evaluation & Final Submission `[PLANNED]`

- **Objectives**: the **Top-10 youngest eligible uncapped candidate board** (PRD §4.3):
  reproducible role-aware ranking per [`docs/RANKING_SPEC.md`](RANKING_SPEC.md) (`RK-1.0.0`),
  reserve list, per-candidate dossiers (eligibility verification, age as of evaluation date,
  roles, domestic evidence, T20 analysis, consistency, context, squad fit, risk/coverage
  limits, sources); strict architectural separation from PVRE Mode A incumbent replacement
  evaluation; full AC suite execution (AC-01…AC-30); submission packaging.
- **Subphases**: ranking model configuration (documented weights version) · Top-10 +
  reserve generation · dossier assembly (evidence tiers) · AC-01…AC-30 regression ·
  documentation reconciliation pass · confidentiality check on outputs.
- **Inputs**: Phase 9 deliverable.
- **Outputs**: `reports/FINAL_VERIFICATION_REPORT.md`, submission dossier.
- **Depends on**: Phase 9. **Checkpoints**: 100% of MVP acceptance criteria green;
  reproducibility test (same inputs + model version → same board, AC-18).
- **Acceptance**: AC-18, AC-19 (final), all green.
- **Testing**: full regression; provenance audit; ranking reproducibility.
- **Status**: PLANNED.

---

<a id="14-cross-phase-risk-assessment--mitigation"></a>
<a id="13-cross-phase-risk-assessment--mitigation"></a>
## 14. Cross-Phase Risk Assessment & Mitigation

| # | Risk | Severity | Phase | Mitigation |
|---|---|---|---|---|
| **R1** | Parser crash on malformed records | High | 1 | Quarantine with traces; run continues |
| **R2** | Similar-name collisions | Critical | 2 | PIRE tier-first; never auto-merge; human review |
| **R3** | Missing context (tracking/weather) | Medium | 6 | Nullable enrichment; NULL never 0.0; 5 provenance tiers |
| **R4** | Super Over contamination | Critical | 1, 5 | `is_super_over` hard exclusion in all career views |
| **R5** | DLS truncation distorting run rates | High | 5 | Revised targets/overs ingested; dynamic phase scaling |
| **R6** | False "never played / uncapped" classification | Critical | 3, 4 | Negative-verification requirements (TRD §4.5); `UNKNOWN`/`NOT_ASSESSED` defaults |
| **R7** | RR suspension mis-modelled | High | 3 | `team_season_participation` franchise rows; AC-06 assertions |
| **R8** | Unverified research polluting reports | Critical | 4, 7 | `verification_records` tiers + CONFLICT→human review; MIE no auto-resolve |
| **R9** | UI performing analytics | Medium | 9 | Import-architecture test (AC-23) |
| **R10** | Proprietary dataset leakage | High | 10 | Isolated handling; exports never include it (AC-20) |
| **R11** | FK support on partitioned `deliveries` below PG 15 | Medium | 2 | Target engine is PG16; documented fallback to Service D reconciliation checks |
| **R12** | External source licence misassumption (Kaggle/Hawkeye) | High | 0b, 4 | Register statuses RESTRICTED/UNVERIFIED until 0b evidence rows; no ingestion on unverified terms |
| **R13** | PVRE multi-league coverage gaps lead to false non-participation assumptions | High | 4B | Enforce four-state coverage tracking (`DATASET_UNAVAILABLE`/`NOT_ESTABLISHED`); mandate that missing datasets are never treated as non-participation; report sample sizes explicitly alongside every recent-form metric |
| **R14** | Mode A replacement evaluation exhibits role bias or uncalibrated replacement scores | High | 4B, 8 | Enforce role-aware comparison protocol across 16 dimensions; prohibit arbitrary single composite replacement scores; report component metrics transparently; label all outputs ANALYTICAL_RECOMMENDATION |

---

## 15. Conclusion & Verification Summary

- **Phase 0a (documentation baseline): COMPLETE** (this remediation cycle).
- **Phase 0b (empirical data-source & licence audit): OPEN / PARTIALLY_COMPLETE** — local
  evidence (counts, ODC-By, SMAT gap) recorded in `DATA_SOURCE_REGISTER.md §3`; external
  source verification outstanding.
- **Phases 1–10: PLANNED**, with MVP core (1–9) targeting the hackathon deadline and
  post-MVP enhancements tracked separately.
- Every phase enforces its acceptance criteria and testing requirements; Service D gates
  merges. No empirical claim in this roadmap exceeds recorded evidence (register §3).
