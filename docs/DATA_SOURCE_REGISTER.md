# Data Source Register

**Project**: RR Squad Intelligence & Team Composition Platform
**Document Version**: 2.1.0-REMEDIATED · **Status**: `[STATUS: PLANNED - GREENFIELD BASELINE]`
**Verification date of local evidence**: 2026-11-10 (this session, working directory
`d:\New folder (2)`)

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
| **S5. CricSheet SMAT (Syed Mushtaq Ali Trophy) (local)** | expected `datasets/sma/` | — | — | **ABSENT locally** (inspected 2026-11-10: no `sma/` directory; v1-era claims of 695 SMAT files described a now-defunct `CricSheet/` archive) | — | ODC-By (expected, same publisher) | Whole source absent from the local lake | **Do not claim SMAT coverage**; route via external research (CDCRE) or download under ODC-By terms at Phase 1 | **UNAVAILABLE** (locally) |
| **S6. Kaggle IPL Complete 2008–2020** | https://www.kaggle.com/datasets/patrickb1912/ipl-complete-dataset-20082020 | Claimed: historical match records, player/team info (match-level CSVs) | Match-level | Claimed 2008–2020; **actual columns/rows not inspected** | match id / date / teams | **RESTRICTED** — Kaggle dataset terms (author-defined); not automatically permissive; no licence text inspected | Provenance = community upload; untrusted until reconciled against S1 | Not collected (no local copy); Phase 1 acquisition under Kaggle terms with provenance record | **UNVERIFIED** (no local evidence; do not label "CC0/open") |
| **S7. Kaggle IPL "2007–2026" ball-by-ball** | https://www.kaggle.com/datasets/vedantbhavsar43/ipl-2007-to-2026-complete-ball-by-ball-dataset | Claimed extended delivery ledger | Delivery | Title claims 2007; **IPL's first match was 2008-04-18** — any 2007 records are pre-IPL/exhibition or corrupt; **must be quarantined if present** | delivery keys per provider | **RESTRICTED** — Kaggle terms; no licence text inspected | Temporal impossibility in title; untrusted numbering vs CricSheet ball index | Not collected locally; if acquired, Phase 1 quarantine rule: flag any `match_date < 2008-04-18` IPL-labelled record | **UNVERIFIED** + quarantine rule |
| **S8. HawkeyeStats** | https://github.com/alittlefitness/HawkeyeStats | Claimed: ball tracking (delivery speed, pitch impact coordinates, post-shot trajectory) for televised matches | Per-delivery (subset) | **Third-party reconstruction, NOT official Hawk-Eye data**; coverage/units/columns not inspected this session | match id + innings + delivery ordinal; provider numbering differs from CricSheet | **UNVERIFIED** — repository licence not inspected (do not assume MIT/permissive) | Sparse (broadcast-only); coordinate definitions/units undocumented locally; post-shot coords must never be read as fielder positions (TRD §7, AI_INSTRUCTIONS R4) | Not collected locally; Phase 1 acquisition + schema audit, provenance record mandatory | **UNVERIFIED / RESTRICTED pending licence check** |
| **S9. Open-Meteo Historical Weather API** | https://open-meteo.com/en/docs/historical-weather-api | Hourly reanalysis fields: temperature, relative humidity, dew point, wind speed/direction, precipitation, cloud cover (ERA5/ERA5-Land reanalysis) | Hourly, geogrid | Historical reanalysis archive (multi-decade), gridded — **matched to stadium coordinates as a proxy; spatial/temporal matching method must be recorded per weather row (TRD §10.2 D10)** | venue lat/long + match timestamp + venue timezone | **CC BY 4.0 (stated in docs; exact current terms to be re-verified at Phase 6)** | Reanalysis ≠ station measurement; **environmental context only, never a pitch measurement**; small-stadium microclimate not represented | API call at Phase 6 with attribution; coordinates per venue | **PARTIALLY_VERIFIED** (API exists; terms to be re-verified at use time) |
| **S10. Official BCCI / IPL / RR records** | bcci.tv, iplt20.com, rrj.co.in announcements | Squad lists, auction results, playing conditions, suspension notices, availability notices | Season / event | RR seasons 2008–2026 verified squad windows; **IPL 2027 squad status: UNKNOWN until published** | team + season; player official name spelling | **RESTRICTED** — fair dealing / automated-access limits apply; cite, don't scrape at scale | 2016–17 RR suspension notice = tier-1 evidence for `team_season_participation`; squad PDFs authoritative for `squad_memberships` | Manual/authorised retrieval at Phase 3 with `verification_records` tier-1 rows | **UNVERIFIED** (per-claim, verified at retrieval) |
| **S11. ESPNcricinfo / Cricbuzz (secondary)** | espncricinfo.com, cricbuzz.com | Player career pages, match reports, scorecards | Player / match | Broad but community-maintained in places | official player page id; match date + fixture | **RESTRICTED** — site terms; no bulk reuse; per-page provenance only | Tiers 4–5 evidence (TRD §4.2 hierarchy); conflicting data → `CONFLICT` → human review | Authorised external research at Phase 4; one `verification_record` per claim | **UNVERIFIED** (per-claim) |
| **S12. Official scorecards (franchise/ICC published)** | Match scorecard pages/PDFs | Full playing XI, ball-by-ball summary, fielding records | Match | Per-match where published | match date + venue + fixture pair | **RESTRICTED** — publisher copyright; use for verification, cite source | Tier-2 evidence; used for appearance counts (`player_team_history.appearances`) | Manual retrieval at Phase 3/4 | **UNVERIFIED** (per-claim) |

### 1.1 Superseded historical claims (do not carry forward)
- "2,822 / 2,832 files across 5 subdirectories incl. 695 SMAT" (v1-era audits, `.agents/teamwork/`):
  describes the **removed `CricSheet/` archive**. **Actual local lake (2026-11-10): 4 directories,
  1,939 match JSON files (1,243+201+265+230), no SMAT.** Historical reports are preserved
  unmodified; this section is the only current statement of local data availability.
- Any statement that Kaggle or HawkeyeStats data is "open dataset / MIT / permissive" is
  **unsupported** in this repository — both are RESTRICTED/UNVERIFIED per the register.

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

## 3. Verification Log (this session, 2026-11-10)

| Evidence | Result |
|---|---|
| `ls datasets/` | 4 directories: `ipl_male_json`, `hnd_male_json`, `icc_mens_cricket_world_cup_male_json`, `icc_mens_t20_world_cup_male_json` — no `sma/`, no `CricSheet/` |
| File counts (`.json` only) | 1,243 / 201 / 265 / 230 — exactly matching each archive's `README.txt` stated count |
| `LICENSE.txt` ×4 | ODC Attribution License text present in all four archives |
| `README.txt` ×4 | Schema version 1.3.0; ODI WC: 24 matches withheld; T20 WC: 29 matches withheld (Afghanistan policy, cricsheet.org/withheld-matches) |
| External claims (Kaggle S6/S7, HawkeyeStats S8, BCCI S10, ESPN S11, Open-Meteo S9 terms) | **Not verified this session** — statuses above reflect exactly that; Phase 4 external research must upgrade each with a dated evidence record |
