import os

with open('docs/ARCHITECTURE.md', 'r', encoding='utf-8') as f:
    text = f.read().replace('\r\n', '\n')

# 1. Update header
old_hdr = '''**Document Version**: 2.1.1-TARGETED-REMEDIATION
**Status**: [STATUS: PLANNED - GREENFIELD BASELINE]
**Author**: Engineering Architecture Team (`teamwork_worker_2`)

> **Revision Note (v2.1.1, targeted remediation)**: The data model is now **33 entities** —'''

new_hdr = '''**Document Version**: 2.2.0
**Status**: [STATUS: PLANNED - GREENFIELD BASELINE]
**Author**: Engineering Architecture Team (`teamwork_worker_2`)

> **Revision Note (v2.2.0, PVRE Dual-Mode Research Architecture)**: Updated architecture from
> six to seven specialised engines (Engine 07: PVRE). Added PVRE dual-mode orchestration diagrams
> (Diagram 2b, Diagram 2c Mode A, Diagram 2d Mode B, Diagram 2e REVIEW_REQUIRED flow). Updated
> high-level architecture diagram and SICE evaluation diagram. Added ADR-008: PVRE Dual-Mode
> Player Verification, Research Routing & REVIEW_REQUIRED Safety Boundary. Reconciled all entity
> mentions to 33 entities across the document suite.
>
> **Revision Note (v2.1.1, targeted remediation, retained for history)**: The data model is now **33 entities** —'''

assert old_hdr in text
text = text.replace(old_hdr, new_hdr)

# 2. Section 1 principles
old_p1 = '1. **Central Orchestration (MIE)**: coordinates the six engines, merges outputs, tracks'
new_p1 = '1. **Central Orchestration (MIE)**: coordinates the seven engines, merges outputs, tracks'
assert old_p1 in text
text = text.replace(old_p1, new_p1)

# 3. Diagram 1
old_engines_subgraph = '''    subgraph Engines["Six Specialised Engines"]
        PIRE["ENGINE 01: PIRE - Identity Resolution"]
        TMVE["ENGINE 02: TMVE - Membership Verification"]
        CDCRE["ENGINE 03: CDCRE - Candidate + Career Discovery"]
        CPPAE["ENGINE 04: CPPAE - Performance Analytics"]
        CMIE["ENGINE 05: CMIE - Contextual Match Intelligence"]
        SICE["ENGINE 06: SICE - Squad Intelligence & Composition"]
    end'''

new_engines_subgraph = '''    subgraph Engines["Seven Specialised Engines"]
        PIRE["ENGINE 01: PIRE - Identity Resolution"]
        TMVE["ENGINE 02: TMVE - Membership Verification"]
        CDCRE["ENGINE 03: CDCRE - Candidate + Career Discovery"]
        CPPAE["ENGINE 04: CPPAE - Performance Analytics"]
        CMIE["ENGINE 05: CMIE - Contextual Match Intelligence"]
        SICE["ENGINE 06: SICE - Squad Intelligence & Composition"]
        PVRE["ENGINE 07: PVRE - Player Verification & Research Engine"]
    end'''

assert old_engines_subgraph in text
text = text.replace(old_engines_subgraph, new_engines_subgraph)

# Add PVRE connections in Diagram 1
old_conn = '    MIE_Orchestrator --> SICE'
new_conn = '''    MIE_Orchestrator --> SICE
    MIE_Orchestrator --> PVRE
    PVRE --> PIRE
    PVRE --> TMVE
    PVRE --> CDCRE
    PVRE --> SICE'''
assert old_conn in text
text = text.replace(old_conn, new_conn)

# 4. Add Diagram 2b, 2c, 2d, 2e after Diagram 2
d2_marker = '### 2.3 Diagram 3: Player Identity Resolution (PIRE) Workflow — revised terminology'
assert d2_marker in text

pvre_diagrams = '''### 2.2b Diagram 2b: PVRE Dual-Mode Orchestration Architecture

```mermaid
flowchart TD
    subgraph Input["PVRE Input Stage"]
        REQ["PVRERequestContract(query, target_season, eval_date, window)"]
    end

    subgraph Controller["PVRE Mother Controller (Engine 07)"]
        MC_Entry["Mother Controller Entry Point"]
        MC_CDCRE["CDCRE Capability 1: Candidate Discovery"]
        MC_PIRE["PIRE: Identity Resolution & Disambiguation"]
        MC_TMVE["TMVE: Dimensions 1 & 2 (RR Relationship & Currency)"]
        MC_EPS["Eligibility Policy Service: Dimension 3 (IPL Eligibility)"]
        MC_Classifier{"Request Classifier & Waterfall Router"}
    end

    subgraph Modes["PVRE Execution Modes"]
        MODE_A["Mode A: Existing RR Player Replacement Intelligence"]
        MODE_B["Mode B: Verified Uncapped Candidate Intelligence"]
        MODE_REV["Mandatory REVIEW_REQUIRED Safety State"]
        MODE_OOS["Out-of-Scope Notice (Non-RR Capped Player)"]
    end

    subgraph Downstream["Downstream Engines & Storage"]
        CPPAE["ENGINE 04: CPPAE (Performance Metrics)"]
        CMIE["ENGINE 05: CMIE (Contextual Conditions)"]
        SICE["ENGINE 06: SICE (Incumbent-vs-Candidate Comparison)"]
        DB[("PostgreSQL 16 Database (33 Entities)")]
    end

    REQ --> MC_Entry
    MC_Entry --> MC_CDCRE
    MC_CDCRE --> MC_PIRE
    MC_PIRE --> MC_TMVE
    MC_TMVE --> MC_EPS
    MC_EPS --> MC_Classifier

    MC_Classifier -->|"Verified RR Incumbent"| MODE_A
    MC_Classifier -->|"Verified Uncapped Non-RR"| MODE_B
    MC_Classifier -->|"Conflict / Incomplete Evidence"| MODE_REV
    MC_Classifier -->|"Verified Non-RR Capped"| MODE_OOS

    MODE_A --> CPPAE
    MODE_A --> CMIE
    MODE_A --> SICE
    MODE_B --> CPPAE
    MODE_B --> DB
    MODE_REV --> DB
```

### 2.2c Diagram 2c: Mode A Replacement Intelligence Flow

```mermaid
flowchart TD
    subgraph Trigger["Mode A Trigger"]
        INC["Verified RR Incumbent (CURRENT_RR / HISTORICAL_RR_APPEARED / SQUAD_ONLY)"]
    end

    subgraph ModA1["Module A1: RR Historical Research"]
        A1_Squad["Documented Squad Memberships by Season"]
        A1_App["Actual Match Appearances (Scorecards)"]
        A1_BatBowl["Season-wise Batting & Bowling Metrics"]
        A1_Field["Fielding & Wicketkeeping Events"]
        A1_Roles["Role Changes & Tactical Evolution"]
    end

    subgraph ModA2["Module A2: Recent Global Performance Research"]
        A2_Win["2-to-3 Year Configurable Evaluation Window"]
        A2_Leagues["Global Competitions: BBL, PSL, CPL, SA20, The Hundred, Intl, Domestic"]
        A2_Stats["Format-Tagged Performance Profiles with Sample Sizes"]
        A2_Injur["Verified Injury & Availability Records"]
        A2_Gaps["Participation Continuity & Gap Tracking"]
    end

    subgraph ModA3["Module A3: Replaceability Evidence Assessment"]
        A3_Synth["Trajectory & Role Importance Synthesis"]
        A3_Sig{"Assessment Signal Generator"}
        SIG_RETAIN["RETAIN_SIGNAL"]
        SIG_MONITOR["MONITOR_SIGNAL"]
        SIG_REPLACE["POTENTIALLY_REPLACEABLE"]
        SIG_INSUFF["INSUFFICIENT_EVIDENCE"]
        SIG_REVIEW["REVIEW_REQUIRED"]
    end

    subgraph SICE_Comp["SICE Replacement Evaluation (§8.4)"]
        SICE_16["16-Dimension Role-Aware Comparison"]
        SICE_Out["ANALYTICAL_RETAIN / MONITOR / REPLACEMENT_CANDIDATE"]
    end

    INC --> ModA1
    INC --> ModA2
    ModA1 --> ModA3
    ModA2 --> ModA3
    A3_Synth --> A3_Sig
    A3_Sig --> SIG_RETAIN
    A3_Sig --> SIG_MONITOR
    A3_Sig --> SIG_REPLACE
    A3_Sig --> SIG_INSUFF
    A3_Sig --> SIG_REVIEW
    A3_Sig --> SICE_Comp
```

### 2.2d Diagram 2d: Mode B Uncapped Candidate Intelligence Flow

```mermaid
flowchart TD
    subgraph TriggerB["Mode B Trigger"]
        CAND["Player with NO_VERIFIED_RR_RELATIONSHIP & VERIFIED_ELIGIBLE"]
    end

    subgraph Discovery["Comprehensive Domestic Career Discovery"]
        DOM_Ranji["Ranji Trophy (First-Class Red-Ball)"]
        DOM_SMAT["Syed Mushtaq Ali Trophy (SMAT T20)"]
        DOM_VHT["Vijay Hazare Trophy (List A 50-Over)"]
        DOM_Duleep["Duleep & Premier BCCI Tournaments"]
        DOM_Age["Age-Group BCCI (U19 Vinoo Mankad / U23 CK Nayudu)"]
        DOM_Leagues["Other Franchise Leagues & Global Records"]
    end

    subgraph Verification["Verification & Coverage Gate"]
        COV["Four-State Coverage Tracking"]
        EPS_Gate["Policy Verification: Zero Senior International Caps"]
        ABS_Check{"Database Absence Check"}
        AFFIRM["Affirmative Proof Established"]
        NO_AFFIRM["Unverified → NOT_ASSESSED"]
    end

    subgraph Pool["Verified Uncapped Pool"]
        UN_POOL["Verified Uncapped Candidate Pool"]
        SICE_B["SICE Squad Integration & Top-10 Ranking Deliverable"]
    end

    CAND --> Discovery
    Discovery --> COV
    COV --> EPS_Gate
    EPS_Gate --> ABS_Check
    ABS_Check -->|"Affirmative Evidence"| AFFIRM
    ABS_Check -->|"Missing Evidence"| NO_AFFIRM
    AFFIRM --> UN_POOL
    UN_POOL --> SICE_B
```

### 2.2e Diagram 2e: Mandatory REVIEW_REQUIRED Safety Flow

```mermaid
flowchart TD
    subgraph Triggers["Safety Trigger Conditions"]
        T1["Multiple Identities / Ambiguity"]
        T2["DOB / Attribute Conflicts"]
        T3["Contradictory RR Relationship Evidence"]
        T4["Unverified IPL Eligibility"]
        T5["Material Source Discrepancies"]
        T6["Incomplete Global / Domestic Sample"]
    end

    subgraph SafetyGate["PVRE Safety Interceptor"]
        INTERCEPT["Intercept Request / Halt Automated Routing"]
        DOSSIER["Compile Structured Review Dossier"]
    end

    subgraph DossierOutput["Review Dossier Attributes"]
        R_Status["review_status = REVIEW_REQUIRED"]
        R_Codes["review_reason_codes"]
        R_Claims["unresolved_claims"]
        R_Src["conflicting_source_ids"]
        R_Miss["missing_evidence"]
        R_Checks["recommended_manual_checks"]
    end

    subgraph Outcome["Safety Outcomes"]
        BLOCK["Block Automated Candidate Pool Entry"]
        ALERT["Alert Human Cricket Analyst / Operations Lead"]
        RESOLVE["Manual Review / Resolution via UI View 11"]
    end

    T1 --> INTERCEPT
    T2 --> INTERCEPT
    T3 --> INTERCEPT
    T4 --> INTERCEPT
    T5 --> INTERCEPT
    T6 --> INTERCEPT

    INTERCEPT --> DOSSIER
    DOSSIER --> R_Status
    DOSSIER --> R_Codes
    DOSSIER --> R_Claims
    DOSSIER --> R_Src
    DOSSIER --> R_Miss
    DOSSIER --> R_Checks

    DOSSIER --> BLOCK
    DOSSIER --> ALERT
    ALERT --> RESOLVE
```

'''

text = text[:text.find(d2_marker)] + pvre_diagrams + text[text.find(d2_marker):]

# 5. Add ADR-008 in Section 3
adr_end = text.find('## 4. Verification & Architecture Integrity')
assert adr_end != -1

adr_008_text = '''### ADR-008: PVRE Dual-Mode Player Verification, Research Routing & REVIEW_REQUIRED Safety Boundary

- **Context**: In v2.1.1, the platform resolved player identities (PIRE), verified franchise
  membership (TMVE), discovered careers (CDCRE), and performed squad analysis (SICE), but lacked
  a dedicated controller to systematically evaluate incumbent Rajasthan Royals players for
  potential replacement by younger uncapped prospects, or to orchestrate deep domestic career
  discovery for uncapped talent. Furthermore, unverified or conflicting identity and eligibility
  claims lacked a unified, non-bypassable safety state, risking automated decision errors.
- **Decision**: Introduce **ENGINE 07 — Player Verification & Research Engine (PVRE)**
  orchestrated by the Mother Intelligence Engine (MIE). PVRE implements:
  1. A central Mother Controller governing deterministic 7-step routing precedence.
  2. **Mode A (Existing RR Player Replacement Intelligence)**: Dual-scope research investigating
     complete RR historical performance (distinguishing squad inclusion from actual appearances)
     and recent 2-to-3 year global performance outside RR across recognised competitions (BBL,
     PSL, CPL, SA20, The Hundred, Intl, domestic). Generates structured analytical signals
     (`RETAIN_SIGNAL`, `MONITOR_SIGNAL`, `POTENTIALLY_REPLACEABLE`, `INSUFFICIENT_EVIDENCE`,
     `REVIEW_REQUIRED`) forwarded to SICE.
  3. **Mode B (Verified Uncapped Candidate Intelligence)**: Complete career discovery across
     Ranji Trophy, SMAT, VHT, Duleep, and age-group competitions; enforces affirmative
     eligibility verification under the active target-season policy.
  4. **Mandatory `REVIEW_REQUIRED` Safety Boundary**: Non-bypassable safety pathway triggered
     on identity ambiguity, attribute conflict, contradictory RR evidence, unverified eligibility,
     or coverage gaps; compiles structured review dossiers with reason codes, unresolved claims,
     conflicting source IDs, and recommended manual checks; strictly blocks unverified players
     from entering the uncapped ranking pool.
  5. **Role-Aware SICE Replacement Evaluation**: SICE evaluates incumbent replacement trade-offs
     across 16 specified dimensions; keeps the hackathon Top-10 ranking deliverable strictly
     separate.
- **Consequences**:
  - *Positive*: Rigorous separation between incumbent evaluation and uncapped candidate discovery;
    deterministic routing; complete provenance tracking; zero silent classification errors.
  - *Trade-offs*: Additional coordination layer managed by MIE; requires strict adherence to
    typed contracts and manual review workflows for flagged records.

---

'''

text = text[:adr_end] + adr_008_text + text[adr_end:]

with open('docs/ARCHITECTURE.md', 'w', encoding='utf-8', newline='\n') as f:
    f.write(text)

print('docs/ARCHITECTURE.md successfully updated and written!')
