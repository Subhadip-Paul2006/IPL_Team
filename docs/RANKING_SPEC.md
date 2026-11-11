# Candidate Ranking & Replacement Intelligence Specification

**Project**: RR Squad Intelligence & Team Composition Platform
**Document Version**: 2.2.0-PVRE-DUAL-MODE · **Status**: `[STATUS: PLANNED - GREENFIELD BASELINE]`
**Companion to**: [`TRD.md`](TRD.md) §8 (SICE), §8.4 (Replacement Comparison), §9 (PVRE) + §11.3 (`ranking_configurations`,
`ranking_runs`) · [`PRD.md`](PRD.md) Use Cases 3 & 5 · [`DATA_DICTIONARY.md`](DATA_DICTIONARY.md)
M01–M07, R01–R06, D01–D16 · [`DATA_SOURCE_REGISTER.md`](DATA_SOURCE_REGISTER.md) §S10–S20
**Config versions**: `RK-1.0.0` (Top-10 Uncapped Candidate Ranking) · `RE-1.0.0` (Incumbent Replacement Evaluation)

---

## 1. Purpose and Scope

This document specifies the versioned, deterministic, and auditable methodologies for two distinct analytical workflows executed by SICE:

1. **Hackathon Top-10 Uncapped Candidate Ranking (`RK-1.0.0`)**: Use Case 3 requires a Top-10 list of the youngest verified eligible uncapped players with age, role, and domestic performance evidence.
2. **Incumbent-vs-Candidate Replacement Comparison (`RE-1.0.0`)**: Use Case 5 (PVRE Mode A integration) requires evaluating an existing/historical Rajasthan Royals player against role-matched verified uncapped candidates across 16 multi-dimensional metrics.

> **Strict Architectural Separation**:
> The Top-10 Uncapped Candidate Ranking workflow (`run_type = 'HACKATHON_TOP10'`) and the Incumbent Replacement Evaluation workflow (`run_type = 'REPLACEMENT_EVALUATION'`) are **completely decoupled**.
> Evaluating an incumbent player under PVRE Mode A **never** modifies, re-weights, or contaminates the standalone Top-10 uncapped ranking. The Top-10 board is a persistent, independent discovery artifact.

Every execution is frozen in `ranking_runs` (TRD §11.3) so identical inputs yield identical stored results (AC-18, AC-25, AC-28). Outputs are labelled **ANALYTICAL_RECOMMENDATION** or **ANALYTICAL_REPLACEMENT_ASSESSMENT**. They are **not** official RR selections, not auction decisions, and carry **no recruitment probabilities** (TRD §8.3, §9.7).

---

## 2. Candidate Universe (the eligible pool)

A candidate is a player who satisfies **all** of the following at `evaluation_date`:

1. **Identity resolved** — `players.identity_status IN ('RESOLVED','PROVISIONAL')`
   (Tier 1–3 resolution; PROVISIONAL candidates are flagged in the board's provenance).
2. **Uncapped-eligible, VERIFIED** — `player_eligibility.eligibility_status =
   'VERIFIED_ELIGIBLE'` under the **active `eligibility_policies` version** for the target
   season (policy carried by `ranking_configurations.policy_id`). Per the platform's
   standing rules, **an unknown player is never assumed uncapped**: players with no
   verified eligibility row default to `NOT_ASSESSED` and are excluded from the pool, not
   promoted into it.
3. **Age band** — `date_of_birth` between `config.evaluation_date − max_age` and
   `config.evaluation_date − min_age` (config values, `RK-1.0.0`: min_age = 18,
   max_age = 26, inclusive). **Age is computed as of the recorded `evaluation_date`,
   never the wall clock** (determinism requirement).
4. **Minimum observed sample** — at least `config.min_sample.verified_innings`
   (`RK-1.0.0`: 5) verified innings across **any** of the formats in
   `config.formats` (`RK-1.0.0`: T20, LIST_A, FIRST_CLASS, ODI, HUNDRED-deferred →
   in practice T20/LIST_A/FIRST_CLASS/ODI; HUNDRED is `DEFERRED` and contributes no
   derived rate until the balls_per_over = 5 handling is validated, per
   DATA_DICTIONARY §5). Players with fewer samples remain **in** the pool (eligibility and
   age stand) but cannot clear the relevance gate (§4), so they may not enter the Top-10
   unless no candidate clears the gate, in which case the board states this explicitly.

The pool is stored verbatim in `ranking_runs.candidate_pool` (JSONB) so the exact input
set of a board is auditable.

---

## 3. Relevance Gate (`config.gate_thresholds_json`)

Before ranking, every pool candidate passes a **within-role** relevance gate:

- Candidates are grouped into the role groups of `config.role_grouping_json`
  (`RK-1.0.0`: Top-order Batter · Wicketkeeper Batter · Batting All-rounder ·
  Bowling All-rounder · Pace Bowler · Spin Bowler). Role comes from
  `players.primary_role`; a Wicketkeeper batter's batting metrics are computed on
  `innings.is_super_over = FALSE` rows only.
- A candidate clears the gate when, within their role group, their verified
  career `batting_strike_rate` (B10) is **at or above** `gate.baseline_percentile`
  of the role group's distribution **and** their career sample
  (`balls_faced`) is at least `gate.min_sample_balls` (`RK-1.0.0`: 75th percentile;
  120 balls). Bowling-only roles use `bowling_strike_rate` (W07) vs wickets at or
  above `gate.baseline_percentile` with `legal_balls_bowled >= gate.min_sample_balls`.
- Candidates who **do not clear the gate** stay in the pool and are eligible for the
  **reserves list** (§6). The gate excludes only from the Top-10 ordering.

Sample sizes are always reported alongside; a small sample never substitutes for a
large one (DATA_DICTIONARY global conventions).

---

## 4. Ordering Keys (`config.ordering_json`, three-level hierarchy)

Ranked candidates are ordered by:

1. **Primary — age (youngest first)**: `age_at_evaluation` in descending birth-order
   (i.e. most recent DOB first). Age is computed from `players.date_of_birth` against
   `config.evaluation_date`.
2. **Secondary — consistency score (reproducible)**:
   `consistency = (verified_innings − DNB_innings) / verified_innings` over the same
   sample set as §2.4, i.e. innings-innings actually batted divided by appearances.
   Higher = more consistent. All metric inputs are **verified** records only.
3. **Tertiary — career batting average (B05)** within `config.formats`, computed
   format-aware (no cross-format mix); `NULL` average (0 dismissals, `*`) sorts
   **after** a computed value at the same age and consistency (a not-out-only record is
   weaker evidence than a computed average).

No LLM, no subjective weighting, no recruitment probability: the three keys are
deterministic SQL expressions over the central database (TRD §11 determinism rule).

---

## 5. Tiebreakers (`config.tiebreakers_json` — total order, documented)

When all three keys are equal, the **final deterministic tiebreak** is applied in this
exact order:

1. `batting_strike_rate` (B10) descending;
2. `career balls_faced` (B04) descending (larger sample wins);
3. `player_id` **string form** ascending (UUIDv4 lexicographic — a total order; it exists
   solely so the board is a function of inputs only, never of execution order).

The seed `config.seed` (`RK-1.0.0`: 0) is recorded in every run; seed 0 means **pure
deterministic SQL ordering with no random component**. A non-zero seed may be used only
to sample among a documented *equivalence class* and must be logged in
`ranking_runs.determinism_note`.

---

## 6. Output: Top-10 and Reserves

- **Top-10**: the first 10 gate-passing candidates under the §4 ordering, each rendered
  with: canonical name · age at `evaluation_date` · role · venue/competition sample
  summary · B05/B10 (with sample counts) · eligibility evidence link
  (`verification_records`) · PIRE identity status · a one-line evidence-backed summary.
- **Reserves**: the next-ranked eligible pool members after position 10 (default: next 5),
  stored in `ranking_runs.reserve_list` and labelled **RESERVE — not in Top-10**.
- Every entry carries `source_provenance` (Service C) and `format_tag`s; zero-sample
  metrics render as "no data", never 0.0 (AI_INSTRUCTIONS R1).
- The board is a **recommendation artifact**: SICE composes it for the Squad Intelligence
  Report; it is explicitly not an official RR selection.

---

## 7. Reproducibility & Configuration (`RK-1.0.0` snapshot)

The configuration published with this document (`RK-1.0.0`) freezes:

| Key | `RK-1.0.0` value |
|---|---|
| `target_season_id` | the hackathon target season (IPL 2027, participation `UNKNOWN`/`UNVERIFIED` — the season row itself stays evidence-bound per TRD D15; ranking targets **uncapped-eligible** players for that season, whose eligibility is assessed under the active policy, not the RR squad) |
| `policy_id` | the active `eligibility_policies` version for the target season |
| `evaluation_date` | recorded date-of-run (e.g. submission date), **stored, not implicit** |
| `min_age` / `max_age` | 18 / 26 (inclusive) |
| `forms` / `formats` | T20 · LIST_A · FIRST_CLASS · ODI (HUNDRED `DEFERRED`) |
| `min_sample.verified_innings` | 5 |
| `gate.baseline_percentile` | 75th within role group |
| `gate.min_sample_balls` | 120 |
| `role_grouping` | the six SICE role groups |
| ordering | age desc-birth → consistency → B05 (rules in §4) |
| tiebreakers | B10 → balls_faced → `player_id` string (rules in §5) |
| `seed` | 0 |

**Run rule**: `run_ranking(config_version, data_snapshot)` produces exactly one
`ranking_runs` row keyed `(config_id, data_snapshot_sha256)`. The `data_snapshot_sha256`
is the SHA-256 over the frozen candidate-pool + relevant metric set, so a re-run on the
same data with the same config is a no-op (row exists), and any data or config change
produces a new, separately stored board. This is the mechanism behind AC-18/AC-25.

---

## 8. Guardrails (inherited from the platform)

- No fabricated players: every row maps to a `players.player_id` with a resolved/
  provisional identity and a verified-eligibility evidence link.
- No assumed uncapped: `NOT_ASSESSED` and `ELIGIBILITY_UNVERIFIED` players are excluded.
- No recruitment probabilities; no official RR/auction claims; no mental-state inference
  (leverage statements, if surfaced, use only M06's measurable-state definition).
- Proprietary hackathon dataset content is **never** part of a public export; it may only
  seed a `verification_records`-backed eligibility/identity row under the confidential
  handling rules (TRD §9.2, AI_INSTRUCTIONS R5).


---

## 9. SICE Incumbent-vs-Candidate Replacement Evaluation (`RE-1.0.0`)

### 9.1 Ingestion of PVRE Mode A Output
When PVRE executes Mode A (Existing RR Player Replacement Intelligence), SICE receives the structured incumbent profile:
1. **Module A1 Dossier**: Verified Rajasthan Royals historical participation, seasons, roles, batting/bowling aggregates, phase performance, and contribution history.
2. **Module A2 Dossier**: Recent global performance across a configurable 2-to-3 year window relative to `evaluation_date` (e.g. BBL, PSL, CPL, SA20, The Hundred, domestic cricket), including window metrics R01–R06 and participation gap analysis.
3. **Module A3 Signal**: Analytical replaceability signal (`RETAIN_SIGNAL`, `MONITOR_SIGNAL`, `POTENTIALLY_REPLACEABLE`, `INSUFFICIENT_EVIDENCE`, `REVIEW_REQUIRED`).

If the incumbent profile carries `REVIEW_REQUIRED`, SICE halts automated comparison and routes the dossier directly to human review (AC-27).

### 9.2 Candidate Matching & Role Filtering
SICE identifies candidate comparison prospects from the verified uncapped candidate pool:
1. **Primary Role Match**: Matches incumbent's `primary_role` and batting/bowling style.
2. **Phase Suitability**: Verifies candidate phase presence (e.g. death bowling overs, powerplay strike rate) aligns with incumbent deployment history.
3. **Eligibility & Age Verification**: Restricts candidates strictly to verified uncapped players under the active season policy (`player_eligibility.eligibility_status = 'VERIFIED_ELIGIBLE'`).

### 9.3 16-Dimensional Comparison Matrix
SICE executes a point-by-point comparison across the 16 dimensions defined in [`DATA_DICTIONARY.md`](DATA_DICTIONARY.md) §11:
- **Batting**: D01 (Base Strike Rate), D02 (Batting Average), D03 (Boundary %), D04 (Dot Ball %).
- **Phases**: D05 (Powerplay Impact), D06 (Middle Acceleration), D07 (Death Execution).
- **Bowling**: D08 (Economy Rate), D09 (Bowling Strike Rate), D10 (Dot Ball Pressure), D11 (Phase Bowling Control).
- **Match Context**: D12 (Matchup Resilience), D13 (High-Leverage Execution M06), D14 (Fielding Contribution F01–F09).
- **Trajectory & Confidence**: D15 (Age & Trajectory Delta), D16 (Sample Adequacy & Evidentiary Tier).

### 9.4 Reproducibility and Storage in `ranking_runs`
Every replacement comparison is executed deterministically and frozen in `ranking_runs`:
- `run_type`: `'REPLACEMENT_EVALUATION'`.
- `config_id`: Reference to `ranking_configurations` row (`RE-1.0.0`).
- `data_snapshot_sha256`: SHA-256 over incumbent profile JSON + candidate pool JSON + metric records.
- `candidate_pool`: JSONB containing incumbent player ID and evaluated candidate IDs.
- `ranking_output`: JSONB containing:
  * `incumbent_summary`: Canonical identity, RR seasons, recent window metrics, sample indicators.
  * `replaceability_signal`: PVRE Module A3 assessment state.
  * `candidate_comparisons`: Array of top role-matched uncapped candidates with 16-dimension deltas and confidence intervals.
  * `provenance_record`: Link to underlying `source_records` and `verification_records`.

### 9.5 Strict Guardrails
- **No Composite Scores**: SICE must NOT collapse the 16 comparison dimensions into a single scalar replacement index.
- **No Uncalibrated Probabilities**: SICE must NOT output replacement probabilities or automated release recommendations.
- **No Hackathon Ranking Contamination**: Incumbent evaluation results are stored under `run_type = 'REPLACEMENT_EVALUATION'` and are strictly isolated from hackathon Top-10 uncapped candidate runs (`run_type = 'HACKATHON_TOP10'`).
