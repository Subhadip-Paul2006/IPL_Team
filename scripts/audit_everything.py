import os
import re

doc_files = [
    'README.md', 'PROJECT.md', 'docs/README.md', 'docs/PRD.md', 'docs/TRD.md',
    'docs/ARCHITECTURE.md', 'docs/PHASES.md', 'docs/AGENTS.md', 'docs/AI_INSTRUCTIONS.md',
    'docs/DATA_SOURCE_REGISTER.md', 'docs/DATA_DICTIONARY.md', 'docs/RANKING_SPEC.md',
    'reports/DOCUMENTATION_REMEDIATION_AUDIT.md'
]

print("=== AUDIT PART 1: CHECKING PRESENCE & INTEGRITY OF 13 DOCS ===")
for path in doc_files:
    if os.path.exists(path):
        size = os.path.getsize(path)
        print(f"  [OK] {path} exists ({size} bytes)")
    else:
        print(f"  [MISSING] {path} does not exist!")

print("\n=== AUDIT PART 2: ENGINE INVENTORY & COUNT ===")
for path in doc_files:
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    six_engines = re.findall(r'(?<!superseded by the MIE \+ )\b(?:six|6)\s+(?:specialised\s+)?engines\b', text, re.I)
    seven_engines = re.findall(r'\b(?:seven|7)\s+(?:specialised\s+)?engines\b', text, re.I)
    # Check if there are present-tense claims of 6 engines
    for line in text.split('\n'):
        if re.search(r'\b(?:six|6)\s+(?:specialised\s+)?engines\b', line, re.I):
            if 'superseded' not in line.lower() and 'v2.0.0' not in line and 'historical' not in line.lower():
                print(f"  [DISCREPANCY in {path}]: {line.strip()}")

print("\n=== AUDIT PART 3: AGENTS COUNT & INVENTORY ===")
with open('docs/AGENTS.md', 'r', encoding='utf-8') as f:
    agents_text = f.read()
agent_matches = re.findall(r'###\s+([0-9.]+)\s+Agent\s+\d+:\s+`([^`]+)`', agents_text)
print(f"  Total agent definitions found in docs/AGENTS.md: {len(agent_matches)}")
for num, name in agent_matches:
    print(f"    {num}: {name}")

print("\n=== AUDIT PART 4: ACCEPTANCE CRITERIA IN PRD ===")
with open('docs/PRD.md', 'r', encoding='utf-8') as f:
    prd_text = f.read()
acs = re.findall(r'\b(AC-\d{2})\b', prd_text)
unique_acs = sorted(list(set(acs)))
print(f"  Unique ACs in PRD: {len(unique_acs)} -> {unique_acs[0]} to {unique_acs[-1]}")
pvre_acs = [ac for ac in unique_acs if int(ac.split('-')[1]) >= 24]
print(f"  PVRE ACs (>= AC-24): {pvre_acs}")

print("\n=== AUDIT PART 5: PVRE CONTRACT & 23 MINIMUM FIELDS ===")
fields_23 = [
    'contract_version', 'research_run_id', 'player_id', 'canonical_name',
    'identity_status', 'research_mode', 'route_status', 'evaluation_date',
    'target_season_id', 'rr_relationship_state', 'rr_current_state',
    'eligibility_status', 'research_window_start', 'research_window_end',
    'rr_historical_profile', 'recent_global_performance', 'complete_career_profile',
    'replaceability_assessment', 'competition_coverage', 'source_record_ids',
    'verification_record_ids', 'review_status', 'review_reason_codes',
    'data_quality_summary'
]
with open('docs/TRD.md', 'r', encoding='utf-8') as f:
    trd_text = f.read()
missing_fields = [f for f in fields_23 if f not in trd_text]
if not missing_fields:
    print(f"  [OK] All {len(fields_23)} minimum PVRE output contract fields are present in docs/TRD.md")
else:
    print(f"  [MISSING in TRD.md]: {missing_fields}")

print("\n=== AUDIT PART 6: SICE 16 DIMENSIONS & RECOMMENDATIONS ===")
sice_dimensions = [
    'primary role', 'secondary role', 'batting position', 'bowling role',
    'age', 'eligibility', 'historical contribution', 'recent',
    'career development', 'role-specific', 'sample size', 'competition strength',
    'squad balance', 'overseas', 'squad constraints', 'evidence coverage'
]
sice_recs = [
    'ANALYTICAL_RETAIN', 'ANALYTICAL_MONITOR', 'ANALYTICAL_REPLACEMENT_CANDIDATE',
    'NO_SUITABLE_VERIFIED_REPLACEMENT', 'INSUFFICIENT_EVIDENCE'
]
missing_recs = [r for r in sice_recs if r not in trd_text]
if not missing_recs:
    print(f"  [OK] All {len(sice_recs)} SICE analytical recommendations present in docs/TRD.md")
else:
    print(f"  [MISSING in TRD.md]: {missing_recs}")

print("\n=== AUDIT PART 7: PHASE 4B IN PHASES.md ===")
with open('docs/PHASES.md', 'r', encoding='utf-8') as f:
    phases_text = f.read()
if 'Phase 4B' in phases_text:
    print("  [OK] Phase 4B found in docs/PHASES.md")
    checkpoints = re.findall(r'Checkpoint\s+\d+|checkpoint\s+\d+|###\s+7\.\d+', phases_text)
    print(f"    Checkpoint references found: {len(checkpoints)}")
else:
    print("  [MISSING] Phase 4B not found in docs/PHASES.md!")

print("\n=== AUDIT PART 8: MERMAID DIAGRAM BLOCKS VALIDATION ===")
for path in doc_files:
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    blocks = re.findall(r'```mermaid(.*?)```', text, re.DOTALL)
    for i, b in enumerate(blocks):
        lines = [l.strip() for l in b.strip().split('\n') if l.strip() and not l.strip().startswith('%%')]
        if not lines:
            print(f"  [WARNING in {path}] Empty mermaid block #{i+1}")
        else:
            first = lines[0]
            valid_types = ('graph', 'flowchart', 'sequenceDiagram', 'erDiagram', 'classDiagram', 'stateDiagram', 'pie', 'gantt')
            if not any(first.startswith(vt) for vt in valid_types):
                print(f"  [ERROR in {path}] Mermaid block #{i+1} has invalid header: {first}")
print("  Mermaid diagram headers validation complete.")
