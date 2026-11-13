-- ============================================================================
-- Rajasthan Royals (RR) Squad Intelligence & Team Composition Platform
-- Rollback Migration: 20261113000001_rls_policies.down.sql
-- Description: Reversibly drop all RLS policies, revoke grants, and disable
--              Row Level Security across all 33 base tables and 5 deliveries partitions.
-- ============================================================================

BEGIN;

-- Drop user_teams policies
DROP POLICY IF EXISTS user_teams_select ON user_teams;
DROP POLICY IF EXISTS user_teams_insert ON user_teams;
DROP POLICY IF EXISTS user_teams_update ON user_teams;
DROP POLICY IF EXISTS user_teams_delete ON user_teams;
DROP POLICY IF EXISTS authenticated_user_teams_crud ON user_teams;

-- Drop user_team_players policies
DROP POLICY IF EXISTS user_team_players_select ON user_team_players;
DROP POLICY IF EXISTS user_team_players_insert ON user_team_players;
DROP POLICY IF EXISTS user_team_players_update ON user_team_players;
DROP POLICY IF EXISTS user_team_players_delete ON user_team_players;
DROP POLICY IF EXISTS authenticated_user_team_players_crud ON user_team_players;

-- Drop generic policies and disable RLS across all 33 base tables + 5 delivery partitions
DO $$
DECLARE
    tbl text;
    all_tables text[] := ARRAY[
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
    FOREACH tbl IN ARRAY all_tables LOOP
        EXECUTE format('DROP POLICY IF EXISTS service_role_all ON %I;', tbl);
        EXECUTE format('DROP POLICY IF EXISTS authenticated_select ON %I;', tbl);
        EXECUTE format('DROP POLICY IF EXISTS anon_select ON %I;', tbl);
        EXECUTE format('ALTER TABLE %I DISABLE ROW LEVEL SECURITY;', tbl);
    END LOOP;
END $$;

-- Revoke parent table grant
REVOKE SELECT ON deliveries FROM anon, authenticated;

COMMIT;
