# Historical CricSheet Data Quality & Coverage Baseline Report

**Document Identifier**: `RR-PHASE1-HISTORICAL-DQ-BASELINE-V1`  
**System**: Rajasthan Royals Squad Intelligence Platform · IPL 2027 Campaign  
**Date Generated**: 2026-11-13T08:06:16.691670+00:00  
**Status**: `[STATUS: VERIFIED HISTORICAL DATA QUALITY BASELINE - GATE 1 CLOSURE]`  
**Scope**: Multi-League CricSheet Data Lake (13 White-Ball Leagues, 5,083 Historical Fixtures)  

---

## 1. Executive Summary & Verification Verdict

This report provides the empirical, bitwise, and relational data quality baseline for the historical cricket data lake, completing **Phase 1 Historical Data Pipeline Closure (Track A)**.

- **Total Leagues Audited**: 13 competitive tournaments (`ipl_male_json`, `bbl_male_json`, `sma_json`, `cpl_male_json`, `psl_male_json`, `bpl_male_json`, `icc_mens_cricket_world_cup_male_json`, `icc_mens_t20_world_cup_male_json`, `hnd_male_json`, `lpl_male_json`, `ilt_male_json`, `sat_male_json`, `mlc_male_json`).
- **Total Matches Audited**: 520 matches sampled across all 13 leagues.
- **Delivery-to-Innings Reconciliation Rate**: **100.0%** (520 / 520 matches fully reconciled).
- **Total Innings Reconciled**: 1,043 / 1,043.
- **Total Granular Deliveries Audited**: 131,309 discrete ball events.
- **Unique Player Registrations**: 1,523 cricketers identified with 1,523 verified 8-character hex CricSheet people hashes.
- **Special Circumstances**: 14 Duckworth-Lewis-Stern rain-affected matches; 6 super over tiebreakers isolated.

---

## 2. League-by-League Data Quality & Reconciliation Matrix

| League Directory | Total Files in Lake | Audited Sample | Reconciled Matches | Reconciliation Rate | Audited Deliveries | DLS Matches | Super Overs |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `ipl_male_json` | 1243 | 40 | 40 | 100.0% | 9,476 | 0 | 1 |
| `bbl_male_json` | 662 | 40 | 40 | 100.0% | 9,477 | 1 | 1 |
| `sma_json` | 695 | 40 | 40 | 100.0% | 9,331 | 0 | 1 |
| `bpl_male_json` | 469 | 40 | 40 | 100.0% | 9,475 | 0 | 0 |
| `cpl_male_json` | 445 | 40 | 40 | 100.0% | 9,178 | 4 | 0 |
| `psl_male_json` | 357 | 40 | 40 | 100.0% | 9,168 | 2 | 1 |
| `icc_mens_cricket_world_cup_male_json` | 265 | 40 | 40 | 100.0% | 22,166 | 1 | 1 |
| `icc_mens_t20_world_cup_male_json` | 230 | 40 | 40 | 100.0% | 9,023 | 0 | 0 |
| `hnd_male_json` | 201 | 40 | 40 | 100.0% | 7,770 | 0 | 0 |
| `lpl_male_json` | 143 | 40 | 40 | 100.0% | 8,711 | 3 | 1 |
| `ilt_male_json` | 134 | 40 | 40 | 100.0% | 9,219 | 0 | 0 |
| `sat_male_json` | 130 | 40 | 40 | 100.0% | 9,113 | 1 | 0 |
| `mlc_male_json` | 109 | 40 | 40 | 100.0% | 9,202 | 2 | 0 |

---

## 3. Cricket Semantic Invariant Verification

Every audited delivery event and innings was validated against the non-negotiable cricket rules:
1. **Runs Consistency**: $\text{runs\_total} = \text{runs\_batter} + \text{runs\_extras}$ strictly validated across 100% of delivery events.
2. **Bowler Credited Wickets**: Discriminates dismissals into bowler-credited (`bowled`, `caught`, `caught and bowled`, `lbw`, `stumped`, `hit wicket`) vs non-bowler-credited (`run out`, `retired hurt`, `obstructing the field`).
3. **Dismissal Distribution Observed**:
   - **Caught**: 4,014 dismissals
   - **Bowled**: 1,174 dismissals
   - **Run Out**: 467 dismissals
   - **Lbw**: 463 dismissals
   - **Caught And Bowled**: 207 dismissals
   - **Stumped**: 151 dismissals
   - **Hit Wicket**: 11 dismissals
   - **Retired Hurt**: 10 dismissals
   - **Retired Out**: 2 dismissals

4. **Extras Breakdown**:
   - **Wides**: 4,897 runs
   - **Legbyes**: 2,458 runs
   - **Byes**: 769 runs
   - **Noballs**: 583 runs

---

## 4. Phase 1A Contract Compatibility Audit

- `src.contracts.match.Match`: 100% compliant with strict toss validation, home/away uniqueness, and date formatting.
- `src.contracts.match.Innings`: 100% compliant with integer ball count allocations and super-over flags.
- `src.contracts.match.Delivery`: 100% compliant with partition key `season_year`, non-negative run checks, and match-phase derivation.

---

## 5. Phase 1 Gate Closure Conclusion

**Prerequisite Status**: **ALL TRACK A HISTORICAL PREREQUISITES IMPLEMENTED & AUDITED**.
1. CricSheet JSON v1.3.0 parser is fully operational in `src/ingestion/cricsheet_parser.py`.
2. SHA-256 manifests covering all 5,083 files are generated in `data/manifests/cricsheet_sha256_manifest.json`.
3. Immutable staging and quarantine pipelines are operational in `src/ingestion/staging.py`.
4. Scorecard and delivery reconciliation is operational in `src/quality/reconciliation.py`.
5. Phase 1 remains marked **PARTIALLY COMPLETE** in platform status until the final unified database migrations (Track B) are integrated.