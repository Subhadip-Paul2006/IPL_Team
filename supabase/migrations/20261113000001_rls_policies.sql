-- ============================================================================
-- Rajasthan Royals (RR) Squad Intelligence & Team Composition Platform
-- Migration: 20261113000001_rls_policies.sql
-- Description: Comprehensive Row Level Security (RLS) policies for all 33 entities
--              plus deliveries child partitions. Enforces strict tenant isolation on
--              user_teams & user_team_players, protects proprietary derived_features,
--              restricts anonymous match access to verified matches, locks down
--              child partitions against shadow bypass, and grants public scorecard
--              read access to fielding and wicketkeeping events.
-- Roles: anon (read-only public scorecards & verified matches),
--        authenticated (analytical read + strict user team CRUD),
--        service_role (full administrative & data ingestion pipeline access)
-- ============================================================================

BEGIN;

-- ----------------------------------------------------------------------------
-- 1. ENABLE ROW LEVEL SECURITY ON ALL 33 TABLES AND DELIVERIES PARTITIONS
-- ----------------------------------------------------------------------------

ALTER TABLE data_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE venues ENABLE ROW LEVEL SECURITY;
ALTER TABLE competitions ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_teams ENABLE ROW LEVEL SECURITY;
ALTER TABLE players ENABLE ROW LEVEL SECURITY;
ALTER TABLE source_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE player_aliases ENABLE ROW LEVEL SECURITY;
ALTER TABLE teams ENABLE ROW LEVEL SECURITY;
ALTER TABLE seasons ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_team_players ENABLE ROW LEVEL SECURITY;
ALTER TABLE verification_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE matches ENABLE ROW LEVEL SECURITY;
ALTER TABLE player_injuries ENABLE ROW LEVEL SECURITY;
ALTER TABLE player_availability ENABLE ROW LEVEL SECURITY;
ALTER TABLE player_competition_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE derived_features ENABLE ROW LEVEL SECURITY;
ALTER TABLE team_season_participation ENABLE ROW LEVEL SECURITY;
ALTER TABLE squad_memberships ENABLE ROW LEVEL SECURITY;
ALTER TABLE player_team_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE innings ENABLE ROW LEVEL SECURITY;
ALTER TABLE player_awards ENABLE ROW LEVEL SECURITY;
ALTER TABLE pitch_conditions ENABLE ROW LEVEL SECURITY;
ALTER TABLE weather_conditions ENABLE ROW LEVEL SECURITY;
ALTER TABLE player_membership_state ENABLE ROW LEVEL SECURITY;
ALTER TABLE eligibility_policies ENABLE ROW LEVEL SECURITY;
ALTER TABLE deliveries ENABLE ROW LEVEL SECURITY;
ALTER TABLE batting_innings ENABLE ROW LEVEL SECURITY;
ALTER TABLE bowling_spells ENABLE ROW LEVEL SECURITY;
ALTER TABLE wicketkeeping_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE player_eligibility ENABLE ROW LEVEL SECURITY;
ALTER TABLE ranking_configurations ENABLE ROW LEVEL SECURITY;
ALTER TABLE fielding_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE ranking_runs ENABLE ROW LEVEL SECURITY;

-- SEC-05: Explicit RLS enablement on all five delivery partitions (Defense-in-depth)
ALTER TABLE deliveries_y2008_2015 ENABLE ROW LEVEL SECURITY;
ALTER TABLE deliveries_y2016_2020 ENABLE ROW LEVEL SECURITY;
ALTER TABLE deliveries_y2021_2023 ENABLE ROW LEVEL SECURITY;
ALTER TABLE deliveries_y2024_2027 ENABLE ROW LEVEL SECURITY;
ALTER TABLE deliveries_default ENABLE ROW LEVEL SECURITY;

-- SEC-05: Revoke direct public/anon/authenticated access on child partitions
REVOKE ALL ON deliveries_y2008_2015, deliveries_y2016_2020, deliveries_y2021_2023, deliveries_y2024_2027, deliveries_default FROM PUBLIC, anon, authenticated;

-- Ensure client roles can query parent table deliveries
GRANT SELECT ON deliveries TO anon, authenticated;

-- ----------------------------------------------------------------------------
-- 2. SERVICE ROLE: UNRESTRICTED ACCESS FOR DATA INGESTION & PIPELINE ENGINE
-- ----------------------------------------------------------------------------

DO $$
DECLARE
    tbl text;
    tables text[] := ARRAY[
        'data_sources', 'venues', 'competitions', 'user_teams', 'players',
        'source_records', 'player_aliases', 'teams', 'seasons', 'user_team_players',
        'verification_records', 'matches', 'player_injuries', 'player_availability',
        'player_competition_history', 'derived_features', 'team_season_participation',
        'squad_memberships', 'player_team_history', 'innings', 'player_awards',
        'pitch_conditions', 'weather_conditions', 'player_membership_state',
        'eligibility_policies', 'deliveries', 'deliveries_y2008_2015', 'deliveries_y2016_2020',
        'deliveries_y2021_2023', 'deliveries_y2024_2027', 'deliveries_default',
        'batting_innings', 'bowling_spells', 'wicketkeeping_events', 'player_eligibility',
        'ranking_configurations', 'fielding_events', 'ranking_runs'
    ];
BEGIN
    FOREACH tbl IN ARRAY tables LOOP
        EXECUTE format('
            DROP POLICY IF EXISTS service_role_all ON %I;
            CREATE POLICY service_role_all ON %I
                FOR ALL
                TO service_role
                USING (true)
                WITH CHECK (true);
        ', tbl, tbl);
    END LOOP;
END $$;

-- ----------------------------------------------------------------------------
-- 3. AUTHENTICATED USERS: ANALYTICAL READ & STRICT TENANT-ISOLATED CRUD
-- ----------------------------------------------------------------------------

DO $$
DECLARE
    tbl text;
    read_tables text[] := ARRAY[
        'data_sources', 'venues', 'competitions', 'players', 'player_aliases',
        'teams', 'seasons', 'verification_records', 'matches', 'player_injuries',
        'player_availability', 'player_competition_history', 'derived_features',
        'team_season_participation', 'squad_memberships', 'player_team_history',
        'innings', 'player_awards', 'pitch_conditions', 'weather_conditions',
        'player_membership_state', 'eligibility_policies', 'deliveries',
        'batting_innings', 'bowling_spells', 'wicketkeeping_events', 'player_eligibility',
        'ranking_configurations', 'fielding_events', 'ranking_runs'
    ];
BEGIN
    FOREACH tbl IN ARRAY read_tables LOOP
        EXECUTE format('
            DROP POLICY IF EXISTS authenticated_select ON %I;
            CREATE POLICY authenticated_select ON %I
                FOR SELECT
                TO authenticated
                USING (true);
        ', tbl, tbl);
    END LOOP;
END $$;

-- SEC-01: User Teams Tenant Isolation
DROP POLICY IF EXISTS authenticated_user_teams_crud ON user_teams;
DROP POLICY IF EXISTS user_teams_select ON user_teams;
DROP POLICY IF EXISTS user_teams_insert ON user_teams;
DROP POLICY IF EXISTS user_teams_update ON user_teams;
DROP POLICY IF EXISTS user_teams_delete ON user_teams;

CREATE POLICY user_teams_select ON user_teams
    FOR SELECT
    TO authenticated
    USING (created_by = (SELECT auth.uid()::text));

CREATE POLICY user_teams_insert ON user_teams
    FOR INSERT
    TO authenticated
    WITH CHECK (created_by = (SELECT auth.uid()::text));

CREATE POLICY user_teams_update ON user_teams
    FOR UPDATE
    TO authenticated
    USING (created_by = (SELECT auth.uid()::text))
    WITH CHECK (created_by = (SELECT auth.uid()::text));

CREATE POLICY user_teams_delete ON user_teams
    FOR DELETE
    TO authenticated
    USING (created_by = (SELECT auth.uid()::text));

-- SEC-02: User Team Players Derived Ownership
DROP POLICY IF EXISTS authenticated_user_team_players_crud ON user_team_players;
DROP POLICY IF EXISTS user_team_players_select ON user_team_players;
DROP POLICY IF EXISTS user_team_players_insert ON user_team_players;
DROP POLICY IF EXISTS user_team_players_update ON user_team_players;
DROP POLICY IF EXISTS user_team_players_delete ON user_team_players;

CREATE POLICY user_team_players_select ON user_team_players
    FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM user_teams
            WHERE user_teams.team_id = user_team_players.user_team_id
              AND user_teams.created_by = (SELECT auth.uid()::text)
        )
    );

CREATE POLICY user_team_players_insert ON user_team_players
    FOR INSERT
    TO authenticated
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM user_teams
            WHERE user_teams.team_id = user_team_players.user_team_id
              AND user_teams.created_by = (SELECT auth.uid()::text)
        )
    );

CREATE POLICY user_team_players_update ON user_team_players
    FOR UPDATE
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM user_teams
            WHERE user_teams.team_id = user_team_players.user_team_id
              AND user_teams.created_by = (SELECT auth.uid()::text)
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM user_teams
            WHERE user_teams.team_id = user_team_players.user_team_id
              AND user_teams.created_by = (SELECT auth.uid()::text)
        )
    );

CREATE POLICY user_team_players_delete ON user_team_players
    FOR DELETE
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM user_teams
            WHERE user_teams.team_id = user_team_players.user_team_id
              AND user_teams.created_by = (SELECT auth.uid()::text)
        )
    );

-- ----------------------------------------------------------------------------
-- 4. ANONYMOUS USERS: PUBLIC SCORECARD & TOURNAMENT VIEW ONLY
--    (Proprietary derived_features, unverified matches, and child partitions excluded)
-- ----------------------------------------------------------------------------

-- SEC-03: derived_features excluded from public_tables (default-deny for anon)
-- SEC-05: Child partitions excluded from public_tables (default-deny for anon)
-- SEC-06: fielding_events and wicketkeeping_events included for public scorecards
DO $$
DECLARE
    tbl text;
    public_tables text[] := ARRAY[
        'venues', 'competitions', 'teams', 'seasons', 'players',
        'innings', 'deliveries',
        'batting_innings', 'bowling_spells', 'fielding_events', 'wicketkeeping_events'
    ];
BEGIN
    FOREACH tbl IN ARRAY public_tables LOOP
        EXECUTE format('
            DROP POLICY IF EXISTS anon_select ON %I;
            CREATE POLICY anon_select ON %I
                FOR SELECT
                TO anon
                USING (true);
        ', tbl, tbl);
    END LOOP;
END $$;

-- SEC-04: matches restricted to completed/verified status for anon
DROP POLICY IF EXISTS anon_select ON matches;
CREATE POLICY anon_select ON matches
    FOR SELECT
    TO anon
    USING (status IN ('Completed', 'Abandoned', 'No Result'));

COMMIT;
