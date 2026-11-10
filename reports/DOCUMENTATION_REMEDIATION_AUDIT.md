# Documentation Remediation Audit — Final Report

**Project**: RR Squad Intelligence & Team Composition Platform
**Repository**: `Subhadip-Paul2006/IPL_Team`
**Date**: 2026-11-10
**Baseline commit inspected**: `1141ef9` (`docs/squad-intelligence-revision-v2`, ahead of `origin/main` `7756945`)
**Companion document**: `DOCUMENTATION_PRE_REMEDIATION_AUDIT.md` (defect register, unmodified by remediation)

---

## 1. Executive Summary

This cycle remediated **all previously identified defects plus 22 additional independently
discovered defects** across the documentation suite:

- **DDL (DB-1…DB-13)**: the invalid `derived_features` expression-UNIQUE constraint was
  replaced with a unique **expression index**; **foreign keys were added to the
  partitioned `deliveries` table** (supported on PostgreSQL ≥ 15, target 16); the
  `fielding_events` delivery link became a real composite FK (`delivery_id, season_year`);
  **false-claim defaults removed** (`national_board_noc_granted DEFAULT TRUE`,
  `is_not_out DEFAULT TRUE`, provenance-tier defaults); cricket overs are now stored as
  integer legal balls with derived over notation; `runs_batter BETWEEN 0 AND 6` was
  removed to admit overthrows; delivery-level provenance (`source_record_id`) added.
- **Membership model (MEM)**: the competition-level `seasons.is_suspension` flag was
  replaced by the franchise-level **`team_season_participation`** entity; the conflated
  six-class taxonomy was split into **three independent dimensions** (RR relationship ·
  current status · season-bound, policy-versioned eligibility) backed by
  `player_membership_state`, `eligibility_policies`, and `player_eligibility`.
- **Circular dependency (OR-1)**: CDCRE now has **two capabilities** — pre-identity
  `discover_candidates(raw_name)` and post-identity `discover_career(player_id)` — and the
  MIE sequence starts with candidate discovery. PIRE terminology corrected to
  **contextual attribute corroboration**; numeric confidence is exposed only when
  calibrated.
- **Completeness**: new `docs/DATA_SOURCE_REGISTER.md` (source-to-field mapping, five
  verification statuses, reconciliation plan, local verification log 2026-11-10) and new
  `docs/DATA_DICTIONARY.md` (every CPPAE metric with formula, numerator/denominator,
  null rules, sample minimums, observed/derived/model classes; explicit NOT_COMPUTABLE
  list including false shots).
- **Governance**: Phase 0 split into **0a (COMPLETE)** and **0b (OPEN /
  PARTIALLY_COMPLETE)**; `PROJECT.md` reconciled into the current charter with a
  prominent supersession notice; `.gitignore` corrected to the real data layout;
  `agent_cdcre` identifier normalised; entity count reconciled to **31** everywhere;
  the hackathon **Top-10 youngest eligible uncapped** deliverable specified
  (PRD §4.3) with a transparent, reproducible ranking methodology.

**Verification status**: internal-link validation **0 broken** (final 2 pointing to this
report resolve at commit); sqlglot PostgreSQL-dialect parse of the full DDL **0 errors,
31 tables, all FK targets defined**; ERD↔DDL cross-check **0 unresolved relationships**;
Mermaid blocks **structurally linted only** (no parser available — limitation recorded);
`.gitignore` behaviour **verified empirically** (payloads ignored, licence/notice files
trackable). **No live PostgreSQL execution was possible** (no psql/dockerd) — execution
of the migration is a Phase 2 gate.

---

## 2. Repository Baseline & Inspected Commit

| Item | Value |
|---|---|
| Branch | `docs/squad-intelligence-revision-v2` (local; `origin/main` at `7756945`) |
| HEAD at inspection | `1141ef9` "docs: revise suite to RR Squad Intelligence & Team Composition Platform" |
| Working tree at inspection | clean except untracked `datasets/` (raw data; not ignored by the pre-fix `.gitignore`) |
| Tracked tree | 8 core docs + `PROJECT.md` + `.gitignore` + 74 `.agents/teamwork/**` historical files |
| Local datasets (untracked) | `datasets/ipl_male_json` (1,243 JSON), `hnd_male_json` (201), `icc_mens_cricket_world_cup_male_json` (265), `icc_mens_t20_world_cup_male_json` (230); each with ODC-By `LICENSE.txt` + CricSheet `README.txt`; **no SMAT directory; no `CricSheet/` directory** |
| Tooling | Python 3.13, Node 22, `sqlglot` 30.30 (installed this session); **no psql, no running PostgreSQL, no Docker daemon, no Mermaid CLI** |

---

## 3. Reading-Gate Ledger (Step 1.3 — completed before any modification)

| File | Entire file read? | Lines | Conflicts identified |
|---|---|---:|---|
| `README.md` | Yes | 252 | 27-entity, six-class, Phase-0-COMPLETE claims (now stale) |
| `PROJECT.md` | Yes | 113 | Entire v1 architecture presented as current (Part 11 defect) |
| `docs/README.md` | Yes | 213 | `agent_cdcpre`, 27-entity, AC-01…14 scope |
| `docs/PRD.md` | Yes | 413 | Conflated six-class; post-identity-only CDCRE; PIRE calibrated scores; no Top-10 spec |
| `docs/TRD.md` | Yes | 1,144 | DB-1…DB-13 (DDL), `seasons.is_suspension`, PIRE "biometric" |
| `docs/ARCHITECTURE.md` | Yes | 438 | Invalid `TEAMS→SEASONS` ERD edge; 27-entity; "Biometrics" diagram |
| `docs/PHASES.md` | Yes | 452 | Phase 0 COMPLETE overclaim |
| `docs/AGENTS.md` | Yes | 253 | `agent_cdcpre` id; six-class language |
| `docs/AI_INSTRUCTIONS.md` | Yes | 291 | "27 entities" tenet; "biometric" line 140; six-class; `DEFAULT TRUE` NOC oversight |
| `.gitignore` | Yes | 3 | Ignores `CricSheet/` only; `datasets/` unprotected |
| `.agents/teamwork/*` (74 files; all substantive ones read in full: ORIGINAL_REQUEST, orchestrator_1 ×6, spec_miner_1/_2, explorer_survey_1, worker_m1–m3/_remediation, reviewer_1/_2/_3, challenger_1/_2, auditor_1/_2/_victory_1, sentinel, dispatches, briefings, progress) | Yes | ≈7,800 | v1-era claims (2,832 files, SMAT present, "2,822 incl. 695 SMAT", 76-broken-anchor history, "FastAPI is implemented" fix) — preserved unmodified; supersession documented in `DATA_SOURCE_REGISTER.md §1.1` and the pre-audit §1 |

Reading gate: **complete** — no document modified before the ledger and
`DOCUMENTATION_PRE_REMEDIATION_AUDIT.md` were finished.

---

## 4. Previously Identified Defects (from the task brief) & Resolution

| Defect | File(s) | Resolution |
|---|---|---|
| Invalid `COALESCE` expression in `derived_features` table-level UNIQUE | TRD | Replaced with **unique expression index** `uq_derived_features (player_id, feature_name, calculation_window, model_version, COALESCE(format_tag,''))`; decision D1 recorded with rationale (no redundant normalised column to drift) |
| Missing FKs on partitioned `deliveries` (`innings_id`, `match_id`, `batter_id`, `bowler_id`, `non_striker_id`, `player_out_id`) | TRD | Column-level FKs added; composite PK already includes partition key `season_year`; **PG ≥ 15 enforced-FK requirement on partitioned referencing tables documented** (target 16; pre-15 fallback = Service D reconciliation checks, D2) |
| `fielding_events.delivery_id` soft link | TRD | Optional but integrity-preserving: composite FK `(delivery_id, season_year)` → `deliveries`, pairing CHECK (both-or-none), partial unique index for event deduplication (D3) |
| RR 2016–17 suspension modelled at competition level | TRD/ARCH/PHASES/README/AGENTS/AI | **Removed** `seasons.is_suspension`; added **`team_season_participation`** (PARTICIPATING/SUSPENDED/NOT_ENTERED/UNKNOWN, evidence source, verification status, unique per team+season); IPL 2016/2017 seasons continue normally; RR 2027 = UNKNOWN (ADR-004) |
| Six-class membership conflates relationship + currency + eligibility | TRD/TMVE/PRD/AI | **Three dimensions**: `rr_relationship_state` (6 states) · `rr_current_state` (CURRENT/NOT_CURRENT/UNKNOWN) · `eligibility_status` (VERIFIED_ELIGIBLE/VERIFIED_NOT_ELIGIBLE/ELIGIBILITY_UNVERIFIED/NOT_ASSESSED, season-bound + `eligibility_policies` version, rule-source traceable, effective-dated, independently verified) — D5/ADR-005 |
| "Biometric" PIRE terminology + calibrated-looking scores | TRD/ARCH/PHASES/AI | **Contextual attribute corroboration** throughout; tiers are deterministic; 0.92/0.95/2 are **tunable matching thresholds**; numeric confidence only with `calibrated=TRUE`; identity/membership/coverage/eligibility confidences separated (ADR-007) |
| CDCRE post-identity-only (MIE circular dependency) | TRD/ARCH/PRD | **Dual capability**; MIE sequence: raw name → candidate discovery → PIRE corroboration → canonical ID → TMVE → CDCRE career → CPPAE/CMIE/SICE; AC-10 contract test |
| Metric definitions promised but absent | TRD/PRD | **`docs/DATA_DICTIONARY.md`** created: B/W/F/M-series + cross-cutting validation + NOT_COMPUTABLE list (false shots; inferred drops; soil sensors; untracked line/length; mental state) |
| Generic dataset descriptions, unsupported licence claims | README/PRD | **`docs/DATA_SOURCE_REGISTER.md`** created: source-to-field matrix with VERIFIED/PARTIALLY_VERIFIED/UNVERIFIED/UNAVAILABLE/RESTRICTED statuses, join keys, match/delivery reconciliation (event-sequence joins, not over/ball joins; wide/no-ball accounting; super-over handling; duplicate/missing rules; confidence levels), local verification log; Kaggle/HawkeyeStats now **not** called "open/permissive" without evidence |
| Phase 0 marked COMPLETE with unsupported audit claims | PHASES/README/docs-README | Split **0a documentation baseline (COMPLETE)** / **0b empirical data-source & licence audit (OPEN, PARTIALLY_COMPLETE)**; counts anchored to local inspection only |
| PROJECT.md still v1 Next.js/FastAPI/20-entity | PROJECT.md | Reconciled into current charter with prominent supersession banner + Appendix A (v1 inventory preserved, each feature re-mapped) |
| `.gitignore` ignores `CricSheet/` but data lives in `datasets/` | .gitignore | New rules: payload file types under `datasets/` (and legacy `CricSheet/`) ignored; LICENSE/README source-notice files remain trackable; `hackathon_dataset/` + large archives excluded; **verified with `git check-ignore`** |
| Hackathon Top-10 deliverable missing | PRD | §4.3 spec: eligibility verification, exact age as of evaluation date, roles, domestic evidence, T20 analysis, role-adjusted comparison, consistency, context, squad fit, risk/coverage limits, **transparent role-aware reproducible ranking** (versioned weights, shrinkage for small samples, age ordering within role groups), Top-10 + reserves + dossiers |

---

## 5. Additional Defects Discovered Independently

1. **ERD contained `TEAMS → SEASONS` relationship with no DDL counterpart** (ARCH §2.7) — removed; teams relate to seasons via `team_season_participation`.
2. **`TEAMS.home_venue_id` FK ordering**: `venues` created after `teams`/`matches` — DDL reordered so the script executes topologically.
3. **False-claim defaults beyond the brief**: `wicketkeeping_events.appearances DEFAULT 1`; `provenance_tier DEFAULT 'OFFICIALLY_REPORTED'` on `fielding_events`/`wicketkeeping_events` (asserts a classification nobody made); `match_phase NOT NULL` with no default (impossible for List A/FC rows) — now nullable; `is_not_out DEFAULT TRUE` (fabricates not-out DNB rows) — now data-set, `did_not_bat` explicit.
4. **`overs_completed NUMERIC(4,1)`** — decimal overs are ambiguous (13.4 ≠ 13+4/6); integer balls are the unit of record; over notation is a display derivation (D6).
5. **`runs_batter BETWEEN 0 AND 6`** rejects legal overthrows (>6 runs off one delivery event on a no-ball/wide) — cap removed; `> 6` flagged for DQ review instead of rejecting (D7).
6. **Innings↔delivery consistency** (match of a delivery vs match of its innings; legal-ball totals vs `total_legal_deliveries`) was only implied — now an explicit Service D reconciliation invariant (TRD §10.3/§9.4).
7. **Delivery-level provenance absent** — `deliveries.source_record_id` added (D9); provenance FKs extended to `matches`/`weather_conditions`/`verification_records.data_source_id`.
8. **`player_eligibility` needs a policy version** — `eligibility_policies` (season + version, rule source, effective/expiry, verified) added; eligibility rows always policy-bound.
9. **Negative membership had no requirements** — TRD §4.5 now specifies coverage scope, season list, squad-list + scorecard coverage, source quality, conflict handling, and human review for `NO_VERIFIED_RR_RELATIONSHIP`.
10. **`agent_cdcpre`** misspelling in AGENTS + docs/README → `agent_cdcre`.
11. **Historical count drift**: v1-era "2,822/2,832 files incl. 695 SMAT" contradicted local reality (1,939 JSON, no SMAT) — supersession recorded; no unsupported counts carried forward.
12. **"strict 3NF" claimed without support** — restated as "normalised 3NF core" with `derived_features` documented as the single exception.
13. **PRD AC scope** was AC-01…14 in v2.0.0; remediated AC set is **AC-01…AC-23** (all FRs mapped in §5 tables).
14. **Kaggle/Hawkeye licence over-claims** (v1 "open dataset", "MIT/Permissive") — now RESTRICTED/UNVERIFIED in the register until evidenced.
15. **Weather rows lacked timezone + match-method** — `venue_timezone`, `local_observation_time`, `spatial_temporal_match_method`, `data_provider` added (D10).
16. **Pitch ratings auto-generated from qualitative reports** — numeric ratings now require a `ratings_methodology_version`; original text preserved in `reported_description` (D10).
17. **Injury `injury_date NOT NULL`** — unknowns forced to a fake date; now nullable, `verified=FALSE` default semantics documented.
18. **`player_availability.availability_status` NOT NULL with no default** — row creation forced a guess; now nullable (unknown stays unknown).
19. **`match_phase` semantics for non-T20** — T20 phase taxonomy forced onto List A/FC rows; now nullable with an explicit "T20-derived" note.
20. **`player_team_history.season_id` missing** — team-history rows could not reference `seasons`; added nullable FK.
21. **README "Phase 2 first task" vs Phase 0b open** — recommended next task corrected to "close 0b, then Phase 1".
22. **docs/README changelog v2.0.0 row** — marked SUPERSEDED (by 2.1.0), current row added.

---

## 6. Changes Made, File by File

| File | Change class | Summary |
|---|---|---|
| `docs/DATA_SOURCE_REGISTER.md` | **NEW** | Source-to-field register, statuses, reconciliation plan, local verification log (2026-11-10), superseded-claims section |
| `docs/DATA_DICTIONARY.md` | **NEW** | B/W/F/M metric series with all ten required attributes; global conventions; NOT_COMPUTABLE list; cross-cutting DQ rules |
| `docs/TRD.md` | Major | 31-entity remediated DDL (D1–D10 decisions documented); PIRE deterministic tiers + calibration gate; TMVE 3 dimensions + §4.5 negative verification + §4.6 eligibility policy; CDCRE dual capability; MIE candidate-first sequence; CMIE weather/pitch separation; API table; NFRs |
| `docs/PRD.md` | Major | Revised workflow; FR traceability tables (contract · arch · phase · agent · AC); §4.3 Top-10 deliverable spec; AC-01…AC-23; scope partition incl. hackathon-minimum |
| `docs/ARCHITECTURE.md` | Major | 10 diagrams updated (MIE flow, PIRE tiers, TMVE dimensions, DDL-mirrored 31-entity ERD, ingestion, SICE, Streamlit, evidence); ADR-001…007 (incl. new ADR-004/005/007); honest validation notes |
| `docs/PHASES.md` | Major | Phase 0 split (0a/0b); per-phase objectives/subphases/IO/dependencies/checkpoints/ACs/testing/status; Top-10 ranking work in Phase 10; risk register R1–R12 |
| `docs/AGENTS.md` | Minor | 31-entity governance; PIRE/TMVE/CDCRE agent contracts corrected (`agent_cdcre`, three-dimension TMVE, dual CDCRE, calibrated-only confidence) |
| `docs/AI_INSTRUCTIONS.md` | Moderate | §4.1–4.3 rewritten (identity determinism, three dimensions, negative-verification rule, eligibility policy versioning); prohibition P7 updated; entity count; conclusion restated |
| `docs/README.md` | Major | Hub: 2 governing docs added to index; reading pathways; full traceability matrix (incl. F-H1 hackathon deliverable); v2.1.0 changelog; Phase 0 status |
| `PROJECT.md` | Major | Reconciled to current charter; prominent supersession banner; Appendix A preserves v1 inventory with per-feature disposition |
| `README.md` | Major | Product overview; 31 entities; three-dimension model; v2.0.0→v2.1.0 change table; repo layout; Phase 0a/0b status; recommended next task; licensing per register |
| `.gitignore` | Rewrite | `datasets/` payload types ignored (LICENSE/README notices stay trackable); legacy `CricSheet/` payload protection; `hackathon_dataset/` + archive exclusions; env/scratch entries; verified via `git check-ignore` |
| `DOCUMENTATION_PRE_REMEDIATION_AUDIT.md` | **NEW** (pre-audit, preserved) | Defect register DB/MEM/ST/DS/EN/ID/OR/DM/RC/GI/PH/CS families; verification methods available |
| `reports/DOCUMENTATION_REMEDIATION_AUDIT.md` | **NEW** | This report |

---

## 7. Revised Architecture

MIE (orchestrator; no invented facts) → PIRE / TMVE / CDCRE (dual capability) / CPPAE /
CMIE / SICE over Services A–E, on a **31-entity normalised PostgreSQL 16 core** with
`team_season_participation`, `player_membership_state`, `eligibility_policies`,
`player_eligibility`; Streamlit-first, frontend-agnostic contracts; deterministic query
path; flagged, provenance-tracked external research; calibration-gated confidence.

---

## 8. Revised Database Schema & Entity Count

**31 logical entities** (27 → +4, with `seasons.is_suspension` removed as a column):
1 `data_sources` · 2 `source_records` · 3 `verification_records` · 4 `players` ·
5 `player_aliases` · 6 `venues` · 7 `teams` · 8 `competitions` · 9 `seasons` ·
10 `team_season_participation` · 11 `squad_memberships` · 12 `player_team_history` ·
13 `matches` · 14 `innings` · 15 `deliveries` (partitioned; FKs; expression-unique on
derived features) · 16 `batting_innings` · 17 `bowling_spells` · 18 `fielding_events`
· 19 `wicketkeeping_events` · 20 `pitch_conditions` · 21 `weather_conditions` ·
22 `player_availability` · 23 `player_injuries` · 24 `player_awards` ·
25 `player_competition_history` · 26 `player_membership_state` ·
27 `eligibility_policies` · 28 `player_eligibility` · 29 `user_teams` ·
30 `user_team_players` · 31 `derived_features`.
(Count verified programmatically against the DDL: `CREATE TABLE` statements = 31,
excluding the 5 `deliveries_y*` partitions.)

---

## 9. Metric Dictionary Summary

`docs/DATA_DICTIONARY.md`: 17 batting (B01–B17 + FALSE_SHOT=NOT_COMPUTABLE), 12 bowling
(W01–W12, integer-balls of record, over notation derived), 9 fielding/WK
(F01–F09, recorded-only drops/saves, coverage classes), 7 match-contribution
(M01–M07; POTM as input signal only; measurable leverage, no mental state). Global
conventions: legal-vs-event separation, NULL-never-0.0, `format_tag` mandatory,
Super Over + DLS handling, minimum-sample flags, NOT_COMPUTABLE list.

---

## 10. Data-Source Coverage & Licence Findings

**Locally verified 2026-11-10** (files inspected): CricSheet IPL 1,243 · The Hundred
201 · ODI WC 265 (24 withheld by publisher policy) · T20 WC 230 (29 withheld) — all
JSON v1.3.0, **ODC-By** (LICENSE.txt in each archive). **SMAT: UNAVAILABLE locally**
(v1-era "695 files" claim describes the removed `CricSheet/` archive; supersession
recorded). **External sources** (Kaggle S6/S7, HawkeyeStats S8, Open-Meteo S9, BCCI/
ESPN/Cricbuzz S10–S12): **UNVERIFIED/RESTRICTED pending Phase 0b** — no permissive
licence assumed; the 2007-claim quarantine rule is documented.

---

## 11. Phase Status Corrections

Phase 0 → **0a COMPLETE** (documentation baseline) / **0b OPEN (PARTIALLY_COMPLETE)**:
local dataset inventory + local licence verification done (register §3); external
source verification (Kaggle terms, HawkeyeStats repo licence, Open-Meteo current terms,
BCCI/ESPN access restrictions) outstanding. No phase claims exact counts beyond locally
verified figures.

---

## 12. Link-Validation Results

GitHub-compatible slug checker (lowercase; strip non-word; each space → hyphen, no
collapsing; duplicate-heading detection) over all 11 markdown docs:
- **79 internal anchors checked → 0 broken** after remediation (the pre-fix checker run
  reported 81; the delta was the checker's own space-collapse bug plus the two
  links to this final report, which resolve at commit time).
- Duplicate heading scan: 0 duplicates.
- All relative file paths resolve.

---

## 13. Mermaid-Validation Results (with recorded limitation)

**No Mermaid CLI/parser is available in this environment** (`@mermaid-js/mermaid-cli`
not installable offline; no node_modules present). What was done instead:
- Structural lint of all 10 diagrams in `ARCHITECTURE.md`: fence balance, `subgraph`/
  `end` pairing (5/5 in diagram 1, 1/1 in diagram 9, 0 elsewhere), unique node
  identifiers, edge-token sanity — **0 issues**.
- **A full parser-validation gate (mermaid-cli lint of all 10 diagrams) is therefore
  recorded as a Phase 9 checkpoint** (see PHASES §11). This report does **not** claim
  syntax validation.

---

## 14. SQL-Validation Results (with recorded limitation)

- **sqlglot 30.30, PostgreSQL dialect**: the complete 31-table DDL (78 executable
  statements after comment stripping) parses with **0 syntax errors**.
- **Structural checks (programmatic)**: all FK target tables defined; partitioned
  `deliveries` composite PK includes the partition key; the `fielding_events`
  composite FK `(delivery_id, season_year)` is a subset of the `deliveries` PK;
  `derived_features` unique constraint now an expression index (expression UNIQUE in a
  table constraint removed); no undefined FK targets.
- **ERD↔DDL**: 31/31 entity match; 51 ERD relationships → every pair backed by an FK
  in one direction (two gaps found and fixed: `verification_records.data_source_id`,
  `weather_conditions.source_record_id`).
- **Limitation**: sqlglot is a transpiler-grade parser, not PostgreSQL's server
  parser; **no live PostgreSQL / Docker execution was available** (psql absent, Docker
  daemon not running), so execution-level checks (deferred FK trigger behaviour on
  partitioned tables, constraint enforcement) remain an explicit **Phase 2 gate**.

---

## 15. Cross-Document Consistency Results

Checked by grep + programmatic cross-reference:
- **Product name** "RR Squad Intelligence & Team Composition Platform": consistent
  across all 11 docs.
- **Entity count 31**: TRD/ARCH/PHASES/AGENTS/AI/PRD/README/PROJECT/docs-README
  (no residual "27-entity" claims outside the changelog rows).
- **Engine names**: PIRE/TMVE/CDCRE/CPPAE/CMIE/SICE + MIE + Services A–E consistent;
  `agent_cdcre` everywhere (misspelling `agent_cdcpre` eliminated).
- **Three-dimension membership** + `team_season_participation` + `eligibility_policies`:
  consistent; "six-class" appears only in supersession context.
- **Phase status** (0a COMPLETE / 0b OPEN): consistent in PHASES/README/docs-README.
- **AC set**: PRD AC-01…AC-23; every FR row carries contract · architecture · phase ·
  agent · AC (traceability tables, PRD §5).
- **`datasets/` path + ODC-By + counts**: consistent with register §3; legacy
  `CricSheet/` references confined to .gitignore legacy protection + changelog rows.

---

## 16. Remaining Limitations (honest, unhidden)

1. **No live PostgreSQL execution** of the 31-entity DDL (no psql/dockerd). sqlglot
   parse + structural FK/PK checks passed; execution-level validation is a Phase 2
   gate.
2. **No Mermaid parser validation** — structural lint only; mermaid-cli gate deferred
   to Phase 9.
3. **External source licences unverified** (Kaggle S6/S7, HawkeyeStats S8, Open-Meteo
   S9, official records S10–S12) — Phase 0b open; ingestion of those sources is gated
   on it.
4. **SMAT coverage**: locally unavailable; any SMAT claim in a submission must carry a
   research provenance record.
5. **Ranking model configuration** (weights, shrinkage constant k): specified and
   versioning rules defined (PRD §4.3), but **no calibrated values exist yet** — they
   are produced and validated in Phase 10, not asserted here.
6. `player_membership_state.as_of_date` uniqueness means one evaluation snapshot per
   date; history of reclassifications accumulates rows by date (by design; noted for
   implementers).

---

## 17. Separate Commit List (one file = one commit, Part 19)

Created in this order on `docs/squad-intelligence-revision-v2` (local only; **not
pushed** — hashes below for user review/push). Each commit staged exactly one file
(`git diff --cached --name-only` verified before every commit; no `git add .` / `-A`
used; no squashing).

| # | File | Commit |
|---|---|---|
| 1 | `docs/DATA_SOURCE_REGISTER.md` | `1245996` |
| 2 | `docs/DATA_DICTIONARY.md` | `8ebdc50` |
| 3 | `docs/TRD.md` | `44a0a20` |
| 4 | `docs/PRD.md` | `aad5783` |
| 5 | `docs/ARCHITECTURE.md` | `41e27b2` |
| 6 | `docs/PHASES.md` | `cf75596` |
| 7 | `docs/AGENTS.md` | `0b74496` |
| 8 | `docs/AI_INSTRUCTIONS.md` | `02e7085` |
| 9 | `docs/README.md` | `736d168` |
| 10 | `PROJECT.md` | `d739127` |
| 11 | `README.md` | `adc83d0` |
| 12 | `.gitignore` | `1d55771` |
| 13 | `DOCUMENTATION_PRE_REMEDIATION_AUDIT.md` | `7777d1f` |
| 14 | `reports/DOCUMENTATION_REMEDIATION_AUDIT.md` | _(this commit — hash visible via `git log --oneline -1` after commit; recorded in the session transcript, not in the file)_ |

---

## 18. Recommended First Implementation Task

**Close Phase 0b, then start Phase 1**: (a) produce dated evidence rows in
`data_sources` for the external licences (Kaggle terms, HawkeyeStats repo licence,
Open-Meteo current terms, BCCI/ESPN access rules) so ingestion of external sources is
lawful; (b) implement the Phase 1 ingestion pipeline over the **locally verified**
datasets (1,243/201/265/230; SMAT gap recorded), including the Phase 2 migration gate
that **executes the 31-entity DDL in a real PostgreSQL 16 database** (closing
Limitation 1) and validates the partitioned-`deliveries` FKs and the
`derived_features` expression index.

---

## 19. Final Verdict

All listed material defects are remediated and cross-checked; the two validation
limitations (no live PostgreSQL execution, no Mermaid parser) are recorded, scoped as
phase gates, and do not mask any unresolved *documentation* defect. Remaining items in
§16 are explicitly future-work, not unresolved defects in the delivered specification.

**GOOD TO GO**


---

## 20. Addendum — v2.2.0 PVRE Dual-Mode Engine Architecture Revision (2026-11-10)

### 20.1 Executive Summary & Baseline
- **Revision Target**: Platform Architecture & Documentation Version `v2.2.0-PVRE-DUAL-MODE`.
- **Git Baseline Commit**: `eaebdcb29f7912451a1af05b4fa6973379d302bd` (`origin/main`).
- **Target Branch**: `docs/v2.2.0-pvre-dual-mode`.
- **Architectural Scope**: Introduces **ENGINE 07 — PVRE (Player Verification & Research Engine)** into the authoritative architecture, orchestrating two distinct execution modes:
  1. **Mode A — Existing RR Player Replacement Intelligence**: Evaluates verified current/historical Rajasthan Royals players by auditing their complete RR participation history (Module A1) and analyzing their recent performance across a configurable 2-to-3 year global window (Module A2: BBL, PSL, CPL, SA20, The Hundred, domestic T20, international cricket). Synthesises replaceability signals (`RETAIN_SIGNAL`, `MONITOR_SIGNAL`, `POTENTIALLY_REPLACEABLE`, `INSUFFICIENT_EVIDENCE`, `REVIEW_REQUIRED`) in Module A3 and forwards structured dossiers to SICE.
  2. **Mode B — Verified Uncapped Candidate Intelligence**: Executes comprehensive domestic career discovery (Ranji, SMAT, Vijay Hazare, Duleep, U19/U23) for players not associated with RR who are independently verified as uncapped-eligible under the applicable season policy.
  3. **Mandatory REVIEW_REQUIRED Safety Gate**: Deterministic fallback whenever player identity, RR association, or eligibility evidence conflicts or remains incomplete. Unresolved candidates never enter the verified ranking pool.
  4. **SICE Incumbent-vs-Candidate Comparison Integration (§8.4)**: Evaluates incumbent RR players against role-matched verified uncapped candidates across 16 multi-dimensional metrics (D01–D16).
  5. **Strict Architectural Decoupling**: Mode A incumbent replacement evaluation (`run_type = 'REPLACEMENT_EVALUATION'`) is strictly isolated from the hackathon Top-10 uncapped candidate ranking (`run_type = 'HACKATHON_TOP10'`, `RK-1.0.0`). Mode A evaluations never alter or contaminate the standalone candidate discovery board.

### 20.2 Architectural Metrics & Counts Reconciled
- **Specialised Engines**: Reconciled from 6 to **7 engines** (PIRE, TMVE, CDCRE, CPPAE, CMIE, SICE, PVRE).
- **Support Services**: Strictly categorized as **5 support services** (Service A: Data Ingestion, Service B: Profile Generator, Service C: Source Verification & Provenance, Service D: Data Quality & Coverage, Service E: Team Builder) plus 1 specialized policy service (Agent 04b Eligibility Policy Service).
- **Central PostgreSQL Core**: Reconciled and verified at **33 entities** (including `player_season_stats` and `player_match_stats` as verified 3NF historical aggregates; schema audit confirmed zero DDL changes required for PVRE data persistence).
- **Multi-Agent System**: Reconciled from 16 to **18 system agents** (adding `agent_pvre` as Agent 08b; Family 1: 2, Family 2: 8, Family 3: 5, Family 4: 3).
- **Engineering Roadmap**: Added **Phase 4B `[STATUS: PLANNED - MVP]`** to `docs/PHASES.md` with 12 explicit checkpoints, acceptance criteria AC-24 through AC-30, and 10 explicit test scenarios.
- **Acceptance Criteria**: Expanded from AC-01..AC-23 to **AC-01..AC-30**.

### 20.3 Empirical Local Dataset Audit & Register Expansion
Empirical filesystem inspection of `datasets/` verified local presence of **5,083 JSON match files** across 13 directories:
- `ipl_male_json`: 1,243 files (ODC-By v1.0)
- `bbl_male_json`: 662 files (ODC-By v1.0)
- `sma_json`: 695 files (ODC-By v1.0 — Syed Mushtaq Ali Trophy verified locally present, resolving prior documentation ambiguity!)
- `bpl_male_json`: 469 files (ODC-By v1.0)
- `cpl_male_json`: 445 files (ODC-By v1.0)
- `psl_male_json`: 357 files (ODC-By v1.0)
- `icc_mens_cricket_world_cup_male_json`: 265 files (ODC-By v1.0, 24 withheld per policy)
- `icc_mens_t20_world_cup_male_json`: 230 files (ODC-By v1.0, 29 withheld per policy)
- `hnd_male_json`: 201 files (ODC-By v1.0, balls_per_over=5)
- `lpl_male_json`: 143 files (ODC-By v1.0)
- `ilt_male_json`: 134 files (ODC-By v1.0)
- `sat_male_json`: 130 files (ODC-By v1.0)
- `mlc_male_json`: 109 files (ODC-By v1.0)
Dedicated domestic and age-group sources (S18A–H, S19B, S20B) and API/browser access constraints documented in `docs/DATA_SOURCE_REGISTER.md`.

### 20.4 Document Modification Summary
All 14 authoritative documentation files updated and cross-synchronised:
1. `README.md`: Bumped to v2.2.0; 7 engines, 18 agents, 5 support services, 33 entities; updated architecture overview, engine table, repository layout, roadmap, and implementation status.
2. `PROJECT.md`: Bumped to v2.2.0; 7 engines, 18 agents, 5 support services, 33 entities; updated feature inventory and roadmap (added Phase 4B); preserved Appendix A.
3. `DOCUMENTATION_PRE_REMEDIATION_AUDIT.md`: Preserved historical audit baseline intact; added dated v2.2.0 supersession banner at top documenting supersession by v2.1.1 (`eaebdcb`) and v2.2.0 (`docs/v2.2.0-pvre-dual-mode`).
4. `reports/DOCUMENTATION_REMEDIATION_AUDIT.md`: Updated Section 20 Addendum covering full 14-file suite, 5,083 JSON dataset audit, 5 support services, and final approval verdict.
5. `docs/README.md`: Bumped to v2.2.0; 7 engines, 18 agents, 5 support services, 33 entities; clarified 31-to-33 entity historical progression; updated reading pathways, traceability matrix, and changelog.
6. `docs/PRD.md`: Bumped to v2.2.0; 7 engines, 18 agents, 5 support services, 33 entities; updated Section 4 workflow; added Use Cases 5, 6, 7; added FR-S6 and FR-PV1..8; updated Views 4, 8, 10, 11; added AC-24..AC-30.
7. `docs/TRD.md`: Bumped to v2.2.0; 7 engines; updated Section 2.3 MIE sequence (MIE sole cross-engine orchestrator; Mother Controller internal to PVRE); added Section 8.4 SICE replacement comparison; added Section 9 PVRE (9.1..9.7) with 26-field typed output contract; updated Section 10 (5 support services, local SMAT lake note); added Section 11.5 documenting 33-entity schema audit.
8. `docs/ARCHITECTURE.md`: Bumped to v2.2.0; 7 engines, 33 entities; updated Diagram 1 and Diagram 2b establishing MIE as sole cross-engine orchestrator and Mother Controller as internal router; added Diagrams 2c, 2d, 2e; added ADR-008.
9. `docs/PHASES.md`: Bumped to v2.2.0; added Phase 4B `[PLANNED - MVP]` with 12 checkpoints, AC-24..AC-30, 26-field contract compliance, and 10 explicit test scenarios; updated Phase 7 (MIE) and Phase 8 (SICE) with explicit Phase 4B dependencies; updated Hackathon phase; added Risks R-13, R-14.
10. `docs/AGENTS.md`: Bumped to v2.2.0; updated hierarchy diagram for 18 agents, 7 engines, 5 support services; updated MIE, SICE, Docs, QA agent contracts; added `agent_pvre`.
11. `docs/AI_INSTRUCTIONS.md`: Bumped to v2.2.0; 33 entities, 7 engines, 5 support services; added Domain Commandments R13–R22.
12. `docs/DATA_SOURCE_REGISTER.md`: Bumped to v2.2.0; added S18A–H, S19B, S20B; updated SMAT local presence (695 files); added global franchise files (BBL, PSL, CPL, SA20, etc., totaling 5,083 JSON files); added Section 2.4 API/browser access constraints; added Section 2.5 marking protocol, conflict resolution, and fallback behavior.
13. `docs/DATA_DICTIONARY.md`: Bumped to v2.2.0; added Section 9 (PVRE Recent-Form Metrics R01–R06 with exponential decay and gap taxonomy), Section 10 (PVRE Replacement Assessment Signals), Section 11 (SICE 16 Role-Aware Comparison Dimensions D01–D16).
14. `docs/RANKING_SPEC.md`: Bumped to v2.2.0; decoupled Top-10 uncapped ranking (`RK-1.0.0`) from Incumbent Replacement Evaluation (`RE-1.0.0`); added Section 9 for SICE replacement comparison reproducibility and storage in `ranking_runs`.

### 20.5 Verification & Audit Results
- **Cross-Document Consistency**: Engine count (7), Agent count (18), Entity count (33), Acceptance Criteria (AC-01..AC-30), and Phase count (Phase 0a/0b, Phases 1–4, 4B, 5–10) verified 100% consistent across all documents.
- **Link Integrity**: Internal markdown document links verified valid.
- **Guardrail Adherence**:
  * No arbitrary composite scores (prohibited; 16 multi-dimensional matrix mandated).
  * No uncalibrated replacement probabilities (prohibited; discrete assessment states mandated).
  * No silent mode fallback (prohibited; `REVIEW_REQUIRED` hard safety path enforced).
  * No assumption of uncapped status for unknown players (prohibited; independent policy verification mandated).
  * Greenfield Baseline status preserved uniformly across all documents (`[STATUS: PLANNED - GREENFIELD BASELINE]`).

### 20.6 Final Verdict
**DOCUMENTATION GOOD TO GO — v2.2.0 APPROVED ARCHITECTURAL BASELINE**
