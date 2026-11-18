-- ============================================================================
-- Rajasthan Royals (RR) Squad Intelligence & Team Composition Platform
-- Migration: 20261113000000_initial_schema.sql
-- Description: Complete PostgreSQL 16 schema covering all 33 TRD entities
-- Topology: 6-Level Topological Dependency Sort (zero circular dependencies)
-- Partitioning: List-partitioned deliveries by season_year with composite FKs
-- Indexes: B-tree, GIN (JSONB & Trigram), Partial, and Unique Expression Index
-- ============================================================================

BEGIN;

-- ----------------------------------------------------------------------------
-- 0. EXTENSIONS SETUP
-- ----------------------------------------------------------------------------
CREATE SCHEMA IF NOT EXISTS extensions;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA extensions;
CREATE EXTENSION IF NOT EXISTS "pg_trgm" WITH SCHEMA extensions;
CREATE EXTENSION IF NOT EXISTS "btree_gist" WITH SCHEMA extensions;

-- ----------------------------------------------------------------------------
-- LEVEL 0: ENTITIES WITH ZERO FOREIGN KEY DEPENDENCIES
-- ----------------------------------------------------------------------------

-- Entity 1: data_sources (TRD §11 Domain 1)
CREATE TABLE IF NOT EXISTS data_sources (
    source_id           UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    source_name         VARCHAR(100) NOT NULL,
    source_type         VARCHAR(50) NOT NULL,
    base_url            VARCHAR(255),
    license_type        VARCHAR(50) NOT NULL,
    license_status      VARCHAR(20) NOT NULL DEFAULT 'UNVERIFIED',
    license_evidence    TEXT,
    update_cadence      VARCHAR(30) NOT NULL,
    data_steward        VARCHAR(100) NOT NULL,
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_data_sources_name UNIQUE (source_name),
    CONSTRAINT chk_data_source_type CHECK (source_type IN (
        'JSON Feed', 'CSV Archive', 'REST API', 'Web Scraping / Official Feed',
        'Manual Ingestion', 'External Research'
    )),
    CONSTRAINT chk_license_status CHECK (license_status IN (
        'VERIFIED', 'PARTIALLY_VERIFIED', 'UNVERIFIED', 'UNAVAILABLE', 'RESTRICTED'
    ))
);

-- Entity 6: venues (TRD §11 Domain 3)
CREATE TABLE IF NOT EXISTS venues (
    venue_id            UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    stadium_name        VARCHAR(150) NOT NULL,
    canonical_name      VARCHAR(100),
    city                VARCHAR(100) NOT NULL,
    country             VARCHAR(50) NOT NULL,
    cricsheet_venue_id  VARCHAR(50),
    capacity            INT CHECK (capacity IS NULL OR capacity > 0),
    latitude            NUMERIC(9,6) CHECK (latitude IS NULL OR (latitude >= -90.0 AND latitude <= 90.0)),
    longitude           NUMERIC(9,6) CHECK (longitude IS NULL OR (longitude >= -180.0 AND longitude <= 180.0)),
    elevation_meters    INT CHECK (elevation_meters IS NULL OR elevation_meters >= -500),
    boundary_size_offside NUMERIC(5,2),
    boundary_size_legside NUMERIC(5,2),
    boundary_size_straight NUMERIC(5,2),
    pitch_type_default  VARCHAR(50),
    pitch_type_baseline VARCHAR(30) CHECK (pitch_type_baseline IS NULL OR pitch_type_baseline IN (
        'Batting Paradise', 'Pace & Bounce', 'Spin Friendly', 'Balanced', 'Slow & Low'
    )),
    home_team_id        UUID, -- Soft reference configured later if needed
    created_at          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_venue_name_city UNIQUE (stadium_name, city)
);

-- Entity 8: competitions (TRD §11 Domain 3)
CREATE TABLE IF NOT EXISTS competitions (
    competition_id      UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    name                VARCHAR(100) NOT NULL,
    competition_name    VARCHAR(100),
    competition_code    VARCHAR(20),
    competition_type    VARCHAR(30) NOT NULL DEFAULT 'Domestic Franchise T20',
    governing_body      VARCHAR(50) NOT NULL DEFAULT 'BCCI',
    country             VARCHAR(50) NOT NULL DEFAULT 'India',
    format              VARCHAR(20),
    gender              VARCHAR(10) NOT NULL DEFAULT 'Male',
    match_overs         INT NOT NULL DEFAULT 20 CHECK (match_overs > 0),
    balls_per_over      INT NOT NULL DEFAULT 6,
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_competitions_name UNIQUE (name),
    CONSTRAINT chk_comp_type CHECK (competition_type IN (
        'Domestic Franchise T20', 'Domestic T20', 'International T20',
        'Domestic List A', 'ODI', 'First Class', 'Other'
    )),
    CONSTRAINT chk_comp_gender CHECK (gender IN ('Male', 'Female', 'Mixed')),
    CONSTRAINT chk_bpo_sane CHECK (balls_per_over BETWEEN 2 AND 8)
);

-- Entity 29: user_teams (TRD §11 Domain 9)
CREATE TABLE IF NOT EXISTS user_teams (
    team_id             UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    team_name           VARCHAR(100) NOT NULL,
    created_by          VARCHAR(50),
    target_season       VARCHAR(20),
    notes               TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Entity 4: players (TRD §11 Domain 2)
CREATE TABLE IF NOT EXISTS players (
    player_id           UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    canonical_name      VARCHAR(100) NOT NULL,
    full_name           VARCHAR(150),
    date_of_birth       DATE,
    birth_year          INT CHECK (birth_year IS NULL OR (birth_year >= 1950 AND birth_year <= 2015)),
    nationality         VARCHAR(50) NOT NULL DEFAULT 'India',
    country             VARCHAR(50) NOT NULL DEFAULT 'India',
    is_overseas         BOOLEAN NOT NULL DEFAULT FALSE,
    primary_role        VARCHAR(30) NOT NULL DEFAULT 'Batter',
    playing_role        VARCHAR(30) NOT NULL DEFAULT 'Batter',
    batting_hand        VARCHAR(20),
    bowling_arm         VARCHAR(10),
    bowling_style       VARCHAR(50),
    cricsheet_id        VARCHAR(50),
    bcci_id             VARCHAR(50),
    espn_id             VARCHAR(50),
    identity_status     VARCHAR(20) NOT NULL DEFAULT 'UNRESOLVED',
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_player_primary_role CHECK (primary_role IN (
        'Top-order Batter', 'Middle-order Batter', 'Wicketkeeper Batter',
        'Batting All-rounder', 'Bowling All-rounder', 'Pace Bowler',
        'Spin Bowler', 'Wicketkeeper', 'Batter', 'Bowler', 'All-Rounder'
    )),
    CONSTRAINT chk_batting_hand CHECK (batting_hand IS NULL OR batting_hand IN (
        'Right', 'Left', 'Right-hand bat', 'Left-hand bat'
    )),
    CONSTRAINT chk_bowling_arm CHECK (bowling_arm IS NULL OR bowling_arm IN ('Right', 'Left')),
    CONSTRAINT chk_identity_status CHECK (identity_status IN (
        'RESOLVED', 'PROVISIONAL', 'UNRESOLVED'
    ))
);

-- ----------------------------------------------------------------------------
-- LEVEL 1: DIRECT DEPENDENTS ON LEVEL 0
-- ----------------------------------------------------------------------------

-- Entity 2: source_records (TRD §11 Domain 1)
CREATE TABLE IF NOT EXISTS source_records (
    record_id           UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    source_id           UUID NOT NULL REFERENCES data_sources(source_id) ON DELETE RESTRICT,
    external_entity_id  VARCHAR(100) NOT NULL,
    raw_payload         JSONB NOT NULL,
    payload_sha256      CHAR(64) NOT NULL,
    ingestion_timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    processing_status   VARCHAR(30) NOT NULL DEFAULT 'Pending',
    error_message       TEXT,
    parsed_entity_type  VARCHAR(50),
    core_record_id      UUID,
    CONSTRAINT uq_source_payload_hash UNIQUE (source_id, external_entity_id, payload_sha256),
    CONSTRAINT chk_processing_status CHECK (processing_status IN (
        'Pending', 'Parsed', 'Normalized', 'Failed', 'Quarantined'
    ))
);

-- Entity 5: player_aliases (TRD §11 Domain 2)
CREATE TABLE IF NOT EXISTS player_aliases (
    alias_id            UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    player_id           UUID NOT NULL REFERENCES players(player_id) ON DELETE CASCADE,
    alias_name          VARCHAR(100) NOT NULL,
    source_id           UUID NOT NULL REFERENCES data_sources(source_id) ON DELETE RESTRICT,
    match_threshold_met BOOLEAN NOT NULL DEFAULT FALSE,
    is_verified         BOOLEAN NOT NULL DEFAULT FALSE,
    needs_review        BOOLEAN NOT NULL DEFAULT FALSE,
    verified_by         VARCHAR(50),
    verified_at         TIMESTAMPTZ,
    match_context       TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_alias_source UNIQUE (alias_name, source_id)
);

-- Entity 7: teams (TRD §11 Domain 3)
CREATE TABLE IF NOT EXISTS teams (
    team_id             UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    team_name           VARCHAR(100) NOT NULL,
    short_code          VARCHAR(10) NOT NULL,
    team_short_name     VARCHAR(10),
    home_venue_id       UUID REFERENCES venues(venue_id) ON DELETE SET NULL,
    franchise_group     VARCHAR(50),
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_teams_short_code UNIQUE (short_code)
);

-- Entity 9: seasons (TRD §11 Domain 3)
CREATE TABLE IF NOT EXISTS seasons (
    season_id           UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    competition_id      UUID NOT NULL REFERENCES competitions(competition_id) ON DELETE RESTRICT,
    season_year         VARCHAR(20) NOT NULL,
    start_date          DATE NOT NULL,
    end_date            DATE NOT NULL,
    roster_lock_date    DATE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_comp_season UNIQUE (competition_id, season_year),
    CONSTRAINT chk_season_dates CHECK (end_date >= start_date)
);

-- Entity 30: user_team_players (TRD §11 Domain 9)
CREATE TABLE IF NOT EXISTS user_team_players (
    id                  UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_team_id        UUID NOT NULL REFERENCES user_teams(team_id) ON DELETE CASCADE,
    player_id           UUID NOT NULL REFERENCES players(player_id) ON DELETE RESTRICT,
    assigned_role       VARCHAR(30),
    batting_order       INT CHECK (batting_order IS NULL OR (batting_order BETWEEN 1 AND 11)),
    is_designated_wk    BOOLEAN NOT NULL DEFAULT FALSE,
    is_captain          BOOLEAN NOT NULL DEFAULT FALSE,
    added_at            TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_team_player UNIQUE (user_team_id, player_id)
);

-- ----------------------------------------------------------------------------
-- LEVEL 2: SECONDARY TRANSACTIONAL & PROVENANCE ENTITIES
-- ----------------------------------------------------------------------------

-- Entity 3: verification_records (TRD §11 Domain 1)
CREATE TABLE IF NOT EXISTS verification_records (
    verification_id     UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    subject_type        VARCHAR(30) NOT NULL,
    subject_id          UUID NOT NULL,
    source_record_id    UUID REFERENCES source_records(record_id) ON DELETE SET NULL,
    data_source_id      UUID REFERENCES data_sources(source_id) ON DELETE SET NULL,
    source_url          VARCHAR(500),
    source_provider     VARCHAR(100),
    evidence_tier       INT,
    retrieval_ts        TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    license             VARCHAR(80),
    verification_status VARCHAR(30) NOT NULL DEFAULT 'PENDING',
    confidence          FLOAT CHECK (confidence IS NULL OR (confidence >= 0.0 AND confidence <= 1.0)),
    original_source_record_id VARCHAR(100),
    notes               TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_subject_type CHECK (subject_type IN (
        'player_identity', 'player_membership', 'player_eligibility',
        'match_performance', 'auction_record', 'medical_clearance'
    )),
    CONSTRAINT chk_verification_status CHECK (verification_status IN (
        'VERIFIED', 'PARTIALLY_VERIFIED', 'UNVERIFIED', 'CONFLICT', 'PENDING'
    ))
);

-- Entity 13: matches (TRD §11 Domain 4)
CREATE TABLE IF NOT EXISTS matches (
    match_id            UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    external_cricsheet_id VARCHAR(50) UNIQUE,
    season_id           UUID NOT NULL REFERENCES seasons(season_id) ON DELETE RESTRICT,
    venue_id            UUID NOT NULL REFERENCES venues(venue_id) ON DELETE RESTRICT,
    match_number        INT,
    match_type          VARCHAR(30) NOT NULL DEFAULT 'T20',
    match_date          DATE NOT NULL,
    home_team_id        UUID NOT NULL REFERENCES teams(team_id) ON DELETE RESTRICT,
    away_team_id        UUID NOT NULL REFERENCES teams(team_id) ON DELETE RESTRICT,
    toss_winner_id      UUID REFERENCES teams(team_id) ON DELETE RESTRICT,
    toss_decision       VARCHAR(10) CHECK (toss_decision IS NULL OR toss_decision IN ('bat', 'field')),
    winner_id           UUID REFERENCES teams(team_id) ON DELETE RESTRICT,
    outcome_type        VARCHAR(30) NOT NULL,
    win_margin_runs     INT CHECK (win_margin_runs IS NULL OR win_margin_runs >= 0),
    win_margin_wickets  INT CHECK (win_margin_wickets IS NULL OR win_margin_wickets >= 0),
    is_dls_applied      BOOLEAN NOT NULL DEFAULT FALSE,
    dls_method_version  VARCHAR(20),
    player_of_match_id  UUID REFERENCES players(player_id) ON DELETE SET NULL,
    innings_balls_scheduled INT NOT NULL DEFAULT 120 CHECK (innings_balls_scheduled > 0),
    source_record_id    UUID REFERENCES source_records(record_id) ON DELETE SET NULL,
    status              VARCHAR(20) NOT NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_match_teams CHECK (home_team_id <> away_team_id),
    CONSTRAINT chk_match_outcome CHECK (outcome_type IN (
        'runs', 'wickets', 'tie', 'super_over', 'no_result', 'abandoned'
    )),
    CONSTRAINT chk_match_status CHECK (status IN (
        'Scheduled', 'Completed', 'Abandoned', 'No Result'
    ))
);

-- Entity 23: player_injuries (TRD §11 Domain 7)
CREATE TABLE IF NOT EXISTS player_injuries (
    injury_id           UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    player_id           UUID NOT NULL REFERENCES players(player_id) ON DELETE CASCADE,
    injury_date         DATE,
    injury_type         VARCHAR(50),
    body_part           VARCHAR(50),
    severity            VARCHAR(20) CHECK (severity IS NULL OR severity IN ('Minor', 'Moderate', 'Severe', 'Catastrophic')),
    surgery_required    BOOLEAN,
    recovery_time_days  INT CHECK (recovery_time_days IS NULL OR recovery_time_days >= 0),
    return_to_play_date DATE,
    recurrence_risk_score NUMERIC(3,2) CHECK (recurrence_risk_score IS NULL OR (recurrence_risk_score >= 0.00 AND recurrence_risk_score <= 1.00)),
    medical_notes       TEXT,
    source_record_id    UUID REFERENCES source_records(record_id) ON DELETE SET NULL,
    verified            BOOLEAN NOT NULL DEFAULT FALSE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Entity 22: player_availability (TRD §11 Domain 7)
CREATE TABLE IF NOT EXISTS player_availability (
    availability_id     UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    player_id           UUID NOT NULL REFERENCES players(player_id) ON DELETE CASCADE,
    season_id           UUID NOT NULL REFERENCES seasons(season_id) ON DELETE CASCADE,
    start_date          DATE NOT NULL,
    end_date            DATE NOT NULL,
    availability_status VARCHAR(30),
    national_board_noc_status VARCHAR(20) CHECK (national_board_noc_status IS NULL OR national_board_noc_status IN ('GRANTED', 'DENIED', 'UNKNOWN', 'NOT_APPLICABLE')),
    matches_expected_available INT CHECK (matches_expected_available IS NULL OR matches_expected_available >= 0),
    reason_for_unavailability TEXT,
    source_record_id    UUID REFERENCES source_records(record_id) ON DELETE SET NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_player_season_avail UNIQUE (player_id, season_id, start_date),
    CONSTRAINT chk_avail_dates CHECK (end_date >= start_date)
);

-- Entity 25: player_competition_history (TRD §11 Domain 7)
CREATE TABLE IF NOT EXISTS player_competition_history (
    comp_history_id     UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    player_id           UUID NOT NULL REFERENCES players(player_id) ON DELETE CASCADE,
    competition_id      UUID NOT NULL REFERENCES competitions(competition_id) ON DELETE RESTRICT,
    season_year         VARCHAR(20) NOT NULL,
    season_id           UUID REFERENCES seasons(season_id) ON DELETE SET NULL,
    appearances         INT CHECK (appearances IS NULL OR appearances >= 0),
    coverage_status     VARCHAR(30) NOT NULL,
    provenance_id       UUID REFERENCES source_records(record_id) ON DELETE SET NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_player_comp_season UNIQUE (player_id, competition_id, season_year),
    CONSTRAINT chk_coverage_status CHECK (coverage_status IN (
        'VERIFIED_PARTICIPATION', 'DATASET_UNAVAILABLE', 'NOT_ESTABLISHED', 'CONFIRMED_NON_PARTICIPATION'
    ))
);

-- Entity 31: derived_features (TRD §11 Domain 10)
CREATE TABLE IF NOT EXISTS derived_features (
    feature_id          UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    player_id           UUID NOT NULL REFERENCES players(player_id) ON DELETE CASCADE,
    feature_group       VARCHAR(50) NOT NULL,
    feature_name        VARCHAR(100) NOT NULL,
    feature_value_numeric NUMERIC(14,4),
    feature_value_text  TEXT,
    feature_value_json  JSONB,
    calculation_window  VARCHAR(50) NOT NULL,
    format_tag          VARCHAR(20),
    status              VARCHAR(20) NOT NULL DEFAULT 'DERIVED',
    model_version       VARCHAR(20) NOT NULL DEFAULT 'v2.1',
    source_provenance   UUID REFERENCES source_records(record_id) ON DELETE SET NULL,
    computed_at         TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_feature_group CHECK (feature_group IN (
        'Batting', 'Bowling', 'Fielding', 'Wicketkeeping', 'Matchup Matrix',
        'Clutch & Pressure', 'Venue Baselines', 'Squad Intelligence', 'Career Coverage'
    )),
    CONSTRAINT chk_feature_status CHECK (status IN (
        'OBSERVED', 'DERIVED', 'MODEL_INFERRED', 'NOT_COMPUTABLE', 'DEFERRED'
    ))
);

-- ----------------------------------------------------------------------------
-- LEVEL 3: MATCH SUB-STRUCTURES & POLICY ENTITIES
-- ----------------------------------------------------------------------------

-- Entity 10: team_season_participation (TRD §11 Domain 3)
CREATE TABLE IF NOT EXISTS team_season_participation (
    participation_id    UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    team_id             UUID NOT NULL REFERENCES teams(team_id) ON DELETE RESTRICT,
    season_id           UUID NOT NULL REFERENCES seasons(season_id) ON DELETE RESTRICT,
    participation_status VARCHAR(20) NOT NULL DEFAULT 'PARTICIPATING',
    status              VARCHAR(20) NOT NULL DEFAULT 'CONFIRMED',
    effective_start_date DATE,
    effective_end_date  DATE,
    verified            BOOLEAN NOT NULL DEFAULT FALSE,
    evidence_source_id  UUID REFERENCES data_sources(source_id) ON DELETE SET NULL,
    verification_id     UUID REFERENCES verification_records(verification_id) ON DELETE SET NULL,
    verification_status VARCHAR(20) NOT NULL DEFAULT 'UNVERIFIED',
    notes               TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_team_season UNIQUE (team_id, season_id),
    CONSTRAINT chk_tsp_status CHECK (status IN (
        'CONFIRMED', 'WITHDRAWN', 'DISQUALIFIED', 'PROVISIONAL'
    )),
    CONSTRAINT chk_tsp_part_status CHECK (participation_status IN (
        'PARTICIPATING', 'SUSPENDED', 'NOT_ENTERED', 'UNKNOWN'
    )),
    CONSTRAINT chk_tsp_ver_status CHECK (verification_status IN (
        'PENDING', 'VERIFIED', 'UNVERIFIED', 'CONFLICT'
    )),
    CONSTRAINT chk_tsp_verified_evidence CHECK (NOT (verified = TRUE AND verification_id IS NULL))
);

-- Entity 11: squad_memberships (TRD §11 Domain 3)
CREATE TABLE IF NOT EXISTS squad_memberships (
    membership_id       UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    player_id           UUID NOT NULL REFERENCES players(player_id) ON DELETE CASCADE,
    team_id             UUID NOT NULL REFERENCES teams(team_id) ON DELETE RESTRICT,
    season_id           UUID NOT NULL REFERENCES seasons(season_id) ON DELETE RESTRICT,
    contract_type       VARCHAR(30) NOT NULL DEFAULT 'Squad Inclusion',
    role                VARCHAR(30) NOT NULL DEFAULT 'Player',
    salary_inr          NUMERIC(12,2) CHECK (salary_inr IS NULL OR salary_inr >= 0),
    jersey_number       INT CHECK (jersey_number IS NULL OR (jersey_number >= 0 AND jersey_number <= 999)),
    is_captain          BOOLEAN NOT NULL DEFAULT FALSE,
    is_overseas         BOOLEAN,
    is_active_squad     BOOLEAN, -- Nullable with NO default per TRD
    verified            BOOLEAN NOT NULL DEFAULT FALSE,
    evidence_source_id  UUID REFERENCES data_sources(source_id) ON DELETE SET NULL,
    notes               TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_squad_player_team_season UNIQUE (player_id, team_id, season_id),
    CONSTRAINT chk_squad_contract_type CHECK (contract_type IN (
        'Retained', 'Auction Buy', 'Replacement', 'Trade', 'Draft', 'Squad Inclusion', 'Released'
    )),
    CONSTRAINT chk_squad_role CHECK (role IN (
        'Player', 'Captain', 'Vice-Captain', 'Reserve', 'Injury Replacement'
    ))
);

-- Entity 12: player_team_history (TRD §11 Domain 3)
CREATE TABLE IF NOT EXISTS player_team_history (
    history_id          UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    player_id           UUID NOT NULL REFERENCES players(player_id) ON DELETE CASCADE,
    team_id             UUID NOT NULL REFERENCES teams(team_id) ON DELETE RESTRICT,
    season_year         VARCHAR(20) NOT NULL,
    season_id           UUID REFERENCES seasons(season_id) ON DELETE SET NULL,
    association_type    VARCHAR(30) NOT NULL,
    appearances         INT CHECK (appearances IS NULL OR appearances >= 0),
    evidence_source     UUID REFERENCES data_sources(source_id) ON DELETE SET NULL,
    provenance_id       UUID REFERENCES source_records(record_id) ON DELETE SET NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_history_player_team_season UNIQUE (player_id, team_id, season_year),
    CONSTRAINT chk_association_type CHECK (association_type IN (
        'Squad', 'Played', 'Released', 'Retained', 'Acquired', 'Loan'
    ))
);

-- Entity 14: innings (TRD §11 Domain 4)
CREATE TABLE IF NOT EXISTS innings (
    innings_id          UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    match_id            UUID NOT NULL REFERENCES matches(match_id) ON DELETE CASCADE,
    innings_number      INT NOT NULL CHECK (innings_number IN (1, 2, 3, 4)),
    batting_team_id     UUID NOT NULL REFERENCES teams(team_id) ON DELETE RESTRICT,
    bowling_team_id     UUID NOT NULL REFERENCES teams(team_id) ON DELETE RESTRICT,
    is_super_over       BOOLEAN NOT NULL DEFAULT FALSE,
    overs_allocated_balls INT NOT NULL DEFAULT 120 CHECK (overs_allocated_balls > 0),
    target_runs         INT CHECK (target_runs IS NULL OR target_runs >= 0),
    target_overs_balls  INT CHECK (target_overs_balls IS NULL OR target_overs_balls > 0),
    total_runs          INT NOT NULL DEFAULT 0 CHECK (total_runs >= 0),
    total_wickets       INT NOT NULL DEFAULT 0 CHECK (total_wickets BETWEEN 0 AND 10),
    total_legal_deliveries INT NOT NULL DEFAULT 0 CHECK (total_legal_deliveries >= 0),
    total_extras        INT NOT NULL DEFAULT 0 CHECK (total_extras >= 0),
    is_declared         BOOLEAN NOT NULL DEFAULT FALSE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_match_innings UNIQUE (match_id, innings_number, is_super_over),
    CONSTRAINT chk_innings_teams CHECK (batting_team_id <> bowling_team_id)
);

-- Entity 24: player_awards (TRD §11 Domain 7)
CREATE TABLE IF NOT EXISTS player_awards (
    award_id            UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    player_id           UUID NOT NULL REFERENCES players(player_id) ON DELETE CASCADE,
    match_id            UUID REFERENCES matches(match_id) ON DELETE SET NULL,
    award_type          VARCHAR(40) NOT NULL,
    award_value         VARCHAR(100),
    award_date          DATE,
    source_record_id    UUID REFERENCES source_records(record_id) ON DELETE SET NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_award_type CHECK (award_type IN (
        'Player of the Match', 'Player of the Tournament', 'MVP', 'Milestone', 'Other'
    ))
);

-- Entity 20: pitch_conditions (TRD §11 Domain 6)
CREATE TABLE IF NOT EXISTS pitch_conditions (
    pitch_condition_id  UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    match_id            UUID NOT NULL REFERENCES matches(match_id) ON DELETE CASCADE,
    venue_id            UUID NOT NULL REFERENCES venues(venue_id) ON DELETE RESTRICT,
    reported_description TEXT,
    soil_type           VARCHAR(50),
    grass_coverage      VARCHAR(30),
    reported_moisture   VARCHAR(30),
    reported_surface_state VARCHAR(40),
    pitch_pace_rating   NUMERIC(3,1) CHECK (pitch_pace_rating IS NULL OR (pitch_pace_rating BETWEEN 1.0 AND 10.0)),
    pitch_bounce_rating NUMERIC(3,1) CHECK (pitch_bounce_rating IS NULL OR (pitch_bounce_rating BETWEEN 1.0 AND 10.0)),
    pitch_turn_rating   NUMERIC(3,1) CHECK (pitch_turn_rating IS NULL OR (pitch_turn_rating BETWEEN 1.0 AND 10.0)),
    ratings_methodology_version VARCHAR(20),
    provenance_tier     VARCHAR(30) NOT NULL DEFAULT 'UNKNOWN',
    source_record_id    UUID REFERENCES source_records(record_id) ON DELETE SET NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_match_pitch UNIQUE (match_id),
    CONSTRAINT chk_pitch_prov_tier CHECK (provenance_tier IN (
        'DIRECTLY_MEASURED', 'OFFICIALLY_REPORTED', 'THIRD_PARTY_ESTIMATE', 'MODEL_INFERRED', 'UNKNOWN'
    )),
    CONSTRAINT chk_ratings_methodology CHECK (
        (pitch_pace_rating IS NULL AND pitch_bounce_rating IS NULL AND pitch_turn_rating IS NULL)
        OR ratings_methodology_version IS NOT NULL
    )
);

-- Entity 21: weather_conditions (TRD §11 Domain 6)
CREATE TABLE IF NOT EXISTS weather_conditions (
    weather_condition_id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    match_id            UUID NOT NULL REFERENCES matches(match_id) ON DELETE CASCADE,
    observation_timestamp TIMESTAMPTZ NOT NULL,
    venue_timezone      VARCHAR(40),
    local_observation_time TIMESTAMPTZ,
    temperature_celsius NUMERIC(4,1),
    relative_humidity_pct NUMERIC(4,1) CHECK (relative_humidity_pct IS NULL OR (relative_humidity_pct BETWEEN 0.0 AND 100.0)),
    dew_point_celsius   NUMERIC(4,1),
    dew_impact_index    VARCHAR(20),
    wind_speed_kmh      NUMERIC(5,2) CHECK (wind_speed_kmh IS NULL OR wind_speed_kmh >= 0),
    wind_direction_degrees INT CHECK (wind_direction_degrees IS NULL OR (wind_direction_degrees BETWEEN 0 AND 360)),
    precipitation_mm    NUMERIC(5,2) CHECK (precipitation_mm IS NULL OR precipitation_mm >= 0),
    atmospheric_pressure_hpa NUMERIC(6,1),
    cloud_cover_pct     NUMERIC(4,1) CHECK (cloud_cover_pct IS NULL OR (cloud_cover_pct BETWEEN 0.0 AND 100.0)),
    spatial_temporal_match_method VARCHAR(80),
    data_provider       VARCHAR(60),
    source_record_id    UUID REFERENCES source_records(record_id) ON DELETE SET NULL,
    data_provenance_flag VARCHAR(100) NOT NULL DEFAULT 'Macro Environmental Context (Not Direct Pitch Moisture)',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_match_weather_obs UNIQUE (match_id, observation_timestamp)
);

-- Entity 26: player_membership_state (TRD §11 Domain 7)
CREATE TABLE IF NOT EXISTS player_membership_state (
    state_id            UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    player_id           UUID NOT NULL REFERENCES players(player_id) ON DELETE CASCADE,
    as_of_date          DATE NOT NULL,
    rr_relationship_state VARCHAR(30) NOT NULL,
    rr_current_state    VARCHAR(15) NOT NULL,
    negative_verification_met BOOLEAN,
    evidence_verification_id UUID REFERENCES verification_records(verification_id) ON DELETE SET NULL,
    notes               TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_membership_state UNIQUE (player_id, as_of_date),
    CONSTRAINT chk_rr_rel_state CHECK (rr_relationship_state IN (
        'HISTORICAL_RR_APPEARANCE', 'HISTORICAL_RR_SQUAD_ONLY', 'PREVIOUSLY_ASSOCIATED',
        'NO_VERIFIED_RR_RELATIONSHIP', 'RR_RELATIONSHIP_UNKNOWN'
    )),
    CONSTRAINT chk_rr_curr_state CHECK (rr_current_state IN ('CURRENT', 'NOT_CURRENT', 'UNKNOWN'))
);

-- Entity 27: eligibility_policies (TRD §11 Domain 8)
CREATE TABLE IF NOT EXISTS eligibility_policies (
    policy_id           UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    season_id           UUID NOT NULL REFERENCES seasons(season_id) ON DELETE CASCADE,
    policy_version      INT NOT NULL DEFAULT 1 CHECK (policy_version >= 1),
    effective_date      DATE NOT NULL,
    expiry_date         DATE,
    rule_source         VARCHAR(200) NOT NULL,
    verified            BOOLEAN NOT NULL DEFAULT FALSE,
    verification_id     UUID REFERENCES verification_records(verification_id) ON DELETE SET NULL,
    policy_json         JSONB,
    notes               TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_policy UNIQUE (season_id, policy_version),
    CONSTRAINT chk_policy_dates CHECK (expiry_date IS NULL OR expiry_date >= effective_date),
    CONSTRAINT chk_policy_verified_evidence CHECK (NOT (verified = TRUE AND verification_id IS NULL))
);

-- ----------------------------------------------------------------------------
-- LEVEL 4: PARTITIONED DELIVERIES & SCORECARDS
-- ----------------------------------------------------------------------------

-- Entity 15: deliveries (TRD §11 Domain 4 - Partitioned by season_year)
CREATE TABLE IF NOT EXISTS deliveries (
    delivery_id         UUID NOT NULL DEFAULT extensions.uuid_generate_v4(),
    innings_id          UUID NOT NULL REFERENCES innings(innings_id) ON DELETE CASCADE,
    season_year         VARCHAR(20) NOT NULL,
    over_number         INT NOT NULL CHECK (over_number >= 0 AND over_number < 60),
    ball_in_over        INT NOT NULL CHECK (ball_in_over >= 1),
    delivery_sequence   INT NOT NULL CHECK (delivery_sequence >= 1),
    batter_id           UUID NOT NULL REFERENCES players(player_id) ON DELETE RESTRICT,
    bowler_id           UUID NOT NULL REFERENCES players(player_id) ON DELETE RESTRICT,
    non_striker_id      UUID NOT NULL REFERENCES players(player_id) ON DELETE RESTRICT,
    runs_batter         INT NOT NULL CHECK (runs_batter >= 0),
    runs_extras         INT NOT NULL DEFAULT 0 CHECK (runs_extras >= 0),
    runs_total          INT NOT NULL CHECK (runs_total >= 0),
    is_wide             BOOLEAN NOT NULL DEFAULT FALSE,
    is_noball           BOOLEAN NOT NULL DEFAULT FALSE,
    is_bye              BOOLEAN NOT NULL DEFAULT FALSE,
    is_legbye           BOOLEAN NOT NULL DEFAULT FALSE,
    is_penalty          BOOLEAN NOT NULL DEFAULT FALSE,
    runs_wides          INT NOT NULL DEFAULT 0 CHECK (runs_wides >= 0),
    runs_noballs        INT NOT NULL DEFAULT 0 CHECK (runs_noballs >= 0),
    runs_byes           INT NOT NULL DEFAULT 0 CHECK (runs_byes >= 0),
    runs_legbyes        INT NOT NULL DEFAULT 0 CHECK (runs_legbyes >= 0),
    runs_penalties      INT NOT NULL DEFAULT 0 CHECK (runs_penalties >= 0),
    is_wicket           BOOLEAN NOT NULL DEFAULT FALSE,
    wicket_kind         VARCHAR(30),
    player_out_id       UUID REFERENCES players(player_id) ON DELETE SET NULL,
    is_bowler_credited_wicket BOOLEAN NOT NULL DEFAULT FALSE,
    match_phase         VARCHAR(20) CHECK (match_phase IS NULL OR match_phase IN ('Powerplay', 'Middle', 'Death')),
    variation_type      VARCHAR(50),
    ball_speed_kph      NUMERIC(5,2) CHECK (ball_speed_kph IS NULL OR ball_speed_kph > 0),
    pitch_coordinate_x  NUMERIC(6,3),
    pitch_coordinate_y  NUMERIC(6,3),
    post_shot_landing_x NUMERIC(6,2),
    post_shot_landing_y NUMERIC(6,2),
    source_record_id    UUID REFERENCES source_records(record_id) ON DELETE SET NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_deliveries PRIMARY KEY (delivery_id, season_year),
    CONSTRAINT chk_runs_consistency CHECK (runs_total = runs_batter + runs_extras),
    CONSTRAINT chk_wicket_credit CHECK (is_wicket = TRUE OR player_out_id IS NULL)
) PARTITION BY LIST (season_year);

-- Declarative Child Partitions for deliveries
CREATE TABLE IF NOT EXISTS deliveries_y2008_2015 PARTITION OF deliveries
    FOR VALUES IN ('2008', '2009', '2010', '2011', '2012', '2013', '2014', '2015');

CREATE TABLE IF NOT EXISTS deliveries_y2016_2020 PARTITION OF deliveries
    FOR VALUES IN ('2016', '2017', '2018', '2019', '2020');

CREATE TABLE IF NOT EXISTS deliveries_y2021_2023 PARTITION OF deliveries
    FOR VALUES IN ('2021', '2022', '2023');

CREATE TABLE IF NOT EXISTS deliveries_y2024_2027 PARTITION OF deliveries
    FOR VALUES IN ('2024', '2025', '2026', '2027');

CREATE TABLE IF NOT EXISTS deliveries_default PARTITION OF deliveries DEFAULT;

-- Entity 16: batting_innings (TRD §11 Domain 5)
CREATE TABLE IF NOT EXISTS batting_innings (
    batting_innings_id  UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    innings_id          UUID NOT NULL REFERENCES innings(innings_id) ON DELETE CASCADE,
    player_id           UUID NOT NULL REFERENCES players(player_id) ON DELETE RESTRICT,
    team_id             UUID NOT NULL REFERENCES teams(team_id) ON DELETE RESTRICT,
    did_not_bat         BOOLEAN NOT NULL DEFAULT FALSE,
    batting_position    INT CHECK (batting_position IS NULL OR (batting_position BETWEEN 1 AND 11)),
    runs_scored         INT NOT NULL DEFAULT 0 CHECK (runs_scored >= 0),
    balls_faced         INT NOT NULL DEFAULT 0 CHECK (balls_faced >= 0),
    minutes_at_crease   INT CHECK (minutes_at_crease IS NULL OR minutes_at_crease >= 0),
    fours               INT NOT NULL DEFAULT 0 CHECK (fours >= 0),
    sixes               INT NOT NULL DEFAULT 0 CHECK (sixes >= 0),
    dot_balls_faced     INT NOT NULL DEFAULT 0 CHECK (dot_balls_faced >= 0),
    strike_rate         NUMERIC(6,2),
    dismissal_kind      VARCHAR(30),
    dismissal_bowler_id UUID REFERENCES players(player_id) ON DELETE SET NULL,
    dismissal_fielder_id UUID REFERENCES players(player_id) ON DELETE SET NULL,
    is_not_out          BOOLEAN NOT NULL,
    runs_powerplay      INT NOT NULL DEFAULT 0 CHECK (runs_powerplay >= 0),
    balls_powerplay     INT NOT NULL DEFAULT 0 CHECK (balls_powerplay >= 0),
    runs_middle         INT NOT NULL DEFAULT 0 CHECK (runs_middle >= 0),
    balls_middle        INT NOT NULL DEFAULT 0 CHECK (balls_middle >= 0),
    runs_death          INT NOT NULL DEFAULT 0 CHECK (runs_death >= 0),
    balls_death         INT NOT NULL DEFAULT 0 CHECK (balls_death >= 0),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_innings_batter UNIQUE (innings_id, player_id),
    CONSTRAINT chk_balls_faced CHECK (dot_balls_faced <= balls_faced),
    CONSTRAINT chk_sr_consistency CHECK (strike_rate IS NULL OR balls_faced > 0),
    CONSTRAINT chk_dnb_zero CHECK (NOT (did_not_bat = TRUE AND balls_faced > 0))
);

-- Entity 17: bowling_spells (TRD §11 Domain 5)
CREATE TABLE IF NOT EXISTS bowling_spells (
    spell_id            UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    innings_id          UUID NOT NULL REFERENCES innings(innings_id) ON DELETE CASCADE,
    player_id           UUID NOT NULL REFERENCES players(player_id) ON DELETE RESTRICT,
    team_id             UUID NOT NULL REFERENCES teams(team_id) ON DELETE RESTRICT,
    spell_order         INT NOT NULL DEFAULT 1 CHECK (spell_order >= 1),
    legal_balls_bowled  INT NOT NULL DEFAULT 0 CHECK (legal_balls_bowled >= 0),
    illegal_events_wides INT NOT NULL DEFAULT 0 CHECK (illegal_events_wides >= 0),
    illegal_events_noballs INT NOT NULL DEFAULT 0 CHECK (illegal_events_noballs >= 0),
    maidens             INT NOT NULL DEFAULT 0 CHECK (maidens >= 0),
    runs_conceded       INT NOT NULL DEFAULT 0 CHECK (runs_conceded >= 0),
    wickets_taken       INT NOT NULL DEFAULT 0 CHECK (wickets_taken BETWEEN 0 AND 10),
    dot_balls_bowled    INT NOT NULL DEFAULT 0 CHECK (dot_balls_bowled >= 0),
    economy_rate        NUMERIC(5,2),
    bowling_average     NUMERIC(6,2),
    bowling_strike_rate NUMERIC(5,2),
    runs_conceded_powerplay INT NOT NULL DEFAULT 0 CHECK (runs_conceded_powerplay >= 0),
    balls_bowled_powerplay INT NOT NULL DEFAULT 0 CHECK (balls_bowled_powerplay >= 0),
    wickets_powerplay   INT NOT NULL DEFAULT 0 CHECK (wickets_powerplay >= 0),
    runs_conceded_middle INT NOT NULL DEFAULT 0 CHECK (runs_conceded_middle >= 0),
    balls_bowled_middle INT NOT NULL DEFAULT 0 CHECK (balls_bowled_middle >= 0),
    wickets_middle      INT NOT NULL DEFAULT 0 CHECK (wickets_middle >= 0),
    runs_conceded_death INT NOT NULL DEFAULT 0 CHECK (runs_conceded_death >= 0),
    balls_bowled_death  INT NOT NULL DEFAULT 0 CHECK (balls_bowled_death >= 0),
    wickets_death       INT NOT NULL DEFAULT 0 CHECK (wickets_death >= 0),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_innings_bowler UNIQUE (innings_id, player_id),
    CONSTRAINT chk_dots_bowled CHECK (dot_balls_bowled <= legal_balls_bowled),
    CONSTRAINT chk_spell_econ CHECK (economy_rate IS NULL OR legal_balls_bowled > 0),
    CONSTRAINT chk_spell_avg CHECK (bowling_average IS NULL OR wickets_taken > 0)
);

-- Entity 19: wicketkeeping_events (TRD §11 Domain 5)
CREATE TABLE IF NOT EXISTS wicketkeeping_events (
    wk_event_id         UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    innings_id          UUID NOT NULL REFERENCES innings(innings_id) ON DELETE CASCADE,
    player_id           UUID NOT NULL REFERENCES players(player_id) ON DELETE RESTRICT,
    match_id            UUID NOT NULL REFERENCES matches(match_id) ON DELETE RESTRICT,
    stumpings           INT NOT NULL DEFAULT 0 CHECK (stumpings >= 0),
    catches             INT NOT NULL DEFAULT 0 CHECK (catches >= 0),
    missed_stumpings    INT CHECK (missed_stumpings IS NULL OR missed_stumpings >= 0),
    missed_catches      INT CHECK (missed_catches IS NULL OR missed_catches >= 0),
    appearances         INT NOT NULL CHECK (appearances > 0),
    provenance_tier     VARCHAR(30) NOT NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_wk_innings UNIQUE (innings_id, player_id),
    CONSTRAINT chk_wk_prov_tier CHECK (provenance_tier IN (
        'DIRECTLY_MEASURED', 'OFFICIALLY_REPORTED', 'THIRD_PARTY_ESTIMATE', 'MODEL_INFERRED', 'UNKNOWN'
    ))
);

-- Entity 28: player_eligibility (TRD §11 Domain 8)
CREATE TABLE IF NOT EXISTS player_eligibility (
    eligibility_id      UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    player_id           UUID NOT NULL REFERENCES players(player_id) ON DELETE CASCADE,
    policy_id           UUID NOT NULL REFERENCES eligibility_policies(policy_id) ON DELETE RESTRICT,
    eligibility_status  VARCHAR(25) NOT NULL,
    verified            BOOLEAN NOT NULL DEFAULT FALSE,
    verification_id     UUID REFERENCES verification_records(verification_id) ON DELETE SET NULL,
    notes               TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_player_policy UNIQUE (player_id, policy_id),
    CONSTRAINT chk_eligibility_status CHECK (eligibility_status IN (
        'VERIFIED_ELIGIBLE', 'VERIFIED_NOT_ELIGIBLE', 'ELIGIBILITY_UNVERIFIED', 'NOT_ASSESSED'
    )),
    CONSTRAINT chk_eligibility_status_flag CHECK (
        ((eligibility_status IN ('VERIFIED_ELIGIBLE', 'VERIFIED_NOT_ELIGIBLE') AND verified = TRUE AND verification_id IS NOT NULL)
         OR (eligibility_status IN ('ELIGIBILITY_UNVERIFIED', 'NOT_ASSESSED') AND verified = FALSE))
    )
);

-- Entity 32: ranking_configurations (TRD §11 Domain 11)
CREATE TABLE IF NOT EXISTS ranking_configurations (
    config_id           UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    config_version      VARCHAR(20) NOT NULL UNIQUE,
    target_season_id    UUID NOT NULL REFERENCES seasons(season_id) ON DELETE RESTRICT,
    policy_id           UUID NOT NULL REFERENCES eligibility_policies(policy_id) ON DELETE RESTRICT,
    evaluation_date     DATE NOT NULL,
    role_grouping_json  JSONB,
    gate_thresholds_json JSONB,
    ordering_json       JSONB NOT NULL,
    tiebreakers_json    JSONB,
    seed                INT NOT NULL DEFAULT 0,
    created_by          VARCHAR(50),
    verified            BOOLEAN NOT NULL DEFAULT FALSE,
    verification_id     UUID REFERENCES verification_records(verification_id) ON DELETE SET NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_ranking_config_evidence CHECK (NOT (verified = TRUE AND verification_id IS NULL))
);

-- ----------------------------------------------------------------------------
-- LEVEL 5: FIELDING EVENTS (COMPOSITE FK TO DELIVERIES) & RANKING RUNS
-- ----------------------------------------------------------------------------

-- Entity 18: fielding_events (TRD §11 Domain 5)
CREATE TABLE IF NOT EXISTS fielding_events (
    fielding_event_id   UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    delivery_id         UUID,
    season_year         VARCHAR(20),
    player_id           UUID NOT NULL REFERENCES players(player_id) ON DELETE RESTRICT,
    is_substitute       BOOLEAN NOT NULL DEFAULT FALSE,
    event_type          VARCHAR(30) NOT NULL,
    is_recorded_opportunity BOOLEAN NOT NULL DEFAULT TRUE,
    assisted_by_player_id UUID REFERENCES players(player_id) ON DELETE SET NULL,
    fielding_position   VARCHAR(40),
    runs_saved          INT CHECK (runs_saved IS NULL OR runs_saved >= 0),
    provenance_tier     VARCHAR(30) NOT NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_fielding_event_type CHECK (event_type IN (
        'Catch', 'Run Out Thrower', 'Run Out Catcher', 'Stumping',
        'Dropped Catch', 'Missed Run Out', 'Boundary Save'
    )),
    CONSTRAINT chk_fielding_prov_tier CHECK (provenance_tier IN (
        'DIRECTLY_MEASURED', 'OFFICIALLY_REPORTED', 'THIRD_PARTY_ESTIMATE', 'MODEL_INFERRED', 'UNKNOWN'
    )),
    CONSTRAINT chk_delivery_pairing CHECK (
        (delivery_id IS NULL AND season_year IS NULL) OR
        (delivery_id IS NOT NULL AND season_year IS NOT NULL)
    ),
    CONSTRAINT fk_fielding_delivery FOREIGN KEY (delivery_id, season_year)
        REFERENCES deliveries(delivery_id, season_year) ON DELETE SET NULL
);

-- Entity 33: ranking_runs (TRD §11 Domain 11)
CREATE TABLE IF NOT EXISTS ranking_runs (
    run_id              UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    config_id           UUID NOT NULL REFERENCES ranking_configurations(config_id) ON DELETE RESTRICT,
    data_snapshot_sha256 CHAR(64) NOT NULL,
    candidate_pool      JSONB NOT NULL,
    top10               JSONB NOT NULL,
    reserve_list        JSONB,
    computed_at         TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    determinism_note    TEXT,
    CONSTRAINT uq_run_per_config_snapshot UNIQUE (config_id, data_snapshot_sha256)
);

-- ----------------------------------------------------------------------------
-- PERFORMANCE INDEXES & EXPRESSION INDEXES
-- ----------------------------------------------------------------------------

-- 1. Unique Expression Index on derived_features (TRD D1)
CREATE UNIQUE INDEX IF NOT EXISTS uq_derived_features ON derived_features (
    player_id,
    feature_name,
    calculation_window,
    model_version,
    COALESCE(format_tag, '')
);

-- 2. PIRE Deterministic & Trigram Indexes
CREATE INDEX IF NOT EXISTS idx_players_clean_name 
    ON players (LOWER(TRIM(canonical_name)));

CREATE INDEX IF NOT EXISTS idx_players_name_trgm 
    ON players USING gin (LOWER(TRIM(canonical_name)) extensions.gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_player_aliases_clean_name 
    ON player_aliases (LOWER(TRIM(alias_name)));

CREATE INDEX IF NOT EXISTS idx_player_aliases_name_trgm 
    ON player_aliases USING gin (LOWER(TRIM(alias_name)) extensions.gin_trgm_ops);

-- 3. GIN Indexes on Semi-Structured JSONB fields
CREATE INDEX IF NOT EXISTS idx_source_records_payload_gin 
    ON source_records USING gin (raw_payload jsonb_path_ops);

CREATE INDEX IF NOT EXISTS idx_derived_features_json_gin 
    ON derived_features USING gin (feature_value_json jsonb_path_ops)
    WHERE feature_value_json IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_ranking_configs_ordering_gin 
    ON ranking_configurations USING gin (ordering_json jsonb_path_ops);

CREATE INDEX IF NOT EXISTS idx_ranking_runs_top10_gin 
    ON ranking_runs USING gin (top10 jsonb_path_ops);

CREATE INDEX IF NOT EXISTS idx_ranking_runs_candidate_pool_gin 
    ON ranking_runs USING gin (candidate_pool jsonb_path_ops);

-- 4. Partial Indexes for Queues and Active States
CREATE INDEX IF NOT EXISTS idx_players_active 
    ON players (player_id) WHERE is_active IS TRUE;

CREATE INDEX IF NOT EXISTS idx_teams_active 
    ON teams (team_id) WHERE is_active IS TRUE;

CREATE INDEX IF NOT EXISTS idx_player_aliases_review_queue 
    ON player_aliases (alias_id, player_id) WHERE needs_review IS TRUE;

CREATE INDEX IF NOT EXISTS idx_verification_conflict_queue 
    ON verification_records (verification_id, subject_type, subject_id) 
    WHERE verification_status = 'CONFLICT';

CREATE INDEX IF NOT EXISTS idx_verification_pending_queue 
    ON verification_records (verification_id, subject_type, subject_id) 
    WHERE verification_status = 'PENDING';

CREATE INDEX IF NOT EXISTS idx_source_records_quarantine_queue 
    ON source_records (record_id) WHERE processing_status = 'Quarantined';

CREATE INDEX IF NOT EXISTS idx_players_cricsheet_id 
    ON players (cricsheet_id) WHERE cricsheet_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_players_bcci_id 
    ON players (bcci_id) WHERE bcci_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_players_espn_id 
    ON players (espn_id) WHERE espn_id IS NOT NULL;

-- 5. Foreign Key & Query Acceleration B-Trees
CREATE INDEX IF NOT EXISTS idx_matches_date ON matches (match_date);
CREATE INDEX IF NOT EXISTS idx_matches_season ON matches (season_id);
CREATE INDEX IF NOT EXISTS idx_matches_venue ON matches (venue_id);
CREATE INDEX IF NOT EXISTS idx_innings_match ON innings (match_id);
CREATE INDEX IF NOT EXISTS idx_batting_player ON batting_innings (player_id);
CREATE INDEX IF NOT EXISTS idx_bowling_player ON bowling_spells (player_id);
CREATE INDEX IF NOT EXISTS idx_fielding_player ON fielding_events (player_id);
CREATE INDEX IF NOT EXISTS idx_wk_player ON wicketkeeping_events (player_id);
CREATE INDEX IF NOT EXISTS idx_derived_features_player ON derived_features (player_id);
CREATE INDEX IF NOT EXISTS idx_derived_features_group ON derived_features (feature_group);

COMMIT;
