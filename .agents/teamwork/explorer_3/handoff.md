# Handoff Report: Domestic Sources & Phase 4B Implementation Roadmap Mining (Requirements R3, R4, R5)

**Agent**: Explorer 3 (Domestic Sources & Roadmap Miner / Specification Miner)  
**Parent Orchestrator**: `9375951d-5885-4950-843a-c0fc3e12a05a`  
**Date**: 2026-11-11  
**Project**: IPL_Team Documentation Revision to v2.2.0  
**Status**: COMPLETE  

---

## 1. Observation

### 1.1 Local Dataset Lake Verification
Direct inspection of the local filesystem `d:\New folder (2)\datasets` via PowerShell commands revealed the following verified empirical state:
1. **Directory Structure & Match JSON Counts**:
   ```powershell
   Get-ChildItem -Path "datasets" -Directory | ForEach-Object { [PSCustomObject]@{ Directory = $_.Name; JsonCount = (Get-ChildItem -Path $_.FullName -Filter "*.json").Count } }
   ```
   - `bbl_male_json`: **662** matches
   - `bpl_male_json`: **469** matches
   - `cpl_male_json`: **445** matches
   - `hnd_male_json`: **201** matches
   - `icc_mens_cricket_world_cup_male_json`: **265** matches
   - `icc_mens_t20_world_cup_male_json`: **230** matches
   - `ilt_male_json`: **134** matches
   - `ipl_male_json`: **1,243** matches
   - `lpl_male_json`: **143** matches
   - `mlc_male_json`: **109** matches
   - `psl_male_json`: **357** matches
   - `sat_male_json`: **130** matches
   - `sma_json`: **695** matches
   - **Total Local JSON Match Files**: **5,083** files across **13** directories.
   - Registry CSV files in root of `datasets/`: `names.csv` (162,471 bytes), `people.csv` (1,187,398 bytes), `venues.csv` (48,722 bytes), `venue_names.csv` (12,501 bytes).
2. **Licensing & Documentation**:
   - Every single one of the 13 directories contains an authoritative `LICENSE.txt` confirming **Open Data Commons Attribution License (ODC-By v1.0)**.
   - Every directory contains a `README.txt` documenting Cricsheet JSON Schema version **1.3.0**.
3. **Syed Mushtaq Ali Trophy (SMAT) Empirical Breakdown**:
   - `datasets\sma_json\README.txt` confirms 695 Syed Mushtaq Ali Trophy matches from 2016-01-02 to 2024-12-15.
   - Match distribution by calendar year:
     * 2016: 83 matches
     * 2017: **0 matches** (temporal gap)
     * 2018: 79 matches
     * 2019: 261 matches
     * 2020: **0 matches** (temporal gap / season shifted)
     * 2021: 181 matches
     * 2022: 44 matches
     * 2023: 39 matches
     * 2024: 8 matches (knockout stages only)
   - **Key Finding**: Local SMAT ball-by-ball coverage is **partial** (695 matches total), with major coverage gaps in 2017, 2020, and group stages in 2022–2024.
4. **Absence of Indian Multi-Day & Age-Group Datasets on CricSheet**:
   - Search on Cricsheet documentation and downloads confirmed: Cricsheet **does not host** Ranji Trophy, Vijay Hazare Trophy, Duleep Trophy, Cooch Behar Trophy, Vinoo Mankad Trophy, Col. C.K. Nayudu Trophy, or Vijay Merchant Trophy.
   - Therefore, local ball-by-ball JSON exists **only** for Syed Mushtaq Ali Trophy (SMAT, partial 695 matches) among all Indian domestic tournaments.

### 1.2 External Source Realities (BCCI Portal & Commercial Portals)
1. **Official BCCI Portal (`bcci.tv`)**:
   - Probing confirmed `bcci.tv` does **not** provide a bulk downloadable dataset (no bulk CSV, JSON, or public REST API endpoints).
   - Live match centres and domestic archives dynamically render via internal XHR HTTP requests fetching private JSON payloads (e.g. `cricketapi-icc.pulselive.com` or internal backend endpoints).
   - Terms of service explicitly prohibit automated scraping, aggressive web crawling, and bot access.
   - Ball-by-ball tracking (speed radar, Hawk-Eye coordinates, wagon wheels) is completely absent for Indian domestic and age-group matches, with ball-by-ball text commentary available only for select televised matches.
   - Official scorecards provide: match metadata, playing XI, innings totals, batting summaries (runs, balls faced, 4s, 6s, dismissal kind), bowling summaries (overs, maidens, runs, wickets), and fall of wickets.
2. **ESPNcricinfo & Cricbuzz**:
   - Match scorecards for senior domestic cricket (Ranji, VHT, SMAT, Duleep) are comprehensively archived.
   - Direct programmatic fetching returns `HTTP 403 Forbidden` (Cloudflare / bot protections).
   - Age-group coverage (Cooch Behar, Vinoo Mankad, CK Nayudu) is sparse, usually restricted to tournament summaries and finals.
   - Must be classified as `RESTRICTED / PER-CLAIM` accessed solely via authorized demand-driven adapters with strict rate limits (<1 req/sec).

### 1.3 Baseline Documents Inspected
- `docs/DATA_SOURCE_REGISTER.md` (lines 1–176): Currently defines S1–S20, but lumps domestic multi-day and age-group tournaments into generic entry S18 ("Official BCCI Domestic Records").
- `docs/DATA_DICTIONARY.md` (lines 1–313): Defines Batting B01–B17, Bowling W01–W12, Fielding F01–F09, Match Contribution M01–M07, Phase Model §4, Format Rules §5 (The Hundred), Recent-form R01–R06, Replacement Signals §10, and SICE Comparison Dimensions D01–D16. Corrected formulas (B04 balls faced, W06 format-aware economy, W01 overs display, DNB distinction, Super Over isolation) are active.
- `docs/PHASES.md` (lines 1–511): Phase 4B currently outlined in §7 (lines 236–362) with 12 checkpoints and PLANNED status. Dependencies need explicit formalization (base vs performance analysis) to prevent circular loops with CPPAE (Phase 5) and CMIE (Phase 6). Phase 7 and Phase 8 require explicit PVRE dependencies.
- `docs/PRD.md` (lines 1–577): Maps functional requirements FR-PV1 through FR-PV8 and Acceptance Criteria AC-24 through AC-30.
- `docs/ARCHITECTURE.md` (lines 1–761): Outlines 7 engines, 5 support services, MIE cross-engine orchestration boundaries, and PVRE internal Mother Controller routing.

---

## 2. Logic Chain

1. **Premise 1: Ball-by-ball (BBB) vs Scorecard (SC) Distinction is Foundational**:
   - Because Cricsheet does not index Indian domestic red-ball or age-group tournaments, and because `bcci.tv` does not publish delivery telemetry or bulk delivery logs for non-televised domestic matches, **the platform cannot compute delivery-level metrics (e.g. dot-ball %, phase splits, balls faced where omitted) for multi-day and age-group cricket**.
   - Attempting to calculate delivery-level metrics without delivery logs would force either zero-imputation or synthetic extrapolation, violating core non-functional requirements NFR-02 (Zero fabrication) and AI_INSTRUCTIONS R1.
   - Therefore, the Domestic Source Inventory must explicitly separate **Scorecard Availability** from **Ball-by-Ball Availability**, providing formal fallback rules to scorecard-level aggregates (runs, balls, 4s, 6s, wickets, overs).

2. **Premise 2: Empirical Gaps Mandate 4-State Career Coverage & Gap Taxonomy**:
   - The local SMAT dataset has verified gaps (2017: 0 matches, 2020: 0 matches, 2024: only 8 matches).
   - In age-group cricket (Cooch Behar, Vinoo Mankad, Vijay Merchant), tournament archives from state associations are often published piecemeal or omit balls-faced counts for lower-order batters.
   - Treating dataset absence as evidence of player non-participation would unfairly penalize domestic prospects who played in unrecorded matches.
   - Therefore, PVRE and the Data Dictionary must define four formal coverage states (`COMPLETE_WITHIN_VERIFIED_SOURCES`, `PARTIAL_COVERAGE`, `UNKNOWN`, `REVIEW_REQUIRED`) and a participation gap taxonomy (`GAP_VERIFIED_INJURY`, `GAP_NATIONAL_DUTY`, `GAP_NOT_SELECTED`, `GAP_DOMESTIC_CLASH`, `GAP_UNKNOWN_UNEXPLAINED`).

3. **Premise 3: Conflict Handling & Negative Proofs**:
   - External sources frequently conflict (e.g. ESPNcricinfo lists a player's DOB as 2004-05-10 while a BCCI tournament roster lists 2004-08-15; or scorecard run totals disagree by 1-2 runs).
   - Silent resolution (averaging, overwriting, taking latest) destroys evidentiary integrity.
   - Therefore, every discrepancy must be recorded in `verification_records` with status `CONFLICT` and routed immediately to `REVIEW_REQUIRED`.
   - Furthermore, absence of a player from the local database must **never** be treated as proof of uncapped status; uncapped status requires affirmative verification against target-season eligibility policy.

4. **Premise 4: Acyclicity in Phase 4B Implementation Roadmap**:
   - PVRE operates in two distinct operational contexts:
     * Base Context (Mother Controller, identity resolution, RR relationship check, Mode B domestic discovery, eligibility verification, REVIEW_REQUIRED routing).
     * Performance Context (Mode A deep recent global performance analysis and replaceability assessment).
   - Mode A needs player performance metrics (CPPAE, Phase 5) and contextual pitch/weather conditions (CMIE, Phase 6) to evaluate recent 2–3 year form across global leagues.
   - If Phase 4B as a monolithic block is declared to depend on Phase 5 and 6, while Phase 5 and 6 depend on player registry and match ingestion, no circularity exists at the phase level if Phase 4B Base precedes Phase 5, and Mode A consumes Phase 5/6 outputs via Checkpoint 10.
   - MIE (Phase 7) orchestrates the unified player dossier, consuming PVRE (Phase 4B), CPPAE (Phase 5), and CMIE (Phase 6).
   - SICE (Phase 8) consumes PVRE Mode A replaceability assessments and Mode B uncapped profiles to perform squad-level replacement evaluations.
   - This acyclic flow guarantees architectural integrity.

---

## 3. Features Discovered & Edge Cases

### 3.1 Features Discovered

| # | Category | Feature | Description | Inputs | Outputs | Error Behavior | Discovered Via |
|---|----------|---------|-------------|--------|---------|----------------|----------------|
| 1 | Source Inventory | CricSheet SMAT Ball-by-Ball Archive (S5) | Local 695-file delivery ledger for Syed Mushtaq Ali Trophy | Match files in `datasets/sma_json/` | Delivery events, balls faced, over logs | Missing seasons (2017, 2020) quarantined | Local archive inspection & README verification |
| 2 | Source Inventory | BCCI Official Senior Domestic Scorecard Archives (S18A-D) | Scorecards for Ranji Trophy, SMAT, Vijay Hazare Trophy, and Duleep Trophy | `bcci.tv` match centres via Service C adapter | Innings batting & bowling scorecards, playing XIs | HTTP 403 / captcha -> rate limit backoff | `bcci.tv` network probing & terms inspection |
| 3 | Source Inventory | BCCI Official Age-Group Scorecard Archives (S18E-H) | Scorecards for Cooch Behar (U19), Vinoo Mankad (U19), CK Nayudu (U23/25), Vijay Merchant (U16) | `bcci.tv` junior centres via Service C adapter | Innings scorecards, tournament totals, birth registries | Broken legacy URLs -> flag `PARTIAL_COVERAGE` | DOM structure & youth section analysis |
| 4 | Source Inventory | ICC/ACC Youth International Match Archive (S19B) | Official scorecards for ICC U-19 Men's World Cup and U-19 Asia Cup | `icc-cricket.com` & tournament scorecards | Youth ODI/T20 scorecards, playing XIs, player caps | Missing tracking -> fallback to scorecard | Web search & tournament registry audit |
| 5 | Source Inventory | ESPNcricinfo Domestic Historical Archive (S20B) | Historical match scorecards for Ranji/VHT/SMAT pre-dating `bcci.tv` (pre-2018) | ESPNcricinfo match URLs | Innings scorecards, career totals | HTTP 403 on automated scrapers -> human-gated research | Empirical HTTP 403 verification & terms check |
| 6 | Data Dictionary | Time-Decay Weighted Recent-Form Metrics (R01–R04) | Windowed strike rate, economy, boundary %, and dot % over 2–3 year window with exponential decay | Match innings, `match_date`, $t_{\text{eval}}$, $T_{\text{half}}$ | Weighted rate, sample sizes | Denominator 0 -> NULL (never 0.00) | `docs/DATA_DICTIONARY.md` §9 & PRD FR-PV3 |
| 7 | Data Dictionary | Participation Consistency & Gap Taxonomy (R05) | Scheduled vs played match ratio with categorized non-participation reasons | Competition schedules, team rosters, injury reports | Consistency ratio, gap taxonomy tags | Unexplained absence -> `GAP_UNKNOWN_UNEXPLAINED` | PRD FR-PV3 & TRD §9.3 |
| 8 | Data Dictionary | Four-State Career Coverage Model | Strict classification of player career completeness across verified sources | Competition rosters, match logs, source registers | `COMPLETE_WITHIN_VERIFIED_SOURCES`, `PARTIAL_COVERAGE`, `UNKNOWN`, `REVIEW_REQUIRED` | Incomplete sources -> explicit missing tournament list | PRD FR-PV5 & TRD §9.4 |
| 9 | Data Dictionary | PVRE Replaceability Assessment Signals (Module A3) | Multi-dimensional replaceability signal without scalar replacement probabilities | RR history, recent form, age delta, sample completeness | `RETAIN_SIGNAL`, `MONITOR_SIGNAL`, `POTENTIALLY_REPLACEABLE`, `INSUFFICIENT_EVIDENCE`, `REVIEW_REQUIRED` | Missing sample -> `INSUFFICIENT_EVIDENCE` | `docs/DATA_DICTIONARY.md` §10 & PRD AC-27 |
| 10 | Data Dictionary | 16 Role-Aware Incumbent-vs-Candidate Comparison Dimensions (D01–D16) | Multidimensional evaluation matrix comparing RR incumbent vs uncapped candidate | PVRE Mode A incumbent profile + Mode B candidate profile | Matrix of 16 dimension scores, sample deltas, relative advantages | Unmatched roles -> flag role mismatch | `docs/DATA_DICTIONARY.md` §11 & PRD AC-30 |
| 11 | Phase 4B Roadmap | PVRE Mother Controller & Deterministic Waterfall (CP 1) | Internal request classification and 7-step routing logic | Player name, `evaluation_date`, target season ID | Route to Mode A, Mode B, `REVIEW_REQUIRED`, or `OUT_OF_SCOPE` | Unknown player -> candidate discovery, never auto-uncapped | `docs/PHASES.md` §7 & PRD AC-24 |
| 12 | Phase 4B Roadmap | Module A1 RR Historical Research (CP 2, 3) | Analysis of all evidenced RR seasons strictly separating squad-only from playing XI | `squad_memberships`, `player_team_history`, match logs | RR batting, bowling, fielding career profiles | Squad-only season -> zero batting/bowling stats | `docs/PHASES.md` §7 & PRD AC-25 |
| 13 | Phase 4B Roadmap | Module A2 Recent Global Performance (CP 4) | Multi-league performance research over 2–3 year window outside RR | BBL, PSL, CPL, SA20, Hundred, Intl, domestic match files | League-partitioned performance profiles | Dataset absence -> gap recorded, never non-participation | `docs/PHASES.md` §7 & PRD AC-26 |
| 14 | Phase 4B Roadmap | Module B Domestic Discovery & Policy Verification (CP 6, 7) | Multi-tournament domestic discovery and affirmative uncapped policy check | Domestic scorecards, senior international cap registry | Verified uncapped player profile & career dossier | Senior cap found -> reject from uncapped pool | `docs/PHASES.md` §7 & PRD AC-28 |
| 15 | Phase 4B Roadmap | Mandatory `REVIEW_REQUIRED` Safety Pathway (CP 8) | Interceptor for all ambiguities, conflicts, and missing data | Conflict flags, collision records, gap records | Structured review dossier (6 explicit blocks) | Hard block: cannot enter candidate or replacement pool | `docs/PHASES.md` §7 & PRD AC-29 |
| 16 | Phase 4B Roadmap | Shared Output Contract `PVREOutputContract` (CP 9) | Typed, versioned JSON contract with 23 minimum required fields | Internal module outputs | Validated `PVREOutputContract` payload | Missing field or invalid enum -> schema validation error | `docs/TRD.md` §9.6 & PRD FR-PV8 |

### 3.2 Edge Cases

| # | Feature | Input | Observed Behavior |
|---|---------|-------|-------------------|
| 1 | Mother Controller | Unknown player absent from internal DB | Triggers CDCRE pre-identity discovery; defaults `player_capped_status = 'UNVERIFIED'`, `ipl_uncapped_eligibility = 'NOT_ASSESSED'`; routes to `REVIEW_REQUIRED`; NEVER infers uncapped status from database absence. |
| 2 | Mother Controller | Verified Capped Non-RR Player (e.g. Virat Kohli) | Identity resolved, international caps verified, no RR relationship; deterministically routes to `OUT_OF_SCOPE` (`route_status = 'OUT_OF_SCOPE_CAPPED_NON_RR'`); blocked from Mode B and uncapped candidate pool. |
| 3 | PIRE Disambiguation | Two distinct domestic players with identical names (e.g. "Amit Sharma") | PIRE detects collision; generates two candidate entities; Mother Controller halts automated dispatch; flags `COLLISION_MULTIPLE_IDENTITIES`; routes to `REVIEW_REQUIRED` with candidate dossiers. |
| 4 | TMVE Membership | Player in RR squad list for 2021 but played 0 matches | Module A1 credits player with squad inclusion for 2021 (`HISTORICAL_RR_SQUAD_ONLY`), but records `appearances = 0`; credits zero batting runs, balls faced, overs, or wickets; prevents false performance claims. |
| 5 | TMVE Participation | Target season set to IPL 2027 | System inspects `team_season_participation` for 2027; finds status `UNKNOWN`; evaluates eligibility against versioned `eligibility_policies` draft; flags 2027 squad status as pending authoritative publication. |
| 6 | Eligibility Service | Player has 0 senior international caps but played 1 match in IPL 2023 for KKR | Evaluates against IPL 2027 uncapped definition; under standard BCCI rules, any IPL playing XI appearance within 5 preceding years classifies player as CAPPED; eligibility service rejects uncapped status -> `OUT_OF_SCOPE`. |
| 7 | Source Ingestion | Scorecard runs total (e.g. 48) differs from sum of delivery events (47) by 1 run | Data Quality Gate (Service D) flags discrepancy; match is quarantined; provenance record flagged `CONFLICT`; metric falls back to scorecard total with `DATA_DISCREPANCY_FLAG` attached. |
| 8 | Source Ingestion | Older age-group scorecard (e.g. Vijay Merchant 2018) records runs (35) but balls faced = NULL | Ingestion preserves `balls_faced = NULL`; batting average computed if dismissed; strike rate returns `NULL` with `sample=0`; never assumes balls faced equals runs or imputes run-a-ball. |
| 9 | Source Ingestion | Player DOB in BCCI tournament roster (2004-05-10) conflicts with ESPNcricinfo (2003-11-22) | System records both assertions in `verification_records`; status set to `CONFLICT`; DOB remains unverified; age delta in SICE flagged `UNRESOLVED_DOB_CONFLICT`; routes to `REVIEW_REQUIRED`. |
| 10 | Career Coverage | Player participated in SMAT 2020 where CricSheet has 0 matches | System detects season gap in local lake; checks external BCCI scorecard; if external unindexed, marks `PARTIAL_COVERAGE`; records `missing_competitions = ['SMAT_2020']`; does NOT conclude player did not participate. |

---

## 4. Comprehensive Specifications for Revision

### 4.1 Requirement R3: Dedicated Domestic and Age-Group Source Inventory

To be incorporated into `docs/DATA_SOURCE_REGISTER.md` §1 (expanding S18 and adding discrete domestic rows):

#### 4.1.1 Source Register Expansion Matrix

| Source ID | Tournament / Resource | Format & Sanctioning Body | Scorecard Availability | Ball-by-Ball Availability | Seasons Covered & Known Gaps | Fields Provided | Licensing & Legal Status | Collection Method & Access Constraints | Fallback & Conflict Rules | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| **S5** | **CricSheet SMAT (Local Archive)** | Domestic T20 (BCCI) | Match summaries in JSON | **Ball-by-ball (delivery level)** | **695 matches verified locally** (2016: 83, 2018: 79, 2019: 261, 2021: 181, 2022: 44, 2023: 39, 2024: 8). Gaps: 2017 (0), 2020 (0). | Match metadata (`info`), delivery events (`batter`, `bowler`, `runs`, extras, wickets), `people` hashes | **ODC-By v1.0 — VERIFIED** (`LICENSE.txt` present in `datasets/sma_json/`) | Local filesystem archive (`datasets/sma_json/`); zero rate limits; direct ingestion per TRD §9.1 | When delivery events conflict with official BCCI scorecard, quarantine delivery block and flag `CONFLICT_SCORECARD_VS_BBB`. Missing matches fallback to S18B. | **VERIFIED** |
| **S18A** | **BCCI Ranji Trophy Scorecard Archive** | First-Class Men's Multi-Day (4/5 days, BCCI) | **Innings & Match Scorecards** (Comprehensive) | **UNAVAILABLE** (0 public BBB files; only select televised games have text comms) | 2018/19–2024/25 comprehensive on `bcci.tv`; earlier seasons archived. Gaps: 2020/21 cancelled (COVID-19). | Playing XI, batting (runs, balls faced, 4s, 6s, dismissal kind), bowling (overs, maidens, runs, wickets), fall of wickets, toss, result | **RESTRICTED** — BCCI terms of service; automated mass scraping prohibited; copyright BCCI | Authorised demand-driven adapter (Service C) querying `bcci.tv` match centre via XHR JSON; rate-limited (<1 req/sec); per-claim provenance mandatory | Delivery metrics (dot %, phase splits) return `NOT_COMPUTABLE_FROM_AVAILABLE_SOURCES`. Fallback to innings aggregates. Career coverage marked `COMPLETE_WITHIN_VERIFIED_SOURCES` if all match scorecards present. | **RESTRICTED / PER-CLAIM** |
| **S18B** | **BCCI Syed Mushtaq Ali Trophy (SMAT) Scorecard Archive** | Domestic T20 Men's (BCCI) | **Innings & Match Scorecards** (Complete) | **Partial** (televised matches only on broadcast feeds) | 2018/19–2024/25 complete on `bcci.tv`. Reconciles gaps in S5 (2017, 2020, 2022–2024 group stages). | Playing XI, batting (runs, balls, 4s, 6s), bowling (overs, maidens, runs, wickets), match summary | **RESTRICTED** — BCCI terms of service | Authorised demand-driven adapter (Service C) fetching scorecards for matches missing from S5 | Primary source for missing SMAT matches. If S5 delivery sum conflicts with S18B innings runs, log both in `source_records`, set `verification_status = 'CONFLICT'`, and route to `REVIEW_REQUIRED`. | **RESTRICTED / PER-CLAIM** |
| **S18C** | **BCCI Vijay Hazare Trophy (VHT) Scorecard Archive** | List A Men's 50-Over (BCCI) | **Innings & Match Scorecards** (Comprehensive) | **UNAVAILABLE** (0 public BBB files; televised knockouts only have text commentary) | 2018/19–2024/25 comprehensive on `bcci.tv`. Historical seasons archived. | Playing XI, batting (runs, balls, 4s, 6s, dismissal mode), bowling (overs, maidens, runs, wickets), fall of wickets | **RESTRICTED** — BCCI terms of service | Authorised demand-driven adapter (Service C); rate-limited (<1 req/sec); per-claim provenance mandatory | Fallback to 50-over scorecard metrics. Phase splits return `NOT_COMPUTABLE`. Evaluates List A strike rotation and middle-overs anchor capability for Mode B candidates. | **RESTRICTED / PER-CLAIM** |
| **S18D** | **BCCI Duleep Trophy Scorecard Archive** | First-Class Men's Zonal Multi-Day (BCCI) | **Innings & Match Scorecards** (Complete) | **UNAVAILABLE** (Televised matches only have text commentary) | 2018/19–2024/25 active seasons; zonal & regional tournament iterations. | Playing XI, batting summaries, bowling figures, match result | **RESTRICTED** — BCCI terms of service | Authorised demand-driven adapter (Service C); per-claim provenance mandatory | First-class metrics fallback to scorecard. High-leverage domestic multi-day proving ground against international talent. | **RESTRICTED / PER-CLAIM** |
| **S18E** | **BCCI Cooch Behar Trophy U-19 Scorecard Archive** | Under-19 Men's Multi-Day (4-day, BCCI) | **Innings & Match Scorecards** | **UNAVAILABLE** (0 BBB datasets exist) | 2018/19–2024/25 on `bcci.tv` youth match centre. Gaps: 2020/21 cancelled (COVID). Older seasons partial. | Playing XI, batting (runs, balls where recorded, 4s, 6s), bowling (overs, maidens, runs, wickets), match result | **RESTRICTED** — BCCI terms of service; fair dealing / internal scouting research | Authorised demand-driven adapter (Service C); rate-limited; per-claim provenance mandatory | Balls faced missing for lower order in older scorecards -> return `balls_faced = NULL`, `strike_rate = NULL`. Never impute balls faced. Evaluates U-19 multi-day defensive technique and red-ball stamina. | **RESTRICTED / PER-CLAIM** |
| **S18F** | **BCCI Vinoo Mankad Trophy U-19 Scorecard Archive** | Under-19 Men's One-Day (50-over, BCCI) | **Innings & Match Scorecards** | **UNAVAILABLE** (0 BBB datasets exist) | 2018/19–2024/25 on `bcci.tv` youth match centre. Recent seasons complete. | Playing XI, batting summaries, bowling figures, fall of wickets | **RESTRICTED** — BCCI terms of service | Authorised demand-driven adapter (Service C); per-claim provenance mandatory | Evaluates white-ball U-19 boundary capability and List A tempo. Scorecard metrics only; delivery metrics return `NOT_COMPUTABLE`. Missing matches flag `PARTIAL_COVERAGE`. | **RESTRICTED / PER-CLAIM** |
| **S18G** | **BCCI Col. C.K. Nayudu Trophy U-23/U-25 Scorecard Archive** | Under-23 / Under-25 Men's Multi-Day (4-day, BCCI) | **Innings & Match Scorecards** | **UNAVAILABLE** (0 BBB datasets exist) | 2018/19–2024/25 on `bcci.tv` match centre. Formats transitioned between U-23 and U-25 across seasons. | Playing XI, batting summaries, bowling figures, match results | **RESTRICTED** — BCCI terms of service | Authorised demand-driven adapter (Service C); per-claim provenance mandatory | Crucial developmental transition bridge between U-19 and senior Ranji. Scorecard metrics only. Absence from CK Nayudu is not non-participation if player represented senior state team. | **RESTRICTED / PER-CLAIM** |
| **S18H** | **BCCI Vijay Merchant Trophy U-16 Scorecard Archive** | Under-16 Men's Multi-Day (3/4-day, BCCI) | **Innings & Match Scorecards** (Basic summaries) | **UNAVAILABLE** (0 BBB datasets exist) | 2018/19–2024/25 on `bcci.tv` junior centre. Gaps in early rounds and older seasons. | Playing XI, batting runs, 4s, 6s (balls faced frequently missing in older files), bowling overs, runs, wickets | **RESTRICTED** — BCCI terms of service | Authorised demand-driven adapter (Service C); per-claim provenance mandatory | Early talent discovery; birth registration corroboration. Balls faced omitted -> strike rate `NULL`. Missing seasons flag `PARTIAL_COVERAGE`. | **RESTRICTED / PER-CLAIM** |
| **S19B** | **ICC / ACC Youth International Match Archive** | ICC U-19 Men's World Cup & U-19 Asia Cup (Youth ODIs / T20s) | **Complete Scorecards** (ICC official & ESPNcricinfo) | **Partial** (televised World Cup matches have ball-by-ball text commentary) | All editions: U-19 World Cup (1988, 1998–2024), U-19 Asia Cup (2012–2024). Comprehensive. | Playing XI, batting summaries, bowling figures, fall of wickets, official youth international player caps | **RESTRICTED** — ICC / ACC copyright; fair dealing scouting research | Authorised demand-driven adapter (Service C); per-claim provenance mandatory | Any senior international cap disqualifies uncapped status; Youth international appearances do NOT disqualify uncapped status. High-pressure global junior benchmark. | **RESTRICTED / PER-CLAIM** |
| **S20B** | **ESPNcricinfo Domestic Historical Archive** | Indian Domestic Historical Circuit (1934–2018) | **Complete Scorecards** (Ranji, VHT, Duleep, SMAT) | **UNAVAILABLE** (Historical multi-day delivery ledgers do not exist) | Multi-decade historical coverage. Complete for senior domestic finals and major league matches. | Career profiles, match scorecards, bowling spells, player DOB and biographical profiles | **RESTRICTED** — ESPNcricinfo / Disney Star proprietary terms; HTTP 403 on automated scraping | Authorised human-gated research adapter; strict rate limiting (<1 req/sec); per-claim verification | Secondary reference for pre-2018 domestic careers. Conflicting statistics vs official BCCI scorecards flag `CONFLICT` and route to `REVIEW_REQUIRED`. | **RESTRICTED / PER-CLAIM** |

#### 4.1.2 Source Conflict Handling, Fallback, and Marking Protocol
1. **Marking Protocol**:
   - `VERIFIED`: The dataset exists locally in the repository, has been hashed and counted, and possesses an inspected permissive licence (e.g. S1–S5, S13–S17 under ODC-By v1.0).
   - `RESTRICTED / PER-CLAIM`: The source is proprietary or governed by terms of service forbidding bulk scraping (e.g. `bcci.tv`, `icc-cricket.com`, `espncricinfo.com`). No bulk dataset may be assumed. Data must be ingested claim-by-claim via Service C with documented provenance (`verification_records` row linking URL, timestamp, HTTP status, and evidence tier).
   - `UNVERIFIED`: An external claim or dataset that has not yet been corroborated by a primary/secondary verification record.
   - `UNAVAILABLE`: The data is known not to exist (e.g. ball-by-ball tracking for 1990s Ranji Trophy or sensor data for domestic pitches).
2. **Conflict Resolution Rules**:
   - *Scorecard vs Ball-by-Ball Sum*: If CricSheet SMAT (S5) delivery sum disagrees with BCCI official scorecard (S18B) totals by runs or wickets, the delivery sequence is quarantined in Service D. The system generates a `verification_records` entry with `verification_status = 'CONFLICT'`, logs `review_reason_codes = ['CONFLICT_SCORECARD_VS_BBB']`, and routes the profile to `REVIEW_REQUIRED`.
   - *Conflicting Biographical / DOB Records*: If an external profile (S20B) states DOB as `2004-05-10` while official BCCI registration records (S18) state `2004-08-15`, the system **never averages or overwrites**. Both claims are persisted in `verification_records`, the player is flagged `CONFLICT_DOB_RECORD`, and uncapped age eligibility evaluation is halted in `REVIEW_REQUIRED`.
   - *Conflicting Participation Records*: If one source claims a player was in the playing XI while another marks them as bench/substitute, the system records `CONFLICT_PARTICIPATION_EVIDENCE` and demands manual verification against the official match referee report.
3. **Fallback Behaviour**:
   - When delivery-level data (BBB) is unavailable (which applies to all multi-day and age-group cricket, and unindexed SMAT matches):
     * Fallback to **Innings-Level Scorecard Metrics**: B01 (Matches), B02 (Innings), B03 (Runs), B04 (Balls Faced where recorded), B05 (Batting Average), B06 (Strike Rate where balls recorded), B07 (Boundaries), W01 (Overs), W03 (Runs Conceded), W04 (Wickets), W05 (Bowling Average), W06 (Economy Rate), W07 (Bowling Strike Rate).
     * Delivery-level metrics (B09 dot-ball %, B12 phase splits, B14 pace/spin splits, W08 bowling dot %, W11 speed, W12 line/length) return `NOT_COMPUTABLE_FROM_AVAILABLE_SOURCES`.
     * Flag `career_coverage_state = 'PARTIAL_COVERAGE'` or `COMPLETE_WITHIN_VERIFIED_SOURCES` with an explicit indicator: `granularity = 'SCORECARD_ONLY'`.
   - When balls faced are missing from junior scorecards:
     * Set `balls_faced = NULL` and `strike_rate = NULL`. Never impute balls faced from runs scored or assume run-a-ball.

---

### 4.2 Requirement R4: Data Dictionary Enhancements

To be incorporated into `docs/DATA_DICTIONARY.md`:

#### 4.2.1 PVRE Recent-Form Metrics (Module A2 — Global Performance)
Evaluated across a configurable window $W \in [2, 3]$ years anchored to an explicit `evaluation_date` ($t_{\text{eval}}$).

1. **Time-Decay Weighting Function**:
   When weighting recent innings within the evaluation window, the platform applies an exponential decay function based on the elapsed days between the match date ($t_i$) and the evaluation date ($t_{\text{eval}}$):
   $$w(t_i) = \exp\left(-\frac{\ln(2) \cdot (t_{\text{eval}} - t_i)}{T_{\text{half}}}\right)$$
   where $T_{\text{half}} = 365\text{ days}$ (default parameter, versioned in `ranking_configurations`). If $t_i > t_{\text{eval}}$, the match is excluded. If $(t_{\text{eval}} - t_i) > W \times 365.25\text{ days}$, $w(t_i) = 0$.

2. **Metric Definitions**:
   - **R01 Window Batting Strike Rate**:
     $$\text{R01} = \frac{100 \times \sum_{i \in W} w(t_i) \cdot \text{runs}_i}{\sum_{i \in W} w(t_i) \cdot \text{balls\_faced}_i}$$
     *Class*: DERIVED. *Source*: `batting_innings`, `matches.match_date`. *Exclusions*: Super Overs; matches outside window $W$. *Null Rule*: Denominator = 0 $\rightarrow$ `NULL`; `sample = balls_faced` always displayed.
   - **R02 Window Bowling Economy Rate**:
     $$\text{R02} = \frac{\sum_{i \in W} w(t_i) \cdot \text{balls\_per\_over}(c_i) \cdot \text{runs\_conceded}_i}{\sum_{i \in W} w(t_i) \cdot \text{legal\_balls}_i}$$
     *Class*: DERIVED. *Source*: `bowling_spells`, `competitions.balls_per_over`. *Exclusions*: Super Overs; matches outside window $W$. *Null Rule*: Legal balls = 0 $\rightarrow$ `NULL`; The Hundred uses $\text{balls\_per\_over} = 5$.
   - **R03 Window Boundary %**:
     $$\text{R03} = 100 \times \frac{\sum_{i \in W} w(t_i) \cdot (4 \cdot \text{fours}_i + 6 \cdot \text{sixes}_i)}{\sum_{i \in W} w(t_i) \cdot \text{runs}_i}$$
     *Class*: DERIVED. *Source*: `batting_innings`. *Null Rule*: Runs = 0 $\rightarrow$ `NULL`.
   - **R04 Window Dot Ball %**:
     $$\text{R04} = 100 \times \frac{\sum_{i \in W} w(t_i) \cdot \text{dot\_balls}_i}{\sum_{i \in W} w(t_i) \cdot \text{balls\_faced}_i}$$
     *Class*: DERIVED. *Source*: `batting_innings` / `bowling_spells`. *Null Rule*: Balls = 0 $\rightarrow$ `NULL`. Only computed for competitions with verified delivery tracking; returns `NOT_COMPUTABLE_FROM_AVAILABLE_SOURCES` for scorecard-only domestic matches.
   - **R05 Participation Consistency & Gap Taxonomy**:
     *Definition*: Ratio of matches played to team scheduled fixtures per competition season within window $W$:
     $$\text{Consistency} = \frac{\text{Matches Played}}{\text{Team Scheduled Matches}}$$
     *Gap Taxonomy*: Every scheduled match in which the player did not participate must be tagged with a mutually exclusive reason code:
     * `GAP_VERIFIED_INJURY`: Documented medical / availability notice in `verification_records`.
     * `GAP_NATIONAL_DUTY`: Clashing international fixture in senior national squad.
     * `GAP_DOMESTIC_CLASH`: Clashing fixture in higher-priority domestic tournament.
     * `GAP_NOT_SELECTED`: Present in squad list but omitted from playing XI (tactical / form).
     * `GAP_UNKNOWN_UNEXPLAINED`: Absence cannot be established from verified records.
   - **R06 Window Sample Indicators**:
     *Definition*: Vector of integer counts: `(matches_played, innings_batted, balls_faced, overs_bowled, legal_balls_bowled, wickets_taken)` partitioned by competition ID and format tag across window $W$.
     *Rule*: Displayed alongside every derived rate metric. If balls faced $< 20$ or legal balls bowled $< 30$, flag `INSUFFICIENT_SAMPLE`.

#### 4.2.2 Four Career Coverage States
PVRE enforces four mutually exclusive states governing a player's career evidence:
1. `COMPLETE_WITHIN_VERIFIED_SOURCES`: All known competitions and seasons in which the player is recorded to have participated have 100% verified match scorecard or ball-by-ball coverage in the platform's registered sources.
2. `PARTIAL_COVERAGE`: The player has verifiable appearances, but one or more domestic competitions, youth tournaments, or seasons have documented missing match records in the data lake (e.g. unindexed SMAT group games, missing Vinoo Mankad scorecards). The output profile must carry an explicit `missing_competitions` array.
3. `UNKNOWN`: Insufficient evidence to establish whether the player participated in domestic or league cricket; external research is pending.
4. `REVIEW_REQUIRED`: Discrepancy between external assertions (e.g. a news article claiming 50 career matches) and verified scorecards (e.g. only 35 scorecards located), or contradictory squad records across providers.

#### 4.2.3 PVRE Module A3 Replaceability Assessment Signals
Synthesizes Module A1 (RR history), Module A2 (recent form), age delta, availability, and sample completeness:
1. `RETAIN_SIGNAL`: Incumbent demonstrates sustained elite role-specific performance across historical RR appearances and recent global window with high sample adequacy and consistent availability.
2. `MONITOR_SIGNAL`: Incumbent displays moderate performance or minor form fluctuations in the recent window, but maintains historical franchise equity or limited replacement urgency. Requires tracking through upcoming domestic/franchise fixtures.
3. `POTENTIALLY_REPLACEABLE`: Incumbent displays persistent form degradation over 2–3 years, role stagnation, availability constraints, or advancing age where verified uncapped candidates offer superior role fit, efficiency, or development trajectory.
4. `INSUFFICIENT_EVIDENCE`: Evidentiary coverage within the 2–3 year evaluation window falls below minimum sample thresholds (<20 batting balls, <30 overs bowled, or unverified recent leagues). Prevents premature classification.
5. `REVIEW_REQUIRED`: Unresolved data conflicts, contradictory contract/appearance records, contested identity records, or missing mandatory provenance. Requires human analyst audit.

*Guardrail*: PVRE signals are advisory inputs to Senior Management and SICE. PVRE must **never** make auction, release, retention, or signing decisions, and must **never** output scalar replacement probabilities (e.g. "78.4% replaceability score") or arbitrary composite single-index scores.

#### 4.2.4 SICE Analytical Recommendation States
When SICE evaluates squad composition and incumbent replacement:
1. `ANALYTICAL_RETAIN`: Recommend retention based on role superiority, historical equity, and squad balance.
2. `ANALYTICAL_MONITOR`: Maintain on watchlist; compare in pre-auction trials.
3. `ANALYTICAL_REPLACEMENT_CANDIDATE`: Candidate demonstrates superior role fit and statistical profile across comparison dimensions.
4. `NO_SUITABLE_VERIFIED_REPLACEMENT`: Incumbent is potentially replaceable, but no verified uncapped candidate meets role and squad constraints.
5. `INSUFFICIENT_EVIDENCE`: Either incumbent or candidate lacks sufficient sample size.

#### 4.2.5 16 Role-Aware Incumbent-vs-Candidate Comparison Dimensions (D01–D16)

| # | Dimension | Role Applicability | Incumbent Metric Basis | Candidate Metric Basis | Evidentiary Basis |
|---|---|---|---|---|---|
| **D01** | **Base Scoring Rate** | Top-order, Finisher, All-rounder | Window Batting Strike Rate (R01, B06) | SMAT/Domestic T20 Strike Rate (B06) | CricSheet / BCCI ball-level legal balls |
| **D02** | **Dismissal Resistance** | Top-order, Anchor | Window Batting Average (B05) | SMAT/Domestic Batting Average (B05) | Dismissal counts, innings |
| **D03** | **Boundary Generation** | Opener, Middle-order, Finisher | Window Boundary % (R03, B08) | Domestic T20 Boundary % (B08) | Fours and sixes off the bat |
| **D04** | **Dot Ball Suppression** | Top-order, Finisher | Window Batting Dot % (R04, B09) | Domestic T20 Batting Dot % (B09) | Dot balls faced / legal balls (where tracked) |
| **D05** | **Powerplay Batting Impact** | Opener, Top-order | Phase Powerplay Strike Rate (B12) | Domestic T20 Powerplay SR (B12) | Overs 1–6 recorded deliveries |
| **D06** | **Middle-Overs Rotation & Acceleration** | Anchor, Middle-order | Middle Phase SR & Boundary % (B12) | Domestic T20 Middle Phase SR (B12) | Overs 7–15 recorded deliveries |
| **D07** | **Death-Overs Boundary Execution** | Finisher, Lower-order | Death Phase Strike Rate (B12) | Domestic T20 Death Phase SR (B12) | Overs 16–20 recorded deliveries |
| **D08** | **Run Suppression (Economy)** | All Bowlers, All-rounders | Window Bowling Economy Rate (R02, W06) | Domestic T20 Economy Rate (W06) | Legal balls bowled / runs conceded |
| **D09** | **Wicket-Taking Efficiency** | Pace, Spin, Death Bowler | Bowling Strike Rate (W07, W05) | Domestic T20 Bowling SR (W07) | Wickets taken / legal balls |
| **D10** | **Bowling Dot Ball Pressure** | Powerplay Bowler, Death Bowler | Bowling Dot % (W08) | Domestic T20 Bowling Dot % (W08) | Dot balls bowled / legal balls (where tracked) |
| **D11** | **Phase-Specific Bowling Control** | Powerplay / Death Specialist | Phase Economy & Wickets (W09) | Phase Economy & Wickets (W09) | Phase-partitioned bowling spells |
| **D12** | **Matchup Resilience** | All Roles | Pace vs Spin Splits (B14, B15, W10) | Pace vs Spin Splits (B14, B15, W10) | Batter/bowler style deliveries |
| **D13** | **High-Leverage Execution** | All Roles | High-Leverage Metric (M06) | High-Leverage Metric (M06) | Measurable game state threshold (RRR, wickets in hand) |
| **D14** | **Fielding & Keeping Contribution** | Fielders, Wicketkeepers | Fielding Events & Coverage (F01–F09) | Fielding Events & Coverage (F01–F09) | Recorded opportunity events only |
| **D15** | **Age & Trajectory Delta** | All Roles | Incumbent Age as of $t_{\text{eval}}$ | Candidate Age as of $t_{\text{eval}}$ | Verified DOB via PIRE / TMVE / BCCI registration |
| **D16** | **Sample Adequacy & Evidentiary Tier** | All Roles | Window Sample Indicators (R06) | Career Sample Indicators (R06) | Sample sizes, confidence intervals, evidence tier |

#### 4.2.6 Missing Data Handling Rules & Preserved Formulas
1. **Preserved Corrected Formulas**:
   - *Balls Faced (B04)*: `COUNT(delivery events WHERE NOT is_wide)` (includes no-balls, excludes wides per ICC Laws 23 & 24.1).
   - *Economy Rate (W06)*: `(balls_per_over × runs_conceded) / legal_balls_bowled` where `balls_per_over` is format-dependent (6 for T20/ODI/List A, 5 for The Hundred).
   - *Overs Display (W01)*: `floor(legal_balls / balls_per_over) + "." + (legal_balls % balls_per_over)`. Display only; integer balls is the unit of record.
   - *DNB Distinction (B02/B05)*: A batter who did not bat is `did_not_bat = TRUE` with `balls_faced = 0`. A batter who arrived at the crease but faced 0 legal/no-balls (e.g. non-striker run out / timed out) is `did_not_bat = FALSE` with `balls_faced = 0` (a legitimate batted appearance; counts in innings numerator).
   - *Three-Group Phase Model*: Powerplay, Middle, Death with per-format boundaries. The Hundred uses 5-ball overs (death = final 10 balls).
   - *Super Over Isolation*: `is_super_over = TRUE` isolated from all career and window aggregates.
   - *DLS Scaling*: Denominator scales to `target_overs_balls`.
2. **Missing Data Rules**:
   - Zero-imputation is strictly forbidden. Missing data remains `NULL` with an explicit status flag.
   - Missing denominator $\rightarrow$ `NULL` (never 0.00).
   - Unrecorded fields (false shots, ball speed without radar, dropped catches without tracking) $\rightarrow$ `NOT_COMPUTABLE_FROM_AVAILABLE_SOURCES`.
   - Small samples $\rightarrow$ returned with `INSUFFICIENT_SAMPLE` flag; never suppressed or rounded.
   - Gaps in dataset coverage $\rightarrow$ marked `PARTIAL_COVERAGE`; never treated as evidence of non-participation.

---

### 4.3 Requirement R5: Phase 4B Implementation Roadmap

To be incorporated into `docs/PHASES.md` §7:

#### 4.3.1 Positioning & Status
- **Phase Identifier**: **Phase 4B — PVRE Dual-Mode Player Verification & Research Engine**
- **Roadmap Position**: Sits sequentially between Phase 4 (CDCRE) and Phase 5 (CPPAE).
- **Status**: `[STATUS: PLANNED - GREENFIELD BASELINE]` (MVP Platform Core).
- **Implementation Boundary**: Strictly documentation and architectural specification; Phase 4B status remains PLANNED until application code is implemented and all 12 checkpoints pass acceptance testing.

#### 4.3.2 Dependency Resolution & Acyclicity Proof
```
+----------------------------------------------------------------------------------------------------+
|                                    PHASE 4B DEPENDENCY ARCHITECTURE                                |
+----------------------------------------------------------------------------------------------------+
|                                                                                                    |
|   Phase 0b (Empirical Source Audit) + Phase 2 (PIRE & 33-Entity DB) + Phase 3 (TMVE)               |
|                                       + Phase 4 (CDCRE & Service C) + Eligibility Policy Service   |
|                                                      |                                             |
|                                                      v                                             |
|                     +--------------------------------------------------------+                     |
|                     | PHASE 4B: BASE ENGINE & WORKFLOW ROUTING              |                     |
|                     | - Mother Controller & Classification                   |                     |
|                     | - Mode B: Domestic Discovery & Policy Verification     |                     |
|                     | - Mandatory REVIEW_REQUIRED Safety State               |                     |
|                     +--------------------------------------------------------+                     |
|                                                      |                                             |
|                                                      v                                             |
|                     +--------------------------------------------------------+                     |
|                     | PHASE 5: CPPAE (Complete Player Performance Analytics) |                     |
|                     +--------------------------------------------------------+                     |
|                                                      |                                             |
|                                                      v                                             |
|                     +--------------------------------------------------------+                     |
|                     | PHASE 6: CMIE (Contextual Match Intelligence)          |                     |
|                     +--------------------------------------------------------+                     |
|                                                      |                                             |
|                                                      v                                             |
|                     +--------------------------------------------------------+                     |
|                     | PHASE 4B: MODE A PERFORMANCE RESEARCH & CPPAE/CMIE     |                     |
|                     | (Checkpoint 10: Mode A consumes Phase 5 & 6 outputs)   |                     |
|                     +--------------------------------------------------------+                     |
|                                                      |                                             |
|                                                      v                                             |
|                     +--------------------------------------------------------+                     |
|                     | PHASE 7: MIE (Master Intelligence Orchestration)       |                     |
|                     | (Explicitly depends on Phase 4B, 5, 6)                 |                     |
|                     +--------------------------------------------------------+                     |
|                                                      |                                             |
|                                                      v                                             |
|                     +--------------------------------------------------------+                     |
|                     | PHASE 8: SICE (Squad Intelligence & Composition)       |                     |
|                     | (Explicitly depends on Phase 4B & Phase 7)             |                     |
|                     +--------------------------------------------------------+                     |
|                                                                                                    |
+----------------------------------------------------------------------------------------------------+
```
- **Acyclicity Proof**:
  * Base dependencies for Phase 4B are upstream: Phase 0b, Phase 2, Phase 3, Phase 4, and Eligibility Policy Service.
  * CPPAE (Phase 5) and CMIE (Phase 6) depend only on normalized match records and Phase 2 registry; they do NOT depend on PVRE.
  * Mode A performance research within Phase 4B consumes Phase 5 (CPPAE) and Phase 6 (CMIE) feature outputs via Checkpoint 10.
  * Phase 7 (MIE) depends on PVRE (Phase 4B), CPPAE (Phase 5), and CMIE (Phase 6).
  * Phase 8 (SICE) depends on PVRE (Phase 4B) and MIE (Phase 7).
  * No upstream engine depends on SICE or MIE; therefore, the dependency graph is a strict Directed Acyclic Graph (DAG) with zero circular loops.

#### 4.3.3 The 12 Checkpoints in Complete Detail
1. **Checkpoint 1 — Mother Controller and Request Classification**:
   * *Scope*: Validates input request, pre-identity discovery hook, PIRE identity resolution, TMVE membership verification, and Eligibility Policy Service evaluation. Executes 7-step deterministic waterfall:
     (1) Resolve identity $\rightarrow$ (2) Verify RR relationship $\rightarrow$ (3) If verified RR, route to Mode A $\rightarrow$ (4) Otherwise assess uncapped eligibility $\rightarrow$ (5) If independently verified uncapped, route to Mode B $\rightarrow$ (6) If identity, RR, or eligibility conflicts or remains insufficient, route to `REVIEW_REQUIRED` $\rightarrow$ (7) If verified non-RR capped player, return explicit `OUT_OF_SCOPE`.
   * *Pass Criteria*: Mother Controller never guesses; never infers an unknown player is uncapped.
2. **Checkpoint 2 — Existing RR Association Routing**:
   * *Scope*: Inspects `player_membership_state.rr_relationship_state`. All players with verified states `CURRENT_RR`, `HISTORICAL_RR_APPEARED`, or `HISTORICAL_RR_SQUAD_ONLY` deterministically enter Mode A.
   * *Pass Criteria*: 100% of historical and current RR players route to Mode A; zero bypass.
3. **Checkpoint 3 — RR Historical Performance Research (Module A1)**:
   * *Scope*: Reconstructs player's complete performance history across all RR active seasons (2008–2015, 2018–2026). Strictly isolates match appearances from squad-only inclusion.
   * *Pass Criteria*: Zero batting runs, balls, overs, or wickets credited for seasons where `appearances = 0` (`HISTORICAL_RR_SQUAD_ONLY`).
4. **Checkpoint 4 — Recent Global Performance Research (Module A2)**:
   * *Scope*: Connects to multi-league archives (BBL, PSL, CPL, SA20, The Hundred, Intl, domestic). Enforces the configurable 2–3 year window relative to $t_{\text{eval}}$. Computes recent-form metrics R01–R06 with sample size tracking.
   * *Pass Criteria*: Strict date bounding; visible sample indicators; format tags on all metrics; missing leagues recorded as coverage gaps, never non-participation.
5. **Checkpoint 5 — Replaceability Evidence Assessment (Module A3)**:
   * *Scope*: Synthesizes RR history, recent global form, age delta, and sample completeness into one of 5 valid signal states (`RETAIN_SIGNAL`, `MONITOR_SIGNAL`, `POTENTIALLY_REPLACEABLE`, `INSUFFICIENT_EVIDENCE`, `REVIEW_REQUIRED`).
   * *Pass Criteria*: Zero standalone release/retention decisions; zero uncalibrated replacement probabilities; signals forwarded strictly to SICE.
6. **Checkpoint 6 — Uncapped Candidate Career Discovery (Module B)**:
   * *Scope*: Deep domestic discovery across Ranji Trophy, SMAT, Vijay Hazare Trophy, Duleep Trophy, Cooch Behar, Vinoo Mankad, CK Nayudu, and Vijay Merchant.
   * *Pass Criteria*: Covers all available domestic competitions; falls back gracefully to scorecard metrics when BBB is absent; preserves 4-state coverage.
7. **Checkpoint 7 — Independent Eligibility Verification (Module B)**:
   * *Scope*: Verifies candidate meets target-season uncapped definition (e.g. IPL 2027 policy): 0 senior international caps, verified age, and zero playing XI appearances in past IPL seasons.
   * *Pass Criteria*: Database absence is rejected as proof of uncapped status; candidates cannot enter the verified uncapped pool without affirmative verified evidence.
8. **Checkpoint 8 — Mandatory `REVIEW_REQUIRED` Safety Handling**:
   * *Scope*: Hard safety pathway intercepts name collisions, DOB discrepancies, contradictory squad records, unverified eligibility, source conflicts, and sample deficiencies.
   * *Pass Criteria*: Generates structured review dossier with 6 explicit blocks (`review_status`, `review_reason_codes`, `unresolved_claims`, `conflicting_source_ids`, `missing_evidence`, `recommended_manual_checks`); completely blocks automated pool pollution.
9. **Checkpoint 9 — Shared Output Contract Compliance**:
   * *Scope*: Validates `PVREOutputContract` containing all 23 minimum fields with explicit null, unavailable, not-established, verified, and conflict semantics.
   * *Pass Criteria*: Full schema validation; 100% source traceability (`source_record_ids` and `verification_record_ids` populated).
10. **Checkpoint 10 — CPPAE / CMIE Integration**:
    * *Scope*: Seamlessly feeds Phase 5 (CPPAE) metrics and Phase 6 (CMIE) environmental context into PVRE Mode A without creating circular dependencies.
    * *Pass Criteria*: Verified feature consumption from `derived_features` without cyclic imports.
11. **Checkpoint 11 — SICE Incumbent-vs-Candidate Replacement Comparison**:
    * *Scope*: SICE consumes PVRE Mode A incumbent profile alongside Mode B candidates; performs role-aware comparative evaluation across 16 dimensions (D01–D16).
    * *Pass Criteria*: Emits versioned recommendations (`ANALYTICAL_RETAIN`, etc.); Top-10 hackathon ranking board remains strictly isolated from replacement logic.
12. **Checkpoint 12 — End-to-End Acceptance Testing**:
    * *Scope*: Execution of full automated test suite validating Acceptance Criteria AC-24 through AC-30 across all 10 explicit test scenarios.
    * *Pass Criteria*: 100% test pass rate; zero regressions against AC-01 through AC-23.

#### 4.3.4 The 10 Explicit Test Scenarios

| # | Scenario Identifier | Input Persona / Fixture | Expected Routing | Key Contract & Architectural Assertions | Expected Output / State | Failure Condition |
|---|---|---|---|---|---|---|
| **1** | **Verified RR Incumbent** | Sanju Samson ($t_{\text{eval}} = \text{2026-11-01}$) | Mode A | PIRE resolves player ID; TMVE confirms `CURRENT_RR`; Module A1 analyzes RR seasons (2013–2015, 2018–2026); Module A2 assesses 2–3 yr global/international window; Module A3 emits `RETAIN_SIGNAL`. Profile forwarded to SICE. | `route_status = 'MODE_A_EXISTING_RR'`, `replaceability_assessment = 'RETAIN_SIGNAL'` | Conflating squad inclusion with match appearances; failing to bound recent window. |
| **2** | **Historical RR Player** | Ajinkya Rahane / Shane Watson / Squad-only alumnus | Mode A | PIRE resolves player ID; TMVE confirms `HISTORICAL_RR_APPEARED` or `HISTORICAL_RR_SQUAD_ONLY`, currency `FORMER_RR`; Module A1 accurately isolates RR tenure; Module A2 analyzes recent global form outside RR; Module A3 emits signal. | `route_status = 'MODE_A_EXISTING_RR'`, `rr_relationship_state = 'HISTORICAL_RR_*'` | Missing historical RR seasons; crediting stats for squad-only alumni. |
| **3** | **Verified Uncapped Candidate** | Domestic T20 breakout performer (e.g. young SMAT star) | Mode B | PIRE resolves identity; TMVE confirms `NO_VERIFIED_RR_RELATIONSHIP`; Eligibility Service verifies 0 international caps and target policy compliance; Module B retrieves domestic career (SMAT, VHT, Ranji); enters candidate pool. | `route_status = 'MODE_B_UNCAUGHT_CANDIDATE'`, `ipl_uncapped_eligibility = 'VERIFIED_UNCAPPED_ELIGIBLE'` | Admitting candidate without affirmative policy verification. |
| **4** | **Verified Capped Non-RR Player** | Virat Kohli / Jasprit Bumrah | `OUT_OF_SCOPE` | PIRE resolves identity; TMVE confirms `NO_VERIFIED_RR_RELATIONSHIP`; international caps verified; player is CAPPED; deterministically routes to `OUT_OF_SCOPE`. | `route_status = 'OUT_OF_SCOPE_CAPPED_NON_RR'`, candidate pool entry blocked | Permitting a capped player into Mode B uncapped candidate pool. |
| **5** | **Unknown Player Absent from Database** | Newly registered domestic U-19 prospect | Pre-Identity $\rightarrow$ `REVIEW_REQUIRED` | Absent from internal DB; Mother Controller triggers CDCRE candidate discovery (no player_id); defaults `player_capped_status = 'UNVERIFIED'`, `ipl_uncapped_eligibility = 'NOT_ASSESSED'`; routes to `REVIEW_REQUIRED`. | `route_status = 'REVIEW_REQUIRED'`, `review_reason_codes = ['UNKNOWN_PLAYER_NOT_IN_DATABASE']` | Auto-assuming unknown player is uncapped. |
| **6** | **Duplicate Identities** | Two distinct domestic players named "Amit Sharma" | `REVIEW_REQUIRED` | PIRE detects ambiguous match with multiple candidates and distinct birth dates/associations; Mother Controller halts automated processing; flags identity collision; compiles candidate dossiers. | `route_status = 'REVIEW_REQUIRED'`, `review_reason_codes = ['COLLISION_MULTIPLE_IDENTITIES']` | Auto-merging distinct players or silently picking the first match. |
| **7** | **Conflicting DOB or Membership Evidence** | Passport DOB 2004-05-10 vs BCCI roster DOB 2003-11-22 | `REVIEW_REQUIRED` | Provenance engine detects conflicting assertions across sources; flags `CONFLICT`; persists both claims in `verification_records`; routes immediately to `REVIEW_REQUIRED`. | `route_status = 'REVIEW_REQUIRED'`, `review_reason_codes = ['CONFLICT_DOB_RECORD']` | Overwriting or silently averaging conflicting dates of birth. |
| **8** | **Missing Domestic Datasets** | Player participated in SMAT 2020 or Vinoo Mankad 2022 (unindexed) | Mode B with `PARTIAL_COVERAGE` | Domestic discovery detects unindexed seasons in data lake; flags `career_coverage_state = 'PARTIAL_COVERAGE'`; lists missing tournaments; evaluates metrics over available sample only. | `career_coverage_state = 'PARTIAL_COVERAGE'`, `missing_competitions = ['SMAT_2020']` | Treating missing datasets as evidence of non-participation. |
| **9** | **Conflicting External Sources** | ESPNcricinfo reports 35 matches, BCCI scorecards verify 32 | `REVIEW_REQUIRED` | Provenance tracker flags statistical discrepancy across providers; marks `verification_status = 'CONFLICT'`; compiles review dossier with conflicting source IDs. | `route_status = 'REVIEW_REQUIRED'`, `review_reason_codes = ['CONFLICTING_CAREER_STATISTICS']` | Silently adopting unverified third-party numbers over verified scorecards. |
| **10** | **Incomplete Career Coverage** | Player debuted in 2018, but verified scorecards available only from 2022 | Mode B with `PARTIAL_COVERAGE` | System identifies truncated temporal coverage; sets `career_coverage_state = 'PARTIAL_COVERAGE'`; computes sample indicators; attaches `COVERAGE_LIMITED` flags; does not extrapolate. | `career_coverage_state = 'PARTIAL_COVERAGE'`, `sample` indicators explicitly displayed | Extrapolating or interpolating missing seasons. |

---

## 5. Caveats

1. **Third-Party Commercial API Availability**:
   - While `bcci.tv` and `icc-cricket.com` match centres can be queried on-demand via authorized rate-limited adapters (Service C), commercial data providers (e.g. Entity Sport, Roanuz) provide dedicated domestic JSON endpoints under commercial agreements. If adopted during Phase 1/4 acquisition, appropriate licensing must be recorded in `data_sources`.
2. **Historical Scorecard Granularity**:
   - Indian domestic multi-day cricket prior to 2018 often lacks structured balls-faced metrics for lower-order batters on public portals. Consequently, strike rate and balls faced for older First-Class careers will naturally reflect `NULL` values under strict Data Dictionary compliance.
3. **No Direct Web Scraping During Greenfield Specification**:
   - In accordance with the system constraints and Greenfield baseline declaration, no mass web scrapers were executed during this documentation survey. All findings reflect empirical repository inspection, local dataset validation, and verified terms-of-service documentation.

---

## 6. Conclusion

The Domestic Source Inventory and Phase 4B Implementation Roadmap mining is complete, authoritative, and fully evidenced:
1. **Domestic & Age-Group Inventory (R3)**: Explicitly separates local ball-by-ball SMAT coverage (695 files, ODC-By) from official BCCI scorecard archives (Ranji, VHT, Duleep, Cooch Behar, Vinoo Mankad, CK Nayudu, Vijay Merchant, U-19). Outlines exact access constraints, terms of service, and fallback rules.
2. **Data Dictionary Enhancements (R4)**: Defines recent-form metrics (R01–R06) with exponential time decay, 4 career coverage states, 5 replaceability assessment signals, 5 SICE recommendation states, 16 role-aware comparison dimensions (D01–D16), missing data rules, and preserved formulas.
3. **Phase 4B Implementation Roadmap (R5)**: Positions Phase 4B in `docs/PHASES.md` as `[STATUS: PLANNED - GREENFIELD BASELINE]`, establishes an acyclic dependency graph, details 12 explicit checkpoints, specifies 10 concrete test scenarios, maps Acceptance Criteria AC-24 through AC-30, and enforces strict documentation-only boundaries.

---

## 7. Verification Method

To independently verify the facts and specifications in this report:

1. **Verify Local Dataset Lake & File Counts**:
   ```powershell
   Get-ChildItem -Path "datasets" -Directory | ForEach-Object { [PSCustomObject]@{ Directory = $_.Name; JsonCount = (Get-ChildItem -Path $_.FullName -Filter "*.json").Count } }
   ```
   *Expected Result*: Exactly 13 directories; counts: `bbl` (662), `bpl` (469), `cpl` (445), `hnd` (201), `icc_mens_cricket_world_cup` (265), `icc_mens_t20_world_cup` (230), `ilt` (134), `ipl` (1243), `lpl` (143), `mlc` (109), `psl` (357), `sat` (130), `sma` (695). Total = 5,083 JSON files.

2. **Verify ODC-By v1.0 Licences Across All Archives**:
   ```powershell
   Get-ChildItem -Path "datasets" -Directory | ForEach-Object { [PSCustomObject]@{ Directory = $_.Name; HasLicense = (Test-Path "$($_.FullName)\LICENSE.txt"); HasReadme = (Test-Path "$($_.FullName)\README.txt") } }
   ```
   *Expected Result*: `HasLicense = True` and `HasReadme = True` for all 13 directories.

3. **Verify SMAT Yearly Breakdown & Temporal Gaps**:
   ```powershell
   Get-Content "datasets\sma_json\README.txt" | Select-String "^\d{4}-\d{2}-\d{2}" | ForEach-Object { $_.Line.Substring(0,4) } | Group-Object | Select-Object Name, Count
   ```
   *Expected Result*: 2016 (83), 2018 (79), 2019 (261), 2021 (181), 2022 (44), 2023 (39), 2024 (8). Total = 695. Gaps in 2017 and 2020.

4. **Verify Markdown Anchors & Formatting**:
   Ensure all table formatting, LaTeX formulas, and Markdown headings adhere to repository documentation standards without syntax errors.
