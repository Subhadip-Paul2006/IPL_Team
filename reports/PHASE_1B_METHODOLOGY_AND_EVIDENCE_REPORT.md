# SupeRR Selector Season 2 — Phase 1B Methodology and Evidence Report
## Contextual Delivery Pressure Analytics & Player Intelligence (2022–2026)

**Target Franchise**: Rajasthan Royals (RR)
**Competition Submission**: Unstop Round 1 Problem Statement
**Data Provenance**: Organizer Historical Dataset (IPL & T20I, 2022–2026)
**Pipeline Version**: `v1.0.0-phase1b-canonical`
**Evaluation Mode**: Local Deterministic Offline Execution

---

## 1. Executive Summary

This report establishes the comprehensive, statistically validated methodology used to solve the **SupeRR Selector Season 2** Round 1 challenge: *Identifying the Most Reliable Players Under Pressure*.

Using strictly chronological pre-delivery match state modeling, we isolate pressure from ordinary play and evaluate player performance relative to dataset-observed baselines:
- **Continuous Delivery Pressure Index (CDPI)**: A bounded continuous index $[0.0, 1.0]$ quantifying situational tension strictly prior to each ball.
- **Match Pressure Tier (MPT)**: Deterministic delivery categorization into LOW, MEDIUM, HIGH, EXTREME, and quarantined SUPER_OVER tiers.
- **Batting Pressure Performance Score (BPPS)**: Multi-component rating incorporating shrunk strike rate, average, dot-ball suppression, boundary execution, and scoring elevation.
- **Bowling Pressure Performance Score (BWPS)**: Multi-component rating incorporating shrunk economy, dot-ball percentage, boundary suppression, bowler-credited wickets, and High-Leverage Execution Score (HLES).
- **Empirical Bayes Shrinkage**: Versioned parameters ($K_{\text{bat}} = 30$, $K_{\text{bowl}} = 40$) preventing sample-size bias.
- **Match-Level Clustered Block Bootstrap**: 1,000 iterations generating 95% confidence intervals and rank stability assessments.

---

## 2. Dataset Inventory and Integrity Fingerprints

The organizer dataset comprises 200,999 ball-by-ball deliveries across 883 matches and 141 competitions from 2022 to 2026.

| File | Rows | Columns | SHA-256 Checksum | Schema Integrity |
|---|---|---|---|---|
| `ball_by_ball.csv` | 200,999 | 33 | `a3926f49d2c684dc...` | VERIFIED |
| `competition_team_player_mapping.csv` | 6,413 | 6 | `1ded4e42a9336185...` | VERIFIED |
| `competitions.csv` | 141 | 4 | `507ceb7189f972d4...` | VERIFIED |
| `matches.csv` | 883 | 22 | `bb100ab84b8b9a15...` | VERIFIED |
| `playing_eleven.csv` | 28,381 | 9 | `7517c73722a28d5d...` | VERIFIED |
| `teams.csv` | 353 | 3 | `a65e5922a9b3bf49...` | VERIFIED |

### Data Quality Findings & Semantic Invariants
1. **`extras1_runs` Categorical Enum**: Correctly interpreted as categorical codes (1=Overstep, 2=wide, 3=legbyes, 4=byes, 5=other, 6=None, 7=Penalty).
2. **Revised Overs**: Converted to integer balls (e.g. 114.0 balls = 19.0 overs).
3. **Ghost Dismissals**: Exactly 12 deliveries identified with `dismissed_player_id` set but `is_wicket=False` (retired hurt); successfully quarantined.
4. **Bowl Speed Sanitization**: 77882 deliveries with speed <= 0 or > 165 km/h sanitized to `NULL`.
5. **Super Over Isolation**: 38 Super Over deliveries isolated from ordinary career aggregates.
6. **Abandoned Fixtures**: 16 matches with 0 deliveries cleanly excluded from rate metrics.

---

## 3. PIRE Player Identity Resolution & Collision Handling

- **Total Mapped Player IDs**: 1,217 (unique players across 6,413 competition-team mappings)
- **Active Players with Match Appearances**: 967
- **Total Unique Names**: 1,210
- **Name Collisions Disambiguated**: 7 name collisions disambiguated strictly by `player_id`:
  - **Abdul Samad**: IDs ['7446', '6922']
  - **Bashir Ahmad**: IDs ['39479', '29833']
  - **Basil Hameed**: IDs ['8638', '39444']
  - **Haider Ali**: IDs ['7338', '28756']
  - **Mohammad Ali**: IDs ['3083', '20229']
  - **Muhammad Farooq**: IDs ['27373', '28978']
  - **Rashid Khan**: IDs ['4722', '20172']

All player comparisons, feature joins, and rankings operate strictly on canonical integer string `player_id` keys, preventing accidental identity merges (Rule R15 / Prohibition P6).

---

## 4. CDPI & MPT Pressure Architecture

### 4.1 Chronological Pre-Delivery State
Every delivery state is reconstructed strictly using information available **prior** to the ball being bowled:
- Legal balls remaining ($B_{\text{rem}}$)
- Wickets in hand ($W_{\text{in\_hand}} = 10 - W_{\text{lost}}$)
- Current Run Rate (CRR)
- In Chases: Runs required ($R_{\text{req}}$) and Required Run Rate (RRR)

### 4.2 Mathematical CDPI Formulations
**Innings 2 (The Chase)**:
$$\text{CDPI}_{\text{chase}} = 0.50 \cdot S_{\text{RRR}} + 0.30 \cdot S_{\text{wickets}} + 0.20 \cdot S_{\text{stage}}$$
where:
- $S_{\text{RRR}} = \text{clip}\left(\frac{\text{RRR} - 5.0}{10.0}, 0, 1\right)$
- $S_{\text{wickets}} = \frac{10 - W_{\text{in\_hand}}}{8.0}$
- $S_{\text{stage}} = 1.0 - \frac{B_{\text{rem}}}{B_{\text{max}}}$
Boosted when $W_{\text{in\_hand}} \le 2$ or $\text{RRR} \ge 14.0$.

**Innings 1 (Setting a Par Target)**:
$$\text{CDPI}_{\text{first}} = 0.20 + 0.45 \cdot S_{\text{stage}} + 0.35 \cdot S_{\text{wicket\_deficit}} + 0.20 \cdot S_{\text{rate\_deficit}}$$

### 4.3 MPT Distribution
- **LOW** ($CDPI < 0.40$): 60,885 deliveries
- **MEDIUM** ($0.40 \le CDPI < 0.60$): 76,584 deliveries
- **HIGH** ($0.60 \le CDPI < 0.80$): 42,503 deliveries
- **EXTREME** ($CDPI \ge 0.80$): 20,989 deliveries
- **SUPER_OVER** (Quarantined): 38 deliveries

---

## 5. Official Top 10 Player Rankings

### 5.1 Top 10 Batters Under Pressure (BPPS)

Eligibility Gate: $\ge 120$ dataset balls faced, $\ge 40$ High/Extreme pressure balls faced, $\ge 10$ match appearances.
Qualified Pool: **226 batters**.

| Rank | Player Name | ID | BPPS | Press BF | Raw Press SR | Shrunk SR | $\Delta$ SR | 95% CI | Top-10 Stability | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **Phil Salt** | `5553` | **77.68** | 112 | 225.0 | 207.8 | +55.7 | [51.3, 87.5] | 70.4% | VERIFIED |
| 2 | **Tom Banton** | `6273` | **76.78** | 61 | 219.7 | 194.6 | +60.2 | [58.8, 88.0] | 58.2% | VERIFIED |
| 3 | **Jos Buttler** | `813` | **74.82** | 297 | 200.0 | 194.8 | +44.6 | [65.9, 81.9] | 57.7% | VERIFIED |
| 4 | **Suryakumar Yadav** | `1699` | **74.23** | 606 | 187.3 | 185.2 | +21.0 | [62.8, 86.3] | 53.6% | VERIFIED |
| 5 | **Naman Dhir** | `37052` | **73.74** | 225 | 196.9 | 190.6 | +28.5 | [58.2, 84.9] | 47.0% | VERIFIED |
| 6 | **Prabhsimran Singh** | `7216` | **73.42** | 80 | 220.0 | 199.2 | +59.8 | [43.6, 85.1] | 40.9% | VERIFIED |
| 7 | **Rohit Sharma** | `126` | **72.80** | 143 | 186.7 | 179.2 | +42.9 | [48.0, 89.9] | 42.3% | VERIFIED |
| 8 | **Glenn Maxwell** | `838` | **68.86** | 209 | 189.9 | 184.1 | +29.0 | [54.8, 79.7] | 21.2% | VERIFIED |
| 9 | **Tim David** | `6396` | **68.77** | 629 | 185.7 | 183.8 | +8.0 | [58.3, 79.8] | 18.0% | PROVISIONAL |
| 10 | **Shashank Singh** | `2756` | **68.70** | 373 | 175.3 | 173.0 | +13.7 | [53.8, 85.5] | 23.4% | PROVISIONAL |

### 5.2 Top 10 Bowlers Under Pressure (BWPS)

Eligibility Gate: $\ge 120$ legal balls bowled, $\ge 36$ High/Extreme pressure legal balls, $\ge 10$ match appearances.
Qualified Pool: **246 bowlers**.

| Rank | Player Name | ID | BWPS | Press LB | Raw Press Econ | Shrunk Econ | $\Delta$ Econ | 95% CI | Top-10 Stability | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **Abrar Ahmed** | `5979` | **93.98** | 303 | 5.33 | 5.75 | +1.33 | [80.5, 96.7] | 94.3% | VERIFIED |
| 2 | **Sufiyan Muqeem** | `34485` | **91.48** | 220 | 5.35 | 5.90 | +0.65 | [76.0, 96.5] | 87.1% | VERIFIED |
| 3 | **Mohammad Nawaz** | `2490` | **86.00** | 248 | 6.19 | 6.58 | +0.93 | [71.5, 96.0] | 61.0% | VERIFIED |
| 4 | **Matthew Humphreys** | `22471` | **83.52** | 69 | 6.09 | 7.14 | +0.98 | [69.2, 93.9] | 46.0% | VERIFIED |
| 5 | **Sunil Narine** | `781` | **82.64** | 452 | 6.15 | 6.37 | +0.72 | [74.1, 91.2] | 39.9% | VERIFIED |
| 6 | **Haider Ali** | `28756` | **82.32** | 49 | 4.90 | 6.72 | +1.50 | [67.2, 95.4] | 36.3% | VERIFIED |
| 7 | **Mitchell Santner** | `4101` | **78.24** | 496 | 6.67 | 6.84 | +0.73 | [68.7, 86.5] | 14.0% | VERIFIED |
| 8 | **Vipraj Nigam** | `46066` | **78.10** | 60 | 6.60 | 7.54 | +3.15 | [54.6, 95.0] | 31.3% | VERIFIED |
| 9 | **Hasan Mahmud** | `6643` | **76.97** | 152 | 7.22 | 7.58 | +0.58 | [59.5, 89.4] | 14.1% | PROVISIONAL |
| 10 | **Saim Ayub** | `7690` | **75.61** | 140 | 6.43 | 6.99 | +0.70 | [61.8, 87.1] | 10.1% | PROVISIONAL |

---

## 6. Reserve Candidates

### Batting Reserves (Ranks 11–20)
| Rank | Role | Player Name | ID | BPPS | Press BF | Raw Press SR | Matches |
|---|---|---|---|---|---|---|---|
| 11 | BATTER | Sanju Samson | `2258` | 68.24 | 238 | 183.2 | 132 |
| 12 | BATTER | Marcus Stoinis | `2639` | 67.95 | 531 | 178.9 | 103 |
| 13 | BATTER | Shai Hope | `4369` | 67.42 | 130 | 179.2 | 59 |
| 14 | BATTER | Finn Allen | `4847` | 67.35 | 47 | 197.9 | 52 |
| 15 | BATTER | Rishabh Pant | `4703` | 66.93 | 292 | 178.1 | 80 |
| 16 | BATTER | Quinton de Kock | `2101` | 66.85 | 162 | 170.4 | 67 |
| 17 | BATTER | Reeza Hendricks | `768` | 66.85 | 158 | 174.7 | 35 |
| 18 | BATTER | Matthew Wade | `796` | 66.74 | 212 | 162.3 | 38 |
| 19 | BATTER | Prithvi Shaw | `5928` | 66.44 | 54 | 188.9 | 26 |
| 20 | BATTER | Faf du Plessis | `88` | 66.42 | 95 | 181.1 | 55 |

### Bowling Reserves (Ranks 11–20)
| Rank | Role | Player Name | ID | BWPS | Press LB | Raw Press Econ | Matches |
|---|---|---|---|---|---|---|---|
| 11 | BOWLER | Gurjapneet Singh | `23467` | 75.59 | 106 | 7.13 | 12 |
| 12 | BOWLER | Mujeeb Ur Rahman | `6450` | 75.07 | 178 | 7.25 | 38 |
| 13 | BOWLER | George Dockrell | `1101` | 74.78 | 53 | 6.11 | 45 |
| 14 | BOWLER | Spencer Johnson | `6354` | 74.66 | 140 | 8.10 | 23 |
| 15 | BOWLER | Tendai Chatara | `1159` | 74.36 | 45 | 7.07 | 10 |
| 16 | BOWLER | Shakib Al Hasan | `499` | 74.33 | 94 | 7.15 | 18 |
| 17 | BOWLER | Shadab Khan | `4926` | 73.87 | 263 | 7.28 | 44 |
| 18 | BOWLER | Kyle Jamieson | `3697` | 73.77 | 158 | 7.90 | 30 |
| 19 | BOWLER | Salman Mirza | `20704` | 73.59 | 97 | 7.24 | 15 |
| 20 | BOWLER | Yasim Murtaza | `2972` | 73.41 | 63 | 5.52 | 14 |

---

## 7. Statistical Sensitivity & Uncertainty Propagation

### 7.1 Shrinkage Parameter Sensitivity
Top-10 ranking membership overlap across shrinkage perturbations:
- **Batting ($K_{\text{bat}} = 20$ vs $30$)**: 100.0% overlap
- **Batting ($K_{\text{bat}} = 30$ vs $40$)**: 100.0% overlap
- **Bowling ($K_{\text{bowl}} = 30$ vs $40$)**: 100.0% overlap
- **Bowling ($K_{\text{bowl}} = 40$ vs $50$)**: 90.0% overlap

### 7.2 Bye / Leg-Bye Uncertainty Scenarios
- Scenario A (Strict observed 1.0 run per bye/legbye) vs Scenario B (Expected 1.40 runs per bye/legbye):
  - **Batting Top-10 Overlap**: 90.0%
  - **Bowling Top-10 Overlap**: 90.0%
- Candidates at Rank 9 and 10 with sensitivity to bye/leg-bye uncertainty are explicitly flagged as **PROVISIONAL** per Rule R4.

### 7.3 Format & Competition Breakdown
- **IPL Matches**: 371 (Average CRR: 8.69 RPO)
- **T20I Matches**: 512 (Average CRR: 7.98 RPO)

---

## 8. Evidentiary Confidence & Limitations

1. **Dataset-Observed Boundary**: All calculations strictly represent **dataset-observed statistics (2022–2026)** rather than lifetime career figures.
2. **Mental State Disclaimer**: High performance under measured high leverage indicates statistical reliability under defined match states, **not an inference of internal psychological composure** (Rule R8 / Prohibition P8).
3. **Data Completeness**: 16 matches with 0 deliveries were identified as abandoned/rain-outs and excluded from rate calculations.
4. **Reproducibility**: All calculations are 100% deterministic and reproducible via the SHA-256 manifest and fixed bootstrap seed (42).