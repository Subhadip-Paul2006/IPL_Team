# ARCHITECTURE & SPECIFICATION MINING HANDOFF REPORT: PVRE (ENGINE 07)
**Milestone**: Survey Phase / Requirements R2 & R4 Mining  
**Agent**: `explorer_2` (Architecture & Spec Miner)  
**Target Repository Version**: `v2.2.0-pvre-dual-mode`  
**Date**: 2026-11-11  

---

## 1. Observation

Direct observations extracted from the authoritative repository files (`ORIGINAL_REQUEST.md`, `README.md`, `PROJECT.md`, `docs/README.md`, `docs/PRD.md`, `docs/TRD.md`, `docs/ARCHITECTURE.md`, `docs/PHASES.md`, `docs/AGENTS.md`, `docs/AI_INSTRUCTIONS.md`, `docs/DATA_DICTIONARY.md`, `docs/DATA_SOURCE_REGISTER.md`, `docs/RANKING_SPEC.md`):

1. **Current Git Baseline & Revision State**:
   - `origin/main` commit: `eaebdcb` (Merge pull request #3: docs/v2.1.1-targeted-remediation).
   - Local working branch: `docs/v2.2.0-pvre-dual-mode` contains commit `a69b6d7` (*docs: introduce PVRE dual-mode research architecture v2.2.0*).
   - Inspection of commit `a69b6d7` shows initial drafting of Engine 07 (PVRE) across 13 files (+1,614 / -265 lines), but contains several critical specification gaps and cross-document inconsistencies against `ORIGINAL_REQUEST.md`.

2. **Orchestration Boundary Discrepancy**:
   - `ORIGINAL_REQUEST.md §R2.1` specifies:
     > *"MIE remains the sole cross-engine orchestrator. PVRE Mother Controller manages only PVRE's internal workflow routing, submodules, and retry/evidence logic; PVRE must not independently bypass MIE to orchestrate PIRE, TMVE, CDCRE, or the Eligibility Policy Service. Define explicit input/output contracts between MIE and PVRE. The Mother Controller must never infer that an unknown player is uncapped."*
   - In contrast, `docs/ARCHITECTURE.md` (lines 142–145) depicts:
     ```mermaid
     PVRE --> PIRE
     PVRE --> TMVE
     PVRE --> CDCRE
     PVRE --> SICE
     ```
   - Furthermore, `docs/ARCHITECTURE.md §2.2b` (lines 215–222) and `docs/TRD.md §9.1` (lines 670–683) describe the Mother Controller directly invoking `CDCRE.discover_candidates`, `PIRE.resolve`, `TMVE.verify`, and `EligibilityPolicyService.assess`. This constitutes an architectural boundary violation: PVRE is an engine specialist, not a substitute cross-engine orchestrator.

3. **Output Contract Incompleteness & Field Conflation**:
   - `ORIGINAL_REQUEST.md §R2.7` specifies 26 explicit response fields:
     > `contract_version`, `research_run_id`, `player_id`, `canonical_name`, `identity_status`, `research_mode`, `route_status`, `evaluation_date`, `target_season_id`, `rr_relationship_state`, `rr_current_state`, `player_capped_status`, `ipl_uncapped_eligibility`, `research_window_start`, `research_window_end`, `career_coverage_state`, `rr_historical_profile`, `recent_global_performance`, `complete_career_profile`, `replaceability_assessment`, `competition_coverage`, `source_record_ids`, `verification_record_ids`, `review_status`, `review_reason_codes`, `data_quality_summary`.
   - In contrast, `docs/TRD.md §9.6.2` (lines 889–934) and `docs/PHASES.md §7` (lines 256, 327) state `"23 Minimum Fields"`. Specifically:
     - `player_capped_status` and `ipl_uncapped_eligibility` were conflated into a single `eligibility_status: str`.
     - `career_coverage_state: str` was completely omitted (only `competition_coverage: Dict[str, str]` was present).

4. **Career Coverage State Taxonomy Missing**:
   - `ORIGINAL_REQUEST.md §R2.5` mandates four explicit career coverage states:
     `COMPLETE_WITHIN_VERIFIED_SOURCES`, `PARTIAL_COVERAGE`, `UNKNOWN`, and `REVIEW_REQUIRED`.
   - Inspection of `docs/DATA_DICTIONARY.md` (line 82–313) revealed zero entries for `COMPLETE_WITHIN_VERIFIED_SOURCES` or `career_coverage_state`. The existing dictionary only had CDCRE competition-level coverage states (`VERIFIED_PARTICIPATION`, `DATASET_COVERAGE_UNAVAILABLE`, etc.), leaving top-level career coverage undefined.

5. **Count Governance Inconsistencies**:
   - `ORIGINAL_REQUEST.md §R4` mandates reporting:
     - Engine count: exactly 7 specialized engines (01 PIRE, 02 TMVE, 03 CDCRE, 04 CPPAE, 05 CMIE, 06 SICE, 07 PVRE).
     - Support service count: exactly 5 support services (Service A: Data Ingestion, Service B: Profile Generator, Service C: Source Verification & Provenance, Service D: Data Quality & Coverage, Service E: Team Builder).
     - Agent count: exactly 18 agents including `agent_pvre`.
   - However, in `README.md` (lines 185, 206) and `docs/README.md` (lines 79, 98, 113), the documentation text erroneously claims `"6 support services"` or `"6 services"`.

6. **Phase Dependencies in PHASES.md**:
   - In `docs/PHASES.md`, Phase 7 (MIE, line 413) states `- Depends on: Phases 3, 4, 5, 6.` omitting Phase 4B.
   - Phase 8 (SICE, line 433) states `- Depends on: Phases 5, 7.` omitting explicit Phase 4B dependency.

---

## 2. Logic Chain

1. **Premise**: MIE is established in `docs/TRD.md §2` and `docs/ARCHITECTURE.md §2.1` as the sole top-level coordinator of the platform.
2. **Inference**: Allowing PVRE Mother Controller to invoke PIRE, TMVE, CDCRE, and Eligibility Policy Service creates circular cross-engine calls and breaks the single-responsibility principle of MIE.
3. **Resolution**: The Mother Controller is an *internal workflow router* within Engine 07. MIE collects preliminary facts (resolved identity from PIRE/CDCRE, RR membership from TMVE, IPL eligibility from Eligibility Policy Service), packages them into `PVRERequestContract`, and invokes `PVRE.execute(...)`. Inside Engine 07, the Mother Controller routes execution to Module A1/A2/A3 (Mode A), Mode B domestic career extractors, or the REVIEW_REQUIRED safety interceptor.

4. **Premise**: Cricketing capped status is ICC-jurisdiction global fact, whereas IPL uncapped eligibility is tournament-specific regulatory rule.
5. **Inference**: An international player may be technically eligible under historical exemption rules (e.g., 5-year retirement rule), while a domestic uncapped player may be ineligible due to age, lack of state association NOC, or disciplinary sanction.
6. **Resolution**: PVRE must maintain two distinct, independently verified fields: `player_capped_status` (`CAPPED`, `UNCAPPED`, `UNVERIFIED`) and `ipl_uncapped_eligibility` (`VERIFIED_ELIGIBLE`, `VERIFIED_NOT_ELIGIBLE`, `ELIGIBILITY_UNVERIFIED`, `NOT_ASSESSED`).

7. **Premise**: Data availability for Indian domestic cricket is asymmetric (e.g., ball-by-ball SMAT archive is missing from the local baseline while scorecards exist).
8. **Inference**: If a system claims "complete career" based only on available files, it produces biased evaluations. Conversely, if missing files are treated as zero appearances, active players are mischaracterized.
9. **Resolution**: Career coverage must be formalized with 4 explicit states: `COMPLETE_WITHIN_VERIFIED_SOURCES`, `PARTIAL_COVERAGE`, `UNKNOWN`, and `REVIEW_REQUIRED`. Missing SMAT records must be prominently surfaced.

10. **Premise**: SICE performs holistic squad evaluation, while the hackathon deliverable requires an auditable Top-10 youngest uncapped candidate ranking.
11. **Inference**: Merging replacement trade-offs with the Top-10 ranking formula contaminates the benchmark and compromises reproducibility.
12. **Resolution**: SICE executes two independent workflows frozen in `ranking_runs`: `run_type = 'HACKATHON_TOP10'` (`RK-1.0.0`) and `run_type = 'REPLACEMENT_EVALUATION'` (`RE-1.0.0`). Mode A replacement assessments evaluate 16 role dimensions and output 5 analytical recommendation states without modifying the Top-10 leaderboard.

---

## 3. Caveats

1. **Read-Only / Greenfield Scope**: This investigation is strictly architectural and specification mining. No application code, database migrations, or live API integrations have been implemented. Phase 4B remains `[STATUS: PLANNED - GREENFIELD BASELINE]`.
2. **Local Data Availability**: While `datasets/sma_json/` exists as an untracked directory in the workspace (695 files), official BCCI scorecards for multi-day tournaments (Ranji, Cooch Behar, CK Nayudu) remain external restricted sources requiring per-claim verification records.
3. **Mermaid Parser Limitation**: Live Mermaid CLI validation is unavailable in the environment; visual syntax has been structurally audited against GitHub-compatible fence rules.

---

## 4. Conclusion & Core Specifications (Areas a–j)

### a) Orchestration Boundary & Mother Controller
- **Sole Cross-Engine Orchestrator**: Mother Intelligence Engine (MIE, Engine 00 / Family 1). MIE exclusively handles cross-engine pipelines, user search requests, and service invocations.
- **Mother Controller Internal Scope**: The Mother Controller is the *internal* execution coordinator of Engine 07 (PVRE). It manages:
  1. Validation of the inbound `PVRERequestContract` received from MIE.
  2. Execution of the deterministic 7-step routing waterfall (§f).
  3. Internal dispatch to Submodules A1, A2, A3 (Mode A), Mode B domestic extractors, or the Safety Review Gateway.
  4. Internal retry management, evidence corroboration thresholds, and conflict tracking.
  5. Compilation and emission of the typed `PVREOutputContract` back to MIE.
- **Strict Boundary Prohibition**: PVRE Mother Controller NEVER directly invokes or bypasses MIE to orchestrate PIRE, TMVE, CDCRE, or the Eligibility Policy Service.
- **MIE-to-PVRE Input Contract**:
  ```python
  @dataclass(frozen=True)
  class PVRERequestContract:
      contract_version: str            # "PVRE-2.2.0"
      research_run_id: UUID            # Unique execution UUIDv4 generated by MIE
      player_query: str                # Raw name, alias, or known identifier
      player_id: Optional[UUID]        # Canonical ID resolved by PIRE (or None)
      canonical_name: str              # Canonical name from PIRE
      identity_status: str             # RESOLVED, PROVISIONAL, UNRESOLVED
      rr_relationship_state: str       # TMVE Dimension 1
      rr_current_state: str            # TMVE Dimension 2
      player_capped_status: str        # CAPPED, UNCAPPED, UNVERIFIED
      ipl_uncapped_eligibility: str    # Eligibility Policy Service Dimension 3
      target_season_id: UUID           # Target season UUID (e.g. IPL 2027)
      evaluation_date: date            # Reference date for window and age calculations
      research_window_years: int = 3   # Configurable recent window (2 or 3 years)
      force_refresh: bool = False      # Bypass cache for authorised external research
  ```
- **Mother Controller Invariant**: The Mother Controller **never infers that an unknown player is uncapped**. Absence from the database or external datasets is never proof of uncapped status or non-membership.

---

### b) Mode A (Existing RR Player Replacement Intelligence)
- **Eligibility Trigger**: Triggered when TMVE confirms `rr_relationship_state` $\in$ (`CURRENT_RR`, `HISTORICAL_RR_APPEARED`, `HISTORICAL_RR_SQUAD_ONLY`).
- **Module A1 (RR Historical Performance Research)**:
  - Investigates complete RR history across all evidenced seasons (2008–2015, 2018–2026; 2016–2017 recorded as `SUSPENDED`).
  - **Strict Appearance vs Squad Separation**: Match appearances are derived strictly from scorecards (`innings` and `matches` where `teams.team_code = 'RR'`). Squad inclusion without match appearances is recorded with `appearances = 0` (`HISTORICAL_RR_SQUAD_ONLY`) and zero batting/bowling statistics. Appearances are *never* inferred from squad lists.
  - **Multi-Discipline Profiles**: Complete season-by-season batting (runs, balls, B05 average, B10 strike rate, B08 boundary %, B09 dot %, phase splits), bowling (integer legal balls, W02 wickets, W06 average, W05 economy, W07 strike rate, W08 dot %, phase splits), fielding (catches, run outs, F04 dropped catches where recorded, F05 boundary saves where recorded), and wicketkeeping (dismissals, byes conceded).
  - **Tactical Evolution**: Batting order position distribution, bowling spell roles, and tactical usage trends across seasons.
- **Module A2 (Recent Global Performance Outside RR)**:
  - **Configurable Research Window**: Explicit window anchored to `evaluation_date` (default 3 years, configurable 2 to 3 years; `research_window_start = evaluation_date - window_years`, `research_window_end = evaluation_date`). Zero unexplained time windows.
  - **Recognised Competitions**: Other IPL franchises (`ipl_male_json`), BBL (`bbl_male_json`), PSL (`psl_male_json`), CPL (`cpl_male_json`), SA20 (`sat_male_json`), The Hundred (`hnd_male_json`, balls_per_over = 5), Senior International (Tests, ODIs, T20Is), Indian Domestic (Ranji Trophy, SMAT, Vijay Hazare Trophy), and other verified leagues (BPL, LPL, MLC, ILT20).
  - **Parameters**: Matches, innings, format-specific performance profiles with visible sample sizes (R06), recent form trajectory, multi-tournament consistency, calendar participation gaps (`GAP_SUSPECTED`, `GAP_VERIFIED_INJURY`, `GAP_NOT_SELECTED`), and verified injuries/availability (strictly from `player_injuries`/`player_availability` with `verified=TRUE`).
  - **Guardrail**: Missing datasets must never be interpreted as non-participation.
- **Module A3 (Replaceability Evidence Assessment)**:
  - Synthesises RR historical depth, recent 2–3 year global form, age trajectory at evaluation date (`evaluation_date - date_of_birth`), role scarcity in modern T20 cricket, benchmark metric deltas, sample adequacy, and verified availability.
  - **Five Structured Assessment Signal States**:
    1. `RETAIN_SIGNAL`: Sustained elite role-specific performance across historical RR appearances and recent global window; clear evidence against replacement.
    2. `MONITOR_SIGNAL`: Mixed recent form, minor sample gaps, or role shifts requiring continued tracking across domestic fixtures.
    3. `POTENTIALLY_REPLACEABLE`: Persistent form degradation over 2–3 years, reduced availability, diminishing returns in key phases, or advanced age relative to role demands.
    4. `INSUFFICIENT_EVIDENCE`: Evidentiary coverage within the 2–3 year evaluation window falls below minimum sample thresholds (<20 batting balls, <30 overs bowled, or unverified recent leagues).
    5. `REVIEW_REQUIRED`: Materially conflicting source data, unverified injuries, or contradictory membership/eligibility status.
  - **Non-Decision Rule**: Signals are analytical evidence vectors, not decisions. PVRE does not make release, retain, or auction decisions, and does not invent arbitrary replacement probabilities or scalar indices. Dossiers are forwarded to SICE for comparative squad evaluation.

---

### c) Mode B (Verified Uncapped Candidate Intelligence)
- **Eligibility Trigger**: Triggered when TMVE confirms `rr_relationship_state = 'NO_VERIFIED_RR_RELATIONSHIP'` AND Eligibility Policy Service confirms `ipl_uncapped_eligibility = 'VERIFIED_ELIGIBLE'`.
- **Career Discovery Workflow**:
  - Domestic competitions: Ranji Trophy (multi-day red ball), Syed Mushtaq Ali Trophy (SMAT, domestic T20 proving ground), Vijay Hazare Trophy (VHT, List A 50-over), Duleep Trophy.
  - Age-group tournaments: BCCI Vinoo Mankad Trophy (U19 one-day), Cooch Behar Trophy (U19 multi-day), Col C.K. Nayudu Trophy (U23 multi-day), Vijay Merchant Trophy (U16 multi-day), and ICC/BCCI U19 match archives.
  - Other authorised domestic and franchise leagues.
  - Senior international appearances: Any senior international appearance (Test, ODI, T20I) immediately disqualifies candidate from uncapped status.
- **Six-Class Data Lake Classification**:
  1. `INTERNAL_NEW`: Player present in internal DB but recently added/first assessed.
  2. `EXTERNAL_DISCOVERED`: Discovered through external sources, not yet ingested into core DB.
  3. `INCOMPLETE_LOCAL_COVERAGE`: Player present in local datasets but coverage has known gaps.
  4. `VERIFIED_UNCAPPED`: Affirmatively verified zero senior international caps and compliant with active target-season uncapped policy.
  5. `CAPPED`: Confirmed senior international appearance or capped status.
  6. `UNVERIFIED`: Ambiguous or uncorroborated status; strictly blocked from candidate pool.
- **Negative Proof Invariant**: Absence from the database is NEVER proof of uncapped status. No candidate enters the verified uncapped pool without affirmative verification.

---

### d) Distinction between `player_capped_status` and `ipl_uncapped_eligibility`

| Field | `player_capped_status` | `ipl_uncapped_eligibility` |
|---|---|---|
| **Definition** | Intrinsic cricketing status indicating whether a player has represented their senior national team in an ICC-recognised international match (Test, ODI, T20I). | Regulatory, season-bound eligibility determination under specific IPL tournament rules and auction guidelines for the target season. |
| **Authority** | ICC official records / verified match archives. | IPL Governing Council / BCCI Regulations for the active `target_season_id`. |
| **Allowed Values** | `CAPPED`, `UNCAPPED`, `UNVERIFIED` | `VERIFIED_ELIGIBLE`, `VERIFIED_NOT_ELIGIBLE`, `ELIGIBILITY_UNVERIFIED`, `NOT_ASSESSED` |
| **Temporal Scope** | Career-wide fact (once capped, always capped, unless historical regulatory classification applies). | Bound strictly to a specific season (e.g. IPL 2027 under policy `IPL-RULE-2025-01`). |
| **Key Distinctions** | - An overseas player may be `UNCAPPED` internationally, but subject to overseas squad limits or distinct eligibility rules.<br>- A former international player may be `CAPPED` internationally, but reclassified as uncapped under the BCCI 5-year retirement policy.<br>- A domestic player may be `UNCAPPED`, but `VERIFIED_NOT_ELIGIBLE` due to age restrictions, disciplinary suspensions, or missing state NOC. |

**Rule**: The system must NEVER assume that an uncapped player is automatically IPL-eligible, or that an IPL-eligible player is automatically uncapped. Both fields must be independently evaluated and cited.

---

### e) Strict Career Coverage Rules
- **Principle**: PVRE must never claim a player's complete career when source coverage is incomplete.
- **Four Explicit Career Coverage States (`career_coverage_state`)**:
  1. `COMPLETE_WITHIN_VERIFIED_SOURCES`: All targeted domestic, franchise, and international competitions within the research scope have verified ball-by-ball or scorecard datasets present and ingested.
  2. `PARTIAL_COVERAGE`: Core competitions are verified present, but known source gaps exist (e.g., SMAT ball-by-ball unavailable while scorecards exist; or specific seasons missing).
  3. `UNKNOWN`: Insufficient source coverage to determine the player's tournament participation history.
  4. `REVIEW_REQUIRED`: Source coverage records conflict, contradictory match ledgers exist, or data integrity anomalies prevent coverage determination.
- **Reporting Semantics**:
  - Missing SMAT or domestic tournament records must remain prominently visible in UI views and reports.
  - Coverage gaps must NEVER be treated as evidence of non-participation.
  - `competition_coverage` (mapping of competition codes to `VERIFIED`, `DATASET_UNAVAILABLE`, `NOT_ESTABLISHED`, `CONFIRMED_NON_PARTICIPATION`) is reported alongside `career_coverage_state`.

---

### f) Routing & Safety Logic (7-Step Precedence Waterfall & REVIEW_REQUIRED)
- **7-Step Deterministic Precedence Waterfall**:
  1. **Step 1 (Identity Resolution)**: PIRE resolves player identity. If identity resolution returns `UNRESOLVED` or multiple unresolved candidate matches $\rightarrow$ route to **`REVIEW_REQUIRED`**.
  2. **Step 2 (RR Relationship Verification)**: Inspect TMVE Dimension 1 (`rr_relationship_state`) and Dimension 2 (`rr_current_state`).
  3. **Step 3 (Mode A Trigger)**: If player has verified current or historical RR relationship (`CURRENT_RR`, `HISTORICAL_RR_APPEARED`, `HISTORICAL_RR_SQUAD_ONLY`) $\rightarrow$ route to **Mode A (Existing RR Player Replacement Intelligence)**.
  4. **Step 4 (Eligibility Assessment)**: If player has no verified RR relationship, inspect Dimension 3 (`ipl_uncapped_eligibility`) from Eligibility Policy Service.
  5. **Step 5 (Mode B Trigger)**: If player is independently verified as uncapped-eligible (`VERIFIED_ELIGIBLE`) under applicable target-season policy $\rightarrow$ route to **Mode B (Verified Uncapped Candidate Intelligence)**.
  6. **Step 6 (Safety Fallback)**: If identity, RR relationship, or eligibility evidence is incomplete, unverified (`ELIGIBILITY_UNVERIFIED`, `NOT_ASSESSED`, `RR_RELATIONSHIP_UNKNOWN`), or contradictory $\rightarrow$ route to **`REVIEW_REQUIRED`**.
  7. **Step 7 (Out of Scope)**: If player is a verified non-RR capped player (`VERIFIED_NOT_ELIGIBLE` with verified international appearances, or other franchise history without uncapped eligibility) $\rightarrow$ return explicit **`OUT_OF_SCOPE`** result; NEVER route to Mode B.

- **Mandatory Triggers for `REVIEW_REQUIRED`**:
  1. Multiple candidate identities returned by PIRE without definitive disambiguation.
  2. Conflicting date of birth, nationality, or playing styles across sources.
  3. Contradictory RR relationship records (e.g., squad list contradicts tournament roster).
  4. Unverified or ambiguous target-season IPL eligibility.
  5. Material disagreement between authoritative sources on performance statistics or team history.
  6. External research fails to meet minimum corroboration threshold (e.g., single uncorroborated tier-4 source).
  7. Career coverage state is `REVIEW_REQUIRED` or data coverage is too sparse to support confident classification.
  8. Authoritative source is restricted or unavailable without a verified secondary fallback.

- **Exact Fields Required in `REVIEW_REQUIRED` Output Dossier**:
  1. `review_status`: Literal `"REVIEW_REQUIRED"`.
  2. `review_reason_codes`: List of strings (e.g., `["IDENTITY_AMBIGUITY", "DOB_CONFLICT", "RR_RECORD_CONTRADICTION", "ELIGIBILITY_UNVERIFIED", "SOURCE_DISCREPANCY", "INSUFFICIENT_COVERAGE"]`).
  3. `unresolved_claims`: List of structured dicts containing claim ID, claim type, conflicting source IDs, and competing values.
  4. `conflicting_source_ids`: List of integer FKs referencing `source_records`.
  5. `missing_evidence`: List of specific missing records needed to resolve the conflict.
  6. `recommended_manual_checks`: List of concrete verification steps for human analysts.

---

### g) PVRE Typed & Versioned Output Contract (All 26 Fields from R2.7)

```python
@dataclass(frozen=True)
class PVREOutputContract:
    # 1. Governance & Run Identification
    contract_version: str                      # "PVRE-2.2.0"
    research_run_id: UUID                      # Unique UUIDv4 per execution run
    player_id: Optional[UUID]                  # Canonical UUID from players table (None if UNRESOLVED)
    canonical_name: str                        # Verified canonical player name
    identity_status: str                       # RESOLVED, PROVISIONAL, UNRESOLVED

    # 2. Routing & Mode Selection
    research_mode: str                         # MODE_A, MODE_B, REVIEW_REQUIRED, OUT_OF_SCOPE
    route_status: str                          # ROUTED_RR_INCUMBENT, ROUTED_UNCAPPED_CANDIDATE,
                                               # ROUTED_SAFETY_REVIEW, ROUTED_OUT_OF_SCOPE
    evaluation_date: date                      # Effective date of evaluation
    target_season_id: UUID                     # Target season evaluated (e.g. IPL 2027 UUID)

    # 3. Membership & Eligibility States (Distinct & Separated)
    rr_relationship_state: str                 # CURRENT_RR, HISTORICAL_RR_APPEARED,
                                               # HISTORICAL_RR_SQUAD_ONLY,
                                               # NO_VERIFIED_RR_RELATIONSHIP,
                                               # RR_RELATIONSHIP_UNKNOWN
    rr_current_state: str                      # CURRENT, NOT_CURRENT, UNKNOWN
    player_capped_status: str                  # CAPPED, UNCAPPED, UNVERIFIED
    ipl_uncapped_eligibility: str              # VERIFIED_ELIGIBLE, VERIFIED_NOT_ELIGIBLE,
                                               # ELIGIBILITY_UNVERIFIED, NOT_ASSESSED

    # 4. Research Windows
    research_window_start: date                # evaluation_date - window_years
    research_window_end: date                  # evaluation_date

    # 5. Career Coverage State
    career_coverage_state: str                 # COMPLETE_WITHIN_VERIFIED_SOURCES,
                                               # PARTIAL_COVERAGE, UNKNOWN, REVIEW_REQUIRED

    # 6. Domain Profiles & Assessments
    rr_historical_profile: Optional[Dict]      # Module A1 outputs (squad vs XI, metrics, roles; None in Mode B)
    recent_global_performance: Optional[Dict]  # Module A2 outputs (leagues, form, sample sizes; None if unassessed)
    complete_career_profile: Optional[Dict]    # Module B outputs (domestic career, formats; None in Mode A)
    replaceability_assessment: Optional[Dict]  # Module A3 outputs (signal, trajectory, rationale; None in Mode B)

    # 7. Coverage, Provenance & Quality
    competition_coverage: Dict[str, str]       # competition_code -> VERIFIED / DATASET_UNAVAILABLE /
                                               # NOT_ESTABLISHED / CONFIRMED_NON_PARTICIPATION
    source_record_ids: List[int]               # FKs to source_records table
    verification_record_ids: List[int]         # FKs to verification_records table
    review_status: str                         # CLEAR, REVIEW_REQUIRED, REJECTED
    review_reason_codes: List[str]             # Reason codes if review_status != CLEAR (empty list if CLEAR)
    data_quality_summary: Dict                 # Completeness score, missing attributes, flags
```

- **Contract Semantics**:
  - `NULL` semantics: Missing statistics or non-applicable profiles must be `NULL`/`None`, never 0.0, empty dicts, or imputed averages.
  - `UNAVAILABLE` semantics: Missing external datasets or tournament records must be explicitly tagged `DATASET_UNAVAILABLE`, never assumed as zero appearances.
  - `VERIFIED` semantics: Any state prefixed `VERIFIED_*` must link to at least one valid row in `verification_records` with evidence tier $\ge 3$.
  - `CONFLICT` semantics: Material disagreements between sources set `verification_status = 'CONFLICT'`, preserve competing claims in `unresolved_claims`, and trigger `review_status = 'REVIEW_REQUIRED'`.
  - Source Traceability: Every claim, statistic, and association must trace to specific integer keys in `source_record_ids` and `verification_record_ids`.

---

### h) SICE Integration & Top-10 Ranking Independence
- **SICE Ingestion**: SICE consumes `PVREOutputContract` when evaluating assembled squads (`user_teams`, `user_team_players`).
- **16-Dimension Role-Aware Incumbent-vs-Candidate Comparison**:
  1. *Primary role match* (e.g. Top-order batter, Pace bowling all-rounder).
  2. *Secondary role & positional flexibility*.
  3. *Batting position distribution* in recent competitions.
  4. *Bowling role, phase specialisation* (Powerplay/Middle/Death), and bowling style.
  5. *Age as of recorded evaluation date* (younger trajectory delta).
  6. *Target season (IPL 2027) eligibility* under active policy.
  7. *RR historical contribution* (match appearances, past equity).
  8. *Recent 2–3 year global performance* outside RR.
  9. *Candidate domestic career development trajectory*.
  10. *Role-specific performance metrics* (strike rate, economy rate, boundary %, dot ball %).
  11. *Sample size depth and consistency* across multi-season samples.
  12. *Format and competition strength context*.
  13. *Squad balance, depth, and role duplication* in user's assembled team.
  14. *Overseas player constraints* (max 8 overseas in squad, 4 in Playing XI).
  15. *Target-season squad constraints* (salary cap impact, uncapped quota requirements).
  16. *Evidence completeness and uncertainty ratings*.
- **Five SICE Structured Recommendation States**:
  1. `ANALYTICAL_RETAIN`: Incumbent maintains superior role-specific performance and squad balance; replacement not recommended.
  2. `ANALYTICAL_MONITOR`: Incumbent remains primary, but a high-potential uncapped candidate demonstrates accelerating trajectory; monitor across domestic fixtures.
  3. `ANALYTICAL_REPLACEMENT_CANDIDATE`: Verified uncapped candidate matches or exceeds incumbent role metrics with age trajectory and squad balance advantages.
  4. `NO_SUITABLE_VERIFIED_REPLACEMENT`: Incumbent replacement is desirable, but no verified candidate satisfies role relevance gates or minimum sample sizes.
  5. `INSUFFICIENT_EVIDENCE`: Either incumbent recent form or candidate domestic samples are below statistical confidence thresholds.
- **Strict Separation from Top-10 Ranking**:
  - The Top-10 youngest eligible uncapped candidate ranking (`RANKING_SPEC.md` `RK-1.0.0`) is an independent hackathon deliverable (`run_type = 'HACKATHON_TOP10'`).
  - Incumbent replacement evaluation (`RE-1.0.0`) is stored under `run_type = 'REPLACEMENT_EVALUATION'`.
  - Mode A replacement evaluation **never modifies, re-weights, or contaminates** the Top-10 leaderboard.

---

### i) Agent Definition: `agent_pvre` and AI Instructions Safety Rules
- **Agent Definition (`docs/AGENTS.md`)**:
  - Identifier: `agent_pvre` (Agent 08b, Family 2: Engine Specialists).
  - Mission: Govern and implement the Player Verification & Research Engine (PVRE — Engine 07), managing the Mother Controller, Mode A replacement intelligence, Mode B uncapped candidate discovery, mandatory `REVIEW_REQUIRED` safety gating, and typed output contracts.
  - Strict Boundaries: Coordinates with but never replaces PIRE, TMVE, CDCRE, Eligibility Policy Service, CPPAE, CMIE, or SICE. Prohibited from making standalone release/retain decisions or inventing arbitrary replacement probabilities.
- **AI Instructions Safety Rules (`docs/AI_INSTRUCTIONS.md`)**:
  - **Rule R13**: Never equate missing database records with uncapped status (absence $\neq$ uncapped).
  - **Rule R14**: Never treat absence of RR records as verified non-membership without TRD §4.5 negative verification requirements.
  - **Rule R15**: Never merge two identities due to name similarity.
  - **Rule R16**: Never treat browser search snippets as verified facts.
  - **Rule R17**: Never overwrite conflicting evidence; preserve competing claims and flag `REVIEW_REQUIRED`.
  - **Rule R18**: Always apply `REVIEW_REQUIRED` when mandatory evidence is insufficient or contradictory.
  - **Rule R19**: Never invent statistics, match appearances, or career participation.
  - **Rule R20**: Never make replacement or release decisions inside PVRE (analytical signals to SICE only).
  - **Rule R21**: Never mix the Top-10 ranking model with replacement evaluation.
  - **Rule R22**: Never expose secrets, credentials, or proprietary hackathon data.

---

### j) Count Governance Across Documentation Suite
- **Seven Specialised Engines (ENGINE 01–07)**:
  1. `ENGINE 01`: PIRE (Player Identity Resolution Engine)
  2. `ENGINE 02`: TMVE (Team Membership Verification Engine)
  3. `ENGINE 03`: CDCRE (Cross-Dataset Career Reconstruction Engine)
  4. `ENGINE 04`: CPPAE (Complete Player Performance Analytics Engine)
  5. `ENGINE 05`: CMIE (Contextual Match Intelligence Engine)
  6. `ENGINE 06`: SICE (Squad Intelligence & Context Engine)
  7. `ENGINE 07`: PVRE (Player Verification & Research Engine)
- **Five Support Services (Services A–E)**:
  1. `Service A`: Data Ingestion Service
  2. `Service B`: Player Profile Generator
  3. `Service C`: Source Verification & Provenance Service
  4. `Service D`: Data Quality & Coverage Service
  5. `Service E`: Team Builder Service
- **One Specialised Policy Service**:
  - `Eligibility Policy Service` (Agent 04b; evaluates Dimension 3 against versioned policies).
- **Eighteen System Agents**:
  - Family 1 (Orchestration & Governance): Agent 01 (Chief Architect), Agent 02 (MIE Orchestration) [2]
  - Family 2 (Engine Specialists): Agent 03 (PIRE), Agent 04 (TMVE), Agent 04b (Eligibility Policy Service), Agent 05 (CDCRE), Agent 06 (CPPAE), Agent 07 (CMIE), Agent 08 (SICE), Agent 08b (PVRE) [8]
  - Family 3 (Support-Service Specialists): Agent 09 (Ingestion), Agent 10 (Provenance), Agent 11 (Data Quality), Agent 12 (Team Builder), Agent 13 (Profile Generator) [5]
  - Family 4 (Delivery & QA): Agent 14 (Streamlit App), Agent 15 (Documentation), Agent 16 (Testing & QA) [3]
  - Total: 2 + 8 + 5 + 3 = 18 agents.
- **Thirty-Three Core Database Entities**: Fully validated PostgreSQL DDL core.
- **Thirty Acceptance Criteria**: AC-01 through AC-30 (AC-24..AC-30 governing PVRE and Phase 4B).

---

## 5. Specification Mining Tables

### Features Discovered

| # | Category | Feature | Description | Inputs | Outputs | Error Behavior | Discovered Via |
|---|---|---|---|---|---|---|---|
| F1 | Orchestration | MIE Sole Cross-Engine Orchestrator | MIE coordinates all 7 engines and passes consolidated context to PVRE; PVRE never directly commands other engines. | User request, raw name, target season | Unified player intelligence report | Halts with `REVIEW_REQUIRED` on ambiguous/colliding data | `ORIGINAL_REQUEST.md §R2.1`, `TRD.md §2.3` |
| F2 | Orchestration | PVRE Mother Controller | Internal workflow routing coordinator for Engine 07; dispatches to Mode A, Mode B, or Review Gateway. | `PVRERequestContract` | `PVREOutputContract` | Immediate interception to `REVIEW_REQUIRED` | `ORIGINAL_REQUEST.md §R2.1`, `TRD.md §9.1` |
| F3 | Mode A | RR Historical Performance (A1) | Complete RR career analysis across 2008–2015 & 2018–2026; strictly separates squad membership from playing XI appearances. | Canonical `player_id`, RR seasons | Season-wise batting, bowling, fielding, wicketkeeping, roles | Squad-only seasons have `appearances = 0` and zero stats | `ORIGINAL_REQUEST.md §R2.2`, `TRD.md §9.3.1` |
| F4 | Mode A | Recent Global Performance (A2) | Analyses recent performance outside RR across 2–3 year window relative to `evaluation_date` across recognised global leagues. | Canonical `player_id`, `evaluation_date`, window years | League-by-league metrics (R01–R06), participation gaps, injury status | Missing datasets flagged `DATASET_UNAVAILABLE`; never assumed non-participation | `ORIGINAL_REQUEST.md §R2.2`, `TRD.md §9.3.2` |
| F5 | Mode A | Replaceability Assessment (A3) | Synthesises RR history, global form, age trajectory, and role scarcity into 5 structured analytical signals. | Module A1 & A2 profiles, age, role benchmarks | Signal (`RETAIN_SIGNAL`, `MONITOR_SIGNAL`, `POTENTIALLY_REPLACEABLE`, etc.) | Sample < threshold $\rightarrow$ `INSUFFICIENT_EVIDENCE`; conflicts $\rightarrow$ `REVIEW_REQUIRED` | `ORIGINAL_REQUEST.md §R2.2`, `TRD.md §9.3.3` |
| F6 | Mode B | Domestic Career Discovery | Discovers career across Ranji, SMAT, VHT, Duleep, and age-group competitions (Vinoo Mankad, Cooch Behar, CK Nayudu, Vijay Merchant). | Canonical `player_id`, target season policy | Multi-format match statistics, batting positions, bowling spells | Gaps preserved; zero international caps enforced | `ORIGINAL_REQUEST.md §R2.3`, `TRD.md §9.4` |
| F7 | Mode B | Negative Proof Invariant | Database absence is never proof of uncapped status; affirmative policy proof required. | Candidate record, `eligibility_policies` | `VERIFIED_UNCAPPED` or blocked from pool | Default state is `NOT_ASSESSED` / `UNVERIFIED` | `ORIGINAL_REQUEST.md §R2.3`, `AI_INSTRUCTIONS.md R13` |
| F8 | Data Governance | Dual Status Separation | Separates intrinsic cricketing cap status (`player_capped_status`) from IPL season regulatory eligibility (`ipl_uncapped_eligibility`). | International records, IPL season regulations | Two distinct verified fields | Never conflate or infer one from the other | `ORIGINAL_REQUEST.md §R2.4` |
| F9 | Data Governance | Career Coverage Taxonomy | Four explicit states: `COMPLETE_WITHIN_VERIFIED_SOURCES`, `PARTIAL_COVERAGE`, `UNKNOWN`, `REVIEW_REQUIRED`. | Verified dataset ledger per player | `career_coverage_state: str` | Missing SMAT or domestic records prominently surfaced | `ORIGINAL_REQUEST.md §R2.5` |
| F10 | Safety | 7-Step Routing Waterfall | Deterministic precedence: Identity $\rightarrow$ RR Relationship $\rightarrow$ Mode A $\rightarrow$ Eligibility $\rightarrow$ Mode B $\rightarrow$ REVIEW_REQUIRED $\rightarrow$ OUT_OF_SCOPE. | `PVRERequestContract` | Deterministic routing branch | Unresolved claims halt at Step 6 `REVIEW_REQUIRED` | `ORIGINAL_REQUEST.md §R2.6`, `TRD.md §9.2` |
| F11 | Safety | Structured Review Dossier | Emits 6 mandatory audit fields on data conflicts or gaps; blocks automated candidate pool pollution. | Ambiguous/conflicting records | Dossier (`review_status`, `review_reason_codes`, `unresolved_claims`, etc.) | Automated routing completely halted | `ORIGINAL_REQUEST.md §R2.6`, `TRD.md §9.5` |
| F12 | Contracts | Typed PVRE Output Contract | Versioned, typed 26-field contract with complete provenance links and explicit null/unavailable semantics. | Execution run results | `PVREOutputContract` | Missing stats $\rightarrow$ `NULL`; missing data $\rightarrow$ `DATASET_UNAVAILABLE` | `ORIGINAL_REQUEST.md §R2.7`, `TRD.md §9.6` |
| F13 | SICE | 16-Dimension Comparison | Role-aware comparison of incumbent vs uncapped candidates across 16 specified performance and squad dimensions. | Incumbent profile, uncapped candidate profiles | Multi-dimensional comparison matrix | No single composite score or scalar probability allowed | `ORIGINAL_REQUEST.md §R2.8`, `TRD.md §8.4` |
| F14 | SICE | SICE Recommendation States | Emits 5 analytical recommendation states (`ANALYTICAL_RETAIN`, `ANALYTICAL_MONITOR`, `ANALYTICAL_REPLACEMENT_CANDIDATE`, etc.). | 16-dimension matrix, squad constraints | Labelled recommendation string | Insufficient samples $\rightarrow$ `INSUFFICIENT_EVIDENCE` | `ORIGINAL_REQUEST.md §R2.8`, `TRD.md §8.4` |
| F15 | SICE | Top-10 Ranking Independence | Top-10 youngest uncapped ranking (`RK-1.0.0`) is strictly isolated from incumbent replacement evaluation (`RE-1.0.0`). | Ranking configuration, data snapshot | Separate `ranking_runs` rows | Replacement evaluation never alters Top-10 board | `ORIGINAL_REQUEST.md §R2.8`, `RANKING_SPEC.md §9` |
| F16 | Agents | `agent_pvre` Specification | Family 2 Engine Specialist governing Engine 07, Mother Controller, Mode A/B, and safety gating. | Engine 07 execution requests | Verified output contracts, review dossiers | Strictly forbidden from making release/retain decisions | `ORIGINAL_REQUEST.md §R4.5`, `AGENTS.md §Agent 08b` |

---

### Edge Cases

| # | Feature | Input Scenario | Observed / Mandated Behavior |
|---|---|---|---|
| E1 | Mother Controller | Unknown player query absent from database and external sources. | PIRE returns `UNRESOLVED` $\rightarrow$ Mother Controller executes Step 1 $\rightarrow$ routes immediately to `REVIEW_REQUIRED`. Invariant holds: never infer player is uncapped. |
| E2 | Mode A (A1) | Historical RR player included in squad for 2 seasons but never selected in playing XI. | `rr_relationship_state = 'HISTORICAL_RR_SQUAD_ONLY'`. Scorecard appearance count is strictly 0. Batting and bowling aggregates are `NULL`. Zero match appearances inferred from squad list. |
| E3 | Mode A (A2) | Incumbent player evaluated on 2026-11-10 with configurable window of 3 years. | Window bounds strictly to `[2023-11-10, 2026-11-10]`. Matches prior to 2023-11-10 are excluded from window rates R01–R04. Sample sizes explicitly displayed. |
| E4 | Mode A (A2) | Local SMAT ball-by-ball archive unavailable for domestic window evaluation. | Competition status reported as `DATASET_UNAVAILABLE`. Career coverage reported as `PARTIAL_COVERAGE`. System never assumes player did not play SMAT. |
| E5 | Mode A (A3) | Incumbent player with declining T20 form but only 12 balls faced in evaluation window. | Module A3 outputs `INSUFFICIENT_EVIDENCE` (below 20-ball sample gate). Prevents premature `POTENTIALLY_REPLACEABLE` signal. |
| E6 | Mode B | Discovered candidate has zero senior international appearances, but played ICC U19 World Cup. | U19 matches do NOT constitute senior international caps. Candidate maintains `player_capped_status = 'UNCAPPED'`. Eligibility checked under target season policy. |
| E7 | Mode B | Discovered candidate has 1 T20I appearance for an ICC Associate member nation. | T20I is an official senior international match. Candidate is classified `player_capped_status = 'CAPPED'` $\rightarrow$ Step 7 triggers $\rightarrow$ returned as `OUT_OF_SCOPE`; blocked from uncapped pool. |
| E8 | Safety Gate | Player has two authoritative sources reporting conflicting DOBs (e.g. 2003-04-12 vs 2002-04-12). | Step 6 triggers $\rightarrow$ routes to `REVIEW_REQUIRED`. Output dossier includes `review_reason_codes: ["DOB_CONFLICT"]`, `unresolved_claims`, and `conflicting_source_ids`. Automated routing halted. |
| E9 | Safety Gate | Player has verified squad contract from franchise website, but official IPL squad release omits player. | Contradictory RR evidence triggers `REVIEW_REQUIRED` with code `RR_RECORD_CONTRADICTION`. Competing claims preserved with status `CONFLICT`. |
| E10 | SICE Integration | Incumbent top-order batter compared against verified uncapped pace-bowling all-rounder. | Role relevance gate fails. SICE role-aware comparison prevents cross-role run comparison. Outputs `NO_SUITABLE_VERIFIED_REPLACEMENT`. |
| E11 | SICE Integration | SICE executes replacement evaluation for 5 incumbent RR players. | Results stored under `ranking_runs.run_type = 'REPLACEMENT_EVALUATION'`. Verified assertion: `ranking_runs.run_type = 'HACKATHON_TOP10'` board remains bit-for-bit identical. |

---

## 6. Verification Method

To independently verify the facts, contracts, and cross-document alignment documented in this report:

1. **Verify Git Baseline and Tree**:
   ```powershell
   git status
   git log -2 --oneline
   ```
2. **Inspect Orchestration Boundary Enforcement**:
   - Check `docs/ARCHITECTURE.md §2.1` & `§2.2b`: confirm MIE remains sole cross-engine orchestrator; verify PVRE Mother Controller does not have direct command arrows to PIRE, TMVE, CDCRE, or EPS.
   - Check `docs/TRD.md §2.3` & `§9.1`: confirm Mother Controller lifecycle is scoped internally to Engine 07.
3. **Verify Output Contract Field Completeness**:
   - Check `docs/TRD.md §9.6.2`: confirm all 26 fields from R2.7 are present, including `player_capped_status`, `ipl_uncapped_eligibility`, and `career_coverage_state`.
4. **Audit Count Governance**:
   ```powershell
   # Search for invalid "6 support services" occurrences:
   Select-String -Path 'README.md', 'docs/README.md' -Pattern '6 support services|6 services'
   ```
   Confirm all documentation files uniformly report **7 specialised engines**, **5 support services**, and **18 agents**.
5. **Verify Phase Dependencies in `docs/PHASES.md`**:
   - Inspect Phase 7 (line 413) and Phase 8 (line 433) to ensure explicit dependency on Phase 4B (PVRE) is declared.

**Invalidation Conditions**:
- If any document allows PVRE Mother Controller to directly execute cross-engine pipelines bypassing MIE.
- If `player_capped_status` and `ipl_uncapped_eligibility` are merged into a single field.
- If missing database records are permitted to infer uncapped eligibility.
- If any document reports an engine count $\neq 7$ or support-service count $\neq 5$.
