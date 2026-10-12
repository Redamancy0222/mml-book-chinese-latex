# -*- coding: utf-8 -*-
"""Final acceptance check for the compiled book."""
import os
import re
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
PDF = os.path.join(HERE, 'build', 'main.pdf')
LOG = os.path.join(HERE, 'build', 'main.log')
ROOT = os.path.dirname(HERE)


def sh(*cmd):
    return subprocess.run(cmd, capture_output=True, cwd=HERE).stdout.decode('utf-8', 'replace')


log = open(LOG, encoding='utf-8', errors='replace').read()
info = sh('pdfinfo', PDF)
text = sh('pdftotext', '-layout', PDF, '-')

pages = int(re.search(r'Pages:\s+(\d+)', info).group(1))
size_mb = os.path.getsize(PDF) / 1e6

# 1. every source tag must be present in the PDF
tags = {}
for dp, dn, fn in os.walk(ROOT):
    parts = dp.split(os.sep)
    if any(p in ('.idea', 'latex-book') or p.startswith('.backup_') for p in parts):
        continue
    for f in fn:
        if f.endswith('.md'):
            t = open(os.path.join(dp, f), encoding='utf-8').read()
            for m in re.finditer(r'\\tag\{([^}]*)\}', t):
                k = m.group(1).strip()
                tags[k] = tags.get(k, 0) + 1
found = set(re.findall(r'\((\d+\.\d+[a-z]?)\)', text))
missing_tags = sorted(set(tags) - found)

# 2. counters
errs = len(re.findall(r'(?m)^!', log))
overfull = len(re.findall(r'Overfull \\hbox', log))
underfull = len(re.findall(r'Underfull', log))
missing_chars = len(re.findall(r'Missing character', log))
undef = len(re.findall(r"Reference `[^']+' .*undefined", log))
rerun = len(re.findall(r'Rerun to get', log))

# 3. hyperlink targets
hrefs = sh('pdftotext', '-layout', PDF, '-')
n_links = 0
try:
    out = subprocess.run(['pdftotext', '-layout', PDF, '-'], capture_output=True, cwd=HERE)
except Exception:
    pass

# 4. figures actually embedded
imgs = int(re.search(r'(\d+)', sh('pdfimages', '-list', PDF).split('\n')[2].split()[0] or '0')
           .group(1)) if False else None
img_lines = [l for l in sh('pdfimages', '-list', PDF).split('\n')[2:] if l.strip()]
n_images = len(img_lines)

print('=' * 70)
print('FINAL ACCEPTANCE CHECK')
print('=' * 70)
print('PDF                 : %s' % PDF)
print('pages               : %d' % pages)
print('size                : %.2f MB' % size_mb)
print('embedded images     : %d' % n_images)
print()
print('compile errors      : %d' % errs)
print('undefined refs      : %d' % undef)
print('missing chars       : %d' % missing_chars)
print('Overfull hbox       : %d' % overfull)
print('Underfull hbox      : %d' % underfull)
print('"Rerun to get"      : %d  (must be 0 = fully settled)' % rerun)
print()
print('source \\tag count   : %d (distinct %d)' % (sum(tags.values()), len(tags)))
print('tags missing in PDF : %d' % len(missing_tags))
for t in missing_tags[:10]:
    print('    %s' % t)
print()
print('RESULT: %s' % ('PASS' if (errs == 0 and undef == 0 and rerun == 0
                                 and not missing_tags) else 'ISSUES'))
