import os

with open('docs/AI_INSTRUCTIONS.md', 'r', encoding='utf-8') as f:
    text = f.read().replace('\r\n', '\n')

# 1. Update version header
old_hdr = '''**Document Version**: 2.0.0-ARCH-REVISION
**Status**: `[STATUS: ACTIVE MANDATORY DIRECTIVE - GREENFIELD BASELINE]`
**Date**: November 2026
**Primary Authors**: Principal Software Architect, Systems Governance Lead, Lead Cricket Data Scientist

> **Revision Note (v2.0.0)**: This directive now governs the **RR Squad Intelligence & Team
> Composition Platform** (MIE + six engines + five services).'''

new_hdr = '''**Document Version**: 2.2.0
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
> (MIE + six engines + five services).'''

assert old_hdr in text
text = text.replace(old_hdr, new_hdr)

# 2. Entity and engine counts
text = text.replace(
    '|  2. CENTRAL NORMALISED 3NF RELATIONAL CORE (27 ENTITIES)                                           |',
    '|  2. CENTRAL NORMALISED 3NF RELATIONAL CORE (33 ENTITIES)                                           |'
)
text = text.replace(
    'All player/match/delivery entities reside in a normalised 3NF PostgreSQL 16 schema of 27 entities',
    'All player/match/delivery entities reside in a normalised 3NF PostgreSQL 16 schema of 33 entities'
)
text = text.replace(
    '| PostgreSQL (Normalised Core) | 16.0+ (3NF, 31 entities)                  |',
    '| PostgreSQL (Normalised Core) | 16.0+ (3NF, 33 entities)                  |'
)

# 3. Add Domain Commandments box R13-R22 and detailed sections
old_box_end = '|  R12: NEVER make an unsupported membership or eligibility claim (absent evidence = UNVERIFIED)     |\n+----------------------------------------------------------------------------------------------------+'

new_box_end = '''|  R12: NEVER make an unsupported membership or eligibility claim (absent evidence = UNVERIFIED)     |
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
+----------------------------------------------------------------------------------------------------+'''

assert old_box_end in text
text = text.replace(old_box_end, new_box_end)

# Add rules R13-R22 after Rule R12
old_r12 = '''### Rule R12 — Unsupported claims stay UNVERIFIED
- Membership, eligibility, and career claims lacking verified evidence are returned as
  `UNVERIFIED` / `NOT_ESTABLISHED`, never as positive or negative determinations.'''

new_rules = '''### Rule R12 — Unsupported claims stay UNVERIFIED
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
  public logs, or client-side JSON/CSV exports.'''

assert old_r12 in text
text = text.replace(old_r12, new_rules)

with open('docs/AI_INSTRUCTIONS.md', 'w', encoding='utf-8', newline='\n') as f:
    f.write(text)

print('docs/AI_INSTRUCTIONS.md successfully updated and written!')
