# Engineering Implementation Roadmap (Phases 0 to 10)

**Project Title**: RR Squad Intelligence & Team Composition Platform
**Event**: IPL 2027 Hackathon
**Target Franchise**: Rajasthan Royals (RR)
**Document Version**: 2.0.0-ARCH-REVISION
**Status**: `[STATUS: PHASE 0 COMPLETE / PHASES 1-10 PLANNED]`
**Date**: November 2026
**Primary Authors**: Principal Software Architect, Cricket Data Engineer, Systems Integration Engineer

> **Revision Note (v2.0.0)**: The roadmap was revised from 9 phases (0–8) to **11 phases (0–10)**
> to reflect the new architecture: dedicated phases for the Membership Verification Engine,
> Career Discovery & external research, Streamlit application delivery, and a final Hackathon
> Candidate Evaluation phase. Each phase defines **Objectives, Subphases, Inputs, Outputs,
> Dependencies, Checkpoints, Acceptance Criteria, Testing Requirements, and Completion Status**.
> MVP-essential features are prioritised against the hackathon deadline; long-term enhancements
> are explicitly separated.

---

## 1. Executive Roadmap Overview & Dependency Graph

```
+----------------------------------------------------------------------------------------------------+
|                          PHASE PROGRESSION & DEPENDENCY TIMELINE (REVISED)                         |
+----------------------------------------------------------------------------------------------------+
| [PHASE 0: DOCUMENTATION & RESEARCH AUDIT]  (COMPLETE)                                             |
|       |                                                                                            |
|       v                                                                                            |
| [PHASE 1: HISTORICAL DATASET ACQUISITION & DATA QUALITY]  (PLANNED - MVP)                          |
|       |                                                                                            |
|       v                                                                                            |
| [PHASE 2: UNIFIED DATABASE & PLAYER IDENTITY RESOLUTION (PIRE)]  (PLANNED - MVP)                   |
|       |                                                                                            |
|       v                                                                                            |
| [PHASE 3: TEAM MEMBERSHIP VERIFICATION ENGINE (TMVE)]  (PLANNED - MVP)                             |
|       |                                                                                            |
|       v                                                                                            |
| [PHASE 4: CAREER DISCOVERY & EXTERNAL RESEARCH (CDCRE)]  (PLANNED - MVP)                           |
|       |                                                                                            |
|       v                                                                                            |
| [PHASE 5: COMPLETE PLAYER PERFORMANCE ANALYTICS (CPPAE)]  (PLANNED - MVP)                          |
|       |                                                                                            |
|       v                                                                                            |
| [PHASE 6: CONTEXTUAL MATCH INTELLIGENCE (CMIE)]  (PLANNED - MVP ENHANCED)                         |
|       |                                                                                            |
|       v                                                                                            |
| [PHASE 7: PLAYER PROFILE GENERATION (MIE + Service B)]  (PLANNED - MVP)                            |
|       |                                                                                            |
|       v                                                                                            |
| [PHASE 8: SQUAD INTELLIGENCE & COMPOSITION (SICE + Service E)]  (PLANNED - MVP)                   |
|       |                                                                                            |
|       v                                                                                            |
| [PHASE 9: STREAMLIT APPLICATION]  (PLANNED - MVP)                                                  |
|       |                                                                                            |
|       v                                                                                            |
| [PHASE 10: HACKATHON CANDIDATE EVALUATION & FINAL SUBMISSION]  (PLANNED)                           |
+----------------------------------------------------------------------------------------------------+
```

**MVP vs Long-Term split**
- **MVP-essential (hackathon deadline)**: Phases 0–9 produce the working platform: identity
  resolution, membership verification, career discovery, performance analytics, contextual
  intelligence, unified player profiles, squad composition evaluation, and the 11-view Streamlit
  application.
- **Long-term enhancements (post-MVP)**: deep HawkeyeStats delivery-speed/line-length analysis,
  EAP regression models, VORP/WAR valuation, Monte Carlo campaign simulation, Playing XI constraint
  optimizer, Impact Player deployment engine, and the Next.js production frontend. These are
  tracked in `docs/PRD.md §7` and are **not** required for hackathon submission.

### Consolidated Phase Status Matrix

| Phase # | Identifier | Target Scope | Status | Depends On |
|---|---|---|---|---|
| **0** | Documentation & Research Audit | Repo inspection, data audit, licensing, documentation baseline (all 7 docs) | **COMPLETE** | — |
| **1** | Historical Dataset Acquisition & Data Quality | Ingest `datasets/`, SHA-256 manifests, quarantine, quality/coverage baselines | PLANNED | 0 |
| **2** | Unified Database & Player Identity Resolution | 27-entity DDL, PIRE, canonical `player_id`, alias registry | PLANNED | 1 |
| **3** | Team Membership Verification Engine | TMVE six-class taxonomy, RR season segmentation, verification hierarchy | PLANNED | 2 |
| **4** | Career Discovery & External Research | CDCRE, four-state coverage, authorised research + provenance (Service C) | PLANNED | 2, 3 |
| **5** | Complete Player Performance Analytics | CPPAE batting/bowling/fielding/WK/match contribution, format-aware | PLANNED | 2 |
| **6** | Contextual Match Intelligence | CMIE conditions + 5-tier provenance, weather/pitch separation | PLANNED | 5 |
| **7** | Player Profile Generation | MIE orchestration + Service B (JSON/CSV), unified report | PLANNED | 3, 4, 5, 6 |
| **8** | Squad Intelligence & Composition | SICE + Service E (Team Builder), squad report | PLANNED | 5, 7 |
| **9** | Streamlit Application | 11 required views, session-state discipline | PLANNED | 7, 8 |
| **10** | Hackathon Candidate Evaluation & Final Submission | Adversarial review, validation run, packaging | PLANNED | 9 |

---

## 2. Phase 0 — Documentation and Research Audit `[COMPLETE]`

### 2.1 Objectives
Establish a forensically audited technical baseline: inspect the workspace, audit local data,
confirm licensing, and produce the authoritative documentation suite.

### 2.2 Subphases
1. Workspace & data inventory (confirm `datasets/` layout: `ipl_male_json`, `hnd_male_json`,
   `icc_mens_cricket_world_cup_male_json`, `icc_mens_t20_world_cup_male_json`).
2. Licensing audit (CricSheet ODC-By v1.0; Open-Meteo CC BY 4.0; HawkeyeStats; Kaggle).
3. Domain anomaly audit (Super Over, DLS, Impact Player, temporal bounds).
4. Documentation baseline: `README.md`, `PRD.md`, `TRD.md`, `ARCHITECTURE.md`, `PHASES.md`,
   `AGENTS.md`, `AI_INSTRUCTIONS.md`.

### 2.3 Inputs / Outputs
- **Inputs**: repository, `datasets/`, external licensing terms.
- **Outputs**: documentation suite under `docs/` and root `README.md`; audit reports under
  `.agents/teamwork/`.

### 2.4 Dependencies / Checkpoints
- **Depends on**: none (baseline).
- **Checkpoint**: all seven documents + root `README.md` exist, cross-referenced, and
  status-marked.

### 2.5 Acceptance Criteria
- File counts in `datasets/` recorded (IPL 1,243 + 2 non-JSON files, The Hundred 203,
  ODI WC 267, T20 WC 232).
- No SMAT dataset on disk is recorded as a coverage gap (feeds CDCRE four-state coverage).
- License headers verified.

### 2.6 Testing Requirements
- Static inventory script; license-header grep. No runtime tests.

### 2.7 Completion Status
**COMPLETE** — repository at 100% Greenfield Baseline.

---

## 3. Phase 1 — Historical Dataset Acquisition and Data Quality `[PLANNED - MVP]`

### 3.1 Objectives
Build a fault-tolerant ingestion pipeline for `datasets/`, producing immutable raw staging with
SHA-256 digests and a data-quality/coverage baseline.

### 3.2 Subphases
1. Checksum & manifest generation across all four dataset folders.
2. Polymorphic parsers (CricSheet JSON v1.3.0 and legacy YAML v0.94).
3. Quarantine staging for malformed payloads.
4. Data Quality & Coverage Service (Service D) baseline: duplicates, conflicts, missing matches.

### 3.3 Inputs / Outputs
- **Inputs**: `datasets/**`.
- **Outputs**: `src/ingestion/*`, `data/manifests/raw_lake_manifest.json`, populated
  `source_records`, `stg_*` staging tables; DQ report.

### 3.4 Dependencies / Checkpoints
- **Depends on**: Phase 0.
- **Checkpoint**: all match files staged; quarantine count documented; DQ baseline report exists.

### 3.5 Acceptance Criteria
- Per-dataset match counts match Phase 0 inventory (IPL 1,243, HND 203, ODI WC 267, T20 WC 232).
- Zero unhandled parser exceptions; all failures in quarantine log with traces.
- DQ baseline flags: duplicates, conflicting stats, missing data categories.

### 3.6 Testing Requirements
- Unit tests per parser; ingestion completeness SQL counts; quarantine assertion.

---

## 4. Phase 2 — Unified Database and Player Identity Resolution `[PLANNED - MVP]`

### 4.1 Objectives
Deploy the 27-entity 3NF schema; implement PIRE (ENGINE 01) producing canonical `player_id`.

### 4.2 Subphases
1. DDL migration (27 entities, FKs, indexes, `deliveries` season partitioning incl. 2024–2027).
2. ELT: raw → normalised (matches, innings, deliveries, batting_innings, bowling_spells,
   fielding_events, wicketkeeping_events).
3. PIRE 4-tier waterfall (registry key → alias → contextual → fuzzy+biometric).
4. Alias registry + human-review queue.

### 4.3 Inputs / Outputs
- **Inputs**: Phase 1 staging; CricSheet `info.registry.people`.
- **Outputs**: `migrations/V001__*.sql`, `src/pir/identity_resolver.py`, populated
  `players`/`player_aliases`.

### 4.4 Dependencies / Checkpoints
- **Depends on**: Phase 1.
- **Checkpoint**: schema live; PIRE fixture suite passes; zero identity collisions.

### 4.5 Acceptance Criteria
- FK integrity: zero orphan deliveries.
- PIRE resolves 50 known difficult name-pair fixtures with zero auto-merges (AC-02).
- Every player row has an `identity_status`; unresolved → `UNRESOLVED`/`PROVISIONAL`, never guessed.

### 4.6 Testing Requirements
- Adversarial name-collision suite; FK integrity queries; partition-pruning sanity check.

---

## 5. Phase 3 — Team Membership Verification Engine `[PLANNED - MVP]`

### 5.1 Objectives
Implement TMVE (ENGINE 02): six-class membership, RR season segmentation, verification hierarchy,
verified-appearance counting distinct from squad inclusion.

### 5.2 Subphases
1. Build `squad_memberships` + `player_team_history` population for RR (2008–2015, 2018–2026).
2. Suspension representation (`seasons.is_suspension` for 2016/2017); 2027 as future-target.
3. Verified RR match-appearance counts (from `matches`/`deliveries`).
4. Six-class classifier + confidence + evidence assembly (verification_records).

### 5.3 Inputs / Outputs
- **Inputs**: Phase 2 player registry; official squad/match records.
- **Outputs**: `src/membership/tmve.py`, populated membership tables, TMVE output contract.

### 5.4 Dependencies / Checkpoints
- **Depends on**: Phase 2.
- **Checkpoint**: every RR player carries exactly one membership class; UNVERIFIED used for gaps.

### 5.5 Acceptance Criteria
- RR 2016–2017 appears only as suspension (AC-04).
- Squad-inclusion-only players show verified-appearance = 0 (AC-06).
- No player is classified `CURRENT_SQUAD` without verified current-season evidence.

### 5.6 Testing Requirements
- Fixture tests per membership class; suspension assertion; appearance-vs-squad-list differential.

---

## 6. Phase 4 — Career Discovery and External Research `[PLANNED - MVP]`

### 6.1 Objectives
Implement CDCRE (ENGINE 03): cross-competition career discovery, four-state coverage, and
authorised external research with provenance (Service C).

### 6.2 Subphases
1. `player_competition_history` population + coverage-state logic.
2. Career gap detection (respecting the RR suspension window and dataset availability).
3. Authorised external research integration (official records → BCCI → reliable DBs → reputable
   reporting), each claim written to `verification_records`.
4. Coverage/provenance report generation.

### 6.3 Inputs / Outputs
- **Inputs**: Phase 2/3 outputs; external sources.
- **Outputs**: `src/research/cdcpre.py`, populated coverage tables, provenance records.

### 6.4 Dependencies / Checkpoints
- **Depends on**: Phases 2, 3.
- **Checkpoint**: no dataset-absence reported as non-participation (AC-07); all external claims
  provenance-tracked.

### 6.5 Acceptance Criteria
- Four coverage states used correctly (verified / dataset-unavailable / not-established /
  confirmed-non-participation).
- Every external claim carries source URL, provider, timestamp, licence, status, confidence, record ID.

### 6.6 Testing Requirements
- Coverage-state audit on sampled players; provenance completeness check (AC-12).

---

## 7. Phase 5 — Complete Player Performance Analytics `[PLANNED - MVP]`

### 7.1 Objectives
Implement CPPAE (ENGINE 04): comprehensive batting, bowling, fielding, wicketkeeping, and
match-contribution profiles; every statistic documented and format-aware.

### 7.2 Subphases
1. Batting profile (positions, phase splits, matchup splits, partnership contributions).
2. Bowling profile (spell phases, batter matchups, pace/spin, speed/line-length when available).
3. Fielding & wicketkeeping profiles (catches/run-outs/stumpings/dropped, WK appearances).
4. Match contribution (POTM via `player_awards`, participation, contribution to outcomes).
5. `derived_features` persistence (versioned, format-tagged, NULL-safe).

### 7.3 Inputs / Outputs
- **Inputs**: normalised scorecard tables.
- **Outputs**: `src/analytics/*`, populated `derived_features`, CPPAE output contract.

### 7.4 Dependencies / Checkpoints
- **Depends on**: Phase 2 (scorecard ELT).
- **Checkpoint**: zero zero-imputed stats; every metric has a definition + format tag.

### 7.5 Acceptance Criteria
- Missing → `NULL` (AC-09); no cross-format mixing without tags; documented definitions present
  (AC-08).

### 7.6 Testing Requirements
- Statistical unit tests against known scorecards; NULL-safety lint; format-tag assertion.

---

## 8. Phase 6 — Contextual Match Intelligence `[PLANNED - MVP ENHANCED]`

### 8.1 Objectives
Implement CMIE (ENGINE 05): condition annotations with 5-tier provenance; weather explicitly
separated from pitch measurement.

### 8.2 Subphases
1. Weather integration (Open-Meteo historical) → `weather_conditions` with macro-context flag.
2. Pitch conditions → `pitch_conditions` with `provenance_tier`.
3. Match-phase / required-run-rate / target / result annotations.
4. Provenance-tier tagging (measured / reported / estimated / inferred / unknown).

### 8.3 Inputs / Outputs
- **Inputs**: matches, venues, weather API, pitch records.
- **Outputs**: populated `weather_conditions`/`pitch_conditions`, CMIE output contract.

### 8.4 Dependencies / Checkpoints
- **Depends on**: Phases 2, 5.
- **Checkpoint**: 100% IPL night fixtures enriched; weather never labelled as pitch measurement
  (AC-10).

### 8.5 Acceptance Criteria
- Five-tier provenance present per contextual datum; no mental-state inference (guardrail).

### 8.6 Testing Requirements
- Weather-linkage test (zero un-enriched IPL matches); provenance-tier audit.

---

## 9. Phase 7 — Player Profile Generation `[PLANNED - MVP]`

### 9.1 Objectives
Wire MIE orchestration end-to-end and implement Service B (Player Profile Generator): unified
player intelligence reports and JSON/CSV exports.

### 9.2 Subphases
1. MIE request routing + engine sequencing + output merging.
2. Unified report assembly with verification status + provenance.
3. Service B export (JSON/CSV) with licensing attribution.
4. Team Builder Service (Service E) wiring to `user_teams`/`user_team_players`.

### 9.3 Inputs / Outputs
- **Inputs**: Phases 3–6 outputs.
- **Outputs**: `src/mie/`, `src/profile_gen/`, export manifests.

### 9.4 Dependencies / Checkpoints
- **Depends on**: Phases 3, 4, 5, 6.
- **Checkpoint**: end-to-end `request_player_intelligence(name)` returns a complete, provenance-
  traced report.

### 9.5 Acceptance Criteria
- MIE returns UNVERIFIED when membership cannot be established (AC-03); request clarification on
  ambiguity; exports embed attribution (NFR-05).

### 9.6 Testing Requirements
- End-to-end orchestration tests; export-contract tests; engine-import independence (AC-13).

---

## 10. Phase 8 — Squad Intelligence and Composition `[PLANNED - MVP]`

### 10.1 Objectives
Implement SICE (ENGINE 06) + Team Builder Service (Service E): team management and squad
evaluation with role-aware analysis and evidence-backed recommendations.

### 10.2 Subphases
1. Team Builder: create/add/remove players, role assignment, save/load configurations.
2. SICE role distribution, depth, pace/spin balance, WK/all-rounder, duplication, gaps.
3. Role-occupant comparison; replacement identification; combination evaluation.
4. Recommendations assembly (labelled analytical, no unvalidated probabilities — AC-11).

### 10.3 Inputs / Outputs
- **Inputs**: Phase 7 profiles; `user_teams`.
- **Outputs**: `src/squad/*`, SICE output contract, squad report.

### 10.4 Dependencies / Checkpoints
- **Depends on**: Phases 5, 7.
- **Checkpoint**: a saved team produces a complete squad intelligence report.

### 10.5 Acceptance Criteria
- Team CRUD works end-to-end (AC-14); recommendations labelled analytical; no recruitment
  probabilities without a validated model.

### 10.6 Testing Requirements
- SICE fixture tests on 2–3 synthetic squads; team CRUD tests; recommendation-label assertion.

---

## 11. Phase 9 — Streamlit Application `[PLANNED - MVP]`

### 11.1 Objectives
Deliver the 11-view Streamlit application consuming MIE/engine contracts; keep UI separate from
analytics.

### 11.2 Subphases
1. App scaffold + navigation across the 11 required views.
2. Per-view wiring to thin adapters (no analytics in Streamlit).
3. Session-state discipline (ephemeral UI state only).
4. Data Source & Verification Report view (provenance + verification status).

### 11.3 Inputs / Outputs
- **Inputs**: MIE/engine/service contracts.
- **Outputs**: `app/streamlit/` application; UI test suite.

### 11.4 Dependencies / Checkpoints
- **Depends on**: Phases 7, 8.
- **Checkpoint**: all 11 views render; no engine module imports Streamlit (AC-13).

### 11.5 Acceptance Criteria
- 11 views functional; session state used cautiously; UI swap to Next.js possible without engine
  changes.

### 11.6 Testing Requirements
- Playwright/Streamlit e2e per view; architecture import test; manual UX walk-through.

---

## 12. Phase 10 — Hackathon Candidate Evaluation and Final Submission `[PLANNED]`

### 12.1 Objectives
Adversarially evaluate the delivered platform against the PRD acceptance criteria, then package
the final hackathon submission.

### 12.2 Subphases
1. Execute the full AC suite (AC-01…AC-14) across a diverse candidate player set (RR current,
   RR historical, never-RR, uncapped prospect, other-franchise, international, unverified).
2. Data Source & Verification Report sign-off (licensing + provenance completeness).
3. Documentation reconciliation pass across all seven documents.
4. Submission packaging (report, demo script, evidence bundle).

### 12.3 Inputs / Outputs
- **Inputs**: Phase 9 deliverable.
- **Outputs**: `reports/FINAL_VERIFICATION_REPORT.md`, submission dossier.

### 12.4 Dependencies / Checkpoints
- **Depends on**: Phase 9.
- **Checkpoint**: 100% of MVP acceptance criteria pass; submission artefacts complete.

### 12.5 Acceptance Criteria
- All AC-01…AC-14 green; confidentiality of the proprietary hackathon dataset preserved;
  attribution embedded in exports.

### 12.6 Testing Requirements
- Full regression suite; provenance audit; final manual review.

---

## 13. Cross-Phase Risk Assessment & Mitigation

| # | Risk | Severity | Impacted Phase | Mitigation |
|---|---|---|---|---|
| **R1** | Parser crash on malformed records | High | 1 | Quarantine lake: malformed payloads logged with traces; run continues |
| **R2** | Player name collisions (e.g. "R Sharma") | Critical | 2, 4 | PIRE registry-key-first; low-confidence quarantined to human review; never auto-merge |
| **R3** | Missing context (Hawkeye/weather) | Medium | 6 | Nullable enrichment; missing → NULL, never (0.0,0.0); five-tier provenance |
| **R4** | Super Over contamination of career totals | Critical | 1, 5 | `is_super_over` hard exclusion in career views |
| **R5** | DLS truncation distorting run rates | High | 5 | Official revised targets/overs ingested; dynamic phase scaling |
| **R6** | False "never played / uncapped" classification | Critical | 3, 4 | Four-state coverage + UNVERIFIED membership class; absence ≠ non-participation |
| **R7** | RR 2016–2017 suspension mis-analysed | High | 3 | `is_suspension` season flag; 2027 future-target handling |
| **R8** | Unverified external research polluting reports | Critical | 4, 7 | verification_records status; CONFLICT → human review; MIE does not auto-resolve |
| **R9** | UI performing analytics (fragile coupling) | Medium | 9 | Engines are frontend-agnostic; Streamlit runs no analytics (AC-13) |
| **R10** | Dataset confidentiality breach in submissions | High | 10 | Isolated handling; public outputs exclude proprietary hackathon dataset contents |

---

## 14. Conclusion & Verification Summary

- **Phase 0** is **COMPLETE**: workspace baseline verified, `datasets/` inventoried, licensing
  confirmed, and the documentation suite authored.
- **Phases 1–10** are **PLANNED**. MVP-essential work (Phases 1–9) targets the hackathon
  deadline; long-term enhancements are deferred and tracked separately.
- Every phase enforces its acceptance criteria and testing requirements before progression, with
  the Data Quality & Coverage Service gating merges.
