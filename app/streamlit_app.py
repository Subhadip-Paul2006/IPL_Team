"""Streamlit entry point: ``streamlit run app/streamlit_app.py``."""

from __future__ import annotations

import contextlib
from typing import Any, cast


def _load_services() -> dict[str, Any]:
    """Create cached backend services without coupling engine modules to Streamlit."""
    from src.config.settings import get_settings
    from src.database.client import SupabaseClientFactory
    from src.mie import MotherIntelligenceEngine
    from src.mie.evidence_repository import SupabaseEvidenceRepository

    settings = get_settings()
    evidence_repository = None
    if settings.mie_evidence_persistence_enabled:
        client = SupabaseClientFactory(settings).create_client_service()
        evidence_repository = SupabaseEvidenceRepository(client)
    mie = MotherIntelligenceEngine(evidence_repository=evidence_repository)
    return {
        "mie": mie,
        "sice": mie.sice.sice,
        "team_builder": mie.sice.team_builder,
    }


def main() -> None:
    """Start the Streamlit application with lazy framework loading."""
    import streamlit as st

    with contextlib.suppress(Exception):
        st.set_page_config(
            page_title="Rajasthan Royals Squad Intelligence",
            page_icon="🏏",
            layout="wide",
            initial_sidebar_state="expanded",
        )

    if "_mie_services" not in st.session_state:
        st.session_state["_mie_services"] = _load_services()
    services = st.session_state["_mie_services"]
    from app.streamlit.views import UI, run_app

    run_app(cast(UI, st), services)


if __name__ == "__main__":
    main()
