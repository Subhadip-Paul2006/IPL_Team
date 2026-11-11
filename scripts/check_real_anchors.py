import os
import re

files_to_check = [
    'README.md', 'PROJECT.md', 'docs/README.md', 'docs/PRD.md', 'docs/TRD.md',
    'docs/ARCHITECTURE.md', 'docs/PHASES.md', 'docs/AGENTS.md', 'docs/AI_INSTRUCTIONS.md',
    'docs/DATA_SOURCE_REGISTER.md', 'docs/DATA_DICTIONARY.md', 'docs/RANKING_SPEC.md',
    'reports/DOCUMENTATION_REMEDIATION_AUDIT.md'
]

def gfm_slug(heading):
    h = heading.strip().lower()
    h = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', h)
    h = re.sub(r'[*_`]', '', h)
    h = re.sub(r'[^\w\s-]', '', h)
    return h.replace(' ', '-')

def collapsed_slug(heading):
    h = heading.strip().lower()
    h = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', h)
    h = re.sub(r'[*_`]', '', h)
    h = re.sub(r'[^\w\s-]', '', h)
    return re.sub(r'\s+', '-', h)

doc_headings = {}
for path in files_to_check:
    if not os.path.exists(path):
        continue
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    headings = set()
    for line in content.split('\n'):
        m = re.match(r'^(#{1,6})\s+(.*)', line)
        if m:
            raw_h = m.group(2).strip()
            headings.add(gfm_slug(raw_h))
            headings.add(collapsed_slug(raw_h))
            h_no_bracket = re.sub(r'\[.*?\]', '', raw_h).strip()
            headings.add(gfm_slug(h_no_bracket))
            headings.add(collapsed_slug(h_no_bracket))
        for am in re.finditer(r'<a\s+(?:name|id)=["\']([^"\']+)["\']', line):
            headings.add(am.group(1).lower())
    doc_headings[path] = headings

truly_broken = []
for path in files_to_check:
    if not os.path.exists(path):
        continue
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    dir_name = os.path.dirname(path)
    links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
    for text, tgt in links:
        if tgt.startswith('http') or tgt.startswith('mailto'):
            continue
        if '#' in tgt:
            parts = tgt.split('#', 1)
            file_part = parts[0]
            anchor_part = parts[1]
            if not file_part:
                target_doc = path
            else:
                target_doc = os.path.normpath(os.path.join(dir_name, file_part)).replace('\\', '/')
            if target_doc in doc_headings:
                if anchor_part.lower() not in doc_headings[target_doc]:
                    truly_broken.append((path, tgt, target_doc, anchor_part))

print(f'Truly broken anchors count: {len(truly_broken)}')
for src, tgt, doc, anc in truly_broken:
    print(f'{src} -> {tgt} (target: {doc}, missing: {anc})')
