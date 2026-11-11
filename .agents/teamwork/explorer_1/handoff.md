# Baseline Repository Reading Gate and Pre-Modification Audit Report (Requirement R1)

**Agent**: `explorer_1` (Baseline & Historical Auditor)  
**Parent Conversation ID**: `9375951d-5885-4950-843a-c0fc3e12a05a`  
**State Directory**: `d:\New folder (2)\.agents\teamwork\explorer_1`  
**Target Architecture**: `v2.2.0-PVRE-DUAL-MODE`  
**Audit Date**: 2026-11-11T03:40:00Z  

---

## 1. Observation

A forensic, read-only audit of the repository status, commit history, file tree, historical teamwork artifacts, and all 14 authoritative documentation files was executed.

### 1.1 Git Repository Status & Commit History
1. **Origin Remote**:
   - URL: `https://github.com/Subhadip-Paul2006/IPL_Team.git`
   - Active tracking HEAD: `remotes/origin/HEAD -> origin/main`
2. **Authoritative `origin/main` Baseline**:
   - Commit SHA: `eaebdcb29f7912451a1af05b4fa6973379d302bd`
   - Author: Subhadip-Paul2006 <subhadippaulff@gmail.com>
   - Commit Date: Tue Nov 10 02:44:03 2026 +0000
   - Commit Subject: `Merge pull request #3 from Subhadip-Paul2006/docs/v2.1.1-targeted-remediation`
   - Merged PR commits:
     - `7d017f6` — `docs(architecture): v2.1.1 — 33-entity DDL-mirrored ERD, MIE sequence, and TMVE Option B alignment`
     - `7e70949` — `docs(prd): v2.1.1 — header bump + AC-22/23 test-mapping corrections`
     - `94a9980` — `docs(agents): v2.1.1 — align agent contracts to revised architecture`
     - `459ee76` — `docs(prd): v2.1.1 — Use Case 3 ranking aligns to RANKING_SPEC RK-1.0.0; AC-06/AC-18 corrected`
     - `0781298` — `docs(trd): link RANKING_SPEC.md in §13 API table (run_ranking description)`
     - `a2c9226` — `docs(ranking): add RANKING_SPEC.md RK-1.0.0 — versioned reproducible Top-10 method`
     - `9750673` — `docs(register): v2.1.1 — external re-checks (S9 VERIFIED, S8 downgraded), Priority E evidence lines, local tier-4 corroboration`
     - `4cbb778` — `docs(trd): v2.1.1 — add ranking_configurations + ranking_runs (Priority F), entity count 31→33`
     - `439812d` — `docs(trd): v2.1.1 — DDL integrity (C1–C6, A3), TMVE three-dimension contracts (Option B), HUNDRED format, evidence-bound participation rows`
3. **Current Working Branch**:
   - Branch Name: `docs/v2.2.0-pvre-dual-mode`
   - Current Local HEAD Commit: `a69b6d7c9b481055f000223661fb5da5fafdf4e1`
   - Commit Date: Wed Nov 11 00:56:32 2026 +0530
   - Commit Subject: `docs: introduce PVRE dual-mode research architecture v2.2.0`
   - Remote Tracking: Not pushed to origin (`remotes/origin/docs/v2.2.0-pvre-dual-mode` does not exist yet).
4. **Working Tree Status**:
   - Clean across all 14 documentation files (no unstaged or staged modifications in documentation files).
   - Untracked directories: `scripts/`, `datasets/` (local data lake), `.agents/teamwork/explorer_1/`, `explorer_2/`, `explorer_3/`, `orchestrator/`.
   - Modifed in teamwork: `.agents/teamwork/ORIGINAL_REQUEST.md`, `.agents/teamwork/interviewer/prompt_draft.md`, `.agents/teamwork/sentinel/BRIEFING.md`.

---

### 1.2 Repository File Tree Structure & Inventory

The repository contains exactly **14 authoritative documentation files**:
- Root documentation (3 files):
  - `README.md` (301 lines, 22,391 bytes)
  - `PROJECT.md` (159 lines, 13,783 bytes)
  - `DOCUMENTATION_PRE_REMEDIATION_AUDIT.md` (141 lines, 18,744 bytes)
- Architecture & Engineering Documentation in `docs/` (10 files):
  - `docs/README.md` (258 lines, 26,218 bytes)
  - `docs/PRD.md` (577 lines, 48,197 bytes)
  - `docs/TRD.md` (2,025 lines, 132,642 bytes)
  - `docs/ARCHITECTURE.md` (761 lines, 37,684 bytes)
  - `docs/PHASES.md` (511 lines, 37,383 bytes)
  - `docs/AGENTS.md` (403 lines, 27,592 bytes)
  - `docs/AI_INSTRUCTIONS.md` (391 lines, 24,849 bytes)
  - `docs/DATA_SOURCE_REGISTER.md` (176 lines, 25,739 bytes)
  - `docs/DATA_DICTIONARY.md` (306 lines, 32,662 bytes)
  - `docs/RANKING_SPEC.md` (213 lines, 13,688 bytes)
- Audit & Governance Reports in `reports/` (1 file):
  - `reports/DOCUMENTATION_REMEDIATION_AUDIT.md` (418 lines, 33,628 bytes)

In addition, the repository tracks:
- `.gitignore` (covers `CricSheet/`, node modules, Python bytecode).
- Dataset license files:
  - `datasets/ipl_male_json/LICENSE.txt`, `README.txt`
  - `datasets/hnd_male_json/LICENSE.txt`, `README.txt`
  - `datasets/icc_mens_cricket_world_cup_male_json/LICENSE.txt`, `README.txt`
  - `datasets/icc_mens_t20_world_cup_male_json/LICENSE.txt`, `README.txt`
- Historical `.agents/teamwork/` metadata directories (74 files from earlier agent runs).

Untracked local data directories in `datasets/` (6,076 total JSON matches across 13 directories):
- `ipl_male_json` (1,243 files, ODC-By)
- `hnd_male_json` (201 files, ODC-By)
- `icc_mens_cricket_world_cup_male_json` (265 files, ODC-By)
- `icc_mens_t20_world_cup_male_json` (230 files, ODC-By)
- `bbl_male_json` (662 files, ODC-By)
- `cpl_male_json` (445 files, ODC-By)
- `psl_male_json` (357 files, ODC-By)
- `sat_male_json` (130 files, ODC-By)
- `sma_json` (695 files, ODC-By — Syed Mushtaq Ali Trophy verified locally present!)
- `bpl_male_json` (469 files, ODC-By)
- `ilt_male_json` (134 files, ODC-By)
- `lpl_male_json` (143 files, ODC-By)
- `mlc_male_json` (109 files, ODC-By)
- `names.csv`, `people.csv`, `venues.csv`, `venue_names.csv`

---

### 1.3 Baseline Architecture Metrics (on `origin/main` commit `eaebdcb`)

| Metric | Measured Baseline on `origin/main` (`eaebdcb`) | Authoritative Target for `v2.2.0` |
|---|---|---|
| **Product Version** | `v2.1.1` (PR #3 remediation; some headers still showed `v2.1.0` or `1.0.0`) | `v2.2.0` across all 14 files |
| **Specialised Engines** | **6 Engines** (PIRE, TMVE, CDCRE, CPPAE, CMIE, SICE) | **7 Engines** (PIRE, TMVE, CDCRE, CPPAE, CMIE, SICE, **PVRE**) |
| **Support Services** | **5 Services** (Service A: Ingestion, B: Profile Gen, C: Provenance, D: DQ, E: Team Builder) | **5 Services** (strictly distinguished from analytical engines) |
| **System Agents** | **17 Agents** (Agent 01–16, plus Agent 04b Eligibility Policy) | **18 Agents** (adding `agent_pvre` as Engine 07 agent) |
| **Database Entities** | **33 Entities** (3NF PostgreSQL 16 schema, DDL mirrored in ERD) | **33 Entities** (no DDL expansion needed; verified 3NF baseline) |
| **Acceptance Criteria** | **AC-01 through AC-23** (in PRD; PHASES had 22; TRD referenced AC-24/25 informally) | **AC-01 through AC-30** (AC-24..AC-30 explicitly mapped) |
| **Roadmap Phases** | **11 Phases** (Phase 0a/0b through Phase 10) | **12 Phases** (adding **Phase 4B** `[STATUS: PLANNED - MVP]`) |
| **MIE Sequence** | Ingestion → PIRE → TMVE+Eligibility → CDCRE → CPPAE → CMIE → Profile Gen → SICE → Streamlit | Ingestion → PIRE → TMVE+Eligibility → CDCRE → **PVRE** → CPPAE → CMIE → Profile Gen → SICE → Streamlit |
| **TMVE Membership Model** | Three dimensions (Relationship, Currency, Season Eligibility) + negative verification protocol | Preserved intact (TRD §4, §4.5, §4.6) |
| **Data Provenance** | 5 Tiers + `verification_records` + `provenance_chains` + `chk_tsp_verified_evidence` | Preserved and expanded to domestic/age-group & global sources |
| **Top-10 Ranking** | Versioned Top-10 uncapped hackathon method (`RANKING_SPEC.md` `RK-1.0.0`) | Decoupled from SICE Mode A replacement comparison (`RE-1.0.0`) |

---

### 1.4 Comprehensive File-by-File Audit & Defect Findings

A line-by-line inspection of commit `a69b6d7` and the 14 documentation files revealed that while `a69b6d7` made extensive progress (+1,614 insertions across 13 files), **several concrete defects, omissions, and governance violations exist**:

#### Defect 1: `DOCUMENTATION_PRE_REMEDIATION_AUDIT.md` Was Omitted Completely
- **Location**: `DOCUMENTATION_PRE_REMEDIATION_AUDIT.md` (lines 1–15).
- **Finding**: Commit `a69b6d7` touched 13 files and completely omitted `DOCUMENTATION_PRE_REMEDIATION_AUDIT.md`. The document still reads as an unhedged audit of commit `1141ef9` without any note that it has been superseded by v2.1.1 and v2.2.0.
- **Requirement Violation**: R4 item 13 explicitly mandates: *"Preserve historical audit baseline intact, adding dated supersession notes only where required without retrospective alteration."*
- **Required Edit**: Add a dated supersession banner at line 8 documenting that this pre-remediation audit reflects the historical `1141ef9` baseline and is superseded by v2.1.1 (`eaebdcb`) and v2.2.0 (`docs/v2.2.0-pvre-dual-mode`).

#### Defect 2: Missing Dedicated Age-Group Sources in `docs/DATA_SOURCE_REGISTER.md`
- **Location**: `docs/DATA_SOURCE_REGISTER.md` (§3 and §4, lines 58–120).
- **Finding**: `docs/DATA_SOURCE_REGISTER.md` added sources S13–S20 for global leagues (BBL, PSL, CPL, SA20, BPL, ILT20, LPL, MLC) and mentions Ranji, SMAT, and Vijay Hazare, but **completely omits dedicated source register entries** for:
  - Cooch Behar Trophy (U-19 4-day)
  - C.K. Nayudu Trophy (U-23/U-25 multi-day)
  - Vijay Merchant Trophy (U-16 multi-day)
  - U-19 ICC / Domestic Tournaments
- **Requirement Violation**: R3 item 1 & 2 explicitly mandates: *"Identify actual sources for Ranji Trophy, Syed Mushtaq Ali Trophy (SMAT), Vijay Hazare Trophy, Duleep Trophy, Cooch Behar Trophy, Vinoo Mankad Trophy, C.K. Nayudu Trophy, Vijay Merchant Trophy, and U-19 competitions. Add separate source entries where required, recording scorecard availability separately from ball-by-ball availability."*
- **Required Edit**: Add explicit source entries S21–S25 in `docs/DATA_SOURCE_REGISTER.md` for these competitions, clearly distinguishing scorecard access (BCCI portal / scrapers) from ball-by-ball delivery ledgers, and stating access constraints.

#### Defect 3: PVRE Response Contract Field Discrepancies in `docs/TRD.md` §9.6.2
- **Location**: `docs/TRD.md` lines 889–934 (§9.6.2).
- **Finding**:
  1. §9.6.2 defines `eligibility_status: str`, conflating senior international cap status with season-bound IPL uncapped eligibility.
  2. It omits the required explicit field `career_coverage_state: str`.
  3. Total fields listed is 24, but R2 items 4 & 7 require 26 distinct typed fields:
     - `player_capped_status: str` (e.g. `CAPPED_SENIOR_INTERNATIONAL`, `UNVERIFIED_CAPPED_STATUS`, `VERIFIED_UNCAPPED`)
     - `ipl_uncapped_eligibility: str` (e.g. `ELIGIBLE_UNCAPPED_2027`, `INELIGIBLE_OVER_CAP`, `UNVERIFIED_ELIGIBILITY`)
     - `career_coverage_state: str` (`COMPLETE_WITHIN_VERIFIED_SOURCES`, `PARTIAL_COVERAGE`, `UNKNOWN`, `REVIEW_REQUIRED`)
- **Requirement Violation**: R2 item 4 ("Maintain distinct fields for player_capped_status and ipl_uncapped_eligibility") and R2 item 7 (26 mandatory contract fields).
- **Required Edit**: Update `PVREOutputContract` in `docs/TRD.md` §9.6.2 to explicitly declare `player_capped_status`, `ipl_uncapped_eligibility`, and `career_coverage_state`.

#### Defect 4: Undeclared Phase 4B Dependencies in Phase 7 (MIE) and Phase 8 (SICE) in `docs/PHASES.md`
- **Location**: `docs/PHASES.md` lines 411–414 (Phase 7) and lines 431–434 (Phase 8).
- **Finding**:
  - Phase 7 (MIE) lines 411–413 state: `Inputs: Phases 3–6 outputs` and `Depends on: Phases 3, 4, 5, 6.` It does NOT list Phase 4B!
  - Phase 8 (SICE) lines 431–433 state: `Inputs: Phase 7 profiles; user_teams` and `Depends on: Phases 5, 7.` It does NOT list Phase 4B!
- **Requirement Violation**: R5 item 1 explicitly states: *"Update Phase 7 (MIE) and Phase 8 (SICE) to explicitly declare dependencies on PVRE."*
- **Required Edit**: In `docs/PHASES.md`, update Phase 7 inputs/dependencies to include Phase 4B (PVRE), and update Phase 8 inputs/dependencies to explicitly include Phase 4B (PVRE replaceability assessments).

#### Defect 5: Compressed Test Cases in `docs/PHASES.md` Phase 4B
- **Location**: `docs/PHASES.md` lines 337–350.
- **Finding**: Phase 4B condensed test scenarios into 4 general bullet points rather than articulating the 10 explicit scenarios required by R5 item 3 (Verified RR incumbent, Historical RR player, Verified uncapped candidate, Verified capped non-RR player, Unknown player absent from DB, Duplicate identities, Conflicting DOB/membership, Missing domestic datasets, Conflicting external sources, Incomplete career coverage).
- **Requirement Violation**: R5 item 3.
- **Required Edit**: Expand Phase 4B test cases in `docs/PHASES.md` to enumerate all 10 explicit test scenarios with pass/fail criteria.

#### Defect 6: Legacy "31-entity" Text in `docs/README.md`
- **Location**: `docs/README.md` line 22.
- **Finding**: Line 22 contains `architecture: **31-entity PostgreSQL core**` in a historical note without clarifying that the authoritative schema expanded to 33 entities in v2.1.1 (Priority F) and remains 33 entities in v2.2.0.
- **Required Edit**: Clarify the historical note in `docs/README.md` line 22 to confirm that 31 entities was the v2.1.0 count, superseded by 33 entities in v2.1.1 and v2.2.0.

#### Defect 7: Reports Remediation Audit Lacks Full 14-File Scope
- **Location**: `reports/DOCUMENTATION_REMEDIATION_AUDIT.md` Section 20.
- **Finding**: Section 20 records changes across "13 files", reflecting the fact that `DOCUMENTATION_PRE_REMEDIATION_AUDIT.md` was omitted.
- **Required Edit**: Update Section 20.1 and 20.4 to document all 14 files, noting the supersession banner added to `DOCUMENTATION_PRE_REMEDIATION_AUDIT.md`.

---

## 2. Logic Chain

1. **Verification of Remote Baseline**:
   - Tool `run_command` fetched `origin/main` and executed `git rev-parse origin/main`, yielding `eaebdcb29f7912451a1af05b4fa6973379d302bd`.
   - Inspection of commit `eaebdcb` verified that PR #3 merged 9 commits establishing the v2.1.1 baseline (33 entities, 17 agents, 6 engines, AC-01..AC-23, `RANKING_SPEC.md` RK-1.0.0).
2. **Verification of Local Branch & Prior Commit**:
   - `git status` and `git log` revealed that branch `docs/v2.2.0-pvre-dual-mode` has a single commit `a69b6d7c9b481055f000223661fb5da5fafdf4e1` on top of `eaebdcb`.
   - `git show --stat a69b6d7` demonstrated that 13 files were modified. `DOCUMENTATION_PRE_REMEDIATION_AUDIT.md` was completely absent from that commit.
3. **Assessment of Audit Evidence in `.agents/teamwork/`**:
   - Examination of historical handoffs (`auditor_victory_1/handoff.md`, `worker_remediation_1/handoff.md`, `sentinel/handoff.md`) confirmed that `.agents/teamwork/` holds historical audit logs from v1.0.0 (20 entities) and v2.1.0/v2.1.1 remediation. These artifacts are historical context only and do not govern v2.2.0 architecture.
4. **Analysis of Compliance against Requirements R1–R6**:
   - The 14 files were scanned programmatically and manually against the specifications in `ORIGINAL_REQUEST.md`.
   - The analysis verified that the architecture correctly introduces Engine 07 (PVRE) and preserves the 33-entity PostgreSQL core without requiring additional tables.
   - However, 7 distinct defects/omissions were identified (missing age-group sources in `DATA_SOURCE_REGISTER.md`, contract field conflation in `TRD.md`, omitted Phase 4B dependencies in `PHASES.md`, omitted supersession note in `DOCUMENTATION_PRE_REMEDIATION_AUDIT.md`, and 13-vs-14 file reporting count).
5. **Formulation of Actionable Change Register**:
   - Each of the 14 files was mapped to its exact required edits, target sections, line ranges, and governance criteria to enable downstream workers and reviewers to execute surgical fixes.

---

## 3. Caveats

1. **Tooling Environment**:
   - PostgreSQL 16 daemon and `psql` are not running locally. SQL DDL was validated via `sqlglot` (PostgreSQL dialect parser) and manual static analysis; live database execution was not performed.
   - Mermaid CLI (`mmdc`) is unavailable in the environment. All 14 Mermaid diagrams were structurally validated using header syntax and link parsers.
2. **Local Data Lake Untracked Status**:
   - The `datasets/` directory contains 6,076 valid JSON match files (including 695 SMAT files in `datasets/sma_json/`). These files are read-only local artifacts and must never be committed to Git.
3. **Pre-Existing Commit `a69b6d7`**:
   - Commit `a69b6d7` exists locally on `docs/v2.2.0-pvre-dual-mode` but has NOT been pushed to origin. Because R6 requires *exactly one commit* on branch `docs/v2.2.0-pvre-dual-mode`, all remaining remediation edits must either be amended into this commit (`git commit --amend`) or squashed/rebased before push.

---

## 4. Conclusion & Pre-Modification Defect/Change Register

### 4.1 Executive Summary
- Baseline `origin/main` commit SHA is **`eaebdcb29f7912451a1af05b4fa6973379d302bd`** (v2.1.1, 6 engines, 33 entities, 17 agents, AC-01..AC-23).
- Branch `docs/v2.2.0-pvre-dual-mode` HEAD is **`a69b6d7c9b481055f000223661fb5da5fafdf4e1`** (v2.2.0, 7 engines, 18 agents, Phase 4B PLANNED, AC-01..AC-30).
- The suite requires surgical remediation across **all 14 authoritative documentation files** to resolve 7 concrete defects and achieve 100% compliance with Requirements R1–R6.

---

### 4.2 Comprehensive 14-File Pre-Modification Defect & Change Register

| # | File Path | Current Status | Defect / Gap in Current State | Required Surgical Edit for v2.2.0 | Exact Sections & Line Ranges |
|---|---|---|---|---|---|
| **1** | `README.md` | v2.2.0 aligned | Minor: ensure engine table, agent counts, and support services are cleanly demarcated | Retain 7 specialised engines, 18 system agents, 5 support services, 33 entities; ensure Greenfield Baseline notice is intact | Header (lines 1–15), Architecture (lines 80–120), Engine Table (lines 100–160), Roadmap (lines 255–275) |
| **2** | `PROJECT.md` | v2.2.0 aligned | Minor: ensure Phase 4B position and engine inventory are strictly synchronized | Engine 07 PVRE in C6b table row; Phase 4B in milestone roadmap; preserve Appendix A historical v1 specs | Header (lines 1–25), Engine table (lines 50–65), Roadmap (lines 70–85) |
| **3** | `DOCUMENTATION_PRE_REMEDIATION_AUDIT.md` | **Unmodified (DEFECT 1)** | Missing dated v2.2.0 supersession note; reads as active spec | Add dated supersession note at top stating this document records historical inspection of commit `1141ef9` and is superseded by v2.1.1 (`eaebdcb`) and v2.2.0 | Header & Section 1 (lines 1–20) |
| **4** | `reports/DOCUMENTATION_REMEDIATION_AUDIT.md` | v2.2.0 addendum present | Section 20 cites 13 files instead of 14; needs full 14-file coverage (DEFECT 7) | Update Addendum §20 to document all 14 files; record baseline SHA `eaebdcb`, branch `docs/v2.2.0-pvre-dual-mode`, local dataset audit, and final approved verdict | Header (lines 1–10), Section 20 (lines 350–418) |
| **5** | `docs/README.md` | v2.2.0 aligned | Line 22 references "31-entity PostgreSQL core" in historical note without 33-entity clarification (DEFECT 6) | Update line 22 note; ensure 7 engines, 18 agents, 5 services, 33 entities are verified in reading hub and traceability matrix | Header (lines 1–25), §1 Overview (lines 30–60), Matrix (lines 120–180), §6 Changelog (lines 230–258) |
| **6** | `docs/PRD.md` | v2.2.0 aligned | Ensure Use Case 5 and AC-24..AC-30 are completely mapped in §10 traceability matrix | Verify Use Case 5 (PVRE Mode A/B), FR-P1..FR-P7, AC-24..AC-30; maintain strict separation between Top-10 hackathon ranking and replacement evaluation | Use Cases (lines 150–220), FR table (lines 330–370), AC table (lines 520–575), Matrix §10 |
| **7** | `docs/TRD.md` | v2.2.0 with contract gap | §9.6.2 response contract conflates capped status and eligibility into `eligibility_status`, and omits `career_coverage_state` (DEFECT 3) | Update §9.6.2 to include all 26 explicit fields (`player_capped_status`, `ipl_uncapped_eligibility`, `career_coverage_state`); preserve 33 entities; update MIE sequence §10; add PVRE API endpoints in §13 | §2.1 DDL (lines 80–120), §9 PVRE (lines 650–940), §10 MIE (lines 950–1000), §13 API (lines 1550–1600) |
| **8** | `docs/ARCHITECTURE.md` | v2.2.0 aligned | Verify Mermaid syntax across all diagrams; ensure PVRE internal vs MIE boundaries are clear | Verify 14 Mermaid diagrams; confirm ADR-008 for PVRE boundaries; verify 33-entity ERD (§3.1); clarify Mother Controller internal scope | §1 Executive (lines 1–40), §2 Architecture (lines 50–180), §3 Data Model (lines 250–350), §8 ADR-008 (lines 680–740) |
| **9** | `docs/PHASES.md` | v2.2.0 with dependency gap | Phase 7 (MIE) and Phase 8 (SICE) omit explicit Phase 4B dependencies (DEFECT 4); test cases compressed (DEFECT 5) | In Phase 7 and Phase 8, add explicit Phase 4B dependencies; expand Phase 4B test cases to enumerate all 10 explicit test scenarios; maintain PLANNED status | Roadmap graph (lines 35–80), Phase 4B (lines 270–360), Phase 7 (lines 405–420), Phase 8 (lines 425–440) |
| **10** | `docs/AGENTS.md` | v2.2.0 aligned | Ensure 18 system agents are numbered and contracts forbid PVRE squad retention decisions | Confirm `agent_pvre` contract; verify Agent 02 (`agent_mie`) and Agent 08 (`agent_sice`) integration; prohibit autonomous squad decision-making in PVRE | System Table (lines 20–45), Agent 02 (lines 70–90), Agent 08b `agent_pvre` (lines 190–235), Agent 08 SICE |
| **11** | `docs/AI_INSTRUCTIONS.md` | v2.2.0 aligned | Ensure all 6 mandatory domain guardrails for PVRE are explicitly codified | Verify rules against false uncapped inference, negative RR membership assumptions, identity merging, unverified web scraping, conflict overwriting, and arbitrary probabilities | Header (lines 1–20), Principles (lines 40–120), PVRE Guardrails (lines 330–390) |
| **12** | `docs/DATA_DICTIONARY.md` | v2.2.0 aligned | Verify recent-form metrics, 16 comparison dimensions (D01–D16), and replaceability signals | Confirm Section 9 (recent form), Section 10 (replaceability states), Section 11 (16 dimensions); ensure missing data rules and sample size attributes are defined | Header (lines 1–15), §9 (lines 255–280), §10 (lines 281–290), §11 (lines 291–306) |
| **13** | `docs/DATA_SOURCE_REGISTER.md` | Missing age-group sources (DEFECT 2) | Omits Cooch Behar, C.K. Nayudu, Vijay Merchant, U-19 sources; needs scorecard vs ball-by-ball distinction | Add dedicated source entries S21–S25 for Cooch Behar, Vinoo Mankad, C.K. Nayudu, Vijay Merchant, and U-19; separate scorecard from ball-by-ball; define access limits and fallback behaviour | Header (lines 1–20), §3 Lake Inventory (lines 40–80), §4 External Registry S13–S25 (lines 81–150), §5 Access rules |
| **14** | `docs/RANKING_SPEC.md` | v2.2.0 aligned | Maintain strict decoupling between Top-10 hackathon ranking (`RK-1.0.0`) and incumbent replacement evaluation (`RE-1.0.0`) | Reaffirm that SICE replacement comparison is independent of the Top-10 uncapped board; no formula alterations to `RK-1.0.0`; ensure reproducible storage in `ranking_runs` | Header (lines 1–20), §1 Scope (lines 21–60), §8 Decoupling (lines 160–213) |

---

## 5. Verification Method

To independently verify this baseline audit report, execute the following commands in PowerShell from the repository root:

1. **Verify Git Baseline Commit**:
   ```powershell
   git fetch origin main
   git rev-parse origin/main
   # Assert SHA equals eaebdcb29f7912451a1af05b4fa6973379d302bd
   ```

2. **Verify Working Branch & HEAD**:
   ```powershell
   git rev-parse HEAD
   # Assert SHA equals a69b6d7c9b481055f000223661fb5da5fafdf4e1
   git diff --stat origin/main..HEAD
   # Assert 13 files modified (+1614, -265) and DOCUMENTATION_PRE_REMEDIATION_AUDIT.md missing
   ```

3. **Verify File Existence & Sizes Across All 14 Files**:
   ```powershell
   python scripts/validate_suite.py
   ```

4. **Verify Markdown Anchors & Links**:
   ```powershell
   python scripts/test_all_links.py
   python scripts/check_real_anchors.py
   ```

5. **Verify Defect Findings**:
   - Check `DOCUMENTATION_PRE_REMEDIATION_AUDIT.md` for lack of v2.2.0 note:
     ```powershell
     Select-String -Path DOCUMENTATION_PRE_REMEDIATION_AUDIT.md -Pattern "v2.2.0"
     # Returns 0 matches (confirms Defect 1)
     ```
   - Check `docs/DATA_SOURCE_REGISTER.md` for missing Cooch Behar / C.K. Nayudu / Vijay Merchant:
     ```powershell
     Select-String -Path docs/DATA_SOURCE_REGISTER.md -Pattern "Cooch Behar", "C.K. Nayudu", "Vijay Merchant"
     # Returns 0 matches (confirms Defect 2)
     ```
   - Check `docs/TRD.md` §9.6.2 for `player_capped_status`:
     ```powershell
     Select-String -Path docs/TRD.md -Pattern "player_capped_status"
     # Returns 0 matches (confirms Defect 3)
     ```
   - Check `docs/PHASES.md` Phase 7 & 8 dependencies:
     ```powershell
     Select-String -Path docs/PHASES.md -Pattern "Depends on:.*Phase 4B"
     # Returns 0 matches (confirms Defect 4)
     ```

---
*Report compiled and verified by `explorer_1` (Baseline & Historical Auditor).*
