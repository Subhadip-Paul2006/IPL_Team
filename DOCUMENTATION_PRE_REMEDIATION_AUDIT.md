# DOCUMENTATION PRE-REMEDIATION AUDIT

> **HISTORICAL AUDIT NOTICE & SUPERSESSION BANNER (v2.2.0 — 2026-11-11)**:  
> This pre-remediation audit records the forensic baseline inspection of commit `1141ef9` performed on 2026-11-10 during the initial pre-revision phase. It is preserved strictly as an un-retouched historical baseline document without retrospective falsification or modification of its historical observations.  
>  
> **Supersession State**:  
> 1. Superseded in part by **v2.1.1** (commit `eaebdcb`, PR #3: `docs/v2.1.1-targeted-remediation`), which expanded the core PostgreSQL relational schema from 31 to 33 entities (`ranking_configurations`, `ranking_runs`), resolved DDL integrity issues C1–C6, aligned TMVE Option B 3-dimension contracts, and introduced `RANKING_SPEC.md` (`RK-1.0.0`).  
> 2. Superseded comprehensively by **v2.2.0** (`docs/v2.2.0-pvre-dual-mode`), which introduces **Engine 07 — PVRE** (Player Verification & Research Engine) with internal Mother Controller routing (Mode A RR incumbent replacement intelligence, Mode B verified uncapped domestic discovery, and mandatory `REVIEW_REQUIRED` safety gating), formalizes Phase 4B in `docs/PHASES.md` (`AC-24`..`AC-30`), expands the domestic and age-group data source register (S18A–H, S19B, S20B), integrates 5,083 local JSON match files across 13 directories (including 695 SMAT matches in `datasets/sma_json/`), synchronizes 7 specialized engines, 18 system agents (`agent_pvre`), 5 support services (Services A–E), and strictly decouples Top-10 ranking (`RK-1.0.0`) from replacement evaluation (`RE-1.0.0`).

**Project**: RR Squad Intelligence & Team Composition Platform (IPL 2027 RR scouting hackathon)
**Repository**: `Subhadip-Paul2006/IPL_Team`
**Audit date**: 2026-11-10
**Auditor**: Principal Software Architect / PostgreSQL DBA / Technical Documentation Auditor
**Baseline commit inspected**: `1141ef9` (branch `docs/squad-intelligence-revision-v2`, ahead of `origin/main` `7756945`)

---

## 1. Repository Baseline

| Item | Value |
|---|---|
| Branch | `docs/squad-intelligence-revision-v2` (local, tracking `origin/...` at `1141ef9`) |
| Primary branch | `main` (`origin/HEAD`) |
| Working tree | Clean except **untracked `datasets/`** (raw data, not tracked; not covered by `.gitignore`) |
| Staged / unstaged changes | None |
| Tracked file tree | 8 core docs (`README.md`, `PROJECT.md`, `docs/README.md`, `docs/PRD.md`, `docs/TRD.md`, `docs/ARCHITECTURE.md`, `docs/PHASES.md`, `docs/AGENTS.md`, `docs/AI_INSTRUCTIONS.md`), `.gitignore`, `.agents/teamwork/**` (74 historical agent files) |
| Ignored data | `.gitignore` covers only `CricSheet/`; **`datasets/` is NOT ignored** |
| Local datasets (inspected, not tracked) | `datasets/ipl_male_json` (1,243 JSON + LICENSE + README), `datasets/hnd_male_json` (201 JSON), `datasets/icc_mens_cricket_world_cup_male_json` (265 JSON), `datasets/icc_mens_t20_world_cup_male_json` (230 JSON). **No SMAT (sma/) directory. No `CricSheet/` directory.** |
| Licence evidence (local) | All four local archives ship `LICENSE.txt` = **ODC-By**; `README.txt` files give authoritative match counts (1243 / 201 / 265 / 230) and note withheld Afghanistan matches (24 ODI WC, 29 T20 WC withheld) |
| Tooling available for validation | `sqlglot` 30.30 (PostgreSQL dialect parser, installed this session). **No `psql`, no running PostgreSQL, no Docker daemon** (tried; unavailable) → SQL validated by parser only, limitation recorded. **No Mermaid CLI / parser** (offline) → Mermaid validated by rule-based structural lint only, limitation recorded. Python 3.13, Node 22. |

### Historical counts reconciliation (Part 13 requirement)
- v1-era audit reports (`.agents/teamwork/spec_miner_1`, `auditor_1`, `auditor_2`) claim "2,822/2,832 files across 5 subdirectories incl. 695 SMAT". That describes the **old `CricSheet/` archive, which no longer exists locally**.
- **Actual local inventory (this audit)**: 4 directories, **1,939 match JSON files** (1243+201+265+230), all JSON v1.3.0, ODC-By. **SMAT: ABSENT locally** → must be recorded as a coverage gap (`DATASET_UNAVAILABLE`), not carried forward as "695 files".
- The v1.0.0 root `README.md` (pre-revision) and its 2,822-file claims are **superseded**; historical `.agents` records are preserved unchanged and only referenced as evidence.

## 2. Documents Inspected (reading-gate ledger)

| File | Entire file read? | Lines | Conflicts / defects identified |
|---|---|---:|---|
| `README.md` | Yes (v2 revision authored this session; re-read) | 252 | 27-entity claim; six-class membership; "Phase 0 COMPLETE"; PIRE "0.980/0.950 calibrated" framing; 2016–17 suspension model |
| `PROJECT.md` | Yes | 113 | **v1 architecture (Next.js/FastAPI/Redis, 20 entities, F01–F25, CricSheet/)** — no superseded notice; misreads as current spec |
| `docs/README.md` | Yes | 213 | 27-entity count; `agent_cdcpre` id; six-class references |
| `docs/PRD.md` | Yes | 413 | Six-class membership conflation; PIRE tier scores; CDCRE post-identity-only contract; "Phase 0 COMPLETE"; AC references; false-shot frequency promise (v1 inheritance) |
| `docs/TRD.md` | Yes | 1144 | **DDL defects (§3.1 A–D)**; `seasons.is_suspension`; `deliveries` FK gaps; `fielding_events.delivery_id` soft link; PIRE tier-4 "biometric"; `overs_completed NUMERIC(4,1)`; `runs_batter 0..6`; `national_board_noc_granted DEFAULT TRUE`; `is_not_out DEFAULT TRUE`; `availability_status NOT NULL` default-less risk |
| `docs/ARCHITECTURE.md` | Yes | 438 | ERD contains `TEAMS ||--o{ SEASONS` (no such table relationship); 27-entity D7; `is_suspension` ADR-007; PIRE diagram "Biometrics"; TMVE diagram start node; `agent_cdcpre` |
| `docs/PHASES.md` | Yes | 452 | Phase 0 COMPLETE with data-inventory claims; 2016–17 suspension via season flag; 27-entity |
| `docs/AGENTS.md` | Yes | 253 | `agent_cdcpre` identifier; six-class language; "biometric" tier |
| `docs/AI_INSTRUCTIONS.md` | Yes | 291 | "27 entities" tenet; "biometric" terminology (line 140); six-class; R12 membership rule needs 3-dimension split |
| `.gitignore` | Yes | 3 | Ignores `CricSheet/` only; **`datasets/` untracked-and-unignored** |
| `.agents/teamwork/*` (74 files, key ones read in full: ORIGINAL_REQUEST, orchestrator_1 BRIEFING/DISPATCH/PROJECT/GATE_STATUS/handoff, spec_miner_1 & _2, explorer_survey_1, worker_m1–m3, reviewer_1/_3, challenger_1/_2, auditor_1/_2, remediation handoffs) | Yes (all substantive ones; 74-file inventory complete) | ~7,800 | v1-era claims (2,832 files, SMAT present, 76 broken anchors fixed in v1 remediation, TRD/ARCH status tags) — **historical; not to be modified**; supersession recorded in §1 above |

Reading gate: **complete**. No file unread; no modification has been made yet.

## 3. Existing Architecture (as it stands)

- MIE orchestrates 6 engines (PIRE, TMVE, CDCRE, CPPAE, CMIE, SICE) + 5 services; Streamlit initial UI; frontend-agnostic contracts. **Preserved as-is** per mandate.
- PostgreSQL 16, 27 entities, 3NF claim, season-partitioned `deliveries`.
- Six-class membership taxonomy (conflates RR relationship, currency, and eligibility).
- PIRE 4-tier waterfall with confidence constants presented as calibrated.
- `seasons.is_suspension` models the RR 2016–17 absence at competition level.

## 4. Defect Register (priorities: C=critical, H=high, M=medium)

### 4.1 Database defects (`docs/TRD.md` DDL)
| # | Sev | Defect | Fix |
|---|---|---|---|
| DB-1 | C | `derived_features`: table-level `UNIQUE (player_id, feature_name, calculation_window, model_version, COALESCE(format_tag,''))` — **PostgreSQL forbids expressions in table-level UNIQUE constraints** (confirmed by reference; `sqlglot` permissively accepts, so parser alone cannot catch it) | Remove constraint; add **unique expression index** `UNIQUE (player_id, feature_name, calculation_window, model_version, COALESCE(format_tag,''))` (chosen option A: expression indexes are the native Postgres mechanism; no redundant normalised column to keep in sync) |
| DB-2 | C | `deliveries` (partitioned): **no FKs** on `innings_id`, `match_id`, `batter_id`, `bowler_id`, `non_striker_id`, `player_out_id` | Add FKs; documented: **PostgreSQL ≥15 enforces FKs on partitioned tables** (deferrable INITIALLY DEFERRED parent constraints), with partition key `season_year` already in the PK; fallback to soft-integrity checks on older engines documented |
| DB-3 | C | `fielding_events.delivery_id` is a "soft logical link" with no integrity; `season_year` duplicated without constraint tying it to the delivery's partition | Make `delivery_id` optional but when present require `(delivery_id, season_year)` composite FK to `deliveries(delivery_id, season_year)`; add matching `wicketkeeping_events` handling (it correctly references `innings`/`matches` — keep) |
| DB-4 | H | `seasons.is_suspension` models a **franchise-specific** suspension at competition level (IPL continued in 2016–17) | Remove column; add **`team_season_participation`** entity (PARTICIPATING/SUSPENDED/NOT_ENTERED/UNKNOWN, evidence source, verification status, uniqueness per team+season) |
| DB-5 | H | `TEAM → SEASON` appears in the ERD but **no such relationship exists** in the DDL (or anywhere) | Replace with `team_season_participation` relationship; D7/D8 ERD reconciled 1:1 with DDL |
| DB-6 | H | Six-class membership conflates RR relationship, currency, and uncapped eligibility | **Three independent dimensions**: `rr_relationship` (6 states), `rr_current_status` (CURRENT/NOT_CURRENT/UNKNOWN), `ipl_eligibility` (VERIFIED_ELIGIBLE/VERIFIED_NOT_ELIGIBLE/ELIGIBILITY_UNVERIFIED/NOT_ASSESSED) stored in a new **`player_verification`** fact table (player_id, as_of_date, dimensions, evidence, confidence) plus `player_team_history` for season-level facts |
| DB-7 | H | Eligibility policy hardcoded / unversioned; "never assume unknown = uncapped" lacks a schema home | Add **`eligibility_policies`** (versioned, season-specific, effective-date, rule source) + **`player_eligibility`** (player × season × policy_version, status + verified flag) |
| DB-8 | H | `bowling_spells.overs_completed NUMERIC(4,1)` — cricket overs are not decimal quantities (13.4 ≠ 13+4/6) | Store integer balls; display notation derived (`floor(b/6)` + `b%6`); keep `legal_balls_bowled` as the integer of record, drop/repurpose `overs_completed` |
| DB-9 | H | `deliveries.runs_batter CHECK (0..6)` rejects valid **overthrow** runs (5th run off the bat on no-balls/wides or overthrows legally exceeds 6 runs per delivery event) | Remove ceiling on `runs_batter`; keep consistency check `runs_total = runs_batter + runs_extras`; overthrows documented in DATA_DICTIONARY |
| DB-10 | H | Defaults that turn unknown into false facts: `national_board_noc_granted DEFAULT TRUE`, `batting_innings.is_not_out DEFAULT TRUE` (DNB rows fabricated as not-out), `wicketkeeping_events.appearances DEFAULT 1` | Make them **nullable, no default** (NULL = unknown); `player_injuries.injury_date` nullable |
| DB-11 | M | Delivery-level provenance absent (no link to the ingesting `source_record`) | Add `deliveries.source_record_id UUID NULL` (soft FK) + index |
| DB-12 | M | `player_availability.availability_status` NOT NULL with no default — row creation forces a guess | Add explicit allowed values + `NULL` permitted (unknown) |
| DB-13 | M | "Strict 3NF" claimed without support | DDL now demonstrates normalisation (facts in atomic tables, no transitive dependency of non-key attrs on keys via repeat groups); 3NF claim softened to "normalised 3NF core (demonstrated by DDL)" with the one exception of `derived_features` (a feature store, intentionally not 3NF) documented |

### 4.2 Membership / suspension / eligibility model
- MEM-1 (C): as DB-4/DB-6/DB-7 above.
- MEM-2 (H): "Negative membership verification" requirements (coverage scope, season list, squad-list coverage, scorecard coverage, source quality, conflict handling, human review) are **not specified anywhere** → new TRD section + TMVE guardrails in `AI_INSTRUCTIONS.md` R12.
- MEM-3 (H): TMVE output contract (§4.4 TRD) still emits single `membership_class` enum → replace with the three dimensions + evidence.

### 4.3 Statistical / metric gaps (Part 5, 14)
- ST-1 (H): **No metric dictionary exists** → create `docs/DATA_DICTIONARY.md` covering every mandated metric with definition, formula, numerator/denominator, source fields, exclusions, format restrictions, phase rules, null handling, min samples, DQ validation, observed/derived/model-inferred class.
- ST-2 (H): v1-inherited promise of **false-shot frequency** — no source records it → DATA_DICTIONARY marks `FALSE_SHOT_FREQUENCY = NOT_COMPUTABLE_FROM_AVAILABLE_SOURCES` (never computed).
- ST-3 (H): **POTM ≠ total impact** rule + no dropped-catch-zeroing rule + sample-size-visibility rule → DATA_DICTIONARY + CPPAE guardrails + PRD FR-A6.
- ST-4 (M): format-awareness (`format_tag`) present in DDL but not mandated in every metric → dictionary enforces per-metric format tags.

### 4.4 Data-source gaps (Part 6, 13)
- DS-1 (C): No source register; generic descriptions; Kaggle/Hawkeye licence status asserted ("open dataset", "MIT/Permissive") **without evidence** → create `docs/DATA_SOURCE_REGISTER.md` with VERIFIED/PARTIALLY_VERIFIED/UNVERIFIED/UNAVAILABLE/RESTRICTED statuses, join-key & reconciliation plan, and the 2007-claim quarantine.
- DS-2 (H): Historical "2,822 files incl. SMAT" claims contradict local reality (1,939 JSON, no SMAT) → reconcile; SMAT recorded `DATASET_UNAVAILABLE` locally.
- DS-3 (H): Match/delivery reconciliation across providers undocumented (wides/no-balls offsets, Cricsheet `ball` index counting including illegal deliveries, provider numbering conventions, duplicate events) → register §"Reconciliation".

### 4.5 Environmental / condition data (Part 7)
- EN-1 (H): `pitch_conditions` auto-converts qualitative reports to 1.0–10.0 numeric ratings with no validated annotation methodology → keep original text (`source_curator_notes` + new `reported_description`), make numeric ratings explicitly **derived-and-optional** (NULL unless a validated methodology exists; provenance tier required).
- EN-2 (M): Weather rows lack `timezone` and spatial/temporal matching method fields → add `venue_timezone`, `match_local_time`, `spatial_temporal_match_method`.
- EN-3 (H): `national_board_noc_granted DEFAULT TRUE` (DB-10) + unvalidated injury recurrence scores (`recurrence_risk_score` presented as though computed) → recurrence score marked **model-inferred, optional, validation-required**; unverified injuries stay `verified=FALSE`, no medical inference from data.

### 4.6 PIRE revision (Part 8)
- ID-1 (H): "biometric" terminology (TRD §3.3, ARCH D3, PHASES P2, AI_INSTRUCTIONS §4.1) → **contextual attribute corroboration**.
- ID-2 (H): Tier confidence constants (1.000/0.980/0.950) presented as calibrated probabilities → restate as **deterministic tier outcomes**; 0.92/0.95/2 are **tunable matching thresholds, not calibrated probabilities**, gated by a labelled-test-set calibration requirement before any numeric confidence is exposed.
- ID-3 (H): Single "confidence" conflates identity / membership / coverage / eligibility → PIRE returns `identity_status` (tier) + matching evidence only; other measurements belong to TMVE/CDCRE/eligibility services.

### 4.7 MIE circular dependency (Part 9)
- OR-1 (H): CDCRE.discover(player_id) is post-identity only, while PIRE for unknown players needs external evidence → **two CDCRE capabilities**: `discover_candidates(raw_name)` (pre-identity) and `discover_career(player_id)` (post-identity). MIE sequence becomes: raw name → **candidate discovery** → PIRE waterfall (corroborated by discovered candidates) → user clarification on ambiguity → canonical ID → TMVE → CDCRE career → CPPAE/CMIE/SICE. Updates: TRD §2.3/§5/§13, ARCH D2, PRD §4 workflow + ACs.

### 4.8 Data model / entity count (Part 10)
- DM-1 (H): 27 → **31 logical entities** after adding `team_season_participation` (4.1), `player_verification`, `player_eligibility`, `eligibility_policies` (4.2), and removing `seasons.is_suspension` (a column, not an entity). Reconcile counts in README, PROJECT, docs/README, PRD, TRD, ARCHITECTURE (ERD), PHASES, AGENTS, AI_INSTRUCTIONS.
- DM-2 (H): ERD ↔ DDL 1:1 reconciliation (DB-5) with explicit PK/FK/cardinality/nullability/referential-action table.

### 4.9 PROJECT.md & root docs (Part 11)
- RC-1 (H): `PROJECT.md` still presents the v1 Next.js/FastAPI/20-entity architecture as current with no supersession notice → **reconcile as current v2 charter** (feature inventory rebuilt to the engine/service model, hackathon deliverable added) with a dated v1-superseded banner.

### 4.10 .gitignore & data paths (Part 12)
- GI-1 (H): `datasets/` untracked but not ignored → raw archives (and any future `CricSheet/`) could enter Git; proprietary hackathon data could leak. Fix: ignore `datasets/**`, `CricSheet/`, `raw_data/`, `*.zip`, keep `!` exceptions for `LICENSE.txt`/`README.txt`/license docs so attribution files remain trackable; do NOT move/delete datasets.
- GI-2 (M): Docs reference `CricSheet/` in v1 history only; current path `datasets/` must be the canonical one everywhere (v2 docs already do; PROJECT.md must too).

### 4.11 Phase status (Part 13)
- PH-1 (H): Phase 0 marked COMPLETE though it claims "data inventory & licensing verification" that the tracked repo does not support (local SMAT absent; external-source licence statuses not actually verified) → split Phase 0 into 0a documentation baseline (COMPLETE) and 0b empirical data-source & licence audit (**PARTIALLY_COMPLETE** / OPEN, with explicit remaining criteria).

### 4.12 Consistency (Part 17)
- CS-1 (M): `agent_cdcpre` vs required `agent_cdcre` (AGENTS.md + docs/README traceability) → rename, update all refs.
- CS-2 (M): "Phase 0 COMPLETE" in PHASES/README vs PH-1 → align.
- CS-3 (M): "strict 3NF" overclaim (DB-13); "27 entities" everywhere; six-class references; "2008–2015 / suspension / 2018+" language that implies season-level suspension → align with participation entity.
- CS-4 (M): Hackathon final deliverable (**Top 10 youngest eligible uncapped RR candidates for IPL 2027**) not represented in any v2 doc (was v1's "diamond-in-the-rough" with hardcoded weights) → new PRD § + transparent, role-aware, reproducible ranking methodology spec (Part 15).

## 5. Remediation Priorities & Files Expected to Change

1. **P0 (correctness)**: TRD DDL (DB-1..DB-13), membership/eligibility model, CDCRE dual capability, ERD↔DDL.
2. **P1 (completeness)**: new `docs/DATA_SOURCE_REGISTER.md`, `docs/DATA_DICTIONARY.md`; negative-membership & eligibility-policy specs; environmental defaults.
3. **P2 (consistency)**: entity count (31), `agent_cdcre`, PIRE terminology, Phase 0 status, PROJECT.md charter, README/docs-README status & links.
4. **P3 (housekeeping)**: `.gitignore`; hackathon deliverable spec; final audit report `reports/DOCUMENTATION_REMEDIATION_AUDIT.md`.

**Files to change** (one commit each, per Part 19):
`docs/TRD.md`, `docs/PRD.md`, `docs/ARCHITECTURE.md`, `docs/PHASES.md`, `docs/AGENTS.md`, `docs/AI_INSTRUCTIONS.md`, `docs/README.md`, `PROJECT.md`, `README.md`, `.gitignore`, new `docs/DATA_SOURCE_REGISTER.md`, new `docs/DATA_DICTIONARY.md`, new `reports/DOCUMENTATION_REMEDIATION_AUDIT.md`. Plus this pre-audit report (its own commit).

## 6. Validation Methods Available (recorded, honest)

- **SQL**: `sqlglot` (PostgreSQL dialect) parse of the full DDL, plus a bespoke structural checker (FK target existence, PK partition-key inclusion, expression-unique detection, default audit). **No live PostgreSQL execution possible** (no psql/dockerd) — recorded limitation; execution-level checks (deferred triggers) remain a Phase-2 gate.
- **Links**: Python GFM-slug anchor checker across all docs (0 broken target).
- **Mermaid**: **no Mermaid CLI/parser available** → structural lint only (node id uniqueness, edge syntax, closing fences); syntax-validation claim NOT made (recorded limitation).
- **Licence/coverage**: local file inspection (done: ODC-By ×4, authoritative counts, no SMAT); external Kaggle/Hawkeye statuses recorded as RESTRICTED/UNVERIFIED pending Phase 4 research — **no invented percentages**.

**No main-documentation file has been modified yet.** Proceeding to remediation.
