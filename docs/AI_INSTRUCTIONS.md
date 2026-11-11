# AI Architectural Principles, Coding Standards & Domain Guardrails

**Project Title**: RR Squad Intelligence & Team Composition Platform
**Event**: IPL 2027 Hackathon
**Target Franchise**: Rajasthan Royals (RR)
**Document Version**: 2.2.0
**Status**: `[STATUS: ACTIVE MANDATORY DIRECTIVE - GREENFIELD BASELINE]`
**Date**: November 2026
**Primary Authors**: Principal Software Architect, Systems Governance Lead, Lead Cricket Data Scientist

> **Revision Note (v2.2.0, PVRE Architecture Mandates)**: This directive now governs the
> **RR Squad Intelligence & Team Composition Platform** (MIE + seven specialised engines + five
> support services over a 33-entity PostgreSQL core). Adds mandatory domain rules R13–R22 governing
> PVRE dual-mode verification, replacement intelligence boundaries, zero uncapped inference from
> database absence, mandatory `REVIEW_REQUIRED` safety gating, and strict separation between the
> hackathon Top-10 ranking and incumbent replacement evaluation.
>
> **Revision Note (v2.0.0, retained for history)**: This directive governed the earlier baseline
> (MIE + seven engines + support services). It adds mandatory guardrails for
> **player identity**, **team membership**, and **evidence verification**, and updates
> the data directory to `datasets/`. The tenet "use LLMs everywhere" is **rejected**:
> deterministic queries serve known facts; external research is used only for evidence
> discovery/verification and is always provenance-tracked.

---

## 1. Purpose & Authority

This document is the **Supreme Engineering Constitution** for all AI agents, software engineers,
and automated code-synthesis systems in this repository.

Every engine design, database migration, analytical formulation, service interface, Streamlit
component, and test suite MUST comply with the principles, standards, and domain guardrails
below. Any change that violates any directive is rejected by the **Data Quality & Coverage
Agent** and the **Chief Architect**.

---

## 2. Core Architectural Tenets

```
+----------------------------------------------------------------------------------------------------+
|                                    CORE ARCHITECTURAL TENETS (REVISED)                             |
+----------------------------------------------------------------------------------------------------+
|  1. DETERMINISTIC REPRODUCIBILITY                                                                  |
|     Identical inputs -> identical outputs. Seeded randomness only where documented.              |
|                                                                                                    |
|  2. CENTRAL NORMALISED 3NF RELATIONAL CORE (33 ENTITIES)                                           |
|     Zero redundant transaction data; strict referential integrity; canonical player_id.            |
|                                                                                                    |
|  3. READ-ONLY IMMUTABLE DATA LAKE                                                                  |
|     Raw source files in `datasets/` are immutable; staged into read-only raw tables.              |
|                                                                                                    |
|  4. EVIDENCE & PROVENANCE FIRST                                                                    |
|     Every external/membership/eligibility claim traces to a verification record + data source.    |
|                                                                                                    |
|  5. STRICT SEPARATION OF CONCERNS                                                                  |
|     Ingestion -> Staging -> Normalisation -> Research -> Analytics -> MIE -> Presentation.        |
|                                                                                                    |
|  6. FRONTEND-AGNOSTIC ENGINES                                                                      |
|     No engine imports a UI framework. Streamlit (initial) and Next.js (future) both consume        |
|     the same typed contracts.                                                                      |
|                                                                                                    |
|  7. NO LLM-DEPENDENCE FOR CORRECTNESS                                                              |
|     Known facts/statistics come from deterministic queries. LLM-assisted research is flagged     |
|     (third-party estimate / model-inferred) and routed to human review when it affects identity,  |
|     membership, or eligibility.                                                                    |
+----------------------------------------------------------------------------------------------------+
```

### 2.1 Deterministic Reproducibility
- All deterministic statistical calculations must yield identical results from identical raw
  inputs. Stochastic routines MUST require an explicit integer seed.

### 2.2 Central Normalised 3NF Relational Core
- All player/match/delivery entities reside in a normalised 3NF PostgreSQL 16 schema across 31
  entities (`derived_features` is the single documented non-3NF feature-store exception).
- Redundant attributes forbidden; deliveries reference canonical entity IDs via foreign keys.
- High-volume rollups live in `derived_features`, isolated from the operational core.

### 2.3 Read-Only Immutable Data Lake
- `datasets/` is immutable; no agent mutates, renames, or appends to it.
- Raw payloads are copied to PostgreSQL staging with SHA-256 digests; malformed payloads are
  quarantined without halting the run.

### 2.4 Evidence & Provenance
- Every derived or externally-sourced claim stores `source_record` provenance (see
  `verification_records`: URL, provider, retrieval timestamp, licence, verification status,
  confidence, original record ID).

---

## 3. Technology Stack & Coding Standards

```
+----------------------------------------------------------------------------------------------------+
|                                    APPROVED TECHNOLOGY STACK (REVISED)                             |
+-------------------+-----------------------------------+--------------------------------------------+
| Layer             | Technology / Framework            | Standard                                  |
+-------------------+-----------------------------------+--------------------------------------------+
| Initial UI        | Streamlit                         | Latest stable; thin adapters, no analytics|
| Future UI         | Next.js / React / TypeScript      | Reuses engine contracts; not in MVP       |
| Core Engines      | Python                            | 3.11+ (strict typing, PEP 8)            |
| Database Core     | PostgreSQL                          | 16.0+ (3NF, 33 entities)                  |
| Scientific Math   | NumPy / Pandas / SciPy             | NumPy 1.26+, Pandas 2.2+                      |
| Orchestration     | MIE + typed engine contracts       | UI-independent, versioned                     |
| Data Sources      | CricSheet, Kaggle, HawkeyeStats,  | Provenance-tracked, licence-compliant         |
                    | Open-Meteo, official records        |                                             |
+-------------------+-----------------------------------+--------------------------------------------+
```

### 3.1 Python Standards
1. **PEP 8 + strict type hints** across all engines and services.
2. **Typed contracts**: engine request/response models as Pydantic (or frozen dataclasses),
   versioned, and documented with Google-style docstrings.
3. **Immutability** for fact records (completed deliveries, scorecard rows).
4. **Frontend independence**: engines must import no UI framework; the Streamlit layer is the
   only consumer that imports Streamlit.

### 3.2 SQL & Database Standards
1. Plural `snake_case` table names; singular `snake_case` column names; FKs as
   `<referenced_singular>_id`.
2. `TIMESTAMPTZ` UTC timestamps (ISO-8601).
3. Precise numeric types: strike rates/economies `NUMERIC(6,2)`; probabilities `NUMERIC(5,4)`;
   coordinates `NUMERIC(6,3)`; INR `NUMERIC(14,2)`.
4. Foreign keys default `ON DELETE RESTRICT` for audit tables.
5. **Format-aware storage**: derived statistics carry a `format_tag`; no cross-format mixing
   without it.

### 3.3 Streamlit Standards (Initial UI)
1. `st.session_state` used **only** for ephemeral UI state (active team, active player, filters).
2. **No analytics in Streamlit**: every rendered figure comes from an engine/service contract.
3. Per-view thin adapters isolate views from engine calls; views are UI components, not
   calculations.
4. The Data Source & Verification Report view must surface UNVERIFIED and CONFLICT items
   explicitly.

---

## 4. Identity, Membership & Evidence-Verification Mandates

The integrity of this platform rests on three verification domains. AI agents and engineers MUST
enforce the following.

### 4.1 Player Identity (PIRE)
- **Never merge two players merely because their names are similar.**
- Identity resolution uses the 4-tier waterfall (registry key → verified alias → deterministic
  contextual intersection → fuzzy + **contextual attribute corroboration**: DOB, hand, role,
  active era — these are registry/cricketing attributes, **not biometric identifiers**).
  Low-confidence or multi-candidate results are quarantined with `needs_review=TRUE` and routed
  to user clarification or human review.
- **Tier outcomes are deterministic; the fuzzy thresholds (Jaro-Winkler ≥ 0.92, Levenshtein ≤
  2) are tunable configuration parameters, not calibrated probabilities.** A numeric
  `confidence` is exposed only after calibration against a labelled test set
  (`calibrated=TRUE`); otherwise it is `NULL`.
- **Identity, membership, career-coverage, and eligibility confidences are separate
  measurements**, reported by their respective engines; PIRE reports identity status only.
- Unresolved identities are stored with `identity_status='UNRESOLVED'`/`PROVISIONAL`; they are
  never silently assigned to an existing player.

### 4.2 Team Membership & Eligibility (TMVE) — three independent dimensions
These dimensions must **never be conflated** into a single label:
- **Dimension 1 — RR relationship** (`rr_relationship_state`): `CURRENT_RR_SQUAD`,
  `HISTORICAL_RR_APPEARANCE`, `HISTORICAL_RR_SQUAD_ONLY`, `PREVIOUSLY_ASSOCIATED`,
  `NO_VERIFIED_RR_RELATIONSHIP`, `RR_RELATIONSHIP_UNKNOWN`.
- **Dimension 2 — Current membership** (`rr_current_state`): `CURRENT`, `NOT_CURRENT`,
  `UNKNOWN` — verified **separately** from relationship history.
- **Dimension 3 — IPL eligibility / uncapped classification** (`eligibility_status`,
  season-bound, `eligibility_policies` version): `VERIFIED_ELIGIBLE`, `VERIFIED_NOT_ELIGIBLE`,
  `ELIGIBILITY_UNVERIFIED`, `NOT_ASSESSED`.

Mandates:
- **`CURRENT_RR_SQUAD` is assigned only with verified current-season squad evidence.**
- **Squad inclusion is not a match appearance**: a player on a squad list is not counted as a
  verified appearance (`appearances = 0`, state `HISTORICAL_RR_SQUAD_ONLY`).
- **Historical membership is not current membership**: a former RR player is not re-classified
  as current.
- **RR 2016–2017 suspension is a franchise participation fact** (IPL continued for all other
  teams), recorded in `team_season_participation` as `SUSPENDED` — never a competition-wide
  property. Membership analysis runs 2008–2015 (PARTICIPATING) / 2016–17 (SUSPENDED) /
  2018–2026 (PARTICIPATING) / 2027 (**UNKNOWN until authoritative squad evidence exists**).
- **A player who does not appear in a record base is `RR_RELATIONSHIP_UNKNOWN`, not
  `NO_VERIFIED_RR_RELATIONSHIP`**, unless the full TRD §4.5 negative-verification requirements
  are met (coverage scope, relevant RR seasons, squad-list + scorecard coverage, source
  quality, conflicting-evidence handling, human review).

### 4.3 Evidence Verification (Service C)
- Every external claim records source URL, provider, retrieval timestamp, licence, verification
  status, **evidence tier (1–5 per the verification hierarchy)**, confidence (only when
  calibrated), and original record ID.
- **The verification hierarchy** is: (1) official IPL/franchise records, (2) official
  scorecards, (3) BCCI records, (4) reliable cricket databases, (5) reputable secondary
  reporting.
- **CONFLICT** between sources routes to human review; MIE does not auto-resolve.
- **Absence in a dataset is `DATASET_UNAVAILABLE` / `NOT_ESTABLISHED`**, never
  `CONFIRMED_NON_PARTICIPATION`.
- **The product must never automatically assume an unknown player is uncapped**; an unknown
  player defaults to `NOT_ASSESSED` eligibility and `RR_RELATIONSHIP_UNKNOWN`.
- **Eligibility policy is versioned, season-bound, source-traceable (BCCI/IPL rule reference),
  independently verified, and effective-date aware** — never a hardcoded rule in application
  logic.

---

## 5. Statistical Correctness & Domain Rules

The following domain rules are mandatory. AI agents and engineers MUST enforce them.

```
+----------------------------------------------------------------------------------------------------+
|                                    DOMAIN COMMANDMENTS (REVISED)                                   |
+----------------------------------------------------------------------------------------------------+
|  R1: NEVER treat missing as zero (NULL, not 0.0)                                                  |
|  R2: NEVER fabricate or hallucinate statistics, players, or memberships                           |
|  R3: NEVER confuse bowling style with delivery variation                                          |
|  R4: NEVER interpret Hawk-Eye post-shot ball coordinates as fielder coordinates                    |
|  R5: NEVER attribute byes/leg-byes/penalty runs to bowler runs conceded                            |
|  R6: STRICT Super Over isolation from career aggregates                                            |
|  R7: RAIN-INTERRUPTED (DLS) revised-target accounting                                             |
|  R8: NEVER infer a player's mental state from match statistics                                     |
|  R9: NEVER fabricate injury histories (unverified injuries stay flagged)                           |
|  R10: NEVER mix IPL/T20/List A/first-class statistics without format-aware comparison             |
|  R11: NEVER represent weather as a direct measurement of pitch conditions                          |
|  R12: NEVER make an unsupported membership or eligibility claim (absent evidence = UNVERIFIED)     |
|  R13: NEVER equate missing database records with uncapped status (absence != uncapped)             |
|  R14: NEVER treat absence of RR evidence as verified non-membership without TRD §4.5 requirements   |
|  R15: NEVER merge two identities because of similar names; maintain strict collision boundaries    |
|  R16: NEVER treat unverified browser snippets or search results as verified facts                  |
|  R17: NEVER overwrite conflicting evidence; preserve source conflicts and flag REVIEW_REQUIRED     |
|  R18: ALWAYS apply REVIEW_REQUIRED when mandatory evidence is incomplete or contradictory          |
|  R19: NEVER invent statistics, match appearances, or career participation (missing = NULL)         |
|  R20: NEVER make replacement or release decisions inside PVRE (analytical signals to SICE only)    |
|  R21: NEVER mix the Top-10 ranking model with incumbent replacement evaluation                     |
|  R22: NEVER expose secrets, credentials, or proprietary hackathon content in public outputs        |
+----------------------------------------------------------------------------------------------------+
```

### Rule R1 — Never treat missing as zero
- Missing ball speed / tracking coordinates / unrecorded figures stay `NULL`.
- Zero dismissals → batting average `NULL`; zero overs bowled → economy `NULL`.

### Rule R2 — Never fabricate
- No synthetic player profiles, invented match records, or placeholder deliveries.
- No invented membership, injury, or eligibility. The Data Quality Agent checksums aggregates
  against raw deliveries and terminates builds on deviation.

### Rule R3 — Bowling style vs variation
- `players.bowling_style` is the registered physical style; `deliveries.variation_type` is the
  per-ball tactic. Matrix aggregations use registered style only.

### Rule R4 — Hawk-Eye post-shot coordinates
- Ball terminal coordinates are never fielder positions.

### Rule R5 — Runs-conceded exclusion
- Bowler runs conceded excludes byes, leg-byes, and penalty runs.

### Rule R6 — Super Over isolation
- `is_super_over = TRUE` deliveries are excluded from career views by default.

### Rule R7 — DLS accounting
- Rain-truncated matches use the official revised target/overs for run-rate denominators.

### Rule R8 — No mental-state inference
- Performance under pressure is expressed via measured leverage situations (e.g., high-leverage
  deliveries), never as a claim about a player's psychology or mental health.

### Rule R9 — No fabricated injuries
- `player_injuries` rows carry `verified BOOLEAN`; unverified records remain `verified=FALSE`
  and are labelled accordingly.

### Rule R10 — Format awareness
- T20, List A, and first-class figures are tagged by `format_tag`; comparisons across formats
  require documented normalisation and are flagged when not available.

### Rule R11 — Weather ≠ pitch
- Ambient weather is a macro-context/dew proxy, labelled as such; it is never presented as
  direct pitch-soil measurement.

### Rule R12 — Unsupported claims stay UNVERIFIED
- Membership, eligibility, and career claims lacking verified evidence are returned as
  `UNVERIFIED` / `NOT_ESTABLISHED`, never as positive or negative determinations.

### Rule R13 — Never equate missing database records with uncapped status
- Absence from the internal database or external datasets is **never** proof of uncapped status.
- Unknown players default strictly to `eligibility_status = 'NOT_ASSESSED'`.
- A player enters the verified uncapped pool only when affirmative evidence verifies zero senior
  international appearances and compliance with the active target-season policy.

### Rule R14 — Never treat absence of RR records as verified non-membership
- Negative RR membership (`NO_VERIFIED_RR_RELATIONSHIP`) is permitted only when all TRD §4.5
  requirements are satisfied (dataset completeness, all RR seasons checked, squad + scorecard
  presence verified negative, source tier-1/tier-2 quality, human analyst sign-off).
- In all other cases of missing or partial records, the state must remain `RR_RELATIONSHIP_UNKNOWN`.

### Rule R15 — Never merge two identities due to name similarity
- Disambiguation must rely on deterministic contextual attribute corroboration (DOB, playing role,
  batting/bowling style, active era).
- Ambiguous or colliding identities must route immediately to `REVIEW_REQUIRED`; auto-merging is
  strictly prohibited.

### Rule R16 — Never treat browser search snippets as verified facts
- Web search summaries, snippets, or unverified browser text are strictly third-party hints.
- Facts require ingestion into `source_records` and validation in `verification_records` with
  documented licence, provider, timestamp, and tier.

### Rule R17 — Never overwrite conflicting evidence
- When source records materially disagree (e.g. conflicting dates of birth, disputed match counts),
  competing claims must be preserved with `verification_status = 'CONFLICT'`.
- AI agents are strictly prohibited from silently picking a winner or averaging conflicting values.

### Rule R18 — Always apply `REVIEW_REQUIRED` when mandatory evidence is insufficient
- Whenever mandatory identity attributes, RR membership status, or eligibility evidence are
  missing, unverified, or contradictory, the execution flow must halt automated routing and
  emit a structured review dossier.
- Unresolved cases must never enter the candidate pool.

### Rule R19 — Never invent statistics or career participation
- Squad inclusion never implies match appearances; squad-only alumni must show `appearances = 0`
  and receive no batting or bowling statistics.
- Missing competition records must be reported as `DATASET_UNAVAILABLE` or `NOT_ESTABLISHED`,
  never assumed as zero matches.

### Rule R20 — Never make replacement decisions inside PVRE
- PVRE produces evidence dossiers and structured analytical signals (`RETAIN_SIGNAL`,
  `MONITOR_SIGNAL`, `POTENTIALLY_REPLACEABLE`, `INSUFFICIENT_EVIDENCE`, `REVIEW_REQUIRED`).
- PVRE is strictly prohibited from deciding to release, replace, or retain a player, and from
  inventing arbitrary replacement probabilities. Final squad evaluations belong to SICE and
  franchise leadership.

### Rule R21 — Never mix the Top-10 ranking model with replacement evaluation
- The Top-10 youngest eligible uncapped candidate ranking (`RANKING_SPEC.md` `RK-1.0.0`) is a
  standalone hackathon competition deliverable.
- It must never be combined, merged, or averaged with PVRE Mode A incumbent replacement evaluation,
  which compares specific incumbent roles against candidate alternatives.

### Rule R22 — Never expose secrets, credentials, or proprietary hackathon data
- API keys, credentials, and confidential hackathon datasets must never appear in Git repositories,
  public logs, or client-side JSON/CSV exports.

---

## 6. Prohibited Practices & Security Guardrails

The following actions are **strictly prohibited** across all agents and scripts.

```
+----------------------------------------------------------------------------------------------------+
|                                    STRICT SYSTEM PROHIBITIONS (REVISED)                            |
+----+------------------------------------------------------------------------------------------------+
| #  | Prohibited Action                                                                    |
+----+----------------------------------------------------------------------------------------+
| P1 | Generating synthetic / mock / hallucinated player or match records                  |
| P2 | Mutating, renaming, or deleting raw files inside `datasets/`                        |
| P3 | Imputing missing values with 0.0 or arbitrary averages                             |
| P4 | Allowing Super Over statistics to increment career totals                           |
| P5 | Attributing byes/leg-byes/penalty runs to bowler runs conceded                     |
| P6 | Merging two players solely because their names are similar                          |
| P7 | Classifying an unknown player as uncapped/eligible or as `NO_VERIFIED_RR_RELATIONSHIP` without the TRD §4.5 evidence|
| P8 | Inferring a player's mental state from match statistics                            |
| P9 | Fabricating injury histories or eligibility facts                                   |
| P10| Representing weather as a direct pitch-condition measurement                       |
| P11| Making an engine depend on an LLM for deterministic correctness                     |
| P12| Using raw, unparameterised SQL (mandatory SQLi prevention)                          |
| P13| Leaking the proprietary hackathon dataset into public outputs or exports           |
| P14| Performing analytics inside Streamlit (engines must be UI-independent)             |
+----+----------------------------------------------------------------------------------------+
```

### 6.1 Database Security
All database interactions use parameterised queries or the ORM. Raw string interpolation of user
input into SQL is forbidden.

### 6.2 Deterministic-Query Mandate
Known facts and statistics are served by deterministic database queries. External research is used
for **evidence discovery and verification** only, with provenance recorded by Service C.

### 6.3 Human-Review Mandate
Ambiguous player identities and conflicting evidence **require human review**; no agent auto-
resolves them.

---

## 7. Conclusion & Engineering Attestation

This directive forms an unbroken chain of architectural and domain constraints. By enforcing
deterministic reproducibility, a normalised 33-entity 3NF core (with `derived_features` as the
single documented non-3NF exception), an immutable data lake, evidence-first provenance, the
three-dimension membership model (relationship · currency · season-bound eligibility), the
franchise-level participation model, the four-state coverage model, and the domain rules above,
the team guarantees that the **RR Squad Intelligence & Team Composition Platform** is built on
forensic accuracy, evidence-backed verification, and production engineering standards.
