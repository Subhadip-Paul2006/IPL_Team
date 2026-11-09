# Metric Data Dictionary

**Project**: RR Squad Intelligence & Team Composition Platform
**Document Version**: 2.1.0-REMEDIATED · **Status**: `[STATUS: PLANNED - GREENFIELD BASELINE]`

> CPPAE (TRD §6) computes **only** metrics defined here. Every metric lists: definition ·
> formula · numerator · denominator · required source fields · exclusions · format restrictions ·
> match-phase rules · null handling · minimum sample · data-quality validation · class
> (**OBSERVED** = copied from source records, **DERIVED** = arithmetic over observed records,
> **MODEL_INFERRED** = model output, **NOT_COMPUTABLE** = no source records the event).
>
> Global conventions:
> - `legal balls` = balls on which a bat may score (excludes wides/no-balls as ball events,
>   which still count as *delivery events*).
> - All ratios return `NULL` (never 0.0) when the denominator is 0 or a required source field
>   is absent. A sample of 0 is displayed with `sample=0`, never as an average.
> - `format_tag ∈ {T20, ODI, FIRST_CLASS, LIST_A}` is mandatory on every computed value;
>   cross-format comparisons are prohibited without an explicit, documented normalisation
>   factor (which no current source supplies → comparisons stay within-format).
> - Super Over innings (`innings.is_super_over = TRUE`) are excluded from all career metrics
>   (OBSERVED segregation, not imputation).
> - DLS-affected innings: phase boundaries scale to `innings.target_overs`; run-rate metrics use
>   the revised target, never the scheduled 20-over target.
> - **Sample size is always returned alongside a metric** (`samples` block, TRD §6.3); a
>   small sample must never be compared with a large one without the difference displayed.

---

## 1. Batting Metrics

| # | Metric | Class | Definition / Formula | Numerator | Denominator | Source fields | Exclusions | Null / sample rules |
|---|---|---|---|---|---|---|---|---|
| B01 | Matches (batting) | OBSERVED | Distinct matches with ≥1 legal delivery faced | `COUNT(DISTINCT match_id)` | — | `batting_innings` joined to `matches` | Super Over innings | `sample=0 → NULL` |
| B02 | Innings (batting) | OBSERVED | Non-DNB innings in scope | `COUNT(innings WHERE did_not_bat=FALSE)` | — | `batting_innings.did_not_bat` | Super Over | DNB counted in `dnb` counter only |
| B03 | Runs | OBSERVED | Total runs off the bat | `SUM(runs_scored)` | — | `batting_innings.runs_scored` | Super Over; all extras | — |
| B04 | Balls faced | OBSERVED | Legal balls faced | `SUM(balls_faced)` | — | `batting_innings.balls_faced` | Wide/no-ball events (excluded from legal balls) | DNB → 0 recorded, not null |
| B05 | Batting average | DERIVED | `runs / (innings − not_outs)` | B03 | non-not-out innings | B01–B03 | — | 0 dismissals → `NULL` (display `*` or "not out"), never 0.00 |
| B06 | Strike rate | DERIVED | `100 × runs / balls` | B03 | B04 | — | — | B04=0 → NULL; `sample=balls` always shown |
| B07 | Boundaries | OBSERVED | `fours` + `sixes` | `SUM(fours), SUM(sixes)` | — | `batting_innings.fours/.sixes` | — | — |
| B08 | Boundary % | DERIVED | `100 × (4×fours + 6×sixes) / runs` | B07 weighted | B03 | — | 0 runs → NULL | Sample visibility required |
| B09 | Dot-ball % | DERIVED | `100 × dot_balls / balls` | `SUM(dot_balls_faced)` | B04 | `batting_innings.dot_balls_faced` | — | B04=0 → NULL; constraint `dot ≤ balls` enforced in DDL |
| B10 | Batting position | OBSERVED | `batting_position` per innings | — | — | `batting_innings.batting_position` | DNB has no position | Position-specific splits use only innings where `batting_position = p` |
| B11 | Position-specific performance | DERIVED | B05/B06/B08/B09 at a fixed `batting_position` | per-position subset | per-position subset | B10 filter | Super Over | Per-position sample count shown; <20 balls → flagged `INSUFFICIENT_SAMPLE` |
| B12 | Phase splits (powerplay/middle/death) | OBSERVED | `runs_powerplay / balls_powerplay` etc. per innings row | `runs_{phase}` | `balls_{phase}` | `batting_innings` phase columns | DLS: phases scaled to `target_overs` | 0 balls in phase → NULL for that phase |
| B13 | Batter vs bowler | DERIVED | Shared-ball subset of B03–B09 | per-pair balls/runs | per-pair balls | `deliveries(batter_id, bowler_id)` join | illegal-only balls excluded from legal-ball metrics | `sample=balls<24 → INSUFFICIENT_SAMPLE` flag |
| B14 | Pace vs spin | DERIVED | B13 split by `players.bowling_style` class (pace/fast-medium vs all spin) | per-class | per-class | `players.bowling_style` | Delivery `variation_type` **never** used for this split | Class coverage <24 balls → flag |
| B15 | Bowling-style matchup | DERIVED | B13 per style group (RAF/LAF/OS/SLA/LBG/LAC) | per style | per style | `players.bowling_style` | as B14 | per-style sample shown |
| B16 | Partnership contribution | DERIVED | Runs from an innings shared with a named partner: partner's contribution = runs attributed to the partnership (delivery-attributed to batter for B03 subset between partner's wicket/striking window and end) | partnership runs | partnership balls | `deliveries` sequence within an innings between striker events | No partnership metric = no inference; recorded deliveries only | NULL when partner unknown in source |
| B17 | Win/loss performance | DERIVED | B05/B06 split by `matches.outcome`/`winner_id` (team won/lost/other) | per-outcome subset | per-outcome subset | `matches.winner_id, outcome_type` | Ties treated as `other` | 0 matches in an outcome → NULL |
| **FALSE_SHOT** | — | **NOT_COMPUTABLE** | No source dataset records false shots; **the metric is never computed or estimated** | — | — | — | — | Always `NOT_COMPUTABLE_FROM_AVAILABLE_SOURCES` |

---

## 2. Bowling Metrics

| # | Metric | Class | Definition / Formula | Numerator | Denominator | Source fields | Exclusions | Null / sample rules |
|---|---|---|---|---|---|---|---|---|
| W01 | Overs (display) | DERIVED | `floor(legal_balls/6) + "." + (legal_balls % 6)` — display only; **integer `legal_balls_bowled` is the unit of record** | — | — | `bowling_spells.legal_balls_bowled` | — | 0 balls (DNBowl) → `overs=0.0 display, sample=0`, economy NULL |
| W02 | Legal balls | OBSERVED | `legal_balls_bowled` | — | — | `bowling_spells.legal_balls_bowled` | wides/noballs are separate counters | — |
| W03 | Runs conceded | OBSERVED | `runs_conceded` | — | — | `bowling_spells.runs_conceded` | **Excludes byes, leg-byes, penalty runs** (DDL: `runs_conceded = Σ(batter + wides + noballs)` convention, no byes/penalties) | — |
| W04 | Wickets | OBSERVED | `wickets_taken` | — | — | `bowling_spells.wickets_taken` | Substitute bowler changes tracked via spell_order | — |
| W05 | Bowling average | DERIVED | `runs / wickets` | W03 | W04 | — | — | 0 wickets → NULL, never 0.00 |
| W06 | Economy rate | DERIVED | `10 × runs / legal_balls` | W03 | W02 | — | — | 0 legal balls → NULL |
| W07 | Bowling strike rate | DERIVED | `legal_balls / wickets` | W02 | W04 | — | — | 0 wickets → NULL |
| W08 | Bowling dot % | DERIVED | `100 × dot_balls / legal_balls` | `dot_balls_bowled` | W02 | `bowling_spells.dot_balls_bowled` | — | DDL constraint `dot ≤ legal` |
| W09 | Phase-specific bowling | OBSERVED | `runs_{phase}, balls_{phase}, wickets_{phase}` | per phase | per phase | `bowling_spells` phase columns | DLS scaling as B12 | 0 balls in phase → NULL |
| W10 | Batter-specific matchups | DERIVED | Bowling analogue of B13 (per batter pair) | per-pair | per-pair | `deliveries(bowler_id, batter_id)` | — | sample shown; <18 balls → `SMALL_SAMPLE_WARNING` |
| W11 | Delivery speed | OBSERVED | `ball_speed_kph` where recorded | mean/min/max over recorded deliveries | — | `deliveries.ball_speed_kph` | NULL speeds **excluded** (never averaged as 0); speed coverage % reported | 0 recorded → NULL + coverage note; kph only |
| W12 | Line and length | OBSERVED | `pitch_coordinate_x/y` buckets (Yorker/Full/Good/Short/Bouncer × line) where tracked | per-bucket counts | tracked deliveries | `deliveries.pitch_coordinate_x/y` | Untracked deliveries excluded; **post-shot landing coords are a different field, never a line/length bucket** | Coverage reported per match/bowler |

---

## 3. Fielding & Wicketkeeping Metrics

| # | Metric | Class | Definition / Formula | Source fields | Exclusions | Null / sample rules |
|---|---|---|---|---|---|---|
| F01 | Catches | OBSERVED | `COUNT(fielding_events WHERE event_type='Catch' AND is_recorded_opportunity=TRUE)` | `fielding_events` | — | `sample = innings fielded (where known)` |
| F02 | Run-outs | OBSERVED | event types `Run Out Thrower` / `Run Out Catcher` counted per credited player | `fielding_events` | — | credit follows recorded event, not inference |
| F03 | Stumpings (keeper) | OBSERVED | `COUNT(event_type='Stumping')` | `fielding_events` / `wicketkeeping_events.stumpings` | — | two views must reconcile (Service D check) |
| F04 | Recorded dropped catches | OBSERVED | `event_type='Dropped Catch'` **only where explicitly recorded**; absence of a record is **not** evidence of zero drops | `fielding_events` | No imputation of missed chances; DDL `is_recorded_opportunity` flag | Datasets where drops are not recorded (most CricSheet rows) → `COVERAGE_LIMITED`, value NULL |
| F05 | Boundary saves | OBSERVED | `event_type='Boundary Save'` where explicitly recorded | `fielding_events` | Same coverage rule as F04 | NULL when not recorded |
| F06 | Missed opportunities | OBSERVED/MODEL | Recorded misses: F04/F05-type events. **Inferred** catches-from-nothing is prohibited; any inferred variant must be MODEL_INFERRED + validated | `fielding_events` | — | Default: NOT_COMPUTABLE unless records exist |
| F07 | Fielding appearances | OBSERVED | Innings where the player was a fielder (recorded in playing XI/fielders of the source) | source playing-XI + `fielding_events` | Super Over excluded | NULL when fielder roster not recorded for a match |
| F08 | Wicketkeeping appearances | OBSERVED | `wicketkeeping_events.appearances` (set from data, no default) | `wicketkeeping_events` | — | No invented appearances |
| F09 | Wicketkeeping dismissals | OBSERVED | `stumpings + catches` per keeper appearances | `wicketkeeping_events` | — | Split shown, not merged |

> **Rule**: fielding ability claims are over-claim risks when event coverage is incomplete.
> Every fielding metric therefore returns its coverage class: `FULLY_RECORDED` /
> `PARTIALLY_RECORDED` / `COVERAGE_LIMITED` (from Service D), and conclusions in SICE/CMIE
> must quote it.

---

## 4. Match Contribution

| # | Metric | Class | Definition | Rules |
|---|---|---|---|---|
| M01 | Player-of-the-Match awards | OBSERVED | `COUNT(player_awards WHERE award_type='Player of the Match')` per season/career | **Input signal only, never a measure of total impact**; reported alongside contribution metrics, never as a substitute |
| M02 | Batting contribution | DERIVED | Team-run share: `player runs / team innings total runs` per match, aggregated | sample per match shown |
| M03 | Bowling contribution | DERIVED | Team-wicket share and run-suppression share (W03 share of team concession excluding extras-as-conceded) | per match |
| M04 | Match situation | OBSERVED | Innings role context: chase/defend, first/second innings, `match_phase` at player's spell/innings | from `matches` + `innings` |
| M05 | Performance in wins/losses | DERIVED | B/W metrics split by team outcome (as B17, for bowling) | 0 matches in an outcome → NULL |
| M06 | Measurable high-leverage contribution | DERIVED | Player's delta on match state at high-leverage moments: high-leverage balls **defined by state (target deficit vs time, wickets in hand) thresholds documented per format** | **Leverage = measurable match state, NEVER inferred mental state** (AI_INSTRUCTIONS R8) |
| M07 | Contribution to team outcome | DERIVED | Composite of M02+M03 in a match, with match result tag | Weights: none hardcoded; composite shown as additive, role-aware (CPPAE exposes components; SICE composes) |

---

## 5. Cross-Cutting Validation Rules

1. **Scorecard ↔ ball-level reconciliation** (Service D gate, TRD §9.4): per innings,
   `SUM(deliveries runs_total by batting side)` = `innings.total_runs + total_extras`
   convention per source; wicket events in `deliveries` reconcile to
   `batting_innings.dismissal_kind` rows; `bowling_spells.runs_conceded` (per DDL D6
   convention) reconciles to per-bowler delivery sums. Any mismatch → match quarantined,
   never patched.
2. **Legal vs total events**: metrics named "balls" use legal balls; "delivery events"
   include wides/noballs; both counts exposed in `samples`.
3. **Format**: every metric carries `format_tag`; format mixing is a DQ failure.
4. **Minimum samples** (defaults, overridable per role): 20 legal balls (batting rates),
   24 balls vs a bowler/batter pair, 18 balls for matchup warnings, 30 overs for pace-speed
   averages; below → metric value returned **with** `INSUFFICIENT_SAMPLE` flag, not suppressed.
5. **Nulls**: all denominators-zero cases return NULL; the UI layer must render NULL as
   "no data / not computed", never 0.0 (AI_INSTRUCTIONS R1).

---

## 6. Not-Computable Metrics (explicit, never estimated)

| Metric | Reason |
|---|---|
| False-shot frequency | No source records false shots |
| Inferred dropped catches / missed chances | Only explicitly recorded events exist |
| Direct pitch moisture / soil sensors | No sensor data in any register source; weather is context only |
| Delivery line/length without tracking | Tracking coverage sparse; untracked balls excluded, coverage reported |
| Mental-state / composure measures | Prohibited by domain rules; high-leverage = measurable state (M06) |
