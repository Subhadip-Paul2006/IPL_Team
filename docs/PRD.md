# Product Requirements Document (PRD)

**Project Title**: Rajasthan Royals Squad Intelligence & Historical Performance Engine  
**Event**: IPL 2027 Auction Scouting Hackathon  
**Target Franchise**: Rajasthan Royals (RR)  
**Document Version**: 1.0.0-PROD-SPEC  
**Status**: `[STATUS: PLANNED - GREENFIELD BASELINE]`  
**Date**: November 2026  
**Primary Authors**: Principal Software Architect, Cricket Data Engineer, Sports Analytics Specialist, Technical Product Manager  

---

## 1. Executive Summary & Problem Statement

### 1.1 Context: The IPL 2027 Mega-Auction Dynamics
The Indian Premier League (IPL) 2027 Mega-Auction represents a generational reset for all ten franchises. Operating under strict regulatory boundaries set by the Board of Control for Cricket in India (BCCI), franchises must rebuild their 18-to-25 player squads from near scratch within an uncompromising operational framework:
- **Purse Cap**: Exactly **INR 120.00 Crore** (₹1,200,000,000) total salary purse.
- **Roster Constraints**:
  - Minimum 18 players; maximum 25 players.
  - Maximum 8 overseas players in the total squad roster.
  - Maximum 4 overseas players permitted in any starting Playing XI (IPL Playing Conditions Rule 1.2).
  - Minimum 1 designated wicketkeeper in any active Playing XI.
  - Minimum 5 bowling options capable of fulfilling the 20-over quota.
- **Retention & Right-to-Match (RTM) Realities**: With strict retention deductions (typically escalating slabs up to ₹18 Cr, ₹14 Cr, ₹11 Cr) and targeted RTM cards, market liquidity for marquee domestic and international match-winners is acutely constrained. Every single auction bid carries immense opportunity cost.
- **Impact Player Regulation**: The modern tactical landscape permits one tactical substitution per match per team from a nominated 5-player substitute list, fundamentally elevating the value of specialized micro-skills (e.g., pure death-overs pinch-hitters, powerplay specialist seamers) over generic, mediocre all-rounders.

### 1.2 Franchise Context: The Rajasthan Royals Mandate
Since the inaugural 2008 IPL championship, the Rajasthan Royals have championed analytical efficiency, youth development, and data-driven talent scouting. Ahead of the 2027 cycle, RR requires a technological step-change:
1. **SMS Fortress Optimization**: Sawai Mansingh Stadium (SMS) in Jaipur presents unique environmental and spatial characteristics:
   - Exceptionally large boundary dimensions (square boundaries extending 68m to 75m; straight boundaries extending 72m to 78m).
   - High boundary-running demands (1s, 2s, and 3s represent a higher proportion of scoring compared to smaller grounds like Chinnaswamy or Wankhede).
   - Marked daytime-to-evening temperature drops in April and May, generating substantial 2nd-innings dew that degrades ball grip for finger spinners and seamers.
   - Distinct pitch soil variations (red-soil bounce vs black-soil low-skid surfaces) demanding targeted bowling release heights and batting bat-speed profiles.
2. **Scouting Asymmetry (Moneyball 2.0)**: Surfacing domestic Indian talent from the Syed Mushtaq Ali Trophy (SMAT), Ranji Trophy, and U-19 World Cup whose micro-skills translate directly to IPL match impact, acquiring them at base or near-base valuations (₹30L to ₹50L) before market consensus discovers them.
3. **Auction Room Execution & Real-Time Pivots**: In the high-velocity chaos of the live auction, emotion and bidding wars destroy franchise value. RR requires real-time algorithmic valuation (Expected Auction Price, Wins Above Replacement, Bidding Ceilings) and dynamic alternative pivot recommendations when primary targets cross economic viability thresholds.

### 1.3 The Failure of Traditional Scouting Metrics
Traditional cricket analytics fails elite franchises due to fundamental contextual blindness:
- **Raw Batting Average**: Ignores balls faced, situational pressure, and the cost of slow accumulators consuming high-value team balls in T20 cricket.
- **Crude Strike Rate**: Equates a 140 SR achieved during low-risk middle overs on a flat road at Chinnaswamy with a 140 SR achieved against 145+ km/h pace at the death in SMS Jaipur.
- **Raw Economy Rate**: Fails to normalize for match phase pars (e.g., an 8.5 RPO economy in the Powerplay is mediocre, whereas an 8.5 RPO economy at the Death is world-class).
- **Small Sample Hallucinations**: Overweighting 2 or 3 high-profile broadcast innings while ignoring multi-tournament underlying physical and tactical metrics.
- **Data Contamination**: Naively aggregating Super Over deliveries into career stats, distorting true career strike rates and economy records.

### 1.4 Product Vision & Proposed Solution
The **Rajasthan Royals Squad Intelligence & Historical Performance Engine** is a forensically audited, modular analytical software platform. It transforms over 2,800 verified historical match files (spanning IPL 2008–2026, Syed Mushtaq Ali Trophy, ICC Men's T20 World Cups, ODI World Cups, and The Hundred) into:
1. **Context-Adjusted True Metrics**: True Strike Rate (TSR), True Economy Rate (TER), Win Probability Added (WPA), Expected Runs (xR), and Leverage Index (LI).
2. **Spatial & Environmental Profiling**: Pitch surface, boundary geometry, and macro-weather dew correlations centered on SMS Jaipur.
3. **Granular Tactical Matchups**: Batter vs 6 bowling archetypes, head-to-head records, delivery trajectory/length vulnerability grids.
4. **Fatigue & Workload Tracking**: Multi-tournament cumulative bowling overs, congestion decay, and injury availability logs.
5. **Auction Valuation & Bidding Architecture**: T20 Wins Above Replacement (WAR), Expected Auction Price (EAP) regression models, and role scarcity multipliers under an INR 120 Cr purse cap.
6. **Regulatory Squad Simulation**: Constraint-satisfaction Playing XI optimization and 10,000-run Monte Carlo tournament simulations.
7. **Talent Scouting Discovery**: Cross-competition normalisation and automated diamond-in-the-rough domestic talent filtering.

---

## 2. Target Users & Stakeholder Personas

The system is engineered to serve five distinct stakeholder personas within the Rajasthan Royals organization, each with dedicated operational goals, technical proficiencies, core queries, and required outputs.

```
+-------------------------------------------------------------------------------------------------------+
|                                    RAJASTHAN ROYALS DECISION HIERARCHY                                |
+-------------------------------------------------------------------------------------------------------+
|  Franchise Chief Executive (CEO) & Ownership                                                          |
|  - High-level purse ROI, compliance sign-off, asset risk mitigation                                   |
+-------------------------------------------------------------------------------------------------------+
                                  |
                                  v
+----------------------------------------------------+--------------------------------------------------+
| Head of Cricket Operations                         | Auction Strategist & Bidding Lead                |
| - Squad balance, pipeline visibility, overseas cap | - Valuation models (EAP, WAR), pivot matrices    |
+----------------------------------------------------+--------------------------------------------------+
                                  |
                                  v
+----------------------------------------------------+--------------------------------------------------+
| Lead Cricket Data Analyst                          | Batting & Bowling Coaching Staff                 |
| - Granular math models, SQL queries, ball lineage  | - Pitch plans, bowler line/length, matchup cards |
+----------------------------------------------------+--------------------------------------------------+
```

### 2.1 Persona 1: Lead Cricket Data Analyst
- **Profile**: Advanced quantitative researcher with expertise in sports analytics, Python, SQL, and probabilistic modeling.
- **Primary Goals**:
  - Access granular, unadulterated ball-by-ball performance metrics normalized against phase and venue pars.
  - Inspect raw data lineage back to exact delivery files (zero black-box algorithms).
  - Parameterize custom baseline pars (e.g., filtering only top-tier pacers bowling > 140 km/h).
- **Frustrations & Pain Points**:
  - Inflexible commercial scouting databases that hide calculation formulas.
  - Imputation of missing values (e.g., treating null ball speeds as zero).
  - Lack of API access or exportable datasets for custom ad-hoc modeling.
- **Core Questions**:
  - *"What is Player X's True Strike Rate against Left-Arm Orthodox spin in overs 7–11 when required run rate exceeds 9.5 RPO?"*
  - *"What is Bowler Y's False Shot Percentage on hard-length deliveries (6–8m from stumps) at SMS Jaipur versus Wankhede?"*
- **Required Outputs & Interfaces**:
  - RESTful API endpoints, raw CSV/Parquet data exports, full SQL schema documentation, delivery-level data lineage provenance tags.

### 2.2 Persona 2: Head of Cricket Operations
- **Profile**: Senior administrator responsible for overall roster construction, contract lifecycles, scouting network management, and regulatory compliance.
- **Primary Goals**:
  - Maintain a transparent, real-time overview of squad composition across all player archetypes.
  - Ensure strict compliance with BCCI regulations (18–25 roster size, maximum 8 overseas players, purse ceiling).
  - Monitor the domestic talent scouting pipeline across SMAT and state leagues to identify long-term franchise assets.
- **Frustrations & Pain Points**:
  - Fragmented scouting reports scattered across scouting notebooks, emails, and isolated spreadsheets.
  - Sudden regulatory disqualifications (e.g., over-subscribing overseas slots).
  - Inability to objectively compare domestic performers with international stars.
- **Core Questions**:
  - *"Do we have adequate Indian pace-bowling depth if our primary overseas strike bowler suffers a stress fracture?"*
  - *"How does Candidate A from Punjab in the Syed Mushtaq Ali Trophy translate to IPL level based on competition difficulty weights?"*
- **Required Outputs & Interfaces**:
  - Visual Squad Composition Dashboard, Multi-Tournament Scouting Radar, Overseas/Domestic Quota Gauges, Automated Compliance Audit Alerts.

### 2.3 Persona 3: Auction Strategist & Bidding Room Lead
- **Profile**: Financial and strategic decision-maker leading real-time bidding in the auction room, operating under immense psychological pressure.
- **Primary Goals**:
  - Maximize team Wins Above Replacement (WAR) within the INR 120.00 Cr purse.
  - Prevent over-bidding on high-profile marquee players driven by bidding war dynamics.
  - Execute instantaneous pivot maneuvers when target players exceed their hard valuation ceiling.
- **Frustrations & Pain Points**:
  - Slow, unresponsive analytical tools that cannot deliver immediate alternatives within a 45-second bidding window.
  - Rigid, static budget plans that collapse as soon as the first target is lost to a competitor.
- **Core Questions**:
  - *"If Player A's bidding reaches ₹14.5 Cr, at what threshold does his Expected Auction Price (EAP) become negative-EV for our purse structure?"*
  - *"What are the top 3 alternative pace-bowling all-rounders offering >= 85% of Player A's death-overs production at < ₹6.0 Cr?"*
- **Required Outputs & Interfaces**:
  - Real-Time Auction Bidding Console, Dynamic Purse Burn Curve, Value-Over-Replacement Matrix, Automated 45-Second Pivot Recommender.

### 2.4 Persona 4: Batting & Bowling Coaching Staff
- **Profile**: Former elite cricketers and domain tacticians responsible for on-field execution, technical skill development, and matchday opposition plans.
- **Primary Goals**:
  - Prepare actionable, digestible tactical plans for players before each fixture.
  - Exploit specific structural weaknesses in opposition batters and bowlers.
  - Tailor bowling rotations and field placements to Sawai Mansingh Stadium pitch conditions and evening dew.
- **Frustrations & Pain Points**:
  - Dense academic statistical reports loaded with mathematical jargon that cannot be communicated to players in a 10-minute team meeting.
  - Generic pitch reports that ignore local ground geometry and time-of-day dew dynamics.
- **Core Questions**:
  - *"Where should our pacers bowl to Batter Z in overs 16–20 at Jaipur given his dismissal history against wide yorkers vs short balls?"*
  - *"Which of our spinners maintains the best release grip and control when relative humidity exceeds 75% in evening second innings?"*
- **Required Outputs & Interfaces**:
  - 1-Page Printable Matchup Tactical Cards, Visual Pitch Length/Line Heatmaps, Batter Wagon Wheels, SMS Jaipur Ground Geometry Plans.

### 2.5 Persona 5: Franchise Chief Executive & Ownership
- **Profile**: Executive leadership responsible for multi-year franchise valuation, brand equity, governance, and return on investment.
- **Primary Goals**:
  - Maintain a sustainable, championship-caliber franchise asset.
  - Approve final high-level auction spending brackets and risk mitigation strategies.
  - Ensure total governance, licensing compliance, and legal integrity across all operational software.
- **Frustrations & Pain Points**:
  - Unclear ROI on multi-crore player acquisitions.
  - Unanticipated availability losses (players missing half the season due to national duty NOC denials or undisclosed injuries).
- **Core Questions**:
  - *"What is our projected championship win probability across our three alternative squad composition scenarios?"*
  - *"What is our financial and competitive exposure if our marquee overseas signing is called back for national bilateral series?"*
- **Required Outputs & Interfaces**:
  - Executive KPI Summary Brief, Monte Carlo Tournament Projection Report, Player Availability & Medical Downtime Ledger.

---

## 3. Product Objectives & Hackathon-Specific Goals

### 3.1 Strategic Product Objectives
1. **Objective Decision-Making Engine**: Eliminate intuition-based biases by grounding all recruitment and matchday tactics in normalized ball-by-ball empirical evidence.
2. **Sawai Mansingh Stadium Fortress Strategy**: Maximize home-ground win percentage (> 70% target) through specialized Jaipur venue modeling (long boundary running, high-pace exploitation, evening dew compensation).
3. **Auction Capital Efficiency**: Maximize Wins Above Replacement per Crore spent, ensuring that Rajasthan Royals extracts at least 25% more WAR per rupee than the league average.
4. **Talent Pipeline Sustainability**: Establish an algorithmic domestic scouting filter identifying top tier-2 emerging talent (age <= 24, base price <= ₹50 Lakhs) with elite micro-skills.

### 3.2 Hackathon Evaluation Rubric & Explicit Alignment
The product architecture and documentation directly address the competitive criteria of the IPL 2027 Auction Scouting Hackathon:

| Weight | Hackathon Evaluation Category | Specific System Capabilities & Architectural Features |
|---|---|---|
| **30%** | **Scouting Accuracy & Analytical Depth** | • True Strike Rate (TSR) & True Economy Rate (TER) normalized by phase and venue pars.<br>• Ball-by-ball Win Probability Added (WPA) and Expected Runs (xR).<br>• T20 Wins Above Replacement (WAR) modeled across Batting, Bowling, and Fielding.<br>• Cross-competition normalisation calibrating SMAT, U-19, and The Hundred to IPL level. |
| **25%** | **System Architecture & Engineering Robustness** | • 3NF Central Normalized Schema in PostgreSQL with 20 distinct entities.<br>• Strict separation: Ingestion -> Quarantine Lake -> Normalisation -> Enrichment -> Analytics.<br>• Sub-200ms p95 query latency via indexed materialized views and Redis caching.<br>• Deterministic reproducibility: bit-for-bit identical outputs from identical raw seeds. |
| **20%** | **Domain Validity & Cricket Logic** | • Strict isolation of Super Over statistics from official career aggregates.<br>• Rigorous handling of DLS rain-affected matches using revised targets/overs.<br>• Accurate modeling of IPL Impact Player tactical substitution mechanics.<br>• Distinction between macro-weather ambient data and direct pitch moisture sensors.<br>• No attribution of byes, leg-byes, or penalty runs to bowler runs conceded. |
| **15%** | **UX, Usability & Actionability** | • Tailored persona interfaces: Bidding Room Console, Coach Matchup Cards, Analyst API.<br>• Interactive pitch heatmaps, boundary wagon wheels, and dynamic purse burn curves.<br>• 45-second real-time pivot recommendation engine for live auction bidding rooms. |
| **10%** | **Innovation & Auction Edge** | • SMS Jaipur Home Fortress Engine (boundary running index, dew grip decay factor).<br>• Predictive Expected Auction Price (EAP) regression models with scarcity multipliers.<br>• 10,000-run Monte Carlo tournament simulator projecting playoff probabilities under squad shock scenarios. |

---

## 4. Comprehensive Functional Requirements (FR-01 to FR-25)

Each functional requirement is documented with strict input specifications, expected outputs, mathematical/algorithmic logic, and explicit error-handling behaviors. The platform encompasses **7 User-Facing Analytical Modules (Modules 1–7)** powering cricket intelligence and auction strategy, underpinned by **1 Foundational Data Governance & Ingestion Subsystem (Module 8)** enforcing 3NF normalization, identity resolution, and MCC/IPL rule compliance.

```
+-------------------------------------------------------------------------------------------------------+
|                                  FUNCTIONAL REQUIREMENTS MODULE MAP                                  |
+-------------------------------------------------------------------------------------------------------+
|  MODULE 1: MATCH IMPACT (FR-01, FR-02, FR-03)                                                        |
|  MODULE 2: VENUE PROFILING & ENVIRONMENT (FR-04, FR-05, FR-06)                                       |
|  MODULE 3: TACTICAL MATCHUPS & MECHANICS (FR-07, FR-08, FR-09)                                        |
|  MODULE 4: WORKLOAD, FATIGUE & INJURY (FR-10, FR-11, FR-12)                                          |
|  MODULE 5: AUCTION VALUATION & ECONOMICS (FR-13, FR-14, FR-15)                                       |
|  MODULE 6: SQUAD SIMULATION & SCENARIOS (FR-16, FR-17, FR-18)                                         |
|  MODULE 7: TALENT SCOUTING & NORMALISATION (FR-19, FR-20)                                            |
|  MODULE 8: CORE DATA INGESTION & LINEAGE (FR-21, FR-22, FR-23, FR-24, FR-25)                         |
+-------------------------------------------------------------------------------------------------------+
```

### Module 1: Match Impact Engine

#### FR-01: Ball-by-Ball Context Valuation (True Strike Rate & True Economy Rate)
- **Description**: Calculates context-adjusted batting and bowling performance relative to tournament phase pars and venue scoring environments.
- **Inputs**: Ball delivery record (`batter_id`, `bowler_id`, `runs_batter`, `extras_runs`, `match_phase`, `over_number`, `innings`, `venue_id`, `season`).
- **Outputs**:
  - `true_strike_rate`: Batting Strike Rate relative to expected phase/venue par ($TSR = SR_{observed} - SR_{expected}$).
  - `true_economy_rate`: Bowling Economy relative to expected phase/venue par ($TER = Economy_{actual} - Economy_{expected} = Econ_{observed} - Econ_{expected}$, measured in runs per over, where negative values indicate run suppression superior to par).
  - `run_value_added` (RVA): Net runs generated above or below the baseline delivery expectation.
- **Calculation Logic**:
  1. Determine match phase: Powerplay (Overs 0.1–5.6), Middle (Overs 6.1–14.6), Death (Overs 15.1–19.6).
  2. Compute Baseline Expected Runs per delivery for Phase $P$ at Venue $V$ in Season $S$:
     $$\bar{R}_{P,V,S} = \frac{\sum \text{Runs scored in phase } P \text{ at venue } V}{\sum \text{Legal deliveries in phase } P \text{ at venue } V}$$
  3. Delivery Run Value: $RVA = \text{Runs scored} - \bar{R}_{P,V,S}$.
- **Error Handling**: If venue sample size is under 3 matches, fall back to tournament-wide season phase baseline. If division by zero occurs (0 deliveries faced), return `NULL`.

#### FR-02: Win Probability Added (WPA) & Expected Runs (xR)
- **Description**: State-based probabilistic model quantifying the shift in match win expectancy produced by every individual delivery.
- **Inputs**: Delivery state ($I \in \{1, 2\}$, balls remaining $B$, wickets lost $W$, current score $S$, target $T$ if $I=2$, historical chase curves).
- **Outputs**:
  - $\Delta WP$ (Win Probability Added per delivery).
  - Cumulative player match WPA ($\sum \Delta WP$).
  - `expected_runs` ($xR$): Probabilistic expectation of runs from current match state.
- **Calculation Logic**:
  $$\Delta WP = WP(S_{t+1}) - WP(S_t)$$
  Where $WP(S_t)$ is generated from a logistic regression / empirical transition matrix trained on 1,243 IPL matches.
- **Error Handling**: If second innings target is missing (e.g. rain abandonment), set delivery $\Delta WP = 0.0$ and flag record as `INCOMPLETE_OUTCOME`.

#### FR-03: Clutch Index & High-Leverage Situations
- **Description**: Measures player execution under extreme psychological pressure.
- **Inputs**: Delivery Leverage Index ($LI$), match stage (Group Stage vs Eliminator / Qualifier / Final), target proximity.
- **Outputs**: `clutch_rating` (0–100 percentile), High-Leverage Strike Rate ($LI \ge 1.5$), High-Leverage Economy ($LI \ge 1.5$).
- **Calculation Logic**:
  $$LI = \frac{|\Delta WP_{\text{max}} - \Delta WP_{\text{min}}|}{\bar{\Delta WP}_{\text{league}}}$$
  Deliveries with $LI \ge 1.5$ are designated High-Leverage.
- **Error Handling**: When deliveries in high-leverage situations are $< 30$, append `SAMPLE_SIZE_WARNING` to player card.

---

### Module 2: Venue Profiling & Environmental Engine

#### FR-04: Pitch & Ground Behavioral Profiling
- **Description**: Models physical dimensions, soil type, and scoring geography for all major IPL grounds.
- **Inputs**: `venue_id`, boundary distances (Straight, Square Off, Square Leg, Fine Leg, Third Man), pitch soil classification (Red Soil, Black Soil, Mixed).
- **Outputs**: Boundary Area ($m^2$), Boundary Frequency Expectation, Pace/Spin Run-Rate Ratio, Ground Classification (Pace Haven, Spin Fortress, Batting Paradise).
- **Calculation Logic**: Geometrical calculation of outfield polygon area; historical phase-wise run rates partitioned by soil category.
- **Error Handling**: For unverified ground dimensions, populate with `UNVERIFIED_ESTIMATE` and record provenance note.

#### FR-05: Sawai Mansingh Stadium (SMS Jaipur) Home Fortress Engine
- **Description**: Dedicated analytical model capturing the operational dynamics of Rajasthan Royals' home ground.
- **Inputs**: SMS historical delivery records (2008–2026), boundary dimensions (68m–75m square, 72m–78m straight), day vs night fixture flags, toss decisions.
- **Outputs**:
  - `sms_running_index`: Proportion of runs scored in 1s, 2s, and 3s vs boundaries compared to IPL average.
  - `sms_phase_pars`: SMS-specific baseline run rates and wicket rates for Powerplay, Middle, and Death.
  - `optimal_sms_bowler_profile`: Preferred release velocity (> 138 km/h) and hard-length boundary suppression score.
- **Calculation Logic**: Benchmark SMS non-boundary strike rotation rate against league standard:
  $$\text{Running Index}_{\text{SMS}} = \frac{(\text{Runs in 1s, 2s, 3s} / \text{Total Runs})_{\text{SMS}}}{(\text{Runs in 1s, 2s, 3s} / \text{Total Runs})_{\text{League}}}$$
- **Error Handling**: Maintain rolling 3-year weighting to capture pitch re-laying conducted by the Rajasthan Cricket Association.

#### FR-06: Environmental & Dew Factor Correlation
- **Description**: Integrates Open-Meteo macro-meteorological measurements to estimate second-innings ball grip degradation.
- **Inputs**: Match date, venue latitude/longitude, start time (15:30 IST vs 19:30 IST), Open-Meteo hourly historical data (Air Temperature, Relative Humidity, Dew Point, Wind Speed).
- **Outputs**: `dew_risk_score` (Low: 0.0–0.3, Moderate: 0.4–0.6, High: 0.7–1.0), Predicted 2nd-Innings Spin Control Degradation Factor.
- **Calculation Logic**: Dew point spread: $T_{\text{spread}} = T_{\text{air}} - T_{\text{dew}}$. If $T_{\text{spread}} \le 2.5^\circ\text{C}$ and $RH \ge 75\%$ during hours 20:00–23:00 IST, assign `dew_risk_score` $\ge 0.8$.
- **Domain Guardrail**: Environmental data MUST be labeled as macro-weather context. Prohibit any claim that this represents sub-surface soil moisture sensors.

---

### Module 3: Tactical Matchups & Mechanics

#### FR-07: Batter vs Bowling Type Profiling
- **Description**: Multi-dimensional matrix measuring batting proficiency across 6 primary bowling archetypes:
  1. Right-Arm Fast / Fast-Medium (RAF)
  2. Left-Arm Fast / Fast-Medium (LAF)
  3. Right-Arm Offbreak (OS)
  4. Left-Arm Orthodox (SLA)
  5. Right-Arm Legbreak / Googly (LBG)
  6. Left-Arm Unorthodox / Chinaman (LAC)
- **Inputs**: `batter_id`, delivery records with `bowler_bowling_style`, runs scored, dismissals, dot balls.
- **Outputs**: Strike Rate, Dot Ball %, Boundary %, Balls Per Dismissal (BPD), False Shot % per bowling archetype.
- **Calculation Logic**: Aggregate ball-level interactions filtered by `bowling_style` and partitioned by match phase.
- **Error Handling**: If balls faced against a style $< 24$, display metric with `INSUFFICIENT_SAMPLE_FLAG`.

#### FR-08: Head-to-Head Batter vs Bowler Matrix
- **Description**: Granular historical micro-data between specific batters and bowlers.
- **Inputs**: `batter_id`, `bowler_id`, complete ball-by-ball history.
- **Outputs**: Deliveries faced, Runs conceded, Dismissal count, Dismissal modes, Wickets summary, Dot ball percentage.
- **Calculation Logic**: Exact inner-join aggregation on `batter_id` and `bowler_id`.
- **Error Handling**: If zero deliveries exist, return empty record with status `NO_PRIOR_ENCOUNTERS`.

#### FR-09: Pitch Trajectory & Length Vulnerability Grids
- **Description**: Evaluates scoring rates and dismissal clusters across delivery lines and lengths.
- **Inputs**: HawkeyeStats trajectory coordinates (release speed, bounce point distance from stumps $Y$, lateral line from center stump $X$).
- **Outputs**: Pitch landing heatmaps, dismissal zones, scoring efficiency grid (Yorker, Full, Good Length, Back of Length, Short).
- **Calculation Logic**: Spatial discretization into length buckets: Yorker (< 2.0m), Full (2.0–4.0m), Good (4.0–6.5m), Back of Length (6.5–8.5m), Short (> 8.5m).
- **Error Handling**: Where Hawkeye tracking is unavailable, leave coordinates strictly as `NULL`. DO NOT impute (0,0).

---

### Module 4: Workload, Fatigue & Injury Tracking

#### FR-10: Cumulative Multi-Format Workload Engine
- **Description**: Tracks cumulative overs bowled, deliveries faced, and high-intensity match days across all sanctioned tournaments.
- **Inputs**: Match records across IPL, SMAT, ICC T20 World Cups, ODI World Cups, and The Hundred.
- **Outputs**: 30-Day, 90-Day, and 365-Day Cumulative Overs Bowled, `workload_strain_tier` (Low, Medium, High, Extreme).
- **Calculation Logic**: Exponentially weighted moving average of deliveries bowled over trailing time windows.
- **Error Handling**: Flag records where tournament coverage is incomplete as `PARTIAL_COVERAGE`.

#### FR-11: Schedule Congestion & Travel Strain
- **Description**: Models physical fatigue induced by compressed recovery intervals (< 48 hours) and transit between Indian host cities.
- **Inputs**: Fixture calendar, match timestamps, host city travel distance matrix.
- **Outputs**: `rest_hours_available`, `travel_km_logged`, `fatigue_decay_multiplier`.
- **Calculation Logic**: Calculate elapsed hours between consecutive match end-times and flight distance in kilometers.
- **Error Handling**: If fixture schedule is unannounced, populate with `DEFAULT_SCHEDULE_ASSUMPTION`.

#### FR-12: Injury History & Availability Ledger
- **Description**: Tracks historical medical downtime, recurrence rates of soft-tissue and stress injuries, and national board NOC restrictions.
- **Inputs**: Player injury records, surgical history, national board bilateral touring schedules, Champions Trophy / World Cup schedules.
- **Outputs**: `availability_probability` (0.0–1.0), `injury_risk_tier` (Low, Medium, High), Expected Matches Available (out of 14 league matches).
- **Calculation Logic**: Actuarial probability model combining player age, previous games missed per season, and confirmed international NOC departure dates.
- **Error Handling**: If injury details are unverified, mark explicitly as `UNVERIFIED_STATUS`.

---

### Module 5: Auction Valuation & Market Economics

#### FR-13: Expected Auction Price (EAP) Predictive Model
- **Description**: Predicts market clearing price for any candidate at the IPL 2027 Mega-Auction under an INR 120 Cr purse cap.
- **Inputs**: Player age, 3-year weighted True SR/Econ, international caps, role category, historical bidding escalations.
- **Outputs**: Expected Auction Price (INR Crores), 80% Confidence Interval (Floor, Median, Ceiling).
- **Calculation Logic**: Multi-variable regularized regression calibrated against 2022 and 2025 mega-auction clearing price data, scaled by 120 Cr cap.
- **Error Handling**: Clamp lower bound at player's official auction base price (₹30L, ₹50L, ₹1.0 Cr, ₹1.5 Cr, ₹2.0 Cr). Never exceed ₹30.0 Cr.

#### FR-14: T20 Wins Above Replacement (WAR)
- **Description**: Quantifies total team wins contributed by a player above an easily obtainable league-minimum replacement player.
- **Inputs**: Batting Run Value Added ($RVA_{bat}$), Bowling Run Value Added ($RVA_{bowl}$), Fielding Value Added ($FVA$), Runs Per Win factor ($RPW \approx 18.5$ runs in T20).
- **Outputs**: $WAR_{bat}$, $WAR_{bowl}$, $WAR_{field}$, Total $WAR$.
- **Calculation Logic**:
  $$WAR = \frac{RVA_{bat} + RVA_{bowl} + FVA - \text{Replacement Level Baseline}}{RPW}$$
- **Error Handling**: If player has zero appearances, return $WAR = 0.0$.

#### FR-15: Role Scarcity Multipliers & Auction Economics
- **Description**: Applies market scarcity coefficients to player archetypes that suffer from chronic supply deficits in the auction pool.
- **Inputs**: Role category (e.g. Indian Pace All-Rounder, Elite Death Bowler, Wicketkeeper-Finisher, Mystery Spinner).
- **Outputs**: `scarcity_multiplier` (1.0x to 1.8x), Scarcity-Adjusted Valuation Ceiling.
- **Calculation Logic**: Inverse ratio of verified available tier-1 candidates to franchise demand slots across 10 teams.
- **Error Handling**: If archetype supply is unverified, default multiplier to neutral (1.0x).

---

### Module 6: Squad Simulation & Tactical Scenarios

#### FR-16: Playing XI Constraint-Satisfaction Optimizer
- **Description**: Algorithmic solver generating valid, highest-utility Playing XIs satisfying all BCCI regulatory constraints.
- **Inputs**: Squad roster (18–25 players), player fitness states, opposition matchup profiles, venue parameters.
- **Outputs**: Optimal Playing XI, 5 Designated Impact Substitutes, Batting Order, Bowling Quota Distribution.
- **Constraints Enforced**:
  - Exactly 11 starting players.
  - Maximum 4 overseas players in the 11.
  - At least 1 designated wicketkeeper.
  - Minimum 5 bowling options capable of delivering 20 overs.
- **Error Handling**: If user manually attempts to save an XI with $> 4$ overseas players, trigger hard exception `VALIDATION_OVERSEAS_EXCEEDED` and block save.

#### FR-17: Impact Player Tactical Deployment Engine
- **Description**: Determines optimal tactical substitute based on match conditions and toss outcome.
- **Inputs**: Batting first vs bowling first, wickets lost at over 6/10, bench substitute options.
- **Outputs**: Recommended Substitution (`Player_Out`, `Player_In`), Target Over Window, Expected Run Delta.
- **Calculation Logic**: Decision-tree evaluating net run differential of fielding an extra bowler vs batting depth under current match state.
- **Error Handling**: Restrict to exactly 1 substitution per team per match.

#### FR-18: Monte Carlo Tournament Campaign Simulator
- **Description**: Simulates full 14-match IPL league stages across 10,000 iterations to project squad performance distribution.
- **Inputs**: Playing XI ratings, schedule matrix, home/away fixtures, stochastic injury shock probabilities.
- **Outputs**: Win Total Distribution, Playoff Qualification Probability (%), Championship Probability (%), Projected Net Run Rate (NRR).
- **Calculation Logic**: Ball-by-ball or over-by-over stochastic simulator using Markov chains and player historical distributions.
- **Reproducibility Mandate**: Require explicit integer seed for random number generator to guarantee deterministic bit-for-bit reproducibility.

---

### Module 7: Talent Scouting & Normalisation

#### FR-19: Cross-Competition Normalisation Engine
- **Description**: Calibrates non-IPL statistical performance (Syed Mushtaq Ali Trophy, U-19 World Cup, The Hundred) to IPL baseline equivalency.
- **Inputs**: Raw tournament match statistics, tournament difficulty coefficient ($k_{tourney}$).
- **Outputs**: `ipl_adjusted_strike_rate`, `ipl_adjusted_economy_rate`, `talent_equivalency_score`.
- **Calculation Logic**:
  $$Metric_{\text{IPL Equiv}} = Metric_{\text{Observed}} \times k_{\text{tourney}}$$
  Where $k_{\text{tourney}}$ is derived from performance of players who competed in both tournaments within a 24-month window.
- **Error Handling**: If competition has no verified crossover players, mark metric as `RAW_UNADJUSTED`.

#### FR-20: Diamond-in-the-Rough Scouting Filter
- **Description**: Algorithmic filter detecting high-impact, undervalued domestic talent with elite micro-skills.
- **Inputs**: Player Age ($\le 24$), Base Price bracket ($\le \text{₹50 Lakhs}$), SMAT ball-by-ball records.
- **Outputs**: Shortlisted candidate ranking, micro-skill attribution (e.g. Powerplay Dot Ball % $\ge 50\%$, Death Over SR $\ge 165$).
- **Filtering Logic**: Multi-threshold rule: Age $\le 24$ AND IPL Appearances $\le 5$ AND (Powerplay True Econ $\le -1.5$ OR Death True SR $\ge +25.0$).
- **Error Handling**: Filter out players with $< 5$ domestic matches or $< 60$ balls to avoid small sample noise.

---

### Module 8: Core Data Ingestion & Lineage

#### FR-21: Multi-Source Player Identity Resolution (PIR)
- **Description**: Disambiguates player names across diverse formats into unique, canonical entity records.
- **Inputs**: Name strings, team names, match dates, CricSheet 8-character hexadecimal hashes (`info.registry.people`).
- **Outputs**: Canonical `player_id`, Master Name, Aliases Table Record.
- **Resolution Logic**: Primary match on CricSheet hex hash. Secondary fallback: Levenshtein distance on full name + team roster verification. Confidence score $\ge 0.95$ auto-accepted; $< 0.95$ sent to human review queue.
- **Error Handling**: Never merge distinct players with identical initials (e.g. "R Sharma" representing Rohit Sharma vs Rahul Sharma).

#### FR-22: Multi-Format Streaming Ingestion Parser
- **Description**: Ingests both modern CricSheet JSON (v1.3.0) and legacy YAML (v0.94) match records without data loss.
- **Inputs**: Raw JSON/YAML files from `CricSheet/`.
- **Outputs**: Staged match records, foreign key validated rows, ingestion audit logs.
- **Calculation Logic**: Polymorphic parsing engine mapping versioned payloads into raw relational staging tables.
- **Error Handling**: Malformed files are quarantined in `quarantine_lake` with a syntax error trace without halting the ingestion run.

#### FR-23: DLS Par & Revised Target Reconciler
- **Description**: Reconciles rain-affected matches against Duckworth-Lewis-Stern target revisions.
- **Inputs**: CricSheet `info.outcome.method` ("D/L" or "DLS"), `info.outcome.target` (revised target runs and overs).
- **Outputs**: Adjusted required run rate, normalized balls remaining, true pressure score.
- **Calculation Logic**: Substitute revised target and overs into denominator for pressure calculations.
- **Error Handling**: If DLS metadata is corrupted or missing revised overs, flag match as `DLS_CALCULATION_ABORTED`.

#### FR-24: Super Over Isolation Protocol
- **Description**: Strictly isolates Super Over innings from official career batting and bowling aggregates.
- **Inputs**: Innings records flagged with `"super_over": true`.
- **Outputs**: Dedicated Super Over performance cards; isolated career totals.
- **Domain Rule Enforced**: Hard assertion that Super Over runs, wickets, and balls faced NEVER increment official career totals (ICC/BCCI official statistical convention).
- **Error Handling**: Throw validation error if an ELT pipeline attempts to insert super over balls into the standard `deliveries` career view.

#### FR-25: Automated Lineage & Data Provenance Tracker
- **Description**: Attaches end-to-end source tracking metadata to every derived analytical metric.
- **Inputs**: Metric calculation execution job, source file identifiers.
- **Outputs**: Provenance manifest record (`derived_feature_id`, `source_file_id`, `calculation_timestamp`, `model_version`, `raw_record_hash`).
- **Verification Rule**: Any analytical output displayed in the user interface must be traceable down to its underlying raw delivery rows.
- **Error Handling**: If a derived feature record has broken foreign keys to source tables, fail the verification test.

---

## 5. Non-Functional Requirements (NFRs)

```
+-------------------------------------------------------------------------------------------------------+
|                                    NON-FUNCTIONAL REQUIREMENTS MATRIX                                 |
+-------------------+-----------------------------------+-----------------------------------------------+
| Dimension         | Standard / Threshold              | Verification Method                           |
+-------------------+-----------------------------------+-----------------------------------------------+
| Query Latency     | p95 < 200ms (Search & Matchups)   | Automated Locust / k6 load test suite         |
| Simulation Time   | < 3,000ms (10,000 Monte Carlo)    | Vectorized NumPy benchmarking harness         |
| Reproducibility   | 100% Bit-for-Bit Deterministic    | Fixed random seed regression test             |
| Data Integrity    | Zero Synthetic / Imputed Zeros    | Data Quality Agent automated schema linters   |
| Availability      | 99.9% Uptime during Auction Window| Multi-AZ containerized deployment             |
| Security & Auth   | RBAC (Analyst, Coach, Exec)       | JWT authentication + SQL parameterization     |
+-------------------+-----------------------------------+-----------------------------------------------+
```

### 5.1 Performance & Latency
- **NFR-01 (API Response Times)**: All standard player search, profile retrieval, and head-to-head matchup queries must return with $p95 < 200\text{ ms}$ and $p99 < 500\text{ ms}$ under concurrent load of 50 active users.
- **NFR-02 (Simulation Throughput)**: 10,000 full-tournament Monte Carlo iterations for an updated Playing XI configuration must complete in $< 3,000\text{ ms}$ using vectorized NumPy operations.
- **NFR-03 (Bulk Ingestion Speed)**: The full historical archive of 2,822 match files must ingest, validate, and populate the PostgreSQL schema within $< 20\text{ minutes}$ on standard developer workstations.

### 5.2 Deterministic Reproducibility
- **NFR-04 (Algorithmic Determinism)**: Given identical raw database records and simulation parameters, all derived statistics, valuation models, and Monte Carlo engines must produce bit-for-bit identical outputs across environments. Stochastic algorithms must require an explicit integer random seed parameter.

### 5.3 Data Integrity & Provenance
- **NFR-05 (Zero Data Fabrication)**: The system must never hallucinate, extrapolate without explicit flags, or synthesize fictional cricket statistics. All metrics must be mathematically derivable from verified raw delivery records.
- **NFR-06 (Missing Data Protocol)**: Missing values (e.g. unrecorded ball release speed or tracking coordinates) must remain strictly `NULL`. The system is expressly forbidden from substituting `0.0` or league averages for missing records.
- **NFR-07 (End-to-End Lineage)**: Every metric displayed on any dashboard must store an unbroken provenance chain tracing back to the raw source file name, delivery timestamp, and parser version.

### 5.4 Security, Access Control & Compliance
- **NFR-08 (Role-Based Access Control)**: Authentication must enforce three distinct privilege tiers:
  1. *Executive / Ownership*: High-level valuation summaries, Monte Carlo projections, budget sign-offs.
  2. *Strategy & Analytics*: Full read/write access to valuation models, simulation parameters, and raw data queries.
  3. *Coaching Staff*: Tactical cards, matchup heatmaps, opposition briefs (restricted from viewing auction pricing models).
- **NFR-09 (SQL Injection Prevention)**: All database interactions must execute through parameterized queries or an approved Object-Relational Mapping (ORM) layer. Raw string interpolation in SQL statements is strictly prohibited.
- **NFR-10 (Licensing & Attribution)**: All data visualizations and exports must embed required legal attributions in compliance with Open Data Commons Attribution License (ODC-By v1.0) for CricSheet and Creative Commons terms for Open-Meteo.

---

## 6. User Workflows & Core Use Cases

### 6.1 Use Case 1: Pre-Auction Target Shortlisting & Valuation
**Primary Actors**: Lead Data Analyst, Auction Strategist  
**Objective**: Build the finalized target board and pricing brackets for the IPL 2027 Mega-Auction under an INR 120 Cr purse cap.

```
+-------------------------------------------------------------------------------------------------------+
| USER WORKFLOW 1: PRE-AUCTION TARGET SHORTLISTING & VALUATION                                          |
+-------------------------------------------------------------------------------------------------------+
|  [Step 1] Select Squad Deficit (e.g. Indian Pace All-Rounder or Death-Overs Bowler)                  |
|       |                                                                                               |
|       v                                                                                               |
|  [Step 2] Apply Core Filters: True Economy (Death) <= -1.2 RPO, Ball Speed >= 138 km/h                |
|       |                                                                                               |
|       v                                                                                               |
|  [Step 3] Cross-Reference Availability Ledger & Injury Downtime (Exclude high-risk NOC denials)       |
|       |                                                                                               |
|       v                                                                                               |
|  [Step 4] Generate Expected Auction Price (EAP) & T20 WAR Valuation Curve                            |
|       |                                                                                               |
|       v                                                                                               |
|  [Step 5] Define Hard Bidding Ceiling (e.g. Floor ₹6.5 Cr, Median ₹8.0 Cr, Ceiling ₹10.25 Cr)          |
|       |                                                                                               |
|       v                                                                                               |
|  [Step 6] Export Target Bidding Tier Card to Live Auction Console                                     |
+-------------------------------------------------------------------------------------------------------+
```

### 6.2 Use Case 2: In-Auction Real-Time Pivot Strategy (45-Second Window)
**Primary Actors**: Auction Strategist, Franchise CEO  
**Objective**: Execute an instantaneous, optimal tactical pivot when a primary auction target exceeds the pre-approved bidding ceiling during live bidding.

```
+-------------------------------------------------------------------------------------------------------+
| USER WORKFLOW 2: IN-AUCTION REAL-TIME PIVOT STRATEGY                                                  |
+-------------------------------------------------------------------------------------------------------+
|  [Bidding Event] Target Player Bidding reaches ₹10.50 Cr (Hard Ceiling ₹10.25 Cr Exceeded)           |
|       |                                                                                               |
|       v                                                                                               |
|  [Trigger Alert] Bidding Console sounds "CEILING VIOLATION" alert; highlights negative-EV warning     |
|       |                                                                                               |
|       v                                                                                               |
|  [Algorithm Execution] Pivot Recommender analyzes remaining un-auctioned talent pool                   |
|       - Evaluates similarity score based on Death Over True Econ & SMS Jaipur Suitability             |
|       - Identifies 2 Alternatives with >= 85% statistical parity at < 60% expected cost               |
|       |                                                                                               |
|       v                                                                                               |
|  [Strategist Action] Strategist signals paddle drop; redirects capital to Alternative B               |
|       |                                                                                               |
|       v                                                                                               |
|  [Purse Recalculation] Live purse dashboard dynamically updates remaining budget headroom             |
+-------------------------------------------------------------------------------------------------------+
```

### 6.3 Use Case 3: Matchday Opposition Game-Planning (SMS Jaipur Night Fixture)
**Primary Actors**: Bowling Coach, Batting Coach, Lead Analyst  
**Objective**: Formulate the bowling defense and batting chase strategy for a night match at Sawai Mansingh Stadium against an opposition featuring destructive top-order left-handers.

```
+-------------------------------------------------------------------------------------------------------+
| USER WORKFLOW 3: MATCHDAY OPPOSITION GAME-PLANNING                                                    |
+-------------------------------------------------------------------------------------------------------+
|  [Step 1] Select Opposition Starting XI & Venue: SMS Jaipur (19:30 IST Start)                         |
|       |                                                                                               |
|       v                                                                                               |
|  [Step 2] Fetch Environmental Context (Open-Meteo): RH 82%, Dew Point 21°C -> High Dew Flagged       |
|       |                                                                                               |
|       v                                                                                               |
|  [Step 3] Query Batter vs Bowling Style Matrix: Opposition LHBs vs Right-Arm Off-Spin vs High Pace     |
|       |                                                                                               |
|       v                                                                                               |
|  [Step 4] Inspect SMS Jaipur Boundary Geometry: Long 74m Square Boundary on North Side                |
|       |                                                                                               |
|       v                                                                                               |
|  [Step 5] Generate Tactical Directive:                                                               |
|       - Deploy Right-Arm Pace bowling back-of-length (7.0–8.0m) angling across LHBs into long boundary |
|       - Complete spin overs before Over 12 prior to heavy dew accumulation on outfield grass          |
|       |                                                                                               |
|       v                                                                                               |
|  [Step 6] Print 1-Page Matchup Cheat-Sheet for Captain and Bowlers                                    |
+-------------------------------------------------------------------------------------------------------+
```

### 6.4 Use Case 4: Emerging Domestic Prospect Discovery (Diamond-in-the-Rough)
**Primary Actors**: Head of Cricket Operations, Domestic Scout  
**Objective**: Identify uncapped Indian talent in the Syed Mushtaq Ali Trophy exhibiting elite micro-skills prior to the auction pool publication.

```
+-------------------------------------------------------------------------------------------------------+
| USER WORKFLOW 4: EMERGING DOMESTIC TALENT DISCOVERY                                                   |
+-------------------------------------------------------------------------------------------------------+
|  [Step 1] Ingest SMAT Tournament Data into Normalised Staging Tables                                  |
|       |                                                                                               |
|       v                                                                                               |
|  [Step 2] Run Diamond-in-the-Rough Filter: Age <= 23, Base Price <= ₹30L, Balls Faced/Bowled >= 60    |
|       |                                                                                               |
|       v                                                                                               |
|  [Step 3] Apply Cross-Competition Normalisation: Scale SMAT strike rates by 0.88x competition factor  |
|       |                                                                                               |
|       v                                                                                               |
|  [Step 4] Rank Candidates by Micro-Skill Outlier Score (e.g. Powerplay Dot Ball % > 52%)             |
|       |                                                                                               |
|       v                                                                                               |
|  [Step 5] Trigger In-Person Scouting Verification Request & Invite Candidate to Jaipur Trial Camp    |
+-------------------------------------------------------------------------------------------------------+
```

---

## 7. Scope Boundaries: MVP Scope vs Out-of-Scope

To ensure rigorous execution and prevent feature creep, product boundaries are formally partitioned into MVP capabilities, planned post-MVP enhancements, and strictly out-of-scope features.

```
+-------------------------------------------------------------------------------------------------------+
|                                        SYSTEM SCOPE PARTITION                                         |
+-------------------------------------------------------------------------------------------------------+
|  IN SCOPE (MVP - GREENFIELD BASELINE)                                                                 |
|  • Ingestion of CricSheet IPL (1,243 matches) & SMAT (695 matches) files                               |
|  • Central Normalised Relational Database Schema (PostgreSQL 20 Entities)                             |
|  • Multi-Tier Player Identity Resolution (PIR) with CricSheet Hex Registry Mapping                    |
|  • True Strike Rate (TSR) & True Economy Rate (TER) Engine                                            |
|  • Batter vs Bowling Type Tactical Matchup Matrix (6 archetypes)                                      |
|  • Sawai Mansingh Stadium (SMS Jaipur) Profiling & Dew Correlation                                    |
|  • Cumulative Multi-Format Workload & Fatigue Tracker                                                 |
|  • Expected Auction Price (EAP) & T20 WAR Valuation Models (INR 120 Cr Cap)                           |
|  • Playing XI Constraint Solver (BCCI rules: max 4 overseas, 1 WK, 5 bowlers)                         |
|  • 10,000-Run Vectorized Monte Carlo Tournament Simulator                                             |
|  • Diamond-in-the-Rough Domestic Scouting Filter                                                      |
|                                                                                                       |
|  PLANNED (POST-MVP ENHANCEMENTS)                                                                      |
|  • Ingestion of international franchise leagues (BBL, CPL, PSL, SA20)                                 |
|  • HawkeyeStats 3D optical trajectory rendering engine (upon licensing validation)                   |
|  • Automated video broadcast clip indexing linked to delivery timestamps                              |
|  • Real-time speech-to-text bidding assistant for auction room audio transcription                     |
|                                                                                                       |
|  STRICTLY OUT-OF-SCOPE (EXCLUDED / REJECTED)                                                          |
|  • Sub-surface physical IoT soil moisture pitch sensors (physically non-existent in public domain)   |
|  • Live in-stadium optical computer vision broadcast scraping during match play                       |
|  • Wearable biometric telemetry (GPS vests, continuous heart rate, blood lactate tracking)            |
|  • Automated real-time auction bidding execution (system provides decision support only)              |
+-------------------------------------------------------------------------------------------------------+
```

---

## 8. Acceptance Criteria & Hackathon Evaluation Rubric

### 8.1 Verification Criteria Matrix

| Requirement ID | Acceptance Criterion | Verification Method | Pass Threshold |
|---|---|---|---|
| **AC-01** | Full Ingestion of local CricSheet IPL and SMAT files | Automated record counter query against PostgreSQL `matches` table | Exactly 1,243 IPL matches and 695 SMAT matches staged without data loss |
| **AC-02** | Zero Orphan Deliveries | Referential integrity check (`deliveries.match_id` -> `matches.id`) | 0 foreign key violations |
| **AC-03** | Super Over Segregation | Query career batting/bowling totals for players with Super Over appearances | Exactly 0 super over deliveries included in career totals |
| **AC-04** | DLS Target Adjustment | Inspection of run-rate denominator in weather-affected matches (e.g. Match 1082648) | Denominator equals official DLS revised overs (not 20 overs) |
| **AC-05** | Playing XI Regulatory Enforcement | Execution of unit tests attempting to save Playing XIs with 5 overseas players | Hard validation exception raised; 0 invalid XIs saved |
| **AC-06** | Query Latency Benchmark | Automated load testing of player profile and head-to-head API endpoints | $p95 < 200\text{ ms}$ under 50 concurrent requests |
| **AC-07** | Monte Carlo Determinism | Running 10,000 simulations twice with seed `42` | Bit-for-bit identical playoff probability distributions |
| **AC-08** | Missing Value Integrity | Schema audit on `deliveries` table for missing ball speed or coordinates | 100% of missing attributes stored as `NULL`; 0 instances of `0.0` imputation |

### 8.2 Hackathon Scoring Evaluation Rubric

```
+-------------------------------------------------------------------------------------------------------+
|                                    HACKATHON COMPETITIVE SCORING RUBRIC                                |
+-------------------------------+-------+---------------------------------------------------------------+
| Evaluation Dimension          | Score | Target Performance Standard                                   |
+-------------------------------+-------+---------------------------------------------------------------+
| 1. Analytical Depth & Math    | 30/30 | Mathematically sound TSR, TER, WPA, xR, and WAR models with    |
|                               |       | rigorous phase, venue, and competition baselines.             |
| 2. Engineering Architecture   | 25/25 | Fully normalized 20-entity 3NF PostgreSQL schema, sub-200ms   |
|                               |       | latency, deterministic seeds, full source provenance logs.     |
| 3. Domain Validity & Rules    | 20/20 | Flawless compliance with ICC/BCCI rules: Super Over isolation,|
|                               |       | DLS target recalculation, Impact Player mechanics.            |
| 4. UX & Usability             | 15/15 | Intuitive persona-tailored dashboards, live bidding console,   |
|                               |       | 45-second pivot recommender, actionable coach cards.          |
| 5. Innovation & Edge          | 10/10 | Dedicated SMS Jaipur Home Fortress engine and predictive EAP   |
|                               |       | valuation with market scarcity multipliers.                   |
+-------------------------------+-------+---------------------------------------------------------------+
| TOTAL SCORE                   |100/100| MAXIMUM EVALUATION GRADE                                      |
+-------------------------------+-------+---------------------------------------------------------------+
```

---

## 9. Conclusion & Greenfield Baseline Declaration

This Product Requirements Document establishes the definitive operational and analytical specification for the **Rajasthan Royals Squad Intelligence & Historical Performance Engine**. 

In strict adherence to the project integrity mandate:
- All features, algorithms, and modules specified herein represent the **planned target state** (`[STATUS: PLANNED - GREENFIELD BASELINE]`).
- No application code has been pre-implemented or fabricated.
- All subsequent engineering phases (Phase 0 through Phase 8) must validate their deliverables against the requirements, constraints, and acceptance criteria set forth in this document.
