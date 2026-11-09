# Technical Requirements Document (TRD) & Central Database Schema
**Rajasthan Royals Squad Intelligence & Historical Performance Engine**  
**Tournament**: Indian Premier League (IPL) 2027 Auction Preparation & Tactical Engine  
**Document Version**: 1.0.0 (Engineering Baseline)  
**Status**: [STATUS: PLANNED - GREENFIELD BASELINE]  
**Author**: Engineering Architecture Team (`teamwork_worker_2`)  

---

## 1. System Overview & Technical Architecture

> **Architecture Baseline Status**: `[STATUS: PLANNED - GREENFIELD BASELINE]`  
> All schemas, database tables, partition schemes, mathematical models, and API endpoints defined in this document represent the approved architectural specification for greenfield implementation. Zero application code currently exists.

The Rajasthan Royals Squad Intelligence & Historical Performance Engine is an enterprise-grade sports analytics platform designed to power data-driven recruitment, tactical valuation, opponent scouting, and live war-room simulation for the IPL 2027 Mega Auction `[STATUS: PLANNED - GREENFIELD BASELINE]`.

The platform processes multi-format historical match feeds, ball-tracking telemetry, macro-environmental telemetry, and physical injury records to generate contextualized player valuations, matchup matrices, and squad optimization models.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       Next.js 15 Presentation Tier                          │
│     (App Router, Tailwind CSS 3.4, ECharts 5.5, Recharts 2.12, React Flow)  │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ Async REST / SSE / WebSocket
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       FastAPI Application Gateway                           │
│        (Python 3.11+, ASGI Uvicorn, Pydantic v2, RFC 7807 Errors)           │
└──────────────┬───────────────────────────────────────────────┬──────────────┘
               │                                               │
               ▼                                               ▼
┌──────────────────────────────┐              ┌──────────────────────────────┐
│     Redis 7 Cache Tier       │              │ Vectorized Analytics Engine  │
│ (Sub-10ms Feature Retrieval) │              │  (NumPy, Pandas, SciPy, WPA) │
└──────────────┬───────────────┘              └──────────────┬───────────────┘
               │                                             │
               └───────────────────────┬─────────────────────┘
                                       │ Asyncpg Connection Pool
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                 Central PostgreSQL 16 Normalized Core                       │
│    (3NF Relational Model, Declarative Range Partitioning, GBN/JSONB Indexes)│
└──────────────────────────────────────▲──────────────────────────────────────┘
                                       │ Batch ELT Transactions
┌──────────────────────────────────────┴──────────────────────────────────────┐
│                    Data Ingestion & Normalization Engine                    │
│   (SHA-256 Deduplication, Pydantic Gate, 4-Tier Identity Resolver, Context) │
└──────────────────────────────────────▲──────────────────────────────────────┘
                                       │
      ┌────────────────┬───────────────┴───────────────┬────────────────┐
      │                │                               │                │
┌─────┴──────────┐ ┌───┴──────────┐            ┌───────┴────────┐ ┌─────┴──────┐
│ Cricsheet JSON │ │  Kaggle CSV  │            │ Open-Meteo API │ │ HawkEye /  │
│ (v1.3.0 / YAML)│ │ (2008–2026)  │            │ (Historical Wx)│ │ Tracking   │
└────────────────┘ └──────────────┘            └────────────────┘ └────────────┘
```

### 1.1 Architectural Subsystems

1. **Client Presentation Tier (Next.js 15)**:
   - Built with Next.js 15 (React 19) utilising the App Router architecture.
   - Server-Side Rendering (SSR) delivers sub-second initial paint times for player dossiers and squad depth charts.
   - Client components leverage Apache ECharts (WebGL/Canvas) for 360-degree wagon wheels, pitch trajectory heatmaps, and pitch spray charts.
   - Recharts handles multi-dimensional phase radar charts (Powerplay, Middle 1, Middle 2, Death) and worm match charts.
   - React Flow orchestrates interactive directed acyclic graphs (DAGs) representing squad depth hierarchies, bowling rotation clusters, and substitution contingencies.

2. **API & Orchestration Layer (FastAPI)**:
   - Asynchronous Python 3.11+ application running on Uvicorn ASGI workers.
   - Strict Pydantic v2 domain schemas enforce bidirectional request/response contracts, automated OpenAPI 3.1 schema generation, and compile-time validation.
   - RFC 7807 Problem Details specification governs all error responses, eliminating ambiguous HTTP payloads.
   - Implements Redis 7 in-memory cache fronting high-frequency endpoints, maintaining sub-10ms response latencies for precomputed player profiles and venue indices.

3. **Analytics & Tactical Computation Engine (Python / NumPy / Pandas)**:
   - High-throughput vectorized calculation modules executing on NumPy 1.26+ and Pandas 2.2+.
   - Computes advanced cricket sabermetrics: True Strike Rate (TSR), True Economy Rate (TER), Win Probability Added (WPA), Value Over Replacement Player (VORP), and Clutch Leverage Indices.
   - Segregates experimental predictive models from the pristine historical scorecard ledger.

4. **Central Normalized Relational Core (PostgreSQL 16)**:
   - Strict Third Normal Form (3NF) relational architecture spanning 20 discrete entities.
   - Declarative range/list partitioning on the high-volume `deliveries` table (over 250,000 deliveries across IPL history) based on tournament seasons.
   - Hard domain check constraints (`CHECK`), foreign key cascaded integrity, and transactional isolation (`READ COMMITTED`) guarantee zero data corruption.

5. **Data Ingestion & ELT Pipeline**:
   - Extract-Load-Transform (ELT) architecture with raw payload immutability.
   - Ingests raw source streams into `source_records` accompanied by cryptographic SHA-256 digests for idempotent deduplication.
   - Pydantic validation gate routes malformed payloads to a Dead-Letter Quarantine table while passing pristine payloads to relational decomposition.

6. **Contextual Enrichment Subsystem**:
   - Augments granular ball-by-ball deliveries with stadium boundary geometry, venue elevation, pitch soil degradation matrices, and historical Open-Meteo macro-weather observations (temperature, relative humidity, dew point, atmospheric pressure, and wind vectors).

7. **Derived Feature Store**:
   - Persists versioned statistical vectors and analytical embeddings in `derived_features`.
   - Supports calculation windows (Career, 3-Year Rolling, Last Season, Home Venue Only) to facilitate instantaneous war-room retrieval.

---

## 2. Central Normalised PostgreSQL Database Schema (PostgreSQL 16)

The data model enforces relational integrity across 20 entities, incorporating declarative table partitioning, composite primary keys, domain check constraints, and performance-tuned btree/gist indexing.

```
                                  DATABASE ENTITY DOMAINS
   ┌─────────────────────────────────────────────────────────────────────────────────┐
   │ 1. INGESTION & AUDIT     : data_sources, source_records                         │
   │ 2. CORE IDENTITY         : players, player_aliases                              │
   │ 3. COMPETITIONS & TEAMS  : venues, teams, competitions, seasons, squad_membs    │
   │ 4. MATCHES & CONDITIONS  : matches, pitch_conditions, weather_conditions        │
   │ 5. GRANULAR CRICKET CORE : innings, deliveries (Partitioned)                    │
   │ 6. SCORECARDS & FIELDING : batting_innings, bowling_spell, fielding_events     │
   │ 7. AVAILABILITY & INJURY : player_availability, player_injuries                 │
   │ 8. FEATURE STORE         : derived_features                                     │
   └─────────────────────────────────────────────────────────────────────────────────┘
```

### 2.1 Complete PostgreSQL 16 DDL

```sql
-- ============================================================================
-- RAJASTHAN ROYALS SQUAD INTELLIGENCE ENGINE: CENTRAL DATABASE DDL
-- Target Engine: PostgreSQL 16+
-- Extensions: uuid-ossp (UUID generation), btree_gist (Advanced Indexing)
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "btree_gist";

-- ============================================================================
-- ENTITY 1: DATA SOURCES (data_sources)
-- Purpose: Registry of upstream data providers, license types, and update cadence.
-- ============================================================================
CREATE TABLE data_sources (
    source_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_name VARCHAR(100) NOT NULL UNIQUE,
    source_type VARCHAR(50) NOT NULL CHECK (source_type IN (
        'JSON Feed', 'CSV Archive', 'REST API', 'Web Scraping / Official Feed', 'Manual Ingestion'
    )),
    base_url VARCHAR(255),
    license_type VARCHAR(50) NOT NULL, -- e.g., 'ODC-By v1.0', 'CC BY-SA 4.0', 'Proprietary'
    update_cadence VARCHAR(30) NOT NULL CHECK (update_cadence IN (
        'Real-time', 'Hourly', 'Daily', 'Post-Match Batch', 'Static Archive'
    )),
    data_steward VARCHAR(100) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE data_sources IS 'Audit registry of all external and internal data providers and feeds.';
COMMENT ON COLUMN data_sources.license_type IS 'Legal licensing framework governing data storage, transformation, and distribution.';

-- ============================================================================
-- ENTITY 2: SOURCE RECORDS (source_records)
-- Purpose: Immutable staging repository for raw, unmutated JSON/CSV payloads.
-- ============================================================================
CREATE TABLE source_records (
    record_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id UUID NOT NULL REFERENCES data_sources(source_id) ON DELETE RESTRICT,
    external_entity_id VARCHAR(100) NOT NULL, -- e.g., Cricsheet match ID '1082591'
    raw_payload JSONB NOT NULL,
    payload_sha256 CHAR(64) NOT NULL,
    ingestion_timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    processing_status VARCHAR(30) NOT NULL DEFAULT 'Pending' CHECK (processing_status IN (
        'Pending', 'Parsed', 'Normalized', 'Failed', 'Quarantined'
    )),
    error_message TEXT,
    parsed_entity_type VARCHAR(50), -- e.g., 'Match', 'PlayerRegistry', 'WeatherObservation'
    core_record_id UUID, -- Foreign pointer to normalized table record once processed
    CONSTRAINT uq_source_payload_hash UNIQUE (source_id, external_entity_id, payload_sha256)
);

CREATE INDEX idx_source_records_status ON source_records(processing_status);
CREATE INDEX idx_source_records_external_id ON source_records(source_id, external_entity_id);
CREATE INDEX idx_source_records_sha256 ON source_records(payload_sha256);

COMMENT ON TABLE source_records IS 'Raw ELT staging table preserving cryptographic provenance of all ingested payloads.';

-- ============================================================================
-- ENTITY 3: PLAYERS (players)
-- Purpose: Canonical master registry of cricket players with normalized traits.
-- ============================================================================
CREATE TABLE players (
    player_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    canonical_name VARCHAR(100) NOT NULL,
    full_name VARCHAR(150),
    date_of_birth DATE,
    nationality VARCHAR(50) NOT NULL,
    primary_role VARCHAR(30) NOT NULL CHECK (primary_role IN (
        'Top-order Batter', 'Middle-order Batter', 'Wicketkeeper Batter',
        'Batting All-rounder', 'Bowling All-rounder', 'Pace Bowler', 'Spin Bowler'
    )),
    batting_hand VARCHAR(10) CHECK (batting_hand IN ('Right', 'Left')),
    bowling_arm VARCHAR(10) CHECK (bowling_arm IN ('Right', 'Left')),
    bowling_style VARCHAR(50), -- Physical biographical style, e.g., 'Right-arm legbreak', 'Left-arm fast'
    cricsheet_id VARCHAR(50) UNIQUE, -- Alphanumeric hash from Cricsheet registry.people
    bcci_id VARCHAR(50) UNIQUE,
    espn_id VARCHAR(50) UNIQUE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_players_canonical_name ON players(canonical_name);
CREATE INDEX idx_players_primary_role ON players(primary_role);
CREATE INDEX idx_players_cricsheet_id ON players(cricsheet_id) WHERE cricsheet_id IS NOT NULL;
CREATE INDEX idx_players_nationality ON players(nationality);

COMMENT ON TABLE players IS 'Master player directory storing canonical identifiers and immutable physical traits.';
COMMENT ON COLUMN players.bowling_style IS 'Biographical physical action. Must NEVER be overwritten with delivery variations like googly or carrom ball.';

-- ============================================================================
-- ENTITY 4: PLAYER ALIASES (player_aliases)
-- Purpose: Multi-source name mapping and disambiguation linkage table.
-- ============================================================================
CREATE TABLE player_aliases (
    alias_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    player_id UUID NOT NULL REFERENCES players(player_id) ON DELETE CASCADE,
    alias_name VARCHAR(100) NOT NULL,
    source_id UUID NOT NULL REFERENCES data_sources(source_id) ON DELETE RESTRICT,
    confidence_score NUMERIC(4,3) NOT NULL CHECK (confidence_score >= 0.000 AND confidence_score <= 1.000),
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    needs_review BOOLEAN NOT NULL DEFAULT FALSE,
    verified_by VARCHAR(50),
    verified_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_alias_source UNIQUE (alias_name, source_id)
);

CREATE INDEX idx_player_aliases_name ON player_aliases(alias_name);
CREATE INDEX idx_player_aliases_lookup ON player_aliases(alias_name, source_id);
CREATE INDEX idx_player_aliases_review ON player_aliases(needs_review) WHERE needs_review IS TRUE;

COMMENT ON TABLE player_aliases IS 'Disambiguation repository mapping source-specific strings to canonical player_id.';

-- ============================================================================
-- ENTITY 5: VENUES (venues)
-- Purpose: Stadium metadata, geographical coordinates, and spatial dimensions.
-- ============================================================================
CREATE TABLE venues (
    venue_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    stadium_name VARCHAR(150) NOT NULL,
    city VARCHAR(100) NOT NULL,
    country VARCHAR(50) NOT NULL,
    cricsheet_venue_id VARCHAR(50) UNIQUE,
    latitude NUMERIC(9,6),
    longitude NUMERIC(9,6),
    elevation_meters NUMERIC(6,2),
    boundary_radius_meters NUMERIC(5,2),
    boundary_size_offside NUMERIC(5,2),
    boundary_size_legside NUMERIC(5,2),
    boundary_size_straight NUMERIC(5,2),
    pitch_type_default VARCHAR(50), -- e.g., 'Red Soil - Bouncy', 'Black Soil - Gripping'
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_venue_name_city UNIQUE (stadium_name, city)
);

CREATE INDEX idx_venues_city ON venues(city);

COMMENT ON TABLE venues IS 'Geospatial and structural registry of cricket stadiums including boundary dimensions.';

-- ============================================================================
-- ENTITY 6: TEAMS (teams)
-- Purpose: Franchise and international team registry with visual identity.
-- ============================================================================
CREATE TABLE teams (
    team_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    team_name VARCHAR(100) NOT NULL UNIQUE,
    short_code VARCHAR(10) NOT NULL UNIQUE, -- e.g., 'RR', 'CSK', 'MI', 'RCB'
    primary_color VARCHAR(7), -- Hex color code, e.g., '#EA1B8C' (RR Pink)
    secondary_color VARCHAR(7), -- Hex color code, e.g., '#004B8C' (Royal Blue)
    home_venue_id UUID REFERENCES venues(venue_id) ON DELETE SET NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE teams IS 'Franchise and team registry linking to home venues and team brand identities.';

-- ============================================================================
-- ENTITY 7: COMPETITIONS (competitions)
-- Purpose: Tournament definitions across franchise, domestic, and internationals.
-- ============================================================================
CREATE TABLE competitions (
    competition_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    competition_type VARCHAR(30) NOT NULL CHECK (competition_type IN (
        'Domestic Franchise T20', 'Domestic T20', 'International T20', 'Domestic List A', 'ODI', 'Other'
    )),
    governing_body VARCHAR(50) NOT NULL, -- e.g., 'BCCI', 'ICC', 'ECB', 'CA'
    country VARCHAR(50) NOT NULL,
    match_overs INT NOT NULL DEFAULT 20 CHECK (match_overs > 0),
    balls_per_over INT NOT NULL DEFAULT 6 CHECK (balls_per_over > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- ENTITY 8: SEASONS (seasons)
-- Purpose: Specific tournament editions/years linked to competitions.
-- ============================================================================
CREATE TABLE seasons (
    season_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    competition_id UUID NOT NULL REFERENCES competitions(competition_id) ON DELETE CASCADE,
    season_year VARCHAR(20) NOT NULL, -- e.g., '2024', '2023/24'
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_season_comp UNIQUE (competition_id, season_year),
    CONSTRAINT chk_season_dates CHECK (end_date >= start_date)
);

CREATE INDEX idx_seasons_competition ON seasons(competition_id);

-- ============================================================================
-- ENTITY 9: SQUAD MEMBERSHIPS (squad_memberships)
-- Purpose: Seasonal player contracts, retention status, auction price, salary.
-- ============================================================================
CREATE TABLE squad_memberships (
    membership_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    player_id UUID NOT NULL REFERENCES players(player_id) ON DELETE RESTRICT,
    team_id UUID NOT NULL REFERENCES teams(team_id) ON DELETE RESTRICT,
    season_id UUID NOT NULL REFERENCES seasons(season_id) ON DELETE RESTRICT,
    contract_type VARCHAR(30) NOT NULL CHECK (contract_type IN (
        'Retained', 'Auction Buy', 'Replacement', 'Trade', 'Draft'
    )),
    salary_inr NUMERIC(14,2) CHECK (salary_inr >= 0),
    jersey_number INT CHECK (jersey_number >= 0 AND jersey_number <= 999),
    is_captain BOOLEAN NOT NULL DEFAULT FALSE,
    is_overseas BOOLEAN NOT NULL DEFAULT FALSE,
    is_active_squad BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_player_team_season UNIQUE (player_id, team_id, season_id)
);

CREATE INDEX idx_squad_team_season ON squad_memberships(team_id, season_id);
CREATE INDEX idx_squad_player ON squad_memberships(player_id);

-- ============================================================================
-- ENTITY 10: MATCHES (matches)
-- Purpose: Fixtures, toss decisions, results, margins, and match status.
-- ============================================================================
CREATE TABLE matches (
    match_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    external_cricsheet_id VARCHAR(50) UNIQUE,
    season_id UUID NOT NULL REFERENCES seasons(season_id) ON DELETE RESTRICT,
    venue_id UUID NOT NULL REFERENCES venues(venue_id) ON DELETE RESTRICT,
    match_number INT,
    match_type VARCHAR(30) NOT NULL DEFAULT 'T20',
    match_date DATE NOT NULL,
    home_team_id UUID NOT NULL REFERENCES teams(team_id) ON DELETE RESTRICT,
    away_team_id UUID NOT NULL REFERENCES teams(team_id) ON DELETE RESTRICT,
    toss_winner_id UUID REFERENCES teams(team_id) ON DELETE RESTRICT,
    toss_decision VARCHAR(10) CHECK (toss_decision IN ('bat', 'field')),
    winner_id UUID REFERENCES teams(team_id) ON DELETE RESTRICT,
    outcome_type VARCHAR(30) NOT NULL CHECK (outcome_type IN (
        'runs', 'wickets', 'tie', 'super_over', 'no_result', 'abandoned'
    )),
    win_margin_runs INT CHECK (win_margin_runs >= 0),
    win_margin_wickets INT CHECK (win_margin_wickets >= 0),
    is_dls_applied BOOLEAN NOT NULL DEFAULT FALSE,
    dls_method_version VARCHAR(20),
    player_of_match_id UUID REFERENCES players(player_id) ON DELETE SET NULL,
    overs_scheduled INT NOT NULL DEFAULT 20 CHECK (overs_scheduled > 0),
    status VARCHAR(20) NOT NULL CHECK (status IN ('Scheduled', 'Completed', 'Abandoned', 'No Result')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_match_teams CHECK (home_team_id <> away_team_id)
);

CREATE INDEX idx_matches_date ON matches(match_date);
CREATE INDEX idx_matches_season ON matches(season_id);
CREATE INDEX idx_matches_venue ON matches(venue_id);
CREATE INDEX idx_matches_teams ON matches(home_team_id, away_team_id);

-- ============================================================================
-- ENTITY 11: PITCH CONDITIONS (pitch_conditions)
-- Purpose: Curator ground ratings, soil type, and par scoring expectations.
-- ============================================================================
CREATE TABLE pitch_conditions (
    pitch_condition_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    match_id UUID NOT NULL REFERENCES matches(match_id) ON DELETE CASCADE,
    venue_id UUID NOT NULL REFERENCES venues(venue_id) ON DELETE RESTRICT,
    soil_type VARCHAR(50) CHECK (soil_type IN ('Red Soil', 'Black Soil', 'Composite / Clay Mix', 'Unknown')),
    pitch_pace_rating NUMERIC(3,1) CHECK (pitch_pace_rating BETWEEN 1.0 AND 10.0),
    pitch_bounce_rating NUMERIC(3,1) CHECK (pitch_bounce_rating BETWEEN 1.0 AND 10.0),
    pitch_turn_rating NUMERIC(3,1) CHECK (pitch_turn_rating BETWEEN 1.0 AND 10.0),
    grass_coverage VARCHAR(30) CHECK (grass_coverage IN (
        'None / Dry', 'Light Sheen', 'Moderate Green', 'Heavy Green Top'
    )),
    expected_par_score_1st_innings INT CHECK (expected_par_score_1st_innings > 0),
    actual_1st_innings_score INT CHECK (actual_1st_innings_score >= 0),
    source_curator_notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_match_pitch UNIQUE (match_id)
);

-- ============================================================================
-- ENTITY 12: WEATHER CONDITIONS (weather_conditions)
-- Purpose: Open-Meteo macro-environmental observation records per match.
-- ============================================================================
CREATE TABLE weather_conditions (
    weather_condition_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    match_id UUID NOT NULL REFERENCES matches(match_id) ON DELETE CASCADE,
    observation_timestamp TIMESTAMPTZ NOT NULL,
    temperature_celsius NUMERIC(4,1),
    relative_humidity_pct NUMERIC(4,1) CHECK (relative_humidity_pct BETWEEN 0.0 AND 100.0),
    dew_point_celsius NUMERIC(4,1),
    dew_impact_index VARCHAR(20) CHECK (dew_impact_index IN (
        'None', 'Low', 'Moderate', 'Heavy / Ball Slippery'
    )),
    wind_speed_kmh NUMERIC(5,2) CHECK (wind_speed_kmh >= 0),
    wind_direction_degrees INT CHECK (wind_direction_degrees BETWEEN 0 AND 360),
    precipitation_mm NUMERIC(5,2) CHECK (precipitation_mm >= 0),
    atmospheric_pressure_hpa NUMERIC(6,1),
    cloud_cover_pct NUMERIC(4,1) CHECK (cloud_cover_pct BETWEEN 0.0 AND 100.0),
    data_provenance_flag VARCHAR(100) NOT NULL DEFAULT 'Open-Meteo Macro Environmental Context (Not Direct Pitch Moisture)',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_match_weather_obs UNIQUE (match_id, observation_timestamp)
);

CREATE INDEX idx_weather_match ON weather_conditions(match_id);

-- ============================================================================
-- ENTITY 13: INNINGS (innings)
-- Purpose: Innings level metadata, totals, DLS targets, and Super Over flags.
-- ============================================================================
CREATE TABLE innings (
    innings_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    match_id UUID NOT NULL REFERENCES matches(match_id) ON DELETE CASCADE,
    innings_number INT NOT NULL CHECK (innings_number IN (1, 2, 3, 4)),
    batting_team_id UUID NOT NULL REFERENCES teams(team_id) ON DELETE RESTRICT,
    bowling_team_id UUID NOT NULL REFERENCES teams(team_id) ON DELETE RESTRICT,
    is_super_over BOOLEAN NOT NULL DEFAULT FALSE,
    overs_allocated NUMERIC(4,1) NOT NULL DEFAULT 20.0 CHECK (overs_allocated > 0),
    target_runs INT CHECK (target_runs >= 0),
    target_overs NUMERIC(4,1) CHECK (target_overs > 0),
    total_runs INT NOT NULL DEFAULT 0 CHECK (total_runs >= 0),
    total_wickets INT NOT NULL DEFAULT 0 CHECK (total_wickets BETWEEN 0 AND 10),
    total_legal_deliveries INT NOT NULL DEFAULT 0 CHECK (total_legal_deliveries >= 0),
    total_extras INT NOT NULL DEFAULT 0 CHECK (total_extras >= 0),
    is_declared BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_match_innings UNIQUE (match_id, innings_number, is_super_over),
    CONSTRAINT chk_innings_teams CHECK (batting_team_id <> bowling_team_id)
);

CREATE INDEX idx_innings_match ON innings(match_id);
CREATE INDEX idx_innings_super_over ON innings(is_super_over) WHERE is_super_over IS TRUE;

-- ============================================================================
-- ENTITY 14: DELIVERIES (deliveries) -- DECLARATIVE PARTITIONED TABLE
-- Purpose: Granular ball-by-ball event ledger partitioned by match season.
-- ============================================================================
CREATE TABLE deliveries (
    delivery_id UUID NOT NULL DEFAULT uuid_generate_v4(),
    innings_id UUID NOT NULL,
    match_id UUID NOT NULL,
    season_year VARCHAR(20) NOT NULL, -- Partitioning key
    over_number INT NOT NULL CHECK (over_number >= 0 AND over_number < 50),
    ball_in_over INT NOT NULL CHECK (ball_in_over >= 1),
    delivery_sequence INT NOT NULL CHECK (delivery_sequence >= 1),
    batter_id UUID NOT NULL,
    bowler_id UUID NOT NULL,
    non_striker_id UUID NOT NULL,
    runs_batter INT NOT NULL CHECK (runs_batter BETWEEN 0 AND 6),
    runs_extras INT NOT NULL DEFAULT 0 CHECK (runs_extras >= 0),
    runs_total INT NOT NULL CHECK (runs_total >= 0),
    is_wide BOOLEAN NOT NULL DEFAULT FALSE,
    is_noball BOOLEAN NOT NULL DEFAULT FALSE,
    is_bye BOOLEAN NOT NULL DEFAULT FALSE,
    is_legbye BOOLEAN NOT NULL DEFAULT FALSE,
    is_penalty BOOLEAN NOT NULL DEFAULT FALSE,
    runs_wides INT NOT NULL DEFAULT 0 CHECK (runs_wides >= 0),
    runs_noballs INT NOT NULL DEFAULT 0 CHECK (runs_noballs >= 0),
    runs_byes INT NOT NULL DEFAULT 0 CHECK (runs_byes >= 0),
    runs_legbyes INT NOT NULL DEFAULT 0 CHECK (runs_legbyes >= 0),
    runs_penalties INT NOT NULL DEFAULT 0 CHECK (runs_penalties >= 0),
    is_wicket BOOLEAN NOT NULL DEFAULT FALSE,
    wicket_kind VARCHAR(30) CHECK (wicket_kind IN (
        'bowled', 'caught', 'caught and bowled', 'lbw', 'stumped', 'run out',
        'retired hurt', 'retired out', 'hit wicket', 'obstructing the field',
        'hit the ball twice', 'timed out'
    )),
    player_out_id UUID,
    is_bowler_credited_wicket BOOLEAN NOT NULL DEFAULT FALSE,
    match_phase VARCHAR(20) NOT NULL CHECK (match_phase IN ('Powerplay', 'Middle 1', 'Middle 2', 'Death')),
    variation_type VARCHAR(50), -- e.g., 'Googly', 'Slower Bouncer', 'Knuckle Ball', 'Carrom Ball'
    ball_speed_kph NUMERIC(5,2), -- NULL if Hawk-Eye unavailable, NEVER 0.00
    pitch_coordinate_x NUMERIC(6,3), -- Pitch lateral landing coord, NULL if tracking absent
    pitch_coordinate_y NUMERIC(6,3), -- Pitch longitudinal length coord, NULL if tracking absent
    post_shot_landing_x NUMERIC(6,2), -- Ball landing/boundary intercept X coord (NOT fielder position)
    post_shot_landing_y NUMERIC(6,2), -- Ball landing/boundary intercept Y coord (NOT fielder position)
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_deliveries PRIMARY KEY (delivery_id, season_year),
    CONSTRAINT chk_runs_consistency CHECK (runs_total = runs_batter + runs_extras)
) PARTITION BY LIST (season_year);

-- Declarative Season Partitions (Sample Partitioning Strategy)
CREATE TABLE deliveries_y2008_2015 PARTITION OF deliveries
    FOR VALUES IN ('2008', '2009', '2010', '2011', '2012', '2013', '2014', '2015');

CREATE TABLE deliveries_y2016_2020 PARTITION OF deliveries
    FOR VALUES IN ('2016', '2017', '2018', '2019', '2020');

CREATE TABLE deliveries_y2021_2023 PARTITION OF deliveries
    FOR VALUES IN ('2021', '2022', '2023');

CREATE TABLE deliveries_y2024_2026 PARTITION OF deliveries
    FOR VALUES IN ('2024', '2025', '2026');

CREATE TABLE deliveries_default PARTITION OF deliveries DEFAULT;

-- Indexes on Partitioned Table
CREATE INDEX idx_deliveries_match_innings ON deliveries(match_id, innings_id);
CREATE INDEX idx_deliveries_batter ON deliveries(batter_id);
CREATE INDEX idx_deliveries_bowler ON deliveries(bowler_id);
CREATE INDEX idx_deliveries_phase ON deliveries(match_phase);
CREATE INDEX idx_deliveries_matchup ON deliveries(batter_id, bowler_id);

COMMENT ON TABLE deliveries IS 'Ball-by-ball event ledger with declarative season partitioning and tracking telemetry.';

-- ============================================================================
-- ENTITY 15: BATTING INNINGS (batting_innings)
-- Purpose: Materialized official batter scorecards per match innings.
-- ============================================================================
CREATE TABLE batting_innings (
    batting_innings_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    innings_id UUID NOT NULL REFERENCES innings(innings_id) ON DELETE CASCADE,
    player_id UUID NOT NULL REFERENCES players(player_id) ON DELETE RESTRICT,
    team_id UUID NOT NULL REFERENCES teams(team_id) ON DELETE RESTRICT,
    batting_position INT NOT NULL CHECK (batting_position BETWEEN 1 AND 11),
    runs_scored INT NOT NULL DEFAULT 0 CHECK (runs_scored >= 0),
    balls_faced INT NOT NULL DEFAULT 0 CHECK (balls_faced >= 0),
    minutes_at_crease INT CHECK (minutes_at_crease >= 0),
    fours INT NOT NULL DEFAULT 0 CHECK (fours >= 0),
    sixes INT NOT NULL DEFAULT 0 CHECK (sixes >= 0),
    dot_balls_faced INT NOT NULL DEFAULT 0 CHECK (dot_balls_faced >= 0),
    strike_rate NUMERIC(6,2), -- NULL if balls_faced == 0
    dismissal_kind VARCHAR(30),
    dismissal_bowler_id UUID REFERENCES players(player_id) ON DELETE SET NULL,
    dismissal_fielder_id UUID REFERENCES players(player_id) ON DELETE SET NULL,
    is_not_out BOOLEAN NOT NULL DEFAULT TRUE,
    runs_powerplay INT NOT NULL DEFAULT 0 CHECK (runs_powerplay >= 0),
    balls_powerplay INT NOT NULL DEFAULT 0 CHECK (balls_powerplay >= 0),
    runs_middle INT NOT NULL DEFAULT 0 CHECK (runs_middle >= 0),
    balls_middle INT NOT NULL DEFAULT 0 CHECK (balls_middle >= 0),
    runs_death INT NOT NULL DEFAULT 0 CHECK (runs_death >= 0),
    balls_death INT NOT NULL DEFAULT 0 CHECK (balls_death >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_innings_batter UNIQUE (innings_id, player_id),
    CONSTRAINT chk_boundary_runs CHECK ((fours * 4 + sixes * 6) <= runs_scored),
    CONSTRAINT chk_balls_faced CHECK (dot_balls_faced <= balls_faced)
);

CREATE INDEX idx_batting_player ON batting_innings(player_id);

-- ============================================================================
-- ENTITY 16: BOWLING SPELL (bowling_spell)
-- Purpose: Materialized official bowling figures per match innings.
-- ============================================================================
CREATE TABLE bowling_spell (
    spell_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    innings_id UUID NOT NULL REFERENCES innings(innings_id) ON DELETE CASCADE,
    player_id UUID NOT NULL REFERENCES players(player_id) ON DELETE RESTRICT,
    team_id UUID NOT NULL REFERENCES teams(team_id) ON DELETE RESTRICT,
    spell_order INT NOT NULL DEFAULT 1 CHECK (spell_order >= 1),
    legal_balls_bowled INT NOT NULL DEFAULT 0 CHECK (legal_balls_bowled >= 0),
    overs_completed NUMERIC(4,1) NOT NULL DEFAULT 0.0 CHECK (overs_completed >= 0.0),
    maidens INT NOT NULL DEFAULT 0 CHECK (maidens >= 0),
    runs_conceded INT NOT NULL DEFAULT 0 CHECK (runs_conceded >= 0),
    wickets_taken INT NOT NULL DEFAULT 0 CHECK (wickets_taken BETWEEN 0 AND 10),
    wides_bowled INT NOT NULL DEFAULT 0 CHECK (wides_bowled >= 0),
    noballs_bowled INT NOT NULL DEFAULT 0 CHECK (noballs_bowled >= 0),
    dot_balls_bowled INT NOT NULL DEFAULT 0 CHECK (dot_balls_bowled >= 0),
    economy_rate NUMERIC(5,2), -- NULL if legal_balls_bowled == 0
    bowling_average NUMERIC(6,2), -- NULL if wickets_taken == 0
    bowling_strike_rate NUMERIC(5,2), -- NULL if wickets_taken == 0
    runs_conceded_powerplay INT NOT NULL DEFAULT 0 CHECK (runs_conceded_powerplay >= 0),
    balls_bowled_powerplay INT NOT NULL DEFAULT 0 CHECK (balls_bowled_powerplay >= 0),
    wickets_powerplay INT NOT NULL DEFAULT 0 CHECK (wickets_powerplay >= 0),
    runs_conceded_middle INT NOT NULL DEFAULT 0 CHECK (runs_conceded_middle >= 0),
    balls_bowled_middle INT NOT NULL DEFAULT 0 CHECK (balls_bowled_middle >= 0),
    wickets_middle INT NOT NULL DEFAULT 0 CHECK (wickets_middle >= 0),
    runs_conceded_death INT NOT NULL DEFAULT 0 CHECK (runs_conceded_death >= 0),
    balls_bowled_death INT NOT NULL DEFAULT 0 CHECK (balls_bowled_death >= 0),
    wickets_death INT NOT NULL DEFAULT 0 CHECK (wickets_death >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_innings_bowler UNIQUE (innings_id, player_id),
    CONSTRAINT chk_dots_bowled CHECK (dot_balls_bowled <= legal_balls_bowled)
);

CREATE INDEX idx_bowling_player ON bowling_spell(player_id);

-- ============================================================================
-- ENTITY 17: FIELDING EVENTS (fielding_events)
-- Purpose: Granular fielding actions, catches, stumpings, runouts & substitutes.
-- ============================================================================
CREATE TABLE fielding_events (
    fielding_event_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    delivery_id UUID NOT NULL, -- Soft logical link to deliveries
    season_year VARCHAR(20) NOT NULL,
    player_id UUID NOT NULL REFERENCES players(player_id) ON DELETE RESTRICT,
    is_substitute BOOLEAN NOT NULL DEFAULT FALSE,
    event_type VARCHAR(30) NOT NULL CHECK (event_type IN (
        'Catch', 'Run Out Thrower', 'Run Out Catcher', 'Stumping',
        'Dropped Catch', 'Missed Run Out', 'Boundary Save'
    )),
    is_successful BOOLEAN NOT NULL DEFAULT TRUE,
    assisted_by_player_id UUID REFERENCES players(player_id) ON DELETE SET NULL,
    fielding_position VARCHAR(40), -- e.g., 'Deep Mid-Wicket', 'Cover Point', 'Slip 1'
    runs_saved INT DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_fielding_player ON fielding_events(player_id);
CREATE INDEX idx_fielding_delivery ON fielding_events(delivery_id);

COMMENT ON TABLE fielding_events IS 'Fielding actions attributing catches/runouts. Substitute fielders flagged via is_substitute.';

-- ============================================================================
-- ENTITY 18: PLAYER AVAILABILITY (player_availability)
-- Purpose: Tracking international duty, NOC clearances, and window availability.
-- ============================================================================
CREATE TABLE player_availability (
    availability_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    player_id UUID NOT NULL REFERENCES players(player_id) ON DELETE CASCADE,
    season_id UUID NOT NULL REFERENCES seasons(season_id) ON DELETE CASCADE,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    availability_status VARCHAR(30) NOT NULL CHECK (availability_status IN (
        'Full Season', 'Partial Season', 'Unavailable', 'Subject to NOC', 'National Duty Clashing'
    )),
    matches_expected_available INT CHECK (matches_expected_available >= 0),
    reason_for_unavailability TEXT,
    national_board_noc_granted BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_player_season_avail UNIQUE (player_id, season_id, start_date),
    CONSTRAINT chk_avail_dates CHECK (end_date >= start_date)
);

CREATE INDEX idx_avail_player_season ON player_availability(player_id, season_id);

-- ============================================================================
-- ENTITY 19: PLAYER INJURIES (player_injuries)
-- Purpose: Medical trauma records, downtime, surgeries, and recurrence risk.
-- ============================================================================
CREATE TABLE player_injuries (
    injury_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    player_id UUID NOT NULL REFERENCES players(player_id) ON DELETE CASCADE,
    injury_date DATE NOT NULL,
    injury_type VARCHAR(50) NOT NULL, -- e.g., 'Hamstring Strain', 'Stress Fracture'
    body_part VARCHAR(50) NOT NULL, -- e.g., 'Lumbar Spine', 'Right Shoulder'
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('Minor', 'Moderate', 'Severe', 'Catastrophic')),
    surgery_required BOOLEAN NOT NULL DEFAULT FALSE,
    recovery_time_days INT CHECK (recovery_time_days >= 0),
    return_to_play_date DATE,
    recurrence_risk_score NUMERIC(3,2) CHECK (recurrence_risk_score BETWEEN 0.00 AND 1.00),
    medical_notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_injuries_player ON player_injuries(player_id);

-- ============================================================================
-- ENTITY 20: DERIVED FEATURES (derived_features)
-- Purpose: Precalculated feature store vectors, TSR, TER, WPA, VORP, valuations.
-- ============================================================================
CREATE TABLE derived_features (
    feature_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    player_id UUID NOT NULL REFERENCES players(player_id) ON DELETE CASCADE,
    feature_group VARCHAR(50) NOT NULL CHECK (feature_group IN (
        'Batting Phase', 'Bowling Phase', 'Matchup Matrix', 'Clutch & Pressure',
        'Venue Baselines', 'Auction Valuation', 'Injury Fatigue Risk'
    )),
    feature_name VARCHAR(100) NOT NULL,
    feature_value_numeric NUMERIC(12,4),
    feature_value_text TEXT,
    feature_value_json JSONB,
    calculation_window VARCHAR(50) NOT NULL, -- e.g., 'Career', '3_Year_Rolling', 'Season_2024'
    model_version VARCHAR(20) NOT NULL DEFAULT 'v1.0',
    computed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_player_feature UNIQUE (player_id, feature_name, calculation_window, model_version)
);

CREATE INDEX idx_derived_features_player ON derived_features(player_id);
CREATE INDEX idx_derived_features_group ON derived_features(feature_group);
CREATE INDEX idx_derived_features_lookup ON derived_features(player_id, feature_name, calculation_window);
```

---

## 3. Player Identity Resolution Specification

### 3.1 Disambiguation Challenge
Cricket data providers use wildly disparate naming conventions for the same athlete:
- Cricsheet records: Short abbreviations or initials (`RV Uthappa`, `V Kohli`, `MS Dhoni`).
- Kaggle datasets: Expanded strings (`Robin Uthappa`, `Virat Kohli`, `Mahendra Singh Dhoni`).
- Patronymic collisions: Hundreds of players share common surnames (e.g., `RG Sharma` vs `MM Sharma` vs `KV Sharma`; `HH Pandya` vs `KH Pandya`).

### 3.2 Exhaustive 4-Tier Disambiguation Algorithm

```
                             INCOMING RAW PLAYER STRING
                                         │
                                         ▼
                      ┌──────────────────────────────────────┐
                      │ Tier 1: Canonical Hex Registry Match │
                      └──────────────────┬───────────────────┘
                                         │
                 ┌───────────────────────┴───────────────────────┐
                 │ Match in Cricsheet info.registry.people?     │
                 │ (e.g. "18e6906e" -> player_id)                │
                 ▼ YES                                           ▼ NO
       [CONFIDENCE: 1.000]                                       │
       Return canonical player_id                                │
                                                                 ▼
                                              ┌──────────────────────────────────────┐
                                              │ Tier 2: Alias Registry Exact Match   │
                                              └──────────────────┬───────────────────┘
                                                                 │
                                         ┌───────────────────────┴───────────────────────┐
                                         │ Exact match in player_aliases for source_id?  │
                                         ▼ YES                                           ▼ NO
                               [CONFIDENCE: 1.000]                                       │
                               Return canonical player_id                                │
                                                                                         ▼
                                              ┌──────────────────────────────────────┐
                                              │ Tier 3: Deterministic Context Match  │
                                              └──────────────────┬───────────────────┘
                                                                 │
                                         ┌───────────────────────┴───────────────────────┐
                                         │ Match date in squad_memberships for team?     │
                                         │ AND Surname + Initials match unique player?   │
                                         ▼ YES                                           ▼ NO / Ambiguous
                               [CONFIDENCE: 0.980]                                       │
                               Return player_id, Insert alias                            │
                                                                                         ▼
                                              ┌──────────────────────────────────────┐
                                              │ Tier 4: Probabilistic Fuzzy + Bio    │
                                              └──────────────────┬───────────────────┘
                                                                 │
                                         ┌───────────────────────┴───────────────────────┐
                                         │ Jaro-Winkler >= 0.92, Levenshtein <= 2,       │
                                         │ Role + Hand + Career Active Window Match?     │
                                         ▼ YES (Score >= 0.950)                          ▼ NO / Collision
                               [CONFIDENCE: Computed]                     ┌──────────────────────────────┐
                               Insert alias (is_verified=FALSE)           │ QUARANTINE TO REVIEW TABLE   │
                                                                          │ needs_review=TRUE            │
                                                                          │ Alert Data Curator Queue     │
                                                                          └──────────────────────────────┘
```

#### Step-by-Step Waterfall Execution
1. **Tier 1: Canonical Registry Key Match**:
   - Inspect Cricsheet match metadata under `info.registry.people`.
   - If the player name maps to an 8-character hex hash matching `players.cricsheet_id`, resolve immediately with confidence `1.000`.
   - Check official BCCI ID or ESPNcricinfo player ID if present.
2. **Tier 2: Verified Alias Registry Lookup**:
   - Query `player_aliases` where `alias_name = LOWER(TRIM(input_name))` and `source_id = current_source_id`.
   - If found and `is_verified = TRUE`, resolve with confidence `1.000`.
3. **Tier 3: Deterministic Contextual Intersection**:
   - Extract `match_date`, `team_name`, and player initials/surname.
   - Filter active rosters in `squad_memberships` for that team on that date.
   - If exactly one player matches the surname and initial token, resolve with confidence `0.980` and insert an unverified alias record into `player_aliases`.
4. **Tier 4: Probabilistic Fuzzy Matching & Biometric Validation**:
   - Compute token-set ratio, Jaro-Winkler similarity ($S_{JW}$), and Levenshtein distance ($D_{Lev}$) against all candidates in the candidate pool.
   - Candidate must satisfy: $S_{JW} \ge 0.92$ AND $D_{Lev} \le 2$.
   - Cross-validate against physical biometrics: batting hand, bowling arm, and career active temporal window: $[\text{Debut Year} - 1, \text{Retirement Year} + 1]$.
   - If combined confidence score $\ge 0.950$ and candidate is unique: link `player_id`, insert to `player_aliases` with `is_verified = FALSE`.
   - If combined confidence $< 0.950$ or multiple ambiguous candidates exist: quarantine record by inserting to `player_aliases` with `needs_review = TRUE` and alert the data steward.

---

## 4. Match & Delivery Reconciliation Specification

### 4.1 Super Overs (Tie-Breaker Innings)
- **Problem**: Super Overs occur when a match ends in a tie (e.g., GL vs MI, 2017; Match 1082625). Under official ICC and BCCI statistical governance, runs scored, balls faced, and wickets taken in a Super Over are excluded from official career averages, season aggregates, and milestone counts.
- **Relational Representation**:
  - Super Over innings are recorded in `innings` with `is_super_over = TRUE` (assigned `innings_number` 3 and 4).
  - All deliveries in the Super Over are stored in `deliveries` linked to the Super Over `innings_id`.
- **Query & Reporting Discipline**:
  - Standard career profile queries, season leaderboards, and scorecard APIs mandate a default predicate: `WHERE is_super_over = FALSE`.
  - Super Over records are exclusively queried by the *High-Pressure & Clutch Index Engine* to evaluate extreme leverage execution.

### 4.2 Rain-Shortened Matches & Duckworth-Lewis-Stern (DLS) Adjustments
- **Problem**: Rain interruptions shorten available overs from 20 to $N$ overs ($5 \le N < 20$), resetting the 2nd innings target (e.g., KKR vs SRH, 2017; Match 1082648 target 48 in 6 overs). Standard strike rates and economy rates become incomparable against full 20-over baselines.
- **Relational Representation**:
  - `matches.is_dls_applied` is set to `TRUE`.
  - `innings.target_runs` and `innings.target_overs` capture revised targets.
- **Analytical Adjustment**:
  - The pipeline calculates **Normalized True Run Rate (NTRR)** by benchmarking actual run rates against phase-specific DLS resource consumption tables rather than static 20-over par rates.

### 4.3 Penalty Runs Attribution
- **Problem**: Under MCC Law 41/42, fielding infractions or ball hitting a discarded helmet award 5 penalty runs to the batting side (e.g., Match 335988). If charged to the bowler, the bowler's figures are unfairly inflated by 5 runs.
- **Attribution Rule**:
  - Penalty runs are recorded in `deliveries.runs_penalties = 5`, `runs_extras = 5`, `runs_total = 5`, `runs_batter = 0`.
  - In `bowling_spell`, runs conceded strictly evaluates:
    $$\text{runs\_conceded} = \sum (\text{runs\_batter} + \text{runs\_wides} + \text{runs\_noballs})$$
  - `runs_byes`, `runs_legbyes`, and `runs_penalties` are EXCLUDED from bowler runs conceded.

### 4.4 Substitute Fielders Tracking
- **Problem**: An injured player is replaced on the field by a substitute who executes a catch or run-out (e.g., `1082591.json` delivery 19.4: `"name": "CJ Jordan", "substitute": true`). If the database requires fielders to be in the match starting XI, foreign key violations crash the ingestion pipeline.
- **Schema Resolution**:
  - `fielding_events.player_id` references `players(player_id)` directly, with `is_substitute = TRUE`.
  - This allows attribution of catches and run outs without violating the starting XI roster constraints in `squad_memberships`.

---

## 5. Contextual Enrichment Pipeline

Granular ball-by-ball deliveries are augmented across four critical analytical dimensions to capture match context:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       CONTEXTUAL ENRICHMENT PIPELINE                        │
└─────────────────────────────────────────────────────────────────────────────┘
          │                                                  │
          ▼                                                  ▼
┌──────────────────────────────────┐       ┌──────────────────────────────────┐
│  Spatial Venue & Geometry        │       │  Open-Meteo Macro-Weather        │
│  - Stadium Elevation (m)         │       │  - Temperature (°C) & Humidity   │
│  - Boundary Radii (Off/Leg/Strt) │       │  - Dew Point & Wet Ball Index    │
│  - Altitude Aerodynamic Drag     │       │  - Macro Environmental Flag      │
└──────────────────────────────────┘       └──────────────────────────────────┘
          │                                                  │
          ▼                                                  ▼
┌──────────────────────────────────┐       ┌──────────────────────────────────┐
│  Pitch & Surface Degradation     │       │  Situational Leverage & Pressure │
│  - Soil Type (Red vs Black Soil) │       │  - Required vs Current Run Rate  │
│  - Pace / Bounce / Turn Ratings  │       │  - Wickets in Hand               │
│  - Historical 3-Yr Par Score     │       │  - Win Expectancy & Leverage (LI)│
└──────────────────────────────────┘       └──────────────────────────────────┘
```

### 5.1 Open-Meteo Macro-Weather Integration
- **Mechanism**: The enrichment engine queries historical weather archives using venue latitude, longitude, and match start timestamp.
- **Parameters Enriched**:
  - Ambient Temperature ($T$ in $^\circ\text{C}$).
  - Relative Humidity ($RH$ in %).
  - Dew Point ($T_{dew}$ in $^\circ\text{C}$).
  - Wind Speed and Direction.
- **Dew Impact Index**:
  Evaluated during 2nd innings of evening matches:
  $$\Delta T = T - T_{dew}$$
  - $\Delta T \le 2.0^\circ\text{C} \implies \text{'Heavy / Ball Slippery'}$
  - $2.0^\circ\text{C} < \Delta T \le 4.0^\circ\text{C} \implies \text{'Moderate'}$
  - $\Delta T > 4.0^\circ\text{C} \implies \text{'Low / None'}$
- **Integrity Mandate**: Stored with `data_provenance_flag = 'Open-Meteo Macro Environmental Context (Not Direct Pitch Moisture)'`. It is strictly prohibited to claim direct internal stadium turf moisture from macro-atmospheric telemetry.

### 5.2 Spatial Venue & Boundary Dimensions
- Venue elevation (e.g., Bengaluru: 920m above sea level) reduces aerodynamic air density, increasing projectile distance by approximately 4–6%.
- Stadium boundary dimensions (meters to off-side, leg-side, straight) allow true normalization of boundary-hitting capability.

### 5.3 Pitch Surface Classification
- **Red Soil**: High clay content, greater bounce, higher deterioration rate, aids pace and seam early, sharp spin later.
- **Black Soil**: Clay-loam mix, lower bounce, holds moisture, slower surface, gripping spin as match progresses.
- Quantitative pace, bounce, and turn ratings (1.0 to 10.0 scale) calibrated against historical 1st innings par scores over a rolling 3-year window.

### 5.4 Situational Leverage Index (LI)
- Evaluates the swing potential of each delivery on win probability:
  $$\text{LI} = \frac{\Delta \text{Win Probability}}{\overline{\Delta \text{Win Probability}}_{\text{all balls}}}$$
- Deliveries with $\text{LI} > 1.5$ are categorized as *High-Pressure / Clutch Scenarios*.

---

## 6. Statistical Computation Engine & Mathematical Models

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                 CRICKET SABERMETRIC COMPUTATION ENGINE                      │
└─────────────────────────────────────────────────────────────────────────────┘
          │                                                  │
          ▼                                                  ▼
┌──────────────────────────────────┐       ┌──────────────────────────────────┐
│  True Strike Rate (TSR)          │       │  True Economy Rate (TER)         │
│  TSR = SR_actual - SR_expected   │       │  TER = Econ_actual - Econ_expect │
│  (Adjusted for Phase & Venue)    │       │  (Adjusted for Phase & Venue)    │
└──────────────────────────────────┘       └──────────────────────────────────┘
          │                                                  │
          ▼                                                  ▼
┌──────────────────────────────────┐       ┌──────────────────────────────────┐
│  Win Probability Added (WPA)     │       │  Value Over Replacement (VORP)   │
│  WPA = WP_post - WP_pre          │       │  VORP = Net Run Value vs Baseln  │
│  (State: Balls, Runs, Wkts, Era) │       │  (Positional Replacement Tier)   │
└──────────────────────────────────┘       └──────────────────────────────────┘
```

### 6.1 True Strike Rate (TSR)
True Strike Rate isolates a batter's scoring velocity from tournament-wide scoring inflation and venue biases:
$$\text{TSR} = \text{SR}_{\text{actual}} - \text{SR}_{\text{expected}}$$
Where:
$$\text{SR}_{\text{expected}} = \sum_{p \in \text{Phases}} \left( \frac{\text{Balls}_{p}}{\text{Balls}_{\text{total}}} \times \overline{\text{SR}}_{p, \text{venue}, \text{season}} \right)$$
- Positive TSR indicates scoring speed above par for that specific venue and phase mix.

### 6.2 True Economy Rate (TER)
True Economy Rate measures runs conceded per over relative to venue and phase expectations:
$$\text{TER} = \text{Economy}_{\text{actual}} - \text{Economy}_{\text{expected}}$$
- Negative TER indicates a bowler conceding fewer runs than expectation (superior performance).

### 6.3 Win Probability Added (WPA)
For every delivery $t$:
$$\text{WPA}_{t} = \text{WP}_{t} - \text{WP}_{t-1}$$
Where $\text{WP}_{t}$ is derived from the empirical win-expectancy transition matrix given state $(B_{\text{rem}}, R_{\text{target}}, W_{\text{lost}}, \text{Phase})$.
- The batter is credited with positive $\text{WPA}$ for boundary hits and negative $\text{WPA}$ for dot balls in high-pressure chases.
- The bowler is credited with positive $\text{WPA}$ for dismissals and tight bowling sequences.

### 6.4 Value Over Replacement Player (VORP)
Quantifies player contribution above a replacement-level domestic cricketer available at base auction price:
$$\text{VORP} = \left( \text{Runs Scored} - \text{Balls Faced} \times \frac{\text{Runs}_{\text{repl}}}{\text{Balls}_{\text{repl}}} \right) + \left( \text{Overs Bowled} \times \text{Econ}_{\text{repl}} - \text{Runs Conceded} \right) + \text{Fielding Runs Saved}$$

### 6.5 Clutch Index
Evaluates player efficiency conditioned on high-leverage deliveries:
$$\text{Clutch Index} = \frac{\sum_{t \in \text{Deliveries}} \text{WPA}_{t} \times \mathbb{I}(\text{LI}_{t} \ge 1.5)}{\sum_{t \in \text{Deliveries}} \mathbb{I}(\text{LI}_{t} \ge 1.5)}$$

### 6.6 Domain Guardrails & Statistical Safeguards
1. **Strict Missing Value Protocol**:
   - Zero dismissals $\implies$ Batting Average is `NULL` (displayed as `NOT OUT` / `N/A`), NEVER `0.00`.
   - Zero legal balls bowled $\implies$ Economy Rate and Bowling Average are `NULL`, NEVER `0.00`.
   - Missing Hawk-Eye coordinates or speeds $\implies$ Field values remain `NULL`, NEVER imputed as `0.0`.
2. **Separation of Trait vs Variation**:
   - `players.bowling_style` stores physical biological style (e.g., `'Right-arm legbreak'`).
   - `deliveries.variation_type` stores delivery event variation (e.g., `'Googly'`).
   - Bowling variations must NEVER overwrite canonical player styles.
3. **Tracking Coordinates**:
   - `post_shot_landing_x` and `post_shot_landing_y` represent terminal ball coordinates, NEVER to be interpreted as starting fielder positions.

---

## 7. API Specification (FastAPI Architecture)

The planned API layer is specified for implementation in FastAPI (Python 3.11+), utilizing asynchronous handlers, Pydantic v2 schemas, and RFC 7807 error responses. `[STATUS: PLANNED - GREENFIELD BASELINE]`

### 7.1 REST Endpoints

| Method | Route | Description | Query Parameters | Cache TTL |
|--------|-------|-------------|------------------|-----------|
| `GET` | `/api/v1/players/{id}/profile` | Comprehensive player profile, career totals, splits | `include_splits: bool = false` | 3600s |
| `GET` | `/api/v1/players/{id}/phases` | Phase-by-phase breakdown (PP, Mid 1, Mid 2, Death) | `season_year: Optional[str]`, `comp_id: Optional[UUID]` | 3600s |
| `GET` | `/api/v1/players/{id}/matchups` | Head-to-head matchup splits vs bowlers/styles | `bowling_type: Optional[str]`, `min_balls: int = 6` | 1800s |
| `GET` | `/api/v1/squads/{team_id}/depth-chart` | Squad depth chart by role with overseas limits | `season_id: UUID` | 600s |
| `GET` | `/api/v1/squads/{team_id}/budget` | Purse balance, retained salaries, budget headroom | `season_id: UUID` | 300s |
| `GET` | `/api/v1/matches/{id}/ball-by-ball` | Granular delivery ledger for match | `innings_number: Optional[int]` | 86400s |
| `GET` | `/api/v1/scouting/candidates` | Filterable recruitment pool for auction targets | `role: Optional[str]`, `is_overseas: Optional[bool]`, `limit: int = 50`, `offset: int = 0` | 300s |
| `POST`| `/api/v1/scouting/valuation-matrix` | Computes VORP, venue fit, and bidding price band | Request Body: `ValuationCriteriaRequest` | None (Live) |
| `GET` | `/api/v1/venues/{id}/conditions` | Venue pitch ratings, boundary sizes, par scores | `season_window: int = 3` | 86400s |

### 7.2 Pydantic v2 Schema Models

```python
from pydantic import BaseModel, Field, UUID4
from typing import Optional, List
from datetime import date

class PlayerBase(BaseModel):
    player_id: UUID4
    canonical_name: str
    primary_role: str
    batting_hand: Optional[str] = None
    bowling_style: Optional[str] = None
    nationality: str

class PhasePerformanceMetrics(BaseModel):
    phase: str = Field(..., description="Powerplay, Middle 1, Middle 2, Death")
    runs: int
    balls: int
    strike_rate: Optional[float] = Field(None, description="NULL if balls faced is 0")
    dot_ball_pct: Optional[float] = None
    boundary_pct: Optional[float] = None
    wickets_lost_or_taken: int
    true_strike_rate: Optional[float] = Field(None, description="Adjusted for venue baseline")
    true_economy_rate: Optional[float] = Field(None, description="Adjusted for venue baseline")

class PlayerProfileResponse(BaseModel):
    player: PlayerBase
    is_overseas: bool
    total_t20_matches: int
    batting_career: Optional[dict] = None
    bowling_career: Optional[dict] = None
    phase_metrics: List[PhasePerformanceMetrics] = []
    injury_recurrence_risk: float = Field(0.0, ge=0.0, le=1.0)
    data_provenance: str = "Pristine Scorecard Normalization"

class ValuationCriteriaRequest(BaseModel):
    candidate_player_id: UUID4
    target_role: str
    home_venue_id: UUID4
    purse_remaining_inr: float = Field(..., gt=0)
    tactical_need_weight: float = Field(1.0, ge=0.5, le=2.0)

class AuctionValuationResponse(BaseModel):
    candidate_player_id: UUID4
    vorp_score: float
    venue_fit_multiplier: float
    injury_discount_factor: float
    recommended_base_bid_inr: float
    recommended_ceiling_bid_inr: float
    risk_rating: str
```

### 7.3 RFC 7807 Problem Details Error Responses

All error responses strictly comply with RFC 7807 (`application/problem+json`):

```json
{
  "type": "https://rajasthanroyals.com/errors/entity-not-found",
  "title": "Player Entity Not Found",
  "status": 404,
  "detail": "Player with UUID 550e8400-e29b-41d4-a716-446655440000 was not found in the master registry.",
  "instance": "/api/v1/players/550e8400-e29b-41d4-a716-446655440000/profile",
  "timestamp": "2026-11-07T07:30:00Z"
}
```

---

## 8. Technology Stack Rationale

| Tier | Chosen Technology | Evaluated Alternatives | Engineering Rationale |
|------|-------------------|------------------------|-----------------------|
| **Core Runtime** | Python 3.11+ | Node.js, Go | Rich scientific ecosystem (NumPy, SciPy, Pandas), exceptional asynchronous I/O performance via Uvicorn/uvloop. |
| **Data Processing** | Pandas 2.2+ & NumPy 1.26+ | Polars, DuckDB | Industry-standard vectorized sports analytics operations; native support for matrix pivoting and rolling time series. |
| **Relational Core** | PostgreSQL 16+ | MongoDB, MySQL, Cassandra | Strict 3NF relational integrity, native declarative partitioning on `deliveries`, robust JSONB indexing, and advanced GIS extensions. |
| **API Gateway** | FastAPI 0.110+ | Flask, Django REST | Native async ASGI, automatic OpenAPI 3.1 generation, high concurrency, strict type enforcement via Pydantic v2. |
| **In-Memory Cache** | Redis 7+ | Memcached, Local LRU | Distributed shared caching, sub-millisecond key retrieval, TTL eviction, and pub/sub cache invalidation. |
| **Frontend Framework** | Next.js 15 (React 19) | Vite SPA, Remix | App Router with Server-Side Rendering (SSR) for fast initial loads, streaming UI tables, and React Server Components. |
| **Design & Styling** | Tailwind CSS 3.4+ | CSS Modules, MUI | Utility-first CSS delivering a cohesive Rajasthan Royals royal blue and pink design system without stylesheet bloat. |
| **Graph Visualizer** | React Flow & Cytoscape.js | D3.js | Declarative canvas/SVG DAG graphs specifically optimized for squad depth charts and tactical bowling rotation networks. |
| **Charts & Heatmaps** | Apache ECharts 5.5+ & Recharts 2.12+ | Chart.js, Highcharts | ECharts delivers WebGL/Canvas acceleration for dense 360-degree wagon wheels and pitch spray heatmaps; Recharts provides SVG radar charts. |

---

## 9. Non-Functional Specifications (NFRs)

### 9.1 Performance & Latency SLAs
- **Cached API Reads**: $P_{95} < 10\text{ ms}$, $P_{99} < 25\text{ ms}$ (Redis in-memory cache).
- **Uncached Database Lookups**: $P_{95} < 50\text{ ms}$ (PostgreSQL indexed queries).
- **Complex Aggregations**: $P_{95} < 200\text{ ms}$ (Multidimensional matchup matrix computation).
- **Throughput**: Sustained capacity of $500\text{ req/sec}$ per API worker instance.

### 9.2 Connection Pooling & Concurrency
- `asyncpg` connection pool: Minimum 20 connections, Maximum 50 connections per API worker, max overflow of 10.
- Pool timeout set to $5.0\text{ seconds}$ to prevent connection exhaustion cascades.

### 9.3 Partition Pruning & Query Optimization
- Partition pruning enabled (`SET enable_partition_pruning = ON`).
- Queries targeting `deliveries` must mandate `season_year` or `match_id` predicates to avoid full-table sequential scans across 250,000+ records.

### 9.4 Security & Data Integrity
- Role-Based Access Control (RBAC): `Scout`, `Lead_Analyst`, `Data_Steward`, `Administrator`.
- Zero SQL Injection risk: Mandatory parameterized SQL queries via `asyncpg` / SQLAlchemy Core.
- Strict 3NF check constraints prevent negative runs, invalid over indices, or illegal match phases.
