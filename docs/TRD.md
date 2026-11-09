# Technical Requirements Document (TRD) & Central Database Schema
**Product**: RR Squad Intelligence & Team Composition Platform
**Focus Franchise**: Rajasthan Royals (RR) · **Primary Interface**: Streamlit (initial) · **Future Frontend**: Next.js
**Document Version**: 2.0.0-ARCH-REVISION
**Status**: [STATUS: PLANNED - GREENFIELD BASELINE]
**Author**: Engineering Architecture Team (`teamwork_worker_2`)

> **Revision Note (v2.0.0)**: This document was revised to reflect the pivot from a
> *historical player analytics / auction war-room system* to the **RR Squad Intelligence &
> Team Composition Platform**. All six specialised engines, the Mother Intelligence Engine
> (MIE) orchestration layer, five support services, the six-class membership taxonomy, and
> the expanded 27-entity database are specified here. The initial user interface is
> **Streamlit**; the engine layer is **frontend-agnostic** so a future Next.js frontend can
> reuse it. All raw data now resides in `datasets/` (previously referenced as `CricSheet/`).

---

## 1. System Overview & Technical Architecture

> **Architecture Baseline Status**: `[STATUS: PLANNED - GREENFIELD BASELINE]`
> All schemas, database tables, partition schemes, mathematical models, engine contracts,
> and service interfaces defined in this document represent the approved architectural
> specification for greenfield implementation. Zero application code currently exists.

The **RR Squad Intelligence & Team Composition Platform** is an evidence-backed decision-support
system for constructing and evaluating a Rajasthan Royals team. The primary workflow is:

1. A user creates a team.
2. The user enters a cricket player's name.
3. The system identifies the player (**PIRE**).
4. The system checks whether the player exists in the internal database.
5. Where necessary, the system performs **authorised external research** to discover and verify
   the player's identity and cricket history (**CDCRE** + external research).
6. The system determines whether the player has represented Rajasthan Royals (**TMVE**).
7. It distinguishes **historical RR players from current RR squad members**.
8. It retrieves and analyses the player's cricket career (**CDCRE**).
9. It evaluates the player's performance, contribution and role (**CPPAE**).
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
│ Identity Res. │ │ Membership   │ │ Career Disc. │ │ Performance  │ │ Context/ Squad │
└──────┬───────┘ └──────┬───────┘ └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
       │                │                │                │                │
       ▼                ▼                ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SUPPORT SERVICES                                          │
│  A. Data Ingestion · B. Player Profile Gen · C. Source Verification &       │
│     Provenance · D. Data Quality & Coverage · E. Team Builder               │
└─────────────────────────────────────────────┬───────────────────────────────┘
                                              │ Read / derive (deterministic)
                                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│              Central PostgreSQL 16 Normalised Core (27 Entities, 3NF)       │
│   players, player_aliases, teams, competitions, seasons, squad_memberships,│
│   player_team_history, matches, innings, deliveries, batting_innings,      │
│   bowling_spells, fielding_events, wicketkeeping_events, venues,           │
│   pitch_conditions, weather_conditions, player_availability,               │
│   player_injuries, player_awards, player_competition_history, user_teams,   │
│   user_team_players, data_sources, source_records, verification_records,    │
│   derived_features                                                          │
└──────────────────────────────────────▲──────────────────────────────────────┘
                                       │ Batch ELT (immutable raw payloads)
┌──────────────────────────────────────┴──────────────────────────────────────┐
│  datasets/ (CricSheet) · Kaggle · HawkeyeStats · Historical Weather ·       │
│  Official Records · Verified Research (provenance-tracked)                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.1 Architectural Subsystems

1. **Presentation Tier (Streamlit, initial)**: Streamlit application exposing the 11 required
   views (§12). UI components call MIE and are **strictly separated** from analytics
   calculations; session state is used cautiously (see §12.2).
2. **Mother Intelligence Engine (MIE)**: The central orchestrator (§2). MIE does **not**
   invent statistics or make unsupported membership decisions; it coordinates the six engines,
   merges their outputs, and returns structured responses to the UI.
3. **Six Specialised Engines (ENGINE 01–06)**: PIRE, TMVE, CDCRE, CPPAE, CMIE, SICE — each with
   a documented input/output contract (§3–§8).
4. **Five Support Services (A–E)**: Data Ingestion, Player Profile Generator, Source Verification
   & Provenance, Data Quality & Coverage, Team Builder (§9).
5. **Central Normalised Relational Core (PostgreSQL 16, 27 entities)**: strict 3NF, canonical
   `player_id` across all engines, declarative season partitioning on `deliveries` (§4).
6. **Data Ingestion & ELT Pipeline**: immutable raw staging with SHA-256 provenance, quarantining
   of malformed payloads (§9.1).

### 1.2 Frontend-Agnostic Engine Contract

All six engines and the MIE expose **typed, versioned Python interfaces** (request/response data
classes or Pydantic models) independent of any UI framework. Streamlit is the **initial** consumer
only; the same engine layer is consumable by a future Next.js frontend without modification.
No engine imports Streamlit, React, or any UI runtime.

---

## 2. Mother Intelligence Engine (MIE) — Central Orchestrator

**ENGINE 00 — Mother Intelligence Engine (MIE)**

### 2.1 Responsibilities
- Accept player search requests (from Streamlit or any frontend-agnostic API).
- Coordinate the six specialised engines in the correct dependency order.
- Manage the player identification workflow end-to-end.
- Trigger internal database searches; trigger **authorised external research** when internal
  records are insufficient.
- Route records to the appropriate analytics modules.
- Merge engine outputs into a unified player intelligence report.
- Maintain player identity consistency (single canonical `player_id` per real-world person).
- Track verification status across identity, membership, and eligibility dimensions.
- Manage confidence scores and source provenance (via Support Service C).
- Produce unified, structured responses returned to the UI layer.

### 2.2 MIE Input / Output Contract
```
MIE.request_player_intelligence(name: str, team_id: Optional[UUID]) -> PlayerIntelligenceReport
PlayerIntelligenceReport {
    identity:       PIRE.Output            # resolved player_id + confidence + warnings
    membership:     TMVE.Output            # six-class classification + evidence
    career:         CDCRE.Output           # competition history + coverage status
    performance:    CPPAE.Output           # batting/bowling/fielding/WK/match contribution
    context:        CMIE.Output            # environmental & match-condition annotations
    squad:          SICE.Output            # (only when a team_id is supplied)
    provenance:     List[SourceRecord]     # every external/derived claim traced to a source
    verification:   VerificationStatus     # aggregate status + human-review flags
}
```

### 2.3 Orchestration Sequence (Happy Path)
1. `PIRE.resolve(name)` → canonical `player_id`, confidence, ambiguity flags.
2. If unresolved or low-confidence → **authorised external research** (CDCRE + research service);
   if still ambiguous → request **user clarification** (do not guess).
3. `TMVE.verify(player_id)` → membership class + RR seasons + verified appearance count.
4. `CDCRE.discover(player_id)` → career across competitions + coverage/provenance.
5. `CPPAE.analyse(player_id)` → full performance profile.
6. `CMIE.contextualise(player_id)` → condition annotations per match situation.
7. If `team_id` supplied → `SICE.evaluate(team_id)` → squad report.
8. MIE merges outputs, attaches provenance (Service C) and coverage (Service D), and returns.

### 2.4 MIE Guardrails
- MIE **never** fabricates statistics; every numeric value in its response is derived by CPPAE,
  CMIE, or SICE from verified records.
- MIE **never** makes unsupported membership decisions; it reports the TMVE classification verbatim.
- If any engine returns `UNVERIFIED`, MIE surfaces that flag — it does not silently resolve it.

---

## 3. ENGINE 01 — Player Identity Resolution Engine (PIRE)

**Purpose**: Resolve the actual identity of a player from a name supplied by the user.

### 3.1 Responsibilities
- Exact-name matching.
- Alias matching.
- Name variations (abbreviations, expanded forms, transliterations).
- Spelling variations.
- Duplicate player detection.
- Disambiguation when multiple players share a name.
- Player ID resolution to a canonical `player_id`.
- Date-of-birth verification where available.
- Team and competition association as corroborating evidence.

### 3.2 Output Contract
```
PIRE.resolve(input_name) -> PIRE.Output {
    resolved_player_id:    Optional[UUID]   # NULL if unresolved
    canonical_name:        Optional[str]
    known_aliases:         List[str]
    identity_confidence:   float            # 0.0–1.0
    matching_records:      List[SourceRecord]
    unresolved_warnings:   List[str]        # e.g. "multiple players share this name"
    requires_human_review: bool
}
```

### 3.3 Disambiguation Algorithm (4-tier waterfall)
1. **Tier 1 — Canonical registry key**: exact CricSheet hex hash / BCCI / ESPN ID → confidence `1.000`.
2. **Tier 2 — Verified alias registry**: exact match in `player_aliases` (`is_verified=TRUE`) → `1.000`.
3. **Tier 3 — Deterministic contextual intersection**: surname + initials + team + match window;
   unique match → `0.980`, insert alias (unverified).
4. **Tier 4 — Probabilistic fuzzy + biometric**: Jaro-Winkler ≥ 0.92 AND Levenshtein ≤ 2,
   cross-validated against role, batting/bowling hand, DOB, active era. Score ≥ 0.950 and
   single candidate → link; else **quarantine** with `needs_review=TRUE`.

> **Mandatory rule**: **Never merge two players merely because their names are similar.**
> Ambiguity below the confidence floor is routed to human review, not auto-resolved.

---

## 4. ENGINE 02 — Team Membership Verification Engine (TMVE)

**Purpose**: Verify whether a player represented Rajasthan Royals, and distinguish historical from
current membership.

### 4.1 Responsibilities
- Search internal historical membership records (`squad_memberships`, `player_team_history`).
- Verify **actual RR match appearances** (from `matches`/`deliveries`), not just squad lists.
- Verify historical squad inclusion.
- Identify the RR seasons in which the player represented RR.
- Identify other IPL teams the player has represented.
- Verify **current** squad membership **separately** from historical membership.
- Check retention / auction / transfer / release information where documented.
- Perform **authorised external research** when internal records are insufficient.

### 4.2 Verification Hierarchy (evidence ranking)
1. Official IPL and franchise records.
2. Official match scorecards.
3. BCCI records.
4. Reliable cricket databases.
5. Reputable secondary reporting.

### 4.3 Six-Class Membership Taxonomy
A player is assigned to **exactly one** class using verified evidence:

| Class | Definition |
|---|---|
| `CURRENT_SQUAD` | Verified current-season squad evidence. Assigned **only** with such evidence. |
| `HISTORICAL_RR_PLAYER` | Verified RR match appearances or squad inclusion in a prior season. |
| `PREVIOUSLY_ASSOCIATED` | Documented prior association (loan, brief squad, release) without confirmed RR match. |
| `NEVER_REPRESENTED_RR` | Verified record base shows no RR representation. |
| `UNVERIFIED` | Identity or membership could not be established; **not** treated as non-member. |
| `ELIGIBILITY_UNVERIFIED` | Identity known but playing eligibility/uncapped status unconfirmed. |

### 4.4 Output Contract
```
TMVE.verify(player_id) -> TMVE.Output {
    current_squad_status:   Optional[str]      # verified current membership or NULL
    historical_rr_status:   bool              # TRUE/FALSE/NULL (unknown)
    rr_seasons:             List[str]         # seasons in which player represented RR
    other_ipl_teams:        List[str]
    verified_rr_appearances:int              # confirmed match count (0 allowed, ≠ unknown)
    membership_class:       enum(6 classes)
    evidence_urls:          List[SourceRecord]
    verification_date:      date
    confidence_level:       float
}
```

### 4.5 TMVE Guardrails
- **Squad inclusion ≠ match appearance**: a player appearing on an RR squad list is not assumed
  to have played a match.
- **Historical membership ≠ current membership**: a player who played for RR in a prior season is
  **not** automatically `CURRENT_SQUAD`.
- **Suspension period represented separately**: RR was suspended for IPL 2016 and 2017 and returned
  in 2018. RR franchise-membership analysis begins **2008–2015**; the 2016–2017 suspension is a
  distinct representation; post-return analysis covers **2018 onwards**, with the primary window
  **2018–2026**. **IPL 2027 is a future target season** and is not treated as verified participation
  until squad records are confirmed.
- **Absence of a search result is not proof of non-membership** — that is the `UNVERIFIED` class.

---

## 5. ENGINE 03 — Career Discovery & Competition Research Engine (CDCRE)

**Purpose**: Discover a player's complete available cricket career **beyond RR**.

### 5.1 Competitions Investigated
Previous IPL franchises · domestic state teams · Ranji Trophy · Syed Mushtaq Ali Trophy · Vijay
Hazare Trophy · Duleep Trophy · India A and age-group cricket · international cricket · other
recognised T20 leagues · other verified competitions.

### 5.2 Responsibilities
- Discover relevant competitions and team history.
- Retrieve available player statistics per competition.
- Identify season participation and career gaps.
- Track data coverage (which competitions are present/absent in the local data lake).
- Record source provenance for every external claim.

### 5.3 Output Contract
```
CDCRE.discover(player_id) -> CDCRE.Output {
    competitions:      List[{competition, seasons[], verified_appearances, stats, coverage_status}]
    career_gaps:       List[str]
    data_coverage:     {verified: [...], dataset_unavailable: [...], not_established: [...],
                        confirmed_non_participation: [...]}
    provenance:        List[SourceRecord]
}
```

### 5.4 CDCRE Guardrails
- **Do not assume** a player who is absent from a dataset never played that competition.
- Distinguish **four** coverage states explicitly:
  1. *Verified participation* — confirmed by a verified source.
  2. *Dataset coverage unavailable* — not present in the local lake; status unknown.
  3. *Participation not established* — no evidence for or against; must not be reported as "none".
  4. *Confirmed non-participation* — a source positively confirms the player did not take part.

---

## 6. ENGINE 04 — Complete Player Performance Analytics Engine (CPPAE)

**Purpose**: Generate a comprehensive, evidence-backed player performance profile. Every statistic
produced by CPPAE has a **documented definition and calculation method** (see §6.6). Unverified
statistics are **not** computed from incomplete data.

### 6.1 Batting
Innings · matches · runs · average · strike rate · boundaries (4s/6s) · dot balls · batting
positions · performance split by opening / top-order / middle-order / finishing · performance
against individual bowlers · performance against pace vs spin · performance against bowling styles
and verified delivery variations · powerplay / middle-over / death-over performance · performance in
successful vs unsuccessful matches · partnership contributions.

### 6.2 Bowling
Overs · runs conceded · wickets · economy · average · bowling strike rate · dot balls · powerplay /
middle / death performance · batter-specific matchups · pace and spin classifications · delivery
speed and line/length **where available** (NULL when unrecorded).

### 6.3 Fielding
Catches · run-outs · stumpings · recorded dropped catches · fielding opportunities · fielding
positions (where verified) · fielding contribution.

### 6.4 Wicketkeeping
Dismissals (catches + stumpings) · recorded missed chances · wicketkeeping appearances.

### 6.5 Match Contribution
Player-of-the-match awards · match participation · batting and bowling contribution · match
situation · contribution to team outcomes · performance under pressure **where measurable**
(leverage-based, not inferred mental state).

### 6.6 Statistical Guardrails
- **Format-aware comparisons only**: IPL / T20 / List A / first-class statistics are never mixed
  without an explicit format tag.
- **No zero-imputation**: missing figures stay `NULL`; a player who did not bowl has a `NULL`
  economy, not `0.00`.
- **Super Over isolation**: Super Over balls are segregated from career aggregates.
- **No mental-state inference**: performance under pressure is expressed via measured leverage
  situations, never as a claim about a player's psychology.

### 6.7 Output Contract
```
CPPAE.analyse(player_id, formats=[...], window="career") -> CPPAE.Output {
    batting:    {…}, bowling: {…}, fielding: {…}, wicketkeeping: {…},
    match_contribution: {…},
    per_stat:   {stat_name: {value, definition, formula, source, format_tag, null_reason?}}
}
```

---

## 7. ENGINE 05 — Contextual Match Intelligence Engine (CMIE)

**Purpose**: Understand the environmental and match conditions in which a player performed.

### 7.1 Analysed Conditions
Opposition · opposing batter/bowler · bowling style · delivery variations · delivery speed · line
and length · venue · pitch type and reported conditions · grass coverage (where documented) ·
weather · humidity · temperature · wind speed/direction · rainfall · dew observations · match
format · innings · match phase · required run rate · score pressure · target · match result.

### 7.2 Output Contract
```
CMIE.contextualise(player_id) -> CMIE.Output {
    match_contexts: List[{match_id, opposition, venue, pitch, weather, phase, rrr,
                         result, provenance_flags[]}]
}
```

### 7.3 CMIE Guardrails
- **Five provenance tiers** are attached to every contextual datum:
  1. *Directly measured* — recorded by an authoritative instrument/official record.
  2. *Officially reported* — published by a governing body.
  3. *Third-party estimate* — reputable external estimate.
  4. *Model-inferred* — derived by a documented model.
  5. *Unknown* — not available.
- **Weather must not be represented as a direct measurement of pitch conditions.** Ambient
  macro-weather (e.g. Open-Meteo) is a context/dew proxy, explicitly labelled as such.
- **Never infer a player's mental state from match statistics.**

---

## 8. ENGINE 06 — Squad Intelligence & Composition Engine (SICE)

**Purpose**: Evaluate the team assembled by the user.

### 8.1 Responsibilities
Analyse player roles · identify batting depth · identify bowling depth · analyse pace/spin balance
· evaluate wicketkeeping options · evaluate all-rounder availability · analyse batting-order
flexibility · identify role duplication · identify weak or missing roles · analyse historical
player contribution · compare players occupying similar roles · identify potential replacements ·
compare current squad players with new candidates · evaluate squad combinations.

### 8.2 Output Contract
```
SICE.evaluate(team_id) -> SICE.Output {
    squad_overview:     {…}
    role_distribution:  {…}
    strengths:          [ ... ]
    weaknesses:         [ ... ]
    dependency_analysis:{…}        # e.g. single-point-of-failure roles
    recruitment_priorities: List[{role, rationale, evidence}]
    alternative_combinations: List[{members[], notes}]
    recommendations:    List[{statement, evidence[], confidence}]
}
```

### 8.3 SICE Guardrails
- **Do not confuse an analytical recommendation with an official RR selection or auction decision.**
- **Do not generate recruitment probabilities** unless the underlying model has been statistically
  validated and calibrated. Unvalidated outputs are presented as *evidence-backed qualitative
  recommendations*, not probabilities.

---

## 9. Support Services

### 9.1 Service A — Data Ingestion Service
Imports: CricSheet datasets (`datasets/`), Kaggle datasets, HawkeyeStats, historical weather,
official cricket records, verified research data. Immutable raw staging with SHA-256 digests;
malformed payloads quarantined without halting the run.

### 9.2 Service B — Player Profile Generator
Generates standardised **JSON and CSV** exports from the central database for a canonical
`player_id`. Exports embed licensing attribution.

### 9.3 Service C — Source Verification & Provenance Service
Records, for every external/derived claim: source URL · source provider · retrieval timestamp ·
licence · verification status · confidence · original source record ID. Backed by
`verification_records` and `data_sources`.

### 9.4 Service D — Data Quality & Coverage Service
Detects: missing data · duplicates · conflicting statistics · invalid player associations ·
inconsistent match identities · unavailable contextual features. Emits coverage states used by
CDCRE and TMVE.

### 9.5 Service E — Team Builder Service
Manages user-created teams: player selection, removal, composition, role assignments, and saved
team configurations. Backed by `user_teams` and `user_team_players`.

---

## 10. Central Normalised PostgreSQL Database Schema (27 Entities)

The data model enforces relational integrity across **27 entities**. Canonical `player_id` is the
single join key across all engines. Raw payloads are kept separate from normalised records and
from `derived_features`.

### 10.1 Entity Domains
```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 1. INGESTION & PROVENANCE : data_sources, source_records, verification_records │
│ 2. CORE IDENTITY          : players, player_aliases                             │
│ 3. TEAMS & COMPETITIONS   : teams, competitions, seasons, squad_memberships,    │
│                             player_team_history                                  │
│ 4. MATCHES & CONDITIONS   : matches, venues, pitch_conditions, weather_conditions│
│ 5. GRANULAR CRICKET CORE  : innings, deliveries (partitioned)                   │
│ 6. SCORECARDS & FIELDING  : batting_innings, bowling_spells, fielding_events,   │
│                             wicketkeeping_events                                  │
│ 7. CAREER & ELIGIBILITY   : player_competition_history, player_awards,          │
│                             player_availability, player_injuries                 │
│ 8. USER TEAM COMPOSITION  : user_teams, user_team_players                       │
│ 9. FEATURE STORE          : derived_features                                     │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 10.2 Complete PostgreSQL 16 DDL

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
    external_entity_id   VARCHAR(100) NOT NULL,
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
-- 2b. verification_records (Source Verification & Provenance Service - C)
-- ============================================================================
CREATE TABLE verification_records (
    verification_id  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    subject_type     VARCHAR(30) NOT NULL CHECK (subject_type IN
        ('player_identity','player_membership','player_eligibility','career_participation','source_record')),
    subject_id       UUID NOT NULL,                 -- player_id, team_id, record_id, etc.
    source_record_id UUID REFERENCES source_records(record_id) ON DELETE SET NULL,
    source_url       VARCHAR(500),
    source_provider  VARCHAR(100),
    retrieval_ts     TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    license          VARCHAR(80),
    verification_status VARCHAR(30) NOT NULL DEFAULT 'PENDING'
        CHECK (verification_status IN ('PENDING','VERIFIED','UNVERIFIED','CONFLICT','RETRIED')),
    confidence       NUMERIC(4,3) CHECK (confidence BETWEEN 0.000 AND 1.000),
    original_source_record_id VARCHAR(100),          -- provider-native record ID
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
    bowling_style      VARCHAR(50),
    cricsheet_id       VARCHAR(50) UNIQUE,
    bcci_id            VARCHAR(50) UNIQUE,
    espn_id            VARCHAR(50) UNIQUE,
    identity_status    VARCHAR(20) NOT NULL DEFAULT 'UNRESOLVED'
        CHECK (identity_status IN ('UNRESOLVED','PROVISIONAL','RESOLVED')),
    is_active          BOOLEAN NOT NULL DEFAULT TRUE,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
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
    confidence_score NUMERIC(4,3) NOT NULL CHECK (confidence_score BETWEEN 0.000 AND 1.000),
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
-- 4b. venues (created before teams/matches, which reference it via FK)
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
    match_overs      INT NOT NULL DEFAULT 20 CHECK (match_overs > 0),
    balls_per_over   INT NOT NULL DEFAULT 6 CHECK (balls_per_over > 0),
    created_at       TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 7. seasons
-- ============================================================================
CREATE TABLE seasons (
    season_id      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    competition_id UUID NOT NULL REFERENCES competitions(competition_id) ON DELETE CASCADE,
    season_year    VARCHAR(20) NOT NULL,
    start_date     DATE NOT NULL,
    end_date       DATE NOT NULL,
    is_suspension  BOOLEAN NOT NULL DEFAULT FALSE,   -- represent the RR 2016-2017 suspension
    created_at     TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_season_comp UNIQUE (competition_id, season_year),
    CONSTRAINT chk_season_dates CHECK (end_date >= start_date)
);
CREATE INDEX idx_seasons_competition ON seasons(competition_id);

-- ============================================================================
-- 8. squad_memberships (seasonal contracts / squad inclusion)
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
    is_overseas   BOOLEAN NOT NULL DEFAULT FALSE,
    is_active_squad BOOLEAN NOT NULL DEFAULT TRUE,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_player_team_season UNIQUE (player_id, team_id, season_id)
);
CREATE INDEX idx_squad_team_season ON squad_memberships(team_id, season_id);
CREATE INDEX idx_squad_player ON squad_memberships(player_id);

-- ============================================================================
-- 8b. player_team_history (verified career team associations, cross-franchise)
-- ============================================================================
CREATE TABLE player_team_history (
    history_id      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    player_id       UUID NOT NULL REFERENCES players(player_id) ON DELETE CASCADE,
    team_id         UUID NOT NULL REFERENCES teams(team_id) ON DELETE RESTRICT,
    season_year     VARCHAR(20) NOT NULL,
    association_type VARCHAR(30) NOT NULL CHECK (association_type IN
        ('Squad','Played','Released','Retained','Acquired','Loan')),
    appearances     INT CHECK (appearances >= 0),
    evidence_source UUID REFERENCES data_sources(source_id) ON DELETE SET NULL,
    provenance_id   UUID REFERENCES source_records(record_id) ON DELETE SET NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_player_team_season UNIQUE (player_id, team_id, season_year)
);
CREATE INDEX idx_team_history_player ON player_team_history(player_id);

-- ============================================================================
-- 9. matches
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
    overs_scheduled    INT NOT NULL DEFAULT 20 CHECK (overs_scheduled > 0),
    status             VARCHAR(20) NOT NULL CHECK (status IN
        ('Scheduled','Completed','Abandoned','No Result')),
    created_at         TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_match_teams CHECK (home_team_id <> away_team_id)
);
CREATE INDEX idx_matches_date ON matches(match_date);
CREATE INDEX idx_matches_season ON matches(season_id);
CREATE INDEX idx_matches_venue ON matches(venue_id);

-- ============================================================================
-- 10. innings
-- ============================================================================
CREATE TABLE innings (
    innings_id     UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    match_id       UUID NOT NULL REFERENCES matches(match_id) ON DELETE CASCADE,
    innings_number INT NOT NULL CHECK (innings_number IN (1,2,3,4)),
    batting_team_id  UUID NOT NULL REFERENCES teams(team_id) ON DELETE RESTRICT,
    bowling_team_id  UUID NOT NULL REFERENCES teams(team_id) ON DELETE RESTRICT,
    is_super_over  BOOLEAN NOT NULL DEFAULT FALSE,
    overs_allocated NUMERIC(4,1) NOT NULL DEFAULT 20.0 CHECK (overs_allocated > 0),
    target_runs    INT CHECK (target_runs >= 0),
    target_overs   NUMERIC(4,1) CHECK (target_overs > 0),
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

-- ============================================================================
-- 11. deliveries (DESCRIPTIVE PARTITIONED by season_year)
-- ============================================================================
CREATE TABLE deliveries (
    delivery_id     UUID NOT NULL DEFAULT uuid_generate_v4(),
    innings_id      UUID NOT NULL,
    match_id        UUID NOT NULL,
    season_year     VARCHAR(20) NOT NULL,
    over_number     INT NOT NULL CHECK (over_number >= 0 AND over_number < 50),
    ball_in_over   INT NOT NULL CHECK (ball_in_over >= 1),
    delivery_sequence INT NOT NULL CHECK (delivery_sequence >= 1),
    batter_id       UUID NOT NULL,
    bowler_id       UUID NOT NULL,
    non_striker_id  UUID NOT NULL,
    runs_batter     INT NOT NULL CHECK (runs_batter BETWEEN 0 AND 6),
    runs_extras     INT NOT NULL DEFAULT 0,
    runs_total      INT NOT NULL CHECK (runs_total >= 0),
    is_wide         BOOLEAN NOT NULL DEFAULT FALSE,
    is_noball       BOOLEAN NOT NULL DEFAULT FALSE,
    is_bye          BOOLEAN NOT NULL DEFAULT FALSE,
    is_legbye       BOOLEAN NOT NULL DEFAULT FALSE,
    is_penalty      BOOLEAN NOT NULL DEFAULT FALSE,
    runs_wides      INT NOT NULL DEFAULT 0,
    runs_noballs    INT NOT NULL DEFAULT 0,
    runs_byes       INT NOT NULL DEFAULT 0,
    runs_legbyes    INT NOT NULL DEFAULT 0,
    runs_penalties  INT NOT NULL DEFAULT 0,
    is_wicket       BOOLEAN NOT NULL DEFAULT FALSE,
    wicket_kind     VARCHAR(30),
    player_out_id   UUID,
    is_bowler_credited_wicket BOOLEAN NOT NULL DEFAULT FALSE,
    match_phase     VARCHAR(20) NOT NULL CHECK (match_phase IN
        ('Powerplay','Middle 1','Middle 2','Death')),
    variation_type  VARCHAR(50),
    ball_speed_kph  NUMERIC(5,2),
    pitch_coordinate_x NUMERIC(6,3),
    pitch_coordinate_y NUMERIC(6,3),
    post_shot_landing_x NUMERIC(6,2),
    post_shot_landing_y NUMERIC(6,2),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_deliveries PRIMARY KEY (delivery_id, season_year),
    CONSTRAINT chk_runs_consistency CHECK (runs_total = runs_batter + runs_extras)
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

CREATE INDEX idx_deliveries_match_innings ON deliveries(match_id, innings_id);
CREATE INDEX idx_deliveries_batter ON deliveries(batter_id);
CREATE INDEX idx_deliveries_bowler ON deliveries(bowler_id);
CREATE INDEX idx_deliveries_matchup ON deliveries(batter_id, bowler_id);

-- ============================================================================
-- 12. batting_innings
-- ============================================================================
CREATE TABLE batting_innings (
    batting_innings_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    innings_id      UUID NOT NULL REFERENCES innings(innings_id) ON DELETE CASCADE,
    player_id       UUID NOT NULL REFERENCES players(player_id) ON DELETE RESTRICT,
    team_id         UUID NOT NULL REFERENCES teams(team_id) ON DELETE RESTRICT,
    batting_position INT NOT NULL CHECK (batting_position BETWEEN 1 AND 11),
    runs_scored     INT NOT NULL DEFAULT 0 CHECK (runs_scored >= 0),
    balls_faced     INT NOT NULL DEFAULT 0 CHECK (balls_faced >= 0),
    minutes_at_crease INT CHECK (minutes_at_crease >= 0),
    fours           INT NOT NULL DEFAULT 0,
    sixes           INT NOT NULL DEFAULT 0,
    dot_balls_faced INT NOT NULL DEFAULT 0,
    strike_rate     NUMERIC(6,2),
    dismissal_kind  VARCHAR(30),
    dismissal_bowler_id UUID REFERENCES players(player_id) ON DELETE SET NULL,
    dismissal_fielder_id UUID REFERENCES players(player_id) ON DELETE SET NULL,
    is_not_out      BOOLEAN NOT NULL DEFAULT TRUE,
    runs_powerplay  INT NOT NULL DEFAULT 0,
    balls_powerplay INT NOT NULL DEFAULT 0,
    runs_middle     INT NOT NULL DEFAULT 0,
    balls_middle    INT NOT NULL DEFAULT 0,
    runs_death      INT NOT NULL DEFAULT 0,
    balls_death     INT NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_innings_batter UNIQUE (innings_id, player_id),
    CONSTRAINT chk_balls_faced CHECK (dot_balls_faced <= balls_faced)
);
CREATE INDEX idx_batting_player ON batting_innings(player_id);

-- ============================================================================
-- 13. bowling_spells
-- ============================================================================
CREATE TABLE bowling_spells (
    spell_id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    innings_id         UUID NOT NULL REFERENCES innings(innings_id) ON DELETE CASCADE,
    player_id          UUID NOT NULL REFERENCES players(player_id) ON DELETE RESTRICT,
    team_id            UUID NOT NULL REFERENCES teams(team_id) ON DELETE RESTRICT,
    spell_order        INT NOT NULL DEFAULT 1,
    legal_balls_bowled INT NOT NULL DEFAULT 0,
    overs_completed    NUMERIC(4,1) NOT NULL DEFAULT 0.0,
    maidens            INT NOT NULL DEFAULT 0,
    runs_conceded      INT NOT NULL DEFAULT 0,
    wickets_taken      INT NOT NULL DEFAULT 0 CHECK (wickets_taken BETWEEN 0 AND 10),
    wides_bowled       INT NOT NULL DEFAULT 0,
    noballs_bowled     INT NOT NULL DEFAULT 0,
    dot_balls_bowled   INT NOT NULL DEFAULT 0,
    economy_rate       NUMERIC(5,2),
    bowling_average    NUMERIC(6,2),
    bowling_strike_rate NUMERIC(5,2),
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
    CONSTRAINT chk_dots_bowled CHECK (dot_balls_bowled <= legal_balls_bowled)
);
CREATE INDEX idx_bowling_player ON bowling_spells(player_id);

-- ============================================================================
-- 14. fielding_events
-- ============================================================================
CREATE TABLE fielding_events (
    fielding_event_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    delivery_id     UUID,
    season_year     VARCHAR(20) NOT NULL,
    player_id       UUID NOT NULL REFERENCES players(player_id) ON DELETE RESTRICT,
    is_substitute   BOOLEAN NOT NULL DEFAULT FALSE,
    event_type      VARCHAR(30) NOT NULL CHECK (event_type IN (
        'Catch','Run Out Thrower','Run Out Catcher','Stumping',
        'Dropped Catch','Missed Run Out','Boundary Save')),
    is_successful   BOOLEAN NOT NULL DEFAULT TRUE,
    assisted_by_player_id UUID REFERENCES players(player_id) ON DELETE SET NULL,
    fielding_position VARCHAR(40),
    runs_saved      INT DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_fielding_player ON fielding_events(player_id);
CREATE INDEX idx_fielding_delivery ON fielding_events(delivery_id);

-- ============================================================================
-- 14b. wicketkeeping_events
-- ============================================================================
CREATE TABLE wicketkeeping_events (
    wk_event_id      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    innings_id       UUID NOT NULL REFERENCES innings(innings_id) ON DELETE CASCADE,
    player_id        UUID NOT NULL REFERENCES players(player_id) ON DELETE RESTRICT,
    match_id         UUID NOT NULL REFERENCES matches(match_id) ON DELETE RESTRICT,
    stumpings        INT NOT NULL DEFAULT 0 CHECK (stumpings >= 0),
    catches          INT NOT NULL DEFAULT 0 CHECK (catches >= 0),
    missed_stumpings INT CHECK (missed_stumpings >= 0),
    missed_catches   INT CHECK (missed_catches >= 0),
    appearances      INT NOT NULL DEFAULT 1,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_wk_innings UNIQUE (innings_id, player_id)
);
CREATE INDEX idx_wk_player ON wicketkeeping_events(player_id);

-- ============================================================================
-- 16. pitch_conditions
-- ============================================================================
CREATE TABLE pitch_conditions (
    pitch_condition_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    match_id         UUID NOT NULL REFERENCES matches(match_id) ON DELETE CASCADE,
    venue_id         UUID NOT NULL REFERENCES venues(venue_id) ON DELETE RESTRICT,
    soil_type        VARCHAR(50),
    pitch_pace_rating   NUMERIC(3,1) CHECK (pitch_pace_rating BETWEEN 1.0 AND 10.0),
    pitch_bounce_rating NUMERIC(3,1) CHECK (pitch_bounce_rating BETWEEN 1.0 AND 10.0),
    pitch_turn_rating   NUMERIC(3,1) CHECK (pitch_turn_rating BETWEEN 1.0 AND 10.0),
    grass_coverage   VARCHAR(30),
    provenance_tier  VARCHAR(30) NOT NULL DEFAULT 'UNKNOWN' CHECK (provenance_tier IN
        ('DIRECTLY_MEASURED','OFFICIALLY_REPORTED','THIRD_PARTY_ESTIMATE','MODEL_INFERRED','UNKNOWN')),
    source_curator_notes TEXT,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_match_pitch UNIQUE (match_id)
);

-- ============================================================================
-- 17. weather_conditions
-- ============================================================================
CREATE TABLE weather_conditions (
    weather_condition_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    match_id            UUID NOT NULL REFERENCES matches(match_id) ON DELETE CASCADE,
    observation_timestamp TIMESTAMPTZ NOT NULL,
    temperature_celsius NUMERIC(4,1),
    relative_humidity_pct NUMERIC(4,1) CHECK (relative_humidity_pct BETWEEN 0.0 AND 100.0),
    dew_point_celsius   NUMERIC(4,1),
    dew_impact_index    VARCHAR(20),
    wind_speed_kmh      NUMERIC(5,2) CHECK (wind_speed_kmh >= 0),
    wind_direction_degrees INT CHECK (wind_direction_degrees BETWEEN 0 AND 360),
    precipitation_mm    NUMERIC(5,2) CHECK (precipitation_mm >= 0),
    atmospheric_pressure_hpa NUMERIC(6,1),
    cloud_cover_pct     NUMERIC(4,1) CHECK (cloud_cover_pct BETWEEN 0.0 AND 100.0),
    data_provenance_flag VARCHAR(100) NOT NULL DEFAULT
        'Macro Environmental Context (Not Direct Pitch Moisture)',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_match_weather_obs UNIQUE (match_id, observation_timestamp)
);
CREATE INDEX idx_weather_match ON weather_conditions(match_id);

-- ============================================================================
-- 18. player_availability
-- ============================================================================
CREATE TABLE player_availability (
    availability_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    player_id      UUID NOT NULL REFERENCES players(player_id) ON DELETE CASCADE,
    season_id      UUID NOT NULL REFERENCES seasons(season_id) ON DELETE CASCADE,
    start_date     DATE NOT NULL,
    end_date       DATE NOT NULL,
    availability_status VARCHAR(30) NOT NULL,
    matches_expected_available INT,
    reason_for_unavailability TEXT,
    national_board_noc_granted BOOLEAN NOT NULL DEFAULT TRUE,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_player_season_avail UNIQUE (player_id, season_id, start_date),
    CONSTRAINT chk_avail_dates CHECK (end_date >= start_date)
);

-- ============================================================================
-- 19. player_injuries
-- ============================================================================
CREATE TABLE player_injuries (
    injury_id   UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    player_id   UUID NOT NULL REFERENCES players(player_id) ON DELETE CASCADE,
    injury_date DATE,
    injury_type VARCHAR(50),
    body_part   VARCHAR(50),
    severity    VARCHAR(20) CHECK (severity IN ('Minor','Moderate','Severe','Catastrophic')),
    surgery_required BOOLEAN NOT NULL DEFAULT FALSE,
    recovery_time_days INT,
    return_to_play_date DATE,
    recurrence_risk_score NUMERIC(3,2),
    medical_notes TEXT,
    verified    BOOLEAN NOT NULL DEFAULT FALSE,   -- NEVER fabricate; unverified injuries stay FALSE
    created_at  TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_injuries_player ON player_injuries(player_id);

-- ============================================================================
-- 19b. player_awards
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
-- 19c. player_competition_history
-- ============================================================================
CREATE TABLE player_competition_history (
    comp_history_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    player_id       UUID NOT NULL REFERENCES players(player_id) ON DELETE CASCADE,
    competition_id  UUID NOT NULL REFERENCES competitions(competition_id) ON DELETE RESTRICT,
    season_year     VARCHAR(20) NOT NULL,
    appearances     INT CHECK (appearances >= 0),
    coverage_status VARCHAR(30) NOT NULL CHECK (coverage_status IN
        ('VERIFIED_PARTICIPATION','DATASET_UNAVAILABLE','NOT_ESTABLISHED','CONFIRMED_NON_PARTICIPATION')),
    provenance_id   UUID REFERENCES source_records(record_id) ON DELETE SET NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_player_comp_season UNIQUE (player_id, competition_id, season_year)
);
CREATE INDEX idx_comp_history_player ON player_competition_history(player_id);

-- ============================================================================
-- 20. user_teams
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
-- 21. user_team_players
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
-- 22. derived_features
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
    model_version     VARCHAR(20) NOT NULL DEFAULT 'v2.0',
    source_provenance UUID REFERENCES source_records(record_id) ON DELETE SET NULL,
    computed_at       TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_player_feature UNIQUE (player_id, feature_name, calculation_window, model_version, COALESCE(format_tag,''))
);
CREATE INDEX idx_derived_features_player ON derived_features(player_id);
CREATE INDEX idx_derived_features_group ON derived_features(feature_group);
```

### 10.3 Key Schema Rules
- **Canonical `player_id`** is the single join key across every engine and service.
- **Raw ↔ normalised ↔ derived separation**: `source_records` (immutable), the normalised
  core (entities 3–21), and `derived_features` are never merged.
- **`is_suspension`** on `seasons` represents the RR 2016–2017 suspension explicitly.
- **`coverage_status`** encodes the four CDCRE states so "absent from dataset" is never read
  as "never played".

---

## 11. Engine Determinism & LLM Independence

- **Deterministic database queries** are used for all known facts and statistics (CPPAE, CMIE,
  SICE read paths). No LLM is required on the deterministic path.
- **External research** (PIRE/TMVE/CDCRE where internal records are insufficient) is used for
  evidence **discovery and verification** only, with provenance recorded by Service C.
- **No engine is made dependent on an LLM** for correctness; LLM-assisted research output is
  always flagged as `THIRD_PARTY_ESTIMATE` or `MODEL_INFERRED` and routed for human review when
  it affects identity, membership, or eligibility.

---

## 12. Streamlit Presentation Requirements

### 12.1 Required Views
1. Home / Team Builder  2. Player Search  3. Player Identity Verification  4. Historical RR
   Membership  5. Player Career Profile  6. Performance Analytics  7. Contextual Analysis  8.
   Player Comparison  9. Squad Composition  10. Squad Intelligence Report  11. Data Source and
   Verification Report.

### 12.2 Session State Discipline
- Use `st.session_state` **only** for ephemeral UI state (current team, active player, filters).
- **No analytics calculation** may live in Streamlit; all views render MIE/engine outputs.
- Components (Streamlit functions) must be separated from engine calls via thin adapters.

### 12.3 Frontend-Agnostic Guarantee
The Streamlit layer consumes the same structured contracts defined in §2–§8 as any future
Next.js frontend; no engine imports Streamlit.

---

## 13. API / Service Specification (frontend-agnostic)

| Capability | Contract | Description |
|---|---|---|
| `resolve_player(name)` | PIRE | Identity resolution + confidence + warnings |
| `verify_membership(player_id)` | TMVE | Six-class membership + RR seasons + evidence |
| `discover_career(player_id)` | CDCRE | Competition history + coverage + provenance |
| `analyse_performance(player_id, formats, window)` | CPPAE | Full performance profile |
| `contextualise(player_id)` | CMIE | Condition annotations with provenance tiers |
| `evaluate_squad(user_team_id)` | SICE | Squad intelligence report |
| `generate_profile_export(player_id, fmt)` | Service B | JSON/CSV export |
| `get_provenance(record_id)` | Service C | Source provenance + verification status |
| `upsert_user_team(user_team)` | Service E | Team create/update |
| `request_player_intelligence(name, team_id)` | MIE | Orchestrated end-to-end report |

All responses are versioned, structured objects; every derived field carries `source_provenance`
and, where applicable, a `format_tag` (no cross-format mixing).

---

## 14. Non-Functional Specifications

- **Determinism**: identical inputs → identical outputs on the deterministic path.
- **Zero fabrication**: missing → `NULL`; no invented players, matches, injuries, or memberships.
- **Evidence-backed**: every membership/eligibility claim carries a `verification_records` entry.
- **Format-aware**: cross-format comparisons are prohibited without explicit normalisation tags.
- **Licensing**: all exports embed ODC-By (CricSheet) and CC BY 4.0 (Open-Meteo) attribution;
  the proprietary hackathon dataset is kept confidential and isolated.
