import re

with open('docs/DATA_DICTIONARY.md', 'r', encoding='utf-8') as f:
    content = f.read().replace('\r\n', '\n')

# 1. Update title and header
old_header = """**Project**: RR Squad Intelligence & Team Composition Platform
**Document Version**: 2.1.1-TARGETED-REMEDIATION · **Status**: `[STATUS: PLANNED - GREENFIELD BASELINE]`

> **v2.1.1 revision**: economy-rate formula corrected to the format-aware"""

new_header = """**Project**: RR Squad Intelligence & Team Composition Platform
**Document Version**: 2.2.0-PVRE-DUAL-MODE · **Status**: `[STATUS: PLANNED - GREENFIELD BASELINE]`

> **v2.2.0 revision**: added PVRE Recent-Form Metrics (Module A2), PVRE Replaceability Assessment
> Signals (Module A3), and SICE 16 Role-Aware Incumbent-vs-Candidate Comparison Dimensions (§9, §10, §11).
> Prohibits uncalibrated replacement probabilities and arbitrary single-number composite scores.
> Maintains format-aware economy, DDL 33-entity schema alignment, and strict evidence-backed provenance.
>
> **v2.1.1 revision**: economy-rate formula corrected to the format-aware"""

assert old_header in content, "Could not find old_header"
content = content.replace(old_header, new_header, 1)

# 2. Add sections 9, 10, 11 at the end of the file
new_sections = """

---

## 9. PVRE Recent-Form Metrics (Module A2 — Global Performance)

PVRE Module A2 assesses an incumbent player's recent global performance outside and within Rajasthan Royals over a configurable window of **two to three years** relative to an explicit `evaluation_date`.

| # | Metric | Class | Definition / Formula | Source fields | Exclusions | Null / sample rules |
|---|---|---|---|---|---|---|
| R01 | Window Batting Strike Rate | DERIVED | Format-aware weighted strike rate over research window $W \in [2, 3]$ years: $\\frac{100 \\times \\sum_{i \\in W} w(t_i) \\times \\text{runs}_i}{\\sum_{i \\in W} w(t_i) \\times \\text{balls}_i}$ | `batting_innings`, `matches.match_date` | Super Over; matches outside window | Denominator 0 → NULL; `sample=balls_faced` displayed |
| R02 | Window Bowling Economy Rate | DERIVED | Format-aware weighted economy over window $W$: $\\frac{\\sum_{i \\in W} w(t_i) \\times \\text{balls\\_per\\_over}(c_i) \\times \\text{runs\\_conceded}_i}{\\sum_{i \\in W} w(t_i) \\times \\text{legal\\_balls}_i}$ | `bowling_spells`, `competitions.balls_per_over` | Super Over; matches outside window | Legal balls 0 → NULL; The Hundred uses 5 balls/over |
| R03 | Window Boundary % | DERIVED | $100 \\times \\frac{\\sum_{i \\in W} w(t_i) \\times (4\\times\\text{fours}_i + 6\\times\\text{sixes}_i)}{\\sum_{i \\in W} w(t_i) \\times \\text{runs}_i}$ | `batting_innings` | Outside window | Runs 0 → NULL |
| R04 | Window Dot Ball % | DERIVED | $100 \\times \\frac{\\sum_{i \\in W} w(t_i) \\times \\text{dot\\_balls}_i}{\\sum_{i \\in W} w(t_i) \\times \\text{balls}_i}$ | `batting_innings` / `bowling_spells` | Outside window | Balls 0 → NULL |
| R05 | Participation Consistency | DERIVED | Ratio of matches played to team scheduled matches per competition season in window $W$; identifies calendar gaps | `matches`, `teams`, `source_records` | Unrecorded fixtures | Expressed as seasonal breakdown; gaps flagged `GAP_SUSPECTED`, `GAP_VERIFIED_INJURY`, `GAP_NOT_SELECTED` |
| R06 | Window Sample Indicators | OBSERVED | Vector of sample counts: `(matches, innings, balls_faced, overs_bowled)` per competition and format in window $W$ | `matches`, `batting_innings`, `bowling_spells` | Outside window | Displayed alongside all window metrics; never hidden |

> **Contextual Normalisation Rule**: Raw cross-league statistics must never be aggregated without explicit league-context metadata (`competition_id`, `tier`, `format_tag`). Performance in one tournament (e.g. domestic T20) is not directly interchangeable with international or IPL statistics without documented baseline weighting.

---

## 10. PVRE Replacement Assessment Signals (Module A3)

PVRE Module A3 produces a structured analytical assessment of an incumbent Rajasthan Royals player. The assessment synthesises RR historical contribution, recent 2–3 year global form, age trajectory, availability evidence, and data completeness.

### 10.1 Assessment States
- `RETAIN_SIGNAL`: The incumbent demonstrates sustained elite role-specific performance across both historical RR appearances and recent global competitions with high sample adequacy and consistent availability.
- `MONITOR_SIGNAL`: The incumbent exhibits moderate role performance or minor form fluctuation in the recent window, but maintains historical equity or limited replacement urgency. Requires ongoing tracking through domestic/franchise seasons.
- `POTENTIALLY_REPLACEABLE`: The incumbent displays persistent form degradation over 2–3 years, role stagnation, availability constraints, or advancing age where verified uncapped candidates offer superior role fit, efficiency, or development trajectory.
- `INSUFFICIENT_EVIDENCE`: Evidentiary coverage within the 2–3 year evaluation window falls below minimum sample thresholds (<20 batting balls, <30 overs bowled, or unverified recent leagues). Prevents premature classification.
- `REVIEW_REQUIRED`: Unresolved data conflicts, contradictory contract/appearance records, contested identity records, or missing mandatory provenance. Requires human analyst audit.

### 10.2 Architectural Guardrails
1. **Analytical Signals, Not Decisions**: PVRE signals are advisory inputs to the Senior Management and SICE engine. PVRE does not make auction, release, retention, or signing decisions.
2. **Prohibition of Replacement Probabilities**: PVRE must NOT generate scalar replacement probabilities (e.g. "78.4% replaceability score") or arbitrary composite single-index scores. Assessments must be multi-dimensional evidence vectors.
3. **No Arbitrary Thresholds**: Classification rules must be parameterized, reproducible, and versioned in `ranking_runs` configuration.

---

## 11. SICE Role-Aware Incumbent-vs-Candidate Comparison Dimensions

When SICE consumes a PVRE Mode A incumbent profile alongside top-ranked verified uncapped candidates (from Mode B / SICE ranking pool), it evaluates the pair across **16 Role-Aware Comparison Dimensions**.

| # | Dimension | Role Applicability | Incumbent Metric Basis | Candidate Metric Basis | Evidentiary Basis |
|---|---|---|---|---|---|
| D01 | Base Scoring Rate | Top-order, Finisher, All-rounder | Window Batting Strike Rate (R01, B06) | SMAT/Domestic T20 Strike Rate (B06) | CricSheet ball-level legal balls |
| D02 | Dismissal Resistance | Top-order, Anchor | Window Batting Average (B05) | SMAT/Domestic Batting Average (B05) | Dismissal counts, innings |
| D03 | Boundary Generation | Opener, Middle-order, Finisher | Window Boundary % (R03, B08) | Domestic T20 Boundary % (B08) | Fours and sixes off the bat |
| D04 | Dot Ball Suppression | Top-order, Finisher | Window Batting Dot % (R04, B09) | Domestic T20 Batting Dot % (B09) | Dot balls faced / legal balls |
| D05 | Powerplay Batting Impact | Opener, Top-order | Phase Powerplay Strike Rate (B12) | Domestic T20 Powerplay SR (B12) | Overs 1–6 recorded deliveries |
| D06 | Middle-Overs Rotation & Acceleration | Anchor, Middle-order | Middle Phase SR & Boundary % (B12) | Domestic T20 Middle Phase SR (B12) | Overs 7–15 recorded deliveries |
| D07 | Death-Overs Boundary Execution | Finisher, Lower-order | Death Phase Strike Rate (B12) | Domestic T20 Death Phase SR (B12) | Overs 16–20 recorded deliveries |
| D08 | Run Suppression (Economy) | All Bowlers, All-rounders | Window Bowling Economy Rate (R02, W06) | Domestic T20 Economy Rate (W06) | Legal balls bowled / runs conceded |
| D09 | Wicket-Taking Efficiency | Pace, Spin, Death Bowler | Bowling Strike Rate (W07, W05) | Domestic T20 Bowling SR (W07) | Wickets taken / legal balls |
| D10 | Bowling Dot Ball Pressure | Powerplay Bowler, Death Bowler | Bowling Dot % (W08) | Domestic T20 Bowling Dot % (W08) | Dot balls bowled / legal balls |
| D11 | Phase-Specific Bowling Control | Powerplay / Death Specialist | Phase Economy & Wickets (W09) | Phase Economy & Wickets (W09) | Phase-partitioned bowling spells |
| D12 | Matchup Resilience | All Roles | Pace vs Spin Splits (B14, B15, W10) | Pace vs Spin Splits (B14, B15, W10) | Handedness and style deliveries |
| D13 | High-Leverage Execution | All Roles | High-Leverage Metric (M06) | High-Leverage Metric (M06) | Measurable game state threshold |
| D14 | Fielding & Keeping Contribution | Fielders, Wicketkeepers | Fielding Events & Coverage (F01–F09) | Fielding Events & Coverage (F01–F09) | Recorded opportunity events only |
| D15 | Age & Trajectory Delta | All Roles | Incumbent Age as of `evaluation_date` | Candidate Age as of `evaluation_date` | DOB verification via PIRE / TMVE |
| D16 | Sample Adequacy & Evidentiary Tier | All Roles | Window Sample Indicators (R06) | Career Sample Indicators (R06) | Confidence interval, sample tier |

> **Comparative Output Contract**: SICE outputs a multidimensional comparison matrix displaying absolute metrics, sample sizes, and relative deltas for each dimension. SICE **never collapses** the comparison into an arbitrary single score.
"""

content = content + new_sections

with open('docs/DATA_DICTIONARY.md', 'w', encoding='utf-8', newline='\n') as f:
    f.write(content)

print("docs/DATA_DICTIONARY.md successfully updated!")
