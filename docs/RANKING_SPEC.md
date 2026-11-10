# Hackathon Candidate Ranking Specification

**Project**: RR Squad Intelligence & Team Composition Platform
**Document Version**: 1.0.0 · **Status**: `[STATUS: PLANNED - GREENFIELD BASELINE]`
**Companion to**: [`TRD.md`](TRD.md) §8 (SICE) + §10.3 (`ranking_configurations`,
`ranking_runs`) · [`PRD.md`](PRD.md) Use Case 3 · [`DATA_DICTIONARY.md`](DATA_DICTIONARY.md)
M01–M07 · [`DATA_SOURCE_REGISTER.md`](DATA_SOURCE_REGISTER.md) §S10
**Config version**: `RK-1.0.0` (first published configuration; all future changes are new
versions, never edits to a published one)

---

## 1. Purpose and Scope

Use Case 3 requires a **Top-10 list of the youngest eligible uncapped players**, each with
age, role, and performance evidence. This document is the single, versioned, reproducible
definition of that method. It is **not** an inline constant and it is **not**
`derived_features.model_version`: the full method lives here and in
`ranking_configurations` (TRD D16); each execution is frozen in `ranking_runs` (TRD D17)
so identical inputs yield exactly one stored board (AC-18 / AC-25).

The output is labelled **ANALYTICAL_RECOMMENDATION** in every rendering. It is **not** an
official RR selection, not an auction decision, and it carries **no recruitment
probabilities** (TRD §8.3).

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
