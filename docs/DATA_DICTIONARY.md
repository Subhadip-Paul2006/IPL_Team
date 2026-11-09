# Metric Data Dictionary

**Project**: RR Squad Intelligence & Team Composition Platform
**Document Version**: 2.1.1-TARGETED-REMEDIATION · **Status**: `[STATUS: PLANNED - GREENFIELD BASELINE]`

> **v2.1.1 revision**: economy-rate formula corrected to the format-aware
> `balls_per_over × runs / legal_balls` convention (W06); balls-faced definition
> corrected to the authoritative scorecard convention (no-balls count as balls faced;
> wides do not — B04 and the ingestion formula); DNB distinguished from zero-ball-batted
> appearances (B02/B05; DDL `chk_dnb_zero`); a **single consistent three-group phase
> model** with per-format boundaries, DLS scaling and Super Over isolation (replacing
> the 4-value delivery enum vs 3-group summary mismatch); The Hundred added as a
> first-class `HUNDRED` format with independently defined ball/over/economy/phase
> conventions (it never inherits six-ball-over calculations); B16 partnership
> contribution and M06/M07 leverage & composite metrics given reproducible definitions
> or explicit deferral.

> CPPAE (TRD §6) computes **only** metrics defined here. Every metric lists: definition ·
> formula · numerator · denominator · required source fields · exclusions · format restrictions ·
> match-phase rules · null handling · minimum sample · data-quality validation · class
> (**OBSERVED** = copied from source records, **DERIVED** = arithmetic over observed records,
> **MODEL_INFERRED** = model output, **NOT_COMPUTABLE** = no source records the event,
> **DEFERRED** = computable only under documented data conditions that no current source
> satisfies).
>
> Global conventions:
> - **Delivery events vs legal balls vs balls faced**: a *delivery event* is any ball of the
>   over sequence (includes wides and no-balls). **Legal balls** exclude both. **Balls faced**
>   (batting) = legal balls **plus no-balls** (a no-ball is delivered and faced); **wide
>   events are never balls faced** (the batter does not face a wide). Authoritative basis:
>   ICC Laws of Cricket — Law 23 (the no-ball is a delivery; the striker is credited a ball
>   faced) and Law 24.1 (the wide is not a delivery faced); scorecard convention "runs off
>   balls" counts no-balls in balls faced and excludes wides.
> - **Single ingestion formula (shared by DDL and this dictionary — the source of
>   truth)**: `batting_innings.balls_faced = COUNT(delivery events in the batter's facing
>   spell WHERE NOT is_wide)` (no-balls included, wides excluded). Bowling:
>   `legal_balls_bowled = COUNT(events WHERE NOT is_wide AND NOT is_noball)`;
>   `illegal_events_wides` / `illegal_events_noballs` counted separately.
> - All ratios return `NULL` (never 0.0) when the denominator is 0 or a required source field
>   is absent. A sample of 0 is displayed with `sample=0`, never as an average.
> - **Formats** — `format_tag ∈ {T20, ODI, LIST_A, FIRST_CLASS, HUNDRED}` is mandatory on
>   every computed value; cross-format comparisons are prohibited without an explicit,
>   documented normalisation factor (which no current source supplies → comparisons stay
>   within-format). **The Hundred (`HUNDRED`) is a distinct 5-ball-over, 100-ball-innings
>   format** (`competitions.balls_per_over = 5`, 20 overs): it **never** inherits the
>   six-ball-over economy, over-notation, or phase calculations — see §7 Format-Specific
>   Rules.
> - **Super Over innings** (`innings.is_super_over = TRUE`) are isolated to their own
>   partition of the over sequence (source `innings_number 3/4` or `"super_over": true`) and
>   excluded from **all** career aggregates (OBSERVED segregation, never imputation).
> - **DLS-affected innings**: phase boundaries and the run-rate denominator scale to
>   `innings.target_overs_balls` (integer balls of the revised target; DLS method version
>   recorded on the match), never the scheduled allocation. A DLS-truncated innings with no
>   revision is `PHASE_DATA_INSUFFICIENT` (below), not silently rescaled.
> - **Sample size is always returned alongside a metric** (`samples` block, TRD §6.3); a
>   small sample must never be compared with a large one without the difference displayed.

---

## 1. Batting Metrics

| # | Metric | Class | Definition / Formula | Numerator | Denominator | Source fields | Exclusions | Null / sample rules |
|---|---|---|---|---|---|---|---|---|
| B01 | Matches (batting) | OBSERVED | Distinct matches with ≥1 legal delivery faced | `COUNT(DISTINCT match_id)` | — | `batting_innings` joined to `matches` | Super Over innings | `sample=0 → NULL` |
| B02 | Innings (batting) | OBSERVED | Non-DNB innings in scope | `COUNT(innings WHERE did_not_bat=FALSE)` | — | `batting_innings.did_not_bat` | Super Over | DNB counted in the `dnb` counter only; DNB rows carry `balls_faced = 0` and `did_not_bat = TRUE` (explicit, not implied). **A player who batted without facing a recorded ball (walkover / timed-out dismissal, `balls_faced = 0` with `did_not_bat = FALSE`) is a batted appearance with 0 balls — a distinct, legitimate state; never treated as DNB and never fabricated.** |
| B03 | Runs | OBSERVED | Total runs off the bat | `SUM(runs_scored)` | — | `batting_innings.runs_scored` | Super Over; all extras | — |
| B04 | Balls faced | OBSERVED | Balls faced under the authoritative scorecard convention (legal balls **+ no-balls**; **wides excluded**) | `SUM(balls_faced)` | — | `batting_innings.balls_faced` (ingestion formula above) | Wide events are delivery events, never balls faced; no-balls included | DNB → 0 recorded, not null; zero-ball batted appearance → 0 (distinct from DNB) |
| B05 | Batting average | DERIVED | `runs / (innings − not_outs)` | B03 | batted (non-DNB) innings − not-out innings | B01–B04 | Super Over | 0 dismissals → `NULL` (display `*` or "not out"), never 0.00; **zero-ball batted appearances count in the innings numerator and honour `is_not_out`** (a walkover-batted player still has an innings) |
| B06 | Strike rate | DERIVED | `100 × runs / balls` | B03 | B04 | — | — | B04=0 → NULL; `sample=balls` always shown |
| B07 | Boundaries | OBSERVED | `fours` + `sixes` | `SUM(fours), SUM(sixes)` | — | `batting_innings.fours/.sixes` | — | — |
| B08 | Boundary % | DERIVED | `100 × (4×fours + 6×sixes) / runs` | B07 weighted | B03 | — | 0 runs → NULL | Sample visibility required |
| B09 | Dot-ball % | DERIVED | `100 × dot_balls / balls` | `SUM(dot_balls_faced)` | B04 | `batting_innings.dot_balls_faced` | — | B04=0 → NULL; constraint `dot ≤ balls` enforced in DDL |
| B10 | Batting position | OBSERVED | `batting_position` per innings | — | — | `batting_innings.batting_position` | DNB has no position | Position-specific splits use only innings where `batting_position = p` |
| B11 | Position-specific performance | DERIVED | B05/B06/B08/B09 at a fixed `batting_position` | per-position subset | per-position subset | B10 filter | Super Over | Per-position sample count shown; <20 balls → flagged `INSUFFICIENT_SAMPLE` |
| B12 | Phase splits (powerplay/middle/death) | OBSERVED | `runs_powerplay / balls_powerplay` etc. per innings row, grouped by the **single three-group phase model** (§4; boundaries per format, DLS scaling to `target_overs_balls`, Super Over isolated) | `runs_{phase}` | `balls_{phase}` | `batting_innings` phase columns | DLS: phase aggregates over recorded balls only, run-rate denominator = `target_overs_balls` (§4.2); no imputation | 0 balls in phase → NULL for that phase |
| B13 | Batter vs bowler | DERIVED | Shared-ball subset of B03–B09 | per-pair balls/runs | per-pair balls | `deliveries(batter_id, bowler_id)` join | illegal-only balls excluded from legal-ball metrics | `sample=balls<24 → INSUFFICIENT_SAMPLE` flag |
| B14 | Pace vs spin | DERIVED | B13 split by `players.bowling_style` class (pace/fast-medium vs all spin) | per-class | per-class | `players.bowling_style` | Delivery `variation_type` **never** used for this split | Class coverage <24 balls → flag |
| B15 | Bowling-style matchup | DERIVED | B13 per style group (RAF/LAF/OS/SLA/LBG/LAC) | per style | per style | `players.bowling_style` | as B14 | per-style sample shown |
| B16 | Partnership contribution | DERIVED | **Reproducible definition**: for an innings and a batter B who is at the crease, the **partnership run-total with a named partner P** = the runs scored off the bat (B03 subset) during the contiguous delivery window in which both B and P are the two batsmen at the crease (from the earlier of their first facing ball / P's appearance to the wicket or dismissal of either, recorded from `deliveries` striker/striker-changed events only). No delivery attribution is inferred; the window is bounded by **recorded** wicket and striker-change events. Sample = recorded partnership balls. | Recorded partnership runs | Recorded partnership balls | `deliveries` striker events within the innings (recorded only) | Super Over; no inference of unrecorded events | **No partner = no metric; NULL when the partner is unknown/absent in the source; never imputed** |
| B17 | Win/loss performance | DERIVED | B05/B06 split by `matches.outcome`/`winner_id` (team won/lost/other) | per-outcome subset | per-outcome subset | `matches.winner_id, outcome_type` | Ties treated as `other` | 0 matches in an outcome → NULL |
| **FALSE_SHOT** | — | **NOT_COMPUTABLE** | No source dataset records false shots; **the metric is never computed or estimated** | — | — | — | — | Always `NOT_COMPUTABLE_FROM_AVAILABLE_SOURCES` |

---

## 2. Bowling Metrics

| # | Metric | Class | Definition / Formula | Numerator | Denominator | Source fields | Exclusions | Null / sample rules |
|---|---|---|---|---|---|---|---|---|
| W01 | Overs (display) | DERIVED | `floor(legal_balls/balls_per_over) + "." + (legal_balls % balls_per_over)` — display only; **integer `legal_balls_bowled` is the unit of record**; `balls_per_over` taken from the format (6 for T20/ODI/List A, **5 for The Hundred**) | — | — | `bowling_spells.legal_balls_bowled`, `competitions.balls_per_over` | — | 0 balls (DNBowl) → `overs=0.0 display, sample=0`, economy NULL; **The Hundred display uses 5-ball over notation (e.g. 100 balls = 20.0), never 6-ball** |
| W02 | Legal balls | OBSERVED | `legal_balls_bowled` | — | — | `bowling_spells.legal_balls_bowled` | wides/noballs are separate counters | — |
| W03 | Runs conceded | OBSERVED | `runs_conceded` | — | — | `bowling_spells.runs_conceded` | **Excludes byes, leg-byes, penalty runs** (DDL: `runs_conceded = Σ(batter + wides + noballs)` convention, no byes/penalties) | — |
| W04 | Wickets | OBSERVED | `wickets_taken` | — | — | `bowling_spells.wickets_taken` | Substitute bowler changes tracked via spell_order | — |
| W05 | Bowling average | DERIVED | `runs / wickets` | W03 | W04 | — | — | 0 wickets → NULL, never 0.00 |
| W06 | Economy rate | DERIVED | Runs conceded **per over**, in the format's over-length: `economy = (balls_per_over × runs) / legal_balls` | W03 × balls_per_over | W02 | `bowling_spells.runs_conceded`, `competitions.balls_per_over` | — | 0 legal balls → NULL; **The Hundred uses `balls_per_over = 5` (never 6)** |
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

## 4. Phase Model (single, consistent) — revised

The four-value `deliveries.match_phase` enum and the three-group batting/bowling summary
columns were inconsistent. **The single authoritative model is three groups** —
`Powerplay`, `Middle`, `Death` — and the delivery enum is reduced to match. Over-boundaries
are **format-specific** and are the source of truth; group membership of a delivery is
determined by its over-number within the format's phase definition, never by a hard-coded
T20 boundary.

### 4.1 Group definitions and per-format boundaries
| Format | `balls_per_over` | Powerplay (balls) | Middle (balls) | Death (balls) |
|---|---|---|---|---|
| **T20** (IPL, etc.) | 6 | overs 1–6 (balls 1–36) | overs 7–15 (balls 37–90) | overs 16–20 (balls 91–120) |
| **ODI / List A** | 6 | overs 1–10 (60) | overs 11–40 (240) | overs 41–50 (60) |
| **First-class** | 6 | not applicable | not applicable | not applicable (`NULL`, phase not meaningful) |
| **The Hundred** | **5** | balls 1–25 (5 overs) | balls 26–90 (13 overs) | balls 91–100 (2 overs = the final 10 balls) |

> **The Hundred must not inherit T20 boundaries.** Its death phase is the final **10 balls**
> (two 5-ball overs), not the final five overs. This is documented, not computed from a
> T20 template.

### 4.2 Shortened innings and DLS
- When an innings is shortened (all-out early, DLS), the phase **group** of each recorded
  ball is still fixed by the format boundary table (a ball in over 3 is Powerplay in T20
  regardless of the innings being truncated). Phase *aggregates* for the truncated innings
  reflect only the recorded balls in each group.
- For a DLS-truncated innings the run-rate denominator uses `innings.target_overs_balls`
  (revised target). Phase **aggregates** are reported over the balls actually bowled; the
  **residual un-bowled phase balls are not imputed** (a DLS match with no balls bowled in
  the death phase has `balls_death = 0` → death-phase rate `NULL`, not 0.00).
- A DLS match with no revised target recorded → the affected run-rate / phase metric is
  `PHASE_DATA_INSUFFICIENT` (explicit NULL + flag), never a rescaled estimate.

### 4.3 Super Over isolation
- `innings.is_super_over = TRUE` deliveries are **excluded** from all three phase groups and
  all career aggregates. They are recorded (for reconciliation) but never mixed into
  Powerplay/Middle/Death.

### 4.4 Missing source data
- If the source lacks delivery-level phase data (no `match_phase`/over-number on a ball),
  the affected phase metric is `NOT_COMPUTABLE_FROM_AVAILABLE_SOURCES` (never estimated).
  `deliveries.match_phase` may be `NULL` for List A / first-class rows (phase not
  meaningful there); the delivery enum is therefore the **three-group** set with `NULL`
  permitted, replacing the old four-value enum.

---

## 5. Format-Specific Rules — The Hundred (Priority B)

The local dataset `datasets/hnd_male_json/` (201 match files, CricSheet JSON v1.3.0,
`info.balls_per_over = 5`) is **The Hundred**, a distinct **5-ball-over, 100-ball-innings**
format. It is modelled as a first-class `HUNDRED` `format_tag` with independently defined
conventions; it **never** inherits the six-ball-over calculations.

| Convention | Six-ball-over formats (T20/ODI/List A) | **The Hundred (`HUNDRED`)** |
|---|---|---|
| Balls per over | 6 | **5** (`competitions.balls_per_over = 5`) |
| Innings length | 120 balls (T20) | **100 balls** (20 five-ball overs) |
| Over display | `floor(balls/6).(balls%6)` | `floor(balls/5).(balls%5)` (100 balls = `20.0`) |
| Economy (W06) | `6 × runs / legal_balls` | **`5 × runs / legal_balls`** |
| Ball notation for balls faced (B04) | legal + no-balls, wides excluded | **same convention** (no-balls count, wides don't) |
| Phase boundaries | §4.1 T20/ODI rows | **§4.1 The Hundred row (death = final 10 balls)** |
| `deliveries.match_phase` | 3-group by T20/ODI | **3-group by the Hundred row** |
| Super Over | isolated (§4.3) | isolated (§4.3) |

**Storage of truth**: all ball counts are integers; the over number is derived as
`floor(balls / balls_per_over)` — never a decimal. `competitions.balls_per_over` is the
governing value per format, so a The Hundred competition row carries `5` and its overs,
economy, notation and phases all follow from that single field. This prevents the format
from silently inheriting six-ball-over behaviour.

> **Deferral (documented)**: The Hundred's powerplay is the **first 25 balls** (per the
> source `powerplays` field `from 0.1 to 4.5`). Phase 5 (CPPAE) computes The Hundred phase
> splits only after `balls_per_over = 5` handling is implemented and validated on the local
> 201-file archive; until then The Hundred is **ingested and preserved as raw data only**
> (Priority B option 2), and no The-Hundred-derived rate is published. This is a deliberate,
> versioned deferral, not an omission.

---

## 6. Match Contribution

| # | Metric | Class | Definition | Rules |
|---|---|---|---|---|
| M01 | Player-of-the-Match awards | OBSERVED | `COUNT(player_awards WHERE award_type='Player of the Match')` per season/career | **Input signal only, never a measure of total impact**; reported alongside contribution metrics, never as a substitute |
| M02 | Batting contribution | DERIVED | Team-run share: `player runs / team innings total runs` per match, aggregated | sample per match shown |
| M03 | Bowling contribution | DERIVED | Team-wicket share and run-suppression share (W03 share of team concession excluding extras-as-conceded) | per match |
| M04 | Match situation | OBSERVED | Innings role context: chase/defend, first/second innings, `match_phase` at player's spell/innings | from `matches` + `innings` |
| M05 | Performance in wins/losses | DERIVED | B/W metrics split by team outcome (as B17, for bowling) | 0 matches in an outcome → NULL |
| M06 | Measurable high-leverage contribution | DERIVED | **Reproducible definition**: a delivery is *high-leverage* when, at the moment it is bowled, the match state crosses a documented threshold computed from recorded state data only — `required_run_rate > RR_threshold(format)` **and/or** `wickets_in_hand ≤ K(format)` (thresholds are versioned per-format constants in the ranking configuration, not estimates). The contribution = the sum of the runs/wickets the player was directly involved in (batter: runs on those balls; bowler: wickets on those balls) over that high-leverage set. Inputs: per-over recorded target/overs/wickets-in-hand reconstructed from the `deliveries` sequence (recorded only). **Leverage = measurable match state, NEVER inferred mental state** (AI_INSTRUCTIONS R8). **If the recorded sequence cannot reconstruct the required run-rate or wickets-in-hand for a ball, that ball is excluded and the metric is reported with its coverage; it is never imputed.** |
| M07 | Contribution to team outcome | DERIVED | **Reproducible definition**: additive composite `M07(match) = M02(match) + M03(match)` with the match result tag (`matches.outcome_type`, `winner_id`) attached. **No weights are applied or hardcoded** — CPPAE exposes the M02 and M03 components separately and M07 is their explicit sum; SICE may compose across matches only by documented, versioned combination (additive by default). A zero-component (e.g. no wickets) is a recorded 0, not a missing value. |

---

## 7. Cross-Cutting Validation Rules

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

## 8. Not-Computable / Deferred Metrics (explicit, never estimated)

| Metric | Class | Reason |
|---|---|---|
| False-shot frequency | **NOT_COMPUTABLE** | No source records false shots |
| Inferred dropped catches / missed chances | **NOT_COMPUTABLE** | Only explicitly recorded events exist |
| Direct pitch moisture / soil sensors | **NOT_COMPUTABLE** | No sensor data in any register source; weather is context only |
| Delivery line/length without tracking | **NOT_COMPUTABLE** | Tracking coverage sparse; untracked balls excluded, coverage reported |
| Mental-state / composure measures | **NOT_COMPUTABLE** | Prohibited by domain rules; high-leverage = measurable state (M06) |
| The-Hundred derived rate metrics | **DEFERRED** | `HUNDRED` phase/economy splits not yet computed (Priority B option 2): ingested & preserved as raw; no derived The-Hundred rate published until `balls_per_over = 5` handling is validated on the local archive (see §5 deferral) |
