import re

def audit_details():
    # 1. Check DATA_SOURCE_REGISTER.md for R3 requirements
    with open('docs/DATA_SOURCE_REGISTER.md', 'r', encoding='utf-8') as f:
        dsr = f.read()
    competitions = [
        'Ranji Trophy', 'Syed Mushtaq Ali', 'Vijay Hazare', 'Duleep Trophy',
        'Cooch Behar', 'Vinoo Mankad', 'C.K. Nayudu', 'Vijay Merchant', 'U-19'
    ]
    print("=== DATA_SOURCE_REGISTER.md R3 Checks ===")
    for c in competitions:
        count = len(re.findall(re.escape(c), dsr, re.I))
        print(f"  {c}: {count} occurrences")
    print("  Scorecard vs Ball-by-ball:", 'scorecard' in dsr.lower() and 'ball-by-ball' in dsr.lower())

    # 2. Check TRD.md for PVRE contracts, 7 engines, 33 entities
    with open('docs/TRD.md', 'r', encoding='utf-8') as f:
        trd = f.read()
    print("\n=== TRD.md Checks ===")
    print("  Engine 07 mention:", len(re.findall(r'ENGINE\s+07', trd, re.I)))
    print("  Mother Controller mention:", len(re.findall(r'Mother\s+Controller', trd, re.I)))
    print("  REVIEW_REQUIRED mention:", len(re.findall(r'REVIEW_REQUIRED', trd)))
    print("  Entities claimed in TRD:", re.findall(r'(\b\d+\s+entities\b)', trd, re.I)[:5])

    # 3. Check PRD.md for AC-24..AC-30 and Top-10 separation
    with open('docs/PRD.md', 'r', encoding='utf-8') as f:
        prd = f.read()
    print("\n=== PRD.md Checks ===")
    for ac in [f'AC-{i:02d}' for i in range(24, 31)]:
        print(f"  {ac}: {len(re.findall(ac, prd))} occurrences")

    # 4. Check ARCHITECTURE.md for Mermaid diagrams and ADR
    with open('docs/ARCHITECTURE.md', 'r', encoding='utf-8') as f:
        arch = f.read()
    print("\n=== ARCHITECTURE.md Checks ===")
    print("  PVRE ADR found:", 'ADR-008' in arch or 'ADR' in arch and 'PVRE' in arch)
    print("  Mermaid blocks count:", len(re.findall(r'```mermaid', arch)))

    # 5. Check PHASES.md for Phase 4B checkpoints and dependencies
    with open('docs/PHASES.md', 'r', encoding='utf-8') as f:
        phases = f.read()
    print("\n=== PHASES.md Checks ===")
    print("  Phase 4B found:", 'Phase 4B' in phases)
    print("  Checkpoints 1-12 found:", len(re.findall(r'Checkpoint\s+\d+', phases)))

    # 6. Check AGENTS.md for agent_pvre
    with open('docs/AGENTS.md', 'r', encoding='utf-8') as f:
        agents = f.read()
    print("\n=== AGENTS.md Checks ===")
    print("  agent_pvre found:", 'agent_pvre' in agents)
    print("  Agent count table rows:", len(re.findall(r'###\s+Agent\s+\d+', agents)))

    # 7. Check AI_INSTRUCTIONS.md for guardrails
    with open('docs/AI_INSTRUCTIONS.md', 'r', encoding='utf-8') as f:
        ai_inst = f.read()
    print("\n=== AI_INSTRUCTIONS.md Checks ===")
    print("  PVRE guardrails found:", 'PVRE' in ai_inst)

    # 8. Check RANKING_SPEC.md for decoupling
    with open('docs/RANKING_SPEC.md', 'r', encoding='utf-8') as f:
        ranking = f.read()
    print("\n=== RANKING_SPEC.md Checks ===")
    print("  Top-10 decoupling found:", 'Top-10' in ranking and 'RE-1.0.0' in ranking)

    # 9. Check DOCUMENTATION_PRE_REMEDIATION_AUDIT.md
    with open('DOCUMENTATION_PRE_REMEDIATION_AUDIT.md', 'r', encoding='utf-8') as f:
        pre_audit = f.read()
    print("\n=== DOCUMENTATION_PRE_REMEDIATION_AUDIT.md Checks ===")
    print("  v2.2.0 mention:", 'v2.2.0' in pre_audit or '2.2.0' in pre_audit)
    print("  Supersession note for v2.2.0:", 'supersed' in pre_audit.lower())

    # 10. Check reports/DOCUMENTATION_REMEDIATION_AUDIT.md
    with open('reports/DOCUMENTATION_REMEDIATION_AUDIT.md', 'r', encoding='utf-8') as f:
        rem_audit = f.read()
    print("\n=== reports/DOCUMENTATION_REMEDIATION_AUDIT.md Checks ===")
    print("  Section 20 Addendum found:", 'Addendum' in rem_audit and 'v2.2.0' in rem_audit)

audit_details()
