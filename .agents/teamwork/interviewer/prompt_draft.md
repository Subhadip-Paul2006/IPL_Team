Act as a Principal Software Architect, Cricket Data Engineer, Sports Analytics Researcher, Technical Product Manager, and Documentation Engineer to inspect the repository and create a complete, consistent, engineering-grade documentation system and final validation report for the Rajasthan Royals Squad Intelligence & Historical Performance Engine (IPL 2027 Auction Scouting Hackathon).

Working directory: d:\New folder (2)
Integrity mode: demo
The team must NOT: copy text or architecture templates from existing open-source projects for core logic or documentation; run external scripts or delegate execution to other tools.

## Reference Sources
- Cricsheet IPL Dataset: https://cricsheet.org/downloads/ipl.zip (Ball-by-ball records, dismissals, recorded fielding events, match/innings metadata)
- Kaggle IPL Complete Dataset 2008–2020: https://www.kaggle.com/datasets/patrickb1912/ipl-complete-dataset-20082020 (Historical match records, player and team information)
- Kaggle IPL Ball-by-Ball 2007–2026: https://www.kaggle.com/datasets/vedantbhavsar43/ipl-2007-to-2026-complete-ball-by-ball-dataset (Extended ball-by-ball history; verify claimed 2007 coverage vs IPL 2008 start)
- HawkeyeStats: https://github.com/alittlefitness/HawkeyeStats (Third-party ball tracking, delivery speed, pitch coordinates, trajectory; verify provenance, coverage, schema, methodology, and license)
- Historical Weather (Open-Meteo): https://open-meteo.com/en/docs/historical-weather-api (Environmental context: temperature, humidity, dew point, wind, precipitation; not to be claimed as direct stadium pitch moisture)
- Research Sources: BCCI official records, IPL official website, ESPNcricinfo, Cricbuzz, official team announcements, match reports. Respect licenses and access terms.

## Requirements

### R1. Repository Inspection and Greenfield Baseline Documentation
Inspect the workspace at `d:\New folder (2)` before creating documentation. Establish the documentation system from a greenfield baseline, noting that no implementation code currently exists. Clearly distinguish planned features from implemented features, and explicitly mark all unverified facts as TBD, UNVERIFIED, or PLANNED.

### R2. Core Documentation System
Generate the complete documentation suite inside `docs/` with a root `README.md` providing an overview and direct links/index to all documents in `docs/`:
1. `README.md`: Project introduction, hackathon objective, vision, problem statement, proposed solution, system overview, analytical modules, data sources, technology stack (Python, Pandas/NumPy, PostgreSQL, FastAPI, Next.js, Tailwind CSS, React Flow/Cytoscape.js, Recharts/Apache ECharts), repository structure, verified install/execution instructions, current implementation status (greenfield), limitations, roadmap, contribution guidelines, and data attribution/licensing notes.
2. `PRD.md`: Problem statement, target users and stakeholders, product objectives, hackathon-specific objectives, functional and non-functional requirements, user workflows, core use cases, player profile/team intelligence/player comparison/recruitment intelligence/dashboard requirements, MVP scope, out-of-scope features, acceptance criteria, and success metrics.
3. `TRD.md`: Technical architecture (backend, frontend, ingestion, normalisation), central normalised database schema (covering players, player_aliases, teams, competitions, seasons, squad_memberships, matches, innings, deliveries, batting_innings, bowling_spell, fielding_events, venues, pitch_conditions, weather_conditions, player_availability, player_injuries, data_sources, source_records, derived_features with PKs, FKs, and relationships), player identity resolution, match/delivery reconciliation, validation, enrichment, statistical computation, profile generation, API/export specs, logging/error handling, testing, security, and performance.
4. `ARCHITECTURE.md`: Complete system architecture using syntactically valid Mermaid diagrams covering: high-level architecture, data ingestion, raw-to-normalised pipeline, data enrichment, player identity resolution workflow, player analytics workflow, database ERD, player profile generation workflow, candidate evaluation workflow, and dashboard interaction architecture.
5. `PHASES.md`: Implementation roadmap with phases 0 through 8 (Phase 0: Research & Audit, Phase 1: Raw Data Acquisition, Phase 2: Normalisation & Identity Resolution, Phase 3: Contextual Enrichment, Phase 4: Player Profiles, Phase 5: Historical Intelligence Engine, Phase 6: Squad Intelligence, Phase 7: Hackathon Candidate Evaluation, Phase 8: Dashboard & Submission), with checkpoints, tasks, expected outputs, verification methods, and status tables.
6. `AGENTS.md`: Definition of 14 specialised AI engineering agents (Chief Architect, Cricket Research, Data Source Audit, Dataset Acquisition, Data Normalisation, Player Identity Resolution, Contextual Enrichment, Cricket Statistics, Historical Performance Analysis, Data Quality & Validation, Backend Engineering, Frontend Engineering, Documentation, Testing & QA) with responsibilities, authority scope, inputs, outputs, dependencies, restrictions, validation, and handoffs.
7. `AI_INSTRUCTIONS.md`: Central instructions for AI agents covering architectural principles, coding/naming/database conventions, data provenance, statistical correctness rules, missing-value handling (never treat missing as zero, never fabricate statistics, never confuse bowling style with delivery variation, never interpret Hawk-Eye post-shot ball coordinates as fielder coordinates), security, and strict prohibitions.

### R3. Execution Restrictions
DOCUMENTATION GENERATION ONLY. The team must not implement application code, download or modify external datasets, generate fictional player records, create dummy model results, provision infrastructure, or build dashboard UI.

### R4. Final Engineering Verification Report
Produce an executive summary report containing:
1. Files created or updated.
2. Existing documentation preserved.
3. Major architectural decisions.
4. Unverified assumptions.
5. Outstanding research questions.
6. Recommended first implementation phase.
7. Discovered conflicts or missing information.

## Verification Resources
Automated syntax verification (file presence and valid Mermaid syntax linting) and rubric-based validation against Section 9 & 10 criteria.

## Acceptance Criteria

### Documentation Suite Deliverables
- [ ] Root `README.md` exists and links directly to the detailed documentation suite in `docs/`.
- [ ] All 7 core documentation files (`README.md`, `PRD.md`, `TRD.md`, `ARCHITECTURE.md`, `PHASES.md`, `AGENTS.md`, `AI_INSTRUCTIONS.md`) exist in `docs/` and meet all specified structural and content requirements.
- [ ] Final validation report addressing all 7 required points is delivered upon completion.

### Architectural & Schema Completeness
- [ ] All Mermaid diagrams in `ARCHITECTURE.md` (and any other documentation files) render and parse without syntax errors.
- [ ] Database schema in `TRD.md` and ERD in `ARCHITECTURE.md` define all required entities (players, player_aliases, teams, competitions, seasons, squad_memberships, matches, innings, deliveries, batting_innings, bowling_spell, fielding_events, venues, pitch_conditions, weather_conditions, player_availability, player_injuries, data_sources, source_records, derived_features) with primary keys, foreign keys, and explicit relationship cardinalities.
- [ ] Clear distinction between planned, implemented, and deferred features maintained across all documents.

### Constraint Compliance
- [ ] No application code, synthetic player datasets, mock ML models, or external dataset downloads generated in the repository.
- [ ] Cross-document consistency: terms, modules, phases, and agent definitions match across PRD, TRD, ARCHITECTURE, PHASES, AGENTS, and AI_INSTRUCTIONS without contradictions.
