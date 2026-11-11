import sys
sys.path.append('scripts')
import check_anchors

with open('broken_anchors_report.txt', 'w', encoding='utf-8') as f:
    f.write(f'Total broken anchors: {len(check_anchors.broken_anchors)}\n\n')
    for src, tgt, doc, anc in check_anchors.broken_anchors:
        f.write(f'Source: {src}\n  Target: {tgt}\n  File: {doc}\n  Missing Anchor: {anc}\n\n')
print('Report written to broken_anchors_report.txt')
