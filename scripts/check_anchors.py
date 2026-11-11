import os
import re

files_to_check = [
    'README.md', 'PROJECT.md', 'docs/README.md', 'docs/PRD.md', 'docs/TRD.md',
    'docs/ARCHITECTURE.md', 'docs/PHASES.md', 'docs/AGENTS.md', 'docs/AI_INSTRUCTIONS.md',
    'docs/DATA_SOURCE_REGISTER.md', 'docs/DATA_DICTIONARY.md', 'docs/RANKING_SPEC.md',
    'reports/DOCUMENTATION_REMEDIATION_AUDIT.md'
]

def heading_to_slug(heading):
    h = heading.strip().lower()
    h = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', h)
    h = re.sub(r'[*_`]', '', h)
    h = re.sub(r'[^\w\s-]', '', h)
    h = re.sub(r'\s+', '-', h)
    return h

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
            slug = heading_to_slug(raw_h)
            headings.add(slug)
        for am in re.finditer(r'<a\s+(?:name|id)=["\']([^"\']+)["\']', line):
            headings.add(am.group(1).lower())
    doc_headings[path] = headings

broken_anchors = []
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
                    broken_anchors.append((path, tgt, target_doc, anchor_part))

print(f'Total broken anchors found: {len(broken_anchors)}')
for src, tgt, doc, anc in broken_anchors:
    print(f'In {src}: {tgt} -> {doc} missing anchor: {anc}')
