import subprocess
import re

def git_show(path):
    cmd = ['git', 'show', f'eaebdcb:{path}']
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8', errors='ignore')
    if p.returncode != 0:
        return None
    return p.stdout

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

print("=== 1. FILE EXISTENCE & HEADERS ON ORIGIN/MAIN (eaebdcb) ===")
for f in files_14:
    content = git_show(f)
    if content is None:
        print(f"[MISSING on origin/main] {f}")
        continue
    lines = content.splitlines()
    header_lines = [l for l in lines[:15] if l.strip()]
    print(f"\n--- {f} ({len(lines)} lines, {len(content)} bytes) ---")
    for hl in header_lines[:3]:
        print(f"  {hl}")

print("\n=== 2. VERSIONS ON ORIGIN/MAIN ===")
for f in files_14:
    content = git_show(f)
    if not content: continue
    vers = set(re.findall(r'v\d+\.\d+\.\d+', content))
    print(f"{f}: {sorted(list(vers))}")

print("\n=== 3. ENGINE COUNT & INVENTORY ON ORIGIN/MAIN ===")
for f in files_14:
    content = git_show(f)
    if not content: continue
    engines_found = re.findall(r'(\b\w+\s+specialised engines\b|\bEngine\s+\d+[^:\n]*:[^\n]*)', content, re.I)
    if engines_found:
        print(f"\n{f}:")
        for ef in engines_found[:5]:
            print(f"  {ef}")

print("\n=== 4. DATABASE ENTITY COUNT ON ORIGIN/MAIN ===")
for f in ['docs/TRD.md', 'docs/ARCHITECTURE.md', 'reports/DOCUMENTATION_REMEDIATION_AUDIT.md', 'DOCUMENTATION_PRE_REMEDIATION_AUDIT.md']:
    content = git_show(f)
    if not content: continue
    counts = re.findall(r'(\d+[- ](?:entity|entities|tables|database entities|core entities)\b[^\n]*)', content, re.I)
    print(f"\n{f}:")
    for c in counts[:8]:
        print(f"  {c}")

print("\n=== 5. AC NUMBERING ON ORIGIN/MAIN ===")
for f in ['docs/PRD.md', 'docs/TRD.md', 'docs/PHASES.md']:
    content = git_show(f)
    if not content: continue
    acs = sorted(list(set(re.findall(r'\bAC-\d{2}\b', content))))
    print(f"{f}: {len(acs)} ACs -> {acs}")

print("\n=== 6. AGENTS ON ORIGIN/MAIN ===")
agents_content = git_show('docs/AGENTS.md')
if agents_content:
    agent_defs = re.findall(r'###\s+([0-9.]+)\s+Agent\s+\d+:\s+`([^`]+)`', agents_content)
    print(f"docs/AGENTS.md: {len(agent_defs)} agents")
    for num, name in agent_defs:
        print(f"  {num}: {name}")

print("\n=== 7. PHASES ON ORIGIN/MAIN ===")
phases_content = git_show('docs/PHASES.md')
if phases_content:
    phase_headers = re.findall(r'##\s+(Phase\s+[^\n]+)', phases_content)
    print(f"docs/PHASES.md: {len(phase_headers)} phases")
    for ph in phase_headers:
        print(f"  {ph}")
