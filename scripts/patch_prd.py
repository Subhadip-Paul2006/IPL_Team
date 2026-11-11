import os

with open('docs/PRD.md', 'r', encoding='utf-8') as f:
    text = f.read().replace('\r\n', '\n')

# 1. Update version header
text = text.replace(
    '**Document Version**: 2.1.1-TARGETED-REMEDIATION',
    '**Document Version**: 2.2.0'
)

# Replace revision note
target_note = '> **Revision Note (v2.1.1, targeted remediation)**: Use Case 3'
assert target_note in text

new_note_prefix = '''> **Revision Note (v2.2.0, PVRE Dual-Mode Research Architecture)**: Introduces Engine 07 — Player
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
> **Revision Note (v2.1.1, targeted remediation, retained for history)**: Use Case 3'''

text = text.replace(target_note, new_note_prefix)

# 2. Section 1.2
old_vision = 'with the **Mother Intelligence Engine (MIE)** orchestrating **six specialised engines** and\n**five support services** over a **31-entity PostgreSQL core**.'
new_vision = 'with the **Mother Intelligence Engine (MIE)** orchestrating **seven specialised engines**\n(PIRE, TMVE, CDCRE, CPPAE, CMIE, SICE, PVRE) and **five support services** over a\n**33-entity PostgreSQL core**.'
assert old_vision in text
text = text.replace(old_vision, new_vision)

# 3. Section 3.2
old_align = '| **High** | Architecture & engineering | MIE + 6 engines + 5 services; 31-entity 3NF core; deterministic queries; provenance records |'
new_align = '| **High** | Architecture & engineering | MIE + 7 engines + 5 services; 33-entity 3NF core; deterministic queries; provenance records |'
assert old_align in text
text = text.replace(old_align, new_align)

# 4. Section 4 replacement
s4_start = text.find('## 4. User Workflow (Primary — revised)')
s5_start = text.find('## 5. Functional Requirements (with traceability)')
assert s4_start != -1 and s5_start != -1

new_s4 = '''## 4. User Workflow (Primary — revised)

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
   /             \\
  No              Yes
  │                │
User clarification  Three-dimension membership verification (TMVE: Dimensions 1 & 2)
 (review & retry)   │
                    Eligibility Policy Service (Dimension 3: season-bound eligibility)
                    │
                    PVRE Mother Controller (Engine 07: Classification & Research Routing)
                   /                    │                         \\                      \\
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

'''

text = text[:s4_start] + new_s4 + text[s5_start:]

# 5. In Section 5.6 add FR-S6, and add Section 5.9 PVRE
sice_end = text.find('### 5.7 Support Services')
assert sice_end != -1

fr_s6 = '''| **FR-S6** | Role-Aware Incumbent-vs-Candidate Replacement Comparison: compares RR incumbent and eligible uncapped candidates across 16 dimensions; outputs versioned recommendations (`ANALYTICAL_RETAIN`, `ANALYTICAL_MONITOR`, `ANALYTICAL_REPLACEMENT_CANDIDATE`, `NO_SUITABLE_VERIFIED_REPLACEMENT`, `INSUFFICIENT_EVIDENCE`); keeps Top-10 ranking separate | TRD §8.4 | ARCH D8 | Phase 8 | `agent_sice` | AC-30 |

'''

text = text[:sice_end] + fr_s6 + text[sice_end:]

s6_hdr = text.find('## 6. Streamlit Views (UI Requirements)')
assert s6_hdr != -1

pvre_sec = '''### 5.9 Player Verification & Research Engine (PVRE — Engine 07)
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

'''

text = text[:s6_hdr] + pvre_sec + text[s6_hdr:]

# 6. Update Section 6 Streamlit views
s6_old = '''## 6. Streamlit Views (UI Requirements)

1. **Home / Team Builder** — create/rename/delete teams; add/remove players; assign roles;
   save configurations.
2. **Player Search** — name entry; PIRE candidates ranked by tier; ambiguity prompts.
3. **Player Identity Verification** — candidate evidence side-by-side; DOB/role corroboration;
   confirm-or-review flow.
4. **Historical RR Membership** — three-dimension badges; RR seasons (2008–15 / 2016–17
   suspension / 2018+ / 2027 unverified); other IPL teams; evidence links + verification
   date.
5. **Player Career Profile** — competition coverage table with four states, gaps, provenance.
6. **Performance Analytics** — CPPAE profile with DATA_DICTIONARY definitions, format
   tags, and visible sample sizes.
7. **Contextual Analysis** — CMIE annotations with provenance-tier badges.
8. **Player Comparison** — similar-role comparison with SICE notes.
9. **Squad Composition** — role distribution, depth, membership classes of current members.
10. **Squad Intelligence Report** — strengths/weaknesses, dependencies, priorities,
    alternatives, labelled recommendations; hackathon Top-10 board.
11. **Data Source and Verification Report** — per-claim provenance, verification status,
    licences, evidence tier; UNVERIFIED/CONFLICT listed explicitly.'''

s6_new = '''## 6. Streamlit Views (UI Requirements)

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
    unresolved claims, conflicting source IDs, and recommended manual checks.'''

assert s6_old in text
text = text.replace(s6_old, s6_new)

# 7. Add AC-24 through AC-30 in Section 8
ac23_str = '''| **AC-23** | Engine modules importable with Streamlit uninstalled (Next.js-ready) | Static import test |'''
ac_new_str = '''| **AC-23** | Engine modules importable with Streamlit uninstalled (Next.js-ready) | Static import test |
| **AC-24** | PVRE Deterministic Routing & Classification: Mother Controller orchestrates identity resolution (PIRE), RR relationship verification (TMVE), and eligibility assessment (Eligibility Policy Service); deterministically routes to Mode A on verified RR relationship, Mode B on verified uncapped non-RR, `REVIEW_REQUIRED` on ambiguous/conflicting evidence, or `OUT_OF_SCOPE` on non-RR capped; never infers uncapped status from database absence or non-membership without meeting TRD §4.5 negative verification rules | Automated classification fixture covering all 4 routing branches + negative proofs |
| **AC-25** | Mode A RR Historical Performance & Squad Separation: Module A1 analyses complete RR history across all evidenced seasons, strictly differentiating squad inclusion from playing XI appearances, calculating season-by-season batting, bowling, fielding/keeping, and role evolution | Contract test with squad-only vs Playing XI fixtures across RR seasons 2008–2025 |
| **AC-26** | Mode A Recent Global Performance Research: Module A2 retrieves performance across a configurable 2–3 year window relative to evaluation date for recognised global leagues (BBL, PSL, CPL, SA20, The Hundred, Intl, domestic); reports sample sizes, participation gaps, and format tags; never assumes non-participation from missing datasets | Multi-league fixture audit + date-window boundary assertions |
| **AC-27** | Mode A Replaceability Evidence Assessment: Module A3 synthesises RR history, recent global form, age trajectory at evaluation date, and sample completeness into structured analytical signals (`RETAIN_SIGNAL`, `MONITOR_SIGNAL`, `POTENTIALLY_REPLACEABLE`, `INSUFFICIENT_EVIDENCE`, `REVIEW_REQUIRED`); strictly forwards profile to SICE; never outputs arbitrary replacement probabilities or standalone release decisions | Signal generation unit tests + contract assertion |
| **AC-28** | Mode B Comprehensive Uncapped Discovery & Independent Verification: Investigates complete domestic career (Ranji, SMAT, VHT, Duleep, age-group, and league competitions); verifies uncapped eligibility under target season policy; rejects unverified players from entering the uncapped pool; preserves four-state coverage | Uncapped candidate fixture test + domestic competition coverage audit |
| **AC-29** | Mandatory `REVIEW_REQUIRED` Safety State: Hard safety pathway triggered on identity ambiguity, conflicting DOB/attributes, contradictory RR evidence, unverified eligibility, source discrepancies, or data coverage gaps; returns complete structured review dossier (`review_status`, `review_reason_codes`, `unresolved_claims`, `conflicting_source_ids`, `missing_evidence`, `recommended_manual_checks`); never silently falls back to Mode A/B | Adversarial conflict injection suite; verification that `REVIEW_REQUIRED` cannot enter candidate pool |
| **AC-30** | SICE Incumbent-vs-Candidate Replacement Comparison: SICE performs role-aware comparative evaluation between incumbent RR player and verified uncapped candidates across 16 specified dimensions (roles, batting position, bowling style, age at evaluation date, 2027 eligibility, RR historical contribution, 2–3 yr global form, sample size, squad balance, overseas limits); outputs versioned recommendations (`ANALYTICAL_RETAIN`, `ANALYTICAL_MONITOR`, `ANALYTICAL_REPLACEMENT_CANDIDATE`, `NO_SUITABLE_VERIFIED_REPLACEMENT`, `INSUFFICIENT_EVIDENCE`); preserves strict separation from the Top-10 hackathon ranking deliverable | Squad comparison test suite + role-separation assertions + reproducibility check |'''

assert ac23_str in text
text = text.replace(ac23_str, ac_new_str)

# 8. Section 10
old_s10 = '''This PRD specifies the target state for the **RR Squad Intelligence & Team Composition
Platform**. No application code exists (`[STATUS: PLANNED - GREENFIELD BASELINE]`).
Phases 1–10 (`docs/PHASES.md`) must validate deliverables against these requirements, scope
boundaries, and acceptance criteria. The hackathon minimum submission (§7, §4.3) is
distinct from the long-term platform (MVP + post-MVP).'''

new_s10 = '''This PRD (v2.2.0) specifies the target state for the **RR Squad Intelligence & Team Composition
Platform**, introducing Engine 07 (PVRE) and Phase 4B. No application code exists (`[STATUS: PLANNED - GREENFIELD BASELINE]`).
Phases 0–10 (`docs/PHASES.md`) must validate deliverables against these requirements, scope
boundaries, and acceptance criteria. The hackathon minimum submission (§7, §4.3) is
distinct from the long-term platform (MVP + post-MVP).'''

assert old_s10 in text
text = text.replace(old_s10, new_s10)

with open('docs/PRD.md', 'w', encoding='utf-8', newline='\n') as f:
    f.write(text)

print('docs/PRD.md successfully updated and written!')
