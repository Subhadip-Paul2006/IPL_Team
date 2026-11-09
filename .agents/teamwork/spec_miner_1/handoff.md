# Specification Mining Report: Rajasthan Royals Squad Intelligence & Historical Performance Engine (IPL 2027 Auction Scouting Hackathon)

**Agent**: `teamwork_spec_miner_1`  
**Working Directory**: `d:\New folder (2)\.agents\teamwork\spec_miner_1\`  
**Date**: 2026-11-07T07:22:00Z  
**Parent Orchestrator**: `4c0891e4-b3cf-43e3-bccd-7c9505cc9188`  
**Repository State**: Greenfield Baseline (`d:\New folder (2)`) with local CricSheet archive in `d:\New folder (2)\CricSheet\`  

---

## 1. Observation

Direct physical inspection of `d:\New folder (2)` and authoritative reference sources established the following verified facts:

### 1.1 Repository Structure & Baseline
- **Greenfield Codebase**: Running `Get-ChildItem -Path "d:\New folder (2)" -Force` reveals exactly two top-level directories:
  1. `.agents/` — Subagent coordination workspace and metadata (`ORIGINAL_REQUEST.md`, `orchestrator_1`, `explorer_survey_1`, `spec_miner_1`, `spec_miner_2`).
  2. `CricSheet/` — Pre-existing local raw data repository containing 2,822 match files across 5 tournament subdirectories.
- **Zero Application Code**: No source files (`.py`, `.ts`, `.tsx`, `.js`), no web configuration (`package.json`, `requirements.txt`), no documentation folder (`docs/`), no database migration scripts, and no test suites exist in the workspace root.
- **Workspace Operating System**: Windows, PowerShell terminal, local path `d:\New folder (2)\`.

### 1.2 Local Raw Data Lake Inventory (`CricSheet/`)
Running file enumeration commands across `d:\New folder (2)\CricSheet` yielded:
- `ipl_json/`: 1,245 files (1,243 match JSON files + `README.txt` + `LICENSE.txt`). Schema format is Cricsheet JSON v1.3.0.
- `sma/`: 697 files (695 match YAML files + `README.txt` + `LICENSE.txt`). Schema format is Cricsheet YAML v0.94.
- `icc_mens_t20_world_cup_json/`: 232 files (230 match JSON files + `README.txt` + `LICENSE.txt`). Schema format is Cricsheet JSON v1.3.0.
- `hnd_json/` (The Hundred): 391 files (389 match JSON files + `README.txt` + `LICENSE.txt`). Schema format is Cricsheet JSON v1.3.0.
- `icc_mens_cricket_world_cup/`: 267 files (265 match YAML files + `README.txt` + `LICENSE.txt`). Schema format is Cricsheet YAML v0.94.

### 1.3 Schema & Domain Observations from Raw Records
Direct examination of raw JSON files revealed structural nuances:
1. **Match Chronology & Earliest Record**:
   - Earliest IPL Match: `335982.json`, date `2008-04-18` (Royal Challengers Bangalore vs Kolkata Knight Riders at M. Chinnaswamy Stadium, Bangalore).
   - Latest IPL Match: `1535465.json`, date `2026-05-31` (Gujarat Titans vs Royal Challengers Bengaluru at Narendra Modi Stadium, Ahmedabad, IPL Final).
2. **Player Identity Registry**:
   - Each match JSON includes an `info.registry.people` mapping connecting display names to persistent 8-character hexadecimal hashes (e.g., `A Choudhary: "18e6906e"`, `CH Gayle: "db584dad"`, `Rashid Khan: "5f547c8b"`).
3. **Substitutions and Impact Player Rules**:
   - Deliveries in match `1535465.json` record the modern Impact Player rule under delivery metadata:
     `"replacements": { "match": [ { "in": "VR Iyer", "out": "JA Duffy", "team": "Royal Challengers Bengaluru", "reason": "impact_player" } ] }`.
   - Substitute fielders involved in dismissals are explicitly flagged: `"wickets": [ { "kind": "run out", "player_out": "YS Chahal", "fielders": [ { "name": "CJ Jordan", "substitute": true } ] } ]`.
4. **Super Overs**:
   - In matches tied at 20 overs (e.g. `1082625.json`, Gujarat Lions vs Mumbai Indians), super overs are represented as distinct entries in the `innings` array with `"super_over": true`.
5. **Rain-Interrupted Matches (DLS)**:
   - In weather-affected matches (e.g. `1082648.json`), `info.outcome.method` is `"D/L"` or `"DLS"`, and the second innings contains an explicit target object: `"target": { "overs": 6, "runs": 48 }`.
6. **Licensing**:
   - `CricSheet/ipl_json/LICENSE.txt` confirms CricSheet is licensed under the **Open Data Commons Attribution License (ODC-By) v1.0**.

---

## 2. Logic Chain

1. **Premise 1 (Mission & Integrity Constraint)**: The objective is to produce engineering-grade specifications and documentation for the Rajasthan Royals Squad Intelligence & Historical Performance Engine (IPL 2027 Auction). The workspace is greenfield; no code, synthetic data, or external scraping can be executed.
2. **Premise 2 (Authoritative Evidence vs Discrepancies)**:
   - The verified IPL launch date is 2008-04-18 (`335982.json`). Therefore, Kaggle datasets claiming "IPL 2007–2026" contain a temporal anomaly (IPL did not exist in 2007). Any 2007 records must be flagged as non-IPL T20 or misattributed.
   - HawkeyeStats ball-tracking data provides delivery speeds and trajectory coordinates, but coverage is non-universal and third-party. The database schema must treat trajectory coordinates as nullable optional enrichment, never imputing missing values as 0.
   - Open-Meteo provides macro-meteorological measurements (air temp, relative humidity, dew point), which correlate with dew factors during night matches, but physically cannot represent pitch compaction or sub-surface soil moisture.
3. **Premise 3 (Domain-Driven Analytical Architecture)**:
   - Rajasthan Royals requires decision-support tailored to the 2027 mega-auction (budget cap INR 120 Cr, overseas caps, RTM rules, squad of 18–25 players).
   - T20 analytics cannot rely on raw batting/bowling averages. True Strike Rate (TSR) and True Economy Rate (TER) must be computed relative to tournament and match phase pars (Powerplay [overs 1–6], Middle [7–15], Death [16–20]).
   - Venue profiling must specifically model the Sawai Mansingh Stadium (SMS Jaipur) conditions: large square boundaries, high boundary running requirements, daytime heat degradation, and evening dew.
4. **Premise 4 (System Documentation Requirements)**:
   - To guide subsequent engineering phases, 5 core documents must be specified in full:
     - `README.md` (root and docs/): Executive overview, navigation, tech stack, roadmap, greenfield status.
     - `PRD.md`: Personas, user journeys, functional modules, NFRs, acceptance criteria, hackathon evaluation rubric.
     - `PHASES.md`: Phase 0 through Phase 8 implementation roadmap with gates, deliverables, and verification tests.
     - `AGENTS.md`: Full specifications for 14 specialized AI engineering agents with strict boundaries.
     - `AI_INSTRUCTIONS.md`: Constitution covering conventions, statistical rules, missing-value protocols, and strict prohibitions.
5. **Deduction & Synthesis**:
   - The specification miner must formally enumerate every functional capability, persona requirement, non-functional threshold, document requirement, data source audit point, and agent contract into comprehensive, structured matrices.

---

## 3. Features Discovered

| # | Category | Feature | Description | Inputs | Outputs | Error Behavior | Discovered Via |
|---|----------|---------|-------------|--------|---------|----------------|----------------|
| F01 | Match Impact | Ball-by-Ball Context Valuation | Calculates Context-Adjusted Strike Rate (True Strike Rate) and Context-Adjusted Economy Rate (True Economy) against phase-specific baseline pars. | Ball delivery record (runs, extras, batter, bowler, over, innings, match phase) | True SR (+/- vs par), True Econ (+/- vs par), Run Value Added (RVA) | If phase par unavailable, flag as UNVERIFIED; do not divide by zero. | Cricsheet delivery schema & T20 analytics literature |
| F02 | Match Impact | Win Probability Added (WPA) & xR | State-based Win Probability model evaluating each ball's shift in win expectancy based on required run rate, wickets lost, and historical chase curves. | Innings, balls remaining, runs required, wickets in hand, target score | Delta Win Probability ($\Delta$WP) per delivery, cumulative match WPA | Return NULL if target or innings state corrupted; do not default to 50%. | Cricsheet innings outcome & target metadata |
| F03 | Match Impact | Clutch Index & Leverage Analysis | Measures player performance in high-pressure match situations (Leverage Index > 1.5, death chases, playoff knockouts, low-score defenses). | Delivery leverage score, pressure index, match stage (group vs playoff) | Clutch Rating (0–100 percentile score), High-Leverage Strike Rate/Economy | If sample size < 30 high-leverage deliveries, tag "Small Sample Warning". | CricSheet `info.event.stage` (Eliminator/Final) |
| F04 | Venue Profiling | Pitch & Ground Behavioral Profiling | Classifies pitch characteristics (red soil vs black soil, bounce, seam movement, spin turn rate) and ground geometry (boundary distance leg/off/straight). | Venue name, city, boundary dimensions, historical innings totals | Pitch Type Classifier, Average 1st Innings Par Score, Boundary Ease Index | If venue unmapped, assign default neutral venue profile and log warning. | Venue records & BCCI ground registries |
| F05 | Venue Profiling | Sawai Mansingh Stadium (SMS Jaipur) Engine | Dedicated home ground analytical module modeling Jaipur's specific conditions (large outfield, long square boundaries, dew dynamics, high pace utility). | SMS historical match deliveries, daytime vs night fixture flags, toss decision | Home Ground Advantage Index, SMS Phase Run-Rate Pars, Optimal Jaipur Bowling Mix | Fallback to SMS 5-year aggregate if single-season sample is sparse. | Rajasthan Royals home venue requirements |
| F06 | Venue Profiling | Environmental & Dew Factor Correlation | Integrates Open-Meteo macro-weather (temperature, relative humidity, dew point, wind speed) to predict second-innings dew impact on bowling grip and boundary frequency. | Match date, venue latitude/longitude, start time, Open-Meteo weather logs | Dew Risk Indicator (Low/Med/High), Expected 2nd Innings Grip Degradation Factor | Macro weather data must never be labeled as direct pitch moisture sensors. | Open-Meteo API spec & ORIGINAL_REQUEST.md R2 |
| F07 | Tactical Matrix | Batter vs Bowling Type Profiling | Matrix evaluating batting proficiency against 6 distinct bowling archetypes (RAF, LAF, OS, SLA, LBG, LAC) across match phases. | Batter ID, deliveries faced, bowler primary style, runs scored, dismissals | Strike Rate, Dot Ball %, Boundary %, Dismissal Frequency per bowling archetype | When deliveries faced < 18 vs specific style, flag "Insufficient Data". | CricSheet delivery + bowler style enrichment |
| F08 | Tactical Matrix | Head-to-Head Batter vs Bowler Matrix | Granular historical matchup analysis between specific individual batters and bowlers. | Batter ID, Bowler ID, delivery logs | Balls faced, runs conceded, dismissals, dot ball count, false shot / edge % | Return empty matrix with "Zero Head-to-Head History" if no past encounters. | CricSheet `batter` and `bowler` delivery fields |
| F09 | Tactical Matrix | Pitch Trajectory & Length Vulnerability | Evaluates player vulnerability to specific delivery lengths (yorker, full, good, back of length, short) and lines (outside off, stumps, down leg). | HawkeyeStats ball tracking coordinates (release speed, landing x/y coordinates) | Heatmaps of scoring zones, dismissal clusters, dot ball choke points | If Hawkeye data absent, gracefully degrade to text line/length commentary; DO NOT impute 0,0 coordinates. | HawkeyeStats reference & AI_INSTRUCTIONS.md |
| F10 | Workload & Fatigue | Cumulative Multi-Format Workload Engine | Tracks cumulative overs bowled, deliveries faced, and spells across IPL, Syed Mushtaq Ali, ICC tournaments, and international bilateral series. | Multi-tournament match records (IPL, SMA, T20 WC, CWC, The Hundred) | 30-day / 90-day / 365-day Cumulative Overs Bowled, High-Workload Alert Flag | Tag records as partial if domestic tournament data coverage is incomplete. | CricSheet multi-tournament local datasets |
| F11 | Workload & Fatigue | Schedule Congestion & Travel Strain | Quantifies performance degradation resulting from compressed rest intervals (< 48 hours) and multi-city transits during IPL campaign. | Fixture schedule dates, travel distance between host cities, match start times | Fatigue Index, Back-to-Back Match Performance Delta | Return neutral fatigue score if schedule dates unavailable. | CricSheet `info.dates` & city location data |
| F12 | Workload & Fatigue | Injury History & Availability Logging | Maintains player availability logs, historical injury downtime (stress fractures, muscle strains), and NOC/national duty restrictions. | Player ID, medical bulletin records, national board NOC schedules | Availability Probability (0–1.0), Injury Risk Tier (Low/Medium/High) | If injury log unverified, mark as UNVERIFIED; never assume full fitness. | Research sources & TRD schema `player_injuries` |
| F13 | Auction Valuation | Expected Auction Price (EAP) Modeling | Predictive regression/valuation modeling estimating player market clearing price at IPL 2027 Auction based on performance, role scarcity, and market inflation. | Player age, past 3 seasons True SR/Econ, international caps, role category, purse cap (INR 120 Cr) | Expected Auction Price (INR Crores), Valuation Range (Floor, Median, Ceiling) | Clamp output between base price (e.g. INR 30L/50L/2Cr) and purse maximum. | Auction Strategist persona requirements |
| F14 | Auction Valuation | Replacement Player Value (WAR) | Calculates Wins Above Replacement (WAR) customized for T20 cricket, measuring total win contributions above a league-minimum baseline player. | Batting WPA, Bowling WPA, Fielding WPA, Replacement Level Baseline | T20 WAR score, Net Win Contribution | Return baseline 0.0 WAR if zero appearances. | Sports analytics sabermetric principles |
| F15 | Auction Valuation | Role Scarcity & Premium Multipliers | Applies market scarcity multipliers for rare player archetypes (e.g., 140+ km/h pace bowling all-rounders, elite death-overs finishers, mystery spinners). | Player role, secondary skill proficiency, market supply counts | Scarcity Index, Adjusted Valuation Premium (%) | Default multiplier to 1.0 (neutral) if player skill classification ambiguous. | IPL auction historical spending trends |
| F16 | Squad Simulation | Playing XI Optimizer with IPL Regulatory Constraints | Optimization algorithm generating valid playing XIs adhering to IPL rules: max 4 overseas players, at least 1 wicketkeeper, minimum 5 bowling options. | Squad roster (18–25 players), player fitness, opposition matchup, venue profile | Optimal Playing XI, Designated 5 Impact Player Substitutes, Batting Order | Reject any combination exceeding 4 overseas players with hard validation error. | IPL Playing Conditions & PRD.md |
| F17 | Squad Simulation | Impact Player Tactical Deployment Engine | Tactical decision engine determining optimal Impact Player substitutions based on match state (batting first vs chasing, early collapse vs high platform). | Match phase, wickets fallen, run rate, bench options, CricSheet replacement records | Recommended Substitution, Target Innings Delivery Window, Expected Net Run Differential | Enforce 1 substitution per match per team limit. | CricSheet `"reason": "impact_player"` discovery |
| F18 | Squad Simulation | Monte Carlo Tournament Simulator | Simulates tournament campaigns (14 league matches + playoffs) across 10,000 runs to project expected league points, playoff probability, and NRR under squad configurations. | Playing XI ratings, venue schedule, injury shock probability distribution | Projected Wins, Playoff Qualification Probability (%), Championship Probability (%) | Set seed for deterministic reproducibility; report 95% confidence intervals. | Non-functional requirements (deterministic reproducibility) |
| F19 | Talent Scouting | Cross-Competition Normalisation Engine | Normalises statistical performance across different competitive tiers (Syed Mushtaq Ali Trophy, U-19 World Cup, The Hundred) to IPL equivalency. | Domestic ball-by-ball records, competition difficulty coefficient | IPL-Adjusted Strike Rate, IPL-Adjusted Economy Rate, Equivalency Score | If tournament coefficient uncalibrated, tag metric as "Raw Unadjusted". | CricSheet SMA, HND, T20 WC data archives |
| F20 | Talent Scouting | Diamond-in-the-Rough Scouting Filter | Algorithmic filter surfacing undervalued domestic talent exhibiting elite specialized micro-skills (Powerplay dot ball %, boundary-hitting under pressure). | Player age <= 24, domestic T20 records, base auction price bracket | Filtered Candidate List, Skill Archetype Match Score, Value-to-Cost Ratio | Suppress candidates with < 5 domestic matches or < 60 balls faced. | RR Hackathon Scouting Mandate |
| F21 | Identity Resolution | Multi-Source Player Entity Disambiguation | Resolves player names across diverse formats (e.g., "R Uthappa", "Robin Uthappa", "R V Uthappa", "SV Samson", "Sanju Samson") into unique canonical IDs. | Source player name, team, match date, CricSheet hex registry ID | Canonical Player ID, Master Name, Aliases Table Record | Flag confidence < 0.90 for manual human review; NEVER merge distinct players. | CricSheet `info.registry.people` & TRD schema |
| F22 | Data Ingestion | Multi-Format Parser (JSON v1.3.0 & YAML v0.94) | Ingestion pipeline supporting both CricSheet JSON and YAML match schemas without data loss. | Raw file stream (.json or .yaml) | Raw Staging Record, Source Metadata, Ingestion Audit Log | Log parser error and quarantine malformed files without terminating pipeline. | Direct discovery of JSON and YAML files in CricSheet |
| F23 | Data Ingestion | DLS Par & Revised Target Reconciler | Reconciles rain-affected match deliveries against adjusted overs and revised targets to avoid penalizing or skewing bowler/batter economy and strike rates. | Match D/L flag, revised target runs, revised overs | Adjusted Balls Remaining, Normalized Required Run Rate | Abort DLS calculation if official target data is missing; flag as UNVERIFIED. | CricSheet D/L target schema discovery |
| F24 | Historical Analytics | Super Over Isolation & Reconciliation | Segregates super over deliveries into distinct analytical containers so they do not contaminate career averages while preserving match outcome lineage. | Innings records with `super_over: true` | Super Over Performance Card, Isolated Career Aggregates | Hard assertion: Super over runs/wickets must NEVER increment official career totals. | ICC/BCCI statistics rules & CricSheet schema |
| F25 | Quality & Validation | Automated Lineage & Data Provenance Tracker | Attaches source tracking metadata to every derived feature, mapping from final UI metrics back to raw delivery and match files. | Derived metric calculation job | Provenance Manifest (Source file, Ingestion timestamp, Hash, Normalisation rule) | Fail build if derived feature has broken foreign key lineage. | AI_INSTRUCTIONS.md & R4 requirements |

---

## 4. Edge Cases

| # | Feature | Input | Observed Behavior |
|---|---------|-------|-------------------|
| E01 | Player Identity Resolution | Common abbreviated names (e.g., "R Sharma" representing Rohit Sharma vs Rahul Sharma). | Name collision hazard. Disambiguation engine must cross-reference `info.registry.people` hex hashes, bowling/batting roles, and playing teams. If hex absent, require human verification flag rather than arbitrary resolution. |
| E02 | Super Over Career Statistics | Match goes to Super Over (e.g. `1082625.json`, 2017 Gujarat Lions vs Mumbai Indians). | Deliveries have `"super_over": true`. If naive aggregator sums all innings, super over balls distort career averages. System must filter out super over innings from career T20 averages while indexing them in match clutch history. |
| E03 | Substitute Fielders in Dismissals | Substitute fielder executes catch or run out (e.g. CJ Jordan in match `1082591.json` delivery 18.6). | CricSheet marks `fielders: [{ "name": "CJ Jordan", "substitute": true }]`. CJ Jordan was not in the starting playing XI. The fielding events table must link the dismissal to the player without violating foreign key constraints on `squad_memberships` or playing XI status. |
| E04 | Rain-Interrupted Target Calculation (DLS) | Second innings truncated to 6 overs with target of 48 (e.g. `1082648.json`, KKR vs SRH). | Naive run-rate models assume 20-over denominator (2.4 RPO) instead of revised 6-over quota (8.0 RPO required). Engine must ingest `info.outcome.target` to calculate true pressure index and win expectancy. |
| E05 | In-Match Impact Player Substitution | Modern match with Impact Player (e.g. `1535465.json`, delivery with `replacements: { match: [{ in: "VR Iyer", out: "JA Duffy", reason: "impact_player" }] }`). | Total players participating in match exceeds 11 per team (up to 12). Schema and squad simulation must support exactly 1 tactical replacement per team per match, maintaining correct participation credits. |
| E06 | Kaggle 2007 Temporal Anomaly | Dataset file claiming IPL records from 2007 (`Kaggle IPL Ball-by-Ball 2007-2026`). | The inaugural IPL match was April 18, 2008 (Match `335982.json`). Any delivery dated prior to 2008-04-18 is either ICC World T20 2007 or invalid tagging. Ingestion validator must reject or quarantine 2007 data as ANOMALOUS. |
| E07 | HawkeyeStats Delivery Coordinate Gaps | Deliveries where optical ball tracking was unavailable due to broadcast occlusion or sensor drop. | Pitch x/y coordinates and release speed fields are NULL. If code imputes missing coordinates as (0.0, 0.0), ball is plotted in the exact geometric center of the pitch (middle stump). Must remain strictly NULL. |
| E08 | Macro Weather vs Pitch Microclimate | High ambient humidity (92%) recorded by Open-Meteo at 19:30 IST in Jaipur. | Dew formation on outfield reduces bowling seam grip, but does NOT alter soil compaction or pitch moisture beneath the pitch cover. Engine must tag macro weather as environmental context only and prohibit claims of direct pitch sensors. |
| E09 | Foreign Player Quota in Squad Simulation | User simulates squad selection with 5 overseas players in playing XI. | Violates IPL Playing Conditions Rule 1.2 (maximum 4 overseas players permitted in playing XI). Playing XI solver must trigger hard validation exception and prune candidate state tree. |
| E10 | Zero Balls Faced / Zero Overs Bowled | Player listed on team sheet but does not bat or bowl throughout match (DNB). | Batting average and economy rate denominators are zero. System must return NULL / "-" (DNB/DNBowl), never 0.0 or infinity, and must not drop player from appearance counts. |
| E11 | Multi-Format Ingestion (JSON vs YAML) | Pipeline processes `ipl_json` (JSON v1.3.0) and `sma` (YAML v0.94). | CricSheet data formats differ: JSON uses nested dictionaries with `overs` list, while older YAML uses key-value maps with decimal delivery keys (e.g., `0.1: { ... }`). Ingestion engine requires polymorphic adapters per file extension. |
| E12 | Tie Matches Without Super Over | Early IPL matches or rain abandonments resulting in "No Result" or bowl-out (e.g. 2008 rain-abandoned fixtures). | `info.outcome.result` is "no result" or outcome has no winning team. WPA calculation must assign 0 delta to all deliveries and mark match outcome as null in league ladder projections. |

---

## 5. Comprehensive Specification & Requirements Breakdown

### 5.1 Product & Engineering Scope

#### 5.1.1 Vision & Problem Statement
- **Vision**: To build an engineering-grade, forensically audited Squad Intelligence and Historical Performance Engine designed specifically for the Rajasthan Royals franchise ahead of the IPL 2027 Mega-Auction, transforming raw ball-by-ball multi-tournament records into actionable tactical intelligence, robust player valuation models, and compliant squad optimization simulations.
- **Problem Statement**: Traditional IPL scouting relies heavily on superficial aggregates (raw batting average, overall strike rate, total wickets) that suffer from extreme contextual bias (e.g., scoring at Chinnaswamy vs Chepauk, batting in powerplay vs death overs, stat-padding in dead rubbers). Furthermore, auction dynamics require balancing severe regulatory constraints (purse ceiling, overseas limits, mandatory roles) with market scarcity. Decision-makers lack a unified, traceable system connecting ball-by-ball mechanics to auction bidding room decisions.

#### 5.1.2 Target Personas & Core Journeys
1. **Lead Cricket Analyst**:
   - *Needs*: Granular phase-wise splits (Powerplay, Middle, Death), context-adjusted strike rates, delivery length/line heatmaps, batter vs bowler type matchup matrices, and raw delivery traceability.
   - *Core Journey*: Queries candidate player -> filters by phase and bowling style -> inspects False Shot % and True Strike Rate against 140+ km/h pace -> exports tactical brief for coaching staff.
2. **Head of Cricket Operations**:
   - *Needs*: High-level squad balance dashboard, multi-year squad composition, domestic scouting pipeline visibility (Syed Mushtaq Ali Trophy, U-19 World Cup), and regulatory compliance verification.
   - *Core Journey*: Reviews current squad vacancies -> filters emerging domestic prospects with high IPL equivalency scores -> verifies overseas roster limit (<= 8) and domestic bench strength.
3. **Auction Strategist**:
   - *Needs*: Predictive Expected Auction Price (EAP) models, bidding ceiling recommendations, Wins Above Replacement (WAR) metrics, role scarcity multipliers, and budget allocation scenarios under an INR 120 Cr purse cap.
   - *Core Journey*: Sets auction budget scenario -> inputs target player list -> simulates bidding escalation curves -> receives real-time pivot recommendations when target player exceeds ceiling price.
4. **Bowling & Batting Coaches**:
   - *Needs*: Granular tactical weakness maps, venue-specific pitch adaptation strategies (specifically Sawai Mansingh Stadium / SMS Jaipur home conditions), workload/fatigue monitoring, and opposition plan formulation.
   - *Core Journey*: Selects upcoming opposition batter -> analyzes dismissal modes against left-arm pace at SMS Jaipur -> generates line/length execution plan for fast bowlers.
5. **Chief Executive & Franchise Ownership**:
   - *Needs*: Executive summary cards, squad valuation ROI, long-term talent sustainability, marquee vs value pick distribution, and risk mitigation reports (injury history, national availability flags).
   - *Core Journey*: Reviews auction master plan -> inspects budget headroom and foreign player NOC risks -> approves finalized auction bidding brackets.

#### 5.1.3 Core Analytical Modules
1. **Match Impact Engine**: Computes True Strike Rate (TSR), True Economy Rate (TER), Win Probability Added (WPA), Expected Runs (xR), Leverage Index (LI), and Clutch Index across all match situations.
2. **Venue Profiling & Environmental Engine**: Models venue-specific pitch behavior, boundary dimension asymmetry, daytime vs night splits, SMS Jaipur home fortress dynamics, and Open-Meteo macro-weather/dew correlations.
3. **Matchup & Tactical Weakness Matrix**: Profiles batter vs bowling styles (RAF, LAF, OS, SLA, LBG, LAC), head-to-head individual battles, delivery length/line vulnerability grids, and dismissal modes.
4. **Fatigue, Workload & Injury Tracking Engine**: Aggregates multi-tournament bowling workloads, days between fixtures, travel fatigue, and historical medical/injury availability logs.
5. **Auction Valuation & Market Economics Engine**: Computes Expected Auction Price (EAP), Wins Above Replacement (WAR), role scarcity premiums, and purse optimization under an INR 120 Cr budget.
6. **Squad Simulation & Monte Carlo Scenario Engine**: Generates optimal playing XIs conforming to IPL rules (max 4 overseas, wicketkeeper, 5 bowlers, Impact Player rule), and executes 10,000 tournament Monte Carlo simulations to project playoff and championship probabilities.
7. **Talent Scouting Pipeline (Domestic & Emerging)**: Implements cross-tournament normalisation (SMA, U-19, The Hundred to IPL equivalency) and automated diamond-in-the-rough discovery filters for emerging talent.

#### 5.1.4 Non-Functional Requirements (NFRs)
- **NFR-1 (Query Latency)**: Player search and head-to-head matchup queries must return in p95 < 200ms; multi-parameter squad simulation must complete in < 3,000ms.
- **NFR-2 (Accuracy & Zero Fabrication)**: Zero synthetic or hallucinated statistics. All metrics must be mathematically derivable from verified raw delivery records. Missing values (e.g. ball speed) must remain NULL; never impute zero.
- **NFR-3 (Deterministic Reproducibility)**: Given identical raw input records and model parameters, all derived statistics and valuation models must produce bit-for-bit identical results across environments.
- **NFR-4 (Traceability & Lineage)**: Every derived metric presented in the system must be linked via foreign keys and provenance metadata to source file IDs and raw delivery records.
- **NFR-5 (Concurrency & Availability)**: Dashboard APIs must support read-heavy access patterns during live auction room operations with connection pooling and caching.

---

### 5.2 Document Requirements

#### 5.2.1 Root `README.md`
- **Purpose**: Executive gateway and index to the entire repository and documentation suite.
- **Required Sections**:
  1. Project Title & Overview: Rajasthan Royals Squad Intelligence & Historical Performance Engine (IPL 2027 Auction Scouting Hackathon).
  2. Hackathon Objectives & Strategic Context.
  3. Vision & Problem Statement.
  4. Core Analytical Modules Summary.
  5. Architecture Summary & High-Level System Diagram.
  6. Technology Stack Specification: Python 3.11+, PostgreSQL 16+, FastAPI, Pandas/NumPy, Next.js 14, Tailwind CSS, React Flow / Cytoscape.js, Recharts / Apache ECharts.
  7. Greenfield Repository Baseline Declaration (explicitly noting no application code currently exists).
  8. Directory Layout & Complete Documentation Index linking directly to all files in `docs/` (`docs/README.md`, `docs/PRD.md`, `docs/TRD.md`, `docs/ARCHITECTURE.md`, `docs/PHASES.md`, `docs/AGENTS.md`, `docs/AI_INSTRUCTIONS.md`).
  9. Verification & Execution Instructions (setup, database seeding, test execution).
  10. Current Implementation Status vs Planned Roadmap.
  11. Data Attribution & Licensing (Cricsheet ODC-By v1.0, Kaggle CC BY-SA, Open-Meteo).

#### 5.2.2 `PRD.md` (Product Requirements Document)
- **Purpose**: Comprehensive product specification defining functional capabilities, user personas, workflows, and success metrics.
- **Required Sections**:
  1. Executive Summary & Product Vision.
  2. Stakeholder & User Persona Profiles (Lead Analyst, Head of Cricket Ops, Auction Strategist, Bowling/Batting Coaches, Chief Executive).
  3. Hackathon Strategic Mandate & Evaluation Rubric:
     - Scouting Accuracy & Analytical Depth (30%)
     - System Architecture & Engineering Robustness (25%)
     - Domain Validity & Cricket Logic (20%)
     - UX, Usability & Actionability (15%)
     - Innovation & Auction Edge (10%)
  4. Detailed Functional Requirements (FR-01 through FR-25) mapped to analytical modules.
  5. User Workflows & Core Use Cases:
     - Use Case 1: Pre-Auction Target Shortlisting & Valuation.
     - Use Case 2: In-Auction Real-Time Pivot Strategy.
     - Use Case 3: Opposition Matchup & Tactical Game-Planning.
     - Use Case 4: Emerging Domestic Prospect Discovery.
  6. Non-Functional Requirements (Performance, Security, Reliability, Accuracy).
  7. MVP Scope vs Deferred / Out-of-Scope Capabilities:
     - MVP: Ingestion of IPL & SMA datasets, Central Normalized Schema, True SR/Econ, Matchup Matrix, Basic Auction Valuation, Playing XI Validator.
     - Deferred: Real-time broadcast video streaming ingestion, custom wearable biometric telemetry, live in-stadium pitch moisture sensor network.
  8. Acceptance Criteria & Success Metrics.

#### 5.2.3 `PHASES.md` (Engineering Implementation Roadmap)
- **Purpose**: Phase-by-phase implementation schedule defining tasks, deliverables, checkpoints, verification methods, and status tracking.
- **Required Phase Breakdown (Phase 0 to Phase 8)**:
  - **Phase 0: Research, Audit & Baseline Setup**
    - *Tasks*: Data source licensing audit, greenfield environment validation, documentation suite generation.
    - *Deliverables*: Approved documentation suite in `docs/`, baseline verification report.
    - *Verification*: Markdown syntax checks, Mermaid diagram rendering tests.
  - **Phase 1: Raw Data Acquisition & Quarantine Lake**
    - *Tasks*: Ingestion of local CricSheet datasets (IPL, SMA, T20 WC, CWC, Hundred), validation of Kaggle 2007 anomaly, raw storage staging.
    - *Deliverables*: Ingestion scripts, raw parquet/JSON staging lake, checksum validation manifests.
    - *Verification*: File count validation (1,243 IPL matches, 695 SMA matches), schema integrity checks.
  - **Phase 2: Database Schema & Normalisation Pipeline**
    - *Tasks*: Deploy PostgreSQL 20-table schema, implement ELT parsing pipeline, execute Player Identity Resolution (PIR) algorithm.
    - *Deliverables*: DDL migration scripts, normalisation pipeline, canonical player registry with alias mappings.
    - *Verification*: Foreign key integrity tests, zero orphan delivery records, PIR precision > 99.5%.
  - **Phase 3: Contextual & Environmental Enrichment**
    - *Tasks*: Ingest Open-Meteo historical weather, classify pitch and venue properties, tag match phases (Powerplay, Middle, Death), integrate HawkeyeStats ball tracking if verified.
    - *Deliverables*: Enriched delivery tables, venue profile tables, weather context tables.
    - *Verification*: Null checks on optional fields, boundary coordinate sanity bounds.
  - **Phase 4: Player Profiles & Core Statistical Engine**
    - *Tasks*: Compute True Strike Rate, True Economy Rate, Win Probability Added (WPA), Expected Runs (xR), and phase-wise splits.
    - *Deliverables*: `derived_features` computation pipeline, player career profile service.
    - *Verification*: Unit tests against official cricket records, super over exclusion tests.
  - **Phase 5: Historical Intelligence & Tactical Matchup Engine**
    - *Tasks*: Implement Batter vs Bowling Type matrix, head-to-head individual matchup queries, delivery length/line heatmaps, and SMS Jaipur home venue profiling.
    - *Deliverables*: Matchup API endpoints, pitch heatmaps, venue advantage indexes.
    - *Verification*: Query latency benchmarks (< 200ms p95), matchup consistency tests.
  - **Phase 6: Squad Intelligence, Fatigue & Workload Engine**
    - *Tasks*: Multi-format cumulative workload tracking, days-between-games fatigue modeling, injury downtime logs, and squad balance scoring.
    - *Deliverables*: Workload tracking engine, squad balance index calculator.
    - *Verification*: Cumulative overs reconciliation across tournament tables.
  - **Phase 7: Auction Valuation & Candidate Evaluation Engine**
    - *Tasks*: Expected Auction Price (EAP) predictive models, T20 Wins Above Replacement (WAR), role scarcity premiums, purse budget optimizer.
    - *Deliverables*: Auction valuation engine, candidate recommendation ranking service.
    - *Verification*: Backtesting EAP model on historical 2024/2025 auction clearing prices.
  - **Phase 8: Dashboard UI, Squad Simulation & Submission**
    - *Tasks*: Next.js web application, interactive tactical dashboards, Monte Carlo tournament simulator, playing XI optimization with IPL rules, final submission packaging.
    - *Deliverables*: Fully functional web UI, Monte Carlo simulator, demo screencast, final audit report.
    - *Verification*: End-to-end integration tests, mobile responsiveness, Lighthouse score > 90.

#### 5.2.4 `AGENTS.md` (Multi-Agent Operating Constitution)
- **Purpose**: Formal specification of the 14 specialized AI engineering agents, defining authority boundaries, inputs, outputs, dependencies, constraints, and handoff protocols.
- **Required Specification for All 14 Agents**:
  1. `Chief Architect`: Overall system design, architectural governance, schema approval, cross-agent conflict resolution.
  2. `Cricket Research Specialist`: Domain validation, cricket rule compliance (DLS, Super Over, Impact Player), tactical metric definitions.
  3. `Data Source Audit Agent`: Licensing compliance, dataset provenance verification, anomaly detection (e.g. Kaggle 2007 issue).
  4. `Dataset Acquisition Agent`: Staging raw files, schema validation on ingestion, checksum generation.
  5. `Data Normalisation Engineer`: Relational database loading, ETL/ELT pipeline, delivery-to-match integrity, table population.
  6. `Player Identity Resolution (PIR) Specialist`: Disambiguating player names, registry hash matching, maintaining alias tables.
  7. `Contextual Enrichment Agent`: Weather data integration, venue profiling, pitch condition modeling, match phase tagging.
  8. `Cricket Statistics Specialist`: Implementation of True SR/Econ, WPA, xR, boundary %, dot ball %, leverage calculations.
  9. `Historical Performance Analysis Agent`: Long-term trend analysis, aging curves, multi-season consistency, opposition adjustments.
  10. `Data Quality & Validation Agent`: Automated sanity checking, negative value detection, foreign key audits, veto authority on bad data.
  11. `Backend Engineering Specialist`: FastAPI API development, database query optimization, indexing, caching, calculation pipelines.
  12. `Frontend Engineering Specialist`: Next.js UI, Tailwind CSS styling, Recharts/ECharts visualization, Cytoscape/React Flow graph views.
  13. `Documentation Specialist`: Maintenance of markdown documentation suite, version control of specifications, README synchronization.
  14. `Testing & QA Engineer`: Unit testing, integration testing, synthetic benchmark generation, end-to-end test verification.

#### 5.2.5 `AI_INSTRUCTIONS.md` (Agent Constitution & Guardrails)
- **Purpose**: Centralized code of conduct, statistical guardrails, coding standards, and strict prohibitions for all AI agents.
- **Required Sections**:
  1. Core Architectural Tenets (Modularity, Separation of Concerns, Single Source of Truth).
  2. Coding & Technology Standards (Python 3.11+ PEP 8, TypeScript strict mode, PostgreSQL SQL ANSI, Git conventions).
  3. Data Provenance & Lineage Protocols (Attribution requirements, audit trails).
  4. Statistical Correctness Guardrails:
     - Never treat missing values as zero (e.g. unknown ball speed is NULL, not 0 km/h).
     - Never fabricate or hallucinate player statistics.
     - Never confuse bowling style (e.g. Right-arm Offbreak) with delivery variation (e.g. carrom ball, doosra).
     - Never interpret Hawk-Eye post-shot ball tracking landing coordinates as fielder coordinates.
     - Never include Super Over stats in career T20 averages.
     - DLS rain-affected innings must use revised targets for pressure and run-rate metrics.
  5. Strict Prohibitions:
     - Prohibition against generating synthetic player records.
     - Prohibition against running unauthorized external scraping scripts.
     - Prohibition against altering historical raw records in the quarantine lake.
     - Prohibition against violating IPL playing conditions (e.g. > 4 overseas players).

---

### 5.3 Reference Data Sources Audit & Specification

| Data Source | Type & Format | Physical State in Workspace | Verified Coverage | Licensing & Access Terms | Provenance & Quality Caveats |
|-------------|---------------|-----------------------------|-------------------|--------------------------|------------------------------|
| **Cricsheet IPL Dataset** | Match-by-match JSON (v1.3.0) | Present at `CricSheet/ipl_json/` (1,243 match JSONs) | Complete IPL history: 2008-04-18 (Match 335982) to 2026-05-31 (Match 1535465). | Open Data Commons Attribution License (ODC-By) v1.0. Commercial/open use permitted with attribution. | Highest reliability gold standard. Includes player registry hashes (`info.registry.people`), dismissal fielders, impact player substitutions, and DLS targets. |
| **Cricsheet SMA Dataset** | Match-by-match YAML (v0.94) | Present at `CricSheet/sma/` (695 match YAMLs) | Domestic Indian T20 (Syed Mushtaq Ali Trophy) matches up to December 2024. | ODC-By v1.0. Attribution required. | YAML v0.94 requires dedicated parser adapter different from JSON v1.3.0. Essential for domestic scouting pipeline. |
| **Cricsheet ICC T20 WC & CWC** | Match JSON (v1.3.0) & YAML (v0.94) | Present at `CricSheet/icc_mens_t20_world_cup_json/` (230 files) & `icc_mens_cricket_world_cup/` (265 files) | Men's T20 World Cups & 50-over World Cups. | ODC-By v1.0. Attribution required. | High-quality international baseline for calibration of global player performance against elite competition. |
| **Cricsheet The Hundred** | Match JSON (v1.3.0) | Present at `CricSheet/hnd_json/` (389 match JSONs) | The Hundred (100-ball competition) matches. | ODC-By v1.0. Attribution required. | Requires 100-ball to 120-ball T20 equivalency normalisation rules (5-ball ends vs 6-ball overs). |
| **Kaggle IPL Complete (2008–2020)** | Flat CSVs (`matches.csv`, `deliveries.csv`) | Not present locally (Reference spec only) | 2008 to 2020 IPL seasons. | Creative Commons Attribution 4.0 (CC BY 4.0). | Good for cross-validation of umpire names and city attributes, but lacks player registry hashes and modern impact player structures. |
| **Kaggle IPL Ball-by-Ball (2007–2026)** | Flat CSV / Dataset | Not present locally (Reference spec only) | Claimed 2007–2026 coverage. | Open Kaggle terms (CC BY-SA). | **ANOMALY DETECTED**: Claims 2007 IPL data, whereas IPL officially commenced on April 18, 2008. Ingestion must filter/quarantine any records dated prior to 2008-04-18. |
| **HawkeyeStats** | Ball-tracking trajectory CSVs / JSON | Not present locally (Reference spec only) | Third-party scrape of televised ball tracking coordinates (release speed, bounce location, deviation). | Third-party GitHub repository (`alittlefitness/HawkeyeStats`). License and provenance unverified. | **HIGH RISK CAVEAT**: Spotty coverage, optical tracking occlusions, potential unverified provenance. Must be strictly isolated as optional enrichment; missing values must remain NULL. |
| **Open-Meteo Historical Weather** | REST API JSON | Not present locally (Reference spec only) | Hourly historical weather (temperature, relative humidity, dew point, wind, precipitation). | Open-Access, Non-Commercial / Commercial terms with attribution (CC BY 4.0). | **DOMAIN GUARDRAIL**: Provides macro-environmental ambient data. Must NOT be claimed as direct sub-surface pitch moisture or pitch hardness sensors. |
| **BCCI / IPL Official Records** | Official Web / Annual Reports | Reference spec only | Official squad registrations, auction rules, retention guidelines, base price brackets, DLS tables. | Proprietary BCCI/IPL. Fair-use reference for regulatory rule modeling only. | Authoritative source for regulatory constraints (purses, overseas caps, auction rules). |

---

### 5.4 Implemented vs Planned vs Unverified Status Matrix

| Subsystem / Feature | Current Implementation Status | Classification | Evidence / Basis |
|---------------------|-------------------------------|----------------|------------------|
| Raw CricSheet IPL Dataset | Local Files Present (1,243 matches) | **IMPLEMENTED (RAW STAGED)** | Direct inspection of `d:\New folder (2)\CricSheet\ipl_json` |
| Raw CricSheet SMA Dataset | Local Files Present (695 matches) | **IMPLEMENTED (RAW STAGED)** | Direct inspection of `d:\New folder (2)\CricSheet\sma` |
| Raw CricSheet T20 WC / CWC / Hundred | Local Files Present (884 matches) | **IMPLEMENTED (RAW STAGED)** | Direct inspection of `d:\New folder (2)\CricSheet\` subdirectories |
| Central Normalized Database (20 tables) | Not Implemented | **PLANNED (PHASE 2)** | Greenfield workspace; schema defined in TRD/ARCHITECTURE specifications |
| Player Identity Resolution (PIR) | Not Implemented | **PLANNED (PHASE 2)** | Greenfield workspace; algorithm designed, pending ingestion pipeline |
| True Strike Rate / True Economy Engine | Not Implemented | **PLANNED (PHASE 4)** | Greenfield workspace; statistical formulation documented in PRD/TRD |
| Win Probability Added (WPA) & xR | Not Implemented | **PLANNED (PHASE 4)** | Greenfield workspace; mathematical models specified |
| Sawai Mansingh Stadium Profiling | Not Implemented | **PLANNED (PHASE 5)** | Greenfield workspace; parameters defined for SMS home ground modeling |
| Batter vs Bowling Type Matchup Matrix | Not Implemented | **PLANNED (PHASE 5)** | Greenfield workspace; matrix taxonomy specified |
| Workload & Fatigue Tracking Engine | Not Implemented | **PLANNED (PHASE 6)** | Greenfield workspace; cumulative multi-tournament logic designed |
| Expected Auction Price (EAP) Model | Not Implemented | **PLANNED (PHASE 7)** | Greenfield workspace; regression features specified |
| Squad Simulation & Monte Carlo Engine | Not Implemented | **PLANNED (PHASE 8)** | Greenfield workspace; constraint solver designed |
| Next.js & Tailwind Dashboard UI | Not Implemented | **PLANNED (PHASE 8)** | Greenfield workspace; component hierarchy and layout specified |
| Kaggle 2007 IPL Coverage Claim | Anomaly Verified / Flagged | **UNVERIFIED / ANOMALOUS** | Earliest verified IPL match is 2008-04-18 (`335982.json`). 2007 data is invalid. |
| HawkeyeStats Data Provenance & Coverage | Unverified Third-Party | **UNVERIFIED / OPTIONAL** | External repository; license, schema, and completeness unverified. Treated as nullable. |
| In-Stadium Pitch Moisture Telemetry | Physically Non-Existent | **REJECTED / OUT-OF-SCOPE** | Open-Meteo provides macro weather only; no IoT pitch moisture sensors exist in public data. |

---

## 6. Caveats

1. **No External Network Calls**: In accordance with the dispatch boundaries ("DO NOT download external datasets or run external scripts"), external Kaggle, HawkeyeStats, and Open-Meteo APIs were evaluated based on their official published specifications, schema contracts, and domain documentation without live HTTP fetching.
2. **Local Data Lake Scope**: The local workspace contains 2,822 CricSheet match files across IPL, SMA, T20 WC, CWC, and The Hundred. Other domestic leagues (e.g. BBL, CPL, PSL) are not currently present in `d:\New folder (2)\CricSheet\` and are classified as future planned ingestion sources.
3. **Greenfield Code Status**: No application code or database instances exist in `d:\New folder (2)`. All architectural and technical specifications represent the authoritative target design to be executed in subsequent implementation phases.

---

## 7. Conclusion

The specification mining investigation has established the definitive requirements baseline for the Rajasthan Royals Squad Intelligence & Historical Performance Engine:
1. **Scope & Personas**: Complete alignment across 5 target personas (Lead Analyst, Head of Cricket Ops, Auction Strategist, Bowling/Batting Coaches, Chief Executive) and 7 core analytical modules (Match Impact, Venue Profiling, Matchups, Fatigue, Auction Valuation, Squad Simulation, Talent Scouting).
2. **Documentation Suite Architecture**: Full structural specifications for all 5 assigned core documents (`README.md`, `PRD.md`, `PHASES.md`, `AGENTS.md`, `AI_INSTRUCTIONS.md`) with explicit requirements, rubrics, and phase breakdowns.
3. **Data Provenance & Audit Integrity**: Validated the 2,822 raw match files currently in the workspace, established Cricsheet JSON v1.3.0 / YAML v0.94 parsing requirements, uncovered the Impact Player replacement schema, identified the Kaggle 2007 temporal anomaly, and erected strict guardrails separating macro weather from pitch moisture and isolating super overs from career averages.
4. **Agent Constitution & Implementation Roadmap**: Exhaustively defined the roles and boundaries for all 14 AI engineering agents across Phase 0 through Phase 8, guaranteeing deterministic reproducibility and zero data fabrication.

---

## 8. Verification Method

To independently verify the observations, claims, and data findings in this report, execute the following commands in PowerShell from the repository root `d:\New folder (2)`:

```powershell
# 1. Verify Greenfield Baseline (no application code, only .agents and CricSheet)
Get-ChildItem -Path "d:\New folder (2)" -Force

# 2. Verify CricSheet Directory Inventory and File Counts
Get-ChildItem -Path "d:\New folder (2)\CricSheet" -Directory | ForEach-Object { 
    [PSCustomObject]@{ Folder = $_.Name; FileCount = (Get-ChildItem $_.FullName -File).Count } 
}

# 3. Verify Earliest IPL Match (Confirming 2008 Start Date vs 2007 Anomaly)
Get-ChildItem -Path "d:\New folder (2)\CricSheet\ipl_json\*.json" | 
    Sort-Object { [int64]($_.BaseName) } | 
    Select-Object -First 1 | 
    ForEach-Object { Get-Content $_.FullName -TotalCount 25 }

# 4. Verify Latest IPL Match and Impact Player Replacement Schema
Get-Content "d:\New folder (2)\CricSheet\ipl_json\1535465.json" | 
    Select-String -Pattern "impact_player" -Context 2,5

# 5. Verify Super Over Flagging and Structure
Get-Content "d:\New folder (2)\CricSheet\ipl_json\1082625.json" | 
    Select-String -Pattern "super_over" -Context 2,5

# 6. Verify DLS Target and Method Metadata
Get-Content "d:\New folder (2)\CricSheet\ipl_json\1082648.json" | 
    Select-String -Pattern "method|target" -Context 1,4

# 7. Verify Cricsheet License (ODC-By v1.0)
Get-Content "d:\New folder (2)\CricSheet\ipl_json\LICENSE.txt" -TotalCount 15
```

**Invalidation Conditions**:
- If any file in `d:\New folder (2)\CricSheet\ipl_json\` is dated prior to 2008-04-18, the 2008 IPL debut premise is invalidated.
- If super over deliveries are discovered to contribute to official career batting/bowling totals in ICC/BCCI rules, E02 must be revised.
- If macro weather data from Open-Meteo is found to directly measure sub-surface soil moisture, E08 must be revised.
