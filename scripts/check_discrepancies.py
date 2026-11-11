import os
import re

files_to_check = [
    'README.md',
    'PROJECT.md',
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

patterns = [
    r'six specialised engines',
    r'six engines',
    r'31-entity',
    r'31 entities',
    r'16 agents',
    r'16 agent',
    r'AC-01.{1,5}AC-23'
]

for p in patterns:
    print(f"\n--- Checking pattern: {p} ---")
    for path in files_to_check:
        with open(path, 'r', encoding='utf-8') as f:
            for idx, line in enumerate(f, 1):
                if re.search(p, line, re.IGNORECASE):
                    # Check if it's explicitly historical/superseded
                    print(f"{path}:{idx}: {line.strip()[:100]}")
