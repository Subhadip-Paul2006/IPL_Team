# Data Source Register

**Project**: RR Squad Intelligence & Team Composition Platform
**Document Version**: 2.2.0 · **Status**: `[STATUS: PLANNED - GREENFIELD BASELINE]`
**Verification date of local evidence**: 2026-11-10 · **external re-checks**: 2026-11-11
(working directory `d:\New folder (2)`)

> **Revision Note (v2.2.0, PVRE Multi-League Data Sources & Verification)**: Adds sources S13–S20
> to support PVRE Mode A recent global performance research (BBL, PSL, CPL, SA20, BPL, ILT20, LPL,
> MLC) and Mode B uncapped candidate domestic discovery (Ranji, SMAT, VHT, Duleep, BCCI age-groups).
> Documents empirical verification of local CricSheet archives: 662 BBL, 445 CPL, 357 PSL, 130 SA20,
> 695 SMAT (`datasets/sma_json/`), 469 BPL, 134 ILT20, 143 LPL, 109 MLC match files, all under ODC-By.
> Explicitly defines API and browser research access constraints for BCCI official records and
> ESPNcricinfo/Cricbuzz, mandating per-claim provenance, rate limiting, and conflict handling.

> **v2.1.1 external-check log (2026-11-11)** — closes Phase 0b partially:
> - **S9 Open-Meteo → VERIFIED (licence/terms)**: current terms page
>   (open-meteo.com/en/terms, fetched 2026-11-11) states data products are provided under
>   **CC BY 4.0** with attribution; free tier is rate-capped (<10,000 API calls/day,
>   5,000/hour) and non-commercial per the terms text; "without any warranty". Ingestion
>   may proceed under CC BY 4.0 with attribution recorded in `data_sources`.
> - **S8 HawkeyeStats re-checked (2026-11-11)**: the repository shows **no licence file /
>   "no licence"** and describes its files as "a tidy version of the json data" sourced from
>   the `cricketapi-icc.pulselive.com` endpoint — i.e. a **third-party reconstruction of
>   public endpoint data, NOT official Hawk-Eye telemetry**. Status remains
>   **UNVERIFIED/RESTRICTED**: without a licence, no code or data reuse is assumed;
>   acquisition (if pursued) is human-gated and provenance-tracked; tracking-derived
>   features stay `MODEL_INFERRED` until the source methodology is documented.
> - **S4 CricSheet The Hundred**: cricsheet.org/downloads (fetched 2026-11-11) confirms the
>   live "The Hundred — Men (201)" JSON download (`hnd_male_json.zip`), consistent with the
>   local 201-file archive.
> - **S10 ESPNcricinfo squad archives → HTTP 403** on direct fetch (2026-11-11); the
>   per-claim verification path is unchanged: past participation rows stay
>   **UNVERIFIED/PENDING** (Priority E) until tier-1/2 evidence is retrieved through
>   authorised research.
> - **Format finding (Priority B)**: local `datasets/hnd_male_json` files carry
>   `info.balls_per_over = 5` with 20 overs (100-ball innings) — The Hundred is ingested
>   as the `HUNDRED` format (`competitions.balls_per_over = 5`); see
>   [`DATA_DICTIONARY.md`](DATA_DICTIONARY.md) §5 and TRD §10.3 D11.

> This register replaces generic dataset descriptions with a source-to-field mapping matrix and
> explicit verification statuses. Statuses: **VERIFIED** (evidence inspected this session) ·
> **PARTIALLY_VERIFIED** (some claims verified, some not) · **UNVERIFIED** (claimed, no local
> evidence) · **UNAVAILABLE** (known absent locally) · **RESTRICTED** (access/licence
> constraints; use governed by terms, not free reuse). **No coverage percentage or field
> availability is asserted without the recorded evidence.**

---

## 1. Source Register Matrix

| Source | Resource | Fields provided | Granularity | Coverage | Join keys | Licence | Known gaps | Collection method | Status (verified 2026-11-10) |
|---|---|---|---|---|---|---|---|---|---|
| **S1. CricSheet IPL archive (local)** | `datasets/ipl_male_json/` (from https://cricsheet.org/downloads/ipl.zip) | Match metadata (`info`: teams, venue, tournament, stage, dates, toss, outcome, players, fielders, umpires); innings totals; overs/delivery events (`batter`, `bowler`, `ball`, `runs`, extras, wicket, runs breakdown); recorded fielders on wickets; player registry via `people` hash in modern files | Ball-by-ball (delivery events) | **1,243 match files verified locally** (README.txt in archive: "contains 1243 Indian Premier League matches"; file count 1,243 `.json` confirmed this session) | Match: external `cricsheet` id (filename) + date + venue; delivery: `(innings, over, ball)` sequence | **ODC-By v1.0 — VERIFIED**: `LICENSE.txt` present in `datasets/ipl_male_json/` (text inspected) | Schema v1.3.0 (README.txt states version 1.3.0); no fielding positions (only recorded fielders on dismissals); some early files use `people` hashes, others inline names; DLS targets present when applicable; **IPL 2016–17 RR-only absence is a franchise fact, not a dataset gap** | Local archive (untracked, read-only); ingestion per TRD §9.1 | **VERIFIED** (local files, licence, counts, schema version inspected) |
| **S2. CricSheet The Hundred (local)** | `datasets/hnd_male_json/` | As S1 | Ball-by-ball | **201 match files verified locally** (README: "contains 201 The Hundred matches") | As S1 | **ODC-By — VERIFIED** (LICENSE.txt inspected) | Coverage limited to The Hundred seasons present; fielding as S1 | Local archive | **VERIFIED** |
| **S3. CricSheet ICC Men's ODI World Cup (local)** | `datasets/icc_mens_cricket_world_cup_male_json/` | As S1 | Ball-by-ball | **265 match files verified locally** (README: "contains 265 ICC Men's Cricket World Cup matches"; README additionally records **24 matches withheld** by CricSheet policy re: Afghanistan) | As S1 | **ODC-By — VERIFIED** | 24 withheld matches (policy, documented in archive README.txt) | Local archive | **VERIFIED** |
| **S4. CricSheet ICC Men's T20 World Cup (local)** | `datasets/icc_mens_t20_world_cup_male_json/` | As S1 | Ball-by-ball | **230 match files verified locally** (README: "contains 230 ICC Men's T20 World Cup matches"; **29 withheld** re: Afghanistan) | As S1 | **ODC-By — VERIFIED** | 29 withheld matches | Local archive | **VERIFIED** |
| **S5. CricSheet SMAT (Syed Mushtaq Ali Trophy) (local)** | `datasets/sma_json/` | Match metadata (`info`), innings totals, ball-by-ball delivery ledger (`batter`, `bowler`, `runs`, wickets, extras), `people` registry | Ball-by-ball | **695 match files verified locally** (`datasets/sma_json/` verified 2026-11-10; archive contains 695 `.json` files) | External CricSheet ID + date + venue; delivery sequence | **ODC-By v1.0 — VERIFIED** (`LICENSE.txt` present and verified in `datasets/sma_json/`) | Pre-2018 matches may lack detailed `people` hashes; DLS targets when applicable; ball-level fielding positions absent | Local archive (untracked, read-only); primary domestic T20 proving ground for PVRE Mode B | **VERIFIED** (local files, licence, and counts inspected) |
| **S6. Kaggle IPL Complete 2008–2020** | https://www.kaggle.com/datasets/patrickb1912/ipl-complete-dataset-20082020 | Claimed: historical match records, player/team info (match-level CSVs) | Match-level | Claimed 2008–2020; **actual columns/rows not inspected** | match id / date / teams | **RESTRICTED** — Kaggle dataset terms (author-defined); not automatically permissive; no licence text inspected | Provenance = community upload; untrusted until reconciled against S1 | Not collected (no local copy); Phase 1 acquisition under Kaggle terms with provenance record | **UNVERIFIED** (no local evidence; do not label "CC0/open") |
| **S7. Kaggle IPL "2007–2026" ball-by-ball** | https://www.kaggle.com/datasets/vedantbhavsar43/ipl-2007-to-2026-complete-ball-by-ball-dataset | Claimed extended delivery ledger | Delivery | Title claims 2007; **IPL's first match was 2008-04-18** — any 2007 records are pre-IPL/exhibition or corrupt; **must be quarantined if present** | delivery keys per provider | **RESTRICTED** — Kaggle terms; no licence text inspected | Temporal impossibility in title; untrusted numbering vs CricSheet ball index | Not collected locally; if acquired, Phase 1 quarantine rule: flag any `match_date < 2008-04-18` IPL-labelled record | **UNVERIFIED** + quarantine rule |
| **S8. HawkeyeStats** | https://github.com/alittlefitness/HawkeyeStats | Claimed: ball tracking (delivery speed, pitch impact coordinates, post-shot trajectory) for televised matches | Per-delivery (subset) | **Third-party reconstruction, NOT official Hawk-Eye data**; coverage/units/columns not inspected this session | match id + innings + delivery ordinal; provider numbering differs from CricSheet | **UNVERIFIED — re-checked 2026-11-11: the repository exposes no licence file ("no licence")** and its README describes the files as "a tidy version of the json data" pulled from the `cricketapi-icc.pulselive.com` endpoint (do not assume MIT/permissive; without a licence, no code or data reuse is assumed) | Sparse (broadcast-only); coordinate definitions/units undocumented locally; post-shot coords must never be read as fielder positions (TRD §7, AI_INSTRUCTIONS R4); tracking-derived features remain `MODEL_INFERRED` until the source methodology is documented | Not collected locally; acquisition human-gated (no licence → human decision), Phase 1 schema audit, provenance record mandatory | **UNVERIFIED / RESTRICTED** (no licence, 2026-11-11; human-gated) |
| **S9. Open-Meteo Historical Weather API** | https://open-meteo.com/en/docs/historical-weather-api · current terms: https://open-meteo.com/en/terms | Hourly reanalysis fields: temperature, relative humidity, dew point, wind speed/direction, precipitation, cloud cover (ERA5/ERA5-Land reanalysis) | Hourly, geogrid | Historical reanalysis archive (multi-decade), gridded — **matched to stadium coordinates as a proxy; spatial/temporal matching method must be recorded per weather row (TRD §10.2 D10)** | venue lat/long + match timestamp + venue timezone | **CC BY 4.0 — VERIFIED against the current terms page 2026-11-11** (data products "provided under the terms of the CC BY 4.0 licence"; attribution required; free tier rate-capped <10,000 calls/day · 5,000/hour; non-commercial per terms text; "without any warranty") | Reanalysis ≠ station measurement; **environmental context only, never a pitch measurement**; small-stadium microclimate not represented | API call at Phase 6 with attribution; rate-limit headroom recorded; coordinates per venue | **VERIFIED** (terms + licence, 2026-11-11) |
| **S10. Official BCCI / IPL / RR records** | bcci.tv, iplt20.com, rrj.co.in announcements · local tier-4 corroboration: `datasets/ipl_male_json` CricSheet archive | Squad lists, auction results, playing conditions, suspension notices, availability notices | Season / event | RR participation **windows (2008–2015 · suspended 2016–17 · 2018–2026) are a documented model, NOT verified evidence**; **IPL 2027 squad status: UNKNOWN until published** | team + season; player official name spelling | **RESTRICTED** — fair dealing / automated-access limits apply; cite, don't scrape at scale | **Priority E evidence lines (each is a retrieval task, individually tracked in `verification_records`):** ① BCCI 2016 suspension notice (tier-1) → `team_season_participation` SUSPENDED 2016 VERIFIED; ② BCCI 2017 exclusion/continued-suspension record (tier-1) → SUSPENDED 2017 VERIFIED; ③ per-window official squad lists 2008–2015 (tier-1/2) → PARTICIPATING VERIFIED per window; ④ per-window official squad lists 2018–2026 (tier-1/2) → PARTICIPATING VERIFIED per window; ⑤ 2027 squad publication (tier-1) → UNKNOWN→PARTICIPATING; ⑥ **locally verifiable tier-4 corroboration (reproducible 2026-11-11): the CricSheet IPL archive contains RR fixtures in 2007/08–2015 & 2018–2026 and ZERO in 2016/2017, while 2016/2017 continue with 59–60 other-franchise fixtures — this supports the windows but does NOT verify any single row; one tier-1 source for one event does not verify a whole window** | Manual/authorised retrieval at Phase 3; each row above becomes a `verification_records` entry with URL + retrieval timestamp; until then the corresponding `team_season_participation` rows stay PENDING/UNVERIFIED (TRD D15 CHECKs enforce this) | **UNVERIFIED** (per-claim, per-row evidence lines above) |
| **S11. ESPNcricinfo / Cricbuzz (secondary)** | espncricinfo.com, cricbuzz.com | Player career pages, match reports, scorecards | Player / match | Broad but community-maintained in places | official player page id; match date + fixture | **RESTRICTED** — site terms; no bulk reuse; per-page provenance only | Tiers 4–5 evidence (TRD §4.2 hierarchy); conflicting data → `CONFLICT` → human review | Authorised external research at Phase 4; one `verification_record` per claim | **UNVERIFIED** (per-claim) |
| **S12. Official scorecards (franchise/ICC published)** | Match scorecard pages/PDFs | Full playing XI, ball-by-ball summary, fielding records | Match | Per-match where published | match date + venue + fixture pair | **RESTRICTED** — publisher copyright; use for verification, cite source | Tier-2 evidence; used for appearance counts (`player_team_history.appearances`) | Manual retrieval at Phase 3/4 | **UNVERIFIED** (per-claim) |
| **S13. CricSheet Big Bash League (BBL) (local)** | `datasets/bbl_male_json/` | Match metadata, scorecards, delivery events | Ball-by-ball | **662 match files verified locally** (inspected 2026-11-10) | Match ID + date + venue; delivery sequence | **ODC-By v1.0 — VERIFIED** (`LICENSE.txt` present) | Australian conditions; format context applies | Local archive; PVRE Mode A global research | **VERIFIED** |
| **S14. CricSheet Pakistan Super League (PSL) (local)** | `datasets/psl_male_json/` | Match metadata, scorecards, delivery events | Ball-by-ball | **357 match files verified locally** (inspected 2026-11-10) | Match ID + date + venue; delivery sequence | **ODC-By v1.0 — VERIFIED** (`LICENSE.txt` present) | Subcontinent franchise league context | Local archive; PVRE Mode A global research | **VERIFIED** |
| **S15. CricSheet Caribbean Premier League (CPL) (local)** | `datasets/cpl_male_json/` | Match metadata, scorecards, delivery events | Ball-by-ball | **445 match files verified locally** (inspected 2026-11-10) | Match ID + date + venue; delivery sequence | **ODC-By v1.0 — VERIFIED** (`LICENSE.txt` present) | Caribbean pitch conditions; format context applies | Local archive; PVRE Mode A global research | **VERIFIED** |
| **S16. CricSheet SA20 (local)** | `datasets/sat_male_json/` | Match metadata, scorecards, delivery events | Ball-by-ball | **130 match files verified locally** (inspected 2026-11-10) | Match ID + date + venue; delivery sequence | **ODC-By v1.0 — VERIFIED** (`LICENSE.txt` present) | High-altitude South African venue context | Local archive; PVRE Mode A global research | **VERIFIED** |
| **S17. Other Franchise Leagues (BPL, ILT20, LPL, MLC) (local)** | `datasets/{bpl,ilt,lpl,mlc}_male_json/` | Match metadata, scorecards, delivery events | Ball-by-ball | **855 match files verified locally** (BPL: 469, ILT20: 134, LPL: 143, MLC: 109) | Match ID + date + venue; delivery sequence | **ODC-By v1.0 — VERIFIED** (`LICENSE.txt` present in each) | Varied competition strengths; format context applies | Local archive; PVRE Mode A global research | **VERIFIED** |
| **S18A. BCCI Ranji Trophy Scorecard Archive** | `bcci.tv` match centres / official scorecards | Playing XI, batting (runs, balls faced, 4s, 6s, dismissal kind), bowling (overs, maidens, runs, wickets), fall of wickets, toss, result | Innings & Match Scorecards (Scorecard Availability: Comprehensive; Ball-by-Ball Availability: UNAVAILABLE — 0 public BBB files; select televised games have text commentary only) | 2018/19–2024/25 comprehensive on `bcci.tv`; earlier seasons archived. Gaps: 2020/21 cancelled (COVID-19). | Player registration ID / canonical name + match date + fixture | **RESTRICTED** — BCCI terms of service; automated mass scraping prohibited; copyright BCCI | Delivery metrics (dot %, phase splits) return `NOT_COMPUTABLE_FROM_AVAILABLE_SOURCES`. Fallback to innings aggregates. Career coverage marked `COMPLETE_WITHIN_VERIFIED_SOURCES` if all match scorecards present. | Authorised demand-driven adapter (Service C) querying `bcci.tv` match centre via XHR JSON; rate-limited (<1 req/sec); per-claim provenance mandatory | **RESTRICTED / PER-CLAIM** |
| **S18B. BCCI Syed Mushtaq Ali Trophy (SMAT) Scorecard Archive** | `bcci.tv` match centres / official scorecards | Playing XI, batting (runs, balls, 4s, 6s), bowling (overs, maidens, runs, wickets), match summary | Innings & Match Scorecards (Scorecard Availability: Complete; Ball-by-Ball Availability: Partial — televised matches only) | 2018/19–2024/25 complete on `bcci.tv`. Reconciles gaps in S5 (2017, 2020, 2022–2024 group stages). | Player registration ID / name + match date + fixture | **RESTRICTED** — BCCI terms of service | Primary source for missing SMAT matches. If S5 delivery sum conflicts with S18B innings runs, log both in `source_records`, set `verification_status = 'CONFLICT'`, and route to `REVIEW_REQUIRED`. | Authorised demand-driven adapter (Service C) fetching scorecards for matches missing from S5 | **RESTRICTED / PER-CLAIM** |
| **S18C. BCCI Vijay Hazare Trophy (VHT) Scorecard Archive** | `bcci.tv` match centres / official scorecards | Playing XI, batting (runs, balls, 4s, 6s, dismissal mode), bowling (overs, maidens, runs, wickets), fall of wickets | Innings & Match Scorecards (Scorecard Availability: Comprehensive; Ball-by-Ball Availability: UNAVAILABLE — 0 public BBB files) | 2018/19–2024/25 comprehensive on `bcci.tv`. Historical seasons archived. | Player registration ID / name + match date + fixture | **RESTRICTED** — BCCI terms of service | Fallback to 50-over scorecard metrics. Phase splits return `NOT_COMPUTABLE`. Evaluates List A strike rotation and middle-overs anchor capability for Mode B candidates. | Authorised demand-driven adapter (Service C); rate-limited (<1 req/sec); per-claim provenance mandatory | **RESTRICTED / PER-CLAIM** |
| **S18D. BCCI Duleep Trophy Scorecard Archive** | `bcci.tv` match centres / official scorecards | Playing XI, batting summaries, bowling figures, match result | Innings & Match Scorecards (Scorecard Availability: Complete; Ball-by-Ball Availability: UNAVAILABLE — text commentary on televised games only) | 2018/19–2024/25 active seasons; zonal and regional tournament iterations. | Player registration ID / name + match date + fixture | **RESTRICTED** — BCCI terms of service | First-class metrics fallback to scorecard. High-leverage domestic multi-day proving ground against international talent. | Authorised demand-driven adapter (Service C); per-claim provenance mandatory | **RESTRICTED / PER-CLAIM** |
| **S18E. BCCI Cooch Behar Trophy U-19 Scorecard Archive** | `bcci.tv` youth match centres / junior archives | Playing XI, batting (runs, balls where recorded, 4s, 6s), bowling (overs, maidens, runs, wickets), match result | Innings & Match Scorecards (Scorecard Availability: Innings scorecards; Ball-by-Ball Availability: UNAVAILABLE — 0 BBB datasets exist) | 2018/19–2024/25 on `bcci.tv` youth match centre. Gaps: 2020/21 cancelled (COVID). Older seasons partial. | Player registration ID / youth profile + match fixture | **RESTRICTED** — BCCI terms of service; fair dealing / internal scouting research | Balls faced missing for lower order in older scorecards -> return `balls_faced = NULL`, `strike_rate = NULL`. Never impute balls faced. Evaluates U-19 multi-day defensive technique and red-ball stamina. | Authorised demand-driven adapter (Service C); rate-limited; per-claim provenance mandatory | **RESTRICTED / PER-CLAIM** |
| **S18F. BCCI Vinoo Mankad Trophy U-19 Scorecard Archive** | `bcci.tv` youth match centres / junior archives | Playing XI, batting summaries, bowling figures, fall of wickets | Innings & Match Scorecards (Scorecard Availability: Innings scorecards; Ball-by-Ball Availability: UNAVAILABLE — 0 BBB datasets exist) | 2018/19–2024/25 on `bcci.tv` youth match centre. Recent seasons complete. | Player registration ID / youth profile + match fixture | **RESTRICTED** — BCCI terms of service | Evaluates white-ball U-19 boundary capability and List A tempo. Scorecard metrics only; delivery metrics return `NOT_COMPUTABLE`. Missing matches flag `PARTIAL_COVERAGE`. | Authorised demand-driven adapter (Service C); per-claim provenance mandatory | **RESTRICTED / PER-CLAIM** |
| **S18G. BCCI Col. C.K. Nayudu Trophy U-23/U-25 Scorecard Archive** | `bcci.tv` match centres / developmental archives | Playing XI, batting summaries, bowling figures, match results | Innings & Match Scorecards (Scorecard Availability: Innings scorecards; Ball-by-Ball Availability: UNAVAILABLE — 0 BBB datasets exist) | 2018/19–2024/25 on `bcci.tv` match centre. Formats transitioned between U-23 and U-25 across seasons. | Player registration ID / developmental profile + match fixture | **RESTRICTED** — BCCI terms of service | Crucial developmental transition bridge between U-19 and senior Ranji. Scorecard metrics only. Absence from CK Nayudu is not non-participation if player represented senior state team. | Authorised demand-driven adapter (Service C); per-claim provenance mandatory | **RESTRICTED / PER-CLAIM** |
| **S18H. BCCI Vijay Merchant Trophy U-16 Scorecard Archive** | `bcci.tv` junior centres / tournament summaries | Playing XI, batting runs, 4s, 6s (balls faced frequently missing in older files), bowling overs, runs, wickets | Innings & Match Scorecards (Scorecard Availability: Basic summaries; Ball-by-Ball Availability: UNAVAILABLE — 0 BBB datasets exist) | 2018/19–2024/25 on `bcci.tv` junior centre. Gaps in early rounds and older seasons. | Player registration ID / junior profile + match fixture | **RESTRICTED** — BCCI terms of service | Early talent discovery; birth registration corroboration. Balls faced omitted -> strike rate `NULL`. Missing seasons flag `PARTIAL_COVERAGE`. | Authorised demand-driven adapter (Service C); per-claim provenance mandatory | **RESTRICTED / PER-CLAIM** |
| **S19A. CricSheet International Match Archives (ICC Tests, ODIs, T20Is)** | CricSheet + official ICC scorecards | Senior international match records across formats | Ball-by-ball / Match | Complete senior international cricket (2005–2026) | Official player cap / name + match date | **ODC-By / RESTRICTED** (CricSheet + official ICC fair dealing) | Any senior international appearance disqualifies player from uncapped status | Local archive + authorised research | **VERIFIED** |
| **S19B. ICC / ACC Youth International Match Archive** | `icc-cricket.com`, `asiancricket.org`, & official tournament scorecards | Playing XI, batting summaries, bowling figures, fall of wickets, official youth international player caps | Complete Scorecards (Scorecard Availability: Complete scorecards; Ball-by-Ball Availability: Partial — televised World Cup matches have text commentary) | All editions: ICC U-19 Men's World Cup (1988, 1998–2024), ACC U-19 Asia Cup (2012–2024). Comprehensive. | Youth player profile / name + match fixture | **RESTRICTED** — ICC / ACC copyright; fair dealing scouting research | Any senior international cap disqualifies uncapped status; Youth international appearances do NOT disqualify uncapped status. High-pressure global junior benchmark. | Authorised demand-driven adapter (Service C); per-claim provenance mandatory | **RESTRICTED / PER-CLAIM** |
| **S20A. ESPNcricinfo & Cricbuzz External Research (Secondary)** | espncricinfo.com, cricbuzz.com | Player career profiles, match reports, injury news, batting/bowling style | Player / Match | Comprehensive global cricket coverage | Player slug / profile ID + fixture date | **RESTRICTED** — Site terms; automated scraping prohibited; strict rate limits (<1 req/sec); fair-dealing research | Secondary reporting; conflicting statistics must be flagged `CONFLICT`; never treat snippets as facts | Authorised research per claim; human review required for ambiguous records | **RESTRICTED / PER-CLAIM** |
| **S20B. ESPNcricinfo Domestic Historical Archive (1934–2018)** | `espncricinfo.com` historical domestic match archives | Career profiles, match scorecards, bowling spells, player DOB and biographical profiles | Complete Scorecards (Scorecard Availability: Complete scorecards for senior finals and major league fixtures; Ball-by-Ball Availability: UNAVAILABLE — historical multi-day delivery ledgers do not exist) | Multi-decade historical coverage (1934–2018). Complete for senior domestic finals and major league matches. | ESPNcricinfo player ID / match ID | **RESTRICTED** — ESPNcricinfo / Disney Star proprietary terms; HTTP 403 on automated scraping | Secondary reference for pre-2018 domestic careers. Conflicting statistics vs official BCCI scorecards flag `CONFLICT` and route to `REVIEW_REQUIRED`. | Authorised human-gated research adapter; strict rate limiting (<1 req/sec); per-claim verification | **RESTRICTED / PER-CLAIM** |

### 1.1 Superseded historical claims (do not carry forward)
- "2,822 / 2,832 files across 5 subdirectories incl. 695 SMAT" (v1-era audits, `.agents/teamwork/`): describes the **removed `CricSheet/` archive**.
- **Current local data lake status (verified 2026-11-11 for v2.2.0)**: Exactly **13 directories, 5,083 match JSON files** (`ipl_male_json`: 1,243, `bbl_male_json`: 662, `sma_json`: 695, `bpl_male_json`: 469, `cpl_male_json`: 445, `psl_male_json`: 357, `icc_mens_cricket_world_cup_male_json`: 265, `icc_mens_t20_world_cup_male_json`: 230, `hnd_male_json`: 201, `lpl_male_json`: 143, `ilt_male_json`: 134, `sat_male_json`: 130, `mlc_male_json`: 109), all under **ODC-By v1.0**. All 13 directories contain verified `LICENSE.txt` and `README.txt` files conforming to Cricsheet schema v1.3.0.
- Any statement that Kaggle or HawkeyeStats data is "open dataset / MIT / permissive" is **unsupported** in this repository — both are RESTRICTED/UNVERIFIED per the register.

---

## 2. Match & Delivery Reconciliation Across Providers

Reconciliation is mandatory; **no dataset is joined on over/ball numbers alone.**

### 2.1 Match-level join
Composite match key: **competition + match date + team pair (unordered) + venue**, then
corroborated against provider-native ids where present (CricSheet numeric id; HawkeyeStats
match id; ESPN match id). CricSheet's `info.match_id` (modern files) is the strongest key and
is preferred when present.

### 2.2 Delivery-level join
CricSheet's ball index **counts all delivery events including wides and no-balls**; a
no-ball/wide at the end of an over produces the next "ball" 0.1. Cross-provider delivery keys
must therefore be:

```
(innings_number, delivery_ordinal)  where delivery_ordinal = 1-based event count,
   NOT (over, ball) text
```

Rules:
1. **Wides/no-balls**: keep the event sequence; a wide adds a delivery event without a legal
   ball; `deliveries.is_wide`/`is_noball` recorded; legal-ball counts derived, never parsed
   from notation strings.
2. **Super Overs**: CricSheet innings_number 3/4 (or `"super_over": true`); excluded from
   career aggregates (TRD §6.2; AI_INSTRUCTIONS R6).
3. **Missing/duplicate deliveries**: reconciliation produces a per-match match report with
   expected-vs-observed delivery counts; mismatches quarantine the match to Service D, never
   silent fill.
4. **Provider numbering differences**: HawkeyeStats uses its own match/innings/delivery
   numbering; a `provider_delivery_map` (external ids only, in `source_records`) is the only
   bridge to `deliveries`; no in-place numeric rewriting.
5. **Confidence levels**: *match-level* reconciliation confidence = (provider ids agree AND
   date/venue/team pair agree) → HIGH; (any attribute conflict) → LOW → human review.
   *Delivery-level* confidence = (event counts reconcile within tolerance AND wicket events
   align) → otherwise the delivery block is quarantined.

### 2.3 Licence & access governance
- RESTRICTED sources: retrieve, cite, store a provenance record (`verification_records` +
  `data_sources.license_evidence`); do not mirror at scale; respect robots/terms and
  automated-access restrictions of BCCI/IPL/ESPN/Cricbuzz pages.
- ODC-By (S1–S5, S6 if confirmed): attribution mandatory in all exports (Service B).
- The proprietary hackathon dataset (when introduced) is **confidential**: isolated
  directory, never referenced from public exports or this register's public rows.

---

### 2.4 API & Browser Research Access Constraints (PVRE Governance)
To protect data integrity, respect intellectual property, and prevent automated IP blocks, all
external research in Engine 07 (PVRE) and Service C must comply with strict access boundaries:

1. **Automated Scraping Prohibitions**:
   - Automated mass web-scraping against `bcci.tv`, `iplt20.com`, `espncricinfo.com`, and
     `cricbuzz.com` is **strictly prohibited**.
   - These sources are classified as **RESTRICTED**. Automated agents must not execute broad
     un-throttled crawling loops or attempt to bypass rate limiters/Cloudflare challenges.
2. **Authorised Research Adapter Protocol (Service C)**:
   - External research is permitted **only** via targeted, demand-driven API lookups or human-gated
     browser sessions targeting specific player or scorecard fixtures.
   - Every accessed page/record must be persisted in `source_records` with exact URL, provider,
     retrieval timestamp, and licensing tier.
   - Every factual assertion derived from external research must generate a corresponding
     `verification_records` row with `calibrated = FALSE` and appropriate tier ranking (Tier 1–4).
3. **Third-Party Snippet Discipline**:
   - Search engine snippets, LLM-generated summaries, and unverified news snippets must **never**
     be ingested as verified facts. They may serve only as discovery hints triggering formal
     verification against an authoritative scorecard or official registry.
4. **Source Discrepancy & Conflict Handling**:
   - If two sources report conflicting data (e.g. date of birth, match participation, runs), the
     system must **never overwrite** or silently average the values.
   - Both assertions must be persisted in `verification_records`, the claim flagged with
     `verification_status = 'CONFLICT'`, and the PVRE execution routed immediately to the
     mandatory **`REVIEW_REQUIRED`** safety state.

### 2.5 Source Marking, Conflict Handling & Fallback Protocol (PVRE Domestic Governance)
1. **Source Marking Protocol**:
   - `VERIFIED`: The dataset exists locally in the repository workspace, has been hashed and counted, and possesses an inspected permissive licence (e.g. S1–S5, S13–S17 under ODC-By v1.0).
   - `RESTRICTED / PER-CLAIM`: The source is proprietary or governed by terms of service forbidding bulk scraping (e.g. `bcci.tv` S18A–H, `icc-cricket.com` S19B, `espncricinfo.com` S20A–B). No bulk dataset may be assumed. Data must be ingested claim-by-claim via Service C with documented provenance (`verification_records` row linking URL, timestamp, HTTP status, and evidence tier).
   - `UNVERIFIED`: An external claim or dataset that has not yet been corroborated by a primary/secondary verification record.
   - `UNAVAILABLE`: The data is known not to exist (e.g. ball-by-ball tracking for historical multi-day Ranji Trophy or sensor data for domestic pitches).
2. **Conflict Resolution Rules**:
   - *Scorecard vs Ball-by-Ball Sum*: If CricSheet SMAT (S5) delivery sum disagrees with BCCI official scorecard (S18B) totals by runs or wickets, the delivery sequence is quarantined in Service D. The system generates a `verification_records` entry with `verification_status = 'CONFLICT'`, logs `review_reason_codes = ['CONFLICT_SCORECARD_VS_BBB']`, and routes the profile to `REVIEW_REQUIRED`.
   - *Conflicting Biographical / DOB Records*: If an external profile (S20B) states DOB as `2004-05-10` while official BCCI registration records (S18) state `2004-08-15`, the system **never averages or overwrites**. Both claims are persisted in `verification_records`, the player is flagged `CONFLICT_DOB_RECORD`, and uncapped age eligibility evaluation is halted in `REVIEW_REQUIRED`.
   - *Conflicting Participation Records*: If one source claims a player was in the playing XI while another marks them as bench/substitute, the system records `CONFLICT_PARTICIPATION_EVIDENCE` and demands manual verification against the official match referee report.
3. **Fallback Behaviour**:
   - When delivery-level data (BBB) is unavailable (which applies to all multi-day and age-group cricket S18A–H, and unindexed SMAT matches):
     * Fallback to **Innings-Level Scorecard Metrics**: B01 (Matches), B02 (Innings), B03 (Runs), B04 (Balls Faced where recorded), B05 (Batting Average), B06 (Strike Rate where balls recorded), B07 (Boundaries), W01 (Overs), W03 (Runs Conceded), W04 (Wickets), W05 (Bowling Average), W06 (Economy Rate), W07 (Bowling Strike Rate).
     * Delivery-level metrics (B09 dot-ball %, B12 phase splits, B14 pace/spin splits, W08 bowling dot %, W11 speed, W12 line/length) return `NOT_COMPUTABLE_FROM_AVAILABLE_SOURCES`.
     * Flag `career_coverage_state = 'PARTIAL_COVERAGE'` or `COMPLETE_WITHIN_VERIFIED_SOURCES` with an explicit indicator: `granularity = 'SCORECARD_ONLY'`.
   - When balls faced are missing from junior scorecards:
     * Set `balls_faced = NULL` and `strike_rate = NULL`. Never impute balls faced from runs scored or assume run-a-ball.

---

## 3. Verification Log (2026-11-10 local · 2026-11-11 external re-checks & dataset lake audit)

| Evidence | Result |
|---|---|
| **Local Dataset Lake Audit (verified 2026-11-11 for v2.2.0)** | Exactly **13 directories, 5,083 match JSON files** (`ipl_male_json`: 1,243, `bbl_male_json`: 662, `sma_json`: 695, `bpl_male_json`: 469, `cpl_male_json`: 445, `psl_male_json`: 357, `icc_mens_cricket_world_cup_male_json`: 265, `icc_mens_t20_world_cup_male_json`: 230, `hnd_male_json`: 201, `lpl_male_json`: 143, `ilt_male_json`: 134, `sat_male_json`: 130, `mlc_male_json`: 109) — all ODC-By v1.0. All 13 directories contain verified `LICENSE.txt` and `README.txt` files. |
| `ls datasets/` (v2.1.0 pre-remediation baseline) | 4 directories: `ipl_male_json`, `hnd_male_json`, `icc_mens_cricket_world_cup_male_json`, `icc_mens_t20_world_cup_male_json` — no `sma/`, no `CricSheet/` (superseded by 13-directory audit above) |
| File counts (`.json` only) | 1,243 / 201 / 265 / 230 — exactly matching each archive's `README.txt` stated count |
| `LICENSE.txt` ×4 | ODC Attribution License text present in all four archives |
| `README.txt` ×4 | Schema version 1.3.0; ODI WC: 24 matches withheld; T20 WC: 29 matches withheld (Afghanistan policy, cricsheet.org/withheld-matches) |
| External claims (Kaggle S6/S7, BCCI S10, ESPN S11) | **Not verified 2026-11-11** — statuses above reflect exactly that; Phase 4 external research must upgrade each with a dated evidence record |
| **S9 Open-Meteo terms (fetched 2026-11-11, open-meteo.com/en/terms)** | CC BY 4.0 for data products (incl. API); attribution required; free tier <10,000 calls/day · 5,000/hour; non-commercial per terms; "without any warranty" → S9 **VERIFIED** for licence/terms |
| **S8 HawkeyeStats repo (fetched 2026-11-11, github.com/alittlefitness/HawkeyeStats)** | No licence file/section; README: "a tidy version of the json data" from `cricketapi-icc.pulselive.com` → third-party reconstruction, not official Hawk-Eye; S8 stays **UNVERIFIED/RESTRICTED**, human-gated |
| **S4 CricSheet HND live download (fetched 2026-11-11, cricsheet.org/downloads)** | "The Hundred — Men (201)" JSON listed as `hnd_male_json.zip` → consistent with local 201-file archive |
| **S11 ESPNcricinfo squad archives (fetched 2026-11-11)** | **HTTP 403** on direct fetch → per-claim verification path only; past participation evidence remains UNVERIFIED (Priority E) |
| **Priority B — The Hundred format (local `datasets/hnd_male_json`, inspected 2026-11-11)** | `info.balls_per_over = 5`, `info.overs = 20` → 100-ball innings; over blocks carry `deliveries` arrays (5 legal events + wide events); `powerplays: [{from: 0.1, to: 4.5, type: mandatory}]`; sample innings: 20 over-blocks / 101–106 delivery events (including wide events). Confirmed by Wikipedia "The Hundred (cricket)": 5-ball overs, 100 balls per innings, 20 overs, max 4 overs per bowler, final-10-balls powerplay with two designated bowlers. → The Hundred is a first-class `HUNDRED` format (`competitions.balls_per_over = 5`); it must NOT inherit six-ball-over maths (DATA_DICTIONARY §5) |
| **Priority E/H — RR participation windows (local `datasets/ipl_male_json`, inspected 2026-11-11)** | Files mentioning "Rajasthan Royals" by season: 2007/08 (16) · 2009 (13) · 2009/10 (14) · 2011 (13) · 2012 (16) · 2013 (18) · 2014 (14) · 2015 (14) · **2016 (0) · 2017 (0)** · 2018 (15) · 2019 (14) · 2020/21 (14) · 2021 (14) · 2022 (17) · 2023 (14) · 2024 (15) · 2025 (14) · 2026 (16). 2016/2017 continue with 59–60 other-franchise fixtures each. → **Tier-4 local corroboration** of the RR 2008–2015 · suspended 2016–17 · 2018–2026 windows; reproducible script evidence, NOT tier-1; each `team_season_participation` row stays PENDING/UNVERIFIED until the S10 per-claim evidence lines are retrieved (TRD D15) |
| **Priority H — wide-event / notation evidence (local archives, 2026-11-11)** | IPL 2017 sample (`1082591.json`): `balls_per_over = 6`, 20 over-blocks; wide events present as delivery events within over blocks (over-block event count can exceed 6). HND sample (`1252666.json`): `balls_per_over = 5`, 20 over-blocks, event counts 101–106 incl. wide events. → legal-ball counts are derived (never parsed from ball-notation strings); wide/no-ball are delivery events; consistent with DATA_DICTIONARY global conventions and TRD DDL ingestion formula |
