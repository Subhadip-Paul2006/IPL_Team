# Product Requirements Document (PRD)

**Project Title**: RR Squad Intelligence & Team Composition Platform
**Target Franchise**: Rajasthan Royals (RR)
**Hackathon**: IPL 2027 Rajasthan Royals scouting hackathon
**Primary Interface (initial)**: Streamlit · **Future Frontend**: Next.js (engines are frontend-agnostic)
**Document Version**: 2.2.0
**Status**: `[STATUS: PLANNED - GREENFIELD BASELINE]`
**Date**: November 2026
**Primary Authors**: Principal Software Architect, Sports Data Engineer, Cricket Analytics Researcher, Technical Documentation Engineer

> **Revision Note (v2.2.0, PVRE Dual-Mode Research Architecture)**: Introduces Engine 07 — Player
> Verification & Research Engine (PVRE) orchestrated by MIE. Defines the Mother Controller,
> deterministic request routing, Mode A (Existing RR Player Replacement Intelligence: Module A1
> RR History, Module A2 Recent Global Performance 2–3 yr configurable window, Module A3
> Replaceability Evidence Assessment with 5 analytical signal states), Mode B (Verified
> Uncapped Candidate Intelligence: complete domestic career discovery across Ranji, SMAT, VHT,
> Duleep, and age-groups), mandatory `REVIEW_REQUIRED` safety pathway, and SICE role-aware
> incumbent-vs-candidate replacement comparison. Reconciles database entity count to 33 entities
> everywhere. Adds AC-24 through AC-30 and Phase 4B. Preserves strict separation between the
> hackathon Top-10 deliverable and incumbent replacement evaluation.
>
> **Revision Note (v2.1.1, targeted remediation, retained for history)**: Use Case 3's ranking methodology is now
> the versioned, reproducible [`RANKING_SPEC.md`](RANKING_SPEC.md) configuration `RK-1.0.0`
> (deterministic gate + three-level ordering + documented total-order tiebreakers, one
> `ranking_runs` row per (config, data snapshot) — AC-18); AC-06 participation rows are
> evidence-bound (local corroboration is not verification); AC-22/AC-23 test mappings
> corrected. Full register: `reports/DOCUMENTATION_REMEDIATION_AUDIT.md` §v2.1.1.
>
> **Revision Note (v2.1.0, remediation, retained for history)**: This revision corrected the v2.0.0 workflow (CDCRE
> now has two capabilities — pre-identity candidate discovery and post-identity career
> retrieval — removing the PIRE↔CDCRE circular dependency), replaces the conflated six-class
> membership taxonomy with **three independent dimensions** (RR relationship · current status ·
> season-bound, policy-versioned eligibility), adds the **franchise-level RR 2016–17
> suspension** model (`team_season_participation`), specifies the **hackathon final
> deliverable** (Top 10 youngest eligible uncapped candidates, §4.3), and attaches a
> traceability mapping (contract · architecture · phase · agent · acceptance criterion) to
> every functional requirement.

---

## 1. Executive Summary & Problem Statement

### 1.1 Context
The platform serves the **IPL 2027 Rajasthan Royals scouting hackathon** and long-term RR
squad-building needs. Decision-makers need an evidence-backed way to:

- Identify any cricket player reliably by name, including players unknown to the internal
  data lake (domestic uncapped prospects, overseas players, players from other franchises).
- Verify RR representation across **three independent dimensions** (relationship history,
  currency, season-bound eligibility), with the RR 2016–2017 franchise suspension represented
  separately and IPL 2027 treated as a future, unverified target season.
- Retrieve and analyse a complete career across competitions, with explicit coverage states.
- Build team compositions from verified, profiled players and receive a squad-intelligence
  evaluation.

**Historical context**: RR membership analysis begins IPL 2008 (first phase 2008–2015). RR
were suspended for IPL 2016 and 2017 (franchise-specific; the IPL competition continued for
all other teams). RR returned in 2018; the post-return window is 2018–2026; **IPL 2027 is a
future target season** and stays unverified until authoritative squad evidence exists.

> **First principle**: *The platform never automatically assumes an unknown player is an
> uncapped player.* Unknown = unverified/NOT_ASSESSED until independently established.

### 1.2 Product Vision
The **RR Squad Intelligence & Team Composition Platform** is a modular analytical system
delivered initially as a **Streamlit application** (frontend-agnostic engine contracts),
with the **Mother Intelligence Engine (MIE)** orchestrating **seven specialised engines**
(PIRE, TMVE, CDCRE, CPPAE, CMIE, SICE, PVRE) and **five support services** over a
**33-entity PostgreSQL core**.

Supported populations: existing RR players · former RR players · players who never
represented RR · domestic uncapped prospects · players from other IPL franchises ·
international players · players whose identity or eligibility is unverified.

### 1.3 The Failure of Naive Team Building
- Classifying a former RR player as a current squad member (currency conflated with history).
- Treating squad-list appearance as a match appearance.
- Treating absence from one dataset as proof of non-participation.
- Auto-labelling unrecognised names "uncapped".
- Mixing T20 / List A / first-class figures without format awareness.
- Inferring mental state, fabricating injury histories, or scoring tiny samples as if large.

---

## 2. Target Users & Stakeholder Personas

```
+-------------------------------------------------------------------------------------------------------+
|                                    RAJASTHAN ROYALS DECISION HIERARCHY                                |
+-------------------------------------------------------------------------------------------------------+
|  Franchise Chief Executive (CEO) & Ownership                                                          |
|  - Squad risk, ROI, compliance sign-off                                                                |
+-------------------------------------------------------------------------------------------------------+
                                  |
                                  v
+----------------------------------------------------+--------------------------------------------------+
| Head of Cricket Operations                         | Squad Strategist & Composition Lead              |
| - Squad balance, depth, role caps                  | - Team building, candidate evaluation           |
+----------------------------------------------------+--------------------------------------------------+
                                  |
                                  v
+----------------------------------------------------+--------------------------------------------------+
| Lead Cricket Data Analyst                          | Batting & Bowling Coaching Staff                |
| - Evidence review, provenance audits               | - Role fit, matchup plans, pitch plans          |
+----------------------------------------------------+--------------------------------------------------+
```

- **Persona 1 — Lead Cricket Data Analyst**: verifies identity/membership/career claims
  end-to-end; inspects evidence tiers and provenance; questions: *"Which seasons did this
  player actually appear for RR, and what is the evidence tier?"*
- **Persona 2 — Head of Cricket Operations**: squad balance and depth; eligibility
  compliance; questions: *"Which of my players have verified current membership and which
  are historical or unverified? Which roles do we lack?"*
- **Persona 3 — Squad Strategist & Composition Lead**: builds the target composition and the
  hackathon candidate board; questions: *"If I swap Player A for candidate B in this role,
  how do strengths/weaknesses change?"*
- **Persona 4 — Coaching Staff**: role-specific performance evidence in actionable form;
  questions: *"How does he perform at the death, in what conditions, against whom?"*
- **Persona 5 — Franchise CEO & Ownership**: governance, evidence integrity, licensing;
  questions: *"What is verified vs estimated in this report?"*

---

## 3. Product Objectives & Hackathon Alignment

### 3.1 Strategic Product Objectives
1. **Evidence-backed intelligence**: every claim traceable to a tiered, provenance-recorded source.
2. **Squad composition capability**: build, edit, and evaluate teams with role-aware SICE analysis.
3. **Correct membership/eligibility semantics**: three independent dimensions; RR suspension as
   franchise participation state; 2027 future-target handling; unknowns surfaced, never
   silently classified.
4. **Talent pipeline continuity**: uncapped prospects discovered via verified career research
   (CDCRE), never assumed from absence.
5. **Hackathon deliverable** (§4.3): a transparent, reproducible, role-aware ranking of the
   **Top 10 youngest eligible uncapped players RR should consider backing for IPL 2027**,
   with full evidence dossiers.

### 3.2 Hackathon Evaluation Alignment
| Priority | Criterion | Platform capability |
|---|---|---|
| **High** | Analytical & domain rigor | Three-dimension membership; four-state career coverage; DATA_DICTIONARY-governed metrics; format-aware stats; zero fabrication |
| **High** | Architecture & engineering | MIE + 7 engines + 5 services; 33-entity 3NF core; deterministic queries; provenance records |
| **High** | Usability | 11-view Streamlit application; team builder; squad report; verification report |
| **Medium** | Innovation | Pre-identity candidate discovery; versioned eligibility policies; negative-membership verification protocol |
| **Lower** | Simulation extras | EAP regression, VORP/WAR, Monte Carlo, Playing XI/Impact Player optimizers — **post-MVP, not required for submission** |

---

## 4. User Workflow (Primary — revised)

```
User opens Streamlit
        │
Creates a team
        │
Enters player name
        │
Mother Intelligence Engine (MIE)
        │
CDCRE capability 1: pre-identity candidate discovery (raw name → corroborating candidates)
        │
Player Identity Resolution (PIRE: deterministic tiers + contextual attribute corroboration)
        │
Is identity resolved?
   /             \
  No              Yes
  │                │
User clarification  Three-dimension membership verification (TMVE: Dimensions 1 & 2)
 (review & retry)   │
                    Eligibility Policy Service (Dimension 3: season-bound eligibility)
                    │
                    PVRE Mother Controller (Engine 07: Classification & Research Routing)
                   /                    │                         \                      \
  Verified RR Incumbent     Verified Uncapped Non-RR    Conflicting/Insufficient   Verified Non-RR Capped
        │                               │                     Evidence                     │
  [Mode A Workflow]             [Mode B Workflow]                 │                  [Out of Scope]
  Module A1: RR History         Full Domestic Career         [REVIEW_REQUIRED]             │
  Module A2: Global Form        Ranji, SMAT, VHT, Duleep          │                  Explicit Notice:
  Module A3: Assessment         Independent Verification     Structured Dossier      Non-RR Capped Player
        │                               │                     Reason Codes &         Outside Workflows
  Signals: RETAIN / MONITOR /   Verified Uncapped Pool        Manual Checks
  POTENTIALLY_REPLACEABLE               │
        │                               │
        +───────────────┬───────────────+
                        │
       Performance analytics (CPPAE, per DATA_DICTIONARY)
                        │
       Contextual match analysis (CMIE, 5 provenance tiers)
                        │
       User adds player to team (Service E)
                        │
       Squad Intelligence Engine (SICE)
         ├── Incumbent-vs-Candidate Replacement Comparison (Mode A evidence)
         ├── Squad Gap & Balance Evaluation
         └── Top 10 Youngest Uncapped Ranking (Separate Deliverable: RK-1.0.0)
                        │
       Squad report and recommendations
```

**Branching rules**:
- Ambiguous identity → **user clarification / human review**; PIRE never auto-merges similar
  names.
- Membership evidence insufficient → the affected dimension returns `UNKNOWN` /
  `ELIGIBILITY_UNVERIFIED` / `NOT_ASSESSED`; **failed searches are never converted into
  proof of non-membership or ineligibility**.
- Conflicting identity, membership, or eligibility evidence → triggers the mandatory
  `REVIEW_REQUIRED` safety pathway; never silently routes or promotes unverified players.
- Verified non-RR capped player → returns an explicit `OUT_OF_SCOPE` notice; never routes to
  Mode B.

### 4.1 Use Case 1: Verified Team Building (MVP core)
Create team → search name → PIRE (with CDCRE candidates) → confirm on Identity Verification
view if ambiguous → review three-dimension membership (incl. verified RR seasons,
2016–17 suspension gap, other IPL teams) → review Career + Performance views → add to team
(with role) → SICE evaluates; user adjusts per the Squad Intelligence Report.

### 4.2 Use Case 2: Uncapped Prospect Discovery (MVP supported population)
Search prospect name → CDCRE candidate discovery + authorised research (SMAT is
`DATASET_UNAVAILABLE` locally → research path, provenance-tracked) → PIRE corroborates →
TMVE: typically `RR_RELATIONSHIP_UNKNOWN` or (negative-verification requirements met)
`NO_VERIFIED_RR_RELATIONSHIP`; eligibility `NOT_ASSESSED` until a `VERIFIED_ELIGIBLE`
assessment under the active policy version → CPPAE presents evidence-backed performance
with format tags and sample sizes → add to team; SICE notes role fit vs incumbents.

### 4.3 Use Case 3: Hackathon Final Deliverable — Top 10 Youngest Eligible Uncapped Candidates
The platform must support (SICE + CPPAE + TMVE + eligibility service):

1. **Candidate eligibility verification**: `VERIFIED_ELIGIBLE` under the active
   `eligibility_policies` version for the target season, with rule-source and verification
   record (uncapped status independently verified, **not** assumed from absence).
2. **Exact age calculation** as of the official evaluation date (date recorded in the
   policy version; per-candidate DOB evidence recorded).
3. **Primary and secondary playing roles** with documented role criteria
   (DATA_DICTIONARY role thresholds, format-tagged observed data only).
4. **Domestic competition evidence** (Ranji/SMAT/Vijay Hazare/Duleep as available; SMAT
   via research where `DATASET_UNAVAILABLE` locally, provenance-tracked).
5. **T20 performance analysis** per DATA_DICTIONARY (strike/economy/samples, phase splits).
6. **Role-adjusted comparison**: rankings within role groups; cross-role presentation uses
   role-adjusted baselines, never raw cross-role numbers.
7. **Historical consistency**: multi-season variance where ≥2 seasons of evidence exist.
8. **Relevant contextual evidence** (CMIE tiers; venue/opposition notes where material).
9. **Squad fit**: SICE gap/role-match analysis against the current RR composition.
10. **Risk and data-coverage limitations** per candidate (coverage class, verification
    status, evidence tier).
11. **Ranking methodology** (transparent, role-aware, measurable, reproducible) —
    **fully specified in [`docs/RANKING_SPEC.md`](RANKING_SPEC.md), configuration
    `RK-1.0.0`** (v2.1.1: replaces the retired equal-weight percentile + shrinkage model):
    - **Candidate universe**: resolved identity + `VERIFIED_ELIGIBLE` under the active
      `eligibility_policies` version for the target season + age band (min 18 / max 26 at the
      recorded `evaluation_date`) + minimum verified-sample rule (unknown players are
      **never** assumed uncapped; `NOT_ASSESSED` is excluded, not promoted).
    - **Within-role relevance gate** (`gate_thresholds`): per role group, verified
      career strike rate (or bowling strike rate) at/above the role baseline percentile
      with a minimum observed-ball sample, so tiny samples cannot out-rank deep samples.
    - **Deterministic three-level ordering** (pure SQL, no LLM, no subjective weights):
      age (youngest first, computed at the recorded evaluation date) → consistency
      (innings batted ÷ appearances) → career average B05 (format-tagged; `NULL`/not-out-only
      averages sort after computed ones at equal keys).
    - **Documented total-order tiebreakers**: strike rate → balls faced → `player_id`
      string form; `seed = 0` (deterministic SQL ordering).
    - **Output**: **Top 10 + reserve list**, each entry with a full evidence dossier
      (sources, tiers, dates, sample sizes; confidence only when calibrated); the board is
      stored in a **`ranking_runs`** row keyed `(ranking_configurations, data_snapshot)` so
      the same inputs always reproduce exactly one board.
12. **No hardcoded arbitrary weights / no inline ranking constants**: the complete method
    is the versioned `ranking_configurations` record + `RANKING_SPEC.md`; every execution is
    a durable `ranking_runs` row (reproducible and auditable).

> **Strict Architectural Separation**: Use Case 3's Top-10 ranking methodology (governed by
> [`docs/RANKING_SPEC.md`](RANKING_SPEC.md) `RK-1.0.0`) is a standalone hackathon competition
> deliverable. It operates exclusively over the pool of verified-eligible uncapped candidates.
> It must NEVER be conflated, combined, or merged with Mode A incumbent replacement evaluation
> (Use Case 5), which evaluates incumbent RR players against eligible uncapped prospects for
> potential squad replacement.

### 4.4 Use Case 4: Squad Gap Analysis (MVP core)
SICE analyses the assembled team (depth, balance, duplication, gaps, comparisons,
alternatives); outputs labelled `ANALYTICAL_RECOMMENDATION`; no probabilities unless a
calibrated, validated model exists.

### 4.5 Use Case 5: Mode A — Existing Rajasthan Royals Player Replacement Intelligence (MVP core)
When the input player has a verified current or historical Rajasthan Royals relationship
(`CURRENT_RR`, `HISTORICAL_RR_APPEARED`, `HISTORICAL_RR_SQUAD_ONLY`), PVRE executes Mode A.
Rather than performing a simple Rajasthan Royals archive lookup, it conducts an intensive
dual-scope research investigation:
1. **Module A1 — RR Historical Performance Research**:
   - Retrieves and analyses the player's complete RR history across all evidenced seasons
     (2008–2015, 2018–2026).
   - **Strictly distinguishes squad membership from actual Playing XI match appearances**:
     squad-only seasons are flagged `appearances = 0` and never credit batting/bowling stats.
   - Evaluates season-wise batting, bowling, fielding, and wicketkeeping contributions.
   - Tracks batting order distribution, bowling phase usage, consistency, and role changes
     across seasons.
2. **Module A2 — Recent Global Performance Research**:
   - Investigates recent cricket performance outside Rajasthan Royals over a configurable
     **2-to-3 year window** relative to a recorded evaluation date (default: 3 years).
   - Investigates recognised competitions: IPL appearances for other franchises, Big Bash
     League (BBL), Pakistan Super League (PSL), Caribbean Premier League (CPL), SA20, The
     Hundred (HND), International cricket (Tests, ODIs, T20Is), and Indian domestic
     competitions (Ranji Trophy, Syed Mushtaq Ali Trophy, Vijay Hazare Trophy).
   - Compiles competition, season, team, matches, innings, performance metrics, roles,
     participation gaps, and verified injury/availability records.
   - Formats statistics with format tags; never mixes cross-format numbers; never interprets
     dataset absence as evidence of non-participation.
3. **Module A3 — Replaceability Evidence Assessment**:
   - Synthesises RR historical contribution, 2–3 year global form, age trajectory at the
     recorded evaluation date, role importance, sample completeness, and availability.
   - Generates structured analytical signals:
     * `RETAIN_SIGNAL`: strong recent performance, high role contribution, stable trajectory.
     * `MONITOR_SIGNAL`: fluctuating form, sample gaps, or role evolution requiring tracking.
     * `POTENTIALLY_REPLACEABLE`: declining multi-season metrics, diminished availability, or
       advanced age relative to role demands.
     * `INSUFFICIENT_EVIDENCE`: sample size below minimum threshold or significant data gaps.
     * `REVIEW_REQUIRED`: conflicting performance or availability records across sources.
   - **Analytical Signals Only**: PVRE never makes standalone release, replace, or retention
     decisions and never invents arbitrary thresholds; it forwards the complete evidence-backed
     dossier to SICE for role-aware comparison against verified uncapped prospects.

### 4.6 Use Case 6: Mode B — Verified Uncapped Candidate Intelligence (MVP core)
When the input player is not a verified RR player (`NO_VERIFIED_RR_RELATIONSHIP`) and is
independently verified as uncapped-eligible under the target season policy (`VERIFIED_ELIGIBLE`),
PVRE executes Mode B. It conducts a comprehensive domestic and franchise career discovery:
1. Full career discovery across Ranji Trophy, Syed Mushtaq Ali Trophy (SMAT), Vijay Hazare
   Trophy (VHT), Duleep Trophy, age-group competitions (U19/U23), other franchise leagues, and
   international appearances (if any; verified international appearances immediately trigger
   capped classification).
2. Complete match-level and season-by-season records across batting, bowling, fielding, and
   wicketkeeping.
3. Career development trajectory, role flexibility, and consistency over recent seasons.
4. Enforces independent policy verification under target-season rules (`eligibility_policies`).
5. **Strict negative inference rule**: Absence from the internal database is **NEVER** proof
   of uncapped status. Candidates enter the verified uncapped pool only when identity, domestic
   records, and policy rules independently confirm eligibility.

### 4.7 Use Case 7: Mandatory `REVIEW_REQUIRED` Safety Pathway (Safety Gate)
A hard safety requirement triggered whenever:
1. Multiple plausible player identities exist (PIRE disambiguation unresolved).
2. Date of birth or other identity attributes conflict materially across sources.
3. RR relationship evidence is contradictory or incomplete.
4. Target season eligibility cannot be verified under the active policy.
5. Source records materially disagree on statistics, matches, or team affiliations.
6. External research fails to establish sufficient corroboration.
7. Data coverage is too incomplete to support replacement or uncapped classification.
8. A source is restricted or unavailable with no acceptable alternative evidence.

In this state, PVRE emits a structured review dossier containing:
- `review_status = 'REVIEW_REQUIRED'`
- `review_reason_codes` (e.g. `['IDENTITY_AMBIGUITY', 'DOB_CONFLICT', 'INSUFFICIENT_GLOBAL_SAMPLE']`)
- `unresolved_claims` (list of specific disputed claims)
- `conflicting_source_ids` (references to conflicting `source_records`)
- `missing_evidence` (explicit missing data items)
- `recommended_manual_checks` (actionable guidance for human analysts)

The system never silently forces a routing decision and never admits unverified players into the
uncapped candidate ranking pool.

---

## 5. Functional Requirements (with traceability)

Every FR maps to: **(1) technical contract · (2) architecture component · (3) implementation
phase · (4) responsible agent · (5) acceptance criterion (AC)**. Contracts in `docs/TRD.md`;
diagrams in `docs/ARCHITECTURE.md`; phases in `docs/PHASES.md`; agents in `docs/AGENTS.md`.

### 5.1 Player Identity Resolution (PIRE)
| FR | Requirement | TRD contract | Architecture | Phase | Agent | AC |
|---|---|---|---|---|---|---|
| **FR-P1** | Resolve exact/alias/varied/misspelt names to canonical IDs | §3 `PIRE.resolve` | D2/D3 | Phase 2 | `agent_pire` | AC-01, AC-02 |
| **FR-P2** | Duplicate detection & disambiguation with **contextual attribute corroboration** (DOB, hand, role, era — not biometric) | §3.3 | D3 | Phase 2 | `agent_pire` | AC-02 |
| **FR-P3** | Output tier, status (RESOLVED/PROVISIONAL/UNRESOLVED), aliases, matching records, warnings | §3.2 | D2/D3 | Phase 2 | `agent_pire` | AC-01 |
| **FR-P4** | Low-confidence / multi-candidate → user clarification | §3.3 + §2.3 | D2 | Phase 7 | `agent_mie_orchestration` | AC-03 |
| **FR-P5** | Never merge two players merely because names are similar | §3.3 | D3 | Phase 2 | `agent_pire` | AC-02 |
| **FR-P6** | Numeric confidence exposed only after calibration (`calibrated=TRUE`), else NULL | §3.3 | — | Phase 10 | `agent_testing_qa` | AC-15 |

### 5.2 Team Membership Verification (TMVE)
| FR | Requirement | TRD contract | Architecture | Phase | Agent | AC |
|---|---|---|---|---|---|---|
| **FR-M1** | Three independent dimensions (relationship · currency · eligibility) never conflated | §4.3, D5 | D4 | Phase 3 | `agent_tmve` | AC-04 |
| **FR-M2** | Verified appearances distinct from squad inclusion | §4.1, `player_team_history.appearances` | D4 | Phase 3 | `agent_tmve` | AC-05 |
| **FR-M3** | RR season segmentation via `team_season_participation` (2008–15 · 2016–17 SUSPENDED · 2018+ · 2027 UNKNOWN) | D4/ADR-004 | D4/D7 | Phase 3 | `agent_tmve` | AC-06 |
| **FR-M4** | Other IPL teams + documented retention/auction/transfer/release | §4.1 | D4 | Phase 3 | `agent_tmve` | AC-05 |
| **FR-M5** | Current membership verified separately from history | §4.3 | D4 | Phase 3 | `agent_tmve` | AC-04 |
| **FR-M6** | Verification hierarchy (5 tiers) + authorised research when internal records insufficient | §4.2 | D5 | Phase 4 | `agent_provenance` | AC-07 |
| **FR-M7** | Negative membership only via TRD §4.5 requirements (coverage, seasons, squad+scorecard, source quality, conflict handling, human review); else UNKNOWN | §4.5 | D4 | Phase 3/4 | `agent_tmve` | AC-08 |
| **FR-M8** | Eligibility: season-bound, policy-versioned, source-traceable, effective-date aware, independently verified; default `NOT_ASSESSED` | §4.6, D5 | D4 | Phase 3 | `agent_tmve` | AC-09 |

### 5.3 Career Discovery & Competition Research (CDCRE)
| FR | Requirement | TRD contract | Architecture | Phase | Agent | AC |
|---|---|---|---|---|---|---|
| **FR-C1** | **Two capabilities**: `discover_candidates(raw_name)` (pre-identity, no player_id required) and `discover_career(player_id)` (post-identity) | §5.1 | D2 | Phase 4 | `agent_cdcre` | AC-10 |
| **FR-C2** | Cross-competition discovery (IPL franchises, domestic state, Ranji, SMAT, Vijay Hazare, Duleep, India A/age-group, international, other T20 leagues) | §5.2 | D2 | Phase 4 | `agent_cdcre` | AC-11 |
| **FR-C3** | Season participation, team history, career gaps | §5.3 | D2 | Phase 4 | `agent_cdcre` | AC-11 |
| **FR-C4** | Four coverage states (verified / dataset-unavailable / not-established / confirmed-non-participation); dataset absence never read as non-participation | §5.4 | D2 | Phase 4 | `agent_cdcre` | AC-11 |
| **FR-C5** | Provenance for every external claim (Service C) | §5.5 | D5/D10 | Phase 4 | `agent_provenance` | AC-07 |

### 5.4 Complete Player Performance Analytics (CPPAE)
| FR | Requirement | TRD contract | Architecture | Phase | Agent | AC |
|---|---|---|---|---|---|---|
| **FR-A1** | Batting profile (all DATA_DICTIONARY B-series metrics incl. position/phase/matchup/partnership) | §6, `DATA_DICTIONARY.md` | D6 | Phase 5 | `agent_cppae` | AC-12 |
| **FR-A2** | Bowling profile (integer legal balls of record; over notation derived; speed/line-length where available) | §6 | D6 | Phase 5 | `agent_cppae` | AC-12 |
| **FR-A3** | Fielding profile (recorded-only drops/saves; coverage class always reported) | §6 | D6 | Phase 5 | `agent_cppae` | AC-12 |
| **FR-A4** | Wicketkeeping profile | §6 | D6 | Phase 5 | `agent_cppae` | AC-12 |
| **FR-A5** | Match contribution (POTM as input signal only; measurable leverage, never mental state) | §6 | D6 | Phase 5 | `agent_cppae` | AC-12 |
| **FR-A6** | Every metric has a documented definition, formula, null rules, min sample, and observed/derived/model class in `DATA_DICTIONARY.md` | `DATA_DICTIONARY.md` | D6 | Phase 5 | `agent_cppae` | AC-13 |
| **FR-A7** | No unverified statistics from incomplete data; missing ≠ zero; sample sizes always visible | §6.2 | D6 | Phase 5 | `agent_cppae` | AC-12 |
| **FR-A8** | No cross-format comparison without format tags; false-shot frequency never computed | §6.2, dictionary §6 | D6 | Phase 5 | `agent_cppae` | AC-12 |

### 5.5 Contextual Match Intelligence (CMIE)
| FR | Requirement | TRD contract | Architecture | Phase | Agent | AC |
|---|---|---|---|---|---|---|
| **FR-X1** | Condition annotations with 5-tier provenance (measured/reported/estimated/inferred/unknown) | §7.3 | D2/D6 | Phase 6 | `agent_cmie` | AC-14 |
| **FR-X2** | Weather recorded as environmental context (timezone + match method fields), never pitch measurement; pitch ratings only with a validated methodology version | §7.1, D10 | D2 | Phase 6 | `agent_cmie` | AC-14 |
| **FR-X3** | No mental-state inference; injury data verified-only; recurrence scores model-inferred + NULL-unvalidated | §7.3 | D2 | Phase 6 | `agent_cmie` | AC-14 |

### 5.6 Squad Intelligence & Composition (SICE)
| FR | Requirement | TRD contract | Architecture | Phase | Agent | AC |
|---|---|---|---|---|---|---|
| **FR-S1** | Role distribution, depth, balance, duplication, gaps, flexibility | §8.1 | D8 | Phase 8 | `agent_sice` | AC-16 |
| **FR-S2** | Comparisons, replacements, combinations | §8.1 | D8 | Phase 8 | `agent_sice` | AC-16 |
| **FR-S3** | Recommendations labelled analytical, evidence-referenced | §8.3 | D8 | Phase 8 | `agent_sice` | AC-17 |
| **FR-S4** | No recruitment probabilities without a validated/calibrated model | §8.3 | D8 | Phase 8/10 | `agent_sice` | AC-17 |
| **FR-S5** | Hackathon ranking: transparent role-aware reproducible methodology, versioned weights, shrinkage, Top 10 + reserves + dossiers (PRD §4.3) | §8 + `derived_features` | D8 | Phase 10 | `agent_sice` | AC-18 |

| **FR-S6** | Role-Aware Incumbent-vs-Candidate Replacement Comparison: compares RR incumbent and eligible uncapped candidates across 16 dimensions; outputs versioned recommendations (`ANALYTICAL_RETAIN`, `ANALYTICAL_MONITOR`, `ANALYTICAL_REPLACEMENT_CANDIDATE`, `NO_SUITABLE_VERIFIED_REPLACEMENT`, `INSUFFICIENT_EVIDENCE`); keeps Top-10 ranking separate | TRD §8.4 | ARCH D8 | Phase 8 | `agent_sice` | AC-30 |

### 5.7 Support Services
| FR | Requirement | TRD contract | Architecture | Phase | Agent | AC |
|---|---|---|---|---|---|---|
| **FR-VA1** | Ingestion with provenance + quarantine (per DATA_SOURCE_REGISTER statuses; SMAT gap recorded) | §9.1, register | D5 | Phase 1 | `agent_data_ingestion` | AC-19 |
| **FR-VB1** | JSON/CSV exports with attribution; confidentiality of proprietary data | §9.2 | D1 | Phase 7 | `agent_profile_generator` | AC-20 |
| **FR-VC1** | Provenance records (URL, provider, timestamp, licence, status, tier, confidence-if-calibrated, record ID) | §9.3 | D10 | Phase 4 | `agent_provenance` | AC-07 |
| **FR-VD1** | Quality/coverage checks incl. innings↔delivery reconciliation | §9.4 | D5 | Phase 1 (all) | `agent_data_quality` | AC-19 |
| **FR-VE1** | Team lifecycle + roles + saved configurations | §9.5 | D1/D8 | Phase 8 | `agent_team_builder` | AC-21 |

### 5.8 Streamlit Application
| FR | Requirement | TRD contract | Architecture | Phase | Agent | AC |
|---|---|---|---|---|---|---|
| **FR-U1** | 11 required views (§6) | §12.1 | D9 | Phase 9 | `agent_streamlit_app` | AC-22 |
| **FR-U2** | Session state for ephemeral UI only; no analytics in Streamlit | §12.2 | D9 | Phase 9 | `agent_streamlit_app` | AC-22 |
| **FR-U3** | Engines importable without Streamlit (Next.js-ready) | §1.2 | D9 | Phase 9 | `agent_streamlit_app` | AC-23 |

---

### 5.9 Player Verification & Research Engine (PVRE — Engine 07)
| FR | Requirement | TRD contract | Architecture | Phase | Agent | AC |
|---|---|---|---|---|---|---|
| **FR-PV1** | Mother Controller: Orchestrates PIRE, TMVE, CDCRE, and Eligibility Policy Service; classifies requests and executes deterministic workflow routing | TRD §9.1 | ARCH D2b | Phase 4B | `agent_pvre` | AC-24 |
| **FR-PV2** | Mode A: Module A1 — RR Historical Performance Research (complete RR history, strict separation of squad inclusion vs playing XI appearances, role evolution across evidenced seasons) | TRD §9.3 | ARCH D2c | Phase 4B | `agent_pvre` | AC-25 |
| **FR-PV3** | Mode A: Module A2 — Recent Global Performance Research (configurable 2–3 year window relative to evaluation date; covers BBL, PSL, CPL, SA20, The Hundred, Intl, domestic; no cross-format contamination) | TRD §9.3 | ARCH D2c | Phase 4B | `agent_pvre` | AC-26 |
| **FR-PV4** | Mode A: Module A3 — Replaceability Evidence Assessment (signals: `RETAIN_SIGNAL`, `MONITOR_SIGNAL`, `POTENTIALLY_REPLACEABLE`, `INSUFFICIENT_EVIDENCE`, `REVIEW_REQUIRED`; forwards profile to SICE; no release decisions inside PVRE) | TRD §9.3 | ARCH D2c | Phase 4B | `agent_pvre` | AC-27 |
| **FR-PV5** | Mode B: Career Discovery & Domestic Coverage (full domestic career: Ranji, SMAT, VHT, Duleep, age-groups, leagues; database absence never treated as uncapped proof) | TRD §9.4 | ARCH D2d | Phase 4B | `agent_pvre` | AC-28 |
| **FR-PV6** | Mode B: Independent Eligibility Verification (verifies uncapped-eligible status under target season policy before admitting player to verified candidate pool) | TRD §9.4 | ARCH D2d | Phase 4B | `agent_pvre` | AC-28 |
| **FR-PV7** | Mandatory `REVIEW_REQUIRED` Safety Pathway (structured review dossier with reason codes, unresolved claims, conflicting sources, missing evidence, manual checks; blocks automated pool pollution) | TRD §9.5 | ARCH D2e | Phase 4B | `agent_pvre` | AC-29 |
| **FR-PV8** | Standardized PVRE Typed Output Contract (minimum 23 fields; explicit null/unavailable/verified/conflict semantics; complete source provenance) | TRD §9.6 | ARCH D2b | Phase 4B | `agent_pvre` | AC-24, AC-29 |

## 6. Streamlit Views (UI Requirements)

1. **Home / Team Builder** — create/rename/delete teams; add/remove players; assign roles;
   save configurations.
2. **Player Search** — name entry; PIRE candidates ranked by tier; ambiguity prompts.
3. **Player Identity Verification** — candidate evidence side-by-side; DOB/role corroboration;
   confirm-or-review flow.
4. **Historical RR Membership & Mode A Profile** — three-dimension badges; RR seasons (2008–15 /
   2016–17 suspension / 2018+ / 2027 unverified); squad inclusion vs match appearances; recent
   2–3 yr global performance across recognised leagues; replaceability evidence assessment
   signals (`RETAIN_SIGNAL`, `MONITOR_SIGNAL`, `POTENTIALLY_REPLACEABLE`, `INSUFFICIENT_EVIDENCE`,
   `REVIEW_REQUIRED`).
5. **Player Career Profile (Mode B Discovery)** — competition coverage table with four states,
   domestic tournament breakdowns (Ranji/SMAT/VHT/Duleep), gaps, provenance.
6. **Performance Analytics** — CPPAE profile with DATA_DICTIONARY definitions, format
   tags, and visible sample sizes.
7. **Contextual Analysis** — CMIE annotations with provenance-tier badges.
8. **Player Comparison & Replacement** — similar-role comparison; Mode A incumbent-vs-candidate
   replacement comparison across 16 role, performance, and squad dimensions with SICE analytical
   recommendations.
9. **Squad Composition** — role distribution, depth, membership classes of current members.
10. **Squad Intelligence Report** — strengths/weaknesses, dependencies, priorities,
    alternatives, labelled recommendations; Mode A incumbent replacement recommendations;
    separate hackathon Top-10 uncapped board.
11. **Data Source, Verification & Safety Review Report** — per-claim provenance, verification
    status, licences, evidence tier; `REVIEW_REQUIRED` structured audit dossier with reason codes,
    unresolved claims, conflicting source IDs, and recommended manual checks.

---

## 7. Scope Boundaries

```
+-------------------------------------------------------------------------------------------------------+
|                                        SYSTEM SCOPE PARTITION                                         |
+-------------------------------------------------------------------------------------------------------+
|  HACKATHON MINIMUM SUBMISSION                                                                           |
|  • Top-10 youngest eligible uncapped candidates + reserve list + per-candidate evidence dossiers       |
|  • Ranking methodology (transparent, role-aware, reproducible, versioned)                               |
|  • The supporting verification pipeline for those candidates (identity, membership, eligibility,       |
|    career coverage, performance)                                                                        |
|                                                                                                       |
|  MVP (PLATFORM CORE, PHASES 1-9)                                                                       |
|  • MIE + PIRE (FR-P*) · TMVE (FR-M*, 3 dimensions) · CDCRE dual capability (FR-C*) · CPPAE (FR-A*)   |
|  • CMIE (FR-X*) · SICE (FR-S1-S4) · PVRE (FR-PV1-8) · Services A-E (FR-V*) · 33-entity core · Streamlit 11 views        |
|  • DATA_SOURCE_REGISTER + DATA_DICTIONARY as governing specs                                          |
|                                                                                                       |
|  POST-MVP ENHANCEMENTS (LONG-TERM, NOT REQUIRED FOR SUBMISSION)                                        |
|  • EAP regression, VORP/WAR, Monte Carlo campaign simulation                                           |
|  • Playing XI constraint optimizer, Impact Player deployment engine                                    |
|  • HawkeyeStats delivery-speed/line-length depth; Next.js production frontend                          |
|                                                                                                       |
|  STRICTLY OUT-OF-SCOPE                                                                                  |
|  • Live auction execution · soil-moisture IoT · wearable biometrics · probabilities from unvalidated   |
|    models · mental-state claims · fabricated injuries · private medical data                          |
+-------------------------------------------------------------------------------------------------------+
```

---

## 8. Acceptance Criteria

| ID | Criterion | Verification |
|---|---|---|
| **AC-01** | PIRE resolves all CricSheet-registry players (tier 1) on the fixture set; `identity_status` semantics hold | Automated resolution tests |
| **AC-02** | PIRE never auto-merges distinct players with similar names | Adversarial collision suite (R Sharma / Rahul Sharma etc.) — zero auto-merges |
| **AC-03** | Ambiguous identities route to user clarification; MIE never guesses | Orchestration tests with multi-candidate fixtures |
| **AC-04** | Three membership dimensions stored/returned independently; no single conflated label | Schema + contract assertions on `player_membership_state` / `player_eligibility` |
| **AC-05** | Squad-inclusion-only players show `appearances = 0` and `HISTORICAL_RR_SQUAD_ONLY`; verified appearances count only match records | Appearance-vs-squad-list differential test |
| **AC-06** | `team_season_participation`: RR×IPL 2016 and 2017 rows = `SUSPENDED`; the IPL 2016/17 seasons exist with other teams `PARTICIPATING`; RR×IPL 2027 = `UNKNOWN` until evidence. **v2.1.1 (Priority E)**: no participation row may be `VERIFIED` without a cited `verification_records` evidence row (DDL `chk_tsp_verified_evidence`); roadmap/model statements and local tier-4 corroboration (CricSheet fixture presence/absence) do **not** constitute verification; rows seed `PENDING`/`UNVERIFIED` | Schema CHECKs + fixture assertions + `chk_tsp_verified_evidence` enforcement |
| **AC-07** | Every external claim carries a provenance record (URL, provider, timestamp, licence, tier, status, record ID) with a verification hierarchy level | Provenance completeness check |
| **AC-08** | `NO_VERIFIED_RR_RELATIONSHIP` only when TRD §4.5 requirements all satisfied + human review; else `RR_RELATIONSHIP_UNKNOWN` | Negative-verification audit fixture |
| **AC-09** | Eligibility rows always reference an `eligibility_policies` version; unknown players default `NOT_ASSESSED`, never auto-uncapped | Schema assertion (`policy_id` NOT NULL) + fixture |
| **AC-10** | `CDCRE.discover_candidates` returns candidates from a raw name with **no player_id argument**; `discover_career` requires a canonical ID | Contract test |
| **AC-11** | Career coverage uses the four states; dataset absence reported as `DATASET_UNAVAILABLE`/`NOT_ESTABLISHED`, never non-participation | Coverage-state audit |
| **AC-12** | Every CPPAE metric exists in `DATA_DICTIONARY.md` with all ten required attributes; sample sizes returned; missing → NULL; false-shot = NOT_COMPUTABLE | Dictionary completeness check + statistical tests |
| **AC-13** | No metric definition missing formula/denominator/null-rule in the dictionary | Static dictionary audit |
| **AC-14** | Five provenance tiers present per contextual datum; weather rows carry `venue_timezone` + match method; no pitch ratings without `ratings_methodology_version` | Schema + UI copy audit |
| **AC-15** | No numeric confidence exposed without `calibrated=TRUE` (NULL otherwise) | Contract assertion |
| **AC-16** | Team CRUD + role assignment + saved configurations work end-to-end | E2E test |
| **AC-17** | SICE outputs labelled `ANALYTICAL_RECOMMENDATION`; no unvalidated probabilities | Output-contract assertion |
| **AC-18** | Top-10 board reproducible: `run_ranking(config_version, data_snapshot)` returns exactly the board stored in the `ranking_runs` row for `(ranking_configurations, data_snapshot_sha256)`; the method is the versioned `RANKING_SPEC.md` config (`RK-1.0.0`), never an inline constant; dossiers complete (§4.3 items 1–12) | Reproducibility test (same config + snapshot → identical stored board; re-run is a no-op) + dossier completeness check |
| **AC-19** | Ingestion: per-dataset counts match DATA_SOURCE_REGISTER verified counts (1,243/201/265/230; SMAT gap recorded); DQ reconciliation gates pass | Ingestion completeness SQL |
| **AC-20** | Exports embed ODC-By attribution; no proprietary hackathon content in public exports | Export-contract + confidentiality audit |
| **AC-21** | Team Builder constraints: 11-view navigation + composition rules (informational caps, not enforced selection) | UI test |
| **AC-22** | All 11 Streamlit views render with no UI-side analytics | View-render test + static audit that no view performs analytics |
| **AC-23** | Engine modules importable with Streamlit uninstalled (Next.js-ready) | Static import test |
| **AC-24** | PVRE Deterministic Routing & Classification: Mother Controller orchestrates identity resolution (PIRE), RR relationship verification (TMVE), and eligibility assessment (Eligibility Policy Service); deterministically routes to Mode A on verified RR relationship, Mode B on verified uncapped non-RR, `REVIEW_REQUIRED` on ambiguous/conflicting evidence, or `OUT_OF_SCOPE` on non-RR capped; never infers uncapped status from database absence or non-membership without meeting TRD §4.5 negative verification rules | Automated classification fixture covering all 4 routing branches + negative proofs |
| **AC-25** | Mode A RR Historical Performance & Squad Separation: Module A1 analyses complete RR history across all evidenced seasons, strictly differentiating squad inclusion from playing XI appearances, calculating season-by-season batting, bowling, fielding/keeping, and role evolution | Contract test with squad-only vs Playing XI fixtures across RR seasons 2008–2025 |
| **AC-26** | Mode A Recent Global Performance Research: Module A2 retrieves performance across a configurable 2–3 year window relative to evaluation date for recognised global leagues (BBL, PSL, CPL, SA20, The Hundred, Intl, domestic); reports sample sizes, participation gaps, and format tags; never assumes non-participation from missing datasets | Multi-league fixture audit + date-window boundary assertions |
| **AC-27** | Mode A Replaceability Evidence Assessment: Module A3 synthesises RR history, recent global form, age trajectory at evaluation date, and sample completeness into structured analytical signals (`RETAIN_SIGNAL`, `MONITOR_SIGNAL`, `POTENTIALLY_REPLACEABLE`, `INSUFFICIENT_EVIDENCE`, `REVIEW_REQUIRED`); strictly forwards profile to SICE; never outputs arbitrary replacement probabilities or standalone release decisions | Signal generation unit tests + contract assertion |
| **AC-28** | Mode B Comprehensive Uncapped Discovery & Independent Verification: Investigates complete domestic career (Ranji, SMAT, VHT, Duleep, age-group, and league competitions); verifies uncapped eligibility under target season policy; rejects unverified players from entering the uncapped pool; preserves four-state coverage | Uncapped candidate fixture test + domestic competition coverage audit |
| **AC-29** | Mandatory `REVIEW_REQUIRED` Safety State: Hard safety pathway triggered on identity ambiguity, conflicting DOB/attributes, contradictory RR evidence, unverified eligibility, source discrepancies, or data coverage gaps; returns complete structured review dossier (`review_status`, `review_reason_codes`, `unresolved_claims`, `conflicting_source_ids`, `missing_evidence`, `recommended_manual_checks`); never silently falls back to Mode A/B | Adversarial conflict injection suite; verification that `REVIEW_REQUIRED` cannot enter candidate pool |
| **AC-30** | SICE Incumbent-vs-Candidate Replacement Comparison: SICE performs role-aware comparative evaluation between incumbent RR player and verified uncapped candidates across 16 specified dimensions (roles, batting position, bowling style, age at evaluation date, 2027 eligibility, RR historical contribution, 2–3 yr global form, sample size, squad balance, overseas limits); outputs versioned recommendations (`ANALYTICAL_RETAIN`, `ANALYTICAL_MONITOR`, `ANALYTICAL_REPLACEMENT_CANDIDATE`, `NO_SUITABLE_VERIFIED_REPLACEMENT`, `INSUFFICIENT_EVIDENCE`); preserves strict separation from the Top-10 hackathon ranking deliverable | Squad comparison test suite + role-separation assertions + reproducibility check |

---

## 9. Non-Functional Requirements

- **NFR-01 Determinism**: deterministic query path; seeded randomness only where documented;
  ranking model versioned and reproducible (AC-18).
- **NFR-02 Zero fabrication**: no invented players, statistics, memberships, injuries,
  mental states.
- **NFR-03 Evidence lineage**: every claim → `verification_records` + `data_sources`.
- **NFR-04 Format awareness**: no T20/List A/first-class mixing without documented
  normalisation.
- **NFR-05 Licensing & confidentiality**: ODC-By (verified locally) / CC BY 4.0 attribution;
  RESTRICTED sources per `DATA_SOURCE_REGISTER.md`; proprietary hackathon data isolated.
- **NFR-06 Frontend independence**: zero UI-framework imports in engines.
- **NFR-07 Status honesty**: documented Phase 0 is **PARTIALLY_COMPLETE** (documentation
  baseline complete; empirical data-source/licence audit incomplete) — see `docs/PHASES.md §2`.

---

## 10. Conclusion & Greenfield Baseline Declaration

This PRD (v2.2.0) specifies the target state for the **RR Squad Intelligence & Team Composition
Platform**, introducing Engine 07 (PVRE) and Phase 4B. No application code exists (`[STATUS: PLANNED - GREENFIELD BASELINE]`).
Phases 0–10 (`docs/PHASES.md`) must validate deliverables against these requirements, scope
boundaries, and acceptance criteria. The hackathon minimum submission (§7, §4.3) is
distinct from the long-term platform (MVP + post-MVP).
