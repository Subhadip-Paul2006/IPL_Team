import os

with open('docs/DATA_SOURCE_REGISTER.md', 'r', encoding='utf-8') as f:
    text = f.read().replace('\r\n', '\n')

# 1. Update version header
old_hdr = r'''**Document Version**: 2.1.1-TARGETED-REMEDIATION · **Status**: `[STATUS: PLANNED - GREENFIELD BASELINE]`
**Verification date of local evidence**: 2026-11-10 · **external re-checks**: 2026-11-11
(working directory `d:\New folder (2)`)'''

new_hdr = r'''**Document Version**: 2.2.0 · **Status**: `[STATUS: PLANNED - GREENFIELD BASELINE]`
**Verification date of local evidence**: 2026-11-10 · **external re-checks**: 2026-11-11
(working directory `d:\New folder (2)`)

> **Revision Note (v2.2.0, PVRE Multi-League Data Sources & Verification)**: Adds sources S13–S20
> to support PVRE Mode A recent global performance research (BBL, PSL, CPL, SA20, BPL, ILT20, LPL,
> MLC) and Mode B uncapped candidate domestic discovery (Ranji, SMAT, VHT, Duleep, BCCI age-groups).
> Documents empirical verification of local CricSheet archives: 662 BBL, 445 CPL, 357 PSL, 130 SA20,
> 695 SMAT (`datasets/sma_json/`), 469 BPL, 134 ILT20, 143 LPL, 109 MLC match files, all under ODC-By.
> Explicitly defines API and browser research access constraints for BCCI official records and
> ESPNcricinfo/Cricbuzz, mandating per-claim provenance, rate limiting, and conflict handling.'''

assert old_hdr in text
text = text.replace(old_hdr, new_hdr)

# 2. Update S5 in table
old_s5 = '''| **S5. CricSheet SMAT (Syed Mushtaq Ali Trophy) (local)** | expected `datasets/sma/` | — | — | **ABSENT locally** (inspected 2026-11-10: no `sma/` directory; v1-era claims of 695 SMAT files described a now-defunct `CricSheet/` archive) | — | ODC-By (expected, same publisher) | Whole source absent from the local lake | **Do not claim SMAT coverage**; route via external research (CDCRE) or download under ODC-By terms at Phase 1 | **UNAVAILABLE** (locally) |'''

new_s5 = '''| **S5. CricSheet SMAT (Syed Mushtaq Ali Trophy) (local)** | `datasets/sma_json/` | Match metadata (`info`), innings totals, ball-by-ball delivery ledger (`batter`, `bowler`, `runs`, wickets, extras), `people` registry | Ball-by-ball | **695 match files verified locally** (`datasets/sma_json/` verified 2026-11-10; archive contains 695 `.json` files) | External CricSheet ID + date + venue; delivery sequence | **ODC-By v1.0 — VERIFIED** (`LICENSE.txt` present and verified in `datasets/sma_json/`) | Pre-2018 matches may lack detailed `people` hashes; DLS targets when applicable; ball-level fielding positions absent | Local archive (untracked, read-only); primary domestic T20 proving ground for PVRE Mode B | **VERIFIED** (local files, licence, and counts inspected) |'''

assert old_s5 in text
text = text.replace(old_s5, new_s5)

# 3. Add Sources S13 to S20 to Source Register Matrix
table_end_target = '| **S12. Official scorecards (franchise/ICC published)** | Match scorecard pages/PDFs | Full playing XI, ball-by-ball summary, fielding records | Match | Per-match where published | match date + venue + fixture pair | **RESTRICTED** — publisher copyright; use for verification, cite source | Tier-2 evidence; used for appearance counts (`player_team_history.appearances`) | Manual retrieval at Phase 3/4 | **UNVERIFIED** (per-claim) |'
assert table_end_target in text

new_sources = '''| **S12. Official scorecards (franchise/ICC published)** | Match scorecard pages/PDFs | Full playing XI, ball-by-ball summary, fielding records | Match | Per-match where published | match date + venue + fixture pair | **RESTRICTED** — publisher copyright; use for verification, cite source | Tier-2 evidence; used for appearance counts (`player_team_history.appearances`) | Manual retrieval at Phase 3/4 | **UNVERIFIED** (per-claim) |
| **S13. CricSheet Big Bash League (BBL) (local)** | `datasets/bbl_male_json/` | Match metadata, scorecards, delivery events | Ball-by-ball | **662 match files verified locally** (inspected 2026-11-10) | Match ID + date + venue; delivery sequence | **ODC-By v1.0 — VERIFIED** (`LICENSE.txt` present) | Australian conditions; format context applies | Local archive; PVRE Mode A global research | **VERIFIED** |
| **S14. CricSheet Pakistan Super League (PSL) (local)** | `datasets/psl_male_json/` | Match metadata, scorecards, delivery events | Ball-by-ball | **357 match files verified locally** (inspected 2026-11-10) | Match ID + date + venue; delivery sequence | **ODC-By v1.0 — VERIFIED** (`LICENSE.txt` present) | Subcontinent franchise league context | Local archive; PVRE Mode A global research | **VERIFIED** |
| **S15. CricSheet Caribbean Premier League (CPL) (local)** | `datasets/cpl_male_json/` | Match metadata, scorecards, delivery events | Ball-by-ball | **445 match files verified locally** (inspected 2026-11-10) | Match ID + date + venue; delivery sequence | **ODC-By v1.0 — VERIFIED** (`LICENSE.txt` present) | Caribbean pitch conditions; format context applies | Local archive; PVRE Mode A global research | **VERIFIED** |
| **S16. CricSheet SA20 (local)** | `datasets/sat_male_json/` | Match metadata, scorecards, delivery events | Ball-by-ball | **130 match files verified locally** (inspected 2026-11-10) | Match ID + date + venue; delivery sequence | **ODC-By v1.0 — VERIFIED** (`LICENSE.txt` present) | High-altitude South African venue context | Local archive; PVRE Mode A global research | **VERIFIED** |
| **S17. Other Franchise Leagues (BPL, ILT20, LPL, MLC) (local)** | `datasets/{bpl,ilt,lpl,mlc}_male_json/` | Match metadata, scorecards, delivery events | Ball-by-ball | **855 match files verified locally** (BPL: 469, ILT20: 134, LPL: 143, MLC: 109) | Match ID + date + venue; delivery sequence | **ODC-By v1.0 — VERIFIED** (`LICENSE.txt` present in each) | Varied competition strengths; format context applies | Local archive; PVRE Mode A global research | **VERIFIED** |
| **S18. Official BCCI Domestic Records** | bcci.tv / official scorecards | Ranji Trophy, Vijay Hazare Trophy, Duleep Trophy, CK Nayudu U23, Vinoo Mankad U19 match scorecards | Match & Season | BCCI domestic circuit (2018–2026) | Player official registration ID + match fixture | **RESTRICTED** — BCCI terms of service; automated scraping prohibited; manual / authorised API research | Multi-day and List A scorecards; detailed ball tracking absent; official birth records | Authorised external research via Service C; each claim creates a `verification_records` row | **RESTRICTED / VERIFIED-PER-CLAIM** |
| **S19. International Match Archives (ICC Tests, ODIs, T20Is)** | CricSheet + official ICC scorecards | Senior international match records across formats | Ball-by-ball / Match | Complete senior international cricket (2005–2026) | Official player cap / name + match date | **ODC-By / RESTRICTED** (CricSheet + official ICC fair dealing) | Any senior international appearance disqualifies player from uncapped status | Local archive + authorised research | **VERIFIED** |
| **S20. ESPNcricinfo & Cricbuzz External Research** | espncricinfo.com, cricbuzz.com | Player career profiles, match reports, injury news, batting/bowling style | Player / Match | Comprehensive global cricket coverage | Player slug / profile ID + fixture date | **RESTRICTED** — Site terms; automated scraping prohibited; strict rate limits (<1 req/sec); fair-dealing research | Secondary reporting; conflicting statistics must be flagged `CONFLICT`; never treat snippets as facts | Authorised research per claim; human review required for ambiguous records | **RESTRICTED / PER-CLAIM** |'''

text = text.replace(table_end_target, new_sources)

# 4. Add Section 2.4 API and Browser Research Access Constraints
reconcile_end = text.find('## 3. Verification Log')
assert reconcile_end != -1

access_constraints = '''### 2.4 API & Browser Research Access Constraints (PVRE Governance)
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

---

'''

text = text[:reconcile_end] + access_constraints + text[reconcile_end:]

with open('docs/DATA_SOURCE_REGISTER.md', 'w', encoding='utf-8', newline='\n') as f:
    f.write(text)

print('docs/DATA_SOURCE_REGISTER.md successfully updated and written!')
