import re

with open('docs/RANKING_SPEC.md', 'r', encoding='utf-8') as f:
    content = f.read().replace('\r\n', '\n')

# 1. Update header
old_header = """# Hackathon Candidate Ranking Specification

**Project**: RR Squad Intelligence & Team Composition Platform
**Document Version**: 1.0.0 · **Status**: `[STATUS: PLANNED - GREENFIELD BASELINE]`
**Companion to**: [`TRD.md`](TRD.md) §8 (SICE) + §10.3 (`ranking_configurations`,
`ranking_runs`) · [`PRD.md`](PRD.md) Use Case 3 · [`DATA_DICTIONARY.md`](DATA_DICTIONARY.md)
M01–M07 · [`DATA_SOURCE_REGISTER.md`](DATA_SOURCE_REGISTER.md) §S10
**Config version**: `RK-1.0.0` (first published configuration; all future changes are new
versions, never edits to a published one)"""

new_header = """# Candidate Ranking & Replacement Intelligence Specification

**Project**: RR Squad Intelligence & Team Composition Platform
**Document Version**: 2.2.0-PVRE-DUAL-MODE · **Status**: `[STATUS: PLANNED - GREENFIELD BASELINE]`
**Companion to**: [`TRD.md`](TRD.md) §8 (SICE), §8.4 (Replacement Comparison), §9 (PVRE) + §11.3 (`ranking_configurations`,
`ranking_runs`) · [`PRD.md`](PRD.md) Use Cases 3 & 5 · [`DATA_DICTIONARY.md`](DATA_DICTIONARY.md)
M01–M07, R01–R06, D01–D16 · [`DATA_SOURCE_REGISTER.md`](DATA_SOURCE_REGISTER.md) §S10–S20
**Config versions**: `RK-1.0.0` (Top-10 Uncapped Candidate Ranking) · `RE-1.0.0` (Incumbent Replacement Evaluation)"""

assert old_header in content, "Could not find old_header in RANKING_SPEC.md"
content = content.replace(old_header, new_header, 1)

# 2. Update Section 1 Purpose & Scope to clarify the two distinct workflows
old_sec1 = """## 1. Purpose and Scope

Use Case 3 requires a **Top-10 list of the youngest eligible uncapped players**, each with
age, role, and performance evidence. This document is the single, versioned, reproducible
definition of that method. It is **not** an inline constant and it is **not**
`derived_features.model_version`: the full method lives here and in
`ranking_configurations` (TRD D16); each execution is frozen in `ranking_runs` (TRD D17)
so identical inputs yield exactly one stored board (AC-18 / AC-25).

The output is labelled **ANALYTICAL_RECOMMENDATION** in every rendering. It is **not** an
official RR selection, not an auction decision, and it carries **no recruitment
probabilities** (TRD §8.3)."""

new_sec1 = """## 1. Purpose and Scope

This document specifies the versioned, deterministic, and auditable methodologies for two distinct analytical workflows executed by SICE:

1. **Hackathon Top-10 Uncapped Candidate Ranking (`RK-1.0.0`)**: Use Case 3 requires a Top-10 list of the youngest verified eligible uncapped players with age, role, and domestic performance evidence.
2. **Incumbent-vs-Candidate Replacement Comparison (`RE-1.0.0`)**: Use Case 5 (PVRE Mode A integration) requires evaluating an existing/historical Rajasthan Royals player against role-matched verified uncapped candidates across 16 multi-dimensional metrics.

> **Strict Architectural Separation**:
> The Top-10 Uncapped Candidate Ranking workflow (`run_type = 'HACKATHON_TOP10'`) and the Incumbent Replacement Evaluation workflow (`run_type = 'REPLACEMENT_EVALUATION'`) are **completely decoupled**.
> Evaluating an incumbent player under PVRE Mode A **never** modifies, re-weights, or contaminates the standalone Top-10 uncapped ranking. The Top-10 board is a persistent, independent discovery artifact.

Every execution is frozen in `ranking_runs` (TRD §11.3) so identical inputs yield identical stored results (AC-18, AC-25, AC-28). Outputs are labelled **ANALYTICAL_RECOMMENDATION** or **ANALYTICAL_REPLACEMENT_ASSESSMENT**. They are **not** official RR selections, not auction decisions, and carry **no recruitment probabilities** (TRD §8.3, §9.7)."""

assert old_sec1 in content, "Could not find old_sec1 in RANKING_SPEC.md"
content = content.replace(old_sec1, new_sec1, 1)

# 3. Add Section 9 at the end of the file for Incumbent Replacement Evaluation
new_sec9 = """

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
"""

content = content + new_sec9

with open('docs/RANKING_SPEC.md', 'w', encoding='utf-8', newline='\n') as f:
    f.write(content)

print("docs/RANKING_SPEC.md successfully updated!")
