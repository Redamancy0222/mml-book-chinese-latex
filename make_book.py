#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Compile the book to a fixed point.

The index stores hard page numbers, so a changed index length shifts every later
page and invalidates those numbers. This script therefore:

  1. runs XeLaTeX until the page count stops changing (toc / refs settle);
  2. rebuilds the index from the resulting PDF;
  3. repeats until both the page count AND the index content are stable.

Usage:  python make_book.py [max_rounds]
"""
import hashlib
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PDF = os.path.join(HERE, 'build', 'main.pdf')
INDEX_TEX = os.path.join(HERE, 'chapters', 'c098_4_Index.tex')


def run(cmd, **kw):
    return subprocess.run(cmd, cwd=HERE, capture_output=True, **kw)


def pages():
    out = run(['pdfinfo', PDF])
    m = re.search(rb'Pages:\s+(\d+)', out.stdout)
    return int(m.group(1)) if m else -1


def latex_pass():
    out = run(['xelatex', '-interaction=nonstopmode', '-file-line-error',
               '-output-directory=build', 'main.tex'])
    err = [l for l in out.stdout.decode('utf-8', 'replace').split('\n')
           if l.startswith('! ')]
    return err


def index_digest():
    if not os.path.exists(INDEX_TEX):
        return ''
    return hashlib.sha256(open(INDEX_TEX, 'rb').read()).hexdigest()[:12]


def main():
    max_rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    prev_pages, prev_digest = None, None
    for rnd in range(1, max_rounds + 1):
        # inner loop: run LaTeX until the page count settles
        for i in range(6):
            err = latex_pass()
            if err:
                print('  LaTeX errors on round %d pass %d:' % (rnd, i + 1))
                for e in err[:8]:
                    print('     %s' % e)
                return 1
            p = pages()
            if p == prev_pages:
                break
            prev_pages = p
        digest = index_digest()
        print('round %d: %d pages, index digest %s' % (rnd, prev_pages, digest))

        # rebuild the index against the settled PDF
        out = run([sys.executable, 'build_index.py'])
        text = out.stdout.decode('utf-8', 'replace')
        n_pages = re.search(r'pdf pages\s+:\s+(\d+)', text)
        n_refs = re.search(r'entries with page refs\s+:\s+(\d+)', text)
        print('        index rebuilt against %s pages, %s entries resolved'
              % (n_pages.group(1) if n_pages else '?',
                 n_refs.group(1) if n_refs else '?'))

        if digest == index_digest() and rnd > 1:
            print('converged: page count and index are stable')
            return 0
        prev_digest = digest
    print('stopped after %d rounds (not fully converged)' % max_rounds)
    return 0


if __name__ == '__main__':
    sys.exit(main())
