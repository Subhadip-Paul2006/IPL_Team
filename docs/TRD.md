# Technical Requirements Document (TRD) & Central Database Schema
**Product**: RR Squad Intelligence & Team Composition Platform
**Focus Franchise**: Rajasthan Royals (RR) · **Primary Interface**: Streamlit (initial) · **Future Frontend**: Next.js
**Document Version**: 2.1.1-TARGETED-REMEDIATION
**Status**: [STATUS: PLANNED - GREENFIELD BASELINE]
**Author**: Engineering Architecture Team (`teamwork_worker_2`)

> **Revision Note (v2.1.1, targeted remediation)**: Corrects the cricket-statistics DDL
> and contracts left in v2.1.0 — decimal overs replaced by integer ball counts of record
> (D11); `deliveries.match_id` removed so delivery↔innings match identity is structural
> (D12); `chk_dnb` → `chk_dnb_zero` distinguishing DNB from zero-ball batted appearances
> (D13); `player_eligibility` policy-season integrity + verification-consistency CHECKs
> (D14); `team_season_participation` evidence-bound status rules (D15); the single
> three-group phase model; The Hundred as a first-class `HUNDRED` format
> (`competitions.balls_per_over = 5`); `CURRENT_RR_SQUAD` removed from Dimension 1
> (currency lives in Dimension 2); TMVE returns Dimensions 1–2 while the Eligibility
> Service returns Dimension 3 (Option B, MIE composes). Full register:
> `reports/DOCUMENTATION_REMEDIATION_AUDIT.md` §v2.1.1.
>
> **Revision Note (v2.1.0, remediation, retained for history)**: This revision corrected the v2.0.0 DDL (invalid
> expression UNIQUE constraint, missing partitioned-table FKs, soft delivery links, false-claim
> defaults, overs datatype), replaces the competition-level `seasons.is_suspension` model with a
> franchise-level **`team_season_participation`** entity, splits the six-class membership taxonomy
> into **three independent dimensions** (RR relationship · currency · IPL eligibility), adds
> versioned **eligibility policies**, revises PIRE terminology (contextual attribute
> corroboration, not "biometric") and confidence semantics, and gives CDCRE **two** capabilities
> (pre-identity candidate discovery + post-identity career retrieval) to remove the MIE circular
> dependency. Entity count: **31**. The metric dictionary now lives in
> [`docs/DATA_DICTIONARY.md`](DATA_DICTIONARY.md); the source register in
> [`docs/DATA_SOURCE_REGISTER.md`](DATA_SOURCE_REGISTER.md).

---

## 1. System Overview & Technical Architecture

> **Architecture Baseline Status**: `[STATUS: PLANNED - GREENFIELD BASELINE]`
> All schemas, database tables, partition schemes, mathematical models, engine contracts, and
> service interfaces represent the approved architectural specification for greenfield
> implementation. **Zero application code currently exists.**

The **RR Squad Intelligence & Team Composition Platform** is an evidence-backed decision-support
system for constructing and evaluating a Rajasthan Royals team. The primary workflow is:

1. A user creates a team.
2. The user enters a cricket player's name.
3. **Pre-identity candidate discovery** (CDCRE capability 1) gathers raw-name evidence.
4. The system identifies the player (**PIRE**), corroborated by discovered candidates;
   ambiguous identities go to **user clarification**.
5. The system checks whether the player exists in the internal database.
6. Where necessary, authorised external research discovers and verifies identity and history.
7. The system determines RR representation (**TMVE**) across the three independent dimensions.
8. It retrieves and analyses the player's complete cricket career (**CDCRE** capability 2).
9. It evaluates performance, contribution and role (**CPPAE**).
10. It presents an evidence-backed player profile (**MIE**).
11. The user adds the player to a team composition (**Team Builder Service**).
12. The Squad Intelligence Engine evaluates the complete team (**SICE**).

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     Presentation Tier (Streamlit - INITIAL)                  │
│   Team Builder · Player Search · Verification · Career · Analytics · SICE    │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ Structured responses (JSON)
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│          MOTHER INTELLIGENCE ENGINE (MIE) - Central Orchestrator            │
│   Accepts player search requests · coordinates engines · merges outputs ·   │
│   maintains identity consistency · tracks verification · source provenance │
└──────────┬──────────────────────────────┬───────────────────────────────────┘
           │ dispatches to engines         │
   ┌───────┴────────────┬──────────────────┼──────────────────┬───────────────┐
   ▼                    ▼                  ▼                  ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ ENGINE 01     │ │ ENGINE 02     │ │ ENGINE 03     │ │ ENGINE 04     │ │ ENGINES 05/06│
│ PIRE         │ │ TMVE         │ │ CDCRE        │ │ CPPAE        │ │ CMIE / SICE  │
│ Identity Res. │ │ Membership   │ │ Candidate +  │ │ Performance  │ │ Context/ Squad │
│              │ │ Verification  │ │ Career Disc. │ │              │ │              │
└──────┬───────┘ └──────┬───────┘ └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
       ▼                ▼                ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SUPPORT SERVICES                                          │
│  A. Data Ingestion · B. Player Profile Generator · C. Source Verification & │
│     Provenance · D. Data Quality & Coverage · E. Team Builder               │
└──────────────────────────────────────────────────────────────────────────────┘
                                              │ Read / derive (deterministic)
                                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│       Central PostgreSQL 16 Normalised Core (33 entities, 3NF core)          │
│   players, player_aliases, teams, competitions, seasons,                    │
│   team_season_participation, squad_memberships, player_team_history,        │
│   matches, innings, deliveries, batting_innings, bowling_spells,           │
│   fielding_events, wicketkeeping_events, venues, pitch_conditions,         │
│   weather_conditions, player_availability, player_injuries, player_awards, │
│   player_competition_history, player_membership_state, eligibility_policies,│
│   player_eligibility, user_teams, user_team_players, data_sources,         │
│   source_records, verification_records, derived_features                    │
└──────────────────────────────────────▲──────────────────────────────────────┘
                                       │ Batch ELT (immutable raw payloads)
┌──────────────────────────────────────┴──────────────────────────────────────┐
│  datasets/ (CricSheet) · Kaggle · HawkeyeStats · Historical Weather ·       │
│  Official Records · Verified Research (provenance-tracked)                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.1 Architectural Subsystems

1. **Presentation Tier (Streamlit, initial)**: Streamlit application exposing the 11 required
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
classes or Pydantic models) independent of any UI framework. Streamlit is the **initial**
consumer only; a future Next.js frontend reuses the identical contracts. No engine imports
Streamlit, React, or any UI runtime.

---

## 2. Mother Intelligence Engine (MIE) — Central Orchestrator

**ENGINE 00 — Mother Intelligence Engine (MIE)**

### 2.1 Responsibilities
- Accept player search requests (from Streamlit or any frontend-agnostic consumer).
- Coordinate the six specialised engines in the correct dependency order.
- Manage the player identification workflow end-to-end.
- Trigger internal database searches; trigger **authorised external research** when internal
  records are insufficient.
- Route records to the appropriate analytics modules.
- Merge engine outputs into a unified player intelligence report.
- Maintain player identity consistency (single canonical `player_id` per real-world person).
- Track verification status across identity, membership, eligibility, and career dimensions.
- Manage confidence and source provenance (via Support Service C).
- Produce unified, structured responses returned to the UI.

### 2.2 MIE Input / Output Contract
```
MIE.request_player_intelligence(name: str, team_id: Optional[UUID]) -> PlayerIntelligenceReport
PlayerIntelligenceReport {
    identity:       PIRE.Output            # resolved player_id + tier + evidence + warnings
    membership:     TMVE.Output            # Dimensions 1-2 (RR relationship + currency), independent states
    eligibility:    EligibilityOutput      # Dimension 3, from the Eligibility Service — season-bound,
                                           # policy-versioned (§4.4 Option B; §4.6); MIE composes the three
                                           # but never blends them into one label
    career:         CDCRE.Output           # competition history + coverage status
    performance:    CPPAE.Output           # batting/bowling/fielding/WK/match contribution
    context:        CMIE.Output            # environmental & match-condition annotations
    squad:          SICE.Output            # (only when a team_id is supplied)
    provenance:     List[SourceRecord]     # every external/derived claim traced to a source
    verification:   VerificationStatus     # aggregate status + human-review flags
}
```

### 2.3 Orchestration Sequence (revised — no circular dependency)
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
> never requires a canonical player ID; capability 2 operates only on resolved IDs.

### 2.4 MIE Guardrails
- MIE **never** fabricates statistics; every numeric value is derived by CPPAE, CMIE, or SICE
  from verified records.
- MIE **never** makes membership or eligibility decisions; it reports TMVE and
  `player_eligibility` states verbatim.
- Any `UNVERIFIED`/`UNKNOWN`/`CONFLICT` result is surfaced, never silently resolved.

---

## 3. ENGINE 01 — Player Identity Resolution Engine (PIRE)

**Purpose**: Resolve the actual identity of a player from a name supplied by the user.

### 3.1 Responsibilities
Exact-name matching · alias matching · name variations (abbreviations, expanded forms,
transliterations) · spelling variations · duplicate detection · disambiguation when multiple
players share a name · player ID resolution to canonical `player_id` · date-of-birth and
team/competition **contextual attribute corroboration** (these are cricketing/registry
attributes, **not** biometric identifiers).

### 3.2 Output Contract
```
PIRE.resolve(input_name, candidates) -> PIRE.Output {
    resolved_player_id:    Optional[UUID]
    canonical_name:        Optional[str]
    known_aliases:         List[str]
    identity_status:       'RESOLVED' | 'PROVISIONAL' | 'UNRESOLVED'
    resolution_tier:       1..4                # deterministic outcome, see §3.3
    matching_records:      List[SourceRecord]
    unresolved_warnings:   List[str]           # e.g. "two players share this name"
    requires_human_review: bool
}
```

### 3.3 Resolution Tiers (deterministic outcomes — not calibrated probabilities)
1. **Tier 1 — Canonical registry key**: exact CricSheet hex hash / BCCI / ESPN ID →
   `identity_status=RESOLVED`, tier 1.
2. **Tier 2 — Verified alias registry**: exact match in `player_aliases` with
   `is_verified=TRUE` → RESOLVED, tier 2.
3. **Tier 3 — Deterministic contextual intersection**: surname + initials + team + match
   window yielding exactly one candidate → RESOLVED, tier 3; alias inserted unverified.
4. **Tier 4 — Probabilistic fuzzy + contextual attribute corroboration**: Jaro-Winkler ≥ 0.92
   AND Levenshtein ≤ 2 as **tunable matching thresholds** against DOB/role/hand/active-era
   corroboration. Single corroborated candidate → PROVISIONAL (alias `is_verified=FALSE`);
   else UNRESOLVED, quarantined with `needs_review=TRUE`.

> **Confidence semantics (correction)**: the tier outcome is deterministic. The numeric
> thresholds above are **configuration parameters, not calibrated probabilities**. A numeric
> `identity_confidence` value is exposed **only** after the resolution model has been
> calibrated and validated against a labelled identity-resolution test set
> (`calibrated=TRUE` flag required; otherwise the field stays `NULL`).
> **Never merge two players merely because their names are similar** — ambiguity is routed to
> user clarification / human review, never auto-resolved.
> Identity confidence, membership verification confidence, career coverage completeness, and
> eligibility confidence are **separate measurements** reported by their respective engines;
> PIRE reports identity status only.

---

## 4. ENGINE 02 — Team Membership Verification Engine (TMVE)

**Purpose**: Verify whether a player represented Rajasthan Royals, distinguishing relationship
history, currency, and (independently) eligibility.

### 4.1 Responsibilities
- Search internal historical membership records (`squad_memberships`, `player_team_history`,
  `team_season_participation`).
- Verify **actual RR match appearances** (from `matches`/`deliveries`), distinct from squad
  inclusion.
- Identify RR seasons of representation using franchise participation: **RR 2008–2015**,
  **RR suspended 2016–2017** (IPL continued; other franchises unaffected), **RR returned
  2018–2026**, **IPL 2027 remains UNVERIFIED participation** until authoritative evidence
  exists.
  > **v2.1.1 evidence-status correction (Priority E)**: the *windows themselves* are a
  > documented model, not verified facts. Each `team_season_participation` row for
  > RR × IPL 2008–2026 is seeded **`UNVERIFIED`/`PENDING`** until claim-level evidence is
  > retrieved into `verification_records` (tier-1 BCCI suspension notice for 2016/17;
  > official squad lists / scorecards per window). The locally-corroborating CricSheet IPL
  > archive (RR fixtures present 2008–2015 & 2018–2026, **absent** 2016–2017; 2016/17
  > continue with 59–60 other-team fixtures) is **tier-4** database corroboration only —
  > it supports the model but does not by itself upgrade a row to `VERIFIED`. A single
  > source establishing one event (e.g. the 2016 suspension notice) does **not** verify
  > the whole 2008–2026 window. 2027 stays `UNKNOWN`/`UNVERIFIED` until official squad
  > publication.
- Identify other IPL teams and documented retention/auction/transfer/release facts.
- Verify current squad membership **separately** from historical membership.
- Perform **authorised external research** when internal records are insufficient.

### 4.2 Verification Hierarchy (evidence ranking)
1. Official IPL and franchise records · 2. Official match scorecards · 3. BCCI records ·
4. Reliable cricket databases · 5. Reputable secondary reporting.

### 4.3 Three Independent Membership/Eligibility Dimensions
These dimensions are stored in `player_membership_state` (relationship + currency) and
`player_eligibility` (eligibility, season-bound) and must **never be conflated** into one
label. A former RR player can simultaneously have a separately assessed uncapped-eligibility
state; a player unknown to the internal database is **never** auto-classified as uncapped.

#### Dimension 1 — RR relationship (`rr_relationship_state`)
> **v2.1.1 deduplication**: `CURRENT_RR_SQUAD` was removed from this dimension. It
> duplicated Dimension 2 (`rr_current_state = CURRENT`), which already expresses currency
> independently. A player's *current-squad* standing is read from Dimension 2, never from
> the relationship state. Dimension 1 therefore captures only the **nature of the
> verified RR association**, preserving the project's four intended distinctions —
> historical appearance · squad-only · previously associated · unknown — plus the
> documented negative-verified state:

| State | Definition |
|---|---|
| `HISTORICAL_RR_APPEARANCE` | Verified RR match appearance in a prior season (whether the player is also on the current squad is Dimension 2, not this state). |
| `HISTORICAL_RR_SQUAD_ONLY` | Verified RR squad inclusion without a confirmed appearance. |
| `PREVIOUSLY_ASSOCIATED` | Documented prior association (loan, brief squad, release) with evidence, no confirmed match. |
| `NO_VERIFIED_RR_RELATIONSHIP` | No verified relationship — **only** via the §4.5 negative-verification requirements. |
| `RR_RELATIONSHIP_UNKNOWN` | Insufficient evidence; must not be reported as "never played RR". |

#### Dimension 2 — Current membership verification (`rr_current_state`)
`CURRENT` · `NOT_CURRENT` · `UNKNOWN` — verified independently of relationship history.

#### Dimension 3 — IPL eligibility / uncapped classification (`eligibility_status`)
`VERIFIED_ELIGIBLE` · `VERIFIED_NOT_ELIGIBLE` · `ELIGIBILITY_UNVERIFIED` · `NOT_ASSESSED` —
always season-bound and policy-versioned (§4.6); `NOT_ASSESSED` is the default for any player
whose eligibility has not been independently verified.

### 4.4 Output Contract (three dimensions, composed by MIE — Option B, v2.1.1)

**Design decision (v2.1.1, documented)**: TMVE returns **Dimensions 1 and 2**
(RR relationship · current membership). **Dimension 3 (IPL/uncapped eligibility) is
returned by the Eligibility Service** against the active `eligibility_policies` version for
the target season, and **MIE composes all three** into the unified report. This keeps TMVE
franchise-scoped (it verifies RR representation; it does not own BCCI/IPL-wide eligibility
rules, which are versioned policy content) and removes the ambiguity where the TMVE output
contract previously described Dimensions 1–2 while the architecture asserted a third.

```
TMVE.verify(player_id, as_of_date) -> TMVE.Output {
    rr_relationship_state:   enum(Dimension 1, §4.3)
    rr_current_state:        enum(Dimension 2, §4.3)   # CURRENT / NOT_CURRENT / UNKNOWN
    rr_seasons:              List[str]       # verified RR seasons (2008-2015, 2018-2026 so far; 2027 unverified)
    other_ipl_teams:         List[str]
    verified_rr_appearances: int             # confirmed match count; 0 is a value, not "unknown"
    evidence:                List[SourceRecord]
    verification_date:       date
    membership_confidence:   Optional[float]  # NULL unless calibrated (see §3.3 semantics)
}

EligibilityService.assess(player_id, target_season_id) -> EligibilityOutput {
    eligibility_status:  enum(Dimension 3, §4.3)      # VERIFIED_ELIGIBLE / VERIFIED_NOT_ELIGIBLE /
                                                       # ELIGIBILITY_UNVERIFIED / NOT_ASSESSED
    policy_id:           UUID                          # active eligibility_policies version for the season
    policy_version:      int
    verified:            bool
    verification_id:     Optional[UUID]                # NULL unless a verified outcome
    evidence:            List[SourceRecord]
}

MIE composition (typed response, §2.2):
    report.membership = TMVE.Output                      # Dimensions 1-2
    report.eligibility = EligibilityService.assess(...)   # Dimension 3
    # MIE never blends the three into one label; each is surfaced independently.
```

**Database ownership**: Dimensions 1–2 → `player_membership_state` (TMVE writes);
Dimension 3 → `player_eligibility` + `eligibility_policies` (Eligibility Service writes).
**Verification responsibility**: TMVE performs §4.5 negative-verification for Dimension 1
and current-squad verification for Dimension 2; the Eligibility Service performs the
rule-source + independently-verified assessment for Dimension 3. **Evidence provenance**:
every state cites `verification_records` rows (Service C). **Error / conflict states**:
each dimension carries its own `UNKNOWN` / `ELIGIBILITY_UNVERIFIED` / `NOT_ASSESSED` /
`CONFLICT` values independently; a conflict in one dimension does not propagate to the
others, and CONFLICT always routes to human review (AI_INSTRUCTIONS §4.3). **Tests /
acceptance criteria**: AC-04 (three dimensions stored/returned independently), AC-08
(negative-verification gate), AC-09 (eligibility rows always reference a policy version;
unknowns default `NOT_ASSESSED`), and the new AC-24 (eligibility season derived from the
policy, never a redundant independent season_id).

### 4.5 Negative Membership Verification Requirements
A player may be classified `NO_VERIFIED_RR_RELATIONSHIP` **only** when all of the following
are satisfied (documented per player in `verification_records`):
1. **Historical coverage scope**: verified squad-list coverage exists for every RR season in
   scope (2008–2015, 2018–2026 verified; 2027 requires official squad publication).
2. **Relevant RR seasons**: the player's active career window overlaps the in-scope seasons
   (a player debuting in 2024 is not "verified absent" in 2009).
3. **Squad-list coverage**: official/authoritative squad lists for in-scope seasons have been
   consulted; absence from *one* dataset or *one* search engine is **not** proof of
   non-membership.
4. **Scorecard coverage**: verified absence from RR match records in the covered window.
5. **Source quality**: at least one tier-1/2 source (official records or official scorecards).
6. **Conflicting evidence handling**: any single contradicting record forces
   `RR_RELATIONSHIP_UNKNOWN` and routes to human review.
7. **Human-review requirement**: negative classifications are always human-reviewed before
   publication.
If the evidence base is incomplete, return `RR_RELATIONSHIP_UNKNOWN`, never a negative.

### 4.6 Eligibility Policy (versioned)
Uncapped-player eligibility rules are **not** hardcoded. They are represented as
`eligibility_policies` rows: season-specific, versioned, traceable to the official IPL/BCCI
rule reference (`rule_source`), independently verified (`verified=TRUE` + verification record),
and effective-date aware (`effective_date`/`expiry_date`). `player_eligibility` rows always
carry `policy_id`.

### 4.7 TMVE Guardrails
- **Squad inclusion ≠ match appearance**; **historical membership ≠ current membership**.
- The RR 2016–2017 suspension is a **franchise participation state**
  (`team_season_participation.participation_status='SUSPENDED'`), not a competition-level
  property: IPL 2016/2017 seasons exist with all other franchises `PARTICIPATING`.
- **IPL 2027 is a future target season**: RR's 2027 participation row is `UNKNOWN` until
  authoritative squad/participation evidence is verified.
- **v2.1.1 (Priority E) — verification-status honesty**: every `team_season_participation`
  row is `PENDING`/`UNVERIFIED` on seeding and may only become `VERIFIED` when a
  `verification_records` row (tier 1–5) is cited (DDL `chk_tsp_verified_evidence`). The
  roadmap and DDL comments describing RR 2008–2015 / 2016–17 / 2018–2026 windows are
  **model statements, not verified evidence**; they do not substitute for retrieval.
  Local CricSheet archive corroboration (RR fixtures present 2008–2015 & 2018–2026,
  absent 2016–2017) is recorded as tier-4 supporting evidence, not tier-1.

---

## 5. ENGINE 03 — Career Discovery & Competition Research Engine (CDCRE)

**Purpose**: Discover a player's complete available cricket career **beyond RR**.

### 5.1 Two Capabilities (resolves the MIE circular dependency)
1. **`discover_candidates(raw_name)` — pre-identity**: given a raw name string (no canonical
   `player_id`), gather candidate records and corroborating evidence from internal aliases and
   authorised external research; returns candidates + per-source provenance. Feeds PIRE.
2. **`discover_career(player_id)` — post-identity**: given a canonical `player_id`, retrieve the
   complete verified career across competitions with four-state coverage.

### 5.2 Competitions Investigated
Previous IPL franchises · domestic state teams · Ranji Trophy · Syed Mushtaq Ali Trophy · Vijay
Hazare Trophy · Duleep Trophy · India A and age-group cricket · international cricket · other
recognised T20 leagues · **The Hundred (England/Wales, 5-ball-over T20 variant)** · other
verified competitions. **Local data note**: SMAT is
`DATASET_UNAVAILABLE` in the current local lake (see `docs/DATA_SOURCE_REGISTER.md`);
discovery of SMAT participation requires external research and is provenance-tracked.
The Hundred local archive (`datasets/hnd_male_json`, 201 files, CricSheet, ODC-By) is a
first-class ingestion source — but its metrics stay `DEFERRED` until the
`balls_per_over = 5` handling is validated (Priority B, DATA_DICTIONARY §5).

### 5.3 Responsibilities
Discover competitions and team history · retrieve available statistics · identify season
participation and career gaps · track data coverage · record provenance for every external claim.

### 5.4 Output Contracts
```
CDCRE.discover_candidates(raw_name) -> CDCRE.CandidateOutput {
    candidates:  List[{name_variants[], team_hints[], season_hints[], source_records[], reliability}]
    ambiguity:   'NONE' | 'SINGLE_CORROBORATED' | 'MULTIPLE'
}

CDCRE.discover_career(player_id) -> CDCRE.Output {
    competitions:  List[{competition, seasons[], verified_appearances, stats, coverage_status}]
    career_gaps:   List[str]
    data_coverage: {verified: [...], dataset_unavailable: [...], not_established: [...],
                    confirmed_non_participation: [...]}
    provenance:    List[SourceRecord]
}
```

### 5.5 CDCRE Guardrails
- **Do not assume** a player absent from a dataset never played that competition.
- Four coverage states, used explicitly: *verified participation* · *dataset coverage
  unavailable* · *participation not established* · *confirmed non-participation*.
- External research follows the §4.2 hierarchy; every claim lands in `verification_records`.

---

## 6. ENGINE 04 — Complete Player Performance Analytics Engine (CPPAE)

**Purpose**: Generate a comprehensive, evidence-backed performance profile.

**Every metric produced by CPPAE is defined in [`docs/DATA_DICTIONARY.md`](DATA_DICTIONARY.md)
with its formula, numerator/denominator, source fields, exclusions, format restrictions, phase
rules, null handling, minimum sample, and observed/derived/model-inferred class.** No metric
exists outside that dictionary.

### 6.1 Metric Families
- **Batting**: matches · innings · runs · average · strike rate · balls faced · boundaries ·
  boundary % · dot-ball % · batting position · position-specific splits · opening/
  top-order/middle-order/finishing · vs individual bowlers · vs pace/spin · vs bowling style
  and verified delivery variations · powerplay/middle/death splits · win/loss splits ·
  partnership contributions.
- **Bowling**: overs (ball count of record: integer legal balls; over notation derived) ·
  runs conceded · wickets · economy · average · bowling strike rate · dot % · phase splits ·
  batter-specific matchups · pace/spin classification · delivery speed and line/length
  **where available** (`NULL` when unrecorded).
- **Fielding**: catches · run-outs · stumpings · recorded dropped catches (recorded only;
  absence from a scorecard ≠ 0) · boundary saves (recorded only) · opportunities · positions
  where verified · contribution measures.
- **Wicketkeeping**: dismissals · catches · stumpings · recorded missed chances (recorded
  only) · appearances.
- **Match contribution**: POTM awards (**an input signal, not a measure of total impact**) ·
  participation · batting/bowling contribution · match situation · win/loss performance ·
  measurable high-leverage contribution (leverage situations measured from state data, never
  inferred mental state).

### 6.2 Statistical Guardrails
- **Format-aware only**: IPL/T20, List A, and first-class statistics are never mixed without
  explicit `format_tag` and documented normalisation.
- **No zero-imputation**: missing → `NULL`; a player who did not bowl has a `NULL` economy.
- **No false-shot frequency**: no available source records false shots; the metric is
  `NOT_COMPUTABLE_FROM_AVAILABLE_SOURCES` in the dictionary and is never estimated.
- **Sample-size visibility**: every metric response includes the underlying sample counts
  (matches/balls faced/overs) so tiny and large samples are always distinguishable.
- **Super Over isolation** and **DLS normalisation** per `docs/AI_INSTRUCTIONS.md`.

### 6.3 Output Contract
```
CPPAE.analyse(player_id, formats=[...], window="career") -> CPPAE.Output {
    batting: {...}, bowling: {...}, fielding: {...}, wicketkeeping: {...},
    match_contribution: {...},
    samples:   {matches, innings, balls_faced, legal_balls_bowled, ...},
    per_stat:  {name: {value, definition_ref, formula, source_fields, format_tag,
                       null_reason?, status='OBSERVED'|'DERIVED'|'MODEL_INFERRED'}}
}
```

---

## 7. ENGINE 05 — Contextual Match Intelligence Engine (CMIE)

**Purpose**: Understand the environmental and match conditions in which a player performed,
separating measured, reported, estimated, inferred, and unknown information.

### 7.1 Analysed Conditions
Opposition · opposing batter/bowler · bowling style · delivery variations · delivery speed ·
line and length · venue · **pitch: surface description, soil type, grass coverage, reported
moisture/pace/bounce/spin, dry/damp/worn condition, preparation notes — original source
description preserved**; numerical pitch ratings are produced **only** when a validated
annotation methodology version exists (`ratings_methodology_version` set), otherwise `NULL`.
**Weather: ambient context only** — temperature, RH, dew point, wind, rainfall, cloud cover,
observation timestamp, venue coordinates, local timezone, provider, and the
spatial/temporal matching method are all recorded; weather is never presented as a direct
pitch measurement. Match format · innings · phase · required run rate · target · result.

### 7.2 Output Contract
```
CMIE.contextualise(player_id) -> CMIE.Output {
    match_contexts: List[{match_id, opposition, venue, pitch{...}, weather{...},
                          phase, rrr, target, result, provenance_tiers[]}]
}
```

### 7.3 CMIE Guardrails
- **Five provenance tiers** per datum: directly measured · officially reported · third-party
  estimate · model-inferred · unknown.
- Qualitative pitch reports are **preserved as text**; auto-numeric rating without a
  validated methodology is prohibited.
- **Player availability/injury data**: only publicly verified, legitimately accessible
  information; no private medical data; no unvalidated recurrence probabilities
  (`recurrence_risk_score` is `MODEL_INFERRED` and NULL until validated; unverified injuries
  stay `verified=FALSE`).
- **Never infer a player's mental state from match statistics.**

---

## 8. ENGINE 06 — Squad Intelligence & Composition Engine (SICE)

**Purpose**: Evaluate the team assembled by the user.

### 8.1 Responsibilities
Role analysis · batting depth · bowling depth · pace/spin balance · wicketkeeping options ·
all-rounder availability · batting-order flexibility · role duplication · weak/missing roles ·
historical contribution analysis · comparisons of similar-role players · replacement
identification · current-squad vs new-candidate comparison · squad-combination evaluation.

### 8.2 Output Contract
```
SICE.evaluate(team_id) -> SICE.Output {
    squad_overview, role_distribution, strengths[], weaknesses[],
    dependency_analysis, recruitment_priorities[], alternative_combinations[],
    recommendations: List[{statement, evidence[], confidence, label='ANALYTICAL_RECOMMENDATION'}]
}
```

### 8.3 SICE Guardrails
- Recommendations are labelled **analytical** — never official RR selections or auction decisions.
- **No recruitment probabilities** unless the underlying model is statistically validated and
  calibrated (`calibrated=TRUE`).

---

## 9. Support Services

### 9.1 Service A — Data Ingestion Service
Imports CricSheet (`datasets/`), Kaggle, HawkeyeStats, historical weather, official records,
and verified research data. Immutable raw staging (SHA-256), quarantining of malformed
payloads without halting the run. Dataset availability and licences are governed by
`docs/DATA_SOURCE_REGISTER.md` (statuses VERIFIED/PARTIALLY_VERIFIED/UNVERIFIED/UNAVAILABLE/
RESTRICTED). **Known local gap: no SMAT archive present.**

### 9.2 Service B — Player Profile Generator
Standardised **JSON/CSV** exports from the central database for a canonical `player_id`,
embedding ODC-By/CC-BY attribution. Public exports never contain proprietary hackathon
dataset content.

### 9.3 Service C — Source Verification & Provenance Service
For every external/derived claim: source URL · provider · retrieval timestamp · licence ·
verification status · confidence (only when calibrated) · original source record ID
(`verification_records`).

### 9.4 Service D — Data Quality & Coverage Service
Detects missing data · duplicates · conflicting statistics · invalid player associations ·
inconsistent match identities (including **innings↔delivery consistency** checks: delivery
counts and innings↔delivery aggregates reconcile to `deliveries` per innings; the
delivery↔innings match-key invariant is now **structural** (C4: `match_id` is derived, not
stored) so no cross-table match-identity check is required) · unavailable contextual
features. Emits coverage states consumed by CDCRE/TMVE.

### 9.5 Service E — Team Builder Service
User team lifecycle: create, add/remove players, composition, role and batting-order
assignment, saved configurations (`user_teams`, `user_team_players`).

---

## 10. Central PostgreSQL 16 Database Schema (33 Entities)

Canonical `player_id` is the single join key across engines. Raw (`source_records`),
normalised, and derived (`derived_features`) layers are strictly segregated. **33 logical
entities** — the v2.1.0 baseline was 31 (adding `team_season_participation`,
`player_membership_state`, `player_eligibility`, `eligibility_policies` and removing the
competition-level suspension flag); **v2.1.1 adds 2 more** (`ranking_configurations`,
`ranking_runs`, Priority F) to hold the versioned, reproducible Top-10 ranking method and
its durable run records.

### 10.1 Entity Domains
```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 1. INGESTION & PROVENANCE : data_sources, source_records, verification_records │
│ 2. CORE IDENTITY          : players, player_aliases                             │
│ 3. TEAMS & COMPETITIONS   : teams, venues, competitions, seasons,              │
│                             team_season_participation, squad_memberships,      │
│                             player_team_history                                 │
│ 4. MATCHES & CONDITIONS   : matches, pitch_conditions, weather_conditions      │
│ 5. GRANULAR CRICKET CORE  : innings, deliveries (partitioned)                  │
│ 6. SCORECARDS & FIELDING  : batting_innings, bowling_spells, fielding_events,  │
│                             wicketkeeping_events                                │
│ 7. CAREER & ELIGIBILITY   : player_competition_history, player_awards,         │
│                             player_availability, player_injuries,              │
│                             player_membership_state, eligibility_policies,    │
│                             player_eligibility                                 │
│ 8. USER TEAM COMPOSITION  : user_teams, user_team_players                       │
│ 9. FEATURE STORE          : derived_features                                    │
│ 10. RANKING (v2.1.1)      : ranking_configurations, ranking_runs                │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 10.2 DDL Design Decisions (remediation)
| # | Decision | Rationale |
|---|---|---|
| D1 | `derived_features`: table UNIQUE constraint **removed**; replaced by a **unique expression index** `UNIQUE (player_id, feature_name, calculation_window, model_version, COALESCE(format_tag,''))` | PostgreSQL forbids expressions inside table-level UNIQUE constraints; expression indexes are the native mechanism and avoid a redundant mutable key column. |
| D2 | `deliveries`: real FKs on `innings_id`, `batter_id`, `bowler_id`, `non_striker_id`, `player_out_id` (nullable). `match_id` is **not stored** — it is derived through `innings_id → innings.match_id` (C4), so a delivery cannot reference a different match from its innings. | Referential integrity. Target PostgreSQL 16 enforces FKs on partitioned referencing tables (supported since PG 15; load order: matches → innings → deliveries, FKs non-deferrable; on pre-15 engines these become enforced-by-check constraints — Phase 2 gate). Composite PK already includes the partition key `season_year`. Match-scoped delivery access goes through `deliveries.innings_id → innings.match_id` (index `idx_deliveries_innings`). |
| D3 | `fielding_events`: `delivery_id` optional, integrity preserved via composite `(delivery_id, season_year)` FK to `deliveries(delivery_id, season_year)` + CHECK (both-or-none); partial unique index on (delivery, season_year, player_id, event_type) where delivery is present | Optional relationship stays optional but valid; NULL delivery links are recorded provenance (scorecard-level events without ball ids). |
| D4 | `team_season_participation` replaces `seasons.is_suspension` | The RR 2016–17 suspension is franchise-specific; IPL continued for other teams. |
| D5 | Membership split into `player_membership_state` + `player_eligibility` + `eligibility_policies` | Relationship, currency, and eligibility are independent dimensions (Part 4.2/4.4). |
| D6 | `bowling_spells`: integer ball counts are the units of record; cricket over notation is a display derivation (`floor(balls/6)` and `balls % 6`); `overs_completed NUMERIC(4,1)` dropped | Decimal overs are ambiguous (13.4 ≠ 13+4/6); display formatting must never round-derive facts. |
| D7 | `deliveries.runs_batter` cap 0..6 **removed** (non-negative check only); `runs_total` unrestricted non-negative | Overthrow sequences make total runs per delivery legally exceed 6; `runs_batter > 6` is flagged for DQ review rather than rejected. |
| D8 | False-claim defaults removed: `national_board_noc_status` nullable (no default), `batting_innings.is_not_out` NOT NULL with no default, `wicketkeeping_events.appearances` NOT NULL with no default, `player_availability.availability_status` nullable | Unknowns must stay unknown (NULL) or be set explicitly from data, never defaulted into a fact. |
| D9 | `deliveries.source_record_id` (nullable FK) | Ball-level provenance mapping to the ingesting raw record. |
| D10 | `weather_conditions` gains timezone + spatial/temporal matching method columns; `pitch_conditions` gains `reported_description` + `ratings_methodology_version` | Measured-vs-reported separation (Part 7). |
| **D11 (v2.1.1)** | `innings.overs_allocated`/`target_overs` → integer `overs_allocated_balls`/`target_overs_balls`; `matches.overs_scheduled` → `innings_balls_scheduled` | C5: integer balls are the source of truth; over notation is display-derived from `competitions.balls_per_over`; DLS stores revised target in integer balls; avoids 13.4 overs ≠ 13+4/6 ambiguity. |
| **D12 (v2.1.1)** | `deliveries.match_id` **removed**; match access is derived via `innings_id → innings.match_id`; index `idx_deliveries_innings` replaces the match+innings index | C4: a delivery can no longer reference a different match from its innings (structural integrity, partition-compatible); the cross-table Service D match-identity invariant is retired. |
| **D13 (v2.1.1)** | `batting_innings.chk_dnb` → `chk_dnb_zero` (`NOT (did_not_bat = TRUE AND balls_faced > 0)`) | A3: DNB must face 0 balls; a batted appearance may legitimately face 0 (walkover/timed-out) without being fabricated as DNB or as a not-out innings. |
| **D14 (v2.1.1)** | `player_eligibility.season_id` removed; uniqueness on `(player_id, policy_id)`; eligibility status CHECKs require cited evidence for `VERIFIED_*` | C1/C2: policy-season pairing is structurally enforced (season derives from the policy, removing the 3NF transitive dependence and cross-season policy references); contradictory verified/flag states are now DDL-rejected. |
| **D15 (v2.1.1)** | `team_season_participation.verification_id` added; `chk_tsp_verified_evidence` + `chk_tsp_status_consistency` enforced; `squad_memberships.is_active_squad` made nullable (no default) | C3/C6 + Priority E: no participation row may be VERIFIED without a cited `verification_records` row; UNKNOWN rows stay PENDING/UNVERIFIED; no defaulted false-claim of active-squad status. |
| **D16 (v2.1.1)** | New **`ranking_configurations`** table: full versioned Top-10 method config (target season · policy gate · evaluation date · role groups · gate thresholds · ordering keys · tiebreakers · seed), `verified` evidence-bound | Priority F: the ranking is a durable, versioned model configuration, not an inline constant and not `derived_features.model_version` alone. |
| **D17 (v2.1.1)** | New **`ranking_runs`** table: one row per `(config_id, data_snapshot_sha256)` storing the candidate pool + Top-10 + reserves | Priority F: same inputs → exactly one stored, reproducible, auditable board (AC-18 / AC-25). Entity count 31 → **33**. |

### 10.3 Complete PostgreSQL 16 DDL

```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "btree_gist";

-- ============================================================================
-- 1. data_sources
-- ============================================================================
CREATE TABLE data_sources (
    source_id        UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_name      VARCHAR(100) NOT NULL UNIQUE,
    source_type      VARCHAR(50) NOT NULL CHECK (source_type IN (
        'JSON Feed','CSV Archive','REST API','Web Scraping / Official Feed','Manual Ingestion','External Research')),
    base_url         VARCHAR(255),
    license_type     VARCHAR(50) NOT NULL,
    license_status   VARCHAR(20) NOT NULL DEFAULT 'UNVERIFIED'
        CHECK (license_status IN ('VERIFIED','PARTIALLY_VERIFIED','UNVERIFIED','UNAVAILABLE','RESTRICTED')),
    license_evidence TEXT,                       -- where the licence status was established
    update_cadence   VARCHAR(30) NOT NULL,
    data_steward     VARCHAR(100) NOT NULL,
    is_active        BOOLEAN NOT NULL DEFAULT TRUE,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 2. source_records (immutable raw staging)
-- ============================================================================
CREATE TABLE source_records (
    record_id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id            UUID NOT NULL REFERENCES data_sources(source_id) ON DELETE RESTRICT,
    external_entity_id   VARCHAR(100) NOT NULL,  -- provider-native ID, e.g. CricSheet match id
    raw_payload          JSONB NOT NULL,
    payload_sha256       CHAR(64) NOT NULL,
    ingestion_timestamp  TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    processing_status    VARCHAR(30) NOT NULL DEFAULT 'Pending'
        CHECK (processing_status IN ('Pending','Parsed','Normalized','Failed','Quarantined')),
    error_message        TEXT,
    parsed_entity_type   VARCHAR(50),
    core_record_id       UUID,
    CONSTRAINT uq_source_payload_hash UNIQUE (source_id, external_entity_id, payload_sha256)
);
CREATE INDEX idx_source_records_status ON source_records(processing_status);
CREATE INDEX idx_source_records_external_id ON source_records(source_id, external_entity_id);

-- ============================================================================
-- 2b. verification_records (Service C)
-- ============================================================================
CREATE TABLE verification_records (
    verification_id  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    subject_type     VARCHAR(30) NOT NULL CHECK (subject_type IN
        ('player_identity','player_membership','player_eligibility','career_participation','source_record','team_participation')),
    subject_id       UUID NOT NULL,
    source_record_id UUID REFERENCES source_records(record_id) ON DELETE SET NULL,
    data_source_id   UUID REFERENCES data_sources(source_id) ON DELETE SET NULL,
    source_url       VARCHAR(500),
    source_provider  VARCHAR(100),
    evidence_tier    SMALLINT CHECK (evidence_tier BETWEEN 1 AND 5),
    retrieval_ts     TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    license          VARCHAR(80),
    verification_status VARCHAR(30) NOT NULL DEFAULT 'PENDING'
        CHECK (verification_status IN ('PENDING','VERIFIED','UNVERIFIED','CONFLICT')),
    confidence       NUMERIC(4,3) CHECK (confidence BETWEEN 0.000 AND 1.000),
    original_source_record_id VARCHAR(100),
    notes            TEXT,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_verification_subject ON verification_records(subject_type, subject_id);

-- ============================================================================
-- 3. players (canonical master registry)
-- ============================================================================
CREATE TABLE players (
    player_id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    canonical_name     VARCHAR(100) NOT NULL,
    full_name          VARCHAR(150),
    date_of_birth      DATE,
    nationality        VARCHAR(50) NOT NULL,
    primary_role       VARCHAR(30) NOT NULL CHECK (primary_role IN (
        'Top-order Batter','Middle-order Batter','Wicketkeeper Batter',
        'Batting All-rounder','Bowling All-rounder','Pace Bowler','Spin Bowler','Wicketkeeper')),
    batting_hand       VARCHAR(10) CHECK (batting_hand IN ('Right','Left')),
    bowling_arm        VARCHAR(10) CHECK (bowling_arm IN ('Right','Left')),
    bowling_style      VARCHAR(50),  -- registered physical style; NEVER a delivery variation
    cricsheet_id       VARCHAR(50) UNIQUE,
    bcci_id            VARCHAR(50) UNIQUE,
    espn_id            VARCHAR(50) UNIQUE,
    identity_status    VARCHAR(20) NOT NULL DEFAULT 'UNRESOLVED'
        CHECK (identity_status IN ('UNRESOLVED','PROVISIONAL','RESOLVED')),
    is_active          BOOLEAN NOT NULL DEFAULT TRUE,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_players_canonical_name ON players(canonical_name);
CREATE INDEX idx_players_cricsheet_id ON players(cricsheet_id) WHERE cricsheet_id IS NOT NULL;

-- ============================================================================
-- 4. player_aliases
-- ============================================================================
CREATE TABLE player_aliases (
    alias_id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    player_id        UUID NOT NULL REFERENCES players(player_id) ON DELETE CASCADE,
    alias_name       VARCHAR(100) NOT NULL,
    source_id        UUID NOT NULL REFERENCES data_sources(source_id) ON DELETE RESTRICT,
    match_threshold_met BOOLEAN NOT NULL DEFAULT FALSE,  -- deterministic tier outcome, not a probability
    is_verified      BOOLEAN NOT NULL DEFAULT FALSE,
    needs_review     BOOLEAN NOT NULL DEFAULT FALSE,
    verified_by      VARCHAR(50),
    verified_at      TIMESTAMPTZ,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_alias_source UNIQUE (alias_name, source_id)
);
CREATE INDEX idx_player_aliases_name ON player_aliases(alias_name);
CREATE INDEX idx_player_aliases_review ON player_aliases(needs_review) WHERE needs_review IS TRUE;

-- ============================================================================
-- 4b. venues (before teams/matches, which reference it)
-- ============================================================================
CREATE TABLE venues (
    venue_id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    stadium_name        VARCHAR(150) NOT NULL,
    city                VARCHAR(100) NOT NULL,
    country             VARCHAR(50) NOT NULL,
    cricsheet_venue_id  VARCHAR(50) UNIQUE,
    latitude             NUMERIC(9,6),
    longitude            NUMERIC(9,6),
    elevation_meters     NUMERIC(6,2),
    boundary_size_offside  NUMERIC(5,2),
    boundary_size_legside  NUMERIC(5,2),
    boundary_size_straight NUMERIC(5,2),
    pitch_type_default   VARCHAR(50),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_venue_name_city UNIQUE (stadium_name, city)
);
CREATE INDEX idx_venues_city ON venues(city);

-- ============================================================================
-- 5. teams
-- ============================================================================
CREATE TABLE teams (
    team_id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    team_name       VARCHAR(100) NOT NULL UNIQUE,
    short_code      VARCHAR(10) NOT NULL UNIQUE,
    home_venue_id   UUID REFERENCES venues(venue_id) ON DELETE SET NULL,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_teams_short_code ON teams(short_code);

-- ============================================================================
-- 6. competitions
-- ============================================================================
CREATE TABLE competitions (
    competition_id   UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name             VARCHAR(100) NOT NULL UNIQUE,
    competition_type VARCHAR(30) NOT NULL CHECK (competition_type IN (
        'Domestic Franchise T20','Domestic T20','International T20','Domestic List A','ODI','First Class','Other')),
    governing_body   VARCHAR(50) NOT NULL,
    country          VARCHAR(50) NOT NULL,
    -- B / format model: the two fields below are the SINGLE source of truth for the
    -- format's ball/over conventions. Every downstream calculation (over display
    -- notation, economy W06, phase boundaries) reads these, never a hard-coded 6.
    match_overs      INT NOT NULL DEFAULT 20 CHECK (match_overs > 0),
        -- The Hundred: match_overs = 20, balls_per_over = 5  (100-ball innings).
    balls_per_over   INT NOT NULL DEFAULT 6 CHECK (balls_per_over IN (4,5,6)),
        -- 6 = T20/ODI/List A/FC; 5 = The Hundred; 4 = reserved (non-standard).
    created_at       TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_bpo_sane CHECK (balls_per_over BETWEEN 2 AND 8)
);
-- Priority B: a The Hundred competition row is seeded `balls_per_over = 5`
-- (`info.balls_per_over` in the local hnd_male_json archive confirms 5). The HUNDRED
-- format_tag is mandatory on every The-Hundred metric; it never inherits six-ball
-- economy / over-notation / phase maths. See DATA_DICTIONARY §5.

-- ============================================================================
-- 7. seasons (competition editions; competition-wide, NOT franchise-specific)
--    NOTE: franchise-level participation (incl. RR 2016-17 suspension) lives in
--    team_season_participation. No competition-level suspension flag exists.
-- ============================================================================
CREATE TABLE seasons (
    season_id      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    competition_id UUID NOT NULL REFERENCES competitions(competition_id) ON DELETE CASCADE,
    season_year    VARCHAR(20) NOT NULL,
    start_date     DATE NOT NULL,
    end_date       DATE NOT NULL,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_season_comp UNIQUE (competition_id, season_year),
    CONSTRAINT chk_season_dates CHECK (end_date >= start_date)
);
CREATE INDEX idx_seasons_competition ON seasons(competition_id);

-- ============================================================================
-- 8. team_season_participation (franchise-level; corrects the old is_suspension model)
-- ============================================================================
CREATE TABLE team_season_participation (
    participation_id     UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    team_id              UUID NOT NULL REFERENCES teams(team_id) ON DELETE CASCADE,
    season_id            UUID NOT NULL REFERENCES seasons(season_id) ON DELETE CASCADE,
    participation_status VARCHAR(20) NOT NULL CHECK (participation_status IN
        ('PARTICIPATING','SUSPENDED','NOT_ENTERED','UNKNOWN')),
    effective_start_date DATE,
    effective_end_date   DATE,
    evidence_source_id   UUID REFERENCES data_sources(source_id) ON DELETE SET NULL,
    verification_id      UUID REFERENCES verification_records(verification_id) ON DELETE SET NULL,
        -- C3: the authoritative evidence row for this participation claim (Service C).
    verification_status  VARCHAR(20) NOT NULL DEFAULT 'UNVERIFIED'
        CHECK (verification_status IN ('PENDING','VERIFIED','UNVERIFIED','CONFLICT')),
    notes                TEXT,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_team_season_participation UNIQUE (team_id, season_id),
    CONSTRAINT chk_tsp_dates CHECK (effective_end_date IS NULL OR effective_start_date IS NULL OR effective_end_date >= effective_start_date),
    -- C3: a row may be VERIFIED only when a supporting verification record is cited.
    --    (Roadmap/documentation assumption of a historical fact is NOT verification
    --    evidence — it is a PENDING/UNVERIFIED row until retrieval lands.)
    CONSTRAINT chk_tsp_verified_evidence CHECK
        (NOT (verification_status = 'VERIFIED' AND verification_id IS NULL)),
    -- C3: status/consistency rules per value combination (documented, enforced):
    --   UNKNOWN participation  -> PENDING or UNVERIFIED only (a row that asserts nothing
    --     cannot be VERIFIED; a CONFLICT implies asserted, contradicting claims).
    --   PARTICIPATING/SUSPENDED/NOT_ENTERED (positive claims) -> PENDING (evidence
    --     outstanding), VERIFIED (with cited verification record, per
    --     chk_tsp_verified_evidence), or CONFLICT (contradicting sources; human review).
    --   UNVERIFIED on a positive claim means "investigated, not established" -> demote the
    --     participation_status to UNKNOWN instead; enforced by this CHECK.
    CONSTRAINT chk_tsp_status_consistency CHECK
        ((participation_status = 'UNKNOWN' AND verification_status IN ('PENDING','UNVERIFIED'))
         OR (participation_status IN ('PARTICIPATING','SUSPENDED','NOT_ENTERED')
             AND verification_status IN ('PENDING','VERIFIED','CONFLICT')))
);
CREATE INDEX idx_tsp_team ON team_season_participation(team_id);
CREATE INDEX idx_tsp_season ON team_season_participation(season_id);
-- Representative rows (documentation, evidence-bound):
--   RR x IPL 2008..2015 = PARTICIPATING; RR x IPL 2016, 2017 = SUSPENDED (BCCI franchise
--   suspension; IPL competition continued for all other teams); RR x IPL 2018..2026 =
--   PARTICIPATING; RR x IPL 2027 = UNKNOWN until authoritative squad evidence exists.
--   CORRECTED v2.1.1: these rows are seeded UNVERIFIED/PENDING until claim-level evidence
--   is retrieved into verification_records (Priority E). The locally verifiable
--   corroboration (CricSheet IPL archive: RR fixtures present 2008-2015 & 2018-2026,
--   ABSENT 2016-2017; 2016/2017 continue with 59-60 other-team fixtures each) supports
--   the windows but is tier-4 database evidence; tier-1/2 (official BCCI suspension notice)
--   retrieval upgrades each row to VERIFIED with a dated record. No row is labelled
--   VERIFIED merely because the roadmap assumes the fact.

-- ============================================================================
-- 9. squad_memberships (seasonal contracts / squad inclusion)
-- ============================================================================
CREATE TABLE squad_memberships (
    membership_id  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    player_id      UUID NOT NULL REFERENCES players(player_id) ON DELETE RESTRICT,
    team_id        UUID NOT NULL REFERENCES teams(team_id) ON DELETE RESTRICT,
    season_id      UUID NOT NULL REFERENCES seasons(season_id) ON DELETE RESTRICT,
    contract_type  VARCHAR(30) NOT NULL CHECK (contract_type IN (
        'Retained','Auction Buy','Replacement','Trade','Draft','Squad Inclusion','Released')),
    salary_inr     NUMERIC(14,2) CHECK (salary_inr >= 0),
    jersey_number  INT CHECK (jersey_number BETWEEN 0 AND 999),
    is_captain     BOOLEAN NOT NULL DEFAULT FALSE,
    is_overseas   BOOLEAN,
    -- C6: is_active_squad is now NULLABLE with NO default (unknown active-squad status
    --     is NULL, never a defaulted TRUE); evidence_source_id stays the source link.
    is_active_squad BOOLEAN,
    evidence_source_id UUID REFERENCES data_sources(source_id) ON DELETE SET NULL,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_player_team_season UNIQUE (player_id, team_id, season_id)
);
CREATE INDEX idx_squad_team_season ON squad_memberships(team_id, season_id);
CREATE INDEX idx_squad_player ON squad_memberships(player_id);

-- ============================================================================
-- 10. player_team_history (verified career team associations)
-- ============================================================================
CREATE TABLE player_team_history (
    history_id       UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    player_id        UUID NOT NULL REFERENCES players(player_id) ON DELETE CASCADE,
    team_id          UUID NOT NULL REFERENCES teams(team_id) ON DELETE RESTRICT,
    season_year      VARCHAR(20) NOT NULL,
    season_id        UUID REFERENCES seasons(season_id) ON DELETE SET NULL,
    association_type VARCHAR(30) NOT NULL CHECK (association_type IN
        ('Squad','Played','Released','Retained','Acquired','Loan')),
    appearances      INT CHECK (appearances >= 0),   -- verified match count; 0 = squad-only
    evidence_source  UUID REFERENCES data_sources(source_id) ON DELETE SET NULL,
    provenance_id    UUID REFERENCES source_records(record_id) ON DELETE SET NULL,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_player_team_season UNIQUE (player_id, team_id, season_year)
);
CREATE INDEX idx_team_history_player ON player_team_history(player_id);

-- ============================================================================
-- 11. matches
-- ============================================================================
CREATE TABLE matches (
    match_id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    external_cricsheet_id VARCHAR(50) UNIQUE,
    season_id          UUID NOT NULL REFERENCES seasons(season_id) ON DELETE RESTRICT,
    venue_id           UUID NOT NULL REFERENCES venues(venue_id) ON DELETE RESTRICT,
    match_number       INT,
    match_type         VARCHAR(30) NOT NULL DEFAULT 'T20',
    match_date         DATE NOT NULL,
    home_team_id       UUID NOT NULL REFERENCES teams(team_id) ON DELETE RESTRICT,
    away_team_id       UUID NOT NULL REFERENCES teams(team_id) ON DELETE RESTRICT,
    toss_winner_id     UUID REFERENCES teams(team_id) ON DELETE RESTRICT,
    toss_decision      VARCHAR(10) CHECK (toss_decision IN ('bat','field')),
    winner_id          UUID REFERENCES teams(team_id) ON DELETE RESTRICT,
    outcome_type       VARCHAR(30) NOT NULL CHECK (outcome_type IN
        ('runs','wickets','tie','super_over','no_result','abandoned')),
    win_margin_runs    INT CHECK (win_margin_runs >= 0),
    win_margin_wickets INT CHECK (win_margin_wickets >= 0),
    is_dls_applied     BOOLEAN NOT NULL DEFAULT FALSE,
    dls_method_version VARCHAR(20),
    player_of_match_id UUID REFERENCES players(player_id) ON DELETE SET NULL,
    innings_balls_scheduled INT NOT NULL DEFAULT 120 CHECK (innings_balls_scheduled > 0),
        -- C5: integer balls of record (120 T20 · 300 ODI/List A · 100 The Hundred);
        -- overs count is display-derived (balls / competitions.balls_per_over).
    source_record_id   UUID REFERENCES source_records(record_id) ON DELETE SET NULL,
    status             VARCHAR(20) NOT NULL CHECK (status IN
        ('Scheduled','Completed','Abandoned','No Result')),
    created_at         TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_match_teams CHECK (home_team_id <> away_team_id)
);
CREATE INDEX idx_matches_date ON matches(match_date);
CREATE INDEX idx_matches_season ON matches(season_id);
CREATE INDEX idx_matches_venue ON matches(venue_id);

-- ============================================================================
-- 12. innings
-- ============================================================================
CREATE TABLE innings (
    innings_id     UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    match_id       UUID NOT NULL REFERENCES matches(match_id) ON DELETE CASCADE,
    innings_number INT NOT NULL CHECK (innings_number IN (1,2,3,4)),
    batting_team_id  UUID NOT NULL REFERENCES teams(team_id) ON DELETE RESTRICT,
    bowling_team_id  UUID NOT NULL REFERENCES teams(team_id) ON DELETE RESTRICT,
    is_super_over  BOOLEAN NOT NULL DEFAULT FALSE,
    overs_allocated_balls INT NOT NULL DEFAULT 120 CHECK (overs_allocated_balls > 0),
        -- integer balls of record (C5): 120 = T20; 100 = The Hundred; ODI/List A = 300.
        -- Over notation is display-derived: floor(balls/balls_per_over) '.' (balls % balls_per_over).
    target_runs    INT CHECK (target_runs >= 0),
    target_overs_balls INT CHECK (target_overs_balls > 0),
        -- DLS revised target as integer balls (C5); NULL when no DLS revision.
    total_runs     INT NOT NULL DEFAULT 0 CHECK (total_runs >= 0),
    total_wickets  INT NOT NULL DEFAULT 0 CHECK (total_wickets BETWEEN 0 AND 10),
    total_legal_deliveries INT NOT NULL DEFAULT 0,
    total_extras   INT NOT NULL DEFAULT 0,
    is_declared    BOOLEAN NOT NULL DEFAULT FALSE,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_match_innings UNIQUE (match_id, innings_number, is_super_over),
    CONSTRAINT chk_innings_teams CHECK (batting_team_id <> bowling_team_id)
);
CREATE INDEX idx_innings_match ON innings(match_id);
CREATE INDEX idx_innings_super_over ON innings(is_super_over) WHERE is_super_over IS TRUE;
-- Consistency invariant (enforced by Service D / reconciliation job, not inline CHECK):
--   COUNT(deliveries per innings) reconciles with innings.total_legal_deliveries
--   (legal balls only; wides/noballs are delivery events, not legal deliveries).

-- ============================================================================
-- 13. deliveries (PARTITIONED by season_year) — remediated FKs (D2, D7, D9)
-- ============================================================================
CREATE TABLE deliveries (
    delivery_id     UUID NOT NULL DEFAULT uuid_generate_v4(),
    innings_id      UUID NOT NULL REFERENCES innings(innings_id) ON DELETE CASCADE,
    -- C4: deliveries.match_id was an independent NOT-NULL fact that could diverge from
    --   innings.match_id. It is now DERIVED (via the innings_id FK to innings.match_id) and
    --   not stored, so the delivery and its innings structurally cannot reference different
    --   matches. Match-level joins go through deliveries.innings_id -> matches. A composite
    --   FK (match_id, innings_id) is not expressible here because `innings` has no
    --   (match_id, innings_id) unique key; column removal is the equivalent, stronger
    --   integrity guarantee and preserves PG16 partitioned-table compatibility
    --   (partition key season_year is unaffected).
    season_year     VARCHAR(20) NOT NULL,
    over_number     INT NOT NULL CHECK (over_number >= 0 AND over_number < 60),
    ball_in_over    INT NOT NULL CHECK (ball_in_over >= 1),
    delivery_sequence INT NOT NULL CHECK (delivery_sequence >= 1),
    batter_id       UUID NOT NULL REFERENCES players(player_id) ON DELETE RESTRICT,
    bowler_id       UUID NOT NULL REFERENCES players(player_id) ON DELETE RESTRICT,
    non_striker_id  UUID NOT NULL REFERENCES players(player_id) ON DELETE RESTRICT,
    runs_batter     INT NOT NULL CHECK (runs_batter >= 0),  -- >6 (overthrows) -> DQ review, never rejected
    runs_extras     INT NOT NULL DEFAULT 0 CHECK (runs_extras >= 0),
    runs_total      INT NOT NULL CHECK (runs_total >= 0),
    is_wide         BOOLEAN NOT NULL DEFAULT FALSE,
    is_noball       BOOLEAN NOT NULL DEFAULT FALSE,
    is_bye          BOOLEAN NOT NULL DEFAULT FALSE,
    is_legbye       BOOLEAN NOT NULL DEFAULT FALSE,
    is_penalty      BOOLEAN NOT NULL DEFAULT FALSE,
    runs_wides      INT NOT NULL DEFAULT 0 CHECK (runs_wides >= 0),
    runs_noballs    INT NOT NULL DEFAULT 0 CHECK (runs_noballs >= 0),
    runs_byes       INT NOT NULL DEFAULT 0 CHECK (runs_byes >= 0),
    runs_legbyes    INT NOT NULL DEFAULT 0 CHECK (runs_legbyes >= 0),
    runs_penalties  INT NOT NULL DEFAULT 0 CHECK (runs_penalties >= 0),
    is_wicket       BOOLEAN NOT NULL DEFAULT FALSE,
    wicket_kind     VARCHAR(30),
    player_out_id   UUID REFERENCES players(player_id) ON DELETE SET NULL,
    is_bowler_credited_wicket BOOLEAN NOT NULL DEFAULT FALSE,
    match_phase     VARCHAR(20) CHECK (match_phase IN ('Powerplay','Middle','Death')),
        -- A4: single three-group phase model (DATA_DICTIONARY §4); the old four-value
        --     enum ('Middle 1','Middle 2') was inconsistent with the three-group batting/
        --     bowling summary columns and has been reduced. Boundaries are per-format
        --     (T20 / ODI / The Hundred rows differ); NULL for List A / first-class rows
        --     where phase is not meaningful.
    variation_type  VARCHAR(50),
    ball_speed_kph  NUMERIC(5,2) CHECK (ball_speed_kph IS NULL OR ball_speed_kph > 0),
    pitch_coordinate_x NUMERIC(6,3),
    pitch_coordinate_y NUMERIC(6,3),
    post_shot_landing_x NUMERIC(6,2),
    post_shot_landing_y NUMERIC(6,2),
    source_record_id UUID REFERENCES source_records(record_id) ON DELETE SET NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_deliveries PRIMARY KEY (delivery_id, season_year),
    CONSTRAINT chk_runs_consistency CHECK (runs_total = runs_batter + runs_extras),
    CONSTRAINT chk_wicket_credit CHECK (is_wicket = TRUE OR player_out_id IS NULL)
) PARTITION BY LIST (season_year);

CREATE TABLE deliveries_y2008_2015 PARTITION OF deliveries
    FOR VALUES IN ('2008','2009','2010','2011','2012','2013','2014','2015');
CREATE TABLE deliveries_y2016_2020 PARTITION OF deliveries
    FOR VALUES IN ('2016','2017','2018','2019','2020');
CREATE TABLE deliveries_y2021_2023 PARTITION OF deliveries
    FOR VALUES IN ('2021','2022','2023');
CREATE TABLE deliveries_y2024_2027 PARTITION OF deliveries
    FOR VALUES IN ('2024','2025','2026','2027');
CREATE TABLE deliveries_default PARTITION OF deliveries DEFAULT;

-- C4: match-level delivery access is served by joining deliveries.innings_id to
--   innings.match_id (the derived match key). A covering index on (innings_id) supports
--   both innings-scoped and match-scoped queries; no delivery.match_id column exists to
--   diverge, so the old "deliveries.innings_id.match_id = deliveries.match_id" Service D
--   cross-table invariant is no longer required — it is enforced structurally.
CREATE INDEX idx_deliveries_innings ON deliveries(innings_id);
CREATE INDEX idx_deliveries_batter ON deliveries(batter_id);
CREATE INDEX idx_deliveries_bowler ON deliveries(bowler_id);
CREATE INDEX idx_deliveries_matchup ON deliveries(batter_id, bowler_id);
CREATE INDEX idx_deliveries_source ON deliveries(source_record_id) WHERE source_record_id IS NOT NULL;

-- ============================================================================
-- 14. batting_innings (D8: no default on is_not_out; sample-size fields explicit)
-- ============================================================================
CREATE TABLE batting_innings (
    batting_innings_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    innings_id      UUID NOT NULL REFERENCES innings(innings_id) ON DELETE CASCADE,
    player_id       UUID NOT NULL REFERENCES players(player_id) ON DELETE RESTRICT,
    team_id         UUID NOT NULL REFERENCES teams(team_id) ON DELETE RESTRICT,
    did_not_bat     BOOLEAN NOT NULL DEFAULT FALSE,  -- DNB rows explicit, not implied
    batting_position INT CHECK (batting_position BETWEEN 1 AND 11),
    runs_scored     INT NOT NULL DEFAULT 0 CHECK (runs_scored >= 0),
    balls_faced     INT NOT NULL DEFAULT 0 CHECK (balls_faced >= 0),
        -- v2.1.1 / A2: authoritative scorecard convention (ICC Law 23 & 24.1,
        -- DATA_DICTIONARY global conventions + B04): no-balls ARE balls faced;
        -- wide events are NOT. Ingestion formula: COUNT(delivery events WHERE
        -- NOT is_wide) in the batter's facing spell. Never "legal only".
    minutes_at_crease INT CHECK (minutes_at_crease >= 0),
    fours           INT NOT NULL DEFAULT 0 CHECK (fours >= 0),
    sixes           INT NOT NULL DEFAULT 0 CHECK (sixes >= 0),
    dot_balls_faced INT NOT NULL DEFAULT 0 CHECK (dot_balls_faced >= 0),
    strike_rate     NUMERIC(6,2),                    -- NULL unless balls_faced > 0
    dismissal_kind  VARCHAR(30),
    dismissal_bowler_id UUID REFERENCES players(player_id) ON DELETE SET NULL,
    dismissal_fielder_id UUID REFERENCES players(player_id) ON DELETE SET NULL,
    is_not_out      BOOLEAN NOT NULL,                -- set from data; never defaulted
    runs_powerplay  INT NOT NULL DEFAULT 0 CHECK (runs_powerplay >= 0),
    balls_powerplay INT NOT NULL DEFAULT 0 CHECK (balls_powerplay >= 0),
    runs_middle     INT NOT NULL DEFAULT 0 CHECK (runs_middle >= 0),
    balls_middle    INT NOT NULL DEFAULT 0 CHECK (balls_middle >= 0),
    runs_death      INT NOT NULL DEFAULT 0 CHECK (runs_death >= 0),
    balls_death     INT NOT NULL DEFAULT 0 CHECK (balls_death >= 0),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_innings_batter UNIQUE (innings_id, player_id),
    CONSTRAINT chk_balls_faced CHECK (dot_balls_faced <= balls_faced),
    CONSTRAINT chk_sr_consistency CHECK (strike_rate IS NULL OR balls_faced > 0),
    -- A3: a DNB must face 0 balls; a batted appearance (did_not_bat=FALSE) may face 0 balls
    --      (walkover / timed-out dismissal) — a legitimate state, not a DNB, never fabricated.
    CONSTRAINT chk_dnb_zero CHECK (NOT (did_not_bat = TRUE AND balls_faced > 0))
);
CREATE INDEX idx_batting_player ON batting_innings(player_id);

-- ============================================================================
-- 15. bowling_spells (D6: integer balls of record; over notation derived)
-- ============================================================================
CREATE TABLE bowling_spells (
    spell_id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    innings_id         UUID NOT NULL REFERENCES innings(innings_id) ON DELETE CASCADE,
    player_id          UUID NOT NULL REFERENCES players(player_id) ON DELETE RESTRICT,
    team_id            UUID NOT NULL REFERENCES teams(team_id) ON DELETE RESTRICT,
    spell_order        INT NOT NULL DEFAULT 1,
    legal_balls_bowled INT NOT NULL DEFAULT 0 CHECK (legal_balls_bowled >= 0),
    illegal_events_wides INT NOT NULL DEFAULT 0 CHECK (illegal_events_wides >= 0),
    illegal_events_noballs INT NOT NULL DEFAULT 0 CHECK (illegal_events_noballs >= 0),
    maidens            INT NOT NULL DEFAULT 0 CHECK (maidens >= 0),
    runs_conceded      INT NOT NULL DEFAULT 0 CHECK (runs_conceded >= 0),
        -- = SUM(runs_batter + runs_wides + runs_noballs + penalty-free) per DDL domain rules;
        --   byes/leg-byes/penalties EXCLUDED (see DATA_DICTIONARY)
    wickets_taken      INT NOT NULL DEFAULT 0 CHECK (wickets_taken BETWEEN 0 AND 10),
    dot_balls_bowled   INT NOT NULL DEFAULT 0,
    economy_rate       NUMERIC(5,2),   -- NULL unless legal_balls_bowled > 0
    bowling_average    NUMERIC(6,2),   -- NULL unless wickets_taken > 0
    bowling_strike_rate NUMERIC(5,2),  -- NULL unless wickets_taken > 0
    runs_conceded_powerplay INT NOT NULL DEFAULT 0,
    balls_bowled_powerplay  INT NOT NULL DEFAULT 0,
    wickets_powerplay INT NOT NULL DEFAULT 0,
    runs_conceded_middle   INT NOT NULL DEFAULT 0,
    balls_bowled_middle    INT NOT NULL DEFAULT 0,
    wickets_middle  INT NOT NULL DEFAULT 0,
    runs_conceded_death    INT NOT NULL DEFAULT 0,
    balls_bowled_death     INT NOT NULL DEFAULT 0,
    wickets_death   INT NOT NULL DEFAULT 0,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_innings_bowler UNIQUE (innings_id, player_id),
    CONSTRAINT chk_dots_bowled CHECK (dot_balls_bowled <= legal_balls_bowled),
    CONSTRAINT chk_spell_econ CHECK (economy_rate IS NULL OR legal_balls_bowled > 0),
    CONSTRAINT chk_spell_avg CHECK (bowling_average IS NULL OR wickets_taken > 0)
);
CREATE INDEX idx_bowling_player ON bowling_spells(player_id);
-- Display derivation (never stored as a fact, and FORMAT-AWARE — the divisor is
-- competitions.balls_per_over, not a hard-coded 6):
--   overs_display = floor(legal_balls_bowled / balls_per_over) || '.' ||
--                   (legal_balls_bowled % balls_per_over)
--   T20/ODI/List A: divisor 6 · The Hundred: divisor 5 (DATA_DICTIONARY W01/§5).

-- ============================================================================
-- 16. fielding_events (D3: optional but integrity-preserving delivery link)
-- ============================================================================
CREATE TABLE fielding_events (
    fielding_event_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    delivery_id     UUID,                        -- optional: ball-level link
    season_year     VARCHAR(20),                 -- required together with delivery_id
    player_id       UUID NOT NULL REFERENCES players(player_id) ON DELETE RESTRICT,
    is_substitute   BOOLEAN NOT NULL DEFAULT FALSE,
    event_type      VARCHAR(30) NOT NULL CHECK (event_type IN (
        'Catch','Run Out Thrower','Run Out Catcher','Stumping',
        'Dropped Catch','Missed Run Out','Boundary Save')),
    is_recorded_opportunity BOOLEAN NOT NULL DEFAULT TRUE,  -- recorded, not inferred
    assisted_by_player_id UUID REFERENCES players(player_id) ON DELETE SET NULL,
    fielding_position VARCHAR(40),
    runs_saved      INT CHECK (runs_saved >= 0),
    provenance_tier VARCHAR(30) NOT NULL CHECK (provenance_tier IN (
        'DIRECTLY_MEASURED','OFFICIALLY_REPORTED','THIRD_PARTY_ESTIMATE','MODEL_INFERRED','UNKNOWN')),
        -- no default: classification must be set explicitly at ELT time
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_delivery_pairing CHECK
        ((delivery_id IS NULL AND season_year IS NULL) OR
         (delivery_id IS NOT NULL AND season_year IS NOT NULL)),
    CONSTRAINT fk_fielding_delivery FOREIGN KEY (delivery_id, season_year)
        REFERENCES deliveries(delivery_id, season_year) ON DELETE SET NULL
);
CREATE INDEX idx_fielding_player ON fielding_events(player_id);
CREATE UNIQUE INDEX uq_fielding_event ON fielding_events(delivery_id, season_year, player_id, event_type)
    WHERE delivery_id IS NOT NULL;
-- FK note: a partitioned referencing table (deliveries) is supported in PostgreSQL >= 15;
-- target engine is 16. On pre-15 engines this becomes a Service D reconciliation check.

-- ============================================================================
-- 17. wicketkeeping_events
-- ============================================================================
CREATE TABLE wicketkeeping_events (
    wk_event_id      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    innings_id       UUID NOT NULL REFERENCES innings(innings_id) ON DELETE CASCADE,
    player_id        UUID NOT NULL REFERENCES players(player_id) ON DELETE RESTRICT,
    match_id         UUID NOT NULL REFERENCES matches(match_id) ON DELETE RESTRICT,
    stumpings        INT NOT NULL DEFAULT 0 CHECK (stumpings >= 0),
    catches          INT NOT NULL DEFAULT 0 CHECK (catches >= 0),
    missed_stumpings INT CHECK (missed_stumpings >= 0),   -- recorded missed chances only
    missed_catches   INT CHECK (missed_catches >= 0),
    appearances      INT NOT NULL CHECK (appearances > 0),  -- set from data; no default
    provenance_tier  VARCHAR(30) NOT NULL CHECK (provenance_tier IN (
        'DIRECTLY_MEASURED','OFFICIALLY_REPORTED','THIRD_PARTY_ESTIMATE','MODEL_INFERRED','UNKNOWN')),
        -- no default: classification must be set explicitly at ELT time
    created_at       TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_wk_innings UNIQUE (innings_id, player_id)
);
CREATE INDEX idx_wk_player ON wicketkeeping_events(player_id);

-- ============================================================================
-- 18. pitch_conditions (D10: preserve reported text; ratings optional+methodology-bound)
-- ============================================================================
CREATE TABLE pitch_conditions (
    pitch_condition_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    match_id         UUID NOT NULL REFERENCES matches(match_id) ON DELETE CASCADE,
    venue_id         UUID NOT NULL REFERENCES venues(venue_id) ON DELETE RESTRICT,
    reported_description TEXT,              -- original source wording, preserved
    soil_type        VARCHAR(50),
    grass_coverage   VARCHAR(30),
    reported_moisture VARCHAR(30),
    reported_surface_state VARCHAR(40),     -- dry / damp / worn, reported only
    pitch_pace_rating   NUMERIC(3,1) CHECK (pitch_pace_rating BETWEEN 1.0 AND 10.0),
    pitch_bounce_rating NUMERIC(3,1) CHECK (pitch_bounce_rating BETWEEN 1.0 AND 10.0),
    pitch_turn_rating   NUMERIC(3,1) CHECK (pitch_turn_rating BETWEEN 1.0 AND 10.0),
    ratings_methodology_version VARCHAR(20),  -- numeric ratings ONLY when a validated methodology exists
    provenance_tier  VARCHAR(30) NOT NULL DEFAULT 'UNKNOWN' CHECK (provenance_tier IN (
        'DIRECTLY_MEASURED','OFFICIALLY_REPORTED','THIRD_PARTY_ESTIMATE','MODEL_INFERRED','UNKNOWN')),
    source_record_id UUID REFERENCES source_records(record_id) ON DELETE SET NULL,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_match_pitch UNIQUE (match_id),
    CONSTRAINT chk_ratings_methodology CHECK
        ((pitch_pace_rating IS NULL AND pitch_bounce_rating IS NULL AND pitch_turn_rating IS NULL) OR
         ratings_methodology_version IS NOT NULL)
);

-- ============================================================================
-- 19. weather_conditions (D10: measured context, never pitch; timezone + match method)
-- ============================================================================
CREATE TABLE weather_conditions (
    weather_condition_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    match_id            UUID NOT NULL REFERENCES matches(match_id) ON DELETE CASCADE,
    observation_timestamp TIMESTAMPTZ NOT NULL,
    venue_timezone      VARCHAR(40),
    local_observation_time TIMESTAMPTZ,
    temperature_celsius NUMERIC(4,1),
    relative_humidity_pct NUMERIC(4,1) CHECK (relative_humidity_pct BETWEEN 0.0 AND 100.0),
    dew_point_celsius   NUMERIC(4,1),
    dew_impact_index    VARCHAR(20),
    wind_speed_kmh      NUMERIC(5,2) CHECK (wind_speed_kmh >= 0),
    wind_direction_degrees INT CHECK (wind_direction_degrees BETWEEN 0 AND 360),
    precipitation_mm    NUMERIC(5,2) CHECK (precipitation_mm >= 0),
    atmospheric_pressure_hpa NUMERIC(6,1),
    cloud_cover_pct     NUMERIC(4,1) CHECK (cloud_cover_pct BETWEEN 0.0 AND 100.0),
    spatial_temporal_match_method VARCHAR(80),  -- how the observation was matched to the match
    data_provider       VARCHAR(60),
    source_record_id    UUID REFERENCES source_records(record_id) ON DELETE SET NULL,
    data_provenance_flag VARCHAR(100) NOT NULL DEFAULT
        'Macro Environmental Context (Not Direct Pitch Moisture)',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_match_weather_obs UNIQUE (match_id, observation_timestamp)
);
CREATE INDEX idx_weather_match ON weather_conditions(match_id);

-- ============================================================================
-- 20. player_availability (D8: unknown stays unknown)
-- ============================================================================
CREATE TABLE player_availability (
    availability_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    player_id      UUID NOT NULL REFERENCES players(player_id) ON DELETE CASCADE,
    season_id      UUID NOT NULL REFERENCES seasons(season_id) ON DELETE CASCADE,
    start_date     DATE NOT NULL,
    end_date       DATE NOT NULL,
    availability_status VARCHAR(30),        -- nullable: absence of a report != 'Unavailable'
    national_board_noc_status VARCHAR(20),  -- GRANTED/DENIED/UNKNOWN/NOT_APPLICABLE; NULL = not reported
    matches_expected_available INT CHECK (matches_expected_available >= 0),
    reason_for_unavailability TEXT,
    source_record_id UUID REFERENCES source_records(record_id) ON DELETE SET NULL,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_player_season_avail UNIQUE (player_id, season_id, start_date),
    CONSTRAINT chk_avail_dates CHECK (end_date >= start_date),
    CONSTRAINT chk_noc_values CHECK (national_board_noc_status IS NULL OR national_board_noc_status IN
        ('GRANTED','DENIED','UNKNOWN','NOT_APPLICABLE'))
);

-- ============================================================================
-- 21. player_injuries (verified-only claims)
-- ============================================================================
CREATE TABLE player_injuries (
    injury_id   UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    player_id   UUID NOT NULL REFERENCES players(player_id) ON DELETE CASCADE,
    injury_date DATE,
    injury_type VARCHAR(50),
    body_part   VARCHAR(50),
    severity    VARCHAR(20) CHECK (severity IN ('Minor','Moderate','Severe','Catastrophic')),
    surgery_required BOOLEAN,
    recovery_time_days INT,
    return_to_play_date DATE,
    recurrence_risk_score NUMERIC(3,2) CHECK (recurrence_risk_score BETWEEN 0.00 AND 1.00),
        -- MODEL_INFERRED, optional: NULL unless a validated, documented model produced it
    medical_notes TEXT,
    source_record_id UUID REFERENCES source_records(record_id) ON DELETE SET NULL,
    verified    BOOLEAN NOT NULL DEFAULT FALSE,   -- NEVER fabricate; unverified stays FALSE
    created_at  TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_injuries_player ON player_injuries(player_id);

-- ============================================================================
-- 22. player_awards
-- ============================================================================
CREATE TABLE player_awards (
    award_id   UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    player_id  UUID NOT NULL REFERENCES players(player_id) ON DELETE CASCADE,
    match_id   UUID REFERENCES matches(match_id) ON DELETE SET NULL,
    award_type VARCHAR(40) NOT NULL CHECK (award_type IN
        ('Player of the Match','Player of the Tournament','MVP','Milestone','Other')),
    award_value VARCHAR(100),
    award_date DATE,
    source_record_id UUID REFERENCES source_records(record_id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_awards_player ON player_awards(player_id);

-- ============================================================================
-- 23. player_competition_history
-- ============================================================================
CREATE TABLE player_competition_history (
    comp_history_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    player_id       UUID NOT NULL REFERENCES players(player_id) ON DELETE CASCADE,
    competition_id  UUID NOT NULL REFERENCES competitions(competition_id) ON DELETE RESTRICT,
    season_year     VARCHAR(20) NOT NULL,
    season_id       UUID REFERENCES seasons(season_id) ON DELETE SET NULL,
    appearances     INT CHECK (appearances >= 0),
    coverage_status VARCHAR(30) NOT NULL CHECK (coverage_status IN
        ('VERIFIED_PARTICIPATION','DATASET_UNAVAILABLE','NOT_ESTABLISHED','CONFIRMED_NON_PARTICIPATION')),
    provenance_id   UUID REFERENCES source_records(record_id) ON DELETE SET NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_player_comp_season UNIQUE (player_id, competition_id, season_year)
);
CREATE INDEX idx_comp_history_player ON player_competition_history(player_id);

-- ============================================================================
-- 24. player_membership_state (D5: relationship + currency, evaluated, evidence-bound)
-- ============================================================================
CREATE TABLE player_membership_state (
    state_id       UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    player_id      UUID NOT NULL REFERENCES players(player_id) ON DELETE CASCADE,
    as_of_date     DATE NOT NULL,
    rr_relationship_state VARCHAR(30) NOT NULL CHECK (rr_relationship_state IN (
        -- C6/D-dedup v2.1.1: CURRENT_RR_SQUAD removed (currency lives in Dimension 2,
        -- rr_current_state); relationship states capture association nature only.
        'HISTORICAL_RR_APPEARANCE','HISTORICAL_RR_SQUAD_ONLY',
        'PREVIOUSLY_ASSOCIATED','NO_VERIFIED_RR_RELATIONSHIP','RR_RELATIONSHIP_UNKNOWN')),
    rr_current_state   VARCHAR(15) NOT NULL CHECK (rr_current_state IN
        ('CURRENT','NOT_CURRENT','UNKNOWN')),
    negative_verification_met BOOLEAN,  -- TRUE only when TRD §4.5 requirements satisfied
    evidence_verification_id UUID REFERENCES verification_records(verification_id) ON DELETE SET NULL,
    notes          TEXT,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_membership_state UNIQUE (player_id, as_of_date)
);
CREATE INDEX idx_membership_player ON player_membership_state(player_id);

-- ============================================================================
-- 25. eligibility_policies (D5: versioned, season-bound, source-traceable)
-- ============================================================================
CREATE TABLE eligibility_policies (
    policy_id        UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    season_id        UUID NOT NULL REFERENCES seasons(season_id) ON DELETE CASCADE,
    policy_version   INT NOT NULL DEFAULT 1 CHECK (policy_version >= 1),
    effective_date   DATE NOT NULL,
    expiry_date      DATE,
    rule_source      VARCHAR(200) NOT NULL,   -- official BCCI/IPL rule reference
    verified         BOOLEAN NOT NULL DEFAULT FALSE,
    verification_id  UUID REFERENCES verification_records(verification_id) ON DELETE SET NULL,
    policy_json      JSONB,                    -- structured, versioned policy content
    notes            TEXT,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_policy UNIQUE (season_id, policy_version),
    CONSTRAINT chk_policy_dates CHECK (expiry_date IS NULL OR expiry_date >= effective_date),
    -- C2: a policy row marked verified MUST cite a supporting verification record.
    CONSTRAINT chk_policy_verified_evidence CHECK
        (NOT (verified = TRUE AND verification_id IS NULL))
);
-- C1: `player_eligibility` no longer carries its own `season_id`. The eligibility season
--    is DERIVED from the referenced policy (`eligibility_policies.season_id`), so a
--    player eligibility row structurally cannot reference a policy belonging to a
--    different season. Composite uniqueness is on (player_id, policy_id). This is the
--    appropriate composite-unique + FK design required by the brief (removing the
--    redundant 3NF-violating season column rather than adding a trigger).

-- ============================================================================
-- 26. player_eligibility (D5: season-bound, policy-versioned assessment)
-- ============================================================================
CREATE TABLE player_eligibility (
    eligibility_id  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    player_id       UUID NOT NULL REFERENCES players(player_id) ON DELETE CASCADE,
    -- C1: no independent season_id. The eligibility season is DERIVED from the referenced
    --     policy (eligibility_policies.season_id, which is NOT NULL). Storing season_id
    --     here was a 3NF violation (transitive dependence on policy_id) and a source of the
    --     "policy from a different season" defect; removing it makes that state impossible.
    policy_id       UUID NOT NULL REFERENCES eligibility_policies(policy_id) ON DELETE RESTRICT,
    eligibility_status VARCHAR(25) NOT NULL CHECK (eligibility_status IN (
        'VERIFIED_ELIGIBLE','VERIFIED_NOT_ELIGIBLE','ELIGIBILITY_UNVERIFIED','NOT_ASSESSED')),
    verified        BOOLEAN NOT NULL DEFAULT FALSE,   -- unknown players are NEVER assumed uncapped/eligible
    verification_id UUID REFERENCES verification_records(verification_id) ON DELETE SET NULL,
    notes           TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    -- C1: composite uniqueness on (player_id, policy_id); season is inherited from the policy.
    CONSTRAINT uq_player_policy UNIQUE (player_id, policy_id),
    -- C2: a VERIFIED_ outcome MUST cite a verification record; an unassessed/unverified
    --     outcome must not carry a spurious verified flag or evidence link.
    CONSTRAINT chk_eligibility_status_flag CHECK
        ((eligibility_status IN ('VERIFIED_ELIGIBLE','VERIFIED_NOT_ELIGIBLE') AND verified = TRUE AND verification_id IS NOT NULL)
         OR (eligibility_status IN ('ELIGIBILITY_UNVERIFIED','NOT_ASSESSED') AND verified = FALSE))
);
CREATE INDEX idx_eligibility_player ON player_eligibility(player_id);

-- ============================================================================
-- 27. user_teams
-- ============================================================================
CREATE TABLE user_teams (
    team_id      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    team_name    VARCHAR(100) NOT NULL,
    created_by   VARCHAR(50),
    target_season VARCHAR(20),
    notes        TEXT,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 28. user_team_players
-- ============================================================================
CREATE TABLE user_team_players (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_team_id UUID NOT NULL REFERENCES user_teams(team_id) ON DELETE CASCADE,
    player_id    UUID NOT NULL REFERENCES players(player_id) ON DELETE RESTRICT,
    assigned_role VARCHAR(30),
    batting_order INT,
    is_designated_wk BOOLEAN NOT NULL DEFAULT FALSE,
    is_captain   BOOLEAN NOT NULL DEFAULT FALSE,
    added_at     TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_team_player UNIQUE (user_team_id, player_id)
);
CREATE INDEX idx_user_team_players ON user_team_players(user_team_id);

-- ============================================================================
-- 29. derived_features (D1: expression index replaces invalid table UNIQUE)
-- ============================================================================
CREATE TABLE derived_features (
    feature_id       UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    player_id        UUID NOT NULL REFERENCES players(player_id) ON DELETE CASCADE,
    feature_group    VARCHAR(50) NOT NULL CHECK (feature_group IN (
        'Batting','Bowling','Fielding','Wicketkeeping','Matchup Matrix',
        'Clutch & Pressure','Venue Baselines','Squad Intelligence','Career Coverage')),
    feature_name     VARCHAR(100) NOT NULL,
    feature_value_numeric NUMERIC(14,4),
    feature_value_text  TEXT,
    feature_value_json  JSONB,
    calculation_window  VARCHAR(50) NOT NULL,
    format_tag        VARCHAR(20),
    status           VARCHAR(20) NOT NULL DEFAULT 'DERIVED' CHECK (status IN
        ('OBSERVED','DERIVED','MODEL_INFERRED','NOT_COMPUTABLE','DEFERRED')),
        -- v2.1.1: DEFERRED = computable only under documented data conditions that no
        -- current source satisfies (e.g. The-Hundred derived rate metrics, Priority B
        -- option 2: ingested & preserved as raw, no derived rate published yet).
    model_version     VARCHAR(20) NOT NULL DEFAULT 'v2.1',
    source_provenance UUID REFERENCES source_records(record_id) ON DELETE SET NULL,
    computed_at       TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
-- D1 decision: UNIQUE expression index (COALESCE allowed in INDEX, not in table constraint)
CREATE UNIQUE INDEX uq_derived_features ON derived_features (
    player_id, feature_name, calculation_window, model_version, COALESCE(format_tag, '')
);
CREATE INDEX idx_derived_features_player ON derived_features(player_id);
CREATE INDEX idx_derived_features_group ON derived_features(feature_group);

-- ============================================================================
-- 30. ranking_configurations (Priority F, v2.1.1) — versioned ranking method config
-- ============================================================================
-- The hackathon Top-10 method is NOT an inline constant and NOT `derived_features.
-- model_version` alone (v2.1.0 gap). The full, versioned configuration lives here so a
-- specific board is always reproducible from (config_version + data_snapshot + seed).
CREATE TABLE ranking_configurations (
    config_id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    config_version       VARCHAR(20) NOT NULL,
    target_season_id     UUID NOT NULL REFERENCES seasons(season_id) ON DELETE RESTRICT,
    policy_id            UUID NOT NULL REFERENCES eligibility_policies(policy_id)
        ON DELETE RESTRICT,
        -- hard eligibility gate: only candidates VERIFIED_ELIGIBLE under this policy version
    evaluation_date      DATE NOT NULL,     -- ages computed as of this recorded date (not now())
    role_grouping_json   JSONB,             -- documented role groups + role criteria (RANKING_SPEC)
    gate_thresholds_json JSONB,             -- relevance gate: within-role baseline percentile + min sample
    ordering_json        JSONB NOT NULL,    -- primary/secondary/tertiary keys: age, consistency, sample
    tiebreakers_json     JSONB,             -- documented final deterministic tiebreak (total order)
    seed                 INT NOT NULL DEFAULT 0,   -- explicit seed; 0 = pure deterministic SQL order
    created_by           VARCHAR(50),
    verified             BOOLEAN NOT NULL DEFAULT FALSE,
    verification_id      UUID REFERENCES verification_records(verification_id) ON DELETE SET NULL,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_config_version UNIQUE (config_version),
    CONSTRAINT chk_ranking_config_evidence CHECK
        (NOT (verified = TRUE AND verification_id IS NULL))
);
CREATE INDEX idx_ranking_config_season ON ranking_configurations(target_season_id);

-- ============================================================================
-- 31. ranking_runs (Priority F, v2.1.1) — durable, versioned ranking-run record
-- ============================================================================
-- One row per (config_version, data snapshot). Same inputs -> exactly one stored board,
-- so the Top-10 + reserves are reproducible and auditable (AC-18 / AC-25).
CREATE TABLE ranking_runs (
    run_id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    config_id             UUID NOT NULL REFERENCES ranking_configurations(config_id)
        ON DELETE RESTRICT,
    data_snapshot_sha256  CHAR(64) NOT NULL,  -- evidence of the frozen input set (hash of candidate pool)
    candidate_pool        JSONB NOT NULL,     -- eligible candidate pool at run time (provenance)
    top10                 JSONB NOT NULL,     -- ordered board: rank, player_id, scores, evidence refs
    reserve_list          JSONB,              -- next-ranked eligible candidates after Top-10
    computed_at           TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    determinism_note      TEXT,
    CONSTRAINT uq_run_per_config_snapshot UNIQUE (config_id, data_snapshot_sha256)
);
CREATE INDEX idx_ranking_run_config ON ranking_runs(config_id);
```

### 10.4 DDL Integrity Summary
- **Dependency ordering** is topological: venues precede teams/matches; `team_season_participation`
  precedes nothing that references it; `eligibility_policies` precedes `player_eligibility`.
- **Partitioned tables**: `deliveries` PK includes the partition key; PG15+ FK support on
  partitioned referencing tables (target PG16; pre-15 fallback = Service D checks, D2).
- **FK deletion actions** documented per column above (RESTRICT for fact integrity, CASCADE for
  owned rows, SET NULL for optional links).
- **3NF status**: the normalised core is 3NF (no repeating groups; non-key attributes depend on
  keys via the documented entity split). `derived_features` is the single documented exception
  (a versioned feature store, not a transactional entity).
- **No false-claim defaults**: every default that could turn unknown into a fact was removed
  (D8).

---

## 11. Engine Determinism & LLM Independence

- **Deterministic database queries** serve all known facts and statistics (CPPAE, CMIE, SICE
  read paths). No LLM is required on the deterministic path.
- **External research** (PIRE corroboration via CDCRE candidates, TMVE/CDCRE gaps) is used for
  evidence **discovery and verification** only, with provenance recorded by Service C.
- LLM-assisted research output is always flagged `THIRD_PARTY_ESTIMATE` or `MODEL_INFERRED` and
  is routed for human review when it affects identity, membership, or eligibility.
- **No engine is made dependent on an LLM** for correctness.

---

## 12. Streamlit Presentation Requirements

### 12.1 Required Views
1. Home / Team Builder · 2. Player Search · 3. Player Identity Verification · 4. Historical RR
   Membership · 5. Player Career Profile · 6. Performance Analytics · 7. Contextual Analysis ·
   8. Player Comparison · 9. Squad Composition · 10. Squad Intelligence Report · 11. Data
   Source and Verification Report.

### 12.2 Session State Discipline
- `st.session_state` holds **only** ephemeral UI state (active team, active player, filters).
- **No analytics in Streamlit**; views render MIE/engine outputs through thin adapters.

### 12.3 Frontend-Agnostic Guarantee
The Streamlit layer consumes the same structured contracts (§2–§8) as any future Next.js
frontend; no engine imports Streamlit.

---

## 13. API / Service Specification (frontend-agnostic)

| Capability | Contract | Description |
|---|---|---|
| `discover_candidates(raw_name)` | CDCRE (pre-identity) | Candidate + corroboration evidence; no player_id required |
| `resolve_player(raw_name, candidates)` | PIRE | Tiered identity resolution + status + evidence |
| `verify_membership(player_id, as_of_date)` | TMVE | Dimensions 1–2 (RR relationship + currency) + evidence + confidence (only if calibrated). Dimension 3 via `assess_eligibility` (§4.4 Option B) |
| `discover_career(player_id)` | CDCRE (post-identity) | Competition history + four-state coverage + provenance |
| `analyse_performance(player_id, formats, window)` | CPPAE | Full performance profile, per DATA_DICTIONARY |
| `contextualise(player_id)` | CMIE | Condition annotations + provenance tiers |
| `evaluate_squad(user_team_id)` | SICE | Squad intelligence report |
| `assess_eligibility(player_id, season_id)` | player_eligibility | Season-bound, policy-versioned status |
| `run_ranking(config_version, data_snapshot)` | SICE / `ranking_runs` | Executes the versioned Top-10 method (full spec: [`RANKING_SPEC.md`](RANKING_SPEC.md)); returns the reproducible board (AC-18/AC-25); one stored `ranking_runs` row per `(config, snapshot)` |
| `get_ranking_run(run_id)` | `ranking_runs` | Read a stored, auditable board + candidate pool |
| `generate_profile_export(player_id, fmt)` | Service B | JSON/CSV export with attribution |
| `get_provenance(record_id)` | Service C | Provenance + verification status |
| `upsert_user_team(user_team)` | Service E | Team create/update |
| `request_player_intelligence(name, team_id)` | MIE | End-to-end orchestrated report |

All responses are versioned structured objects; every derived field carries
`source_provenance` and, where applicable, a `format_tag` (no cross-format mixing).

---

## 14. Non-Functional Specifications

- **Determinism**: identical inputs → identical deterministic outputs; seeded randomness only
  where documented.
- **Zero fabrication**: missing → `NULL`; no invented players, matches, injuries, memberships,
  or mental-state claims.
- **Evidence-backed**: every membership/eligibility/career claim carries a
  `verification_records` entry with evidence tier.
- **Format-aware**: cross-format comparisons prohibited without explicit normalisation tags.
- **Licensing & confidentiality**: ODC-By (CricSheet, verified locally) and CC BY 4.0
  (Open-Meteo, stated terms — verification per DATA_SOURCE_REGISTER) attribution embedded in
  exports; the proprietary hackathon dataset is confidential and isolated.
- **Data-lake gap**: local SMAT data is `DATASET_UNAVAILABLE`; SMAT claims route through
  CDCRE external research with provenance.
