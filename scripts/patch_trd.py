import os

with open('docs/TRD.md', 'r', encoding='utf-8') as f:
    text = f.read().replace('\r\n', '\n')

# 1. Update version header & revision note
old_hdr = '''**Document Version**: 2.1.1-TARGETED-REMEDIATION
**Status**: [STATUS: PLANNED - GREENFIELD BASELINE]
**Author**: Engineering Architecture Team (`teamwork_worker_2`)

> **Revision Note (v2.1.1, targeted remediation)**: Corrects the cricket-statistics DDL'''

new_hdr = '''**Document Version**: 2.2.0
**Status**: [STATUS: PLANNED - GREENFIELD BASELINE]
**Author**: Engineering Architecture Team (`teamwork_worker_2`)

> **Revision Note (v2.2.0, PVRE Dual-Mode Architecture)**: Introduces Engine 07 — Player
> Verification & Research Engine (PVRE) orchestrated by MIE. Defines the Mother Controller,
> deterministic routing precedence, Mode A (Existing RR Player Replacement Intelligence: Module A1
> RR History, Module A2 Recent Global Performance across a configurable 2–3 year window, Module A3
> Replaceability Evidence Assessment with 5 analytical signal states), Mode B (Verified Uncapped
> Candidate Intelligence: complete domestic career discovery and independent target-season policy
> verification), mandatory `REVIEW_REQUIRED` safety pathway, and SICE role-aware incumbent-vs-candidate
> replacement comparison. Reconciles database entity count to 33 entities everywhere. Documents that
> existing 33-entity PostgreSQL core fully supports PVRE research runs and replacement features
> without DDL expansion.
>
> **Revision Note (v2.1.1, targeted remediation, retained for history)**: Corrects the cricket-statistics DDL'''

assert old_hdr in text
text = text.replace(old_hdr, new_hdr)

# 2. Section 1 Diagram and description
old_diagram = '''   ┌───────┴────────────┬──────────────────┼──────────────────┬───────────────┐
   ▼                    ▼                  ▼                  ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ ENGINE 01     │ │ ENGINE 02     │ │ ENGINE 03     │ │ ENGINE 04     │ │ ENGINES 05/06│
│ PIRE         │ │ TMVE         │ │ CDCRE        │ │ CPPAE        │ │ CMIE / SICE  │
│ Identity Res. │ │ Membership   │ │ Candidate +  │ │ Performance  │ │ Context/ Squad │
│              │ │ Verification  │ │ Career Disc. │ │              │ │              │
└──────┬───────┘ └──────┬───────┘ └──────┬───────┘ └──────┬───────┘ └──────┬───────┘'''

new_diagram = '''   ┌───────┴────────────┬──────────────────┼──────────────────┬───────────────┬───────────────┐
   ▼                    ▼                  ▼                  ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ ENGINE 01     │ │ ENGINE 02     │ │ ENGINE 03     │ │ ENGINE 04     │ │ ENGINES 05/06│ │ ENGINE 07     │
│ PIRE         │ │ TMVE         │ │ CDCRE        │ │ CPPAE        │ │ CMIE / SICE  │ │ PVRE         │
│ Identity Res. │ │ Membership   │ │ Candidate +  │ │ Performance  │ │ Context/Squad│ │ Verification │
│              │ │ Verification  │ │ Career Disc. │ │              │ │ Intelligence │ │ & Research   │
└──────┬───────┘ └──────┬───────┘ └──────┬───────┘ └──────┬───────┘ └──────┬───────┘ └──────┬───────┘'''

assert old_diagram in text
text = text.replace(old_diagram, new_diagram)

old_subsystems = '''1. **Presentation Tier (Streamlit, initial)**: Streamlit application exposing the 11 required
   views (§12). UI components call MIE and are **strictly separated** from analytics;
   `st.session_state` is used for ephemeral UI state only (§12.2).
2. **Mother Intelligence Engine (MIE)**: central orchestrator (§2). MIE does **not** invent
   statistics or make membership/eligibility decisions; it coordinates the six engines, merges
   outputs, and returns structured responses.
3. **Six Specialised Engines (ENGINE 01–06)**: PIRE, TMVE, CDCRE, CPPAE, CMIE, SICE — each with
   a documented input/output contract (§3–§8).
4. **Five Support Services (A–E)**: §9.
5. **Central Normalised Relational Core (PostgreSQL 16, 33 entities)**: normalised 3NF core
   with canonical `player_id` across all engines and declarative season partitioning on
   `deliveries` (§10). `derived_features` is a deliberately denormalised feature store,
   documented as the one non-3NF table.
6. **Data Ingestion & ELT Pipeline**: immutable raw staging with SHA-256 provenance and
   quarantining (§9.1).

### 1.2 Frontend-Agnostic Engine Contract
All six engines and MIE expose **typed, versioned Python interfaces** (request/response data
classes or Pydantic models) independent of any UI framework.'''

new_subsystems = '''1. **Presentation Tier (Streamlit, initial)**: Streamlit application exposing the 11 required
   views (§13). UI components call MIE and are **strictly separated** from analytics;
   `st.session_state` is used for ephemeral UI state only (§13.2).
2. **Mother Intelligence Engine (MIE)**: central orchestrator (§2). MIE does **not** invent
   statistics or make membership/eligibility decisions; it coordinates the seven engines, merges
   outputs, and returns structured responses.
3. **Seven Specialised Engines (ENGINE 01–07)**: PIRE, TMVE, CDCRE, CPPAE, CMIE, SICE, PVRE — each with
   a documented input/output contract (§3–§9).
4. **Five Support Services (A–E)**: §10.
5. **Central Normalised Relational Core (PostgreSQL 16, 33 entities)**: normalised 3NF core
   with canonical `player_id` across all engines and declarative season partitioning on
   `deliveries` (§11). `derived_features` is a deliberately denormalised feature store,
   documented as the one non-3NF table.
6. **Data Ingestion & ELT Pipeline**: immutable raw staging with SHA-256 provenance and
   quarantining (§10.1).

### 1.2 Frontend-Agnostic Engine Contract
All seven engines and MIE expose **typed, versioned Python interfaces** (request/response data
classes or Pydantic models) independent of any UI framework.'''

assert old_subsystems in text
text = text.replace(old_subsystems, new_subsystems)

# 3. Section 2.3 Orchestration Sequence
old_seq = '''### 2.3 Orchestration Sequence (revised — no circular dependency)
1. `CDCRE.discover_candidates(name)` — **pre-identity** candidate discovery: retrieve candidate
   records (internal aliases + authorised external research) that *corroborate* the raw name.
   This step works on raw names; it does **not** require a canonical `player_id`.
2. `PIRE.resolve(name, candidates)` — deterministic tiered identity resolution using the
   discovered candidates as corroboration. If the identity is ambiguous or unresolved →
   **request user clarification / human review**; MIE does not guess.
3. On resolution: canonical `player_id`.
4. `TMVE.verify(player_id)` — three-dimension membership evaluation (RR relationship, currency,
   evidence); triggers authorised research only where internal records are insufficient.
5. `CDCRE.discover_career(player_id)` — **post-identity** full career retrieval + coverage.
6. `CPPAE.analyse(player_id)` → `CMIE.contextualise(player_id)`.
7. Eligibility: `EligibilityOutput` computed against the active `eligibility_policies` version
   for the target season; `NOT_ASSESSED` until TMVE/research evidence supports a status.
8. If `team_id` supplied → `SICE.evaluate(team_id)` → squad report.
9. MIE merges, attaches provenance (Service C) and coverage (Service D), and returns.

> **Process invariant**: `Raw name → candidate discovery → identity corroboration → canonical
> player ID → membership verification → career retrieval → analytics`. CDCRE capability 1
> never requires a canonical player ID; capability 2 operates only on resolved IDs.'''

new_seq = '''### 2.3 Orchestration Sequence (revised — PVRE Dual-Mode Integration)
1. `CDCRE.discover_candidates(name)` — **pre-identity** candidate discovery: retrieve candidate
   records (internal aliases + authorised external research) that *corroborate* the raw name.
   This step works on raw names; it does **not** require a canonical `player_id`.
2. `PIRE.resolve(name, candidates)` — deterministic tiered identity resolution using the
   discovered candidates as corroboration. If identity is ambiguous or unresolved →
   **route to `REVIEW_REQUIRED` / request user clarification**; MIE never guesses.
3. On resolution: obtain canonical `player_id`.
4. `TMVE.verify(player_id)` — evaluate Dimension 1 (`rr_relationship_state`) and Dimension 2
   (`rr_current_state`) backed by `player_membership_state` and evidence.
5. `EligibilityPolicyService.assess(player_id, target_season_id)` — evaluate Dimension 3
   (`eligibility_status`) against the active `eligibility_policies` version.
6. **PVRE Mother Controller Execution (Engine 07)** — deterministic classification and routing:
   - **Mode A (Verified RR Incumbent)**: If current or historical RR relationship is verified
     (`CURRENT_RR`, `HISTORICAL_RR_APPEARED`, `HISTORICAL_RR_SQUAD_ONLY`):
     * Execute Module A1: complete RR historical performance research (appearances vs squad inclusion).
     * Execute Module A2: recent global performance research across a configurable 2–3 year window
       (BBL, PSL, CPL, SA20, The Hundred, Intl, domestic).
     * Execute Module A3: replaceability evidence assessment (`RETAIN_SIGNAL`, `MONITOR_SIGNAL`,
       `POTENTIALLY_REPLACEABLE`, `INSUFFICIENT_EVIDENCE`, `REVIEW_REQUIRED`).
     * Forward incumbent profile and replaceability assessment to SICE for comparative squad evaluation.
   - **Mode B (Verified Uncapped Prospect)**: If non-RR (`NO_VERIFIED_RR_RELATIONSHIP`) and
     independently verified uncapped (`VERIFIED_ELIGIBLE`):
     * Execute full domestic career discovery across Ranji, SMAT, VHT, Duleep, and age-groups.
     * Enforce independent eligibility policy verification.
     * Populate candidate pool for SICE squad integration and hackathon ranking.
   - **Mandatory `REVIEW_REQUIRED` Safety Pathway**: If identity is ambiguous, DOB/attributes
     conflict, RR evidence is contradictory, eligibility is unverified, or coverage is insufficient:
     * Emit structured review dossier (`review_status`, `review_reason_codes`, `unresolved_claims`,
       `conflicting_source_ids`, `missing_evidence`, `recommended_manual_checks`).
     * Halt automated routing; block candidate pool promotion; trigger human review.
   - **Out of Scope Notice**: If player is a verified non-RR capped player:
     * Return explicit `OUT_OF_SCOPE` notice; never route to Mode B.
7. `CPPAE.analyse(player_id)` and `CMIE.contextualise(player_id)` provide underlying performance
   metrics and contextual environmental conditions for the research scope defined by PVRE.
8. `SICE.evaluate(team_id, replacement_context)` — evaluate assembled squad:
   - Perform role-aware incumbent-vs-candidate replacement comparisons (§8.4) for Mode A players.
   - Separately produce the hackathon Top-10 uncapped ranking board per `RANKING_SPEC.md` (`RK-1.0.0`).
9. MIE merges, attaches provenance (Service C) and coverage (Service D), and returns the unified
   report.

> **Process invariant**: `Raw name → candidate discovery → identity corroboration → canonical
> player ID → membership verification → eligibility assessment → PVRE Mother Controller routing
> (Mode A / Mode B / REVIEW_REQUIRED) → performance & context analytics → SICE evaluation`.
> CDCRE capability 1 never requires a canonical player ID; capability 2 operates only on resolved IDs.'''

assert old_seq in text
text = text.replace(old_seq, new_seq)

# 4. In Section 8 SICE add Section 8.4
old_sice_end = '''### 8.3 SICE Guardrails
- Recommendations are labelled **analytical** — never official RR selections or auction decisions.
- **No recruitment probabilities** unless the underlying model is statistically validated and
  calibrated (`calibrated=TRUE`).

---'''

new_sice_sec = '''### 8.3 SICE Guardrails
- Recommendations are labelled **analytical** — never official RR selections or auction decisions.
- **No recruitment probabilities** unless the underlying model is statistically validated and
  calibrated (`calibrated=TRUE`).

### 8.4 SICE Incumbent-vs-Candidate Replacement Comparison (Mode A Integration)
When evaluating an incumbent Rajasthan Royals player under PVRE Mode A, SICE performs a
structured, role-aware squad-level comparison between the incumbent and one or more
verified-eligible uncapped candidates:

1. **Role-Aware Comparison Across 16 Specified Dimensions**:
   - Primary role (e.g. Top-order batter, Pace bowling all-rounder)
   - Secondary role and flexibility
   - Batting position distribution in recent competitions
   - Bowling role, phase specialisation (Powerplay/Middle/Death), and bowling style
   - Age as of the recorded `evaluation_date` (younger trajectory)
   - IPL 2027 eligibility under the active `eligibility_policies` version
   - RR historical contribution (match appearances, longevity, past contributions)
   - Recent 2–3 year global performance outside RR
   - Candidate domestic career development trajectory
   - Role-specific performance metrics (strike rate, economy rate, boundary %, dot ball %)
   - Sample size depth and consistency across multi-season samples
   - Format and competition strength context
   - Squad balance, depth, and role duplication in the user's assembled team
   - Overseas player constraints (maximum 8 overseas in squad, 4 in Playing XI)
   - Target-season squad constraints (salary cap impact, uncapped quota requirements)
   - Evidence completeness and uncertainty ratings
2. **Role-Aware Discipline**:
   - Comparisons are strictly role-aware. An all-rounder must **never** be compared with a
     specialist batter solely on total runs.
   - Metrics are compared against role-specific benchmarks defined in `DATA_DICTIONARY.md`.
3. **Structured SICE Recommendations**:
   - `ANALYTICAL_RETAIN`: Incumbent maintains superior role-specific performance and squad balance;
     replacement is not recommended.
   - `ANALYTICAL_MONITOR`: Incumbent remains primary, but a high-potential uncapped candidate
     demonstrates accelerating trajectory; monitor across domestic fixtures.
   - `ANALYTICAL_REPLACEMENT_CANDIDATE`: Verified uncapped candidate matches or exceeds incumbent
     role metrics with age trajectory and squad balance advantages.
   - `NO_SUITABLE_VERIFIED_REPLACEMENT`: Incumbent replacement is desirable, but no verified
     candidate satisfies role relevance gates or minimum sample sizes.
   - `INSUFFICIENT_EVIDENCE`: Either incumbent recent form or candidate domestic samples are below
     statistical confidence thresholds.
4. **Reproducibility & Audit Trail**:
   - Evaluated comparisons are frozen in `ranking_runs` with `(config_id, data_snapshot_sha256)`,
     guaranteeing identical inputs reproduce bit-for-bit identical recommendations.
5. **Strict Deliverable Separation**:
   - The Top-10 youngest eligible uncapped candidate ranking (`RANKING_SPEC.md` `RK-1.0.0`)
     remains a separate standalone deliverable and is **never** merged with incumbent replacement
     evaluation.

---'''

assert old_sice_end in text
text = text.replace(old_sice_end, new_sice_sec)

# 5. Add Section 9 ENGINE 07 PVRE and renumber subsequent sections
s9_target = '## 9. Support Services'
assert s9_target in text

pvre_section_text = '''## 9. ENGINE 07 — Player Verification & Research Engine (PVRE)

**ENGINE 07 — Player Verification & Research Engine (PVRE)**

**Purpose**: Orchestrated by the Mother Intelligence Engine (MIE), PVRE provides dual-mode
player verification, multi-format career discovery, and replacement intelligence. PVRE
determines whether an existing Rajasthan Royals incumbent can be replaced by a younger,
verified-eligible uncapped prospect (Mode A), or conducts deep career discovery for newly
identified uncapped prospects (Mode B). It enforces a mandatory `REVIEW_REQUIRED` safety
pathway whenever identity, membership, or eligibility evidence is ambiguous, incomplete, or
contradictory.

PVRE does **not** replace PIRE, TMVE, CDCRE, CPPAE, CMIE, the Eligibility Policy Service, or
SICE. Rather, it coordinates their outputs and defines the targeted research scope required
for the selected workflow.

### 9.1 Mother Controller & Input Classification
The **Mother Controller** is the central execution coordinator of Engine 07. Its lifecycle:
1. **Receive input**: Accepts the user's player input (raw name, alias, or known identifier)
   and execution context (target season ID, evaluation date, research window).
2. **Pre-identity discovery**: Triggers CDCRE capability 1 (`discover_candidates`) when
   operating on raw or ambiguous names to gather corroborating candidates.
3. **Identity resolution**: Uses PIRE (`resolve`) to resolve the canonical `player_id`,
   identity tier, and status.
4. **RR relationship retrieval**: Obtains verified Rajasthan Royals relationship information
   from TMVE (`verify`), specifically Dimension 1 (`rr_relationship_state`) and Dimension 2
   (`rr_current_state`).
5. **Eligibility assessment**: Obtains season-specific IPL eligibility from the Eligibility
   Policy Service (Dimension 3: `eligibility_status`) evaluated against the active policy.
6. **Request classification & mode selection**: Evaluates the gathered evidence against the
   deterministic routing precedence (§9.2).
7. **Research orchestration**: Coordinates targeted deep research dependencies (CDCRE
   capability 2 for career data, CPPAE for performance metrics, CMIE for contextual conditions)
   and retries.
8. **Evidence & conflict tracking**: Tracks source coverage, provenance records, and conflicting
   claims via Support Service C.
9. **Contract compilation**: Emits the standardised, typed `PVREOutputContract` (§9.6).

> **Mother Controller Invariant**: The Mother Controller **never infers that an unknown player
> is uncapped**. Absence from the database or external datasets is never proof of uncapped
> status or non-membership.

### 9.2 Deterministic Routing Precedence
PVRE executes a deterministic 7-step routing waterfall:
1. **Step 1 (Identity)**: Resolve player identity via PIRE. If identity resolution yields
   `UNRESOLVED` or multiple unresolved candidates → route to **`REVIEW_REQUIRED`**.
2. **Step 2 (RR Relationship)**: Inspect TMVE Dimension 1 (`rr_relationship_state`) and
   Dimension 2 (`rr_current_state`).
3. **Step 3 (Mode A Trigger)**: If the player has a verified current or historical RR
   relationship (`CURRENT_RR`, `HISTORICAL_RR_APPEARED`, `HISTORICAL_RR_SQUAD_ONLY`) → route to
   **Mode A (Existing RR Player Replacement Intelligence)**.
4. **Step 4 (Eligibility Assessment)**: If the player has no verified RR relationship, inspect
   Dimension 3 (`eligibility_status`) from the Eligibility Policy Service.
5. **Step 5 (Mode B Trigger)**: If the player is independently verified as uncapped-eligible
   (`VERIFIED_ELIGIBLE`) under the applicable target-season policy → route to **Mode B
   (Uncapped Candidate Intelligence)**.
6. **Step 6 (Safety Fallback)**: If identity, RR relationship, or eligibility evidence is
   incomplete, unverified (`ELIGIBILITY_UNVERIFIED`, `NOT_ASSESSED`, `RR_RELATIONSHIP_UNKNOWN`),
   or conflicting → route to **`REVIEW_REQUIRED`**.
7. **Step 7 (Out of Scope)**: If the player is verified as a non-RR capped player
   (`VERIFIED_NOT_ELIGIBLE` with verified international appearances or other franchise history
   without uncapped eligibility) → return an explicit **`OUT_OF_SCOPE`** result; **never**
   route to Mode B.

### 9.3 Mode A: Existing Rajasthan Royals Player Replacement Intelligence
When an input player has a verified current or historical RR relationship, PVRE investigates
whether that player may be replaceable by a younger, verified-eligible uncapped prospect.
PVRE conducts an intensive dual-scope research investigation covering both RR history and
recent global performance.

#### 9.3.1 Module A1 — RR Historical Performance Research
Retrieves and analyses the player's complete RR history across all evidenced seasons
(2008–2015, 2018–2026):
- **Squad membership by season**: Documented seasons in `squad_memberships`.
- **Actual RR match appearances**: Derived strictly from `innings` and `matches` scorecards
  where `teams.team_code = 'RR'`. Squad inclusion without match appearances is flagged
  `appearances = 0` (`HISTORICAL_RR_SQUAD_ONLY`). Appearances are **never inferred** from squad
  membership.
- **Season-wise batting performance**: Runs, balls, dismissals, batting average (B05), strike
  rate (B10), boundary percentage (B08), dot ball percentage (B09), phase splits (Powerplay,
  Middle, Death).
- **Season-wise bowling performance**: Integer legal balls bowled, wickets (W02), bowling average
  (W06), economy rate (W05), bowling strike rate (W07), dot ball percentage (W08), phase splits.
- **Fielding and wicketkeeping contribution**: Catches, run outs, stumpings, missed chances
  where recorded in `fielding_events` and `wicketkeeping_events`.
- **Tactical role evolution**: Batting order position distribution, bowling spell roles, and
  tactical usage changes across seasons.
- **Historical participation & association evidence**: Provenance links for each season's
  association (`source_records` and `verification_records`).

#### 9.3.2 Module A2 — Recent Global Performance Research
Retrieves and analyses the player's recent performance outside Rajasthan Royals:
- **Configurable research window**: Default window is the **previous three years** relative to
  the recorded `evaluation_date` (configurable between 2 and 3 years).
- **Recognised competitions investigated**:
  1. Other IPL franchise appearances (`ipl_male_json`).
  2. Big Bash League (`bbl_male_json`).
  3. Pakistan Super League (`psl_male_json`).
  4. Caribbean Premier League (`cpl_male_json`).
  5. SA20 (`sat_male_json`).
  6. The Hundred (`hnd_male_json`, balls_per_over = 5).
  7. International cricket (Tests, ODIs, T20Is; `icc_*_json` + official match archives).
  8. Indian domestic cricket (Ranji Trophy, Syed Mushtaq Ali Trophy, Vijay Hazare Trophy).
  9. Other verified recognised leagues (BPL, LPL, MLC, ILT20).
- **Research metrics & parameters**:
  - Competition, season, team representation, matches, and innings.
  - Batting and bowling performance profiles per format with visible sample sizes.
  - Fielding contribution where available.
  - Tactical role and batting position.
  - Recent form trajectory and multi-tournament consistency.
  - Participation gaps across seasons.
  - Injury and availability records supported strictly by verified evidence (`player_injuries`,
    `player_availability`); no unevidenced fitness claims.
  - Data coverage completeness and sample size flags.
- **Methodological guardrails**:
  - Do not assume every player participates in every league.
  - Do not treat unavailable datasets as evidence of non-participation.
  - Do not compare raw statistics across formats or leagues without appropriate contextual
    normalisation.

#### 9.3.3 Module A3 — Replaceability Evidence Assessment
Synthesises RR historical contribution, recent global form, and career trajectory into a
structured replaceability assessment:
- **Evaluation criteria**:
  1. RR historical contribution depth and role centrality.
  2. Recent 2–3 year global form and trajectory.
  3. Age at evaluation date (`evaluation_date - date_of_birth`).
  4. Role importance and scarcity in modern T20 cricket.
  5. Role-specific metric performance against competition baselines.
  6. Sample size depth and consistency across tournaments.
  7. Availability and injury history.
  8. Data completeness and source quality scores.
- **Structured assessment signal states**:
  - `RETAIN_SIGNAL`: Strong recent performance, high role contribution, stable multi-season
    metrics; clear evidence against replacement.
  - `MONITOR_SIGNAL`: Mixed recent form, minor sample gaps, or role shifts requiring continued
    observation.
  - `POTENTIALLY_REPLACEABLE`: Declining multi-season performance, reduced availability,
    diminishing returns in key phases, or advanced age relative to role demands.
  - `INSUFFICIENT_EVIDENCE`: Observed sample size below minimum threshold or significant data gaps
    precluding confident evaluation.
  - `REVIEW_REQUIRED`: Materially conflicting source data, unverified injuries, or contradictory
    membership/eligibility status.
- **Non-Decision Rule**: These signal states are **analytical signals only**, not final
  recruitment decisions. PVRE does **not** independently decide to release, replace, or retain
  a player, and does **not** invent arbitrary thresholds or replacement probabilities. The
  complete evidence dossier and replaceability assessment are forwarded to **SICE** (§8.4) for
  comparative evaluation against eligible uncapped prospects.

### 9.4 Mode B: Verified Uncapped Candidate Intelligence
When the player is verified as non-RR (`NO_VERIFIED_RR_RELATIONSHIP`) and independently verified
as uncapped-eligible (`VERIFIED_ELIGIBLE`) under the target-season policy, PVRE executes Mode B.
It conducts a complete career discovery workflow:
1. **Identity & alias verification**: Canonical identity, official names, DOB, age as of the
   evaluation date, playing styles.
2. **Domestic career investigation**:
   - Ranji Trophy (multi-day red-ball foundation).
   - Syed Mushtaq Ali Trophy (SMAT - primary domestic T20 proving ground).
   - Vijay Hazare Trophy (VHT - domestic 50-over List A).
   - Duleep Trophy and other BCCI premier competitions.
   - Age-group competitions (BCCI Vinoo Mankad U19, Cooch Behar U19, Col CK Nayudu U23).
   - Other franchise leagues and authorised domestic leagues.
   - International appearances (any senior international appearance immediately disqualifies
     the candidate from uncapped status).
3. **Career metrics & role flexibility**:
   - Complete match-level and season-by-season batting, bowling, fielding, and keeping records.
   - Batting position distribution, bowling spell roles, phase effectiveness.
   - Career development trajectory, year-on-year metric improvements, consistency.
4. **Independent policy verification**: Enforces explicit rule-source citations and verification
   records under the active `eligibility_policies` version.
5. **Data lake reconciliation**: Distinguishes between internal database presence, external
   discovery, incomplete local coverage, verified uncapped candidate, capped player, and
   unverified candidate.
6. **Negative proof invariant**: **Absence from the database is NEVER proof of uncapped status.**
   No candidate enters the verified uncapped pool without affirmative verification.

### 9.5 Mandatory `REVIEW_REQUIRED` Safety Pathway
The `REVIEW_REQUIRED` state is a hard, non-bypassable safety requirement designed to prevent
automated decision errors and candidate pool pollution.

**Trigger conditions**:
1. Multiple plausible identities returned by PIRE without definitive disambiguation.
2. Conflicting dates of birth, nationality, or playing attributes across sources.
3. Contradictory RR relationship records (e.g. conflicting squad lists vs rosters).
4. Unverified or ambiguous target-season IPL eligibility.
5. Material disagreement between authoritative sources on performance statistics or team
   history.
6. External research fails to achieve the minimum corroboration threshold.
7. Data coverage is too incomplete to support replaceability or uncapped classification.
8. Authoritative source is restricted/unavailable and no verified secondary source exists.

**Structured review dossier contents**:
```json
{
  "review_status": "REVIEW_REQUIRED",
  "review_reason_codes": [
    "IDENTITY_AMBIGUITY",
    "DOB_CONFLICT",
    "INSUFFICIENT_GLOBAL_SAMPLE",
    "SOURCE_DISCREPANCY"
  ],
  "unresolved_claims": [
    {
      "claim_id": "CLM-2026-0891",
      "claim_type": "DATE_OF_BIRTH",
      "source_a": {"source_id": 1, "value": "2003-04-12"},
      "source_b": {"source_id": 10, "value": "2002-04-12"}
    }
  ],
  "conflicting_source_ids": [1, 10],
  "missing_evidence": [
    "SMAT_2024_BALL_BY_BALL_LOG",
    "OFFICIAL_BCCI_REGISTRATION_RECORD"
  ],
  "recommended_manual_checks": [
    "Verify state association birth registration certificate",
    "Inspect official match scorecard for SMAT 2024 fixture vs Delhi"
  ]
}
```
**Safety Invariants**:
- PVRE **never silently selects a mode** when a mandatory routing condition is unresolved.
- Unresolved eligibility or identity cases are **strictly blocked from entering the verified
  uncapped ranking pool**.

### 9.6 PVRE Request and Response Output Contracts

#### 9.6.1 Request Contract
```python
@dataclass(frozen=True)
class PVRERequestContract:
    contract_version: str            # e.g. "PVRE-2.2.0"
    player_query: str                # raw player name, alias, or known identifier
    target_season_id: UUID           # season UUID for eligibility (e.g. IPL 2027)
    evaluation_date: date            # reference date for age and window calculations
    research_window_years: int = 3   # configurable recent-form window (2 or 3 years)
    force_refresh: bool = False      # bypass cache to trigger authorised external research
```

#### 9.6.2 Response Contract (23 Minimum Fields)
```python
@dataclass(frozen=True)
class PVREOutputContract:
    # 1. Governance & Run Identification
    contract_version: str                      # "PVRE-2.2.0"
    research_run_id: UUID                      # unique UUIDv4 per execution run
    player_id: Optional[UUID]                  # canonical UUID from players table
    canonical_name: str                        # verified canonical player name
    identity_status: str                       # RESOLVED, PROVISIONAL, UNRESOLVED

    # 2. Routing & Mode Selection
    research_mode: str                         # MODE_A, MODE_B, REVIEW_REQUIRED, OUT_OF_SCOPE
    route_status: str                          # ROUTED_RR_INCUMBENT, ROUTED_UNCAPPED_CANDIDATE,
                                               # ROUTED_SAFETY_REVIEW, ROUTED_OUT_OF_SCOPE
    evaluation_date: date                      # effective date of evaluation
    target_season_id: UUID                     # target season evaluated

    # 3. Membership & Eligibility States
    rr_relationship_state: str                 # CURRENT_RR, HISTORICAL_RR_APPEARED,
                                               # HISTORICAL_RR_SQUAD_ONLY,
                                               # NO_VERIFIED_RR_RELATIONSHIP,
                                               # RR_RELATIONSHIP_UNKNOWN
    rr_current_state: str                      # CURRENT, NOT_CURRENT, UNKNOWN
    eligibility_status: str                    # VERIFIED_ELIGIBLE, VERIFIED_NOT_ELIGIBLE,
                                               # ELIGIBILITY_UNVERIFIED, NOT_ASSESSED

    # 4. Research Windows
    research_window_start: date                # evaluation_date - window_years
    research_window_end: date                  # evaluation_date

    # 5. Domain Profiles & Assessments
    rr_historical_profile: Optional[Dict]      # Module A1 outputs (squad vs XI, metrics, roles)
    recent_global_performance: Optional[Dict]  # Module A2 outputs (leagues, form, sample sizes)
    complete_career_profile: Optional[Dict]    # Module B outputs (domestic career, formats)
    replaceability_assessment: Optional[Dict]  # Module A3 outputs (signal, trajectory, rationale)

    # 6. Coverage, Provenance & Quality
    competition_coverage: Dict[str, str]       # competition_code -> VERIFIED / DATASET_UNAVAILABLE /
                                               # NOT_ESTABLISHED / CONFIRMED_NON_PARTICIPATION
    source_record_ids: List[int]               # FKs to source_records table
    verification_record_ids: List[int]         # FKs to verification_records table
    review_status: str                         # CLEAR, REVIEW_REQUIRED, REJECTED
    review_reason_codes: List[str]             # reason codes if review_status != CLEAR
    data_quality_summary: Dict                 # completeness score, missing attributes, flags
```

### 9.7 PVRE Guardrails
- **Zero statistical fabrication**: Missing metrics must be `NULL`, never 0.0 or imputed.
- **Absence is not proof**: Database absence never implies uncapped status; absence of RR records
  never implies non-membership without satisfying TRD §4.5 negative verification rules.
- **No release/retention decisions**: PVRE generates evidence and analytical signals; final squad
  decisions belong strictly to franchise leadership and SICE.
- **No arbitrary thresholds or probabilities**: Replaceability signals are based on documented
  criteria; recruitment probabilities are prohibited.
- **Preserve conflicting evidence**: Never overwrite conflicting records; preserve competing
  claims and trigger `REVIEW_REQUIRED`.

---

## 10. Support Services'''

text = text.replace(s9_target, pvre_section_text)

# 6. Renumber subsequent sections:
# Section 10 Support Services -> 10. Support Services (done by above)
# Replace subheadings in Support Services:
text = text.replace('### 9.1 Service A', '### 10.1 Service A')
text = text.replace('### 9.2 Service B', '### 10.2 Service B')
text = text.replace('### 9.3 Service C', '### 10.3 Service C')
text = text.replace('### 9.4 Service D', '### 10.4 Service D')
text = text.replace('### 9.5 Service E', '### 10.5 Service E')

# Renumber Section 10 Central PostgreSQL -> Section 11 Central PostgreSQL
text = text.replace('## 10. Central PostgreSQL 16 Database Schema (33 Entities)', '## 11. Central PostgreSQL 16 Database Schema (33 Entities)')
text = text.replace('### 10.1 Entity Domains', '### 11.1 Entity Domains')
text = text.replace('### 10.2 DDL Design Decisions (remediation)', '### 11.2 DDL Design Decisions (remediation)')
text = text.replace('### 10.3 Complete PostgreSQL 16 DDL', '### 11.3 Complete PostgreSQL 16 DDL')
text = text.replace('### 10.4 DDL Integrity Summary', '### 11.4 DDL Integrity Summary')

# Add Section 11.5 PVRE Schema Support & Greenfield Audit
pvre_schema_audit = '''### 11.5 PVRE Schema Support & Greenfield Audit (v2.2.0)
The existing **33-entity PostgreSQL 16 core** fully supports the PVRE dual-mode architecture,
research runs, and replaceability assessments without requiring additional tables or DDL
modifications:
1. **`source_records`**: Stores all raw external research extracts, competitive match files, and
   tournament data payloads across leagues (BBL, PSL, CPL, SA20, The Hundred, Ranji, SMAT).
2. **`verification_records`**: Stores claim-level verification records, provenance tiers, source
   citations, and explicit conflict logs (`verification_status = 'CONFLICT'`).
3. **`player_membership_state`**: Persists Dimension 1 (`rr_relationship_state`) and Dimension 2
   (`rr_current_state`) for routing and squad status tracking.
4. **`player_eligibility` & `eligibility_policies`**: Persists Dimension 3 season-specific
   eligibility assessments under active, versioned policy rules.
5. **`derived_features`**: Stores calculated multi-season performance rollups, recent-form
   weighted metrics, competition strength factors, and replaceability feature vectors
   (`feature_set_name = 'pvre_replacement_assessment'`).
6. **`ranking_runs`**: Persists durable, reproducible SICE squad-level evaluation runs and
   incumbent-vs-candidate replacement comparison boards (`run_type = 'REPLACEMENT_EVALUATION'`).

The database schema remains cleanly stabilized at **33 logical entities** with zero schema drift.'''

ddl_summary_end = text.find('## 11. Engine Determinism & LLM Independence')
assert ddl_summary_end != -1
text = text[:ddl_summary_end] + pvre_schema_audit + '\n\n---\n\n' + text[ddl_summary_end:]

# Renumber sections 11, 12, 13, 14
text = text.replace('## 11. Engine Determinism & LLM Independence', '## 12. Engine Determinism & LLM Independence')
text = text.replace('## 12. Streamlit Presentation Requirements', '## 13. Streamlit Presentation Requirements')
text = text.replace('### 12.1 Required Views', '### 13.1 Required Views')
text = text.replace('### 12.2 Session State Discipline', '### 13.2 Session State Discipline')
text = text.replace('### 12.3 Frontend-Agnostic Guarantee', '### 13.3 Frontend-Agnostic Guarantee')
text = text.replace('## 13. API / Service Specification (frontend-agnostic)', '## 14. API / Service Specification (frontend-agnostic)')
text = text.replace('## 14. Non-Functional Specifications', '## 15. Non-Functional Specifications')

with open('docs/TRD.md', 'w', encoding='utf-8', newline='\n') as f:
    f.write(text)

print('docs/TRD.md successfully updated and written!')
