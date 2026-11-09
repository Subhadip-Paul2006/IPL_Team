# System Architecture & Technical Design Specification
**Product**: RR Squad Intelligence & Team Composition Platform
**Focus Franchise**: Rajasthan Royals (RR) · **Primary Interface (initial)**: Streamlit
**Document Version**: 2.0.0 (ARCHITECTURE REVISION)
**Status**: [STATUS: PLANNED - GREENFIELD BASELINE]
**Author**: Engineering Architecture Team (`teamwork_worker_2`)

> **Revision Note (v2.0.0)**: The architecture has been re-centred on the **Mother
> Intelligence Engine (MIE)** orchestrating **six specialised engines** (PIRE, TMVE, CDCRE,
> CPPAE, CMIE, SICE) and **five support services**, with a **Streamlit** initial frontend that
> is strictly separated from the analytical core. The raw data directory is `datasets/`
> (previously `CricSheet/`). The central database now spans **27 entities**. Engines expose
> frontend-agnostic contracts so a future Next.js frontend can reuse them unchanged.

---

## 1. Architectural Overview & Design Principles

> **Architecture Baseline Status**: `[STATUS: PLANNED - GREENFIELD BASELINE]`
> All diagrams and Architectural Decision Records (ADRs) depict the approved target state.

The RR Squad Intelligence & Team Composition Platform is an evidence-backed decision-support
system. Its workflow: user creates a team → enters a player name → MIE resolves identity,
verifies RR membership, discovers the career, analyses performance, adds contextual
intelligence, and evaluates the assembled squad. The architecture is guided by seven principles:

1. **Central Orchestration (MIE)**: A single Mother Intelligence Engine coordinates the six
   specialised engines, merges their outputs, and returns structured responses. MIE never
   invents statistics or makes unsupported membership decisions.
2. **Frontend-Agnostic Engines**: Every engine and MIE exposes typed input/output contracts
   independent of any UI framework. Streamlit is the **initial** consumer; a future Next.js
   frontend reuses the same layer.
3. **Strict 3NF Relational Core**: A 27-entity PostgreSQL 16 schema enforces referential
   integrity; canonical `player_id` is used across all engines.
4. **Raw / Normalised / Derived Separation**: immutable raw payloads, normalised records, and
   `derived_features` are strictly segregated.
5. **Evidence & Provenance First**: external research is authorised, provenance-tracked, and
   verification-statused; membership/eligibility claims never rest on a single unverified source.
6. **Deterministic Queries**: known facts and statistics are served by deterministic database
   queries; external research is used only for evidence discovery and verification.
7. **No LLM-Dependency for Correctness**: no engine requires an LLM on its deterministic path;
   LLM-assisted research output is always flagged (third-party estimate / model-inferred) and
   routed for human review when it affects identity, membership, or eligibility.

---

## 2. System Architecture Diagrams

All diagrams use Mermaid. Node identifiers avoid reserved keywords; edges are explicit.

### 2.1 Diagram 1: High-Level Orchestration Architecture

```mermaid
flowchart TD
    subgraph UI["Presentation Tier (Streamlit - INITIAL / Next.js FUTURE)"]
        V_TeamBuilder["Home / Team Builder"]
        V_Search["Player Search"]
        V_Verify["Identity Verification"]
        V_Membership["Historical RR Membership"]
        V_Career["Player Career Profile"]
        V_Analytics["Performance Analytics"]
        V_Context["Contextual Analysis"]
        V_Compare["Player Comparison"]
        V_Squad["Squad Composition"]
        V_Report["Squad Intelligence Report"]
        V_Provenance["Data Source & Verification Report"]
    end

    subgraph MIE["Mother Intelligence Engine (MIE) - Central Orchestrator"]
        MIE_Orchestrator["Request Router & Engine Coordinator"]
        MIE_Merge["Output Merger & Unified Report Builder"]
        MIE_Verif["Verification Status & Provenance Tracker"]
    end

    subgraph Engines["Six Specialised Engines"]
        PIRE["ENGINE 01: PIRE - Identity Resolution"]
        TMVE["ENGINE 02: TMVE - Membership Verification"]
        CDCRE["ENGINE 03: CDCRE - Career Discovery"]
        CPPAE["ENGINE 04: CPPAE - Performance Analytics"]
        CMIE["ENGINE 05: CMIE - Contextual Match Intelligence"]
        SICE["ENGINE 06: SICE - Squad Intelligence & Composition"]
    end

    subgraph Services["Five Support Services"]
        S_Ingest["A: Data Ingestion"]
        S_ProfileGen["B: Player Profile Generator"]
        S_Provenance["C: Source Verification & Provenance"]
        S_Quality["D: Data Quality & Coverage"]
        S_TeamBuilder["E: Team Builder"]
    end

    subgraph Storage["Central PostgreSQL 16 Core (27 Entities, 3NF)"]
        DB_Core[("players, matches, deliveries, batting_innings, ...")]
        DB_Provenance[("data_sources, source_records, verification_records")]
        DB_User[("user_teams, user_team_players")]
        DB_Features[("derived_features")]
    end

    V_TeamBuilder --> MIE_Orchestrator
    V_Search --> MIE_Orchestrator
    V_Verify --> MIE_Orchestrator
    V_Membership --> MIE_Orchestrator
    V_Career --> MIE_Orchestrator
    V_Analytics --> MIE_Orchestrator
    V_Context --> MIE_Orchestrator
    V_Compare --> MIE_Orchestrator
    V_Squad --> MIE_Orchestrator
    V_Report --> MIE_Orchestrator
    V_Provenance --> MIE_Orchestrator

    MIE_Orchestrator --> PIRE
    MIE_Orchestrator --> TMVE
    MIE_Orchestrator --> CDCRE
    MIE_Orchestrator --> CPPAE
    MIE_Orchestrator --> CMIE
    MIE_Orchestrator --> SICE

    PIRE --> MIE_Merge
    TMVE --> MIE_Merge
    CDCRE --> MIE_Merge
    CPPAE --> MIE_Merge
    CMIE --> MIE_Merge
    SICE --> MIE_Merge

    MIE_Merge --> MIE_Verif
    MIE_Verif --> S_Provenance
    S_Provenance --> DB_Provenance

    PIRE --> DB_Core
    TMVE --> DB_Core
    CDCRE --> DB_Core
    CPPAE --> DB_Core
    CMIE --> DB_Core
    SICE --> DB_Core
    SICE --> DB_User
    S_TeamBuilder --> DB_User

    S_Ingest --> DB_Provenance
    S_Ingest --> DB_Core
    S_ProfileGen --> DB_Core
    S_Quality --> DB_Core
```

### 2.2 Diagram 2: MIE Orchestration Workflow (End-to-End Player Intelligence)

```mermaid
flowchart TD
    Start(["User enters player name in Streamlit"]) --> MIE_Accept["MIE: Accept Player Search Request"]
    MIE_Accept --> PIRE_Run["PIRE: Resolve Identity (4-tier waterfall)"]
    PIRE_Run --> PIRE_Res{"Resolved with confidence >= 0.95?"}

    PIRE_Res -- "Yes" --> InternalDB["Internal Database Search (TMVE + CDCRE)"]
    PIRE_Res -- "No / Ambiguous" --> ExtResearch["Authorised External Research (CDCRE + research service)"]
    ExtResearch --> IdentityReview["Identity Review (provenance-tracked)"]
    IdentityReview --> Ambig{"Still ambiguous?"}
    Ambig -- "Yes" --> UserClarify["Request User Clarification"] --> MIE_Accept
    Ambig -- "No" --> InternalDB

    InternalDB --> TMVE_Run["TMVE: Verify RR Membership (6-class)"]
    TMVE_Run --> TMVE_Res{"Internal records sufficient?"}
    TMVE_Res -- "No" --> ExtResearch
    TMVE_Res -- "Yes" --> Classify["Player Classification (CURRENT_SQUAD / HISTORICAL_RR_PLAYER / PREVIOUSLY_ASSOCIATED / NEVER_REPRESENTED_RR / UNVERIFIED / ELIGIBILITY_UNVERIFIED)"]

    Classify --> CDCRE_Run["CDCRE: Career Discovery & Coverage Tracking"]
    CDCRE_Run --> CPPAE_Run["CPPAE: Performance Analytics (format-aware)"]
    CPPAE_Run --> CMIE_Run["CMIE: Contextual Match Intelligence (provenance tiers)"]
    CMIE_Run --> Unified["MIE: Unified Player Intelligence Report"]
    Unified --> AddTeam["User Adds Player to Team (Service E)"]
    AddTeam --> SICE_Run["SICE: Evaluate Complete Team"]
    SICE_Run --> SquadReport["Squad Report & Recommendations (Service B export)"]
```

### 2.3 Diagram 3: Player Identity Resolution (PIRE) Workflow

```mermaid
flowchart TD
    Input(["Incoming Raw Player Name String"]) --> T1{"Tier 1: Canonical Registry Key Present?"}
    T1 -- "Yes" --> T1Match{"Match in players?"}
    T1Match -- "Yes" --> T1OK["Resolve Canonical player_id (Confidence 1.000)"] --> Done(["PIRE Output: Resolved"])
    T1Match -- "No" --> T2
    T1 -- "No" --> T2{"Tier 2: Exact Match in player_aliases?"}
    T2 -- "Yes" --> T2OK["Resolve player_id (Confidence 1.000)"] --> Done
    T2 -- "No" --> T3{"Tier 3: Name + Team + Date Intersection?"}
    T3 -- "Unique Match" --> T3OK["Resolve player_id (Confidence 0.980)"] --> Done
    T3 -- "Ambiguous / None" --> T4["Tier 4: Jaro-Winkler + Levenshtein + Biometrics (DOB, hand, era)"]
    T4 --> T4Score{"Score >= 0.950 and single candidate?"}
    T4Score -- "Yes" --> T4OK["Resolve player_id, insert alias (is_verified=FALSE)"] --> Done
    T4Score -- "No / Multiple candidates" --> Quarantine["QUARANTINE: needs_review=TRUE"] --> Human(["Human Review Queue / User Clarification"])
```

### 2.4 Diagram 4: Team Membership Verification (TMVE) Decision Flow

```mermaid
flowchart TD
    P(["Canonical player_id from PIRE"]) --> QueryHist["Query squad_memberships + player_team_history + matches (RR team)"]
    QueryHist --> HasApp{"Verified RR match appearances?"}
    HasApp -- "Yes" --> Seasons["Identify RR seasons (2008-2015 | 2016-2017 suspension | 2018+)"]
    Seasons --> CurrentCheck{"Verified CURRENT-season squad evidence?"}
    CurrentCheck -- "Yes" --> CL_CURRENT["Classify: CURRENT_SQUAD"]
    CurrentCheck -- "No" --> CL_HIST["Classify: HISTORICAL_RR_PLAYER"]
    HasApp -- "No, but documented association" --> CL_ASSOC["Classify: PREVIOUSLY_ASSOCIATED"]
    HasApp -- "No, verified absence in full record base" --> CL_NEVER["Classify: NEVER_REPRESENTED_RR"]
    HasApp -- "Insufficient evidence" --> CL_UNVERIFIED["Classify: UNVERIFIED (NOT never)"]
    CL_ASSOC --> Other["Record other IPL teams + retention/auction facts"]
    CL_HIST --> Other
    CL_NEVER --> Other
    Other --> Out(["TMVE Output: class + evidence + confidence"])
```

### 2.5 Diagram 5: Data Ingestion & Provenance Architecture

```mermaid
flowchart TD
    subgraph Sources["Data Sources"]
        SRC_Cric["CricSheet in datasets/ (JSON/YAML)"]
        SRC_Kaggle["Kaggle Historicals"]
        SRC_Hawkeye["HawkeyeStats Telemetry"]
        SRC_Weather["Historical Weather (Open-Meteo)"]
        SRC_Official["Official BCCI / ICC Records"]
        SRC_Research["Verified External Research (provenance-tracked)"]
    end

    subgraph Ingest["Service A: Data Ingestion"]
        Hasher["SHA-256 Digest Generator"]
        Staging[("source_records (immutable raw staging)")]
        DLQ[("Quarantine / Dead-Letter")]
        Validator["Pydantic Schema Validation Gate"]
    end

    subgraph Provenance["Service C: Source Verification & Provenance"]
        VRec[("verification_records")]
        DSrc[("data_sources")]
    end

    SRC_Cric --> Hasher
    SRC_Kaggle --> Hasher
    SRC_Hawkeye --> Hasher
    SRC_Weather --> Hasher
    SRC_Official --> Hasher
    SRC_Research --> Hasher

    Hasher --> Staging
    Staging --> Validator
    Validator -- "Valid" --> Normalise["Normalisation into 27-entity core"]
    Validator -- "Malformed" --> DLQ
    Hasher --> VRec
    Hasher --> DSrc
```

### 2.6 Diagram 6: Performance Analytics & Derived Feature Flow

```mermaid
flowchart TD
    Sub(["Canonical player_id"]) --> Fetch["Deterministic queries: batting_innings, bowling_spells, fielding_events, wicketkeeping_events, player_awards"]
    Fetch --> Format["Format-aware filtering (IPL/T20 vs List A vs first-class; no mixing)"]
    Format --> Calc["CPPAE: compute documented statistics (NULL-safe, no zero-imputation)"]
    Calc --> Persist[("derived_features (versioned, format-tagged)")]
    Persist --> Cache["Optional in-memory cache"]
    Cache --> Out(["CPPAE.Output: structured performance profile"])
```

### 2.7 Diagram 7: Central Database Entity-Relationship Diagram (27 Entities)

```mermaid
erDiagram
    PLAYERS ||--o{ PLAYER_ALIASES : "has"
    PLAYERS ||--o{ SQUAD_MEMBERSHIPS : "belongs_to"
    PLAYERS ||--o{ PLAYER_TEAM_HISTORY : "associated_with"
    PLAYERS ||--o{ PLAYER_COMPETITION_HISTORY : "played_in"
    PLAYERS ||--o{ PLAYER_AWARDS : "received"
    PLAYERS ||--o{ PLAYER_AVAILABILITY : "tracked_in"
    PLAYERS ||--o{ PLAYER_INJURIES : "affected_by"
    PLAYERS ||--o{ BATTING_INNINGS : "bats_in"
    PLAYERS ||--o{ BOWLING_SPELLS : "bowls_in"
    PLAYERS ||--o{ FIELDING_EVENTS : "fields_in"
    PLAYERS ||--o{ WICKETKEEPING_EVENTS : "keeps_in"
    PLAYERS ||--o{ DERIVED_FEATURES : "evaluated_in"
    PLAYERS ||--o{ USER_TEAM_PLAYERS : "selected_in"
    TEAMS ||--o{ SQUAD_MEMBERSHIPS : "contracts"
    TEAMS ||--o{ PLAYER_TEAM_HISTORY : "linked_to"
    TEAMS ||--o{ MATCHES : "plays"
    TEAMS ||--o{ INNINGS : "bats_bowls"
    TEAMS ||--o{ SEASONS : "competes_in"
    COMPETITIONS ||--o{ SEASONS : "has"
    COMPETITIONS ||--o{ PLAYER_COMPETITION_HISTORY : "context_of"
    SEASONS ||--o{ SQUAD_MEMBERSHIPS : "applies_to"
    SEASONS ||--o{ MATCHES : "contains"
    VENUES ||--o{ MATCHES : "hosts"
    VENUES ||--o{ PITCH_CONDITIONS : "has_surface"
    MATCHES ||--o{ INNINGS : "comprises"
    MATCHES ||--o{ PITCH_CONDITIONS : "has_surface_match"
    MATCHES ||--o{ WEATHER_CONDITIONS : "experiences"
    MATCHES ||--o{ FIELDING_EVENTS : "includes"
    MATCHES ||--o{ WICKETKEEPING_EVENTS : "includes"
    INNINGS ||--o{ DELIVERIES : "contains_balls"
    INNINGS ||--o{ BATTING_INNINGS : "records_batting"
    INNINGS ||--o{ BOWLING_SPELLS : "records_bowling"
    INNINGS ||--o{ WICKETKEEPING_EVENTS : "records_wk"
    DELIVERIES ||--o{ FIELDING_EVENTS : "results_in"
    USER_TEAMS ||--o{ USER_TEAM_PLAYERS : "contains"
    DATA_SOURCES ||--o{ SOURCE_RECORDS : "provides"
    DATA_SOURCES ||--o{ VERIFICATION_RECORDS : "backed_by"
    SOURCE_RECORDS ||--o{ VERIFICATION_RECORDS : "evidenced_in"
    PLAYER_TEAM_HISTORY }o--|| DATA_SOURCES : "evidence_source"
    PLAYER_COMPETITION_HISTORY }o--|| SOURCE_RECORDS : "provenance"
```

> The 27 entities: `players`, `player_aliases`, `teams`, `competitions`, `seasons`,
> `squad_memberships`, `player_team_history`, `matches`, `innings`, `deliveries`,
> `batting_innings`, `bowling_spells`, `fielding_events`, `wicketkeeping_events`, `venues`,
> `pitch_conditions`, `weather_conditions`, `player_availability`, `player_injuries`,
> `player_awards`, `player_competition_history`, `user_teams`, `user_team_players`,
> `data_sources`, `source_records`, `verification_records`, `derived_features`.
> Full DDL, PK/FK/index definitions: `docs/TRD.md §10`.

### 2.8 Diagram 8: Squad Intelligence & Composition (SICE) Evaluation Flow

```mermaid
flowchart TD
    T(["user_team_id (Service E)"]) --> Load["Load team players (user_team_players) + role assignments"]
    Load --> Roles["Analyse role distribution & depth (batting, bowling, WK, all-rounders)"]
    Roles --> Balance["Pace/spin balance, batting-order flexibility, role duplication"]
    Balance --> History["Historical contribution (CPPAE-derived) per role"]
    History --> Compare["Compare similar-role players; identify replacements"]
    Compare --> Gaps["Weak/missing roles + dependency analysis"]
    Gaps --> Combos["Evaluate squad combinations & alternative lineups"]
    Combos --> Recs["Evidence-backed recommendations (no probabilities unless model validated)"]
    Recs --> Out(["SICE.Output: Squad Intelligence Report"])
```

### 2.9 Diagram 9: Streamlit Presentation Tier

```mermaid
flowchart LR
    subgraph Streamlit["Streamlit App (initial UI)"]
        SUI["11 required views (see PRD §6)"]
        SSESS["st.session_state (ephemeral UI state only)"]
    end
    SUI --> SSESS
    SUI --> Adapter["Thin UI adapters (no analytics in Streamlit)"]
    Adapter --> MIE["MIE / engine structured contracts"]
    MUI["Next.js frontend (future)"] --> MIE
```

### 2.10 Diagram 10: Evidence & Verification Flow (MIE → Provenance)

```mermaid
flowchart TD
    Claim(["Any membership / career / eligibility claim"]) --> VLookup["Service C: lookup verification_records"]
    VLookup --> VState{"verification_status?"}
    VState -- "VERIFIED" --> Cite["Cite: source URL + provider + timestamp + licence + confidence + original record ID"]
    VState -- "UNVERIFIED / PENDING" --> Flag["Flag in report; list under Data Source & Verification Report"]
    VState -- "CONFLICT" --> HumanReview["Route to human review; MIE does not auto-resolve"]
    Cite --> Report["Unified Player Intelligence Report"]
    Flag --> Report
    HumanReview --> Report
```

---

## 3. Architectural Decision Records (ADRs)

### ADR-001: PostgreSQL 16 3NF Core with Season Partitioning
- **Status**: APPROVED TARGET `[STATUS: PLANNED]`
- **Context**: The engine analyses >250,000 delivery rows across 2008–2026 plus multi-competition
  career data. A document store risks inconsistent player names and broken joins.
- **Decision**: PostgreSQL 16 3NF across 27 entities; `deliveries` partitioned by
  `season_year` (including a 2024–2027 partition to admit a future 2027 season).
- **Consequences**: referential integrity, partition pruning, and a stable canonical `player_id`.

### ADR-002: Mother Intelligence Engine as the Single Orchestration Point
- **Status**: APPROVED TARGET
- **Context**: Prior design had engines invoked directly by the UI, creating ad-hoc sequencing
  and inconsistent merging.
- **Decision**: A central MIE accepts search requests, coordinates all six engines in a fixed
  dependency order, merges outputs, tracks verification status, and returns a single structured
  report. MIE never invents statistics or makes membership decisions.
- **Consequences**: deterministic orchestration, single audit point, engine contracts stable.

### ADR-003: Frontend-Agnostic Engine Contracts (Streamlit now, Next.js later)
- **Status**: APPROVED TARGET
- **Context**: The initial product ships as a Streamlit application, but the analytical core must
  outlive that UI.
- **Decision**: All engines and MIE expose typed, versioned, UI-independent contracts. Streamlit
  sessions never perform analytics; a future Next.js layer consumes identical contracts.
- **Consequences**: no engine imports a UI framework; UI swaps do not require re-architecting
  analytics.

### ADR-004: Four-State Coverage + Six-Class Membership to Prevent False Negatives
- **Status**: APPROVED TARGET
- **Context**: Naïve absence-of-data reads create false "never played RR" / "uncapped" labels.
- **Decision**: `player_competition_history.coverage_status` uses four states
  (verified / dataset-unavailable / not-established / confirmed-non-participation); TMVE uses a
  six-class membership taxonomy where "insufficient evidence" maps to `UNVERIFIED`, never to
  `NEVER_REPRESENTED_RR`.
- **Consequences**: unknowns are surfaced for review instead of silently misclassified.

### ADR-005: Evidence & Provenance Records with Verification Status
- **Status**: APPROVED TARGET
- **Context**: Authorised external research is required, but unverified external claims must not
  masquerade as verified facts.
- **Decision**: `verification_records` + `data_sources` capture source URL, provider, retrieval
  timestamp, licence, verification status, confidence, and original record ID. MIE tracks
  verification status and routes CONFLICT to human review.
- **Consequences**: every external claim is auditable and licence-compliant.

### ADR-006: Deterministic Queries First, LLM-Optional Research
- **Status**: APPROVED TARGET
- **Context**: Making every engine depend on an LLM is fragile, non-reproducible, and costly.
- **Decision**: Known facts and statistics are served by deterministic database queries.
  External research (with LLM assistance where useful) is used only for evidence discovery and
  verification; such output is flagged third-party-estimate / model-inferred and requires
  human review when it affects identity, membership, or eligibility.
- **Consequences**: reproducible core; research stays isolated, flagged, and auditable.

### ADR-007: RR Suspension Period Represented as a First-Class State
- **Status**: APPROVED TARGET
- **Context**: RR were suspended for IPL 2016–2017 and returned in 2018; naive season
  enumeration would misclassify the gap.
- **Decision**: `seasons.is_suspension` flag plus TMVE segmentation (2008–2015 / suspension /
  2018+ / 2027-future). No squad data is generated for suspension years without the flag.
- **Consequences**: membership analysis is historically accurate and judge-auditable.

---

## 4. Verification & Architecture Integrity

1. **Syntax Validation**: All Mermaid diagrams validated against Mermaid parser rules; node
   identifiers unique, edges explicit.
2. **Relational Completeness**: The ERD (Diagram 7) mirrors the 27-entity DDL in
   `docs/TRD.md §10` (PKs, FKs, cardinalities).
3. **Contract Consistency**: Engine I/O contracts in `docs/TRD.md §3–§13` match MIE orchestration
   (Diagram 2) and the SICE flow (Diagram 8).
4. **Cross-Document Consistency**: Terminology, entity names, and the six-class membership
   taxonomy match across `PRD.md`, `TRD.md`, `ARCHITECTURE.md`, `PHASES.md`, `AGENTS.md`, and
   `AI_INSTRUCTIONS.md`.
5. **Streamlit Independence Check**: An automated import test confirms no engine module imports
   Streamlit (see PRD AC-13).
