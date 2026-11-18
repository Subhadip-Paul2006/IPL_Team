-- ============================================================================
-- Rollback Migration: 20261113000000_initial_schema.down.sql
-- Description: Clean reversal of all 33 entities and partitions in reverse DAG order
-- ============================================================================

BEGIN;

-- Drop Level 5
DROP TABLE IF EXISTS ranking_runs CASCADE;
DROP TABLE IF EXISTS fielding_events CASCADE;

-- Drop Level 4
DROP TABLE IF EXISTS ranking_configurations CASCADE;
DROP TABLE IF EXISTS player_eligibility CASCADE;
DROP TABLE IF EXISTS wicketkeeping_events CASCADE;
DROP TABLE IF EXISTS bowling_spells CASCADE;
DROP TABLE IF EXISTS batting_innings CASCADE;

-- Drop deliveries and child partitions
DROP TABLE IF EXISTS deliveries_default CASCADE;
DROP TABLE IF EXISTS deliveries_y2024_2027 CASCADE;
DROP TABLE IF EXISTS deliveries_y2021_2023 CASCADE;
DROP TABLE IF EXISTS deliveries_y2016_2020 CASCADE;
DROP TABLE IF EXISTS deliveries_y2008_2015 CASCADE;
DROP TABLE IF EXISTS deliveries CASCADE;

-- Drop Level 3
DROP TABLE IF EXISTS eligibility_policies CASCADE;
DROP TABLE IF EXISTS player_membership_state CASCADE;
DROP TABLE IF EXISTS weather_conditions CASCADE;
DROP TABLE IF EXISTS pitch_conditions CASCADE;
DROP TABLE IF EXISTS player_awards CASCADE;
DROP TABLE IF EXISTS innings CASCADE;
DROP TABLE IF EXISTS player_team_history CASCADE;
DROP TABLE IF EXISTS squad_memberships CASCADE;
DROP TABLE IF EXISTS team_season_participation CASCADE;

-- Drop Level 2
DROP TABLE IF EXISTS derived_features CASCADE;
DROP TABLE IF EXISTS player_competition_history CASCADE;
DROP TABLE IF EXISTS player_availability CASCADE;
DROP TABLE IF EXISTS player_injuries CASCADE;
DROP TABLE IF EXISTS matches CASCADE;
DROP TABLE IF EXISTS verification_records CASCADE;

-- Drop Level 1
DROP TABLE IF EXISTS user_team_players CASCADE;
DROP TABLE IF EXISTS seasons CASCADE;
DROP TABLE IF EXISTS teams CASCADE;
DROP TABLE IF EXISTS player_aliases CASCADE;
DROP TABLE IF EXISTS source_records CASCADE;

-- Drop Level 0
DROP TABLE IF EXISTS players CASCADE;
DROP TABLE IF EXISTS user_teams CASCADE;
DROP TABLE IF EXISTS competitions CASCADE;
DROP TABLE IF EXISTS venues CASCADE;
DROP TABLE IF EXISTS data_sources CASCADE;

COMMIT;
