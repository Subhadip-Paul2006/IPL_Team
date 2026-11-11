import re

with open('PROJECT.md', 'r', encoding='utf-8') as f:
    content = f.read().replace('\r\n', '\n')

# 1. Update Notice
old_notice = """> ⚠️ **SUPERSEDED-V1 NOTICE**: This file previously carried the **v1.0.0** "Historical
> Performance Engine" specification (Next.js 15 / FastAPI / Redis presentation-and-service
> stack, 20-entity schema, F01–F25 auction-war-room feature inventory, `CricSheet/` data
> path). **That architecture is no longer the project architecture.** This file has been
> reconciled (v2.1.0) to the current charter. The superseded v1 content is preserved for
> audit at the end of this file under "Appendix A — Historical v1.0.0 Specification
> (superseded)". Authoritative current documents: `README.md`, `docs/PRD.md`,
> `docs/TRD.md`, `docs/ARCHITECTURE.md`, `docs/PHASES.md`, `docs/AGENTS.md`,
> `docs/AI_INSTRUCTIONS.md`, `docs/DATA_SOURCE_REGISTER.md`, `docs/DATA_DICTIONARY.md`.

## Architecture (current, v2.1.0)"""

new_notice = """> ⚠️ **SUPERSEDED-V1 NOTICE**: This file previously carried the **v1.0.0** "Historical
> Performance Engine" specification (Next.js 15 / FastAPI / Redis presentation-and-service
> stack, 20-entity schema, F01–F25 auction-war-room feature inventory, `CricSheet/` data
> path). **That architecture is no longer the project architecture.** This file has been
> reconciled (v2.2.0) to the current charter. The superseded v1 content is preserved for
> audit at the end of this file under "Appendix A — Historical v1.0.0 Specification
> (superseded)". Authoritative current documents: `README.md`, `docs/PRD.md`,
> `docs/TRD.md`, `docs/ARCHITECTURE.md`, `docs/PHASES.md`, `docs/AGENTS.md`,
> `docs/AI_INSTRUCTIONS.md`, `docs/DATA_SOURCE_REGISTER.md`, `docs/DATA_DICTIONARY.md`, `docs/RANKING_SPEC.md`.

## Architecture (current, v2.2.0)"""

assert old_notice in content, "Could not find old_notice in PROJECT.md"
content = content.replace(old_notice, new_notice, 1)

# 2. Update Architecture bullets
old_arch_bullets = """- **Mother Intelligence Engine (MIE)**: central orchestrator — coordinates the six
  specialised engines, merges verified outputs, tracks verification status and source
  provenance, returns structured reports. MIE never invents statistics, identities,
  memberships, or eligibility decisions.
- **Six specialised engines**: PIRE (identity) · TMVE (membership verification) · CDCRE
  (career discovery, dual capability) · CPPAE (performance analytics) · CMIE (contextual
  match intelligence) · SICE (squad intelligence & composition).
- **Five support services**: A. Data Ingestion · B. Player Profile Generator ·
  C. Source Verification & Provenance · D. Data Quality & Coverage · E. Team Builder.
- **Normalised 31-entity PostgreSQL 16 core** (3NF core; `derived_features` the single
  documented non-3NF exception; season-partitioned `deliveries` with enforced
  partitioned-table FKs on PG ≥ 15)."""

new_arch_bullets = """- **Mother Intelligence Engine (MIE)**: central orchestrator — coordinates the seven
  specialised engines, merges verified outputs, tracks verification status and source
  provenance, returns structured reports. MIE never invents statistics, identities,
  memberships, or eligibility decisions.
- **Seven specialised engines**: PIRE (identity) · TMVE (membership verification) · CDCRE
  (career discovery, dual capability) · CPPAE (performance analytics) · CMIE (contextual
  match intelligence) · SICE (squad intelligence & composition) · PVRE (player verification & research engine).
- **Support services**: A. Data Ingestion · B. Player Profile Generator ·
  C. Source Verification & Provenance · D. Data Quality & Coverage · E. Team Builder.
- **Normalised 33-entity PostgreSQL 16 core** (3NF core; `derived_features` the single
  documented non-3NF exception; season-partitioned `deliveries` with enforced
  partitioned-table FKs on PG ≥ 15; includes `player_season_stats` and `player_match_stats`)."""

assert old_arch_bullets in content, "Could not find old_arch_bullets in PROJECT.md"
content = content.replace(old_arch_bullets, new_arch_bullets, 1)

# 3. Update Feature & Component Inventory Table
old_c6_c9 = """| C6 | SICE | Engine 06 | Squad role/depth/balance analysis; labelled analytical recommendations; hackathon ranking support | 8 | TRD §8 | `[STATUS: PLANNED]` |
| C7 | MIE | Orchestrator | Candidate-discovery-first sequence; merges outputs; verification tracking; provenance assembly | 7 | TRD §2 | `[STATUS: PLANNED]` |
| C8 | Services A–E | Support | Ingestion · profile export · provenance · quality/coverage · team builder | 1/7/4/1/8 | TRD §9 | `[STATUS: PLANNED]` |
| C9 | 31-entity DDL | Data | Remediated PostgreSQL 16 core (design decisions D1–D10) | 2 | TRD §10 | `[STATUS: PLANNED]` |"""

new_c6_c9 = """| C6 | SICE | Engine 06 | Squad role/depth/balance analysis; 16-dimension replacement comparison (§8.4); labelled analytical recommendations; hackathon ranking support | 8 | TRD §8 | `[STATUS: PLANNED]` |
| C6b | PVRE | Engine 07 | Dual-mode player research & replacement intelligence (Mode A: RR replacement; Mode B: uncapped domestic discovery; REVIEW_REQUIRED safety) | 4B | TRD §9 | `[STATUS: PLANNED - MVP]` |
| C7 | MIE | Orchestrator | Candidate-discovery-first sequence; merges outputs; verification tracking; provenance assembly | 7 | TRD §2 | `[STATUS: PLANNED]` |
| C8 | Services A–E | Support | Ingestion · profile export · provenance · quality/coverage · team builder | 1/7/4/1/8 | TRD §10 | `[STATUS: PLANNED]` |
| C9 | 33-entity DDL | Data | Verified PostgreSQL 16 core (design decisions D1–D10 + entity reconciliation) | 2 | TRD §11 | `[STATUS: PLANNED]` |"""

assert old_c6_c9 in content, "Could not find old_c6_c9 in PROJECT.md"
content = content.replace(old_c6_c9, new_c6_c9, 1)

# 4. Update Roadmap
old_roadmap = """## Roadmap
Phases 0a/0b → 1–10 per [`docs/PHASES.md`](docs/PHASES.md). **Phase 0a COMPLETE; Phase 0b
OPEN (PARTIALLY_COMPLETE)**; Phases 1–10 PLANNED."""

new_roadmap = """## Roadmap
Phases 0a/0b → 1–4 → 4B (PVRE) → 5–10 per [`docs/PHASES.md`](docs/PHASES.md). **Phase 0a COMPLETE; Phase 0b
OPEN (PARTIALLY_COMPLETE)**; Phase 4B `[PLANNED - MVP]`; Phases 1–10 PLANNED."""

assert old_roadmap in content, "Could not find old_roadmap in PROJECT.md"
content = content.replace(old_roadmap, new_roadmap, 1)

# 5. Update docs count in Repository Layout
old_repo_docs = """├── docs/                                # Authoritative documentation suite (9 documents)
│   ├── README.md · PRD.md · TRD.md · ARCHITECTURE.md · PHASES.md
│   ├── AGENTS.md · AI_INSTRUCTIONS.md
│   ├── DATA_SOURCE_REGISTER.md · DATA_DICTIONARY.md"""

new_repo_docs = """├── docs/                                # Authoritative documentation suite (10 documents)
│   ├── README.md · PRD.md · TRD.md · ARCHITECTURE.md · PHASES.md
│   ├── AGENTS.md · AI_INSTRUCTIONS.md
│   ├── DATA_SOURCE_REGISTER.md · DATA_DICTIONARY.md · RANKING_SPEC.md"""

assert old_repo_docs in content, "Could not find old_repo_docs in PROJECT.md"
content = content.replace(old_repo_docs, new_repo_docs, 1)

with open('PROJECT.md', 'w', encoding='utf-8', newline='\n') as f:
    f.write(content)

print("PROJECT.md successfully updated!")
