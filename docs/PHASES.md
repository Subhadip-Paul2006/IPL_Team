# Engineering Implementation Roadmap (Phases 0 to 8)

**Project Title**: Rajasthan Royals Squad Intelligence & Historical Performance Engine  
**Event**: IPL 2027 Auction Scouting Hackathon  
**Target Franchise**: Rajasthan Royals (RR)  
**Document Version**: 1.0.0-PROD-SPEC  
**Status**: `[STATUS: PHASES 0 COMPLETE / PHASES 1-8 PLANNED]`  
**Date**: November 2026  
**Primary Authors**: Principal Software Architect, Cricket Data Engineer, Systems Integration Engineer  

---

## 1. Executive Roadmap Overview

The development lifecycle of the **Rajasthan Royals Squad Intelligence & Historical Performance Engine** is structured into nine sequential, rigorous engineering phases (Phase 0 through Phase 8). Each phase establishes an immutable technical foundation for downstream modules, enforcing strict data verification gates, architectural boundaries, and regression testing prior to phase progression.

```
+----------------------------------------------------------------------------------------------------+
|                               PHASE PROGRESSION & DEPENDENCY TIMELINE                              |
+----------------------------------------------------------------------------------------------------+
| [PHASE 0: RESEARCH & AUDIT]                                                                        |
| Greenfield Baseline, Source Licensing, Temporal Anomaly Isolation (COMPLETE)                      |
|       |                                                                                            |
|       v                                                                                            |
| [PHASE 1: RAW INGESTION]                                                                           |
| Checksums, Quarantine Staging Lake, Multi-Format Parsers (PLANNED)                                 |
|       |                                                                                            |
|       v                                                                                            |
| [PHASE 2: NORMALISATION & PIR]                                                                     |
| 20-Entity PostgreSQL Schema, CricSheet Hex Hash Entity Disambiguation (PLANNED)                    |
|       |                                                                                            |
|       v                                                                                            |
| [PHASE 3: CONTEXTUAL ENRICHMENT]                                                                   |
| Macro-Weather (Open-Meteo), SMS Jaipur Profiling, Phase Boundaries (PLANNED)                       |
|       |                                                                                            |
|       v                                                                                            |
| [PHASE 4: STATISTICAL CORE & PROFILES]                                                             |
| True Strike Rate (TSR), True Economy (TER), WPA, xR, Super Over Segregation (PLANNED)              |
|       |                                                                                            |
|       v                                                                                            |
| [PHASE 5: HISTORICAL INTELLIGENCE & MATCHUPS]                                                      |
| Batter vs 6 Bowling Styles, Head-to-Head Matrix, SMS Fortress Advantage (PLANNED)                  |
|       |                                                                                            |
|       v                                                                                            |
| [PHASE 6: SQUAD INTELLIGENCE & WORKLOAD]                                                           |
| Multi-Tournament Fatigue Ledger, Rest Intervals, Medical Availability (PLANNED)                   |
|       |                                                                                            |
|       v                                                                                            |
| [PHASE 7: VALUATION & CANDIDATE EVALUATION]                                                        |
| Expected Auction Price (EAP), T20 WAR, Scarcity Multipliers (₹120 Cr Cap) (PLANNED)                 |
|       |                                                                                            |
|       v                                                                                            |
| [PHASE 8: DASHBOARDS, SIMULATION & SUBMISSION]                                                     |
| Next.js UI, 10,000-Run Monte Carlo Engine, IPL XI Optimizer, Submission Dossier (PLANNED)          |
+----------------------------------------------------------------------------------------------------+
```

### Consolidated Phase Status Matrix

| Phase # | Phase Identifier | Target Scope | Assigned Agent(s) | Status | Milestone Mapping |
|---|---|---|---|---|---|
| **Phase 0** | Research, Schema Audit & Greenfield Baseline | Repository inspection, data audit, licensing verification, documentation baseline | Chief Architect, Data Source Audit Agent, Documentation Agent | **COMPLETE** | Milestone 1 |
| **Phase 1** | Raw Data Acquisition & Quarantine Staging | Multi-format file validation, SHA-256 manifest generation, quarantine lake staging | Dataset Acquisition Agent, Data Quality Agent | **PLANNED** | Milestone 2 / Phase 1 |
| **Phase 2** | Normalisation & Player Identity Resolution | PostgreSQL 20-entity DDL migration, CricSheet hex registry mapping, alias resolution | Data Normalisation Agent, PIR Specialist | **PLANNED** | Milestone 2 / Phase 2 |
| **Phase 3** | Contextual & Environmental Enrichment | Open-Meteo weather integration, venue profiling, phase boundary tagging | Contextual Enrichment Agent, Cricket Research Specialist | **PLANNED** | Milestone 2 / Phase 3 |
| **Phase 4** | Player Profiles & Core Statistical Engine | Computation of True SR, True Econ, WPA, xR, Super Over isolation | Cricket Statistics Specialist, Backend Engineer | **PLANNED** | Milestone 2 / Phase 4 |
| **Phase 5** | Historical Performance & Tactical Matchups | Batter vs 6 bowling archetypes, head-to-head matrix, SMS Jaipur home engine | Historical Performance Agent, Cricket Research Specialist | **PLANNED** | Milestone 2 / Phase 5 |
| **Phase 6** | Squad Intelligence, Fatigue & Workload Engine | Cumulative overs across tournaments, rest interval decay, medical availability logs | Historical Performance Agent, Backend Engineer | **PLANNED** | Milestone 2 / Phase 6 |
| **Phase 7** | Candidate Evaluation & Auction Valuation Engine | Expected Auction Price (EAP) regression, T20 WAR, scarcity multipliers (₹120 Cr Cap) | Backend Engineer, Cricket Statistics Specialist | **PLANNED** | Milestone 2 / Phase 7 |
| **Phase 8** | Interactive Dashboard, Simulation & Submission | Next.js UI, 10,000 Monte Carlo simulator, Playing XI optimizer, final packaging | Frontend Engineer, Backend Engineer, QA Agent | **PLANNED** | Milestone 3 & 4 |

---

## 2. Phase 0: Research, Schema Audit & Greenfield Baseline Setup

### 2.1 Objective & Scope
Establish an uncompromised, forensically audited technical baseline. Inspect the workspace, audit local raw data archives (`CricSheet/`), confirm legal licensing terms, uncover temporal/structural schema anomalies, and generate the authoritative engineering documentation suite.

### 2.2 Tasks & Subtasks
1. **Workspace Inspection**:
   - Verify greenfield state: confirm zero application code, build files, or pre-existing databases.
   - Establish directory layout for agent metadata (`.agents/teamwork/`) and documentation (`docs/`).
2. **Local Data Lake Forensic Audit**:
   - Inventory files across `CricSheet/`: 1,243 IPL JSON files, 695 SMAT YAML files, 230 T20 WC JSON files, 265 ODI WC YAML files, 389 The Hundred JSON files (Total: 2,822 match files).
   - Verify Cricsheet JSON schema (v1.3.0) and legacy YAML schema (v0.94).
   - Verify licensing terms: Open Data Commons Attribution License (ODC-By v1.0).
3. **Domain Anomaly & Edge Case Detection**:
   - Audit earliest IPL match: Verify `335982.json` (2008-04-18). Formally flag external Kaggle claims of "2007 IPL data" as a temporal impossibility.
   - Uncover modern Impact Player replacement syntax in `1535465.json`.
   - Inspect Super Over representations in tie matches (e.g. `1082625.json`).
   - Audit DLS rain-affected target schemas (e.g. `1082648.json`).
4. **Documentation Baseline Generation**:
   - Author engineering specifications: `README.md`, `PRD.md`, `TRD.md`, `ARCHITECTURE.md`, `PHASES.md`, `AGENTS.md`, and `AI_INSTRUCTIONS.md`.

### 2.3 Deliverables & Artifacts
- Baseline Documentation Suite in `d:\New folder (2)\docs\`.
- Root Project Navigation Hub in `d:\New folder (2)\README.md`.
- Specification Mining & Audit Report (`.agents/teamwork/spec_miner_1/handoff.md`).

### 2.4 Verification Methods
- **File System Inspection**: Verify that exactly the required markdown files exist.
- **Licensing Audit Command**:
  ```powershell
  Get-Content "d:\New folder (2)\CricSheet\ipl_json\LICENSE.txt" -TotalCount 15
  ```
- **Temporal Integrity Command**:
  ```powershell
  Get-ChildItem -Path "d:\New folder (2)\CricSheet\ipl_json\*.json" | 
      Sort-Object { [int64]($_.BaseName) } | Select-Object -First 1 | 
      ForEach-Object { Get-Content $_.FullName -TotalCount 25 }
  ```
- **Status**: **COMPLETE / GREENFIELD BASELINE**

---

## 3. Phase 1: Raw Data Acquisition & Quarantine Lake Staging

### 3.1 Objective & Scope
Build a fault-tolerant, streaming ingestion pipeline that reads raw match files from `CricSheet/`, validates JSON/YAML syntax, computes cryptographic SHA-256 checksums, and stages records into an immutable, read-only Quarantine Lake.

```
+----------------------------------------------------------------------------------------------------+
|                                PHASE 1: DATA INGESTION & QUARANTINE FLOW                           |
+----------------------------------------------------------------------------------------------------+
|  [Raw Data Source: CricSheet/]                                                                     |
|  - ipl_json (1,243 files, JSON v1.3.0)                                                             |
|  - sma (695 files, YAML v0.94)                                                                     |
|  - icc_mens_t20_world_cup_json (230 files)                                                         |
|  - icc_mens_cricket_world_cup (265 files)                                                          |
|  - hnd_json (389 files)                                                                            |
|       |                                                                                            |
|       v                                                                                            |
|  [Ingestion Streaming Engine]                                                                      |
|  - Computes SHA-256 Hash per file                                                                  |
|  - Detects Schema Format (JSON vs YAML)                                                            |
|  - Validates JSON Syntax & Minimum Required Keys                                                   |
|       |                                                                                            |
|       +------------------------------------+-----------------------------------+                   |
|       | (Valid Payload)                    | (Syntax Error / Corrupted)        |                   |
|       v                                    v                                   v                   |
|  [Immutable Quarantine Lake]          [Quarantine Error Vault]            [SHA-256 Manifest]       |
|  - Raw JSON staging tables            - Malformed payload dump            - Checksum verification  |
|  - Read-only partition                - Error stack trace log             - Ingestion audit trail  |
+----------------------------------------------------------------------------------------------------+
```

### 3.2 Tasks & Subtasks
1. **Checksum & Manifest Generation**:
   - Traverse `CricSheet/` directories; calculate SHA-256 hashes for all 2,822 raw match files.
   - Write immutable checksum manifest (`raw_lake_manifest.json`) recording file path, file size, hash, and modified date.
2. **Polymorphic Ingestion Adapters**:
   - Develop `JsonV13Parser` for Cricsheet JSON v1.3.0 (handling `info` dictionary, `innings` list, and `overs` arrays).
   - Develop `YamlV094Parser` for legacy YAML formats (handling key-value mappings and decimal delivery keys like `0.1`).
3. **Quarantine Staging Engine**:
   - Stream raw records into staging tables: `stg_cricsheet_matches` and `stg_cricsheet_deliveries`.
   - Implement error-handling queue: malformed or unparseable files are written to `quarantine_errors/` with stack traces without breaking the batch run.
4. **Temporal Anomaly Enforcement**:
   - Filter any match claiming IPL competition status dated before `2008-04-18`. Flag as `ANOMALY_PRE_IPL_2008` and route to quarantine.

### 3.3 Deliverables & Artifacts
- `src/ingestion/parser_json.py` & `src/ingestion/parser_yaml.py`.
- `src/ingestion/quarantine_manager.py`.
- `data/manifests/raw_lake_manifest.json`.
- PostgreSQL staging schema: `stg_cricsheet_matches`, `stg_cricsheet_deliveries`, `stg_quarantine_log`.

### 3.4 Verification Methods
- **File Ingestion Completeness Test**:
  ```sql
  SELECT source_competition, COUNT(*) AS match_count 
  FROM stg_cricsheet_matches 
  GROUP BY source_competition;
  -- Expected: IPL = 1243, SMA = 695, T20_WC = 230, CWC = 265, HND = 389.
  ```
- **Zero Ingestion Failures**: Ensure `COUNT(*)` in `stg_quarantine_log` is exactly 0 for the verified CricSheet archive.
- **Status**: **PLANNED**

---

## 4. Phase 2: Central Normalised Database Schema & Player Identity Resolution

### 4.1 Objective & Scope
Deploy the production 3NF relational database schema across 20 distinct entities in PostgreSQL 16+. Execute the multi-tiered Player Identity Resolution (PIR) engine to resolve player name strings into canonical master entities using persistent CricSheet registry hashes.

```
+----------------------------------------------------------------------------------------------------+
|                         PHASE 2: PLAYER IDENTITY RESOLUTION (PIR) WORKFLOW                         |
+----------------------------------------------------------------------------------------------------+
|  [Raw Player String] (e.g. "SV Samson", "Sanju Samson", "S Samson")                                |
|       |                                                                                            |
|       v                                                                                            |
|  [Tier 1: CricSheet Registry Hex Hash Match]                                                       |
|  - Inspect `info.registry.people` in match JSON (e.g. hash "1b58269e")                             |
|  - Query `player_aliases` table by hex hash                                                        |
|       |                                                                                            |
|       +------------------------------------+                                                       |
|       | Match Found (Confidence: 1.00)     | Hash Absent / Legacy YAML                             |
|       v                                    v                                                       |
|  [Assign Canonical `player_id`]       [Tier 2: Normalized Full Name & Team Roster Match]          |
|                                       - Strip punctuation, accents, middle initials                |
|                                       - Cross-reference team squad sheet for match date           |
|                                            |                                                       |
|                                            +-----------------------------------+                   |
|                                            | High Confidence (>= 0.95)         | Ambiguous (< 0.95)|
|                                            v                                   v                   |
|                                       [Assign Canonical `player_id`]      [Human Review Queue]     |
|                                       - Insert new alias record           - Flag for manual audit  |
|                                                                           - NEVER merge distinct   |
|                                                                             names arbitrarily      |
+----------------------------------------------------------------------------------------------------+
```

### 4.2 Tasks & Subtasks
1. **Schema Deployment (DDL Migration)**:
   - Deploy 20 core relational tables: `players`, `player_aliases`, `teams`, `competitions`, `seasons`, `squad_memberships`, `matches`, `innings`, `deliveries`, `batting_innings`, `bowling_spells`, `fielding_events`, `venues`, `pitch_conditions`, `weather_conditions`, `player_availability`, `player_injuries`, `data_sources`, `source_records`, and `derived_features`.
   - Apply composite primary keys, foreign key constraints (`ON DELETE RESTRICT`), and performance indexes.
2. **Multi-Tier Identity Resolution Engine**:
   - *Tier 1*: Direct hexadecimal match against CricSheet `info.registry.people`.
   - *Tier 2*: Normalized string phonetic distance (Levenshtein + Jaro-Winkler) conditioned on verified team rosters and match dates.
   - *Tier 3*: Ambiguity isolation: if confidence $< 0.95$, route to `pir_disambiguation_queue` without guessing.
3. **Delivery-to-Match Relational ELT**:
   - Transform staged raw deliveries into 3NF `deliveries`, `batting_innings`, and `bowling_spells`.
   - Correctly record substitute fielders in dismissals (flagging `substitute = true` in `fielding_events`).
   - Track Impact Player substitutions into `squad_memberships` and match replacement events.

### 4.3 Deliverables & Artifacts
- `migrations/V001__initial_3nf_schema.sql`.
- `src/pir/identity_resolver.py`.
- `src/elt/normalisation_pipeline.py`.
- Master Player Registry table (`players` and `player_aliases`).

### 4.4 Verification Methods
- **Foreign Key Integrity Check**:
  ```sql
  SELECT COUNT(*) FROM deliveries d 
  LEFT JOIN matches m ON d.match_id = m.id 
  WHERE m.id IS NULL;
  -- Expected: Exactly 0 orphan deliveries.
  ```
- **PIR Precision Benchmark**: Run validation on 50 known difficult name pairs (e.g. Rohit Sharma vs Rahul Sharma, Albie Morkel vs Morne Morkel) to confirm zero identity collisions.
- **Status**: **PLANNED**

---

## 5. Phase 3: Contextual & Environmental Enrichment

### 5.1 Objective & Scope
Augment delivery and match records with external contextual datasets: Open-Meteo historical macro-weather (temperature, relative humidity, dew point), venue ground geometries (boundary dimensions), pitch surface classifications, and match phase tags.

### 5.2 Tasks & Subtasks
1. **Macro-Weather Integration (Open-Meteo)**:
   - Query Open-Meteo Historical Weather API for all venue coordinates and match timestamps (15:30 IST and 19:30 IST).
   - Ingest hourly air temperature, relative humidity, dew point, wind speed, and precipitation into `weather_conditions`.
   - Calculate dew risk indicator: $T_{\text{spread}} = T_{\text{air}} - T_{\text{dew}}$; flag `high_dew_risk` when $T_{\text{spread}} \le 2.5^\circ\text{C}$ and $RH \ge 75\%$.
   - **Enforce Attribution**: Embed Open-Meteo CC BY 4.0 license metadata.
2. **Venue Geometry & Pitch Modeling**:
   - Populate `venues` and `pitch_conditions` with boundary dimensions (square and straight distances in meters) and soil classifications (Red Soil vs Black Soil vs Mixed).
   - Specifically parameterize Sawai Mansingh Stadium (SMS Jaipur): Square boundaries 68m–75m, Straight boundaries 72m–78m, high-altitude arid dry air profile.
3. **Match Phase Boundary Materialization**:
   - Tag every delivery with exact operational match phase:
     - *Powerplay*: Overs 0.1 to 5.6
     - *Middle Overs*: Overs 6.1 to 14.6
     - *Death Overs*: Overs 15.1 to 19.6
   - Tag DLS-truncated innings with dynamically recalculated phase boundaries.
4. **HawkeyeStats Optional Trajectory Integration**:
   - Audit HawkeyeStats trajectory dataset for schema compliance and licensing terms.
   - If verified, join release speed and landing $(X,Y)$ coordinates into `deliveries` table.
   - Enforce domain rule: missing trajectory attributes must remain strictly `NULL`.

### 5.3 Deliverables & Artifacts
- `src/enrichment/weather_client.py`.
- `src/enrichment/venue_profiler.py`.
- `src/enrichment/phase_tagger.py`.
- Populated tables: `weather_conditions`, `pitch_conditions`, `venues`.

### 5.4 Verification Methods
- **Null Safety Assertion**:
  ```sql
  SELECT COUNT(*) FROM deliveries 
  WHERE pitch_x_coord = 0.0 AND pitch_y_coord = 0.0;
  -- Expected: Exactly 0. Missing tracking data must be NULL, never (0.0, 0.0).
  ```
- **Weather Linkage Test**:
  ```sql
  SELECT COUNT(*) FROM matches m 
  LEFT JOIN weather_conditions w ON m.id = w.match_id 
  WHERE w.id IS NULL AND m.source_competition = 'IPL';
  -- Expected: Exactly 0 un-enriched IPL matches.
  ```
- **Status**: **PLANNED**

---

## 6. Phase 4: Player Profiles & Core Statistical Engine

### 6.1 Objective & Scope
Implement the mathematical calculations for context-adjusted metrics: True Strike Rate (TSR), True Economy Rate (TER), Win Probability Added (WPA), Expected Runs (xR), Leverage Index (LI), and Clutch Index. Enforce strict isolation of Super Over statistics.

```
+----------------------------------------------------------------------------------------------------+
|                         PHASE 4: STATISTICAL FORMULATION & SUPER OVER ISOLATION                     |
+----------------------------------------------------------------------------------------------------+
|  [Deliveries Table]                                                                                |
|       |                                                                                            |
|       +------------------------------------+-----------------------------------+                   |
|       | Filter: `is_super_over = false`    | Filter: `is_super_over = true`    |                   |
|       v                                    v                                   v                   |
|  [Official Career Analytics Core]     [Super Over Vault]                  [DLS Targets Recalculation|
|  - Compute Phase Baseline Pars         - Isolate runs, balls, wickets      - Ingest revised targets|
|  - True Strike Rate (TSR)              - Compute Super Over Clutch Card    - Recalculate required  |
|  - True Economy Rate (TER)             - Hard Rule: Never increment          run rates and pressure|
|  - Win Probability Added (WPA)           official career averages            denominators          |
|  - Expected Runs (xR)                                                                              |
|       |                                                                                            |
|       v                                                                                            |
|  [Materialized `derived_features` View]                                                            |
|  - High-performance indexed storage for player career cards & phase splits                        |
+----------------------------------------------------------------------------------------------------+
```

### 6.2 Tasks & Subtasks
1. **Tournament & Venue Baseline Par Calculation**:
   - Compute baseline expected runs per ball ($\bar{R}_{P,V,S}$) and expected dismissal probability ($\bar{W}_{P,V,S}$) for every combination of phase ($P$), venue ($V$), and season ($S$).
2. **True Strike Rate (TSR) & True Economy Rate (TER) Formulation**:
   - Compute batter delivery Run Value Added: $RVA = \text{Runs} - \bar{R}_{P,V,S}$.
   - Aggregate player-level $TSR = SR_{\text{observed}} - SR_{\text{expected}}$ and $TER = Econ_{\text{expected}} - Econ_{\text{observed}}$.
3. **Win Probability Added (WPA) & Expected Runs (xR)**:
   - Train a multinomial logistic regression state model estimating win probability $WP(I, B, W, R_{\text{diff}})$ on 1,243 IPL matches.
   - Compute delivery $\Delta WP = WP_{t+1} - WP_t$.
   - Attribute batting WPA to striker and bowling WPA to bowler.
4. **Super Over Isolation Enforcement**:
   - Isolate all innings where `is_super_over = true`. Store in `super_over_performances`.
   - Ensure official career batting and bowling views exclude super over records by default.
5. **DLS Target Reconciliation**:
   - In weather-affected matches, replace the 20-over denominator with the official revised overs from `matches.dls_revised_overs`.

### 6.3 Deliverables & Artifacts
- `src/analytics/pars_calculator.py`.
- `src/analytics/true_metrics.py`.
- `src/analytics/wpa_engine.py`.
- `migrations/V002__derived_features_views.sql`.

### 6.4 Verification Methods
- **Super Over Cleanliness Assertion**:
  ```sql
  SELECT p.canonical_name, SUM(d.runs_batter) AS career_runs 
  FROM players p 
  JOIN deliveries d ON p.id = d.batter_id 
  WHERE d.is_super_over = true 
  GROUP BY p.canonical_name;
  -- Must return isolated super over runs that do NOT match career totals.
  ```
- **Formula Unit Tests**: Verify that a batter scoring 12 runs off 6 balls in a Death phase where par is 9.0 runs achieves a positive Run Value Added ($RVA = +3.0$) and positive TSR ($+50.0$).
- **Status**: **PLANNED**

---

## 7. Phase 5: Historical Performance Analysis & Tactical Matchup Engine

### 7.1 Objective & Scope
Build the multidimensional tactical matchup engine. Profile batter proficiency against 6 distinct bowling archetypes, execute head-to-head batter vs bowler micro-analytics, generate pitch trajectory/length heatmaps, and implement the Sawai Mansingh Stadium (SMS Jaipur) Home Fortress engine.

### 7.2 Tasks & Subtasks
1. **Batter vs 6 Bowling Archetypes Engine**:
   - Classify all bowlers into 6 primary styles:
     1. Right-Arm Fast / Fast-Medium (RAF)
     2. Left-Arm Fast / Fast-Medium (LAF)
     3. Right-Arm Offbreak (OS)
     4. Left-Arm Orthodox (SLA)
     5. Right-Arm Legbreak / Googly (LBG)
     6. Left-Arm Unorthodox / Chinaman (LAC)
   - Compute batter metrics against each archetype: Strike Rate, Dot Ball %, Boundary %, Balls Per Dismissal (BPD), False Shot %.
   - Flag small samples: If deliveries faced $< 24$, append `INSUFFICIENT_SAMPLE_FLAG`.
2. **Head-to-Head Batter vs Bowler Matrix**:
   - Construct real-time lookup queries for any batter-bowler pair: balls, runs, dismissals, dot balls, boundary count, and dismissal breakdown (e.g. bowled, caught behind).
3. **Pitch Trajectory & Length Scoring Heatmaps**:
   - Aggregate delivery coordinates into 5 vertical length zones (Yorker, Full, Good Length, Back of Length, Short) and 3 lateral line zones (Outside Off, Stumps, Down Leg).
   - Generate strike rate and dismissal density matrices across the $5 \times 3$ grid.
4. **Sawai Mansingh Stadium (SMS Jaipur) Fortress Engine**:
   - Model SMS Jaipur-specific parameters:
     - Boundary Running Index: Ratio of non-boundary runs (1s, 2s, 3s) to total runs.
     - Pace Advantage Factor: Seamer wicket-taking efficiency on SMS red soil.
     - Dew Grip Degradation: Night fixture 2nd-innings spinner economy decay.

### 7.3 Deliverables & Artifacts
- `src/tactics/archetype_matrix.py`.
- `src/tactics/head_to_head.py`.
- `src/tactics/sms_jaipur_engine.py`.
- API Endpoints: `/api/v1/tactics/matchup`, `/api/v1/tactics/sms-profile`.

### 7.4 Verification Methods
- **Matchup Consistency Test**: Verify head-to-head query returns identical totals to direct delivery aggregations for high-profile matchups (e.g. MS Dhoni vs Sunil Narine).
- **Latency Benchmark**: Head-to-head matchup query execution time must be $< 150\text{ ms}$ under PostgreSQL `EXPLAIN ANALYZE`.
- **Status**: **PLANNED**

---

## 8. Phase 6: Squad Intelligence, Fatigue & Workload Engine

### 8.1 Objective & Scope
Quantify player physical strain, workload accumulation, schedule congestion, and medical availability across multi-tournament records (IPL, SMAT, ICC T20 World Cups, ODI World Cups, and The Hundred).

### 8.2 Tasks & Subtasks
1. **Multi-Format Workload Aggregation**:
   - Compute cumulative overs bowled and deliveries faced across 30-day, 90-day, and 365-day rolling windows.
   - Categorize fast bowlers into workload strain tiers: Low ($< 30$ overs/month), Medium ($30–60$ overs), High ($60–90$ overs), Extreme ($> 90$ overs).
2. **Schedule Congestion & Travel Decay Modeling**:
   - Calculate rest intervals (hours elapsed between consecutive fixtures).
   - Integrate travel distance matrix across Indian host cities.
   - Compute performance decay factor for back-to-back matches with $< 48$ hours rest.
3. **Medical Downtime & Availability Ledger**:
   - Ingest injury records, surgical downtime, and national board NOC departure windows.
   - Calculate `availability_probability` ($0.0–1.0$) for the 14-match IPL league stage.
   - Flag high-risk overseas players facing bilateral international series call-ups during April/May.

### 8.3 Deliverables & Artifacts
- `src/workload/fatigue_tracker.py`.
- `src/workload/availability_model.py`.
- Populated tables: `player_availability`, `player_injuries`.

### 8.4 Verification Methods
- **Multi-Tournament Overs Reconciliation**:
  ```sql
  SELECT p.canonical_name, c.name AS tournament, COUNT(d.id)/6.0 AS overs_bowled 
  FROM players p 
  JOIN deliveries d ON p.id = d.bowler_id 
  JOIN matches m ON d.match_id = m.id 
  JOIN competitions c ON m.competition_id = c.id 
  GROUP BY p.canonical_name, c.name;
  ```
- Cross-check results against official tournament scorecards.
- **Status**: **PLANNED**

---

## 9. Phase 7: Candidate Evaluation & Auction Valuation Engine

### 9.1 Objective & Scope
Construct the economic and predictive valuation models for the IPL 2027 Mega-Auction. Implement T20 Wins Above Replacement (WAR), Expected Auction Price (EAP) predictive regression, role scarcity multipliers, and purse budget optimization under an INR 120.00 Cr purse cap.

```
+----------------------------------------------------------------------------------------------------+
|                         PHASE 7: AUCTION VALUATION & WAR ENGINE ARCHITECTURE                       |
+----------------------------------------------------------------------------------------------------+
|  [Player Performance Features]                                                                     |
|  - Batting RVA, Bowling RVA, Fielding VA                                                           |
|  - True Strike Rate & True Economy (Phase-Weighted)                                                |
|       |                                                                                            |
|       v                                                                                            |
|  [T20 Wins Above Replacement (WAR)]                                                                |
|  $$WAR = (RVA_{bat} + RVA_{bowl} + FVA - \text{Baseline}_{rep}) / 18.5$$                           |
|       |                                                                                            |
|       v                                                                                            |
|  [Market Scarcity Multiplier]                                                                      |
|  - Archetype Supply vs Demand Ratio (Pace All-Rounder, Death Seamer, Mystery Spin)                 |
|       |                                                                                            |
|       v                                                                                            |
|  [Expected Auction Price (EAP) Model]                                                              |
|  - Multi-Variable Regression conditioned on ₹120.00 Cr Purse Cap                                   |
|  - Outputs: Expected Price (₹ Cr), 80% Confidence Interval (Floor, Median, Ceiling)                |
|       |                                                                                            |
|       v                                                                                            |
|  [Bidding Room Strategy & Dynamic 45-Second Pivot Matrix]                                          |
|  - Live Purse Burn Curve                                                                           |
|  - Negative-EV Alerts when bidding crosses hard ceiling                                            |
|  - Immediate Statistical Parity Alternatives                                                       |
+----------------------------------------------------------------------------------------------------+
```

### 9.2 Tasks & Subtasks
1. **T20 Wins Above Replacement (WAR) Formulation**:
   - Establish replacement-level baseline for each player role (top 85th percentile of unselected domestic pool).
   - Convert net run values into wins using T20 conversion factor ($1\text{ Win} \approx 18.5\text{ net runs}$).
   - Compute total player $WAR = WAR_{\text{bat}} + WAR_{\text{bowl}} + WAR_{\text{field}}$.
2. **Expected Auction Price (EAP) Predictive Regression**:
   - Train predictive model on historical 2018, 2022, and 2025 mega-auction clearing prices.
   - Features: 3-year weighted WAR, age curve, international caps, role scarcity, purse inflation scale ($\frac{120\text{ Cr}}{100\text{ Cr}} = 1.20$).
   - Predict price distribution: Floor, Median, Ceiling. Clamp lower bound at base price (₹30L to ₹2.0 Cr).
3. **Role Scarcity Multipliers**:
   - Calculate archetype supply deficits:
     - Indian Pace-Bowling All-Rounders: Multiplier $1.4\times - 1.8\times$.
     - Elite Death-Overs Specialists (TER $\ge +1.8$): Multiplier $1.3\times - 1.5\times$.
     - Top-Order Anchor (Low TSR): Multiplier $0.7\times - 0.9\times$ (market deflation).
4. **45-Second Live Auction Pivot Recommender**:
   - Algorithmic similarity matcher: when player price crosses hard ceiling, recommend top 3 alternatives matching $\ge 85\%$ of player's micro-skills at $< 65\%$ of expected cost.

### 9.3 Deliverables & Artifacts
- `src/valuation/war_calculator.py`.
- `src/valuation/eap_regressor.py`.
- `src/valuation/pivot_recommender.py`.
- API Endpoints: `/api/v1/valuation/eap`, `/api/v1/valuation/pivots`.

### 9.4 Verification Methods
- **Historical Backtesting**: Backtest EAP model against 2022 Mega-Auction clearing prices; verify $R^2 \ge 0.75$ and Mean Absolute Error (MAE) $< \text{₹1.8 Cr}$.
- **Purse Cap Invariant Test**: Run mock auction with 25 players; verify total expenditure $\le \text{₹120.00 Cr}$ under all generated portfolios.
- **Status**: **PLANNED**

---

## 10. Phase 8: Interactive Dashboard, Simulation & Final Submission

### 10.1 Objective & Scope
Deliver the complete end-to-end user application: responsive Next.js frontend, interactive tactical visualization dashboards, vectorized 10,000-run Monte Carlo tournament simulator, IPL-compliant Playing XI solver, and the final hackathon submission package.

```
+----------------------------------------------------------------------------------------------------+
|                         PHASE 8: APPLICATION DELIVERY & PRESENTATION LAYER                         |
+----------------------------------------------------------------------------------------------------+
|  [Next.js 14 Web Application] (Tailwind CSS, ECharts, Cytoscape.js)                                |
|       |                                                                                            |
|       +-------------------+-------------------+-------------------+-------------------+            |
|       v                   v                   v                   v                   v            |
|  [Executive KPI]     [Live Auction]      [Matchup War Room]  [Playing XI Solver] [Monte Carlo]     |
|  - Total WAR         - Bidding Console   - Pitch Heatmaps    - IPL Rules Engine  - 10,000 Runs     |
|  - Purse Burn Rate   - 45s Pivot Alerts  - Batter vs Bowler  - Max 4 Overseas    - Playoff Prob %  |
|  - Compliance Status - Ceiling Gauges    - SMS Jaipur Plan   - Impact Player     - Seeded Runs     |
|       |                                                                                            |
|       v                                                                                            |
|  [FastAPI Backend & Service Layer] (p95 < 200ms, Redis Caching, Connection Pooling)                |
|       |                                                                                            |
|       v                                                                                            |
|  [PostgreSQL 16+ Database Core] (3NF Relational Tables, Materialized Views, Lineage Traces)        |
+----------------------------------------------------------------------------------------------------+
```

### 10.2 Tasks & Subtasks
1. **Next.js Frontend Development**:
   - Implement persona-specific dashboards:
     - *Auction Bidding Console*: Live purse tracker, dynamic burn curve, 45-second pivot popup.
     - *Tactical Matchup War Room*: $5 \times 3$ pitch heatmaps, batter wagon wheels, SMS boundary plans.
     - *Executive Summary*: Roster compliance audit, WAR efficiency, injury availability ledger.
2. **Playing XI Optimization Solver**:
   - Enforce IPL Playing Conditions: Exactly 11 players, $\le 4$ overseas players, $\ge 1$ wicketkeeper, $\ge 5$ bowling options.
   - Enforce Impact Player tactical substitute workflow (1 tactical swap per team per match).
3. **10,000-Run Monte Carlo Campaign Simulator**:
   - Vectorized simulation of 14 league fixtures using transition matrices.
   - Output: Win totals, playoff qualification probability (%), championship probability (%), Net Run Rate (NRR) bounds.
   - Enforce deterministic integer random seed parameter for reproducible audits.
4. **Final Hackathon Submission Packaging**:
   - Complete technical documentation review, execute all automated validation suites, compile video demonstration walkthrough, and publish final engineering audit report.

### 10.3 Deliverables & Artifacts
- Next.js Web Application (`frontend/`).
- FastAPI Application & Routers (`backend/`).
- Monte Carlo Engine (`src/simulation/tournament_simulator.py`).
- Final Engineering Verification Report (`reports/FINAL_VERIFICATION_REPORT.md`).

### 10.4 Verification Methods
- **End-to-End Latency Audit**: Execute automated Locust load tests; verify $p95 < 200\text{ ms}$ on API endpoints.
- **Monte Carlo Seed Reproducibility Test**: Execute 10,000 simulations twice using seed `2027`; verify bit-for-bit identical playoff probability results.
- **Regulatory Rule Validation**: Attempt to submit an invalid Playing XI with 5 overseas players; verify hard UI and API rejection.
- **Lighthouse Performance Score**: Next.js dashboard UI must achieve Lighthouse performance score $\ge 90$.
- **Status**: **PLANNED**

---

## 11. Cross-Phase Risk Assessment & Mitigation Matrix

| # | Risk Description | Severity | Impacted Phase | Mitigation Strategy |
|---|---|---|---|---|
| **R1** | Ingestion parser crashes on corrupted YAML records | High | Phase 1 | Implement quarantine lake architecture: malformed records are logged to `quarantine_errors/` with stack traces; batch pipeline continues without interruption. |
| **R2** | Player name collision across tournaments (e.g. "R Sharma") | Critical | Phase 2 | Primary matching strictly uses CricSheet 8-character hexadecimal hashes. Low confidence matches are quarantined to manual review queue; never merge distinct names. |
| **R3** | HawkeyeStats optical tracking coordinates unavailable or missing | Medium | Phase 3 | Treat delivery coordinates as strictly nullable enrichment. Missing coordinates remain `NULL`; forbidden from substituting `(0.0, 0.0)`. |
| **R4** | Super Over statistics contaminate official career aggregates | Critical | Phase 4 | Hard database assertion: `is_super_over = true` deliveries are quarantined into isolated views; official career views filter out super overs. |
| **R5** | DLS weather interruptions distort required run-rate calculations | High | Phase 4 | Ingest official DLS revised overs from match metadata. Recalculate phase boundaries dynamically for truncated matches. |
| **R6** | Monte Carlo simulation exceeds acceptable latency (> 5,000ms) | Medium | Phase 8 | Vectorize transition matrix operations using NumPy arrays; run multi-threaded simulations with pre-compiled match probabilities. |
| **R7** | Auction bidding war causes team to exceed INR 120.00 Cr purse cap | Critical | Phase 7, 8 | Hard system ceiling: bidding console blocks any bid that leaves insufficient purse to acquire minimum required roster of 18 players at base price. |

---

## 12. Conclusion & Verification Summary

The **Engineering Implementation Roadmap (Phases 0 to 8)** provides a deterministic, transparent blueprint for constructing the Rajasthan Royals Squad Intelligence & Historical Performance Engine. 

- **Phase 0** is **COMPLETE**, having verified the workspace baseline, audited 2,822 raw match files, and authored the foundational engineering specifications.
- **Phases 1 through 8** are formally designated as **PLANNED**, awaiting sequential implementation and rigorous verification gate enforcement.
