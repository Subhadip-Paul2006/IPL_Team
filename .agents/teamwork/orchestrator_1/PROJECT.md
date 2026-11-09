# Project: Rajasthan Royals Squad Intelligence & Historical Performance Engine (IPL 2027 Auction Scouting Hackathon)

## Architecture
- **Multi-Tier Analytical Architecture**: Client Presentation (Next.js 15, Tailwind, ECharts, React Flow) <-> REST API & Service Layer (FastAPI, Pydantic v2, Redis) <-> Analytics & Tactical Simulation Engine (Python, Pandas, NumPy) <-> Central Normalized Relational Core (PostgreSQL 16, 20 Entities) <-> Ingestion & Contextual Enrichment Pipeline (CricSheet JSON v1.3.0/YAML v0.94, Kaggle Historicals, Open-Meteo Weather, HawkeyeStats Tracking).
- **Core Principles**: Deterministic reproducibility, strict 3NF database schema, zero statistical fabrication, strict distinction between planned features vs greenfield baseline, ODC-By v1.0 data provenance.

## Feature Inventory
| # | Feature | Category | Description | Assigned Milestone | Source |
|---|---------|----------|-------------|-------------------|--------|
| F01 | Ball-by-Ball Context Valuation | Match Impact | True Strike Rate & True Economy vs Phase Pars | M1, M2 | Cricsheet delivery schema & Survey |
| F02 | Win Probability Added (WPA) & xR | Match Impact | State-based Win Probability model evaluating delta WP per delivery | M1, M2 | Cricsheet innings outcome & Survey |
| F03 | Clutch Index & Leverage Analysis | Match Impact | High-pressure performance rating (Leverage Index > 1.5) | M1, M2 | Cricsheet stage metadata & Survey |
| F04 | Pitch & Ground Behavioral Profiling | Venue Profiling | Pitch soil/bounce classification & boundary geometry modeling | M1, M2 | Venue records & Survey |
| F05 | SMS Jaipur Engine | Venue Profiling | Sawai Mansingh Stadium home ground analytics (dew, boundary dimensions) | M1, M2 | RR home venue spec & Survey |
| F06 | Environmental & Dew Factor Correlation | Venue Profiling | Open-Meteo macro-weather integration for dew impact modeling | M1, M2 | Open-Meteo API spec & Survey |
| F07 | Batter vs Bowling Type Profiling | Tactical Matrix | Proficiency vs 6 bowling archetypes (RAF, LAF, OS, SLA, LBG, LAC) | M1, M2 | CricSheet deliveries & Survey |
| F08 | Head-to-Head Batter vs Bowler Matrix | Tactical Matrix | Granular historical matchup analysis between individual players | M1, M2 | CricSheet delivery fields & Survey |
| F09 | Pitch Trajectory & Length Vulnerability | Tactical Matrix | Scoring heatmaps by delivery line/length via Hawkeye tracking | M1, M2 | HawkeyeStats spec & Survey |
| F10 | Multi-Format Workload Engine | Workload & Fatigue | Cumulative overs bowled & spells across IPL, SMA, T20 WC, The Hundred | M1, M2 | Multi-tournament datasets & Survey |
| F11 | Schedule Congestion & Travel Strain | Workload & Fatigue | Performance degradation from compressed rest intervals (<48h) and transit | M1, M2 | Match schedule dates & Survey |
| F12 | Injury History & Availability Logging | Workload & Fatigue | Medical downtime, injury risk tiers, and national duty NOC restrictions | M1, M2 | TRD schema & Survey |
| F13 | Expected Auction Price (EAP) Modeling | Auction Valuation | Predictive valuation modeling estimating market clearing price at IPL 2027 Auction | M1, M2 | Auction Strategist spec & Survey |
| F14 | Replacement Player Value (WAR/VORP) | Auction Valuation | Value Over Replacement Player adapted for T20 cricket | M1, M2 | Sabermetric principles & Survey |
| F15 | Role Scarcity & Premium Multipliers | Auction Valuation | Market scarcity premiums for rare archetypes (pace all-rounders, death finishers) | M1, M2 | Historical IPL auction data & Survey |
| F16 | Playing XI Optimizer | Squad Simulation | Lineup optimization enforcing IPL regulatory constraints (max 4 overseas, 1 WK) | M1, M2 | IPL Playing Conditions & Survey |
| F17 | Impact Player Deployment Engine | Squad Simulation | Tactical decision engine for optimal Impact Player substitutions | M1, M2 | CricSheet replacement schema & Survey |
| F18 | Monte Carlo Tournament Simulator | Squad Simulation | 10,000-run campaign simulation projecting playoff qualification probability | M1, M2 | NFR spec & Survey |
| F19 | Cross-Competition Normalisation | Talent Scouting | Equivalency modeling calibrating SMA / U-19 / The Hundred stats to IPL tier | M1, M2 | CricSheet domestic data & Survey |
| F20 | Diamond-in-the-Rough Scouting Filter | Talent Scouting | Micro-skill detection filtering undervalued domestic talent (age <= 24) | M1, M2 | RR Hackathon mandate & Survey |
| F21 | Multi-Source Player Identity Resolution | Core Data | Disambiguation mapping aliases to canonical IDs using CricSheet hex hashes | M1, M2 | CricSheet people registry & Survey |
| F22 | Multi-Format Ingestion Engine | Data Ingestion | Streaming parsers for JSON v1.3.0 and YAML v0.94 with SHA-256 staging | M2 | CricSheet multi-format data & Survey |
| F23 | DLS Par & Revised Target Reconciler | Data Ingestion | Rain-affected match delivery adjustment against DLS revised targets | M1, M2 | CricSheet DLS schema & Survey |
| F24 | Super Over Isolation & Accounting | Core Data | Segregation of Super Over deliveries from career aggregates | M1, M2 | ICC/BCCI rules & Survey |
| F25 | Central 20-Entity PostgreSQL Schema | Architecture | Full DDL covering all required entities with PKs, FKs, indexes, constraints | M2 | ORIGINAL_REQUEST.md & Survey |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Product, Process & Agent Specifications | Author `docs/PRD.md`, `docs/PHASES.md`, `docs/AGENTS.md`, `docs/AI_INSTRUCTIONS.md` | Survey Complete | IN_PROGRESS |
| M2 | Technical Architecture & Database Schema | Author `docs/TRD.md` and `docs/ARCHITECTURE.md` (with 10 Mermaid diagrams) | Survey Complete | IN_PROGRESS |
| M3 | Repository Overview & Navigation Hub | Author root `README.md` and `docs/README.md` | M1, M2 | PLANNED |
| M4 | Verification, Audit & Final Report | Reviewer approval, Challenger empirical verification, Forensic Audit, Final Report | M1, M2, M3 | PLANNED |

## Code Layout
```
d:\New folder (2)\
├── .agents/                          # AI Orchestration & Metadata
│   └── teamwork/                     # Briefings, progress tracking, dispatches, handoffs
├── CricSheet/                        # [IMMUTABLE READ-ONLY CACHE] Raw Cricket Match Datasets
│   ├── hnd_json/                     # The Hundred
│   ├── icc_mens_cricket_world_cup/   # ODI World Cup
│   ├── icc_mens_t20_world_cup_json/  # T20 World Cup
│   ├── ipl_json/                     # IPL 2008-2026
│   └── sma/                          # Syed Mushtaq Ali Trophy
├── docs/                             # Engineering Documentation Suite
│   ├── README.md                     # Documentation Index & Cross-Reference Hub
│   ├── PRD.md                        # Product Requirements Document
│   ├── TRD.md                        # Technical Requirements & Database Schema Spec
│   ├── ARCHITECTURE.md               # System Architecture & 10 Mermaid Diagrams
│   ├── PHASES.md                     # 9-Phase Implementation Roadmap (Phases 0-8)
│   ├── AGENTS.md                     # 14 Specialised AI Agent Specifications
│   └── AI_INSTRUCTIONS.md            # AI Architectural Principles & Domain Guardrails
└── README.md                         # Project Root Overview, Architecture & Evaluation Index
```
