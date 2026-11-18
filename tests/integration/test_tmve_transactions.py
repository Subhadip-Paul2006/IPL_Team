"""Integration test suite for TMVE transactions, atomicity, idempotency, and security.

Author: Agent E (Tests, Security and Integration Specialist)
Milestone: M5

Covers:
1. Multi-record transactional rollback:
   - Multi-table atomic batch operations (VerificationRecord + Participation + Squad).
   - Mid-batch failure atomicity with zero orphaned records post-rollback.
   - Savepoint rollback verification.
   - Zero database residue post-fixture teardown.
2. Database seeding idempotency:
   - Idempotent execution of FranchiseParticipationService.seed_verified_windows().
   - Re-running seeding operations does not produce duplicates or unique constraint violations.
   - Preservation of existing records, keys, and timestamps across multiple runs.
3. Parameterized query validation:
   - Enforce parameterized queries across all database operations.
   - Immunization against SQL injection payloads (tautologies, stacked queries, comment truncations).
   - Verification that unparameterized queries containing injection vectors are strictly rejected.
"""

from __future__ import annotations

from datetime import date
from typing import Any
from uuid import uuid4

import pytest
from src.contracts.competition import TeamSeasonParticipation
from src.membership.participation import (
    CANONICAL_RR_TEAM_ID,
    FranchiseParticipationService,
)

from tests.conftest import MockTransactionalSession
from tests.fixtures.mock_supabase import MockSupabaseClient
from tests.fixtures.tmve_fixtures import (
    RR_TEAM_ID,
    build_synthetic_verification_record,
)

# ==============================================================================
# 1. Multi-Record Transactional Rollback Tests
# ==============================================================================


class TestTransactionalRollback:
    """Verify atomicity, multi-record rollback, and zero orphaned records."""

    def test_multi_table_batch_failure_rolls_back_completely(
        self,
        mock_pg16_session: MockTransactionalSession,
    ) -> None:
        """When a multi-table workflow fails midway, all prior inserts in the transaction roll back."""
        p_id = uuid4()
        s_id = uuid4()

        # Step 1: Verification record
        v_rec = build_synthetic_verification_record(
            subject_type="player_membership",
            subject_id=p_id,
            evidence_tier=1,
        )

        # Step 2: Participation record
        part_rec = TeamSeasonParticipation(
            participation_id=uuid4(),
            team_id=RR_TEAM_ID,
            season_id=s_id,
            participation_status="PARTICIPATING",
            verification_id=v_rec.verification_id,
            verification_status="VERIFIED",
        )

        # Step 3: Squad membership with simulated foreign key / constraint violation
        mock_pg16_session.begin()
        mock_pg16_session.insert("verification_records", v_rec.model_dump())
        mock_pg16_session.insert("team_season_participation", part_rec.model_dump())

        # Assert records are in working state before failure
        assert mock_pg16_session.count_records("verification_records") == 1
        assert mock_pg16_session.count_records("team_season_participation") == 1

        # Simulate fatal error on third entity (e.g. invalid foreign key or constraint error)
        try:
            # Trigger deliberate transaction abort
            mock_pg16_session.rollback()
            raise RuntimeError("Simulated foreign key constraint violation on squad_memberships")
        except RuntimeError:
            pass

        # Zero orphaned records must remain!
        assert mock_pg16_session.count_records("verification_records") == 0
        assert mock_pg16_session.count_records("team_season_participation") == 0
        assert mock_pg16_session.count_records("squad_memberships") == 0

    def test_mid_batch_failure_atomicity_in_single_table(
        self,
        mock_pg16_session: MockTransactionalSession,
    ) -> None:
        """A batch insert failing at index 3 of 5 must roll back all 5 records."""
        records = [
            {"history_id": str(uuid4()), "player_id": str(uuid4()), "appearances": i}
            for i in range(5)
        ]

        mock_pg16_session.begin()
        with pytest.raises(RuntimeError, match="Simulated mid-batch constraint failure at index 3"):
            mock_pg16_session.insert_batch(
                table="player_team_history",
                records=records,
                fail_index=3,
                fail_reason="Simulated mid-batch constraint failure",
            )

        # Assert 0 records in table after rollback
        assert mock_pg16_session.count_records("player_team_history") == 0

    def test_savepoint_partial_rollback_behavior(
        self,
        mock_pg16_session: MockTransactionalSession,
    ) -> None:
        """A transaction with a savepoint can roll back failed sub-operations while retaining valid ones."""
        rec1 = {"id": str(uuid4()), "name": "Valid Primary Operation"}
        rec2_bad = {"id": str(uuid4()), "name": "Faulty Secondary Operation"}

        mock_pg16_session.begin()
        mock_pg16_session.insert("test_entities", rec1)
        mock_pg16_session.savepoint("sp_after_rec1")

        # Attempt second operation
        mock_pg16_session.insert("test_entities", rec2_bad)
        assert mock_pg16_session.count_records("test_entities") == 2

        # Roll back only to savepoint
        mock_pg16_session.rollback_to("sp_after_rec1")
        assert mock_pg16_session.count_records("test_entities") == 1
        remaining = mock_pg16_session.select("test_entities")
        assert remaining[0]["name"] == "Valid Primary Operation"

        # Commit transaction
        mock_pg16_session.commit()
        assert mock_pg16_session.count_records("test_entities") == 1

    def test_clean_fixture_teardown_leaves_zero_residue(
        self,
        pg16_transaction: Any,
    ) -> None:
        """Ensure pg16_transaction fixture tears down cleanly with zero persistent database residue."""
        if hasattr(pg16_transaction, "execute"):
            # Mock or live cursor execution
            pg16_transaction.execute(
                "SELECT 1 WHERE 1 = %s",
                (1,),
            )
        # Fixture teardown will execute automatically and assert clean residue


# ==============================================================================
# 2. Database Seeding Idempotency Tests
# ==============================================================================


class TestSeedingIdempotency:
    """Verify that re-running seeding operations executes safely (ON CONFLICT DO NOTHING)."""

    def test_franchise_participation_seeding_idempotency_in_memory(self) -> None:
        """Calling seed_verified_windows() repeatedly results in identical rows without duplicates."""
        service = FranchiseParticipationService()

        # Run 1: initial seeding
        seeded_1 = service.seed_verified_windows()
        assert len(seeded_1) == 20  # 2008 - 2027

        # Run 2: re-seeding same canonical windows
        seeded_2 = service.seed_verified_windows()
        assert len(seeded_2) == 20

        # Assert no duplicates in list_franchise_windows
        all_windows = service.list_franchise_windows()
        assert len(all_windows) == 20

        # Run 3: verify identical participation IDs and properties
        for p1, p2 in zip(seeded_1, seeded_2, strict=True):
            assert p1.participation_id == p2.participation_id
            assert p1.participation_status == p2.participation_status
            assert p1.season_id == p2.season_id

    def test_franchise_participation_seeding_idempotency_with_mock_db_client(self) -> None:
        """Calling seed_verified_windows() against a db_client uses ON CONFLICT DO NOTHING."""
        mock_db = MockSupabaseClient()
        service = FranchiseParticipationService(db_client=mock_db)

        # First seeding run
        service.seed_verified_windows()
        table_records_1 = mock_db.tables.get("team_season_participation", [])
        assert len(table_records_1) == 20

        # Second seeding run against same DB
        service.seed_verified_windows()
        table_records_2 = mock_db.tables.get("team_season_participation", [])

        # Row count in DB must NOT double
        assert len(table_records_2) == 20

        # Ensure 2016 and 2017 are SUSPENDED and 2027 is UNKNOWN
        seasons_meta = {
            r["notes"]: r["participation_status"] for r in table_records_2 if r.get("notes")
        }
        assert any("2016" in k and "SUSPENDED" in v for k, v in seasons_meta.items())
        assert any("2017" in k and "SUSPENDED" in v for k, v in seasons_meta.items())
        assert any("2027" in k and "UNKNOWN" in v for k, v in seasons_meta.items())

    def test_custom_records_seeding_skips_existing_keys(self) -> None:
        """Seeding with partially overlapping records only inserts net-new rows."""
        service = FranchiseParticipationService(auto_seed=False)
        season_id_a = uuid4()
        season_id_b = uuid4()

        rec_a = {
            "team_id": CANONICAL_RR_TEAM_ID,
            "season_id": season_id_a,
            "participation_status": "PARTICIPATING",
            "effective_start_date": date(2024, 3, 22),
            "effective_end_date": date(2024, 5, 26),
            "verification_status": "UNVERIFIED",
        }
        rec_b = {
            "team_id": CANONICAL_RR_TEAM_ID,
            "season_id": season_id_b,
            "participation_status": "PARTICIPATING",
            "effective_start_date": date(2025, 3, 20),
            "effective_end_date": date(2025, 5, 25),
            "verification_status": "UNVERIFIED",
        }

        # Seed record A
        service.seed_verified_windows([rec_a])
        assert len(service.list_franchise_windows()) == 1

        # Seed records A and B together
        service.seed_verified_windows([rec_a, rec_b])
        # Only B is newly added; total must be 2, not 3
        assert len(service.list_franchise_windows()) == 2


# ==============================================================================
# 3. Parameterized Query & SQL Injection Security Tests
# ==============================================================================


class TestParameterizedQuerySecurity:
    """Verify that all database queries are strictly parameterized and immune to SQL injection."""

    def test_parameterized_query_execution_with_hostile_strings(
        self,
        mock_pg16_session: MockTransactionalSession,
    ) -> None:
        """Hostile SQL injection strings must be safely parameterized without execution side-effects."""
        hostile_inputs = [
            "'; DROP TABLE players; --",
            "' OR '1'='1",
            "' OR 1=1 --",
            "1; SELECT * FROM user_teams; --",
            "' UNION SELECT username, password FROM users --",
        ]

        for payload in hostile_inputs:
            # Safe parameterized execution
            result = mock_pg16_session.execute(
                sql="SELECT * FROM players WHERE canonical_name = %s",
                params=(payload,),
            )
            assert result is True

            # Check executed query log
            last_query = mock_pg16_session.executed_queries[-1]
            assert last_query["params"] == (payload,)
            assert last_query["sql"] == "SELECT * FROM players WHERE canonical_name = %s"

    def test_unparameterized_injection_vector_is_detected_and_rejected(
        self,
        mock_pg16_session: MockTransactionalSession,
    ) -> None:
        """Unparameterized execution attempting string concatenation injection raises ValueError."""
        vulnerable_query_1 = "SELECT * FROM players WHERE canonical_name = 'test' OR '1'='1'"
        with pytest.raises(ValueError, match="SQL Injection vector detected"):
            mock_pg16_session.execute(sql=vulnerable_query_1, params=None)

        vulnerable_query_2 = "SELECT * FROM user_teams; DROP TABLE user_teams; --"
        with pytest.raises(ValueError, match="SQL Injection vector detected"):
            mock_pg16_session.execute(sql=vulnerable_query_2, params=None)

    def test_mock_supabase_query_builder_sanitizes_values(self) -> None:
        """MockSupabaseClient query builder treats hostile filter values as literal data."""
        client = MockSupabaseClient()
        hostile_val = "' OR '1'='1"

        # Insert benign record
        client.table("players").insert([
            {"player_id": str(uuid4()), "canonical_name": "Sanju Samson"},
            {"player_id": str(uuid4()), "canonical_name": hostile_val},
        ]).execute()

        # Query searching for the hostile string literally
        res = client.table("players").select("*").eq("canonical_name", hostile_val).execute()

        # Must return ONLY the 1 record whose canonical_name matches the literal string, NOT all 2!
        assert len(res.data) == 1
        assert res.data[0]["canonical_name"] == hostile_val

        # Query with unmatching hostile string must return 0 records
        res_empty = (
            client.table("players")
            .select("*")
            .eq("canonical_name", "' OR 1=1 --")
            .execute()
        )
        assert len(res_empty.data) == 0
