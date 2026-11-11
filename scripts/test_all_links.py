import os
import re

all_md_files = []
for root, dirs, files in os.walk('.'):
    if '.git' in root or 'datasets' in root:
        continue
    for f in files:
        if f.endswith('.md'):
            all_md_files.append(os.path.normpath(os.path.join(root, f)).replace('\\', '/'))

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
for path in all_md_files:
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

broken_file_links = []
broken_anchor_links = []

for path in all_md_files:
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    dir_name = os.path.dirname(path)
    links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
    for text, tgt in links:
        if tgt.startswith('http') or tgt.startswith('mailto'):
            continue
        parts = tgt.split('#', 1)
        file_part = parts[0]
        anchor_part = parts[1] if len(parts) > 1 else None

        if file_part:
            target_path = os.path.normpath(os.path.join(dir_name, file_part)).replace('\\', '/')
            if not os.path.exists(target_path):
                broken_file_links.append((path, tgt, target_path))
                continue
        else:
            target_path = path

        if anchor_part:
            if target_path in doc_headings:
                if anchor_part.lower() not in doc_headings[target_path]:
                    broken_anchor_links.append((path, tgt, target_path, anchor_part))

print(f'Total markdown files scanned: {len(all_md_files)}')
print(f'Broken file links: {len(broken_file_links)}')
for src, tgt, resolved in broken_file_links:
    print(f'  FILE: {src} -> {tgt} (resolved: {resolved})')
print(f'Broken anchor links: {len(broken_anchor_links)}')
for src, tgt, resolved, anc in broken_anchor_links:
    print(f'  ANCHOR: {src} -> {tgt} (target: {resolved}, missing: {anc})')
