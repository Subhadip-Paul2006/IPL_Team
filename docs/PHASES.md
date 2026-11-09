# Engineering Implementation Roadmap (Phases 0 to 10)

**Project Title**: RR Squad Intelligence & Team Composition Platform
**Event**: IPL 2027 Hackathon (Rajasthan Royals scouting)
**Target Franchise**: Rajasthan Royals (RR)
**Document Version**: 2.1.0-REMEDIATED
**Status**: `[STATUS: PHASE 0 PARTIALLY_COMPLETE (0a COMPLETE / 0b OPEN) · PHASES 1–10 PLANNED]`
**Date**: November 2026
**Primary Authors**: Principal Software Architect, Cricket Data Engineer, Systems Integration Engineer

> **Revision Note (v2.1.0, remediation)**: Phase 0 is **split** and its status corrected.
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
| [PHASE 2: UNIFIED DATABASE & PIRE]  31-entity DDL, PIRE deterministic tiers  (PLANNED - MVP)        |
|       |                                                                                            |
|       v                                                                                            |
| [PHASE 3: TMVE - 3-DIMENSION MEMBERSHIP + team_season_participation + eligibility policies] (MVP)  |
|       |                                                                                            |
|       v                                                                                            |
| [PHASE 4: CDCRE DUAL CAPABILITY + AUTHORISED RESEARCH + PROVENANCE (Service C)]  (PLANNED - MVP)   |
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
| **2** | Unified Database & Player Identity Resolution | 31-entity DDL execution + migration validation, PIRE deterministic tiers | PLANNED | 1 |
| **3** | TMVE + Franchise Participation + Eligibility Policies | `team_season_participation` seeding (RR 2008–15/2016–17 suspended/2018–26; 2027 UNKNOWN), three-dimension states, versioned eligibility policies | PLANNED | 2 |
| **4** | CDCRE dual capability + external research | Candidate discovery + career retrieval; provenance (Service C); negative-verification protocol | PLANNED | 2, 3, 0b |
| **5** | CPPAE per DATA_DICTIONARY | All B/W/F/M-series metrics, sample sizes, NULL discipline | PLANNED | 2 |
| **6** | CMIE provenance-tiered context | Weather/pitch separation, timezone + match-method fields, ratings only with methodology version | PLANNED | 5 |
| **7** | MIE + Profile Generator | Orchestration (candidate-discovery-first sequence), unified reports, JSON/CSV export | PLANNED | 3, 4, 5, 6 |
| **8** | SICE + Team Builder | Role/depth/balance analysis, comparisons, Team Builder service | PLANNED | 5, 7 |
| **9** | Streamlit application | 11 views, session-state discipline, import-architecture tests | PLANNED | 7, 8 |
| **10** | Hackathon evaluation & submission | Top-10 reproducible ranking + dossiers, AC-01…AC-23 execution, submission packaging | PLANNED | 9 |

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
  31-entity DDL passing the available SQL parse (see audit report §14).
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

## 4. Phase 2 — Unified Database & Player Identity Resolution `[PLANNED - MVP]`

- **Objectives**: execute the **31-entity** DDL (migration gates: expression index on
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

## 7. Phase 5 — Complete Player Performance Analytics (CPPAE) `[PLANNED - MVP]`

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

## 8. Phase 6 — Contextual Match Intelligence (CMIE) `[PLANNED - MVP ENHANCED]`

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

## 9. Phase 7 — Player Profile Generation (MIE + Service B) `[PLANNED - MVP]`

- **Objectives**: MIE end-to-end orchestration (candidate-discovery-first sequence);
  unified provenance-traced reports; JSON/CSV export with attribution; Team Builder
  wiring to `user_teams`/`user_team_players`.
- **Subphases**: MIE routing/merge/verification-status assembly · ambiguity → user
  clarification path · Service B export + confidentiality guard · Service E wiring.
- **Inputs**: Phases 3–6 outputs.
- **Outputs**: `src/mie/`, `src/profile_gen/`, export manifests.
- **Depends on**: Phases 3, 4, 5, 6. **Checkpoints**: `request_player_intelligence(name)`
  returns a complete report with all three membership dimensions + eligibility state;
  UNVERIFIED surfaces (never resolved silently).
- **Acceptance**: AC-03, AC-20.
- **Testing**: end-to-end orchestration tests; export-contract tests; engine-import
  independence (AC-23).
- **Status**: PLANNED.

## 10. Phase 8 — Squad Intelligence & Composition (SICE + Service E) `[PLANNED - MVP]`

- **Objectives**: team management + role-aware squad evaluation; comparisons; labelled
  recommendations; no unvalidated probabilities.
- **Subphases**: Team Builder CRUD/roles/saved configs · SICE role/duplication/gap
  analysis · replacement + combination evaluation · recommendation assembly.
- **Inputs**: Phase 7 profiles; `user_teams`.
- **Outputs**: `src/squad/*`, SICE contract, squad report.
- **Depends on**: Phases 5, 7. **Checkpoints**: saved team → complete report; labels
  `ANALYTICAL_RECOMMENDATION` (AC-17).
- **Acceptance**: AC-16, AC-17.
- **Testing**: SICE fixture tests; team CRUD tests.
- **Status**: PLANNED.

## 11. Phase 9 — Streamlit Application `[PLANNED - MVP]`

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

## 12. Phase 10 — Hackathon Candidate Evaluation & Final Submission `[PLANNED]`

- **Objectives**: the **Top-10 youngest eligible uncapped candidate board** (PRD §4.3):
  reproducible role-aware ranking (versioned weights, shrinkage, age-within-role ordering),
  reserve list, per-candidate dossiers (eligibility verification, age as of evaluation date,
  roles, domestic evidence, T20 analysis, consistency, context, squad fit, risk/coverage
  limits, sources); full AC suite execution; submission packaging.
- **Subphases**: ranking model configuration (documented weights version) · Top-10 +
  reserve generation · dossier assembly (evidence tiers) · AC-01…AC-23 regression ·
  documentation reconciliation pass · confidentiality check on outputs.
- **Inputs**: Phase 9 deliverable.
- **Outputs**: `reports/FINAL_VERIFICATION_REPORT.md`, submission dossier.
- **Depends on**: Phase 9. **Checkpoints**: 100% of MVP acceptance criteria green;
  reproducibility test (same inputs + model version → same board, AC-18).
- **Acceptance**: AC-18, AC-19 (final), all green.
- **Testing**: full regression; provenance audit; ranking reproducibility.
- **Status**: PLANNED.

---

## 13. Cross-Phase Risk Assessment & Mitigation

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

---

## 14. Conclusion & Verification Summary

- **Phase 0a (documentation baseline): COMPLETE** (this remediation cycle).
- **Phase 0b (empirical data-source & licence audit): OPEN / PARTIALLY_COMPLETE** — local
  evidence (counts, ODC-By, SMAT gap) recorded in `DATA_SOURCE_REGISTER.md §3`; external
  source verification outstanding.
- **Phases 1–10: PLANNED**, with MVP core (1–9) targeting the hackathon deadline and
  post-MVP enhancements tracked separately.
- Every phase enforces its acceptance criteria and testing requirements; Service D gates
  merges. No empirical claim in this roadmap exceeds recorded evidence (register §3).
