# BRIEFING — 2026-11-11T03:33:00Z

## Mission
Survey and mine specifications for Domestic & Age-group Source Inventory, Data Dictionary Enhancements, and Phase 4B Implementation Roadmap (Requirements R3, R4, R5) for IPL_Team documentation revision to v2.2.0.

## 🔒 My Identity
- Archetype: Specification Miner
- Roles: Domestic Sources & Roadmap Miner
- Working directory: d:\New folder (2)
- State folder: d:\New folder (2)\.agents\teamwork\explorer_3
- Original parent: 9375951d-5885-4950-843a-c0fc3e12a05a
- Milestone: v2.2.0 Survey / Mining Phase

## 🔒 Key Constraints
- Strictly documentation and architectural specification; Phase 4B status remains PLANNED.
- Real sources for domestic (Ranji, SMAT, Vijay Hazare, Duleep) and age-group (Cooch Behar, Vinoo Mankad, C.K. Nayudu, Vijay Merchant, U-19).
- Distinguish scorecard availability vs ball-by-ball availability, seasons, licensing, access constraints (never assume official portal provides downloadable bulk dataset).
- Define source conflict handling, fallback behavior, unverified/restricted source marking.
- Data dictionary enhancements for recent-form, coverage states, replacement comparison outputs, role-specific metrics, missing data handling, preserving existing corrected formulas.
- Phase 4B Roadmap: position in PHASES.md as PLANNED, dependencies on Phase 0B, 2, 3, 4, Eligibility Policy Service. Mode A consumes Phase 5, 6 when available. Phase 7 and 8 depend on PVRE.
- Detail 12 checkpoints and 10 explicit test scenarios.
- Do NOT implement code — read-only specification miner.
- Self-contained handoff.md at d:\New folder (2)\.agents\teamwork\explorer_3\handoff.md.

## Current Parent
- Conversation ID: 9375951d-5885-4950-843a-c0fc3e12a05a
- Updated: 2026-11-11T03:33:00Z

## Task Summary
- **What to build**: Survey report and comprehensive specification document for R3, R4, R5.
- **Success criteria**: Detailed source catalog with BBB vs scorecard distinctions, licensing, fallback; complete data dictionary expansion; rigorous Phase 4B specification with 12 checkpoints, dependencies, and 10 test scenarios.
- **Interface contracts**: `docs/DATA_SOURCE_REGISTER.md`, `docs/DATA_DICTIONARY.md`, `docs/PHASES.md`
- **Code layout**: Documentation files in `docs/` and reports in `.agents/teamwork/explorer_3/`

## Key Decisions Made
- Confirmed empirical local dataset lake: 13 directories, 5,083 JSON files under ODC-By v1.0.
- Confirmed SMAT is the ONLY Indian domestic competition with local ball-by-ball JSON (695 files), with temporal gaps in 2017, 2020, and partial group stages in 2022-2024.
- Confirmed absence of Ranji, Vijay Hazare, Duleep, and all youth tournaments on Cricsheet; established fallback to official BCCI match scorecards via Service C.
- Confirmed `bcci.tv` does not provide bulk downloadable datasets and enforces anti-scraping terms; classified as `RESTRICTED / PER-CLAIM`.
- Structured complete source register matrix for Ranji (S18A), SMAT (S18B), VHT (S18C), Duleep (S18D), Cooch Behar (S18E), Vinoo Mankad (S18F), CK Nayudu (S18G), Vijay Merchant (S18H), ICC/ACC Youth (S19B), and ESPNcricinfo historical (S20B).
- Formulated time-decay weighted recent-form metrics (R01–R06), 4 career coverage states, 5 replaceability assessment signals, 5 SICE recommendation states, and 16 role-aware comparison dimensions (D01–D16).
- Preserved existing corrected formulas: B04 balls faced, W06 format-aware economy, W01 overs display, DNB distinction, 3-group phase model, and Super Over isolation.
- Positioned Phase 4B in `docs/PHASES.md` as `[STATUS: PLANNED - GREENFIELD BASELINE]`; detailed 12 checkpoints, 10 explicit test scenarios, and verified acyclicity.

## Artifact Index
- `d:\New folder (2)\.agents\teamwork\ORIGINAL_REQUEST.md` — User request & specification requirements
- `d:\New folder (2)\docs\DATA_SOURCE_REGISTER.md` — Existing data source register
- `d:\New folder (2)\docs\DATA_DICTIONARY.md` — Existing data dictionary
- `d:\New folder (2)\docs\PHASES.md` — Existing phases roadmap
- `d:\New folder (2)\.agents\teamwork\explorer_3\progress.md` — Liveness & progress tracking
- `d:\New folder (2)\.agents\teamwork\explorer_3\handoff.md` — Final handoff report
