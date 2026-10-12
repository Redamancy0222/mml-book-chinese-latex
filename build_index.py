# -*- coding: utf-8 -*-
"""
Build a real page index for the Chinese edition.

The source 4.Index.md carries the *original English* page numbers, which do not
match this PDF. This script:

  1. parses the 459 index entries (English headword + Chinese gloss);
  2. searches the compiled PDF page by page for the headword / gloss;
  3. writes chapters/c098_4_Index.tex with the real PDF page numbers, each one a
     hyperlink into the document.

Usage:  python build_index.py            (needs build/main.pdf to exist)
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PDF = os.path.join(HERE, 'build', 'main.pdf')
SRC = os.path.join(ROOT, '4.Index.md')
DEST = os.path.join(HERE, 'chapters', 'c098_4_Index.tex')

MAX_REFS = 6          # pages listed per entry


def parse_index():
    """-> [(letter, english, chinese)] preserving source order."""
    text = open(SRC, encoding='utf-8').read()
    letter = ''
    entries = []
    for line in text.split('\n'):
        m = re.match(r'^##\s+(.*)$', line.strip())
        if m:
            letter = m.group(1).strip()
            continue
        m = re.match(r'^-\s+\*\*(.+?)\*\*(.*)$', line.strip())
        if not m:
            continue
        english = m.group(1).strip()
        rest = m.group(2).strip()
        # trailing ", 364" style page list (original edition) is discarded
        rest = re.sub(r',\s*[\d,\s]+$', '', rest).strip()
        chinese = ''
        g = re.match(r'^[（(](.*)[)）]$', rest)
        if g:
            chinese = g.group(1).strip()
        # strip a nested parenthetical gloss: 词（english）
        chinese = re.sub(r'[（(][^（()）]*[)）]', '', chinese).strip()
        entries.append((letter, english, chinese))
    return entries


def pdf_pages():
    """-> list of page texts (index 0 == PDF page 1)."""
    out = subprocess.run(['pdftotext', '-layout', PDF, '-'], capture_output=True)
    raw = out.stdout.decode('utf-8', 'replace')
    return raw.split('\f')


def search(pages, needle, limit=MAX_REFS):
    if not needle or len(needle) < 2:
        return []
    hits = []
    for i, page in enumerate(pages):
        if needle in page:
            hits.append(i + 1)
            if len(hits) >= limit:
                break
    return hits


def main():
    if not os.path.exists(PDF):
        print('build/main.pdf missing - compile first')
        return 1
    entries = parse_index()
    pages = pdf_pages()
    # Never point an index entry at the index itself. The index pages contain
    # every headword AND the page numbers, so without this bound each entry
    # would match the index pages and collect a bogus self-reference.
    body_end = len(pages)
    for i, p in enumerate(pages):
        if '术语索引' in p and i > 50:          # the index chapter heading
            body_end = i
            break
    searchable = pages[:body_end]
    print('index entries : %d' % len(entries))
    print('pdf pages     : %d (searching 1..%d)' % (len(pages), body_end))

    def search_clean(needle):
        return search(searchable, needle)

    found = 0
    out = [r'\chapter*{术语索引}', r'\addcontentsline{toc}{chapter}{术语索引}', '']
    out.append('本索引由译本正文自动生成，页码指向本 PDF 的实际页码。')
    out.append('')
    out.append(r'\begin{multicols}{2}\small')
    cur_letter = None
    for letter, english, chinese in entries:
        if letter != cur_letter:
            cur_letter = letter
            out.append('')
            out.append(r'\medskip\noindent{\hei %s}\par\smallskip' % letter)
        refs = search_clean(chinese) if chinese else []
        if not refs:
            refs = search_clean(english)
        if refs:
            found += 1
        pagetext = ''
        if refs:
            pagetext = '，'.join(r'\hyperpage{%d}' % p for p in refs)
        label = english
        if chinese:
            label += '（%s）' % chinese
        if pagetext:
            out.append(r'\noindent %s，%s\par' % (label, pagetext))
        else:
            out.append(r'\noindent %s\par' % label)
    out.append(r'\end{multicols}')
    out.append('')

    os.makedirs(os.path.dirname(DEST), exist_ok=True)
    with open(DEST, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write('\n'.join(out) + '\n')
    print('entries with page refs : %d / %d' % (found, len(entries)))
    print('written %s' % DEST)
    return 0


if __name__ == '__main__':
    sys.exit(main())
