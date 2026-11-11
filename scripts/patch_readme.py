import re

with open('README.md', 'r', encoding='utf-8') as f:
    content = f.read().replace('\r\n', '\n')

# 1. Update Header
old_header = """**Focus Franchise**: Rajasthan Royals (RR) · **Competition**: IPL 2027 RR scouting hackathon
**Primary Interface (initial)**: Streamlit · **Future Frontend**: Next.js (engines are frontend-agnostic)
**Status**: `[STATUS: GREENFIELD BASELINE — PHASE 0a COMPLETE / PHASE 0b OPEN (PARTIALLY_COMPLETE) / PHASES 1–10 PLANNED]`

> **Product version 2.1.0 (remediated)**. This revision corrects the v2.0.0 schema defects"""

new_header = """**Focus Franchise**: Rajasthan Royals (RR) · **Competition**: IPL 2027 RR scouting hackathon
**Primary Interface (initial)**: Streamlit · **Future Frontend**: Next.js (engines are frontend-agnostic)
**Status**: `[STATUS: GREENFIELD BASELINE — PHASE 0a COMPLETE / PHASE 0b OPEN (PARTIALLY_COMPLETE) / PHASES 1–10 PLANNED]`

> **Product version 2.2.0 (PVRE Dual-Mode Intelligence)**. Introduces **ENGINE 07 — PVRE
> (Player Verification & Research Engine)** featuring Mother Controller routing, Mode A (Existing
> RR Player Replacement Intelligence: Module A1 RR history + Module A2 2–3 year recent global window +
> Module A3 Replaceability Signals), Mode B (Verified Uncapped Candidate Domestic Career Intelligence),
> and mandatory `REVIEW_REQUIRED` safety gating. Integrates SICE 16 role-aware comparison dimensions
> (§8.4) with strict separation from the hackathon Top-10 uncapped candidate ranking. Establishes
> **Phase 4B** in `docs/PHASES.md` as the authoritative roadmap with 12 checkpoints and AC-24..AC-30.
> Reconciles database baseline to **33 entities** (including `player_season_stats` and `player_match_stats`),
> **7 specialised engines**, and **18 system agents**.
>
> **Product version 2.1.0 (remediated)**. This revision corrects the v2.0.0 schema defects"""

assert old_header in content, "Could not find old_header in README.md"
content = content.replace(old_header, new_header, 1)

# 2. Update Architecture diagram and description
old_arch_block = """A central **Mother Intelligence Engine (MIE)** orchestrates **six specialised engines** and
**five support services**, all reading a **31-entity normalised PostgreSQL core**. The MIE
never invents statistics or makes membership/eligibility decisions; it coordinates the
engines, merges their outputs, tracks verification status and source provenance, and returns
structured reports. Engines are **frontend-agnostic**: the initial UI is **Streamlit**, and
a future **Next.js** frontend reuses the same contracts.

```
┌────────────────────────────────────────────────────────────────────┐
│  Presentation (Streamlit initial / Next.js future)                  │
│  Team Builder · Search · Verification · Career · Analytics · SICE  │
└───────────────────────────────┬────────────────────────────────────┘
                                ▼
┌────────────────────────────────────────────────────────────────────┐
│  MOTHER INTELLIGENCE ENGINE (MIE) — orchestrates, merges, tracks  │
│  Sequence: candidate discovery → identity → membership → career   │
│           → performance → context → eligibility → squad           │
└──┬──────┬──────┬──────┬──────┬──────┬────────────────────────────┘
   ▼      ▼      ▼      ▼      ▼      ▼
 PIRE   TMVE   CDCRE  CPPAE  CMIE   SICE
 Eng01  Eng02  Eng03  Eng04  Eng05  Eng06
   └────┴────┴────┴────┴────┴────── Support Services A–E
   │
   ▼
 Central PostgreSQL 16 core (31 entities, normalised 3NF core)  ←  datasets/ (immutable)
```

### The six specialised engines
| Engine | Name | Purpose |
|---|---|---|
| **ENGINE 01 — PIRE** | Player Identity Resolution | Resolve names to canonical player IDs; deterministic 4-tier waterfall with contextual attribute corroboration; never merges similar names; confidence only when calibrated. |
| **ENGINE 02 — TMVE** | Team Membership Verification | Three-dimension membership (relationship · currency · season-bound eligibility); verified appearances vs squad inclusion; negative-verification protocol; franchise participation model. |
| **ENGINE 03 — CDCRE** | Career Discovery & Competition Research | **Two capabilities**: `discover_candidates(raw_name)` (pre-identity) and `discover_career(player_id)` (post-identity); four-state coverage; provenance-tracked external research. |
| **ENGINE 04 — CPPAE** | Complete Player Performance Analytics | Batting / bowling / fielding / wicketkeeping / match contribution, governed by `DATA_DICTIONARY.md` (formulas, null rules, sample minimums, format tags). |
| **ENGINE 05 — CMIE** | Contextual Match Intelligence | Environmental & match conditions; five provenance tiers; weather ≠ pitch; no mental-state inference. |
| **ENGINE 06 — SICE** | Squad Intelligence & Composition | Role/depth/balance/duplication/gap analysis; comparisons; labelled analytical recommendations; hackathon Top-10 ranking support. |"""

new_arch_block = """A central **Mother Intelligence Engine (MIE)** orchestrates **seven specialised engines** and
support services, all reading a **33-entity normalised PostgreSQL core**. The MIE
never invents statistics or makes membership/eligibility decisions; it coordinates the
engines, merges their outputs, tracks verification status and source provenance, and returns
structured reports. Engines are **frontend-agnostic**: the initial UI is **Streamlit**, and
a future **Next.js** frontend reuses the same contracts.

```
┌────────────────────────────────────────────────────────────────────────────────┐
│  Presentation (Streamlit initial / Next.js future)                             │
│  Team Builder · Search · Verification · Career · Analytics · SICE · PVRE Views │
└───────────────────────────────────────┬────────────────────────────────────────┘
                                        ▼
┌────────────────────────────────────────────────────────────────────────────────┐
│  MOTHER INTELLIGENCE ENGINE (MIE) — orchestrates, merges, tracks               │
│  Sequence: candidate discovery → identity → membership → career                │
│           → performance → context → eligibility → PVRE research → SICE        │
└──┬──────┬──────┬──────┬──────┬──────┬──────┬───────────────────────────────────┘
   ▼      ▼      ▼      ▼      ▼      ▼      ▼
 PIRE   TMVE   CDCRE  CPPAE  CMIE   SICE   PVRE
 Eng01  Eng02  Eng03  Eng04  Eng05  Eng06  Eng07 (Mode A / Mode B / Review)
   └────┴────┴────┴────┴────┴────── Support Services A–E
   │
   ▼
 Central PostgreSQL 16 core (33 entities, normalised 3NF core)  ←  datasets/ (immutable)
```

### The seven specialised engines
| Engine | Name | Purpose |
|---|---|---|
| **ENGINE 01 — PIRE** | Player Identity Resolution | Resolve names to canonical player IDs; deterministic 4-tier waterfall with contextual attribute corroboration; never merges similar names; confidence only when calibrated. |
| **ENGINE 02 — TMVE** | Team Membership Verification | Three-dimension membership (relationship · currency · season-bound eligibility); verified appearances vs squad inclusion; negative-verification protocol; franchise participation model. |
| **ENGINE 03 — CDCRE** | Career Discovery & Competition Research | **Two capabilities**: `discover_candidates(raw_name)` (pre-identity) and `discover_career(player_id)` (post-identity); four-state coverage; provenance-tracked external research. |
| **ENGINE 04 — CPPAE** | Complete Player Performance Analytics | Batting / bowling / fielding / wicketkeeping / match contribution, governed by `DATA_DICTIONARY.md` (formulas, null rules, sample minimums, format tags). |
| **ENGINE 05 — CMIE** | Contextual Match Intelligence | Environmental & match conditions; five provenance tiers; weather ≠ pitch; no mental-state inference. |
| **ENGINE 06 — SICE** | Squad Intelligence & Composition | Role/depth/balance/duplication/gap analysis; 16-dimension replacement comparison (§8.4); labelled analytical recommendations; hackathon Top-10 ranking support. |
| **ENGINE 07 — PVRE** | Player Verification & Research Engine | Dual-mode player research & replacement intelligence: Mother Controller, Mode A (RR Replacement: RR history + 2–3 yr global window + Replaceability Signals), Mode B (Verified Uncapped Domestic Career Discovery), and mandatory `REVIEW_REQUIRED` safety gating. |"""

assert old_arch_block in content, "Could not find old_arch_block in README.md"
content = content.replace(old_arch_block, new_arch_block, 1)

# 3. Update Section 4 Table
old_sec4_table = """| **Agent id** | `agent_cdcpre` | `agent_cdcre` |
| **Hackathon deliverable** | Not represented | **Top-10 youngest eligible uncapped candidates** spec + reproducible role-aware ranking methodology (PRD §4.3) |"""

new_sec4_table = """| **Agent id** | `agent_cdcpre` | `agent_cdcre` (now 18 agents total, adding `agent_pvre` and `agent_doc_remediation`) |
| **Specialised Engines** | 6 engines | **7 specialised engines** (+ ENGINE 07 PVRE with Mode A & Mode B) |
| **Entity count** | 31 | **33 entities** (verified PostgreSQL core including `player_season_stats` and `player_match_stats`) |
| **Hackathon deliverable** | Not represented | **Top-10 youngest eligible uncapped candidates** spec + reproducible role-aware ranking methodology (PRD §4.3), strictly isolated from Mode A replacement comparisons |"""

assert old_sec4_table in content, "Could not find old_sec4_table in README.md"
content = content.replace(old_sec4_table, new_sec4_table, 1)

# 4. Update Section 5 Repository Layout
old_repo_layout = """├── docs/                                # Authoritative documentation suite
│   ├── README.md                        #   Hub: pathways + traceability matrix
│   ├── PRD.md                           #   Requirements, workflow, Top-10 deliverable, AC-01…AC-23
│   ├── TRD.md                           #   MIE + 6 engine contracts, 5 services, 31-entity DDL
│   ├── ARCHITECTURE.md                  #   10 Mermaid diagrams (DDL-mirrored ERD) + 7 ADRs
│   ├── PHASES.md                        #   Phase 0a/0b + 1–10 roadmap (MVP vs long-term)
│   ├── AGENTS.md                        #   16 agent contracts (`agent_cdcre` etc.)
│   ├── AI_INSTRUCTIONS.md               #   Identity/membership/evidence mandates + domain rules
│   ├── DATA_SOURCE_REGISTER.md          #   Source-to-field matrix, statuses, reconciliation
│   └── DATA_DICTIONARY.md               #   Metric dictionary (B/W/F/M series + NOT_COMPUTABLE)"""

new_repo_layout = """├── docs/                                # Authoritative documentation suite
│   ├── README.md                        #   Hub: pathways + traceability matrix
│   ├── PRD.md                           #   Requirements, workflow, PVRE dual-mode, Top-10 deliverable, AC-01…AC-30
│   ├── TRD.md                           #   MIE + 7 engine contracts (incl. PVRE), 6 services, 33-entity DDL
│   ├── ARCHITECTURE.md                  #   14 Mermaid diagrams (DDL-mirrored ERD, PVRE flows) + 8 ADRs
│   ├── PHASES.md                        #   Phase 0a/0b + Phase 4B (PVRE) + 1–10 roadmap (MVP vs long-term)
│   ├── AGENTS.md                        #   18 agent contracts (`agent_pvre`, `agent_cdcre` etc.)
│   ├── AI_INSTRUCTIONS.md               #   Identity/membership/evidence mandates + domain rules R1..R22
│   ├── DATA_SOURCE_REGISTER.md          #   Source-to-field matrix, statuses, reconciliation, S1..S20
│   ├── DATA_DICTIONARY.md               #   Metric dictionary (B/W/F/M, R01..R06, D01..D16 + NOT_COMPUTABLE)
│   └── RANKING_SPEC.md                  #   Candidate ranking & replacement intelligence (RK-1.0.0, RE-1.0.0)"""

assert old_repo_layout in content, "Could not find old_repo_layout in README.md"
content = content.replace(old_repo_layout, new_repo_layout, 1)

# 5. Update Section 6 docs table
old_doc_table = """| [`docs/PRD.md`](docs/PRD.md) | Updated user experience (candidate-discovery-first workflow), three-dimension membership, FR traceability, 11 Streamlit views, Top-10 hackathon spec, AC-01…AC-23. |
| [`docs/TRD.md`](docs/TRD.md) | MIE + 6 engine I/O contracts, 5 services, remediated 31-entity DDL (design decisions D1–D10), negative-verification requirements, versioned eligibility policies, Streamlit requirements. |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Orchestration and data-flow: 10 Mermaid diagrams (DDL-mirrored 31-entity ERD), MIE/Pire/TMVE flows, SICE flow, 7 ADRs. |"""

new_doc_table = """| [`docs/PRD.md`](docs/PRD.md) | Updated user experience (candidate-discovery-first workflow), PVRE dual-mode intelligence (Mode A replacement & Mode B uncapped), three-dimension membership, FR traceability, 11 Streamlit views, Top-10 hackathon spec, AC-01…AC-30. |
| [`docs/TRD.md`](docs/TRD.md) | MIE + 7 engine I/O contracts (incl. PVRE §9), SICE replacement comparison (§8.4), 6 services, verified 33-entity DDL, negative-verification requirements, versioned eligibility policies, Streamlit requirements. |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Orchestration and data-flow: 14 Mermaid diagrams (DDL-mirrored 33-entity ERD, PVRE dual-mode flows), MIE/PIRE/TMVE/SICE/PVRE flows, 8 ADRs (incl. ADR-008). |"""

assert old_doc_table in content, "Could not find old_doc_table in README.md"
content = content.replace(old_doc_table, new_doc_table, 1)

# 6. Update Section 8 implementation status
old_status_box = """[STATUS: PLANNED]   Phase 3 — TMVE (three dimensions + team_season_participation + policies)
[STATUS: PLANNED]   Phase 4 — CDCRE dual capability & external research
[STATUS: PLANNED]   Phase 5 — CPPAE per DATA_DICTIONARY"""

new_status_box = """[STATUS: PLANNED]   Phase 3 — TMVE (three dimensions + team_season_participation + policies)
[STATUS: PLANNED]   Phase 4 — CDCRE dual capability & external research
[STATUS: PLANNED - MVP] Phase 4B — PVRE Dual-Mode Research & Replacement Intelligence
[STATUS: PLANNED]   Phase 5 — CPPAE per DATA_DICTIONARY"""

assert old_status_box in content, "Could not find old_status_box in README.md"
content = content.replace(old_status_box, new_status_box, 1)

# 7. Update PostgreSQL 31-entity mentions to 33-entity in Section 7
content = content.replace("PostgreSQL 16+** (31-entity normalised core", "PostgreSQL 16+** (33-entity normalised core", 1)
content = content.replace("apply the 31-entity DDL from", "apply the 33-entity DDL from", 1)
content = content.replace("validation of the 31-entity DDL", "validation of the 33-entity DDL", 1)

with open('README.md', 'w', encoding='utf-8', newline='\n') as f:
    f.write(content)

print("README.md successfully updated!")
