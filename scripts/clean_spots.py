with open('docs/TRD.md', 'r', encoding='utf-8') as f:
    trd = f.read()

trd = trd.replace('- Coordinate the six specialised engines in the correct dependency order.',
                  '- Coordinate the seven specialised engines in the correct dependency order.', 1)

with open('docs/TRD.md', 'w', encoding='utf-8', newline='\n') as f:
    f.write(trd)
print("docs/TRD.md cleaned")

with open('README.md', 'r', encoding='utf-8') as f:
    rm = f.read()

rm = rm.replace('| [`docs/AGENTS.md`](docs/AGENTS.md) | 16 specialised agent contracts mapped to MIE, the six engines, five services, delivery & QA. |',
                '| [`docs/AGENTS.md`](docs/AGENTS.md) | 18 specialised agent contracts mapped to MIE, the seven engines, support services, delivery & QA. |', 1)
rm = rm.replace('[STATUS: PLANNED]   Phase 2 — Unified Database & Player Identity Resolution (31-entity DDL + PIRE)',
                '[STATUS: PLANNED]   Phase 2 — Unified Database & Player Identity Resolution (33-entity DDL + PIRE)', 1)

with open('README.md', 'w', encoding='utf-8', newline='\n') as f:
    f.write(rm)
print("README.md cleaned")

with open('PROJECT.md', 'r', encoding='utf-8') as f:
    proj = f.read()

proj = proj.replace('2. *Normalised 3NF relational core* — 31 entities, hard foreign keys, expression',
                    '2. *Normalised 3NF relational core* — 33 entities, hard foreign keys, expression', 1)

with open('PROJECT.md', 'w', encoding='utf-8', newline='\n') as f:
    f.write(proj)
print("PROJECT.md cleaned")

with open('docs/AI_INSTRUCTIONS.md', 'r', encoding='utf-8') as f:
    ai = f.read()

ai = ai.replace('> (MIE + six engines + five services). It adds mandatory guardrails for',
                '> (MIE + seven engines + support services). It adds mandatory guardrails for', 1)
ai = ai.replace('| Database Core     | PostgreSQL                          | 16.0+ (3NF, 31 entities)                |',
                '| Database Core     | PostgreSQL                          | 16.0+ (3NF, 33 entities)                |', 1)
ai = ai.replace('deterministic reproducibility, a normalised 31-entity 3NF core (with `derived_features` as the',
                'deterministic reproducibility, a normalised 33-entity 3NF core (with `derived_features` as the', 1)

with open('docs/AI_INSTRUCTIONS.md', 'w', encoding='utf-8', newline='\n') as f:
    f.write(ai)
print("docs/AI_INSTRUCTIONS.md cleaned")

with open('docs/README.md', 'r', encoding='utf-8') as f:
    d_rm = f.read()

d_rm = d_rm.replace('|                    ingestion/provenance, analytics, 31-entity ERD (DDL-mirrored), SICE flow,',
                    '|                    ingestion/provenance, analytics, 33-entity ERD (DDL-mirrored), SICE flow,', 1)
d_rm = d_rm.replace('| [**`ARCHITECTURE.md`**](./ARCHITECTURE.md) | **System Architecture Specification**<br>*(10 Mermaid Diagrams + 7 ADRs)*',
                    '| [**`ARCHITECTURE.md`**](./ARCHITECTURE.md) | **System Architecture Specification**<br>*(14 Mermaid Diagrams + 8 ADRs)*', 1)
d_rm = d_rm.replace('| [**`AGENTS.md`**](./AGENTS.md) | **Multi-Agent Operating Constitution**<br>*(16 Agent Contracts)*',
                    '| [**`AGENTS.md`**](./AGENTS.md) | **Multi-Agent Operating Constitution**<br>*(18 Agent Contracts)*', 1)
d_rm = d_rm.replace('2. [`TRD.md §10`](./TRD.md#10-central-postgresql-16-database-schema-31-entities) — 31-entity DDL',
                    '2. [`TRD.md §11`](./TRD.md#11-central-postgresql-16-database-schema-33-entities) — 33-entity DDL', 1)
d_rm = d_rm.replace('2. **Normalised 3NF 31-entity relational core** with canonical `player_id` everywhere',
                    '2. **Normalised 3NF 33-entity relational core** with canonical `player_id` everywhere', 1)

with open('docs/README.md', 'w', encoding='utf-8', newline='\n') as f:
    f.write(d_rm)
print("docs/README.md cleaned")

with open('docs/PRD.md', 'r', encoding='utf-8') as f:
    prd = f.read()

prd = prd.replace('• CMIE (FR-X*) · SICE (FR-S1-S4) · Services A-E (FR-V*) · 31-entity core · Streamlit 11 views',
                  '• CMIE (FR-X*) · SICE (FR-S1-S4) · PVRE (FR-PV1-8) · Services A-E (FR-V*) · 33-entity core · Streamlit 11 views', 1)

with open('docs/PRD.md', 'w', encoding='utf-8', newline='\n') as f:
    f.write(prd)
print("docs/PRD.md cleaned")

with open('docs/PHASES.md', 'r', encoding='utf-8') as f:
    ph = f.read()

ph = ph.replace('| [PHASE 2: UNIFIED DATABASE & PIRE]  31-entity DDL, PIRE deterministic tiers  (PLANNED - MVP)',
                '| [PHASE 2: UNIFIED DATABASE & PIRE]  33-entity DDL, PIRE deterministic tiers  (PLANNED - MVP)', 1)
ph = ph.replace('31-entity DDL passing the available SQL parse (see audit report §14).',
                '33-entity DDL passing the available SQL parse (see audit report §14 and TRD §11.5).', 1)
ph = ph.replace('- **Objectives**: execute the **31-entity** DDL (migration gates: expression index on',
                '- **Objectives**: execute the **33-entity** DDL (migration gates: expression index on', 1)
ph = ph.replace('reserve generation · dossier assembly (evidence tiers) · AC-01…AC-23 regression ·',
                'reserve generation · dossier assembly (evidence tiers) · AC-01…AC-30 regression ·', 1)

with open('docs/PHASES.md', 'w', encoding='utf-8', newline='\n') as f:
    f.write(ph)
print("docs/PHASES.md cleaned")
