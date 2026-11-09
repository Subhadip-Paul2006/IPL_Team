## 2026-11-07T07:10:58Z
You are teamwork_spec_miner_1, operating in directory d:\New folder (2)\.agents\teamwork\spec_miner_1.
Your parent orchestrator is conversation ID 4c0891e4-b3cf-43e3-bccd-7c9505cc9188.

MANDATORY INPUTS:
- Read ORIGINAL_REQUEST.md at: d:\New folder (2)\.agents\teamwork\ORIGINAL_REQUEST.md

OBJECTIVE:
Analyze all requirements, specifications, reference data sources, and constraints for the Rajasthan Royals Squad Intelligence & Historical Performance Engine (IPL 2027 Auction Scouting Hackathon).
Enumerate and specify in exhaustive detail:
1. Product and Engineering Scope:
   - Vision, problem statement, target personas (Lead Analyst, Head of Cricket Operations, Auction Strategist, Bowling/Batting Coaches, Chief Executive).
   - Core functional requirements and analytical modules (Match Impact, Venue Profiling, Matchup & Weakness Matrix, Fatigue & Workload, Auction Valuation, Squad Simulation, Scouting Pipeline).
   - Non-functional requirements (query latency, accuracy, deterministic reproducibility, traceability).
2. Document Requirements:
   - Root README.md requirements.
   - PRD.md requirements: user workflows, acceptance criteria, MVP scope, out-of-scope features, hackathon evaluation rubric.
   - PHASES.md requirements: complete breakdown of Phase 0 through Phase 8 (checkpoints, deliverables, verification, status table).
   - AGENTS.md requirements: complete specification for all 14 AI engineering agents (Chief Architect, Cricket Research, Data Source Audit, Dataset Acquisition, Data Normalisation, Player Identity Resolution, Contextual Enrichment, Cricket Statistics, Historical Performance Analysis, Data Quality & Validation, Backend Engineering, Frontend Engineering, Documentation, Testing & QA).
   - AI_INSTRUCTIONS.md requirements: coding conventions, naming standards, data provenance, missing-value rules, statistical guardrails, strict prohibitions.
3. Reference Data Sources Audit & Specification:
   - Cricsheet IPL Dataset, Kaggle 2008-2020, Kaggle 2007-2026 (note 2007 anomaly vs 2008 IPL debut), HawkeyeStats (ball tracking, coordinates, license/provenance caveats), Open-Meteo historical weather (macro environmental data vs stadium pitch moisture caveats), BCCI/IPL/ESPNcricinfo official records.
4. Distinguish implemented vs planned vs unverified features.

BOUNDARIES & CONSTRAINTS:
- You are read-only. DO NOT write or edit source code, tests, or application logic.
- DO NOT download external datasets or run external scripts.
- Write your metadata and reports ONLY inside your working directory: d:\New folder (2)\.agents\teamwork\spec_miner_1\
- Update progress.md regularly with timestamp.

OUTPUT REQUIREMENTS:
Write your comprehensive specification report to:
d:\New folder (2)\.agents\teamwork\spec_miner_1\handoff.md

When complete, send a message to your parent orchestrator (Recipient: 4c0891e4-b3cf-43e3-bccd-7c9505cc9188) using send_message.
