# Product Requirements Document (PRD)

**Project Title**: RR Squad Intelligence & Team Composition Platform
**Target Franchise**: Rajasthan Royals (RR)
**Primary Interface (initial)**: Streamlit · **Future Frontend**: Next.js (engines are frontend-agnostic)
**Document Version**: 2.0.0-ARCH-REVISION
**Status**: `[STATUS: PLANNED - GREENFIELD BASELINE]`
**Date**: November 2026
**Primary Authors**: Principal Software Architect, Sports Data Engineer, Cricket Analytics Researcher, Technical Documentation Engineer

> **Revision Note (v2.0.0)**: This PRD was revised to describe the evolved product — a squad
> intelligence & team composition platform with verified player identity, membership and
> career discovery — replacing the previous auction-war-room-centric specification. The
> IPL 2027 hackathon context is retained as the deadline driver and evaluation frame.

---

## 1. Executive Summary & Problem Statement

### 1.1 Context
The platform serves the **IPL 2027 Hackathon** and long-term Rajasthan Royals squad-building
needs. Franchise decision-makers (front office, coaches, analysts) need an **evidence-backed**
way to:

- Identify any cricket player reliably by name, including players unknown to the internal data
  lake (domestic uncapped prospects, overseas players, players from other IPL franchises).
- Verify whether a player has represented Rajasthan Royals, and distinguish **historical RR
  players** from **current squad members** (with the RR 2016–2017 suspension represented
  separately and IPL 2027 treated as a future target season).
- Retrieve and analyse a player's complete cricket career across competitions.
- Build a team composition from verified, profiled players and receive a squad-intelligence
  evaluation of the assembled team.

### 1.2 Product Vision
The **RR Squad Intelligence & Team Composition Platform** is a modular analytical system that
turns a user-supplied player name into a verified, evidence-backed player intelligence report,
and evaluates user-built teams. It is **initially delivered as a Streamlit application**, with
the analytical core kept independent of the UI so a future Next.js frontend can reuse it.

**The product must support all of the following player populations:**
- Existing RR players · Former RR players · Players who have never represented RR ·
  Domestic uncapped prospects · Players from other IPL franchises · International players ·
  Players whose identity or eligibility remains unverified.

> **First principle**: *The platform must never automatically assume that an unknown player is
> an uncapped player.* Unknown ≠ uncapped; unknown = `UNVERIFIED` until established otherwise.

### 1.3 Historical Context (Rajasthan Royals)
- RR franchise membership analysis **begins with IPL 2008** and the first phase runs **2008–2015**.
- RR were **suspended for IPL 2016 and 2017**; the suspension period must be represented
  separately (never analysed as normal seasons, never filled with fabricated data).
- RR returned in **2018**; post-return historical squad analysis covers **2018 onwards**.
- The primary post-return analytical window initially covers **2018–2026**.
- **IPL 2027 is a future target season**: it is treated as such until actual participation and
  squad records are verified.

### 1.4 The Failure of Naive Team Building
- Classifying a player who played for RR in a prior season as a current squad member.
- Treating a squad-list appearance as a match appearance.
- Treating a missing record as proof of non-participation ("not in the dataset" ≠ "never played").
- Auto-labeling any unrecognized name as an "uncapped domestic prospect".
- Mixing IPL/T20, List A and first-class figures without format-aware comparison.
- Inferring mental state or fabricating injury histories from match statistics.

---

## 2. Target Users & Stakeholder Personas

The system is engineered to serve five distinct stakeholder personas within the Rajasthan Royals
organization, each with dedicated operational goals, technical proficiencies, core queries, and
required outputs.

```
+-------------------------------------------------------------------------------------------------------+
|                                    RAJASTHAN ROYALS DECISION HIERARCHY                                |
+-------------------------------------------------------------------------------------------------------+
|  Franchise Chief Executive (CEO) & Ownership                                                          |
|  - High-level squad risk, ROI, compliance sign-off                                                     |
+-------------------------------------------------------------------------------------------------------+
                                  |
                                  v
+----------------------------------------------------+--------------------------------------------------+
| Head of Cricket Operations                         | Squad Strategist & Composition Lead              |
| - Squad balance, depth, overseas/role caps         | - Team building, candidate evaluation, pivots    |
+----------------------------------------------------+--------------------------------------------------+
                                  |
                                  v
+----------------------------------------------------+--------------------------------------------------+
| Lead Cricket Data Analyst                          | Batting & Bowling Coaching Staff                |
| - Evidence review, provenance audits               | - Role fit, matchup plans, pitch plans          |
+----------------------------------------------------+--------------------------------------------------+
```

### 2.1 Persona 1: Lead Cricket Data Analyst
- **Profile**: Quantitative researcher with sports analytics, Python, SQL and probabilistic modelling skills.
- **Primary Goals**: Verify player identity, membership and career claims end-to-end; inspect evidence and provenance behind every figure.
- **Frustrations & Pain Points**: Black-box databases; missing-value imputation; unverifiable claims; identity collisions on common surnames.
- **Core Questions**:
  - *"Has this player actually played for RR, and in which seasons — with evidence?"*
  - *"What is the provenance of this statistic and how confident are we in it?"*
- **Required Outputs & Interfaces**: Data Source and Verification Report view, provenance-traced player profiles, JSON/CSV exports.

### 2.2 Persona 2: Head of Cricket Operations
- **Profile**: Senior administrator responsible for roster construction, squad balance and regulatory compliance.
- **Primary Goals**: Maintain a transparent overview of squad composition; verify eligibility and membership; monitor role depth and dependencies.
- **Frustrations & Pain Points**: Fragmented scouting notes; unverified player lists; confusing role overlap.
- **Core Questions**:
  - *"Which players in my team have verified current RR membership, and which are historical or unverified?"*
  - *"What roles does my squad lack, and who are evidence-backed alternatives?"*
- **Required Outputs & Interfaces**: Squad Composition view, Squad Intelligence Report, role-distribution summaries.

### 2.3 Persona 3: Squad Strategist & Composition Lead
- **Profile**: Strategic decision-maker building the target team composition for a season or the 2027 auction pool.
- **Primary Goals**: Assemble a balanced squad; compare candidate vs incumbent role occupants; test alternative combinations.
- **Frustrations & Pain Points**: No structured way to compare similar-role players; no quantitative weakness analysis.
- **Core Questions**:
  - *"If I swap Player A for candidate Player B in the same role, how do squad strengths/weaknesses change?"*
  - *"Which role duplications and gaps exist in my current composition?"*
- **Required Outputs & Interfaces**: Player Comparison view, SICE recommendations, alternative-combination analyses.

### 2.4 Persona 4: Batting & Bowling Coaching Staff
- **Profile**: Domain tacticians responsible for on-field execution and matchday opposition plans.
- **Primary Goals**: Digest role-specific performance evidence and matchup context in plain, actionable form.
- **Frustrations & Pain Points**: Dense statistical reports; weather data presented as pitch measurements.
- **Core Questions**:
  - *"How does this player perform in the death phase, and in what conditions?"*
  - *"Which opponents does he historically struggle against?"*
- **Required Outputs & Interfaces**: Performance Analytics view, Contextual Analysis view, one-page printable player cards.

### 2.5 Persona 5: Franchise Chief Executive & Ownership
- **Profile**: Executive leadership responsible for multi-year franchise value and governance.
- **Primary Goals**: Approve squad direction; ensure governance, licensing and evidence integrity across outputs.
- **Frustrations & Pain Points**: Unsupported claims in reports; unverifiable analytics; missing licensing attribution.
- **Core Questions**:
  - *"What evidence supports this squad's expected strength profile?"*
  - *"Which conclusions in this report are verified vs estimated?"*
- **Required Outputs & Interfaces**: Executive summary of the Squad Intelligence Report, verification-status summary.

---

## 3. Product Objectives & Hackathon-Specific Goals

### 3.1 Strategic Product Objectives
1. **Evidence-Backed Intelligence**: Every player report is traceable to verified sources; verification status is always visible.
2. **Squad Composition Capability**: Users can build, edit and evaluate teams; the Squad Intelligence Engine delivers role-aware analysis and recommendations.
3. **Correct Membership Semantics**: Six-class membership taxonomy enforced; current vs historical RR status never conflated; RR 2016–2017 suspension represented separately; IPL 2027 treated as a future target season.
4. **Talent Pipeline Continuity**: Uncapped domestic prospects are supported *as one of many* player populations, discovered via career research — never assumed from absence.

### 3.2 Hackathon Evaluation Alignment
| Priority | Hackathon Criterion | Platform Capability |
|---|---|---|
| **High** | **Analytical & Domain Rigor** | Evidence-backed player profiles; six-class membership; coverage-state tracking; format-aware statistics; zero fabrication |
| **High** | **System Architecture & Engineering** | MIE orchestration of six engines + five services; 27-entity 3NF PostgreSQL core; deterministic queries; provenance records |
| **High** | **Usability & Actionability** | Streamlit 11-view application; team builder; squad intelligence report; comparison views |
| **Medium** | **Innovation** | Authorised external research integration with verification; unified player intelligence reports; squad dependency analysis |
| **Lower** | **Simulation Extras** | Monte Carlo, EAP regression and live war-room simulation are long-term enhancements, not MVP (see §7) |

---

## 4. User Workflow (Primary)

The complete workflow the product implements:

```
User opens Streamlit
        |
Creates a team
        |
Enters player name
        |
Mother Intelligence Engine
        |
Player Identity Resolution (PIRE)
        |
Internal Database Search
        |
Is player identified?
   /             \
  No              Yes
  |                |
External research  Membership verification (TMVE)
  |                |
Identity review    |
        \          /
         Player classification (6 classes)
                  |
       Career Discovery Engine (CDCRE)
                  |
       Performance Analytics (CPPAE)
                  |
       Contextual Match Analysis (CMIE)
                  |
       Unified Player Profile
                  |
       User adds player to team
                  |
       Squad Intelligence Engine (SICE)
                  |
       Squad report and recommendations
```

**Branching rules:**
- If identity remains ambiguous, **request user clarification** — the system does not guess.
- If external research cannot establish membership, the player is returned as **UNVERIFIED**.
- The system **does not automatically convert failed searches into proof of non-membership**;
  absence of evidence is reported as `UNVERIFIED` / `NOT_ESTABLISHED`, never as `NEVER_REPRESENTED_RR`.

### 4.1 Use Case 1: Verified Team Building (MVP Core)
1. User creates a team in the Team Builder view.
2. User searches for a player by name (any known alias or spelling).
3. PIRE resolves identity; user confirms on the Identity Verification view when ambiguity exists.
4. TMVE classifies membership (e.g., HISTORICAL_RR_PLAYER, seasons 2008–2015; other IPL teams listed).
5. User reviews the Career Profile and Performance Analytics views.
6. User adds the player to the team, optionally assigning a role.
7. SICE evaluates the team; user reviews the Squad Intelligence Report and adjusts.

### 4.2 Use Case 2: Uncapped Prospect Discovery (MVP Supported Population)
1. User searches for a domestic prospect name.
2. PIRE/CDCRE perform authorised external research; CDCRE reports career coverage per competition
   (e.g., SMAT: VERIFIED_PARTICIPATION; Ranji: NOT_ESTABLISHED) — without assuming uncapped status.
3. TMVE reports membership class (typically NEVER_REPRESENTED_RR only when a verified record base
   supports it; otherwise UNVERIFIED).
4. CPPAE presents career evidence-backed performance with format tags.
5. User adds the player to a team; SICE notes role fit and comparison vs incumbents.

### 4.3 Use Case 3: Squad Gap Analysis (MVP Core)
1. SICE analyses the assembled team: batting depth, bowling depth, pace/spin balance, wicketkeeping,
   all-rounders, batting-order flexibility, role duplication, weak/missing roles.
2. SICE compares role occupants and suggests alternatives with evidence references.
3. Report clearly labels outputs as *analytical recommendations*, never as official RR selections
   or auction decisions; no recruitment probabilities unless a calibrated model exists.

---

## 5. Functional Requirements

Requirements are grouped by engine/service. Detailed I/O contracts live in `docs/TRD.md` (§3–§13).

### 5.1 Player Identity Resolution (PIRE)
- **FR-P1**: Resolve exact, aliased, varied and misspelt player names to canonical player IDs.
- **FR-P2**: Detect and disambiguate duplicate/near-duplicate players; verify DOB where available.
- **FR-P3**: Output identity confidence, known aliases, matching records, and unresolved warnings.
- **FR-P4**: Route low-confidence or multi-candidate cases to user clarification.
- **FR-P5**: **Never merge two players merely because their names are similar.**

### 5.2 Team Membership Verification (TMVE)
- **FR-M1**: Classify every player into exactly one of the six membership classes.
- **FR-M2**: Verify **actual RR match appearances** (count verified appearances; squad inclusion
  alone is not a match appearance).
- **FR-M3**: Identify RR seasons of representation; respect the 2008–2015 / 2016–2017 suspension /
  2018-onwards segmentation; treat 2027 as a future target season.
- **FR-M4**: Identify other IPL teams and documented retention/auction/transfer/release facts.
- **FR-M5**: Verify current squad membership **separately** from historical membership.
- **FR-M6**: When internal records are insufficient, trigger authorised external research with
  the documented verification hierarchy (official records > scorecards > BCCI > reliable
  databases > reputable reporting); attach evidence and confidence.

### 5.3 Career Discovery & Competition Research (CDCRE)
- **FR-C1**: Discover career across IPL franchises, domestic state teams, Ranji, SMAT, Vijay
  Hazare, Duleep, India A/age-group, international cricket and other recognised T20 leagues.
- **FR-C2**: Report season participation, team history and career gaps.
- **FR-C3**: Track data coverage and record source provenance for every external claim.
- **FR-C4**: Distinguish verified participation / dataset coverage unavailable / participation not
  established / confirmed non-participation — and **never** infer non-participation from dataset
  absence.

### 5.4 Complete Player Performance Analytics (CPPAE)
- **FR-A1**: Produce batting profiles: innings, matches, runs, average, strike rate, boundaries,
  dot balls, batting positions, opening/top-order/middle-order/finishing splits, performance vs
  individual bowlers, vs pace/spin, vs bowling styles and verified delivery variations, phase
  splits, win/loss splits, partnership contributions.
- **FR-A2**: Produce bowling profiles: overs, runs, wickets, economy, average, strike rate, dot
  balls, phase splits, batter-specific matchups, pace/spin classification, delivery speed and
  line/length **when available**.
- **FR-A3**: Produce fielding profiles: catches, run-outs, stumpings, recorded dropped catches,
  opportunities, positions where verified, contribution measures.
- **FR-A4**: Produce wicketkeeping profiles: dismissals, catches, stumpings, recorded missed
  chances, appearances.
- **FR-A5**: Produce match-contribution profiles: POTM awards, participation, batting/bowling
  contribution, match situation, contribution to outcomes, measurable pressure performance.
- **FR-A6**: Every statistic carries a documented definition and calculation method.
- **FR-A7**: Do not compute unverified statistics from incomplete data; missing ≠ zero.
- **FR-A8**: No cross-format (IPL/T20/List A/first-class) comparisons without format-aware
  comparison.

### 5.5 Contextual Match Intelligence (CMIE)
- **FR-X1**: Annotate performance with opposition, venue, pitch conditions, weather, match format,
  innings, phase, required run rate, target and result.
- **FR-X2**: Classify each contextual datum into: directly measured / officially reported /
  third-party estimate / model-inferred / unknown.
- **FR-X3**: Weather must never be represented as a direct measurement of pitch conditions.
- **FR-X4**: Never infer a player's mental state from match statistics.

### 5.6 Squad Intelligence & Composition (SICE)
- **FR-S1**: Analyse role distribution, batting depth, bowling depth, pace/spin balance,
  wicketkeeping, all-rounder availability, batting-order flexibility, role duplication, weak or
  missing roles.
- **FR-S2**: Analyse historical contribution; compare players in similar roles; identify
  replacements; compare current squad players vs new candidates; evaluate squad combinations.
- **FR-S3**: Provide squad overview, strengths/weaknesses, dependency analysis, role-specific
  recruitment priorities, alternative combinations, and evidence-backed recommendations.
- **FR-S4**: Recommendations are labelled as analytical, not official selections/auction decisions.
- **FR-S5**: No recruitment probabilities unless the underlying model is statistically validated
  and calibrated.

### 5.7 Support Services
- **FR-VA1 (Ingestion)**: Import CricSheet datasets, Kaggle datasets, HawkeyeStats, historical
  weather, official records, and verified research data with provenance.
- **FR-VB1 (Profile Generator)**: Emit standardised JSON and CSV exports from the central database.
- **FR-VC1 (Provenance)**: Record source URL, provider, retrieval timestamp, licence, verification
  status, confidence, and original source record ID for every external claim.
- **FR-VD1 (Quality & Coverage)**: Detect missing data, duplicates, conflicting statistics,
  invalid player associations, inconsistent match identities, unavailable contextual features.
- **FR-VE1 (Team Builder)**: Manage user teams, player add/remove, composition, role assignment,
  and saved team configurations.

### 5.8 Streamlit Application
- **FR-U1**: Implement the eleven required views (see §6).
- **FR-U2**: Use session state carefully; separate UI components from analytics calculations.
- **FR-U3**: Keep core engines independent of Streamlit (reusable by a future Next.js frontend).

---

## 6. Streamlit Views (UI Requirements)

1. **Home / Team Builder** — create/rename/delete teams; add/remove players; assign roles; save configurations.
2. **Player Search** — name entry, PIRE candidates ranked by identity confidence, ambiguity prompts.
3. **Player Identity Verification** — side-by-side candidate evidence, DOB/role corroboration, confirm-or-review flow.
4. **Historical RR Membership** — six-class badge, RR seasons (2008–2015 / suspension / 2018+), other IPL teams, evidence links and verification date.
5. **Player Career Profile** — competition coverage table with four coverage states, gaps, provenance.
6. **Performance Analytics** — CPPAE profile: batting/bowling/fielding/WK/match-contribution with per-stat definitions and format tags.
7. **Contextual Analysis** — CMIE annotations with provenance-tier badges (measured / reported / estimated / inferred / unknown).
8. **Player Comparison** — side-by-side comparison of players occupying similar roles, with SICE notes.
9. **Squad Composition** — role distribution chart, depth view, current team contents with membership classes.
10. **Squad Intelligence Report** — strengths/weaknesses, dependencies, recruitment priorities, alternative combinations, recommendations with evidence.
11. **Data Source and Verification Report** — per-claim provenance, verification status, licences, confidence; UNVERIFIED items listed explicitly.

---

## 7. Scope Boundaries: MVP vs Post-MVP vs Out-of-Scope

```
+-------------------------------------------------------------------------------------------------------+
|                                        SYSTEM SCOPE PARTITION                                         |
+-------------------------------------------------------------------------------------------------------+
|  MVP (HACKATHON-ESSENTIAL)                                                                            |
|  • MIE orchestration + PIRE (identity resolution)                                                      |
|  • TMVE (6-class membership verification, RR 2008-2015/suspension/2018+ segmentation)                  |
|  • CDCRE (career discovery + 4-state coverage tracking)                                                |
|  • CPPAE (documented performance profiles, format-aware)                                               |
|  • CMIE (contextual annotations + 5-tier provenance, weather/pitch separation)                        |
|  • SICE (role/depth/balance analysis, comparisons, recommendations)                                    |
|  • Services A–E (ingestion, profile export, provenance, quality, team builder)                         |
|  • 27-entity PostgreSQL core; Streamlit 11-view application                                            |
|  • Authorised external research with verification + provenance                                        |
|                                                                                                       |
|  POST-MVP ENHANCEMENTS (long-term)                                                                     |
|  • CMIE depth: full delivery-speed/line-length analysis (HawkeyeStats)                                 |
|  • EAP regression models, VORP/WAR valuation, Monte Carlo campaign simulation                         |
|  • Playing XI constraint optimizer and Impact Player deployment engine                                 |
|  • Next.js production frontend reusing the same engine contracts                                       |
|                                                                                                       |
|  STRICTLY OUT-OF-SCOPE (EXCLUDED)                                                                     |
|  • Live auction bidding execution (decision support only)                                             |
|  • Sub-surface soil-moisture IoT sensors                                                               |
|  • Wearable biometric telemetry                                                                        |
|  • Recruitment probability outputs from unvalidated models                                             |
|  • Any claim of mental-state, fabricated injury history, or invented player data                       |
+-------------------------------------------------------------------------------------------------------+
```

---

## 8. Acceptance Criteria

| ID | Acceptance Criterion | Verification |
|---|---|---|
| AC-01 | PIRE resolves all known CricSheet hex-hash players with confidence 1.000 | Automated resolution tests against a known-player fixture set |
| AC-02 | PIRE never auto-merges two distinct players with similar names | Adversarial name-collision suite (e.g., R Sharma vs Rahul Sharma) — zero auto-merges |
| AC-03 | TMVE assigns exactly one membership class per player; UNVERIFIED is returned (never NEVER_REPRESENTED_RR) when evidence is insufficient | Review of UNVERIFIED-fixture outcomes |
| AC-04 | RR 2016–2017 appears as a suspension period, not as seasons with squad data | Schema assertion: `seasons.is_suspension` for 2016, 2017; zero squad rows for those years without explicit suspension flag |
| AC-05 | IPL 2027 season data exists only as `future_target` and is excluded from verified-membership logic | Query audit on 2027-season rows |
| AC-06 | Squad-inclusion-only players are not counted as RR match appearances | Verified-appearance count = 0 while `Squad Inclusion` membership row exists |
| AC-07 | CDCRE reports one of the four coverage states per competition; absence in dataset reported as `DATASET_UNAVAILABLE` or `NOT_ESTABLISHED`, never as non-participation | Coverage-state audit on a sample of players |
| AC-08 | Every CPPAE statistic has a documented definition and format tag | Static documentation check per `derived_features.feature_name` |
| AC-09 | Missing values are `NULL`, never 0.0 | Schema lint: zero zero-imputed physical measurements |
| AC-10 | Weather data is displayed only as macro-context, explicitly not as pitch measurement | UI copy + `data_provenance_flag` audit |
| AC-11 | SICE outputs are labelled "analytical recommendation" and no recruitment probability appears unless a validated model is registered | Output-contract assertion |
| AC-12 | Every external claim in a report carries a provenance record (URL, provider, timestamp, licence, status, confidence, record ID) | Provenance completeness check on a generated report |
| AC-13 | Streamlit renders all 11 views with no UI-side analytics code (engines untouched by Streamlit imports) | Architecture test: engine modules importable without Streamlit installed |
| AC-14 | Team Builder supports create, add/remove players, role assignment, and save/load team configurations | End-to-end team CRUD test |

---

## 9. Non-Functional Requirements

- **NFR-01 Determinism**: deterministic queries produce identical outputs for identical data;
  seeded randomness only where documented.
- **NFR-02 Zero fabrication**: no invented players, statistics, memberships, injuries, or mental-state claims.
- **NFR-03 Evidence lineage**: every membership/eligibility/career claim traces to `verification_records` and `data_sources`.
- **NFR-04 Format awareness**: no IPL/T20/List A/first-class mixing without explicit format tags and normalisation.
- **NFR-05 Licensing & confidentiality**: ODC-By (CricSheet) and CC BY 4.0 (Open-Meteo) attribution in exports; the proprietary hackathon dataset is kept confidential and isolated from public outputs.
- **NFR-06 Frontend independence**: engines have zero UI-framework dependencies.

---

## 10. Conclusion & Greenfield Baseline Declaration

This PRD establishes the operational specification for the **RR Squad Intelligence & Team
Composition Platform**. All features represent the **planned target state**
(`[STATUS: PLANNED - GREENFIELD BASELINE]`). No application code has been pre-implemented.
Subsequent engineering phases (Phases 0–10, see `docs/PHASES.md`) must validate deliverables
against these requirements, scope boundaries, and acceptance criteria.
