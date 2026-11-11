import os

with open('docs/PHASES.md', 'r', encoding='utf-8') as f:
    text = f.read().replace('\r\n', '\n')

# 1. Update version header
old_hdr = '''**Document Version**: 2.1.0-REMEDIATED
**Status**: `[STATUS: PHASE 0 PARTIALLY_COMPLETE (0a COMPLETE / 0b OPEN) · PHASES 1–10 PLANNED]`
**Date**: November 2026
**Primary Authors**: Principal Software Architect, Cricket Data Engineer, Systems Integration Engineer

> **Revision Note (v2.1.0, remediation)**: Phase 0 is **split** and its status corrected.'''

new_hdr = '''**Document Version**: 2.2.0
**Status**: `[STATUS: PHASE 0 PARTIALLY_COMPLETE (0a COMPLETE / 0b OPEN) · PHASES 1–10 PLANNED]`
**Date**: November 2026
**Primary Authors**: Principal Software Architect, Cricket Data Engineer, Systems Integration Engineer

> **Revision Note (v2.2.0, PVRE Dual-Mode Implementation Phase)**: Introduces **Phase 4B — PVRE
> Dual-Mode Player Verification & Research Engine** [PLANNED - MVP] into the authoritative
> implementation roadmap. Phase 4B governs the implementation of the Mother Controller,
> deterministic routing precedence, Mode A (Existing RR Player Replacement Intelligence: Module A1
> RR History, Module A2 Recent Global Performance across a configurable 2–3 year window, Module A3
> Replaceability Evidence Assessment with 5 analytical signal states), Mode B (Verified Uncapped
> Candidate Intelligence: complete domestic career discovery across Ranji, SMAT, VHT, Duleep, and
> age-groups), mandatory `REVIEW_REQUIRED` safety pathway, and SICE role-aware incumbent-vs-candidate
> replacement comparison. Reconciles database entity count to 33 entities everywhere. Adds 12 explicit
> checkpoints and maps Acceptance Criteria AC-24 through AC-30.
>
> **Revision Note (v2.1.0, remediation, retained for history)**: Phase 0 is **split** and its status corrected.'''

assert old_hdr in text
text = text.replace(old_hdr, new_hdr)

# 2. Update Timeline diagram in Section 1
old_timeline = '''| [PHASE 4: CDCRE DUAL CAPABILITY + AUTHORISED RESEARCH + PROVENANCE (Service C)]  (PLANNED - MVP)   |
|       |                                                                                            |
|       v                                                                                            |
| [PHASE 5: CPPAE PER DATA_DICTIONARY]  (PLANNED - MVP)                                              |'''

new_timeline = '''| [PHASE 4: CDCRE DUAL CAPABILITY + AUTHORISED RESEARCH + PROVENANCE (Service C)]  (PLANNED - MVP)   |
|       |                                                                                            |
|       v                                                                                            |
| [PHASE 4B: PVRE DUAL-MODE RESEARCH & REPLACEMENT ENGINE] (PLANNED - MVP)                           |
|   - Mother Controller · Mode A (RR history + global form) · Mode B (uncapped) · REVIEW_REQUIRED    |
|       |                                                                                            |
|       v                                                                                            |
| [PHASE 5: CPPAE PER DATA_DICTIONARY]  (PLANNED - MVP)                                              |'''

assert old_timeline in text
text = text.replace(old_timeline, new_timeline)

# 3. Update Consolidated Phase Status Matrix in Section 1
text = text.replace(
    '| **2** | Unified Database & Player Identity Resolution | 31-entity DDL execution + migration validation, PIRE deterministic tiers | PLANNED | 1 |',
    '| **2** | Unified Database & Player Identity Resolution | 33-entity DDL execution + migration validation, PIRE deterministic tiers | PLANNED | 1 |'
)

old_matrix_entry = '''| **4** | CDCRE dual capability + external research | Candidate discovery + career retrieval; provenance (Service C); negative-verification protocol | PLANNED | 2, 3, 0b |
| **5** | CPPAE per DATA_DICTIONARY | All B/W/F/M-series metrics, sample sizes, NULL discipline | PLANNED | 2 |'''

new_matrix_entry = '''| **4** | CDCRE dual capability + external research | Candidate discovery + career retrieval; provenance (Service C); negative-verification protocol | PLANNED | 2, 3, 0b |
| **4B** | PVRE Dual-Mode Player Verification & Research Engine | Mother Controller routing, Mode A (RR history + recent global form 2–3 yr window + replaceability assessment), Mode B (full domestic career discovery + independent eligibility verification), mandatory `REVIEW_REQUIRED` safety pathway, SICE replacement comparison integration | PLANNED | 2, 3, 4 |
| **5** | Complete Player Performance Analytics | DATA_DICTIONARY-governed profiles (B/W/F/M), integer-ball bowling notation, derived_features persistence, scorecard reconciliation | PLANNED | 2 |'''

assert old_matrix_entry in text
text = text.replace(old_matrix_entry, new_matrix_entry)

text = text.replace(
    '| **10** | Hackathon evaluation & submission | Top-10 reproducible ranking + dossiers, AC-01…AC-23 execution, submission packaging | PLANNED | 9 |',
    '| **10** | Hackathon evaluation & submission | Top-10 reproducible ranking + dossiers, AC-01…AC-30 execution, submission packaging | PLANNED | 9 |'
)

# 4. Insert Section 7 Phase 4B before Phase 5
p5_marker = '## 7. Phase 5 — Complete Player Performance Analytics (CPPAE) `[PLANNED - MVP]`'
assert p5_marker in text

phase_4b_text = '''## 7. Phase 4B — PVRE Dual-Mode Player Verification & Research Engine `[PLANNED - MVP]`

- **Status**: `[STATUS: PLANNED - GREENFIELD BASELINE]`
- **Objective**: Implement and validate Engine 07 (PVRE), the specialised dual-mode research and
  verification engine orchestrated by MIE. PVRE equips Rajasthan Royals decision-makers with the
  intelligence required to evaluate whether an existing RR incumbent can be replaced by a younger,
  verified-eligible uncapped talent (Mode A), or to execute deep, multi-format domestic career
  discovery for uncapped prospects (Mode B). It enforces an inviolable, non-bypassable
  `REVIEW_REQUIRED` safety pathway whenever identity, membership, or eligibility evidence is
  conflicting or incomplete.
- **Scope**:
  1. Mother Controller lifecycle, request classification, and deterministic 7-step routing waterfall.
  2. Mode A: Module A1 (RR historical research, squad membership vs match appearances separation).
  3. Mode A: Module A2 (recent global performance research across 2–3 year configurable window in
     recognised leagues: BBL, PSL, CPL, SA20, The Hundred, International, and Indian domestic).
  4. Mode A: Module A3 (replaceability evidence assessment; analytical signals: `RETAIN_SIGNAL`,
     `MONITOR_SIGNAL`, `POTENTIALLY_REPLACEABLE`, `INSUFFICIENT_EVIDENCE`, `REVIEW_REQUIRED`).
  5. Mode B: Uncapped candidate career discovery across Ranji Trophy, SMAT, VHT, Duleep, and
     age-groups, with independent policy verification (absence is never proof of uncapped status).
  6. Mandatory `REVIEW_REQUIRED` safety state with structured review dossiers.
  7. Typed, versioned request and response contracts (`PVREOutputContract` with 23 minimum fields).
  8. Downstream integration with SICE for 16-dimension role-aware incumbent-vs-candidate replacement
     comparisons.
- **Subphases**:
  - **4B.1 Mother Controller & Classification Engine**: Request ingestion, pre-identity discovery
    hook, PIRE identity resolution, TMVE membership retrieval, Eligibility Policy Service check,
    deterministic routing waterfall, and retry management.
  - **4B.2 Mode A RR Historical & Recent Global Research Modules**:
    * *Module A1 (RR History)*: Scorecard join vs squad membership, batting/bowling/fielding/keeping
      career tables, phase splits, role changes across 2008–2015 and 2018–2026.
    * *Module A2 (Recent Global Form)*: Multi-league connectors (BBL, PSL, CPL, SA20, The Hundred,
      Intl, Ranji, SMAT, VHT), 2–3 year configurable window, sample size tracking, format-tagged
      metrics, verified injury/availability integration.
  - **4B.3 Mode A Replaceability Evidence Assessment**: Signal synthesis algorithm generating
    `RETAIN_SIGNAL`, `MONITOR_SIGNAL`, `POTENTIALLY_REPLACEABLE`, `INSUFFICIENT_EVIDENCE`, or
    `REVIEW_REQUIRED` without arbitrary thresholds or fabricated release probabilities.
  - **4B.4 Mode B Uncapped Discovery & Policy Verification**: Domestic competition extractors,
    match-level aggregations, senior international cap verification, policy validation under active
    `eligibility_policies` version, and affirmative uncapped pool registration.
  - **4B.5 Mandatory `REVIEW_REQUIRED` Safety Pathway & Audit Dossier**: Interceptor for identity
    ambiguity, DOB conflicts, membership contradictions, unverified eligibility, source conflicts,
    and missing samples; compiles structured review dossiers and blocks automated pool entry.
  - **4B.6 SICE Replacement Integration**: Implementation of the 16-dimension role-aware comparison
    protocol and durable `ranking_runs` storage.
- **Inputs**:
  - Phase 1 staged datasets (`datasets/`).
  - Phase 2 canonical player registry (`players`, `player_aliases`).
  - Phase 3 three-dimension membership state (`player_membership_state`, `team_season_participation`).
  - Phase 3 active eligibility policy (`eligibility_policies`, `player_eligibility`).
  - Phase 4 CDCRE candidate discovery and career discovery capabilities.
- **Outputs**:
  - `src/pvre/mother_controller.py`: Mother Controller and classification router.
  - `src/pvre/mode_a/rr_history.py`: Module A1 RR historical performance analyzer.
  - `src/pvre/mode_a/global_performance.py`: Module A2 recent global performance research.
  - `src/pvre/mode_a/replaceability_assessor.py`: Module A3 replaceability signal generator.
  - `src/pvre/mode_b/uncapped_intelligence.py`: Mode B domestic discovery & verification engine.
  - `src/pvre/safety/review_handler.py`: Mandatory `REVIEW_REQUIRED` dossier generator.
  - `src/pvre/contracts.py`: Typed `PVRERequestContract` and `PVREOutputContract` models.
  - Populated `derived_features` rows (`feature_set_name = 'pvre_replacement_assessment'`).
  - Populated `verification_records` audit entries.
- **Dependencies**: Phase 2 (PIRE), Phase 3 (TMVE & Eligibility Service), Phase 4 (CDCRE),
  Phase 0b (External source verification).
- **Implementation Sequence**:
  1. Author Pydantic/dataclass contracts (`PVRERequestContract`, `PVREOutputContract`).
  2. Implement Mother Controller classification logic and routing waterfall.
  3. Implement Module A1 (RR history) with strict appearance vs squad membership separation.
  4. Implement Module A2 (Global form) with 2–3 year window boundary enforcement and multi-league
     format tagging.
  5. Implement Module A3 (Replaceability assessment) signal synthesis.
  6. Implement Mode B domestic discovery and affirmative policy verification.
  7. Implement `REVIEW_REQUIRED` safety interceptor and review dossier generation.
  8. Integrate PVRE output into SICE role-aware replacement comparison protocol.
  9. Execute comprehensive test suite covering all routing branches and edge cases.
- **Checkpoints (12 Explicit Verification Gates)**:
  1. *Mother Controller and classification*: Correctly dispatches requests to Mode A, Mode B,
     `REVIEW_REQUIRED`, or `OUT_OF_SCOPE` without guessing.
  2. *Existing RR association routing*: All players with `CURRENT_RR`, `HISTORICAL_RR_APPEARED`,
     or `HISTORICAL_RR_SQUAD_ONLY` deterministically enter Mode A.
  3. *RR historical research*: Scorecard appearances strictly separated from squad inclusion;
     zero batting/bowling stats credited for squad-only seasons.
  4. *Recent global performance research*: Accurately bounds performance to the 2–3 year
     configurable window; captures recognised leagues with visible sample sizes; format tags
     prevent cross-format contamination.
  5. *Replaceability evidence assessment*: Produces one of the 5 valid signal states with
     traceable component scores; generates zero standalone release decisions.
  6. *Uncapped candidate research*: Covers Ranji, SMAT, VHT, Duleep, and age-group matches without
     assuming uncapped status from database absence.
  7. *Eligibility verification*: Uncapped candidates carry verified affirmative proof under the
     active target-season policy; zero senior international caps.
  8. *`REVIEW_REQUIRED` handling*: Hard safety interceptor triggers on all ambiguous or conflicting
     fixtures, generating structured review dossiers and blocking candidate pool entry.
  9. *Shared output contract*: Contract validates all 23 minimum fields with explicit null,
     unavailable, not-established, verified, and conflict semantics.
  10. *CPPAE/CMIE integration*: Performance metrics and contextual conditions seamlessly feed
      the PVRE research scope.
  11. *SICE incumbent-vs-candidate comparison*: SICE successfully compares incumbent dossiers and
      candidate profiles across 16 role-aware dimensions, emitting versioned analytical
      recommendations.
  12. *End-to-end acceptance tests*: Full test harness executes successfully across all PVRE
      acceptance criteria (AC-24 through AC-30).
- **Acceptance Criteria**: AC-24, AC-25, AC-26, AC-27, AC-28, AC-29, AC-30.
- **Test Cases**:
  - *Mode A Tests*: Fixture with verified RR players (e.g. Sanju Samson, historical RR players,
    squad-only alumni); verify Module A1 appearance vs squad separation; verify Module A2 2–3 yr
    window bounding across global leagues; verify Module A3 analytical signal generation.
  - *Mode B Tests*: Fixture with verified domestic uncapped prospects; verify domestic tournament
    discovery (Ranji/SMAT/VHT); verify policy check rejects capped players; verify negative proof
    rule (database absence != uncapped).
  - *REVIEW_REQUIRED Tests*: Adversarial fixtures with name collisions (e.g. similar names), DOB
    discrepancies, contradictory squad records, and missing sample sizes; assert immediate
    interception and structured dossier emission.
  - *SICE Integration Tests*: Role-aware replacement comparison test comparing incumbent top-order
    batter vs uncapped batter, and pace all-rounder vs uncapped all-rounder; verify overseas
    constraints; assert Top-10 ranking remains strictly separate.
- **Failure Conditions**:
  - Any unknown player automatically assumed to be uncapped.
  - Any squad-only player credited with match appearances or performance metrics.
  - Cross-format statistics merged without format tagging.
  - A standalone player release or retention decision made inside PVRE.
  - An ambiguous identity or conflicting DOB bypassing `REVIEW_REQUIRED`.
  - Top-10 hackathon ranking logic merged into incumbent replacement evaluation.
- **Data & Provenance Requirements**: Every external datum must link to a `source_records` row and
  a `verification_records` assertion with documented tier, provider, timestamp, and licence.
- **Completion Evidence**: Test execution reports demonstrating 100% pass rate on AC-24..AC-30,
  zero auto-merges, zero fabricated stats, and verified contract compliance.

---

'''

text = text[:text.find(p5_marker)] + phase_4b_text + text[text.find(p5_marker):]

# 5. Renumber subsequent sections
text = text.replace('## 7. Phase 5 — Complete Player Performance Analytics (CPPAE)', '## 8. Phase 5 — Complete Player Performance Analytics (CPPAE)')
text = text.replace('## 8. Phase 6 — Contextual Match Intelligence (CMIE)', '## 9. Phase 6 — Contextual Match Intelligence (CMIE)')
text = text.replace('## 9. Phase 7 — Player Profile Generation (MIE + Service B)', '## 10. Phase 7 — Player Profile Generation (MIE + Service B)')
text = text.replace('## 10. Phase 8 — Squad Intelligence & Composition (SICE + Service E)', '## 11. Phase 8 — Squad Intelligence & Composition (SICE + Service E)')
text = text.replace('## 11. Phase 9 — Streamlit Application', '## 12. Phase 9 — Streamlit Application')
text = text.replace('## 12. Phase 10 — Hackathon Candidate Evaluation & Final Submission', '## 13. Phase 10 — Hackathon Candidate Evaluation & Final Submission')
text = text.replace('## 13. Cross-Phase Risk Assessment & Mitigation', '## 14. Cross-Phase Risk Assessment & Mitigation')
text = text.replace('## 14. Conclusion & Verification Summary', '## 15. Conclusion & Verification Summary')

# 6. Update Phase 7 (now Phase 10), Phase 8 (now Phase 11), Phase 10 (now Phase 13)
old_p7 = '''- **Objectives**: MIE end-to-end orchestration (candidate-discovery-first sequence);
  unified provenance-traced reports; JSON/CSV export with attribution; Team Builder
  wiring to `user_teams`/`user_team_players`.'''

new_p7 = '''- **Objectives**: MIE end-to-end orchestration (candidate-discovery-first sequence);
  PVRE Mother Controller routing (Mode A / Mode B / REVIEW_REQUIRED); unified
  provenance-traced reports; JSON/CSV export with attribution; Team Builder wiring
  to `user_teams`/`user_team_players`.'''

assert old_p7 in text
text = text.replace(old_p7, new_p7)

old_p8 = '''- **Objectives**: team management + role-aware squad evaluation; comparisons; labelled
  recommendations; no unvalidated probabilities.'''

new_p8 = '''- **Objectives**: team management + role-aware squad evaluation; SICE incumbent-vs-candidate
  replacement evaluation (§8.4) consuming PVRE Mode A replaceability assessments across 16
  dimensions; comparisons; labelled recommendations; no unvalidated probabilities; durable
  storage in `ranking_runs` (`run_type = 'REPLACEMENT_EVALUATION'`).'''

assert old_p8 in text
text = text.replace(old_p8, new_p8)

old_p10 = '''- **Objectives**: the **Top-10 youngest eligible uncapped candidate board** (PRD §4.3):
  reproducible role-aware ranking (versioned weights, shrinkage, age-within-role ordering),
  reserve list, per-candidate dossiers (eligibility verification, age as of evaluation date,
  roles, domestic evidence, T20 analysis, consistency, context, squad fit, risk/coverage
  limits, sources); full AC suite execution; submission packaging.'''

new_p10 = '''- **Objectives**: the **Top-10 youngest eligible uncapped candidate board** (PRD §4.3):
  reproducible role-aware ranking per [`docs/RANKING_SPEC.md`](RANKING_SPEC.md) (`RK-1.0.0`),
  reserve list, per-candidate dossiers (eligibility verification, age as of evaluation date,
  roles, domestic evidence, T20 analysis, consistency, context, squad fit, risk/coverage
  limits, sources); strict architectural separation from PVRE Mode A incumbent replacement
  evaluation; full AC suite execution (AC-01…AC-30); submission packaging.'''

assert old_p10 in text
text = text.replace(old_p10, new_p10)

# 7. Add Risk R13 and R14 to Risk Register
old_risk_end = '''| **R12** | External source licence misassumption (Kaggle/Hawkeye) | High | 0b, 4 | Register statuses RESTRICTED/UNVERIFIED until 0b evidence rows; no ingestion on unverified terms |'''

new_risk_end = '''| **R12** | External source licence misassumption (Kaggle/Hawkeye) | High | 0b, 4 | Register statuses RESTRICTED/UNVERIFIED until 0b evidence rows; no ingestion on unverified terms |
| **R13** | PVRE multi-league coverage gaps lead to false non-participation assumptions | High | 4B | Enforce four-state coverage tracking (`DATASET_UNAVAILABLE`/`NOT_ESTABLISHED`); mandate that missing datasets are never treated as non-participation; report sample sizes explicitly alongside every recent-form metric |
| **R14** | Mode A replacement evaluation exhibits role bias or uncalibrated replacement scores | High | 4B, 8 | Enforce role-aware comparison protocol across 16 dimensions; prohibit arbitrary single composite replacement scores; report component metrics transparently; label all outputs ANALYTICAL_RECOMMENDATION |'''

assert old_risk_end in text
text = text.replace(old_risk_end, new_risk_end)

with open('docs/PHASES.md', 'w', encoding='utf-8', newline='\n') as f:
    f.write(text)

print('docs/PHASES.md successfully updated and written!')
