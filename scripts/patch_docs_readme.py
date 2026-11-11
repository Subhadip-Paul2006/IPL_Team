import re

with open('docs/README.md', 'r', encoding='utf-8') as f:
    content = f.read().replace('\r\n', '\n')

# 1. Update Header
old_header = """**Competition**: IPL 2027 Hackathon (Rajasthan Royals scouting)
**Target Franchise**: Rajasthan Royals (RR)
**Document Suite Version**: 2.1.0-REMEDIATED
**Status**: `[STATUS: ACTIVE BASELINE - GREENFIELD IMPLEMENTATION TARGET]`
**Date**: November 2026
**Primary Authors**: Principal Software Architect, Sports Data Engineer, Cricket Analytics Researcher, Technical Documentation Engineer

> **Revision Note (v2.1.0, remediation)**: This suite now describes the remediated
> architecture: **31-entity PostgreSQL core**, the franchise-level"""

new_header = """**Competition**: IPL 2027 Hackathon (Rajasthan Royals scouting)
**Target Franchise**: Rajasthan Royals (RR)
**Document Suite Version**: 2.2.0-PVRE-DUAL-MODE
**Status**: `[STATUS: ACTIVE BASELINE - GREENFIELD IMPLEMENTATION TARGET]`
**Date**: November 2026
**Primary Authors**: Principal Software Architect, Sports Data Engineer, Cricket Analytics Researcher, Technical Documentation Engineer

> **Revision Note (v2.2.0, PVRE Dual-Mode Architecture)**: Introduces **ENGINE 07 — PVRE
> (Player Verification & Research Engine)** featuring Mother Controller routing, Mode A (Existing
> RR Player Replacement Intelligence: RR history + 2–3 year recent global window + replaceability
> signals), Mode B (Verified Uncapped Candidate Domestic Career Intelligence), and mandatory
> `REVIEW_REQUIRED` safety gating. Integrates SICE 16 role-aware comparison dimensions for
> incumbent replacement without contaminating the hackathon Top-10 uncapped ranking. Establishes
> **Phase 4B** in `PHASES.md` as the authoritative implementation roadmap with AC-24..AC-30.
> Aligns architecture to **7 specialised engines**, **18 agents**, and **33 database entities**.
>
> **Revision Note (v2.1.0, remediation)**: This suite now describes the remediated
> architecture: **31-entity PostgreSQL core**, the franchise-level"""

assert old_header in content, "Could not find old_header in docs/README.md"
content = content.replace(old_header, new_header, 1)

# 2. Update architectural map text and engine list
old_map_section = """|   BUSINESS & PRODUCT SPECIFICATION                                                                 |
|   └── docs/PRD.md (Personas, revised workflow, FRs with full traceability, 11 Streamlit views,     |
|                    hackathon Top-10 deliverable spec, MVP vs post-MVP, AC-01…AC-23)                |
|                                                                                                    |
|   TECHNICAL SPECIFICATION & DATA MODEL                                                             |
|   └── docs/TRD.md (MIE + 6 engine I/O contracts, 5 support services, 31-entity DDL,               |
|                    three-dimension membership, eligibility policies, Streamlit reqs,               |
|                    frontend-agnostic contracts)                                                    |"""

new_map_section = """|   BUSINESS & PRODUCT SPECIFICATION                                                                 |
|   └── docs/PRD.md (Personas, revised workflow, FRs with full traceability, 11 Streamlit views,     |
|                    hackathon Top-10 deliverable spec, PVRE FR-PV1..8, MVP vs post-MVP, AC-01…AC-30) |
|                                                                                                    |
|   TECHNICAL SPECIFICATION & DATA MODEL                                                             |
|   └── docs/TRD.md (MIE + 7 engine I/O contracts [incl. PVRE], 6 support services, 33-entity DDL,   |
|                    three-dimension membership, eligibility policies, Streamlit reqs,               |
|                    frontend-agnostic contracts)                                                    |"""

assert old_map_section in content, "Could not find old_map_section in docs/README.md"
content = content.replace(old_map_section, new_map_section, 1)

old_agents_map = """|   MULTI-AGENT OPERATING CONSTITUTION                                                               |
|   └── docs/AGENTS.md (16 agent contracts mapped to MIE, 6 engines, 5 services, delivery & QA)      |"""

new_agents_map = """|   MULTI-AGENT OPERATING CONSTITUTION                                                               |
|   └── docs/AGENTS.md (18 agent contracts mapped to MIE, 7 engines, 6 services, delivery & QA)      |"""

assert old_agents_map in content, "Could not find old_agents_map in docs/README.md"
content = content.replace(old_agents_map, new_agents_map, 1)

# 3. Update table in Section 2
old_table_rows = """| [**`PRD.md`**](./PRD.md) | **Product Requirements Document**<br>*(Squad Intelligence & Team Composition)* | Franchise CEO, Head of Cricket Ops, Squad Strategists, Product Managers | Product vision, three-dimension membership/eligibility semantics, candidate-discovery-first workflow, FRs with full traceability (contract · architecture · phase · agent · AC), 11 Streamlit views, hackathon Top-10 deliverable spec (§4.3), scope partition, AC-01…AC-23 | Workflow diagram, FR traceability tables, acceptance matrix |
| [**`TRD.md`**](./TRD.md) | **Technical Requirements Document**<br>*(MIE + 6 Engines + 5 Services + 31-Entity DDL)* | Principal Architects, Data Engineers, Backend Engineers, DBA | MIE orchestration contract, engine I/O contracts (PIRE tiers · TMVE 3 dimensions · CDCRE dual capability · CPPAE · CMIE · SICE), support services, remediated 31-entity PostgreSQL 16 DDL (design decisions D1–D10), negative-verification requirements, versioned eligibility policies, Streamlit requirements, frontend-agnostic API surface | Engine contracts, 31-entity DDL, API table |"""

new_table_rows = """| [**`PRD.md`**](./PRD.md) | **Product Requirements Document**<br>*(Squad Intelligence & Team Composition)* | Franchise CEO, Head of Cricket Ops, Squad Strategists, Product Managers | Product vision, three-dimension membership/eligibility semantics, candidate-discovery-first workflow, PVRE dual-mode intelligence (Mode A replacement & Mode B uncapped), FRs with full traceability, 11 Streamlit views, hackathon Top-10 deliverable spec, AC-01…AC-30 | Workflow diagrams, FR traceability tables, acceptance matrix |
| [**`TRD.md`**](./TRD.md) | **Technical Requirements Document**<br>*(MIE + 7 Engines + 6 Services + 33-Entity DDL)* | Principal Architects, Data Engineers, Backend Engineers, DBA | MIE orchestration contract, 7 engine I/O contracts (PIRE, TMVE, CDCRE, CPPAE, CMIE, SICE, PVRE), SICE replacement comparison (§8.4), support services, verified 33-entity PostgreSQL 16 DDL, negative-verification requirements, versioned eligibility policies, Streamlit requirements | Engine contracts, 33-entity DDL, API table |"""

assert old_table_rows in content, "Could not find old_table_rows in docs/README.md"
content = content.replace(old_table_rows, new_table_rows, 1)

# 4. Update Stakeholder reading pathways
content = content.replace(
    "[`TRD.md §3–§8`](./TRD.md#3-engine-01--player-identity-resolution-engine-pire) — engine\n   contracts (PIRE → SICE).",
    "[`TRD.md §3–§9`](./TRD.md#3-engine-01--player-identity-resolution-engine-pire) — engine\n   contracts (PIRE → SICE, and PVRE §9 with SICE replacement comparison §8.4).",
    1
)

content = content.replace(
    "[`PRD.md §8`](./PRD.md#8-acceptance-criteria) — acceptance criteria AC-01…AC-23.",
    "[`PRD.md §8`](./PRD.md#8-acceptance-criteria) — acceptance criteria AC-01…AC-30 (including PVRE criteria AC-24..AC-30).",
    1
)

# 5. Update Cross-Document Traceability Matrix
old_trace_entry = """| **F-E6** | Squad Intelligence & Composition (SICE) | [PRD §5.6](./PRD.md#56-squad-intelligence--composition-sice) | [TRD §8](./TRD.md#8-engine-06--squad-intelligence--composition-engine-sice) | [ARCH §2.8](./ARCHITECTURE.md#28-diagram-8-squad-intelligence--composition-sice-evaluation-flow) | [Phase 8](./PHASES.md#10-phase-8--squad-intelligence--composition-sice--service-e) | `agent_sice` |
| **F-O1** | MIE Orchestration & Unified Report | [PRD §4](./PRD.md#4-user-workflow-primary--revised) | [TRD §2](./TRD.md#2-mother-intelligence-engine-mie--central-orchestrator) | [ARCH §2.2 / §2.10](./ARCHITECTURE.md#210-diagram-10-evidence--verification-flow-mie--provenance) | [Phase 7](./PHASES.md#9-phase-7--player-profile-generation-mie--service-b) | `agent_mie_orchestration` |"""

new_trace_entry = """| **F-E6** | Squad Intelligence & Composition (SICE) | [PRD §5.6](./PRD.md#56-squad-intelligence--composition-sice) | [TRD §8 / §8.4](./TRD.md#8-engine-06--squad-intelligence--composition-engine-sice) | [ARCH §2.8](./ARCHITECTURE.md#28-diagram-8-squad-intelligence--composition-sice-evaluation-flow) | [Phase 8](./PHASES.md#10-phase-8--squad-intelligence--composition-sice--service-e) | `agent_sice` |
| **F-E7** | Player Verification & Research Engine (PVRE) | [PRD §5.6a](./PRD.md) | [TRD §9](./TRD.md#9-engine-07--player-verification--research-engine-pvre) | [ARCH §2.2b–e](./ARCHITECTURE.md#22b-diagram-2b-pvre-dual-mode-mother-controller-architecture) | [Phase 4B](./PHASES.md#7-phase-4b--player-verification--research-engine-pvre-dual-mode) | `agent_pvre` |
| **F-O1** | MIE Orchestration & Unified Report | [PRD §4](./PRD.md#4-user-workflow-primary--revised) | [TRD §2](./TRD.md#2-mother-intelligence-engine-mie--central-orchestrator) | [ARCH §2.2 / §2.10](./ARCHITECTURE.md#210-diagram-10-evidence--verification-flow-mie--provenance) | [Phase 7](./PHASES.md#9-phase-7--player-profile-generation-mie--service-b) | `agent_mie_orchestration` |"""

assert old_trace_entry in content, "Could not find old_trace_entry in docs/README.md"
content = content.replace(old_trace_entry, new_trace_entry, 1)

content = content.replace(
    "| **F-D1** | 31-Entity PostgreSQL Core | [PRD §3.1](./PRD.md#31-strategic-product-objectives) | [TRD §10](./TRD.md#10-central-postgresql-16-database-schema-31-entities) | [ARCH §2.7](./ARCHITECTURE.md#27-diagram-7-central-database-entity-relationship-diagram-31-entities-ddl-mirrored) | [Phase 2](./PHASES.md#4-phase-2--unified-database--player-identity-resolution) | `agent_chief_architect` |",
    "| **F-D1** | 33-Entity PostgreSQL Core | [PRD §3.1](./PRD.md#31-strategic-product-objectives) | [TRD §11](./TRD.md#11-central-postgresql-16-database-schema-33-entities) | [ARCH §2.7](./ARCHITECTURE.md#27-diagram-7-central-database-entity-relationship-diagram-33-entities-ddl-mirrored) | [Phase 2](./PHASES.md#4-phase-2--unified-database--player-identity-resolution) | `agent_chief_architect` |",
    1
)

# 6. Update changelog table at bottom
old_changelog = """| **2.1.0-REMEDIATED** | November 2026 (this cycle) | DDL remediation (expression-unique index; partitioned `deliveries` FKs; composite fielding link; false-claim defaults removed; overs as integer balls; overthrows allowed); `team_season_participation` replaces `seasons.is_suspension`; three-dimension membership + versioned eligibility policies (31 entities); PIRE deterministic tiers + contextual-attribute terminology + calibrated-only confidence; CDCRE dual capabilities (circular dependency removed); `agent_cdcre`; new `DATA_SOURCE_REGISTER.md` (verification statuses; local evidence 2026-11-10; SMAT gap) and `DATA_DICTIONARY.md` (B/W/F/M-series + NOT_COMPUTABLE list); Phase 0 split (0a COMPLETE / 0b OPEN); PRD AC-01…AC-23 + hackathon Top-10 deliverable spec; PROJECT.md reconciled; ERD reconciled 1:1 to DDL (invalid TEAMS→SEASONS edge removed). | **APPROVED RE-REVISION** |"""

new_changelog = """| **2.1.0-REMEDIATED** | November 2026 (earlier) | DDL remediation (expression-unique index; partitioned `deliveries` FKs; composite fielding link; false-claim defaults removed; overs as integer balls; overthrows allowed); `team_season_participation` replaces `seasons.is_suspension`; three-dimension membership + versioned eligibility policies (31 entities); PIRE deterministic tiers + contextual-attribute terminology; CDCRE dual capabilities; new data register and dictionary; AC-01…AC-23. | SUPERSEDED (by 2.2.0) |
| **2.2.0-PVRE-DUAL-MODE** | November 2026 (this cycle) | Introduces **ENGINE 07 — PVRE (Player Verification & Research Engine)**: Mother Controller routing, Mode A (RR Replacement Intelligence: RR history A1 + 2–3 year global window A2 + Replaceability Signals A3), Mode B (Verified Uncapped Domestic Career Discovery), and mandatory `REVIEW_REQUIRED` safety gating. SICE 16 role-aware comparison dimensions (§8.4) with strict separation from hackathon Top-10 uncapped ranking. Establishes **Phase 4B** in `PHASES.md` as the authoritative roadmap with 12 checkpoints and AC-24..AC-30. Aligns documentation across 7 engines, 18 agents, and verified 33-entity PostgreSQL baseline (`player_season_stats`, `player_match_stats` reconciled). | **CURRENT AUTHORITATIVE BASELINE** |"""

assert old_changelog in content, "Could not find old_changelog in docs/README.md"
content = content.replace(old_changelog, new_changelog, 1)

with open('docs/README.md', 'w', encoding='utf-8', newline='\n') as f:
    f.write(content)

print("docs/README.md successfully updated!")
