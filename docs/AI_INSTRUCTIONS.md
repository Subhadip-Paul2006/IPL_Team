# AI Architectural Principles, Coding Standards & Domain Guardrails

**Project Title**: Rajasthan Royals Squad Intelligence & Historical Performance Engine  
**Event**: IPL 2027 Auction Scouting Hackathon  
**Target Franchise**: Rajasthan Royals (RR)  
**Document Version**: 1.0.0-PROD-SPEC  
**Status**: `[STATUS: ACTIVE MANDATORY DIRECTIVE - GREENFIELD BASELINE]`  
**Date**: November 2026  
**Primary Authors**: Principal Software Architect, Systems Governance Lead, Lead Cricket Data Scientist  

---

## 1. Purpose & Authority

This document serves as the **Supreme Engineering Constitution** for all artificial intelligence agents, software engineers, and automated code synthesis systems operating within this repository. 

Every architectural design, database migration, analytical formulation, API endpoint, and test suite MUST strictly comply with the principles, standards, and domain guardrails detailed herein. Any pull request or automated code synthesis that violates any directive in this document shall be automatically rejected by the **Data Quality & Validation Agent** and the **Chief Architect**.

---

## 2. Core Architectural Tenets

```
+----------------------------------------------------------------------------------------------------+
|                                    CORE ARCHITECTURAL TENETS                                       |
+----------------------------------------------------------------------------------------------------+
|  1. DETERMINISTIC REPRODUCIBILITY                                                                  |
|     Bit-for-bit identical outputs from identical raw seeds across all execution environments.     |
|                                                                                                    |
|  2. CENTRAL NORMALISED 3NF RELATIONAL CORE                                                         |
|     Zero redundant transaction data; single source of truth; strict foreign key referential integrity.|
|                                                                                                    |
|  3. READ-ONLY IMMUTABLE DATA LAKE                                                                  |
|     Raw source files (CricSheet/) are immutable assets staged into a read-only Quarantine Lake.     |
|                                                                                                    |
|  4. UNBROKEN END-TO-END DATA LINEAGE                                                               |
|     Every metric displayed on the UI traces back via foreign keys to underlying delivery records.   |
|                                                                                                    |
|  5. STRICT SEPARATION OF CONCERNS                                                                  |
|     Ingestion -> Staging -> Normalisation -> Enrichment -> Analytics -> APIs -> Presentation.       |
+----------------------------------------------------------------------------------------------------+
```

### 2.1 Deterministic Reproducibility
- **Mandate**: All statistical calculations, probabilistic valuation models, and simulation routines must yield bit-for-bit identical results when executed with identical raw inputs and configuration parameters.
- **Random Number Generation**: Stochastic algorithms (such as the 10,000-iteration Monte Carlo tournament simulator) MUST require an explicit integer random seed parameter (e.g., `seed=42`). The use of unseeded pseudo-random number generators or system-time seeds is strictly prohibited.
- **Pure Functions**: Core statistical transformation routines must be written as pure functions with zero external side effects, operating solely on their explicit input parameters.

### 2.2 Central Normalised 3NF Relational Core
- **Mandate**: All production match, player, and delivery entities must reside in a fully normalized Third Normal Form (3NF) relational schema within PostgreSQL 16+.
- **Data Deduplication**: Redundant transaction attributes (such as repeating player names, team names, or venue city strings on delivery records) are strictly forbidden. Deliveries must reference canonical entity IDs via foreign keys.
- **Materialized Views for Performance**: High-performance analytical rollups (e.g., career phase aggregates, rolling workloads) must be maintained in dedicated materialized views or analytical feature tables (`derived_features`), clearly isolated from core operational tables.

### 2.3 Read-Only Immutable Data Lake (Quarantine Lake Architecture)
- **Mandate**: The local raw data archive (`d:\New folder (2)\CricSheet\`) is an immutable, read-only data repository.
- **Prohibition on Direct Mutation**: No agent or script shall modify, delete, rename, or append to any file within `CricSheet/`.
- **Quarantine Staging**: All raw JSON and YAML payloads must be copied into PostgreSQL raw staging tables (`stg_cricsheet_matches`, `stg_cricsheet_deliveries`) accompanied by SHA-256 cryptographic hashes. Any malformed payload that fails parsing is staged into `stg_quarantine_log` with full error traces, preserving the raw data stream without halting the batch ingestion.

### 2.4 Unbroken End-to-End Data Lineage
- **Mandate**: Every statistical metric, valuation figure, and tactical card displayed on the user interface must maintain an unbroken provenance chain tracing back to the raw source file name, delivery timestamp, and calculation version.
- **Audit Table**: The `derived_features` table must store `source_file_id`, `calculation_timestamp`, `model_version`, and `raw_record_hash` for every calculated row.

---

## 3. Technology Stack & Coding Standards

```
+----------------------------------------------------------------------------------------------------+
|                                    APPROVED TECHNOLOGY STACK                                       |
+-------------------+-----------------------------------+--------------------------------------------+
| Layer             | Technology / Framework            | Minimum Version / Standard                 |
+-------------------+-----------------------------------+--------------------------------------------+
| Database Core     | PostgreSQL                        | 16.0+ (ANSI SQL, 3NF Normalized)           |
| In-Memory Cache   | Redis                             | 7.2+ (Sub-200ms query caching)             |
| Backend Service   | Python / FastAPI                  | Python 3.11+, Pydantic v2, SQLAlchemy 2.0  |
| Scientific Math   | NumPy / Pandas / Scipy            | NumPy 1.26+, Pandas 2.2+                   |
| Frontend Web App  | Next.js / React / TypeScript      | Next.js 14+, TypeScript 5.3+ (Strict)      |
| Styling & UI      | Tailwind CSS / Lucide Icons       | Tailwind 3.4+                              |
| Data Visualization| Recharts / Apache ECharts         | ECharts 5.5+, Recharts 2.12+               |
| Network Graphs    | Cytoscape.js / React Flow         | React Flow 11.11+                          |
+-------------------+-----------------------------------+--------------------------------------------+
```

### 3.1 Python Standards (Backend & Analytics)
1. **PEP 8 & Type Hints**: All Python source code must comply with PEP 8 style standards and mandate strict type hinting (`from typing import Optional, List, Dict, Union, Tuple`).
2. **Pydantic v2 Validation**: All API request and response models must be defined as Pydantic v2 schemas with explicit field validators, regex constraints, and documentation strings.
3. **Immutability**: Domain models representing facts (e.g. a completed delivery record) must use immutable constructs (such as `@dataclass(frozen=True)` or Pydantic `frozen=True`).
4. **Docstrings**: All functions, classes, and modules must include Google-style docstrings specifying:
   ```python
   def compute_true_strike_rate(
       observed_runs: int,
       balls_faced: int,
       expected_runs: float
   ) -> Optional[float]:
       """Computes the context-adjusted True Strike Rate relative to phase par.

       Args:
           observed_runs: Total runs scored off the bat by the player.
           balls_faced: Total legal deliveries faced by the player.
           expected_runs: Tournament phase baseline expected runs for balls faced.

       Returns:
           Context-adjusted True Strike Rate (TSR) in runs per 100 balls,
           or None if balls_faced is zero.

       Raises:
           ValueError: If balls_faced is negative or observed_runs is negative.
       """
   ```

### 3.2 SQL & Database Standards (PostgreSQL 16+)
1. **Naming Conventions**:
   - Table names: plural `snake_case` (e.g., `matches`, `deliveries`, `player_aliases`).
   - Column names: singular `snake_case` (e.g., `match_id`, `delivery_number`, `is_super_over`).
   - Primary keys: single-column `id` (BIGSERIAL or UUID) or explicit composite keys.
   - Foreign keys: `<referenced_table_singular>_id` (e.g., `batter_id`, `venue_id`).
2. **Timestamps & Timezones**: All temporal columns must use `TIMESTAMPTZ` and store timestamps in UTC conforming to ISO-8601 (`YYYY-MM-DDTHH:MM:SSZ`).
3. **Explicit Type Casting**: Avoid loose typing; use precise numeric definitions:
   - Currency: `NUMERIC(14, 2)` (e.g. purse amounts in INR).
   - Strike rates & economies: `NUMERIC(6, 2)`.
   - Probabilities / Win percentages: `NUMERIC(5, 4)` ($0.0000$ to $1.0000$).
   - Coordinates: `NUMERIC(6, 3)` (trajectory meters).
4. **Referential Integrity**: Foreign keys must explicitly specify delete actions, defaulting to `ON DELETE RESTRICT` for audit tables to prevent accidental deletion of historical data.

### 3.3 TypeScript & Frontend Standards (Next.js 14+)
1. **Strict Type Safety**: `tsconfig.json` must enforce `"strict": true`, `"noImplicitAny": true`, and `"strictNullChecks": true`. The use of `any` is strictly prohibited.
2. **Functional React Components**: All UI components must be written as functional React components with explicit prop interfaces:
   ```typescript
   interface MatchupCardProps {
     readonly batterId: string;
     readonly bowlerId: string;
     readonly seasonYear: number;
     readonly isNightFixture: boolean;
   }
   ```
3. **Zero Mockup Hardcoding in Production**: UI components must consume structured data from FastAPI endpoints. Mock arrays embedded in component files are prohibited.

---

## 4. Data Provenance, Licensing & Attribution Compliance

### 4.1 Legal Licensing Attribution
Every output, API response, exported report, and UI view generated by this platform must comply with the licensing agreements governing the underlying datasets:

| Data Source | License Standard | Mandatory Attribution Text | Application Guardrail |
|---|---|---|---|
| **CricSheet** | Open Data Commons Attribution License (ODC-By) v1.0 | *"Cricket match data sourced from CricSheet (cricsheet.org), licensed under the Open Data Commons Attribution License (ODC-By) v1.0."* | Attribution must be displayed in the application footer and embedded in CSV/JSON data exports. |
| **Open-Meteo** | Creative Commons Attribution 4.0 (CC BY 4.0) | *"Historical weather data provided by Open-Meteo.com under Creative Commons Attribution 4.0 International (CC BY 4.0)."* | Environmental data must be labeled as macro-weather context only. |
| **Kaggle Datasets** | Creative Commons (CC BY-SA / CC BY 4.0) | *"Historical records cross-referenced against Kaggle IPL open datasets under respective CC licensing terms."* | Verified against CricSheet gold-standard; anomalous 2007 records quarantined. |
| **HawkeyeStats** | Third-Party GitHub Repository (`alittlefitness`) | *"Ball-tracking trajectory metrics derived from HawkeyeStats open research repository."* | Isolated as optional nullable enrichment; strict null-safety enforced. |

### 4.2 Data Provenance Architecture
Every row in `derived_features` must maintain foreign keys to its calculation lineage:
```sql
CREATE TABLE derived_features (
    id BIGSERIAL PRIMARY KEY,
    feature_name VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50) NOT NULL, -- 'PLAYER', 'VENUE', 'MATCHUP'
    entity_id BIGINT NOT NULL,
    feature_value NUMERIC(10, 4) NOT NULL,
    calculation_timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    model_version VARCHAR(50) NOT NULL,
    source_match_count INTEGER NOT NULL,
    source_file_hashes TEXT[] NOT NULL
);
```

---

## 5. Strict Statistical Correctness & Domain Rules

The integrity of this analytics platform rests upon unwavering fidelity to official cricket laws (MCC Laws of Cricket), ICC T20 International Playing Conditions, and BCCI IPL Playing Conditions. 

AI agents and software engineers MUST enforce the following nine domain rules:

```
+----------------------------------------------------------------------------------------------------+
|                                    NINE STATISTICAL COMMANDMENTS                                   |
+----------------------------------------------------------------------------------------------------+
|  RULE 1: NEVER TREAT MISSING AS ZERO                                                              |
|  RULE 2: NEVER FABRICATE OR HALLUCINATE STATISTICS                                                 |
|  RULE 3: NEVER CONFUSE BOWLING STYLE WITH DELIVERY VARIATION                                       |
|  RULE 4: NEVER INTERPRET HAWK-EYE BALL COORDINATES AS FIELDER COORDINATES                          |
|  RULE 5: NEVER ATTRIBUTE BYES, LEGBYES, OR PENALTY RUNS TO BOWLER'S RUNS CONCEDED                 |
|  RULE 6: STRICT SUPER OVER ISOLATION PROTOCOL                                                     |
|  RULE 7: RAIN-INTERRUPTED (DLS) REVISED TARGET ACCOUNTING                                          |
|  RULE 8: IMPACT PLAYER SUBSTITUTION ACCOUNTING (UP TO 12 PARTICIPANTS PER TEAM)                    |
|  RULE 9: ZERO BALLS FACED / ZERO OVERS BOWLED HANDLING (DNB / DNBOWL != 0.0)                      |
+----------------------------------------------------------------------------------------------------+
```

### Rule 1: NEVER Treat Missing as Zero
- **Domain Reality**: In sports analytics, the absence of an observation is fundamentally distinct from an observed value of zero.
- **Specific Applications**:
  1. *Ball Tracking Speed*: If radar/Hawk-Eye optical tracking did not record delivery speed, `ball_speed_kph` must be `NULL`. Setting it to `0.0 km/h` produces catastrophic errors in pace-filtering algorithms.
  2. *Pitch Landing Coordinates*: If Hawk-Eye coordinates are missing, `pitch_x_coord` and `pitch_y_coord` must be `NULL`. Setting them to `(0.0, 0.0)` erroneously plots the ball dead-center on the middle stump!
  3. *Batting Average / Economy Rate*: A player with zero dismissals or zero legal balls bowled cannot have a mathematical average computed. Return `NULL`, never `0.0`.
- **Database Constraint**: Columns representing physical measurements must be nullable without default zeros.

### Rule 2: NEVER Fabricate or Hallucinate Statistics
- **Domain Reality**: All metrics must be mathematically derivable from verified historical records.
- **Strict Prohibition**: Under no circumstances shall an AI agent generate synthetic player profiles, invent fictional match scorecards, create placeholder deliveries, or fabricate model outputs to simulate a complete dataset.
- **Validation Mandate**: The Data Quality Agent shall run automated checksum verifications between raw deliveries and career aggregates. Any detected deviation results in an immediate build termination.

### Rule 3: NEVER Confuse Bowling Style with Delivery Variation
- **Domain Reality**: A bowler's **style** is their permanent physical bowling action registered with the match referee. A **delivery variation** is an individual ball mechanic chosen for a specific delivery.
- **Taxonomy Definition**:
  - *Bowling Styles (Permanent)*:
    1. Right-Arm Fast / Fast-Medium (RAF)
    2. Left-Arm Fast / Fast-Medium (LAF)
    3. Right-Arm Offbreak (OS)
    4. Left-Arm Orthodox (SLA)
    5. Right-Arm Legbreak (LBG)
    6. Left-Arm Unorthodox / Chinaman (LAC)
  - *Delivery Variations (Tactical Mechanics)*:
    - Slower ball, Off-cutter, Leg-cutter, Knuckle ball, Yorker, Bouncer.
    - Carrom ball, Doosra, Arm ball, Top-spinner, Slider, Flipper, Googly.
- **Engine Rule**: When generating the "Batter vs Bowling Type Matrix" (FR-07), aggregate strictly against the bowler's registered **bowling style**, not ad-hoc delivery commentary tags.

### Rule 4: NEVER Interpret Hawk-Eye Post-Shot Coordinates as Fielder Coordinates
- **Domain Reality**: Hawk-Eye optical tracking systems record ball trajectory in two distinct phases: pre-shot (release to pitch bounce to bat impact) and post-shot (bat impact to boundary or fielder interception).
- **Strict Prohibition**: The landing coordinate of the ball or its point of rest in the outfield MUST NEVER be interpreted as the physical spatial position of the fielding player.
- **Reasoning**: Outfield ball coordinates represent the terminal trajectory of the ball, not the movement path, starting depth, or physical location of the fielder making the stop or catch.

### Rule 5: NEVER Attribute Byes, Legbyes, or Penalty Runs to Bowler's Runs Conceded
- **Domain Reality**: Under ICC Law 21 (No ball), Law 22 (Wide ball), and Law 23 (Bye and Leg bye), runs scored from byes, leg-byes, and penalty runs are awarded to the team total but are NOT debited against the bowler's bowling analysis.
- **Mathematical Formulation for Bowler Runs Conceded**:
  $$\text{Bowler Runs Conceded} = \sum (\text{runs\_batter} + \text{wides} + \text{noballs})$$
  $$\text{Byes and Legbyes Excluded}: \text{byes} = 0, \text{legbyes} = 0, \text{penalty} = 0$$
- **Verification Rule**: Any bowling economy calculation that includes byes or leg-byes in the numerator is invalid and must be rejected.

### Rule 6: Strict Super Over Isolation Protocol
- **Domain Reality**: In official ICC and BCCI statistical records, runs scored, wickets taken, and deliveries bowled during a Super Over (one-over eliminator) to break a tie DO NOT increment a player's official career batting or bowling statistics.
- **Implementation Mandate**:
  1. All innings where `innings.is_super_over = true` must be excluded from default career aggregation views:
     ```sql
     CREATE VIEW v_career_batting AS
     SELECT 
         batter_id,
         SUM(runs_batter) AS career_runs,
         COUNT(id) AS balls_faced
     FROM deliveries
     WHERE is_super_over = false
     GROUP BY batter_id;
     ```
  2. Super Over performances must be indexed into a dedicated `super_over_performances` table to serve as high-leverage clutch situational metrics.

### Rule 7: Rain-Interrupted (DLS) Revised Target Accounting
- **Domain Reality**: In matches affected by adverse weather, target scores and innings overs are revised using the Duckworth-Lewis-Stern (DLS) method.
- **Calculation Rule**:
  - In a match truncated to 6 overs with a revised target of 48 (e.g. Match 1082648), the required run rate must be calculated using the revised target and revised overs:
    $$\text{Required Run Rate} = \frac{48 - \text{Current Score}}{6.0 - \text{Overs Completed}}$$
  - **Prohibition**: NEVER divide the target by the standard 20-over quota when the match was officially shortened.
  - Deliveries in truncated matches must have their match phases dynamically scaled proportionally to innings length.

### Rule 8: Impact Player Substitution Accounting
- **Domain Reality**: Under modern IPL playing conditions (2023–present), each team may introduce one tactical Impact Player substitute during the match from a pre-nominated list of 5 substitutes.
- **Schema & Modeling Mandate**:
  1. A team roster for an IPL match may include up to 12 participating players (11 starters + 1 active Impact Player).
  2. The `squad_memberships` table must support the flag `is_impact_player = true`.
  3. The `deliveries` table must support delivery-level replacement events recording the outgoing player, incoming player, and exact over timestamp.
  4. In squad simulation (FR-16, FR-17), the constraint solver must allow exactly one tactical replacement per team per match.

### Rule 9: Zero Balls Faced / Zero Overs Bowled Handling
- **Domain Reality**: A player named in the official starting Playing XI who does not bat (Did Not Bat - DNB) or does not bowl (Did Not Bowl - DNBowl) must have their appearance recorded without distorting their averages.
- **Rule Formulation**:
  - Batting Average: $\frac{\text{Career Runs}}{\text{Career Dismissals}}$. If dismissals $= 0$ and balls faced $> 0$, average is undefined (conventionally displayed as `career_runs*` or `NULL`). If balls faced $= 0$, average is strictly `NULL` / `DNB`.
  - Bowling Average & Economy: If balls bowled $= 0$, economy is strictly `NULL` / `DNBowl`. NEVER return `0.00` RPO for a player who did not bowl!

---

## 6. Prohibited Practices & Security Guardrails

The following ten actions are **strictly prohibited** across all agents and automated scripts:

```
+----------------------------------------------------------------------------------------------------+
|                                    STRICT SYSTEM PROHIBITIONS                                      |
+----+-----------------------------------------------------------------------------------------------+
| #  | Prohibited Action Description                                                                 |
+----+-----------------------------------------------------------------------------------------------+
| P1 | Generating synthetic, mock, or hallucinated player performance records.                      |
| P2 | Mutating, modifying, renaming, or deleting raw match files inside `CricSheet/`.                |
| P3 | Imputing missing values with `0.0` or arbitrary global averages.                              |
| P4 | Permitting Super Over statistics to increment career batting or bowling totals.                |
| P5 | Attributing byes, leg-byes, or penalty runs to bowler runs conceded.                         |
| P6 | Permitting more than 4 overseas players in any simulated Starting Playing XI.                 |
| P7 | Using raw, unparameterized SQL queries in API endpoints (Mandatory SQLi prevention).          |
| P8 | Executing live external scraping scripts or making unauthorized network API calls.            |
| P9 | Bypassing or suppressing failed automated quality test assertions.                            |
| P10| Confusing macro-meteorological weather (Open-Meteo) with direct in-ground pitch sensors.       |
+----+-----------------------------------------------------------------------------------------------+
```

### 6.1 Database Security (SQL Injection Prevention)
All database interactions in FastAPI services, background tasks, and migration scripts must use parameterized SQL queries or the SQLAlchemy 2.0 ORM. Raw string formatting (`f"SELECT * FROM players WHERE name = '{name}'"`) is strictly forbidden and constitutes a critical security vulnerability.

### 6.2 Regulatory Validation Invariants
Any squad configuration generated by the optimization solver or user interface must pass hard validation checks before persisting:
```python
def validate_playing_xi(playing_xi: List[Player]) -> None:
    if len(playing_xi) != 11:
        raise ValidationError(f"Playing XI must contain exactly 11 players; received {len(playing_xi)}.")
    
    overseas_count = sum(1 for p in playing_xi if p.is_overseas)
    if overseas_count > 4:
        raise ValidationError(f"Playing XI exceeds overseas limit: {overseas_count} overseas players (maximum 4).")
        
    wk_count = sum(1 for p in playing_xi if p.is_wicketkeeper)
    if wk_count < 1:
        raise ValidationError("Playing XI must contain at least 1 designated wicketkeeper.")
```

---

## 7. Conclusion & Engineering Attestation

This document forms an unbroken chain of architectural and domain constraints. By maintaining strict adherence to these principles, the engineering team guarantees that the **Rajasthan Royals Squad Intelligence & Historical Performance Engine** is built upon forensic mathematical accuracy, regulatory validity, and elite production engineering standards.
