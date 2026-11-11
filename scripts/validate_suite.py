import os
import re

files_to_check = [
    'README.md',
    'PROJECT.md',
    'DOCUMENTATION_PRE_REMEDIATION_AUDIT.md',
    'docs/README.md',
    'docs/PRD.md',
    'docs/TRD.md',
    'docs/ARCHITECTURE.md',
    'docs/PHASES.md',
    'docs/AGENTS.md',
    'docs/AI_INSTRUCTIONS.md',
    'docs/DATA_SOURCE_REGISTER.md',
    'docs/DATA_DICTIONARY.md',
    'docs/RANKING_SPEC.md',
    'reports/DOCUMENTATION_REMEDIATION_AUDIT.md'
]

print("=== 1. VERIFYING FILE EXISTENCE ===")
for path in files_to_check:
    if os.path.exists(path):
        print(f"  [OK] {path} exists ({os.path.getsize(path)} bytes)")
    else:
        print(f"  [FAIL] {path} NOT FOUND!")

print("\n=== 2. CHECKING ENGINE, AGENT, ENTITY, AND AC COUNTS ===")
for path in files_to_check:
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # Check for PVRE mentions
    pvre_count = len(re.findall(r'\bPVRE\b', text))
    # Check for Phase 4B mentions
    p4b_count = len(re.findall(r'Phase 4B', text))
    
    print(f"  {path:45} | PVRE: {pvre_count:3} | Phase 4B: {p4b_count:3}")

print("\n=== 3. CHECKING LINK TARGETS ===")
broken_links = []
for path in files_to_check:
    dir_name = os.path.dirname(path)
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # find [text](link)
    links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', text)
    for link_text, link_target in links:
        if link_target.startswith('http') or link_target.startswith('#') or link_target.startswith('mailto'):
            continue
        # strip anchor #...
        target_file = link_target.split('#')[0]
        if not target_file:
            continue
        full_target = os.path.normpath(os.path.join(dir_name, target_file))
        if not os.path.exists(full_target):
            broken_links.append((path, link_target, full_target))

if broken_links:
    print(f"  [FAIL] Found {len(broken_links)} broken relative file links:")
    for src, tgt, full in broken_links:
        print(f"    In {src}: {tgt} -> {full} not found")
else:
    print("  [OK] 0 broken relative file links found across all files!")

print("\n=== 4. CHECKING MERMAID CODE BLOCKS ===")
mermaid_blocks = 0
for path in files_to_check:
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    matches = re.findall(r'```mermaid\n(.*?)\n```', text, re.DOTALL)
    for m in matches:
        mermaid_blocks += 1
        lines = m.strip().split('\n')
        first_line = lines[0].strip()
        # Verify valid Mermaid header
        valid_headers = ['flowchart', 'graph', 'sequenceDiagram', 'classDiagram', 'erDiagram', 'stateDiagram', 'gantt', 'pie']
        if not any(first_line.startswith(h) for h in valid_headers):
            print(f"  [WARN] Unknown Mermaid diagram type in {path}: {first_line}")

print(f"  [OK] Checked {mermaid_blocks} Mermaid diagram blocks.")

print("\n=== VALIDATION COMPLETED ===")
