#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
md2tex.py — convert the mml-book-chinese markdown sources into LaTeX chapter files.

Design notes
------------
* Everything is emitted as UTF-8 and compiled with XeLaTeX, so CJK text and
  fullwidth punctuation can be written literally (no escaping needed).
* Display maths keeps the book's ORIGINAL equation numbers by re-emitting
  \\tag{...} inside an amsmath display environment. Blocks without a tag become
  unnumbered equations, so LaTeX never invents its own numbering.
* Headings keep the book's own numbering ("2.3.1") by using starred sectioning
  commands; the unstarred \\chapter is still used at chapter level so that
  headers/running titles work.
* Images are measured with Pillow so each figure gets a sane width/height that
  cannot overflow the text block.
* Markdown special characters are escaped only OUTSIDE maths, so LaTeX commands
  inside $...$ are never damaged.
"""
from __future__ import annotations

import json
import os
import re
import sys
import unicodedata

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                 # repo root (contains the .md files)
IMGDIR = os.path.join(ROOT, 'docs', 'images')
OUTDIR = os.path.join(HERE, 'chapters')
ARXIV_CACHE = os.path.join(HERE, '_image_ratios.json')

FENCE = '`' * 3

# --------------------------------------------------------------------------
# image metrics (used to size includegraphics)
# --------------------------------------------------------------------------
_RATIOS = {}


def image_ratios():
    if _RATIOS:
        return _RATIOS
    if os.path.exists(ARXIV_CACHE):
        with open(ARXIV_CACHE, encoding='utf-8') as fh:
            _RATIOS.update(json.load(fh))
        return _RATIOS
    for f in os.listdir(IMGDIR):
        if f.lower().endswith('.png'):
            with Image.open(os.path.join(IMGDIR, f)) as im:
                w, h = im.size
            _RATIOS[f] = [w, h]
    with open(ARXIV_CACHE, 'w', encoding='utf-8') as fh:
        json.dump(_RATIOS, fh)
    return _RATIOS


# --------------------------------------------------------------------------
# inline conversion (text mode only)
# --------------------------------------------------------------------------
def esc_text(s: str) -> str:
    """Escape LaTeX specials in ordinary (non-math) text."""
    s = s.replace('\\', r'\textbackslash{}')
    for a, b in (('&', r'\&'), ('%', r'\%'), ('$', r'\$'), ('#', r'\#'),
                 ('_', r'\_'), ('{', r'\{'), ('}', r'\}'),
                 ('~', r'\textasciitilde{}'), ('^', r'\textasciicircum{}')):
        s = s.replace(a, b)
    return s


# placeholders protect maths and code spans while the rest is escaped
_PH = '\x01%d\x02'
_STORE: list[str] = []


def _keep(latex: str) -> str:
    _STORE.append(latex)
    return _PH % (len(_STORE) - 1)


# Inline maths never spans a line break: allowing it to would let a "$ ... $$"
# pair swallow the opening of a following display equation.
_MATH_INLINE = re.compile(
    r'(?<!\\)\$\$([^$\n]+?)\$\$(?!\$)'
    r'|(?<!\\)\$(?!\$)([^$\n]+?)(?<!\\)\$(?!\$)')


def inline(text: str) -> str:
    """Convert one line/paragraph of markdown text to LaTeX."""
    global _STORE
    _STORE = []

    # 1. protect math first (it must survive escaping untouched).
    #    "$$ x $$" is also matched: table cells in the preface are written that
    #    way even though they are inline maths.
    def math_repl(m):
        body = m.group(1) if m.group(1) is not None else m.group(2)
        return _keep('$%s$' % body)
    text = _MATH_INLINE.sub(math_repl, text)

    # 2. protect escaped dollar literals from the coin example
    text = text.replace('\\$', _keep(r'\$'))

    # 3. protect inline code
    def code_repl(m):
        return _keep(r'\texttt{%s}' % esc_text(m.group(1)))
    text = re.sub(r'`([^`\n]+)`', code_repl, text)

    # 4. html bits: keep what we can render, drop the rest
    text = re.sub(r'<br\s*/?>', _keep(r'\newline '), text)
    text = re.sub(r'</?b>', _keep('\x03'), text)          # marker -> \textbf{}
    text = re.sub(r'<sub>(.*?)</sub>', lambda m: _keep(r'\textsubscript{%s}' % esc_text(m.group(1))), text)
    text = re.sub(r'<sup>(.*?)</sup>', lambda m: _keep(r'\textsuperscript{%s}' % esc_text(m.group(1))), text)
    text = re.sub(r'<[^>]+>', '', text)

    # 5. markdown emphasis MUST be handled before escaping, otherwise the
    #    underscores get escaped to "\_" and never match again.
    text = re.sub(r'\*\*(.+?)\*\*',
                  lambda m: _keep('\\textbf{' + m.group(1) + '}'), text)
    # the sources contain a handful of spans with a stray space inside the
    # markers ("_ 主元（pivot）_", "_备注 _"), so allow and trim that padding.
    # A closing "_" followed by an ASCII letter is left alone so that things
    # like "word_word" and "α_b" are never mistaken for emphasis.
    text = re.sub(r'(?<![\w\\])_\s*([^_\n]{1,400}?)\s*_(?![\w])',
                  lambda m: _keep('\\emph{' + m.group(1).strip() + '}'), text)

    # 6. links [text](url) — also before escaping so the URL survives intact
    def link_repl(m):
        label, url = m.group(1), m.group(2)
        return _keep('\\href{%s}{%s}' % (url.replace('%', r'\%'), label))
    text = re.sub(r'\[([^\]]*)\]\(([^)\s]+)\)', link_repl, text)

    # 7. escape everything that is left
    text = esc_text(text)

    # 8. restore protected spans and resolve <b> markers to a fixed point.
    #    A restoration can itself contain a placeholder (e.g. the bold span in
    #    "**求坐标 $ \\lambda $**" holds the maths placeholder) and a bold pair
    #    may only become adjacent after restoring, so both steps alternate.
    def restore(m):
        return _STORE[int(m.group(1))]

    def resolve_bold(s):
        while '\x03' in s:
            first = s.find('\x03')
            second = s.find('\x03', first + 1)
            if second < 0:
                s = s[:first] + s[first + 1:]
            else:
                inner = s[first + 1:second]
                s = s[:first] + '\\textbf{' + inner + '}' + s[second + 1:]
        return s

    for _ in range(20):
        before = text
        text = re.sub('\x01(\\d+)\x02', restore, text)
        text = resolve_bold(text)
        if text == before:
            break

    # 9. safety net: no control character may survive into the output
    text = (text.replace('\x03', '').replace('\x01', '').replace('\x02', ''))
    return text


# --------------------------------------------------------------------------
# figures
# --------------------------------------------------------------------------
_IMG_TAG = re.compile(r'<img\s+([^>]*?)/?>', re.I | re.S)


def _attr(attrs: str, name: str):
    m = re.search(r'%s\s*=\s*"([^"]*)"' % name, attrs, re.I)
    if not m:
        m = re.search(r"%s\s*=\s*'([^']*)'" % name, attrs, re.I)
    return m.group(1) if m else None


def parse_figure_number(caption_html: str) -> str | None:
    """Pull "4.8" out of a figure block, whether from the caption or the <img> alt."""
    m = re.search(r'<b>\s*图\s*(\d+\.\d+)', caption_html)
    if m:
        return m.group(1)
    m = re.search(r'(?:title|alt)="[^"]*?图\s*(\d+\.\d+)', caption_html)
    if m:
        return m.group(1)
    for m in re.finditer(r'图\s*(\d+\.\d+)', caption_html):
        return m.group(1)
    return None


def figure(src: str, caption: str, title: str, width_attr: str | None) -> str:
    """Emit a centered non-floating figure so it stays where the text puts it.

    The caption keeps the book's own number ("图 4.8 ..."). That leading number
    is rendered as a counter reference (so \\ref prints "4.8") and the \\label is
    emitted *before* \\caption, because caption.sty defines the label from the
    caption at \\caption time — placing it afterwards stores \\caption@xref and
    every reference to the figure stays undefined.
    """
    fname = os.path.basename(src)
    ratios = image_ratios()
    w, h = ratios.get(fname, [1000, 700])
    aspect = h / w if w else 0.7

    if aspect > 1.35:
        opts = 'width=%.2f\\textwidth,height=0.80\\textheight,keepaspectratio' % min(0.95, 1.35 / aspect)
    elif aspect > 0.95:
        opts = 'width=%dpt,keepaspectratio' % 320
    else:
        opts = 'width=%.2f\\textwidth,keepaspectratio' % 0.92

    cap = inline(caption) if caption else ''
    head = ''
    m = re.match(r'^\s*图\s*(\d+\.\d+)(.*)$', cap, re.S)
    if m:
        num, rest = m.group(1), m.group(2)
        # keep the numbering in step with the book's own numbers
        FIG_TARGETS.add(num)
        head = ('\\refstepcounter{figcounter}'
                '\\label{%s}图~\\thefigcounter%s' % (fig_label(num), rest))
    body = head if head else cap
    return ('\n\\begin{figure}[H]\n\\centering\n'
            '\\includegraphics[%s]{docs/images/%s}\n'
            '\\caption*{%s}\n'
            '\\end{figure}\n' % (opts, fname, body))


# --------------------------------------------------------------------------
# headings
# --------------------------------------------------------------------------
def is_table_sep(line: str) -> bool:
    return bool(re.match(r'^\s*\|[\s:|-]+\|\s*$', line))


def split_row(row: str) -> list[str]:
    """Split a markdown table row on pipes that are NOT inside maths.

    Cells such as "| $ \\| \\boldsymbol{x} \\| $ | ... |" carry pipes inside the
    maths, so a plain str.split('|') would shred them.
    """
    s = row.strip()
    if s.startswith('|'):
        s = s[1:]
    if s.endswith('|'):
        s = s[:-1]
    cells, buf, i, n = [], [], 0, len(s)
    while i < n:
        ch = s[i]
        if ch == '\\' and i + 1 < n:
            buf.append(s[i:i + 2])
            i += 2
            continue
        if ch == '$':
            if s.startswith('$$', i):
                end = s.find('$$', i + 2)
                if end >= 0:
                    buf.append(s[i:end + 2])
                    i = end + 2
                    continue
            else:
                end = s.find('$', i + 1)
                if end >= 0:
                    buf.append(s[i:end + 1])
                    i = end + 1
                    continue
        if ch == '|':
            cells.append(''.join(buf).strip())
            buf = []
            i += 1
            continue
        buf.append(ch)
        i += 1
    cells.append(''.join(buf).strip())
    return cells


def column_spec(ncol: int) -> str:
    """Build a longtable preamble: fixed-width, ragged-right columns.

    Each column also consumes 2*\\tabcolsep, so the usable text width must be
    reduced by that amount or the table overflows the margin (this bit c044/c062).
    """
    n = max(1, ncol)
    tabcolsep = 6.0                       # pt, the value used in the preamble
    width = r'\dimexpr(\textwidth-%dpt)/%d\relax' % (2 * tabcolsep * n, n)
    return ' '.join(r'>{\raggedright\arraybackslash}p{%s}' % width
                    for _ in range(n))


def inline_cell(text: str) -> str:
    """Like inline(), but maths is copied verbatim.

    Table cells hold maths such as "$$ \\| \\boldsymbol{x} \\| $$" that must not
    be escaped; running the normal inline() conversion would turn "\\tag" into
    "\\textbackslash tag" etc.
    """
    parts = []
    pos = 0
    for m in _MATH_INLINE.finditer(text):
        parts.append(('text', text[pos:m.start()]))
        body = m.group(1) if m.group(1) is not None else m.group(2)
        parts.append(('math', body))
        pos = m.end()
    parts.append(('text', text[pos:]))
    out = []
    for kind, chunk in parts:
        if kind == 'math':
            out.append('$%s$' % chunk.strip())
        elif chunk:
            out.append(inline(chunk))
    return ''.join(out)


# Inline maths that cannot possibly fit a text line. A matrix/array inside
# $...$ has to become a display equation, otherwise it overflows the margin.
_BIG_ENVS = ('bmatrix', 'pmatrix', 'vmatrix', 'matrix', 'array', 'cases')
# inline maths longer than this is promoted to a display equation even when it
# has no matrix: at ~10pt such an expression cannot share a line with text and
# would either overflow the margin or force a ragged paragraph.
INLINE_MAX = 150


def inline_too_wide(body: str) -> bool:
    if any(('\\begin{%s}' % e) in body for e in _BIG_ENVS):
        return True
    return len(body) > INLINE_MAX


def tagged_math_parts(line: str) -> list[tuple[str, str]]:
    """Split a source line into ('text'|'math', payload) around inline maths
    that must become a display equation.

    Two reasons to promote: the expression carries a \\tag (illegal in $...$,
    LaTeX would drop it), or it is structurally too wide for a text line.
    """
    out = []
    pos = 0
    for m in _MATH_INLINE.finditer(line):
        body = m.group(1) if m.group(1) is not None else m.group(2)
        if '\\tag{' not in body and not inline_too_wide(body):
            continue
        out.append(('text', line[pos:m.start()]))
        out.append(('math', body))
        pos = m.end()
    if not out:
        return [('text', line)]
    out.append(('text', line[pos:]))
    return out


def table_to_latex(rows: list[str]) -> str:
    """Convert a markdown pipe table into a longtable."""
    parsed = [split_row(r) for r in rows]
    if len(parsed) >= 2 and is_table_sep(rows[1]):
        head, body = parsed[0], parsed[2:]
    else:
        head, body = None, parsed
    # ignore the separator row when sizing the table
    ncol = max([len(r) for r in parsed if not is_table_sep('|'.join(r))] or [1])
    ncol = max(1, ncol)

    def row(cells, bold=False):
        cells = list(cells)
        if len(cells) > ncol:            # never silently drop content
            cells = cells[:ncol - 1] + [' '.join(cells[ncol - 1:])]
        cells = (cells + [''] * ncol)[:ncol]
        out = []
        for c in cells:
            t = inline_cell(c)
            out.append(r'\textbf{%s}' % t if bold else t)
        return ' & '.join(out) + r' \\ \hline'

    lines = [r'\begin{longtable}{%s}' % column_spec(ncol), r'\hline']
    if head:
        lines.append(row(head, bold=True))
    lines.append(r'\endhead')
    for r in body:
        lines.append(row(r))
    lines.append(r'\end{longtable}')
    return '\n'.join(lines)


_STRAY_ENV = re.compile(r'\\(?:begin|end)\{(equation\*?|align\*?|gather\*?|displaymath)\}')
# a lone \end{equation*} left behind when a $$ block carried a redundant pair
_LONE_STRAY = re.compile(r'\\(?:begin|end)\{(?:equation\*?|align\*?|gather\*?|displaymath)\}')
_INNER_ENVS = ('array', 'aligned', 'matrix', 'bmatrix', 'pmatrix', 'cases', 'split')


def balance_left_right(s: str) -> str:
    """Balance \\left / \\right so a half-equation still compiles."""
    nleft = len(re.findall(r'\\left\b', s))
    nright = len(re.findall(r'\\right\b', s))
    if nleft > nright:
        s = s.rstrip() + ' ' + r'\right.' * (nleft - nright)
    elif nright > nleft:
        s = r'\left.' * (nright - nleft) + ' ' + s.lstrip()
    return s


def _split_at_tags(body: str) -> list[tuple[str, str | None]]:
    """Cut the body at every \\tag{}, returning (content, tag) pairs."""
    raw = []
    buf = body
    while True:
        idx = buf.find(r'\tag{')
        if idx < 0:
            raw.append((buf, None))
            break
        end = buf.find('}', idx + 5)
        if end < 0:
            raw.append((buf, None))
            break
        raw.append((buf[:idx], buf[idx + 5:end].strip()))
        buf = buf[end + 1:]
    return raw


_ONLY_CLOSERS = re.compile(
    r'^(?:\s|\\(?:end\{[A-Za-z*]+\}|right\.|left\.|tag\{[^}]*\}|,|;|\.))*$')


def is_structural_only(s: str) -> bool:
    """True when a segment holds nothing but stray closers (no real maths).

    When a source block writes "\\tag{2.3}" before "\\end{array}", splitting at
    the tag leaves a trailing segment containing just "\\end{array}". Emitting
    that would produce an equation with no content, so it is dropped.
    """
    return bool(_ONLY_CLOSERS.match(s))


def normalize_display(body: str) -> tuple[str, str | None]:
    """Clean one display equation and report its tag.

    * removes a redundant \\begin/\\end{equation*} pair that some source blocks
      carry inside the $$ ... $$
    * closes any inner environment (array/aligned/...) that is still open, so
      the \\tag that follows it is legal — LaTeX rejects \\tag inside array
    * balances \\left / \\right
    """
    tags = re.findall(r'\\tag\{[^}]*\}', body)
    text = _LONE_STRAY.sub('', body)
    text = re.sub(r'\\tag\{[^}]*\}', '', text)
    text = text.strip().strip(',').strip()

    opens = re.findall(r'\\begin\{([A-Za-z*]+)\}', text)
    closes = re.findall(r'\\end\{([A-Za-z*]+)\}', text)
    pending = list(opens)
    for name in closes:
        if name in pending:
            pending.remove(name)
    for name in reversed(pending):
        if name in _INNER_ENVS:
            text = text.rstrip() + '\n\\end{%s}' % name

    text = balance_left_right(text)
    tag = None
    if tags:
        tag = re.match(r'\\tag\{(.*)\}$', tags[-1], re.S).group(1).strip()
    return text, tag


def needs_shrink(text: str) -> bool:
    """True when a display is structurally too wide for the text block.

    Displays that contain an inner aligned/array/matrix are multi-line and
    cannot break within a row, so a long one will always overflow; those are
    scaled down. It is harmless to shrink a display that would have fitted.
    """
    if len(text) >= 220:
        return True
    return text.count('&') >= 12


def math_block(body: str, indent: str = '', eqno: str | None = None) -> str:
    """Render one $$ ... $$ block, preserving every original tag.

    A block may contain several tagged equations; each becomes its own
    numbered display so the book keeps its own numbering scheme. Each numbered
    display also gets \\label{eq:...} so that "式 (2.16)" can be made clickable.
    """
    pieces: list[tuple[str, str | None]] = []
    segments = _split_at_tags(body)
    for content, tag in segments:
        if is_structural_only(content):
            continue
        text, own = normalize_display(content)
        if own is None:
            own = tag
        if not text or is_structural_only(text):
            continue
        pieces.append((text, own))

    out = []
    for text, tag in pieces:
        shrink = needs_shrink(text)
        if shrink:
            # adjustbox sits INSIDE the maths, so no \ensuremath is involved
            text = ('\\begin{adjustbox}{max width=\\linewidth}\n%s\n'
                    '\\end{adjustbox}' % text)
        if tag:
            label = '\\label{%s}' % eq_label(tag)
            out.append('%s\\begin{equation}\n%s\n\\tag{%s}%s\n%s\\end{equation}'
                       % (indent, text, tag, label, indent))
        else:
            out.append('%s\\begin{equation*}\n%s\n%s\\end{equation*}'
                       % (indent, text, indent))
    return '\n'.join(out)


_CJK_RE = re.compile(r'[\u3000-\u303f\u4e00-\u9fff\uff00-\uffef]')
_TEXT_OR_TEXTB = re.compile(r'\\text(?:cn)?\{[^{}]*\}')
_CJK_RUN = re.compile(r'[\u3000-\u303f\u4e00-\u9fff\uff00-\uffef]+')

# Maths regions in the FINAL output: either the original $ delimiters (inline
# maths that was kept inline) or the amsmath environments the converter emits.
_MATH_ENV = (r'equation\*?|align\*?|gather\*?|multline\*?|displaymath|'
             r'flalign\*?|alignat\*?')
_REGIONS = [
    (re.compile(r'\\begin\{(?:%s)\}(?:.|\n)*?\\end\{(?:%s)\}' % (_MATH_ENV, _MATH_ENV)),
     'env'),
    (re.compile(r'\\\$.'), 'skip'),
    (re.compile(r'(?<!\\)\$\$(?!\$)(?:[^$]|\$(?!\$))+?(?<!\\)\$\$(?!\$)'), 'delim'),
    (re.compile(r'(?<!\\)\$(?!\$)(?:[^$\n]|\$(?!\$))+?(?<!\\)\$(?!\$)'), 'delim'),
]
_REGION_MASTER = re.compile('|'.join('(?:%s)' % p.pattern for p, _ in _REGIONS), re.S)


def _region_kind(text: str, m) -> str:
    if text.startswith('\\begin{', m.start()):
        return 'env'
    return 'delim'


def cjk_in_math(text: str) -> str:
    r"""Wrap CJK that sits in maths with \textcn so it uses the CJK font.

    Two cases occur in the sources:

    * Chinese inside \text{...} — amsmath switches to the Latin text font, which
      has no CJK glyphs;
    * Chinese entirely outside any \text{}, e.g. "... \quad \text{对所有 } i =
      1, \ldots, m 。" where the final full stop is bare maths.

    \\textcn{} is defined in main.tex and uses \\mbox so the CJK font applies.
    """
    out = []
    pos = 0
    for m in _REGION_MASTER.finditer(text):
        region = m.group(0)
        out.append(text[pos:m.start()])
        if region.startswith('\\$'):
            out.append(region)                      # escaped literal dollar
        else:
            out.append(_fix_math_region(region))
        pos = m.end()
    out.append(text[pos:])
    return ''.join(out)


def _fix_math_region(region: str) -> str:
    """Replace CJK inside one maths region, leaving existing \\text*{} alone."""
    pieces = []
    last = 0
    for tm in _TEXT_OR_TEXTB.finditer(region):
        pieces.append(_wrap_cjk(region[last:tm.start()]))
        cmd = tm.group(0)
        if not cmd.startswith('\\textcn') and _CJK_RE.search(cmd):
            cmd = '\\textcn' + cmd[len('\\text'):]
        pieces.append(cmd)
        last = tm.end()
    pieces.append(_wrap_cjk(region[last:]))
    return ''.join(pieces)


def _wrap_cjk(s: str) -> str:
    if not _CJK_RE.search(s):
        return s
    return _CJK_RUN.sub(lambda m: '\\textcn{%s}' % m.group(0), s)


def cjk_in_text(text: str) -> str:
    """Entry point used by convert(): route all maths CJK to the CJK font."""
    return cjk_in_math(text)


# --------------------------------------------------------------------------
# cross reference labels
# --------------------------------------------------------------------------
def eq_label(tag: str) -> str:
    """Label for a numbered equation, e.g. 2.16 -> eq:2-16."""
    return 'eq:' + tag.replace('.', '-')


def fig_label(num: str) -> str:
    return 'fig:' + num.replace('.', '-')


# "式 (2.16)" / "式(2.16)" -> clickable reference
_EQUATION_REF = re.compile(r'式\s*[（(]\s*(\d+\.\d+[a-z]?)\s*[)）]')
# "图 3.4" / "图3.14" -> clickable reference. The negative lookahead keeps an
# already-linked "图~\ref{...}" or a caption header "图~\thefigcounter" intact.
_FIGURE_REF = re.compile(r'图(?!\s*~?\s*\\)\s*(\d+\.\d+)')
# "表 8.1" -> clickable reference
_TABLE_REF = re.compile(r'表(?!\s*~?\s*\\)\s*(\d+\.\d+)')


def link_references(text: str, fig_nums: set[str], tab_nums: set[str]) -> str:
    r"""Turn "式 (2.16)", "图 3.4", "表 8.1" into hyperlinks.

    Only references whose target actually exists get a link, so a stray number
    never produces an unresolved reference. Maths regions are skipped so that a
    formula containing 图/表/式 is left alone.
    """
    def eq_repl(m):
        tag = m.group(1)
        if tag not in EQ_TAGS_SEEN:
            return m.group(0)
        return '式~\\eqref{%s}' % eq_label(tag)

    def fig_repl(m):
        num = m.group(1)
        if num not in fig_nums:
            return m.group(0)
        return '图~\\ref{%s}' % fig_label(num)

    def tab_repl(m):
        num = m.group(1)
        if num not in tab_nums:
            return m.group(0)
        return '表~\\ref{%s}' % tab_label(num)

    out = []
    pos = 0
    for m in _REGION_MASTER.finditer(text):
        chunk = text[pos:m.start()]
        out.append(_apply_refs(chunk, eq_repl, fig_repl, tab_repl))
        out.append(m.group(0))
        pos = m.end()
    out.append(_apply_refs(text[pos:], eq_repl, fig_repl, tab_repl))
    return ''.join(out)


def _apply_refs(chunk, eq_repl, fig_repl, tab_repl):
    if '式' in chunk:
        chunk = _EQUATION_REF.sub(eq_repl, chunk)
    if '图' in chunk:
        chunk = _FIGURE_REF.sub(fig_repl, chunk)
    if '表' in chunk:
        chunk = _TABLE_REF.sub(tab_repl, chunk)
    return chunk


def tab_label(num: str) -> str:
    return 'tab:' + num.replace('.', '-')


# filled in by main(): the equation tags and figure/table numbers that exist
EQ_TAGS_SEEN: set[str] = set()
FIG_NUMS_SEEN: set[str] = set()
TAB_NUMS_SEEN: set[str] = set()
# only the numbers that actually got a \label while converting; a reference to a
# figure the translation never included must stay plain text, not a dead link
FIG_TARGETS: set[str] = set()
TAB_TARGETS: set[str] = set()


def index_existing():
    """Collect the tags / figure / table numbers present in the sources."""
    for p in gather():
        t = open(p, encoding='utf-8').read()
        for m in re.finditer(r'\\tag\{([^}]*)\}', t):
            EQ_TAGS_SEEN.add(m.group(1).strip())
        for m in re.finditer(r'图\s*(\d+\.\d+)', t):
            FIG_NUMS_SEEN.add(m.group(1))
        for m in re.finditer(r'表\s*(\d+\.\d+)', t):
            TAB_NUMS_SEEN.add(m.group(1))


def convert(md: str, *, is_chapter_start: bool = False) -> tuple[str, dict]:
    """Convert one markdown file body into LaTeX."""
    lines = md.replace('\r\n', '\n').split('\n')
    out: list[str] = []
    meta = {'title': None, 'sections': []}
    i = 0
    n = len(lines)
    in_code = False
    code_buf: list[str] = []

    while i < n:
        line = lines[i]
        stripped = line.strip()

        # ---- code fences (only 2 in the whole book) ----
        if stripped.startswith(FENCE):
            if not in_code:
                in_code = True
                code_buf = []
            else:
                in_code = False
                out.append('\\begin{quote}\\ttfamily\\small\n'
                           + '\n'.join(esc_text(x) for x in code_buf)
                           + '\n\\end{quote}')
            i += 1
            continue
        if in_code:
            code_buf.append(line)
            i += 1
            continue

        # ---- table caption "**表 8.1** ..." ----
        # Tested first: as a standalone line it would otherwise be swallowed by
        # the paragraph branch, leaving "表 8.1" references with no target.
        # Requiring the bold marker is what distinguishes a caption from prose
        # that merely starts with "表 6.2 ...".
        mt = re.match(r'^\s*\*\*\s*表\s*(\d+\.\d+)\s*\*\*\s*(.*)$', stripped, re.S)
        if mt and len(stripped) < 240:
            rest = mt.group(2).strip()
            num = mt.group(1)
            TAB_TARGETS.add(num)
            body = ('\\quad %s' % inline(rest)) if rest else ''
            out.append('\\refstepcounter{tabcounter}'
                       '\\label{%s}表~\\thetabcounter%s' % (tab_label(num), body))
            i += 1
            continue

        # ---- display maths ----
        if stripped.startswith('$$'):
            # NB: after trimming markdown, "$$ " (trailing space) is a very
            # common form, so the remainder must be stripped before testing.
            rest = stripped[2:].strip()
            buf = []
            if rest.endswith('$$') and len(rest) > 2:
                # single-line form:  $$ formula $$
                buf.append(rest[:-2])
                i += 1
            else:
                if rest:
                    buf.append(rest)
                i += 1
                while i < n:
                    s2 = lines[i].strip()
                    if s2.endswith('$$'):
                        head = s2[:-2].strip()
                        if head:
                            buf.append(head)
                        i += 1
                        break
                    buf.append(re.sub(r'^>\s?', '', lines[i]))
                    i += 1
            out.append(math_block('\n'.join(buf)))
            continue

        # ---- blockquote (the book's "例 / 备注 / 定理" side notes) ----
        if stripped.startswith('>'):
            buf = []
            while i < n:
                cur = lines[i]
                if cur.strip().startswith('>'):
                    buf.append(re.sub(r'^\s*>\s?', '', cur))
                    i += 1
                    continue
                # A display equation may open inside the quote and only close on
                # a following non-quoted line (the sources do this), so keep
                # consuming lines until the $$ pairs balance again.
                joined = '\n'.join(buf)
                if joined.count('$$') % 2 == 1 and not cur.strip().endswith('$$'):
                    buf.append(cur)
                    i += 1
                    continue
                if joined.count('$$') % 2 == 1:
                    # this line closes the display that opened inside the quote
                    buf.append(cur)
                    i += 1
                break
            out.append(note_block(buf))
            continue

        # ---- markdown table ----
        if stripped.startswith('|'):
            rows = []
            while i < n and lines[i].strip().startswith('|'):
                rows.append(lines[i])
                i += 1
            # The caption "**表 8.1** ..." sits on a following line and is
            # absorbed into the next paragraph, so look ahead to register the
            # number that the table will actually be labelled with.
            for la in range(i, min(n, i + 3)):
                cm = re.match(r'^\s*\*{0,2}\s*表\s*(\d+\.\d+)', lines[la])
                if cm:
                    TAB_TARGETS.add(cm.group(1))
                    break
            for r in rows:
                for tm in re.finditer(r'表\s*(\d+\.\d+)', r):
                    TAB_TARGETS.add(tm.group(1))
            out.append(table_to_latex(rows))
            continue

        # ---- html <p align="center"> ... </p> wrapper ----
        if stripped.startswith('<p align="center"') or stripped.startswith('<div align="center"'):
            buf = []
            close = '</p>' if stripped.startswith('<p') else '</div>'
            i += 1
            while i < n and close not in lines[i]:
                buf.append(lines[i])
                i += 1
            i += 1
            blk = '\n'.join(buf)
            m = _IMG_TAG.search(blk)
            if m:
                src = _attr(m.group(1), 'src') or ''
                alt = _attr(m.group(1), 'alt') or ''
                title = _attr(m.group(1), 'title') or ''
                width = _attr(m.group(1), 'width')
                cap = title or alt
                # a <b> caption after the image is more reliable than the attr
                mb = re.search(r'<b>(.*?)</b>', blk, re.S)
                if mb:
                    cap = re.sub(r'<[^>]+>', '', mb.group(1)).strip()
                out.append(figure(src, cap, title, width))
            else:
                txt = re.sub(r'<[^>]+>', '', blk).strip()
                if txt:
                    out.append('\\begin{center}%s\\end{center}' % inline(txt))
            continue

        # ---- headings ----
        m = re.match(r'^(#{1,6})\s+(.*)$', line)
        if m:
            level = len(m.group(1))
            text = m.group(2).strip()
            out.append(heading(level, text, meta))
            i += 1
            continue

        # ---- horizontal rule ----
        if re.match(r'^-{3,}\s*$', stripped):
            out.append('\\medskip\\hrule\\medskip')
            i += 1
            continue

        # ---- a standalone <br> is a spacer, not a line break ----
        # ("\newline" with nothing before it raises "There's no line here to end")
        if re.fullmatch(r'(?:<br\s*/?>\s*)+', stripped):
            i += 1
            continue

        # ---- lists ----
        if re.match(r'^\s*[-*+]\s+', line) or re.match(r'^\s*\d+\.\s+', line):
            buf = []
            while i < n and (re.match(r'^\s*[-*+]\s+', lines[i])
                             or re.match(r'^\s*\d+\.\s+', lines[i])
                             or (lines[i].startswith(('  ', '\t')) and lines[i].strip())):
                buf.append(lines[i])
                i += 1
            out.append(list_block(buf))
            continue

        # ---- blank ----
        if not stripped:
            i += 1
            continue

        # ---- paragraph ----
        buf = []
        while i < n and lines[i].strip() and not re.match(
                r'^(#{1,6}\s|\s*[-*+]\s|\s*\d+\.\s|>|\||\$\$|<p align|<div align)', lines[i].strip()) \
                and not lines[i].strip().startswith(FENCE) \
                and not re.match(r'^-{3,}\s*$', lines[i].strip()):
            buf.append(lines[i])
            i += 1
        if buf:
            out.append(paragraph_with_math(buf))
    joined = '\n\n'.join(x for x in out if x.strip())
    joined = cjk_in_text(joined)
    joined = link_references(joined, FIG_TARGETS, TAB_TARGETS)
    return joined, meta


def split_item_math(text: str) -> tuple[str, str | None]:
    """Return (item prose, display maths or None) for one list item.

    Three of the book's equations (2.66, 2.77, 2.124a/b) live inside bullet
    items, where a \\tag would otherwise be dropped by LaTeX. The equation is
    returned separately so the caller can close the list, emit the display and
    reopen the list.
    """
    pieces = tagged_math_parts(text)
    if len(pieces) == 1:
        return text, None
    prose: list[str] = []
    maths: list[str] = []
    for kind, payload in pieces:
        if kind == 'text':
            if payload.strip():
                prose.append(payload.strip())
        else:
            maths.append(math_block(payload))
    return ' '.join(prose), '\n'.join(maths) if maths else None


def paragraph_with_math(lines: list[str]) -> str:
    """Render a paragraph, lifting tagged/too-wide inline maths into displays.

    A line that ends with the "$$" that OPENS a display equation (the sources
    frequently write "... 由下式给出 $$" and put the maths on the next line)
    must not leave those dollars in the text: joining the buffered lines with a
    space would create a stray "$$" and desynchronise inline-maths matching.
    """
    buf: list[str] = []
    out: list[str] = []

    def flush():
        if buf:
            out.append(inline(' '.join(buf)))
            buf.clear()

    for line in lines:
        s = line.strip()
        # the display opener is handled by the caller; just record its lead-in
        if s.endswith('$$') and not s.endswith('$$$'):
            s = s[:-2].rstrip()
        pieces = tagged_math_parts(s)
        if len(pieces) == 1:
            if s:
                buf.append(s)
            continue
        for kind, payload in pieces:
            if kind == 'text':
                if payload.strip():
                    buf.append(payload.strip())
            else:
                flush()
                out.append(math_block(payload))
    flush()
    return '\n\n'.join(x for x in out if x.strip())


def heading(level: int, text: str, meta: dict) -> str:
    """Map markdown heading level onto the book's sectioning scheme."""
    num = re.match(r'^(\d+(?:\.\d+)*)\s+(.*)$', text)
    if level <= 2:
        # chapter opener: "2 线性代数" (whole chapter) or "4.5 奇异值分解"
        meta['title'] = text
        if num and '.' not in num.group(1):
            meta['chapter_number'] = num.group(1)
            return '\\chapter{%s}' % inline(text)
        # a chapter file that is really just one section of a chapter: starred
        # section + its own label so subsections can \ref it
        if num:
            meta['section_owner'] = num.group(1)
            return ('\\section*{%s}\n\\addcontentsline{toc}{section}{%s}\n'
                    '\\label{sec:%s}' % (inline(text), inline(text), num.group(1)))
        meta['section_owner'] = None
        return '\\chapter*{%s}\n\\addcontentsline{toc}{section}{%s}' % (
            inline(text), inline(text))
    if level == 3:
        meta['sections'].append(text)
        return '\\section*{%s}\n\\addcontentsline{toc}{subsection}{%s}' % (
            inline(text), inline(text))
    if level == 4:
        return '\\subsection*{%s}\n\\addcontentsline{toc}{subsubsection}{%s}' % (
            inline(text), inline(text))
    return '\\subsubsection*{%s}' % inline(text)


def list_block(buf: list[str]) -> str:
    """Convert a run of markdown list items into properly nested LaTeX lists.

    A stack records which environment is open at each depth, because the marked
    and ordered kinds can alternate between levels (the sources do exactly that,
    e.g. an enumerate whose third item contains a nested enumerate).
    """
    items = []          # (indent, ordered, text)
    for raw in buf:
        m = re.match(r'^(\s*)([-*+]|\d+\.)\s+(.*)$', raw)
        if m:
            items.append((len(m.group(1)), m.group(2)[0].isdigit(), m.group(3)))
        elif items:
            items[-1] = (items[-1][0], items[-1][1], items[-1][2] + ' ' + raw.strip())
    if not items:
        return ''

    stack: list[str] = []          # environment name per open depth
    out: list[str] = []
    for indent, is_ord, text in items:
        want = 1 if indent >= 2 else 0
        # close deeper levels
        while len(stack) > want + 1:
            out.append(r'\end{%s}' % stack.pop())
        # open / switch the current level
        env = 'enumerate' if is_ord else 'itemize'
        if len(stack) == want + 1 and stack[-1] != env:
            out.append(r'\end{%s}' % stack.pop())
        while len(stack) < want + 1:
            out.append(r'\begin{%s}' % env)
            stack.append(env)
        prose, maths = split_item_math(text)
        out.append(r'\item %s' % inline(prose))
        if maths:
            # close the list so the numbered display is not indented into it
            while stack:
                out.append(r'\end{%s}' % stack.pop())
            out.append(maths)
            # reopen at the same level for the following items
            out.append(r'\begin{%s}' % env)
            stack.append(env)
    while stack:
        out.append(r'\end{%s}' % stack.pop())
    return '\n'.join(out)


def note_block(buf: list[str]) -> str:
    """A blockquote becomes one or more styled 'note' boxes.

    A blank quoted line separates independent notes; keeping them apart also
    lets each box break across pages on its own.
    """
    groups: list[list[str]] = [[]]
    for raw in buf:
        if raw.strip() == '':
            if groups[-1]:
                groups.append([])
            continue
        groups[-1].append(raw)
    groups = [g for g in groups if g]
    if not groups:
        return ''
    rendered = []
    for g in groups:
        inner, _ = convert('\n'.join(g))
        if inner.strip():
            rendered.append('\\begin{notebox}\n%s\n\\end{notebox}' % inner)
    return '\n\n'.join(rendered)


# --------------------------------------------------------------------------
# driver
# --------------------------------------------------------------------------
FRONT = {'0.Foreword.md'}
BACK = {'3.References.md': 'references', '4.Index.md': 'index'}


def gather():
    files = []
    for dp, dn, fn in os.walk(ROOT):
        parts = dp.split(os.sep)
        if any(p in ('.idea',) or p.startswith('.backup_') or p in ('latex-book',) for p in parts):
            continue
        for f in fn:
            if f.endswith('.md') and f != 'README.md':
                files.append(os.path.join(dp, f))
    return sorted(files)


def order_key(p):
    r = os.path.relpath(p, ROOT).replace('\\', '/')
    if r == '0.Foreword.md':
        return (0, 0, 0)
    if r == '3.References.md':
        return (99, 0, 0)
    if r == '4.Index.md':
        return (100, 0, 0)
    m = re.match(r'^(\d+)\.Part [^/]+/(\d+)/(?:(\d+)\.(\d+))?', r)
    if m:
        part = int(m.group(1)); ch = int(m.group(2))
        sec = int(m.group(4)) if m.group(4) else -1
        return (part * 10 + ch // 100, ch, sec)
    return (500, 0, 0)


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    files = sorted(gather(), key=order_key)
    # first pass: learn which equations / figures / tables exist so that only
    # real targets become hyperlinks
    index_existing()
    print('targets: %d equations, %d figures, %d tables'
          % (len(EQ_TAGS_SEEN), len(FIG_NUMS_SEEN), len(TAB_NUMS_SEEN)))
    manifest = []
    for idx, p in enumerate(files):
        rel = os.path.relpath(p, ROOT).replace('\\', '/')
        md = open(p, encoding='utf-8').read()
        tex, meta = convert(md)
        stem = 'c%03d_%s' % (idx, re.sub(r'[^A-Za-z0-9]+', '_', os.path.splitext(os.path.basename(p))[0]))
        dest = os.path.join(OUTDIR, stem + '.tex')
        with open(dest, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(tex + '\n')
        manifest.append({'index': idx, 'source': rel, 'tex': 'chapters/' + stem + '.tex',
                         'title': meta.get('title'), 'sections': meta['sections'],
                         'chars': len(md)})
        print('%-64s -> %-42s %6d chars, %2d sections'
              % (rel, stem + '.tex', len(md), len(meta['sections'])))
    with open(os.path.join(HERE, '_manifest.json'), 'w', encoding='utf-8') as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=1)
    print('\nconverted %d files; manifest written.' % len(files))
    return 0


if __name__ == '__main__':
    sys.exit(main())
