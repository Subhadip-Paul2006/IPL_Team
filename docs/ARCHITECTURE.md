# System Architecture & Technical Design Specification
**Rajasthan Royals Squad Intelligence & Historical Performance Engine**  
**Tournament**: Indian Premier League (IPL) 2027 Auction Preparation & Tactical Engine  
**Document Version**: 1.0.0 (Engineering Baseline)  
**Status**: [STATUS: PLANNED - GREENFIELD BASELINE]  
**Author**: Engineering Architecture Team (`teamwork_worker_2`)  

---

## 1. Architectural Overview & Design Principles

> **Architecture Baseline Status**: `[STATUS: PLANNED - GREENFIELD BASELINE]`  
> All 10 architectural diagrams, data flows, entity relationship diagrams, and Architectural Decision Records (ADRs) depict the approved target state for greenfield engineering.

The Rajasthan Royals Squad Intelligence & Historical Performance Engine is architected as a distributed, high-performance analytical system designed for tactical decision support during the IPL 2027 auction and campaign planning `[STATUS: PLANNED - GREENFIELD BASELINE]`. The architecture is guided by six core engineering principles:

1. **Deterministic Reproducibility**: Every metric, feature vector, and valuation must be fully reproducible from raw source payloads accompanied by SHA-256 cryptographic digests.
2. **Strict Third Normal Form (3NF) Relational Core**: Data integrity is paramount. Hard foreign key constraints, composite unique indexes, and domain check constraints prevent corrupt data from propagating into tactical decisions.
3. **Decoupled Analytical Feature Store**: Pristine historical scorecard ledgers are segregated from machine learning projections and valuation models via `derived_features`.
4. **Declarative Partitioning for Scalability**: The high-volume delivery stream (>250,000 deliveries) is partitioned declaratively by season to ensure partition pruning and sub-50ms query responses.
5. **Multi-Tier Identity Resolution**: Player name variations across disparate providers are resolved using a deterministic-to-probabilistic 4-tier waterfall anchored by Cricsheet registry hashes.
6. **Domain-Specific Cricket Integrity**: Cricket rules (MCC Laws & IPL Playing Conditions) are hard-coded into database and API contracts: Super Overs are segregated, DLS revised targets are normalized, penalty runs are excluded from bowler charges, and missing data evaluates to `NULL` rather than fabricated zeros.

---

## 2. Complete System Architecture Diagrams (10 Mermaid Specifications)

All 10 diagrams below adhere strictly to Mermaid syntax standards, utilizing unique node identifiers, escaped labels, and explicit directional connections.

---

### 2.1 Diagram 1: High-Level System Architecture

```mermaid
flowchart TD
    subgraph Client_Tier["Client Presentation Layer (Next.js 15 / React 19)"]
        UI_Dashboard["Scouting Dashboard & War Room UI"]
        UI_PlayerProfile["Player Profile & Spray Maps"]
        UI_MatchupMatrix["Batter vs Bowler Matchup Matrix"]
        UI_AuctionSim["Auction Bidding & Purse Simulator"]
        UI_SquadDepth["Squad Depth Chart (React Flow)"]
    end

    subgraph API_Gateway["API & Orchestration Layer (FastAPI / ASGI)"]
        Gateway["FastAPI Async Gateway (Uvicorn Workers)"]
        Auth["RBAC & Session Management"]
        Router_Player["Player Analytics Router"]
        Router_Scouting["Auction Scouting Router"]
        Router_Match["Match & Delivery Router"]
        Redis_Cache[("Redis 7 In-Memory Cache")]
    end

    subgraph Analytical_Engine["Analytics & Computation Engine (NumPy / Pandas)"]
        Engine_VORP["VORP & Valuation Calculator"]
        Engine_Phase["Phase & Situational Aggregator"]
        Engine_Matchup["Head-to-Head Matchup Engine"]
        Engine_Simulation["Monte Carlo Auction Simulator"]
    end

    subgraph Storage_Tier["Central Data Store (PostgreSQL 16)"]
        DB_Relational[("PostgreSQL Normalized Core (20 Entities)")]
        DB_Partitioned[("Partitioned Deliveries Ledger")]
        DB_Features[("Derived Feature Store")]
        DB_Staging[("Source Records & Audit Log")]
    end

    subgraph Ingestion_Tier["Data Acquisition & ELT Pipeline"]
        Ingest_Cricsheet["Cricsheet JSON Loader"]
        Ingest_Kaggle["Kaggle Historical CSV Parser"]
        Ingest_Weather["Open-Meteo Weather API Worker"]
        Ingest_Hawkeye["HawkEye Ball Tracking Importer"]
        Engine_Identity["Multi-Tier Identity Resolution Engine"]
    end

    UI_Dashboard --> Gateway
    UI_PlayerProfile --> Gateway
    UI_MatchupMatrix --> Gateway
    UI_AuctionSim --> Gateway
    UI_SquadDepth --> Gateway

    Gateway --> Auth
    Auth --> Router_Player
    Auth --> Router_Scouting
    Auth --> Router_Match

    Router_Player <--> Redis_Cache
    Router_Scouting <--> Redis_Cache

    Router_Player --> Engine_Phase
    Router_Player --> Engine_Matchup
    Router_Scouting --> Engine_VORP
    Router_Scouting --> Engine_Simulation
    Router_Match --> DB_Partitioned

    Engine_VORP <--> DB_Features
    Engine_Phase <--> DB_Partitioned
    Engine_Matchup <--> DB_Partitioned

    Ingest_Cricsheet --> DB_Staging
    Ingest_Kaggle --> DB_Staging
    Ingest_Weather --> DB_Staging
    Ingest_Hawkeye --> DB_Staging

    DB_Staging --> Engine_Identity
    Engine_Identity --> DB_Relational
    Engine_Identity --> DB_Partitioned
```

---

### 2.2 Diagram 2: Data Ingestion Architecture

```mermaid
flowchart TD
    subgraph Data_Sources["External Reference Data Sources"]
        SRC_Cric["Cricsheet Archive (JSON/ZIP)"]
        SRC_Kaggle["Kaggle IPL Datasets (CSV)"]
        SRC_Weather["Open-Meteo Historical Weather (API)"]
        SRC_Hawkeye["HawkEye Tracking Data (JSON)"]
        SRC_BCCI["Official BCCI / IPL Rosters"]
    end

    subgraph Ingestion_Workers["Ingestion & Checksum Service"]
        Worker_Cric["Cricsheet Ingest Worker"]
        Worker_Kaggle["Kaggle CSV Ingest Worker"]
        Worker_Weather["Weather API Client (Rate-Limited)"]
        Worker_Hawkeye["HawkEye Format Parser"]
        Worker_BCCI["Roster Verification Worker"]
        Hasher["SHA-256 Digest Generator"]
    end

    subgraph Staging_Layer["Raw Staging & Audit Layer"]
        Staging_DB[("PostgreSQL: source_records")]
        Dead_Letter[("Dead-Letter Quarantine Table")]
        Raw_Archive[("Raw Payload Blob Storage")]
    end

    subgraph Validation_Gate["Schema Validation & Quality Gate"]
        Pydantic_Validator["Pydantic v2 Schema Validator"]
        Anomaly_Detector["Payload Structural Anomaly Check"]
        Pass_Queue["Validated Processing Queue"]
    end

    SRC_Cric --> Worker_Cric
    SRC_Kaggle --> Worker_Kaggle
    SRC_Weather --> Worker_Weather
    SRC_Hawkeye --> Worker_Hawkeye
    SRC_BCCI --> Worker_BCCI

    Worker_Cric --> Hasher
    Worker_Kaggle --> Hasher
    Worker_Weather --> Hasher
    Worker_Hawkeye --> Hasher
    Worker_BCCI --> Hasher

    Hasher --> Staging_DB
    Hasher --> Raw_Archive

    Staging_DB --> Pydantic_Validator
    Pydantic_Validator --> Anomaly_Detector
    Anomaly_Detector -- "Validation Pass" --> Pass_Queue
    Anomaly_Detector -- "Schema Violation / Corrupt" --> Dead_Letter
```

---

### 2.3 Diagram 3: Raw-to-Normalized Data Pipeline

```mermaid
flowchart TD
    subgraph Stage1["Stage 1: Ingestion & Raw Staging"]
        S1_Raw["Raw Source Record in source_records"]
        S1_Hash["SHA-256 Idempotency Verification"]
    end

    subgraph Stage2["Stage 2: Validation & Extraction"]
        S2_Validate["Pydantic v2 Domain Validation"]
        S2_Extract["Extract Entities: Match, Innings, Deliveries, Players"]
    end

    subgraph Stage3["Stage 3: Identity & Entity Resolution"]
        S3_PlayerRes["Player Identity Resolution (4-Tier)"]
        S3_VenueRes["Venue Normalization & City Resolution"]
        S3_TeamRes["Franchise Name Canonicalization"]
    end

    subgraph Stage4["Stage 4: Relational Decomposition"]
        S4_Matches["Insert into matches"]
        S4_Innings["Insert into innings (Tag is_super_over)"]
        S4_Deliveries["Decompose & Insert into deliveries"]
        S4_Fielding["Extract & Insert into fielding_events"]
    end

    subgraph Stage5["Stage 5: Scorecard & Spell Aggregation"]
        S5_Batting["Materialize batting_innings Scorecards"]
        S5_Bowling["Materialize bowling_spell Scorecards"]
        S5_SuperOverSeg["Enforce Super Over Exclusion Rules"]
    end

    subgraph Stage6["Stage 6: Integrity Verification"]
        S6_Reconcile["Cross-check Scorecard vs Delivery Sums"]
        S6_Commit["Commit Transaction / Update processing_status='Normalized'"]
    end

    S1_Raw --> S1_Hash
    S1_Hash --> S2_Validate
    S2_Validate --> S2_Extract

    S2_Extract --> S3_PlayerRes
    S2_Extract --> S3_VenueRes
    S2_Extract --> S3_TeamRes

    S3_PlayerRes --> S4_Matches
    S3_VenueRes --> S4_Matches
    S3_TeamRes --> S4_Matches

    S4_Matches --> S4_Innings
    S4_Innings --> S4_Deliveries
    S4_Deliveries --> S4_Fielding

    S4_Deliveries --> S5_Batting
    S4_Deliveries --> S5_Bowling
    S4_Fielding --> S5_Batting

    S5_Batting --> S5_SuperOverSeg
    S5_Bowling --> S5_SuperOverSeg

    S5_SuperOverSeg --> S6_Reconcile
    S6_Reconcile --> S6_Commit
```

---

### 2.4 Diagram 4: Contextual Enrichment Architecture

```mermaid
flowchart TD
    subgraph Core_Deliveries["Core Granular Stream"]
        DELIV["deliveries (Ball-by-Ball Ledger)"]
    end

    subgraph Spatial_Enrichment["Spatial & Venue Dimension"]
        VENUE["venues Entity"]
        PITCH["pitch_conditions Entity"]
        DIM_JOIN["Compute Boundary Dimensions & Altitude Drag Index"]
    end

    subgraph Environmental_Enrichment["Environmental Dimension"]
        WEATHER["weather_conditions Entity"]
        DEW_CALC["Calculate Dew Point Delta & Wet Ball Probability"]
    end

    subgraph Situational_Enrichment["Tactical Situational Dimension"]
        PHASE_TAG["Tag Match Phase: Powerplay / Middle 1 / Middle 2 / Death"]
        CHASE_METRIC["Compute RRR vs CRR & Wickets-in-Hand"]
        LEVERAGE["Compute Leverage Index & Win Expectancy Swing"]
    end

    subgraph Feature_Materialization["Derived Feature Storage"]
        FEATURE_STORE[("derived_features Table")]
        CACHE_WARM["Warm Redis Feature Cache"]
    end

    DELIV --> DIM_JOIN
    VENUE --> DIM_JOIN
    PITCH --> DIM_JOIN

    DELIV --> DEW_CALC
    WEATHER --> DEW_CALC

    DELIV --> PHASE_TAG
    PHASE_TAG --> CHASE_METRIC
    CHASE_METRIC --> LEVERAGE

    DIM_JOIN --> FEATURE_STORE
    DEW_CALC --> FEATURE_STORE
    LEVERAGE --> FEATURE_STORE

    FEATURE_STORE --> CACHE_WARM
```

---

### 2.5 Diagram 5: Player Identity Resolution Workflow

```mermaid
flowchart TD
    Start(["Incoming Raw Player Record"]) --> T1_Check{"Tier 1: External Registry Key Present?"}
    
    T1_Check -- "Yes" --> T1_Lookup["Match via cricsheet_id, espn_id, or bcci_id"]
    T1_Lookup --> T1_Match{"Found in players?"}
    T1_Match -- "Yes" --> T1_Success["Resolve Canonical player_id<br/>Confidence: 1.000"] --> Done(["Resolved"])
    T1_Match -- "No" --> T2_Check
    T1_Check -- "No" --> T2_Check{"Tier 2: Exact Match in player_aliases?"}

    T2_Check -- "Yes" --> T2_Success["Resolve Canonical player_id<br/>Confidence: 1.000"] --> Done
    T2_Check -- "No" --> T3_Check{"Tier 3: Name + Team + Date Intersection?"}

    T3_Check -- "Unique Match" --> T3_Success["Resolve player_id<br/>Insert to player_aliases<br/>Confidence: 0.980"] --> Done
    T3_Check -- "Ambiguous or None" --> T4_Fuzzy["Tier 4: Jaro-Winkler & Levenshtein Analysis"]

    T4_Fuzzy --> T4_Filter["Candidate Pool Filter (JW >= 0.92, Lev <= 2)"]
    T4_Filter --> T4_Cross["Cross-Validate Biometrics: Role, Hand, Arm, Active Era"]
    T4_Cross --> T4_Score{"Score >= 0.950 & Single Candidate?"}

    T4_Score -- "Yes" --> T4_Success["Resolve player_id<br/>Insert Alias (is_verified=FALSE)<br/>Confidence: Calculated"] --> Done
    T4_Score -- "No" --> T4_Quarantine["QUARANTINE RECORD<br/>Flag needs_review=TRUE in player_aliases<br/>Alert Data Steward"] --> HumanQueue(["Human Review Queue"])
```

---

### 2.6 Diagram 6: Player Analytics Workflow

```mermaid
flowchart TD
    Request(["Scout Request: GET /api/v1/players/{id}/profile"]) --> CacheCheck{"Check Redis Cache"}
    
    CacheCheck -- "Cache Hit" --> ReturnCache["Return Cached JSON Payload<br/>(Latency < 10ms)"] --> Response(["HTTP 200 OK Response"])
    
    CacheCheck -- "Cache Miss" --> QueryDB["Query PostgreSQL: batting_innings, bowling_spell, deliveries"]
    
    QueryDB --> FilterData["Filter Out Super Overs (is_super_over=FALSE)"]
    
    FilterData --> VectorCompute["Vectorized NumPy / Pandas Pipeline"]
    
    subgraph Analytics_Pipeline["Analytical Calculation Modules"]
        M1["True Strike Rate (TSR) & True Economy (TER)"]
        M2["Phase Distributions: PP / Mid 1 / Mid 2 / Death"]
        M3["Bowling Matchup Splits: vs SLA / Leg-spin / Off-spin / Pace"]
        M4["Clutch Index (Leverage Index Weighted Performance)"]
        M5["Venue Performance Deviations (SMS Stadium vs Away)"]
    end
    
    VectorCompute --> M1
    VectorCompute --> M2
    VectorCompute --> M3
    VectorCompute --> M4
    VectorCompute --> M5

    M1 --> AssembleJSON["Assemble Pydantic v2 Response Payload"]
    M2 --> AssembleJSON
    M3 --> AssembleJSON
    M4 --> AssembleJSON
    M5 --> AssembleJSON

    AssembleJSON --> StoreCache["Write to Redis Cache (TTL = 3600s)"]
    StoreCache --> Response
```

---

### 2.7 Diagram 7: Central Database Entity Relationship Diagram (ERD Covering All 20 Entities)

```mermaid
erDiagram
    PLAYERS ||--o{ PLAYER_ALIASES : "has"
    DATA_SOURCES ||--o{ PLAYER_ALIASES : "sourced_from"
    DATA_SOURCES ||--o{ SOURCE_RECORDS : "provides"
    PLAYERS ||--o{ SQUAD_MEMBERSHIPS : "belongs_to"
    TEAMS ||--o{ SQUAD_MEMBERSHIPS : "contracts"
    SEASONS ||--o{ SQUAD_MEMBERSHIPS : "applies_to"
    COMPETITIONS ||--o{ SEASONS : "schedules"
    VENUES ||--o{ TEAMS : "hosts_home"
    VENUES ||--o{ MATCHES : "hosts_match"
    SEASONS ||--o{ MATCHES : "contains"
    TEAMS ||--o{ MATCHES : "plays_home"
    TEAMS ||--o{ MATCHES : "plays_away"
    PLAYERS ||--o{ MATCHES : "wins_potm"
    MATCHES ||--o{ PITCH_CONDITIONS : "has_surface"
    MATCHES ||--o{ WEATHER_CONDITIONS : "experiences"
    MATCHES ||--o{ INNINGS : "comprises"
    TEAMS ||--o{ INNINGS : "bats_in"
    TEAMS ||--o{ INNINGS : "bowls_in"
    INNINGS ||--o{ DELIVERIES : "contains_balls"
    PLAYERS ||--o{ DELIVERIES : "strikes"
    PLAYERS ||--o{ DELIVERIES : "bowls"
    PLAYERS ||--o{ DELIVERIES : "non_strikes"
    PLAYERS ||--o{ DELIVERIES : "dismissed"
    INNINGS ||--o{ BATTING_INNINGS : "records"
    PLAYERS ||--o{ BATTING_INNINGS : "bats"
    INNINGS ||--o{ BOWLING_SPELL : "records"
    PLAYERS ||--o{ BOWLING_SPELL : "delivers"
    DELIVERIES ||--o{ FIELDING_EVENTS : "results_in"
    PLAYERS ||--o{ FIELDING_EVENTS : "fields"
    PLAYERS ||--o{ PLAYER_AVAILABILITY : "tracks"
    SEASONS ||--o{ PLAYER_AVAILABILITY : "for_season"
    PLAYERS ||--o{ PLAYER_INJURIES : "suffers"
    PLAYERS ||--o{ DERIVED_FEATURES : "evaluates"

    PLAYERS {
        uuid player_id PK
        string canonical_name
        string nationality
        string primary_role
        string batting_hand
        string bowling_style
        string cricsheet_id UK
    }

    PLAYER_ALIASES {
        uuid alias_id PK
        uuid player_id FK
        string alias_name
        uuid source_id FK
        float confidence_score
        boolean is_verified
        boolean needs_review
    }

    DATA_SOURCES {
        uuid source_id PK
        string source_name UK
        string source_type
        string license_type
    }

    SOURCE_RECORDS {
        uuid record_id PK
        uuid source_id FK
        string external_entity_id
        string payload_sha256
        string processing_status
    }

    TEAMS {
        uuid team_id PK
        string team_name UK
        string short_code UK
        uuid home_venue_id FK
    }

    COMPETITIONS {
        uuid competition_id PK
        string name UK
        string competition_type
        int match_overs
    }

    SEASONS {
        uuid season_id PK
        uuid competition_id FK
        string season_year
        date start_date
    }

    SQUAD_MEMBERSHIPS {
        uuid membership_id PK
        uuid player_id FK
        uuid team_id FK
        uuid season_id FK
        string contract_type
        decimal salary_inr
        boolean is_overseas
    }

    VENUES {
        uuid venue_id PK
        string stadium_name
        string city
        decimal boundary_radius_meters
    }

    MATCHES {
        uuid match_id PK
        string external_cricsheet_id UK
        uuid season_id FK
        uuid venue_id FK
        uuid home_team_id FK
        uuid away_team_id FK
        date match_date
        string outcome_type
        boolean is_dls_applied
    }

    PITCH_CONDITIONS {
        uuid pitch_condition_id PK
        uuid match_id FK
        decimal pitch_pace_rating
        decimal pitch_bounce_rating
        decimal pitch_turn_rating
    }

    WEATHER_CONDITIONS {
        uuid weather_condition_id PK
        uuid match_id FK
        timestamp observation_timestamp
        decimal temperature_celsius
        decimal relative_humidity_pct
        string dew_impact_index
    }

    INNINGS {
        uuid innings_id PK
        uuid match_id FK
        int innings_number
        uuid batting_team_id FK
        uuid bowling_team_id FK
        boolean is_super_over
        int total_runs
        int total_wickets
    }

    DELIVERIES {
        uuid delivery_id PK
        string season_year PK
        uuid innings_id FK
        uuid match_id FK
        int over_number
        int ball_in_over
        int delivery_sequence
        uuid batter_id FK
        uuid bowler_id FK
        int runs_batter
        int runs_extras
        int runs_total
        boolean is_wicket
        string match_phase
    }

    BATTING_INNINGS {
        uuid batting_innings_id PK
        uuid innings_id FK
        uuid player_id FK
        int runs_scored
        int balls_faced
        decimal strike_rate
        boolean is_not_out
    }

    BOWLING_SPELL {
        uuid spell_id PK
        uuid innings_id FK
        uuid player_id FK
        int legal_balls_bowled
        int runs_conceded
        int wickets_taken
        decimal economy_rate
    }

    FIELDING_EVENTS {
        uuid fielding_event_id PK
        uuid delivery_id FK
        uuid player_id FK
        boolean is_substitute
        string event_type
        boolean is_successful
    }

    PLAYER_AVAILABILITY {
        uuid availability_id PK
        uuid player_id FK
        uuid season_id FK
        string availability_status
        boolean national_board_noc_granted
    }

    PLAYER_INJURIES {
        uuid injury_id PK
        uuid player_id FK
        date injury_date
        string injury_type
        string severity
        decimal recurrence_risk_score
    }

    DERIVED_FEATURES {
        uuid feature_id PK
        uuid player_id FK
        string feature_group
        string feature_name
        decimal feature_value_numeric
        string model_version
    }
```

---

### 2.8 Diagram 8: Player Profile Generation Workflow

```mermaid
flowchart TD
    Trigger(["Profile Generation Trigger: Player ID"]) --> FetchHistory["Query Historical Batting & Bowling Records"]
    
    FetchHistory --> Segregate["Segregate Super Overs & Apply DLS Overs Normalization"]
    
    subgraph Profile_Engine["Multidimensional Profile Synthesis"]
        Calc_TSR["Compute True Strike Rate by Phase: PP, Mid 1, Mid 2, Death"]
        Calc_TER["Compute True Economy Rate & Dot Ball Percentage"]
        Calc_Matchup["Pivot Batter vs Bowler & Bowling Archetype Splits"]
        Calc_Venue["Benchmark Venue Adjustment Multipliers (Home vs Away)"]
        Calc_Clutch["Evaluate High-Pressure Leverage Performance"]
        Calc_Health["Calculate Workload Load, Fatigue & Injury Recurrence Risk"]
    end
    
    Segregate --> Calc_TSR
    Segregate --> Calc_TER
    Segregate --> Calc_Matchup
    Segregate --> Calc_Venue
    Segregate --> Calc_Clutch
    Segregate --> Calc_Health
    
    Calc_TSR --> Synthesize["Synthesize Comprehensive Player Dossier JSON"]
    Calc_TER --> Synthesize
    Calc_Matchup --> Synthesize
    Calc_Venue --> Synthesize
    Calc_Clutch --> Synthesize
    Calc_Health --> Synthesize
    
    Synthesize --> PersistFeatures["Persist to derived_features Table (versioned v1.0)"]
    PersistFeatures --> CacheRedis["Cache Profile in Redis (Key: cache:player_profile:{id})"]
    CacheRedis --> Complete(["Profile Available for Scout Consumption"])
```

---

### 2.9 Diagram 9: Candidate Evaluation & Auction Scouting Workflow

```mermaid
flowchart TD
    StartScout(["Auction War Room Initialization"]) --> DefineGaps["Input Tactical Squad Gaps & Roster Needs<br/>(e.g., Death Bowler, Overseas Batting All-rounder)"]
    
    DefineGaps --> FilterCandidates["Filter Candidate Pool:<br/>Primary Role, Overseas Quota, Availability NOC Status"]
    
    subgraph Valuation_Model["Auction Valuation & Bidding Model"]
        V1["Calculate Base VORP Score vs Replacement Level"]
        V2["Apply Home Venue Fit Multiplier (Sawai Mansingh Stadium)"]
        V3["Apply Recency Exponential Weighting (Last 3 Seasons)"]
        V4["Apply Availability & Injury Risk Penalty Factor"]
        V1 --> CalcPrice["Calculate Estimated Fair Value & Bidding Ceiling"]
        V2 --> CalcPrice
        V3 --> CalcPrice
        V4 --> CalcPrice
    end
    
    FilterCandidates --> Valuation_Model
    
    CalcPrice --> RankCandidates["Rank Candidates by Net Value / Target Price"]
    
    subgraph Simulation_Engine["Live Auction War Room Simulator"]
        Sim_Draft["Simulate Dynamic Auction Draft"]
        Sim_Purse["Enforce Purse Constraints (Remaining Purse >= Min Base Prices)"]
        Sim_Squad["Enforce Squad Limits (Min 18, Max 25 players, Max 8 Overseas)"]
        Sim_Risk["Flag Single-Point-of-Failure Tactical Gaps"]
    end
    
    RankCandidates --> Sim_Draft
    Sim_Draft --> Sim_Purse
    Sim_Purse --> Sim_Squad
    Sim_Squad --> Sim_Risk
    Sim_Risk --> FinalShortlist(["Approved Auction Target Strategy Sheet"])
```

---

### 2.10 Diagram 10: Dashboard Interaction & UI Component Architecture

```mermaid
flowchart TD
    subgraph User_Interface["Next.js 15 Client Interface (React 19)"]
        Scout_User(("Scout / Analyst"))
        View_Filter["Filter Selectors: Season, Venue, Phase, Opposition"]
        View_Spray["Wagon Wheel & Pitch Spray Chart (Apache ECharts)"]
        View_Radar["Phase Profile Radar Chart (Recharts)"]
        View_Depth["Squad Depth Chart DAG (React Flow)"]
        View_Auction["Live Auction Bidding Matrix"]
    end

    subgraph State_Management["Client State & Data Fetching"]
        Query_Client["React Query / SWR Data Fetching"]
        Zustand_Store["Zustand Client State (Active Filters & Shortlist)"]
    end

    subgraph Backend_Services["FastAPI High-Performance Backend"]
        FastAPI_Router["Async FastAPI Endpoints"]
        Redis_Service["Redis Cache (Sub-millisecond Retrieval)"]
        DB_Pool["PostgreSQL Asyncpg Connection Pool"]
    end

    Scout_User --> View_Filter
    View_Filter --> Zustand_Store
    Zustand_Store --> Query_Client

    Query_Client --> FastAPI_Router
    FastAPI_Router <--> Redis_Service
    FastAPI_Router <--> DB_Pool

    FastAPI_Router -- "JSON Stream" --> Query_Client
    Query_Client --> View_Spray
    Query_Client --> View_Radar
    Query_Client --> View_Depth
    Query_Client --> View_Auction
```

---

## 3. Architectural Decision Records (ADRs)

### ADR-001: Adoption of PostgreSQL 16 3NF with Declarative Season Partitioning
- **Status**: APPROVED ARCHITECTURAL TARGET `[STATUS: PLANNED - GREENFIELD BASELINE]`
- **Context**: The engine must store and analyze over 250,000 granular delivery rows from 2008 to 2026. A non-relational document store (e.g., MongoDB) introduces significant risks of inconsistent player names, invalid run counts, and difficult multi-table analytical joins.
- **Decision**: Adopt PostgreSQL 16 with a strict Third Normal Form (3NF) relational core spanning 20 entities. The high-volume `deliveries` table utilizes declarative list partitioning on `season_year`.
- **Consequences**: Guarantees referential integrity, eliminates orphaned records, and enables partition pruning so queries targeting a specific season scan only that partition's tablespace.

---

### ADR-002: Four-Tier Waterfall Architecture for Multi-Source Player Identity Resolution
- **Status**: APPROVED ARCHITECTURAL TARGET `[STATUS: PLANNED - GREENFIELD BASELINE]`
- **Context**: Player naming inconsistencies across Cricsheet (short tokens like `RV Uthappa`), Kaggle (full strings like `Robin Uthappa`), and external feeds create severe duplicate player entity risks.
- **Decision**: Implement a strict 4-tier waterfall resolution engine:
  1. *Tier 1*: Exact match on Cricsheet 8-character hex hash (`registry.people`) or official BCCI/ESPN ID (Confidence: 1.000).
  2. *Tier 2*: Exact match in verified `player_aliases` (Confidence: 1.000).
  3. *Tier 3*: Deterministic match on Surname + Initials + Team Roster + Match Date (Confidence: 0.980).
  4. *Tier 4*: Probabilistic fuzzy match using Jaro-Winkler ($\ge 0.92$) and Levenshtein ($\le 2$) cross-validated with player role, batting/bowling hand, and active career era.
- **Consequences**: Records falling below the 0.950 confidence threshold are quarantined with `needs_review = TRUE` in `player_aliases` for human curator audit, preventing erroneous player merges.

---

### ADR-003: Immutable Staging & Cryptographic Checksums in ELT Pipeline
- **Status**: APPROVED ARCHITECTURAL TARGET `[STATUS: PLANNED - GREENFIELD BASELINE]`
- **Context**: Upstream data formats from Cricsheet and Kaggle occasionally change or contain corrupt entries. Ingesting directly into relational tables without staging risks partial or unrecoverable data loading.
- **Decision**: Adopt an Extract-Load-Transform (ELT) pattern. Raw payloads are stored unmutated in `source_records` accompanied by a SHA-256 cryptographic digest. A unique constraint on `(source_id, external_entity_id, payload_sha256)` enforces idempotent processing.
- **Consequences**: Any source file can be re-parsed without re-downloading; pipeline regressions can be debugged against the raw payload stored in PostgreSQL JSONB.

---

### ADR-004: Segregation of Super Over and Rain-Shortened Deliveries from Career Statistics
- **Status**: APPROVED ARCHITECTURAL TARGET `[STATUS: PLANNED - GREENFIELD BASELINE]`
- **Context**: Super Overs distort career batting/bowling figures because they represent extreme tie-break states rather than standard innings. Similarly, rain-shortened matches under DLS reset run rates artificially.
- **Decision**: Super Over deliveries are recorded in `innings` with `is_super_over = TRUE` (assigned innings 3 & 4) and partitioned in `deliveries`. Standard queries mandate `WHERE is_super_over = FALSE`. DLS matches are flagged with `is_dls_applied = TRUE`, and scoring rates are normalized using phase-specific DLS resource consumption tables.
- **Consequences**: Adheres strictly to official ICC and BCCI statistical governance while preserving Super Over data for clutch evaluation.

---

### ADR-005: Hybrid Visualization Architecture (Apache ECharts + Recharts + React Flow)
- **Status**: APPROVED ARCHITECTURAL TARGET `[STATUS: PLANNED - GREENFIELD BASELINE]`
- **Context**: The scouting dashboard requires diverse visualizations: spatial pitch spray heatmaps with thousands of coordinates, multi-metric radar charts, and interactive squad depth DAG networks. No single chart library excels at all three paradigms.
- **Decision**: Implement a hybrid visualization architecture:
  1. *Apache ECharts 5.5+* (WebGL/Canvas) for 360-degree wagon wheels, pitch trajectory heatmaps, and spray maps.
  2. *Recharts 2.12+* (Declarative SVG) for phase radar charts, worm run-rate charts, and bar charts.
  3. *React Flow* for interactive squad depth hierarchy DAGs and tactical bowling rotation networks.
- **Consequences**: Maximum rendering performance (60 FPS on spatial scatter maps) while preserving declarative React state integration for dashboards.

---

### ADR-006: Asynchronous Multi-Tier Caching with Redis 7 and PostgreSQL Asyncpg Pool
- **Status**: APPROVED ARCHITECTURAL TARGET `[STATUS: PLANNED - GREENFIELD BASELINE]`
- **Context**: During live auction simulations, scouts execute concurrent queries across player profiles, matchup matrices, and purse models. Direct database hits for complex aggregations would cause connection pool starvation.
- **Decision**: Deploy Redis 7 in-memory caching fronting an `asyncpg` connection pool (min 20, max 50 connections). Precomputed player dossiers and phase metrics are cached with a 3600-second TTL. Cache keys include the feature store model version (`cache:player_profile:{id}:{version}`).
- **Consequences**: Read queries achieve sub-10ms response latencies; database CPU utilization remains low during intense war-room sessions.

---

## 4. Verification & Architecture Integrity

1. **Syntax Validation**: All 10 Mermaid diagrams have been validated against Mermaid parser specifications. Node identifiers avoid reserved keywords, edge statements use explicit syntax, and ER relationships map all 20 tables.
2. **Relational Completeness**: The entity relationship diagram in Section 2.7 mirrors the complete PostgreSQL DDL specified in `docs/TRD.md`, confirming primary keys, foreign keys, and cardinalities across all 20 entities.
3. **Cross-Document Consistency**: Terminology, entity names, API paths, and architectural layers match across `PRD.md`, `TRD.md`, `PHASES.md`, `AGENTS.md`, and `AI_INSTRUCTIONS.md`.
