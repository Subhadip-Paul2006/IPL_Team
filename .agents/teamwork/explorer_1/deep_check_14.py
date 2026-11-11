import subprocess
import re

files_14 = [
    'README.md',
    'PROJECT.md',
    'DOCUMENTATION_PRE_REMEDIATION_AUDIT.md',
    'reports/DOCUMENTATION_REMEDIATION_AUDIT.md',
    'docs/README.md',
    'docs/PRD.md',
    'docs/TRD.md',
    'docs/ARCHITECTURE.md',
    'docs/PHASES.md',
    'docs/AGENTS.md',
    'docs/AI_INSTRUCTIONS.md',
    'docs/DATA_DICTIONARY.md',
    'docs/DATA_SOURCE_REGISTER.md',
    'docs/RANKING_SPEC.md'
]

def check_file(path):
    print(f"\n=======================================================")
    print(f"FILE: {path}")
    print(f"=======================================================")
    try:
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        print(f"Total lines: {len(lines)}")
        
        # Check header
        print("Header lines (first 5 non-empty):")
        cnt = 0
        for l in lines:
            if l.strip():
                print(f"  {l.strip()}")
                cnt += 1
                if cnt >= 5: break
                
        # Check PVRE occurrences
        pvre_lines = [(i+1, l.strip()) for i, l in enumerate(lines) if 'PVRE' in l]
        print(f"PVRE occurrences: {len(pvre_lines)}")
        if pvre_lines:
            print(f"  First 3 PVRE mentions: {pvre_lines[:3]}")
            print(f"  Last 2 PVRE mentions: {pvre_lines[-2:]}")
            
        # Check Mode A / Mode B
        mode_a = [(i+1, l.strip()) for i, l in enumerate(lines) if 'Mode A' in l]
        mode_b = [(i+1, l.strip()) for i, l in enumerate(lines) if 'Mode B' in l]
        print(f"Mode A mentions: {len(mode_a)}, Mode B mentions: {len(mode_b)}")
        
        # Check REVIEW_REQUIRED
        rev_req = [(i+1, l.strip()) for i, l in enumerate(lines) if 'REVIEW_REQUIRED' in l]
        print(f"REVIEW_REQUIRED mentions: {len(rev_req)}")
        
        # Check Phase 4B
        phase_4b = [(i+1, l.strip()) for i, l in enumerate(lines) if 'Phase 4B' in l or 'Phase 4b' in l]
        print(f"Phase 4B mentions: {len(phase_4b)}")
        
        # Check versions
        v220 = [(i+1, l.strip()) for i, l in enumerate(lines) if 'v2.2.0' in l or '2.2.0' in l]
        print(f"v2.2.0 mentions: {len(v220)}")
        if v220:
            print(f"  Sample v2.2.0 lines: {v220[:3]}")
            
    except Exception as e:
        print(f"Error checking {path}: {e}")

for f in files_14:
    check_file(f)
