#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate main.tex (the book driver) from _manifest.json."""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
manifest = json.load(open(os.path.join(HERE, '_manifest.json'), encoding='utf-8'))

PART1 = '1.Part I Mathematical Foundations'
PART2 = '2.Part II Central Machine Learning Problems'

part1, part2, back = [], [], []
for m in manifest:
    src = m['source']
    inc = m['tex'].replace('.tex', '')
    if src == '0.Foreword.md':
        continue                      # front matter, handled separately
    if src in ('3.References.md', '4.Index.md'):
        back.append(inc)
    elif src.startswith(PART1):
        part1.append(inc)
    elif src.startswith(PART2):
        part2.append(inc)
    else:
        part1.append(inc)

# the foreword is a front-matter chapter; find it again cleanly
foreword = [m['tex'].replace('.tex', '') for m in manifest if m['source'] == '0.Foreword.md'][0]

PREAMBLE = r"""%=====================================================================
%  《机器学习中的数学》中文版 —— 合订本
%  Mathematics for Machine Learning (Chinese translation), single volume
%
%  本文件由 gen_main.py 自动生成，请勿手工编辑。
%  编译（需 XeLaTeX）：
%      latexmk -xelatex main.tex
%  或：  xelatex main.tex   (连续运行 3 次以生成目录 / 书签)
%=====================================================================
\documentclass[11pt,openany,oneside]{book}

%------------------------- 中文支持 -----------------------------------
\usepackage[UTF8,scheme=chinese,fontset=none,heading=true]{ctex}
\usepackage{fontspec}
% 正文宋体、标题黑体 —— 中文科技书常见搭配
\setCJKmainfont{SimSun}[BoldFont=SimHei,ItalicFont=KaiTi]
\setCJKsansfont{SimHei}
\setCJKmonofont{FangSong}
\setCJKfamilyfont{zhkai}{KaiTi}
\setCJKfamilyfont{zhfs}{FangSong}
\setCJKfamilyfont{zhhei}{SimHei}
\newcommand{\kai}{\CJKfamily{zhkai}}
\newcommand{\hei}{\CJKfamily{zhhei}}

%------------------------- 数学 ---------------------------------------
\usepackage{amsmath,amssymb,amsfonts,mathtools}
\usepackage{bm}
% amsmath 的 \text{} 会切到拉丁正文字体，其中没有汉字，中文会变成空白；
% \textcn 用 \mbox 让中文落到 CJK 字体上（用于公式内的中文说明）
\newcommand{\textcn}[1]{\mbox{\mdseries\upshape #1}}
% 正文里出现的真正 Unicode 上下标（下标 ₁₂₃₅₀、上标 ⁴⁻ᵀᵢ 等）统一交给数学模式排版
\usepackage{newunicodechar}
\newunicodechar{₀}{\textsubscript{0}}
\newunicodechar{₁}{\textsubscript{1}}
\newunicodechar{₂}{\textsubscript{2}}
\newunicodechar{₃}{\textsubscript{3}}
\newunicodechar{₅}{\textsubscript{5}}
\newunicodechar{ᵢ}{\textsubscript{i}}
\newunicodechar{⁴}{\textsuperscript{4}}
\newunicodechar{⁻}{\textsuperscript{\textminus}}
\newunicodechar{ᵀ}{\textsuperscript{T}}
\newunicodechar{ˣ}{\textsuperscript{x}}
\newunicodechar{ℓ}{\ensuremath{\ell}}
\newunicodechar{∈}{\ensuremath{\in}}
\newunicodechar{ℝ}{\ensuremath{\mathbb{R}}}
\newunicodechar{⊥}{\ensuremath{\perp}}
\newunicodechar{∥}{\ensuremath{\parallel}}
\newunicodechar{∑}{\ensuremath{\sum}}
\newunicodechar{⊗}{\ensuremath{\otimes}}
\newunicodechar{♦}{\ensuremath{\blacklozenge}}
\newunicodechar{α}{\ensuremath{\alpha}}
\newunicodechar{β}{\ensuremath{\beta}}
\newunicodechar{δ}{\ensuremath{\delta}}
\newunicodechar{θ}{\ensuremath{\theta}}
\newunicodechar{λ}{\ensuremath{\lambda}}
\newunicodechar{μ}{\ensuremath{\mu}}
\newunicodechar{π}{\ensuremath{\pi}}
\newunicodechar{σ}{\ensuremath{\sigma}}
\newunicodechar{ω}{\ensuremath{\omega}}

%------------------------- 版面与图形 ---------------------------------
\usepackage[a4paper,inner=2.7cm,outer=2.3cm,top=2.7cm,bottom=2.5cm,
            footskip=1.0cm]{geometry}
\usepackage{graphicx}
\usepackage{float}
\usepackage{booktabs,longtable,array}
\usepackage{enumitem}
\usepackage{multicol}
\usepackage{xcolor}
\usepackage{fancyhdr}
\usepackage{titlesec}
\usepackage{tocloft}
\usepackage{needspace}
\usepackage{mdframed}
\usepackage{adjustbox}
\usepackage[hidelinks,bookmarksnumbered=true,bookmarksopen=true,
            pdfstartview=FitH]{hyperref}
\usepackage{bookmark}
\usepackage{caption}

% 索引页码链接：\hyperpage{N} 放置隐藏锚点，索引中的页码即可点击跳转
% （必须在 hyperref 之后定义，\Hy@raisedlink 由它提供）
\newcommand{\hyperpage}[1]{\Hy@raisedlink{\hypertarget{page.#1}{}}#1}

\graphicspath{{docs/images/}}

\definecolor{notebg}{RGB}{247,247,245}
\definecolor{noterule}{RGB}{198,198,192}

% 行内数组列间距略收紧：书中大量使用 array 排版对齐公式，
% 默认 5pt 的 \arraycolsep 会让宽阵列溢出文本宽度
\setlength{\arraycolsep}{3pt}
% 表格列宽按 \tabcolsep 精确扣减（见 md2tex.py 的 column_spec）
\setlength{\tabcolsep}{6pt}

%------------------------- 标题样式 -----------------------------------
% 章节标题自带 "2.3" 之类的编号，因此用带星号的标题命令，只用 \chapter 驱动页眉页码
\renewcommand{\chaptername}{}
\ctexset{
  chapter/format={\hei\LARGE\raggedright},
  chapter/beforeskip={1ex plus .3ex},
  chapter/afterskip={2.2ex plus .3ex},
  section/format={\hei\large\raggedright},
  section/beforeskip={2.3ex plus .4ex minus .2ex},
  section/afterskip={1.0ex plus .2ex},
  subsection/format={\hei\normalsize\raggedright},
  subsubsection/format={\hei\normalsize\raggedright},
}
\titleformat{\chapter}[display]
  {\hei\LARGE\raggedright}{}{0pt}{\Large\bfseries}%
  [\vspace{-0.7em}\rule{\textwidth}{0.6pt}]
\titlespacing*{\chapter}{0pt}{0.6ex}{2.0em}

%------------------------- 目录 ---------------------------------------
\renewcommand{\cftchapfont}{\hei}
\renewcommand{\cftchappagefont}{\normalfont}
\renewcommand{\cftsecfont}{\normalfont}
\renewcommand{\cftsubsecfont}{\small\normalfont}
\renewcommand{\cftsubsubsecfont}{\small\normalfont}
\setlength{\cftbeforechapskip}{0.5em}
\setlength{\cftbeforesecskip}{0.10em}
\setlength{\cftbeforesubsecskip}{0.02em}
\renewcommand{\cftchapleader}{\cftdotfill{\cftdotsep}}

%------------------------- 页眉页脚 -----------------------------------
\pagestyle{fancy}
\fancyhf{}
\renewcommand{\headrulewidth}{0.4pt}
\fancyhead[L]{\small\kai 机器学习中的数学}
\fancyhead[R]{\small\thepage}
\fancypagestyle{plain}{%
  \fancyhf{}\fancyhead[R]{\small\thepage}%
  \renewcommand{\headrulewidth}{0pt}}

%------------------------- 提示框（例 / 备注 / 定理 / 定义）-----------
% mdframed 可以跨页断开，minipage 方案会在跨页时画出贯穿整页的竖线
\mdfdefinestyle{notestyle}{%
  linecolor=noterule, linewidth=1.6pt, topline=false, bottomline=false,
  rightline=false, leftline=true, backgroundcolor=notebg,
  innerleftmargin=0.7em, innerrightmargin=0.6em,
  innertopmargin=0.5em, innerbottommargin=0.5em,
  skipabove=0.8em, skipbelow=0.8em, nobreak=false}
\newmdenv[style=notestyle]{notebox}

%------------------------- 细节 ---------------------------------------
% 原书的图 / 表编号自带章号（图 4.8、表 8.1），因此用 \label + \ref 生成
% 可点击引用，而 \caption* 不会改动编号，编号始终取自图题文字本身。
\newcounter{figcounter}[chapter]
\newcounter{tabcounter}[chapter]
\renewcommand{\thefigcounter}{\thechapter.\arabic{figcounter}}
\renewcommand{\thetabcounter}{\thechapter.\arabic{tabcounter}}
\captionsetup{font=small,labelformat=empty,justification=centering,skip=6pt}
\setlength{\parindent}{2em}
\linespread{1.16}
\setlength{\parskip}{0.2ex plus 0.1ex}
\setlist[itemize]{topsep=0.4ex,itemsep=0.15ex,parsep=0pt,leftmargin=2.2em}
\setlist[enumerate]{topsep=0.4ex,itemsep=0.15ex,parsep=0pt,leftmargin=2.4em}
\allowdisplaybreaks
% 书中若干段落含很宽的行内公式，给断行留一点弹性以减少溢出
\emergencystretch=2.5em
\newcommand{\Lcol}[1]{>{\raggedright\arraybackslash}p{#1}}

\begin{document}

%========================= 封面 =======================================
\begin{titlepage}
\centering
\vspace*{2.4cm}
{\hei\fontsize{30}{38}\selectfont 机器学习中的数学\par}
\vspace{1.2cm}
{\LARGE\itshape Mathematics for Machine Learning\par}
\vspace{0.55cm}
{\large\kai 中文翻译版\par}
\vspace{2.8cm}
{\large Marc Peter Deisenroth\quad A.\ Aldo Faisal\quad Cheng Soon Ong\ \ 著\par}
\vspace{0.8cm}
{\large 社区翻译\par}
\vspace{3.0cm}
{\large 全书 12 章\quad·\quad 144 幅插图\quad·\quad 1{,}202 个编号公式\par}
\vfill
{\small 本译本依据原著公开版本翻译，原著版权归原作者所有。\par}
{\small 原书在线版：\href{https://mml-book.com}{https://mml-book.com}\par}
\vspace{1.2cm}
\end{titlepage}

%========================= 前言部分 ===================================
\frontmatter
\pagestyle{fancy}
\tableofcontents
\cleardoublepage

%========================= 正文 =======================================
\mainmatter
"""


def part_block(title, incs):
    out = ['', r'\part{%s}' % title, '']
    prev_ch = None
    for inc in incs:
        out.append(r'\input{%s}' % inc)
    return '\n'.join(out)


def main():
    pieces = [PREAMBLE]
    pieces.append(r'\input{%s}' % foreword)
    pieces.append(part_block('数学基础', part1))
    pieces.append(part_block('机器学习核心问题', part2))
    pieces.append('\n\\backmatter\n')
    for inc in back:
        pieces.append(r'\input{%s}' % inc)
    pieces.append('\n\\end{document}\n')
    dest = os.path.join(HERE, 'main.tex')
    with open(dest, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write('\n'.join(pieces))
    print('wrote %s' % dest)
    print('  front matter : 1 file (%s)' % foreword)
    print('  part I       : %d files' % len(part1))
    print('  part II      : %d files' % len(part2))
    print('  back matter  : %d files' % len(back))
    print('  total inputs : %d' % (1 + len(part1) + len(part2) + len(back)))


if __name__ == '__main__':
    main()
