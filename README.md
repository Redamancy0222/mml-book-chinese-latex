# 机器学习中的数学 · 中文版 LaTeX 合订本

> **Mathematics for Machine Learning（中文翻译版）** 的完整 LaTeX 工程与编译成品 PDF。

[![PDF](https://img.shields.io/badge/PDF-408%20%E9%A1%B5-red)](#-下载完整-pdf)
[![XeLaTeX](https://img.shields.io/badge/build-XeLaTeX-008080)](#-自行编译)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

---

## 📥 下载完整 PDF

**➡️ [点击下载《机器学习中的数学》中文版完整 PDF（408 页）](https://github.com/Redamancy0222/mml-book-chinese-latex/releases/latest)**

成品规格：

| 项目 | 数值 |
| --- | --- |
| 页数 | 408 页（A4） |
| 体积 | 约 11.8 MB |
| 插图 | 144 幅，全部内嵌 |
| 编号公式 | 1,203 个 |
| 参考文献 | 231 条 |
| 术语索引 | 459 条，其中 412 条带真实页码且可点击跳转 |
| 编译错误 | 0 |
| 未解析引用 | 0 |

---

## 来源声明与致谢
| 角色 | 贡献 | 链接 |
| --- | --- | --- |
| **原著作者** | Marc Peter Deisenroth、A. Aldo Faisal、Cheng Soon Ong 撰写 *Mathematics for Machine Learning*（Cambridge University Press, 2020），并在官网免费公开全书 | [mml-book.com](https://mml-book.com) · [原书仓库](https://github.com/mml-book/mml-book.github.io) |
| **中文译者** | 社区译者完成了**全部正文的中文翻译**——12 章、144 幅图、1,203 个公式。**这是本仓库全部内容的真正来源。** | [dxxzst/mml-book-chinese](https://github.com/dxxzst/mml-book-chinese) |
| **本仓库** | 由 **DeepSeek** 把上述中文 Markdown 译本转换为 LaTeX 工程，处理排版细节，编译为单一 PDF | 你正在看的这里 |

### 本仓库做了什么

把 Markdown 变成一本能印刷的书，需要处理的排版问题远超「格式转换」：

1. **公式编号完整保留** —— 不使用 LaTeX 计数器，而是保留原书每一个 `\tag{}`，因此 PDF 中的编号与 Markdown 源文件**完全一致**，可以两相对照检索。
2. **交叉引用可点击** —— 正文里的「式 (2.16)」「图 3.4」「表 8.1」全部改写成 `\eqref` / `\ref`，共 146 + 173 + 4 处，无一悬空。
3. **中文排版** —— 正文宋体、标题黑体、强调楷体；公式内的中文单独处理（`amsmath` 的 `\text{}` 会切到拉丁字体导致汉字空白）。
4. **版式** —— 提示框（例 / 备注 / 定理 / 定义）排成浅底竖线样式；超宽公式自动等比缩放；过长的行内公式提升为独立编号公式。
5. **术语索引** —— 原索引带的是**英文原书页码**，对本 PDF 毫无意义，因此改为扫描成品 PDF 反向生成**真实页码**。

---

## 📖 这本书讲什么

这不是一本讲「怎么调库」的书。它的出发点是：**很多人想深入理解机器学习，却卡在数学上。**

全书把机器学习所需的数学**集中讲清楚**，并且**直接说明每个数学概念在机器学习里有什么用**，而不是先讲一堆抽象定义再让你自己去联系。

### 全书结构

**第一部分 · 数学基础（第 1–7 章）**

| 章 | 内容 | 核心问题 |
| --- | --- | --- |
| 1 | 介绍和动机 | 为什么需要这些数学 |
| 2 | **线性代数** | 方程组、矩阵、向量空间、基与秩、线性映射、仿射空间 |
| 3 | **解析几何** | 范数、内积、长度与距离、夹角与正交性、正交投影、旋转 |
| 4 | **矩阵分解** | 行列式与迹、特征值、Cholesky、特征分解、**SVD**、矩阵近似 |
| 5 | **向量微积分** | 偏微分与梯度、矩阵梯度、**反向传播与自动微分**、泰勒级数 |
| 6 | **概率与分布** | 概率空间、贝叶斯定理、**高斯分布**、指数族、变量替换 |
| 7 | **连续优化** | 梯度下降、拉格朗日乘子、凸优化 |

**第二部分 · 机器学习核心问题（第 8–12 章）**

| 章 | 内容 | 核心问题 |
| --- | --- | --- |
| 8 | 当模型遇到数据 | 经验风险最小化、参数估计、有向图模型、模型选择 |
| 9 | **线性回归** | 最小二乘、**贝叶斯线性回归**、极大似然作为正交投影 |
| 10 | **主成分分析（PCA）** | 最大方差视角、投影视角、低秩近似、隐变量视角 |
| 11 | **高斯混合模型（GMM）** | 密度估计、极大似然、**EM 算法** |
| 12 | **支持向量机（SVM）** | 分隔超平面、软/硬间隔、对偶问题、**核方法** |

每一章末尾附**延伸阅读**，第一部分第 2–7 章还配有**练习**（共 75 道）。

### 适合谁读

- **本科高年级 / 研究生**：想补上机器学习背后的数学，而不是只会调用 `sklearn`；
- **转行者 / 自学者**：有高中数学基础（微积分、二维三维几何向量）即可开始；
- **从业者**：想搞清楚自己每天用的算法「为什么成立」、「边界在哪里」。

### 两种读法

原书前言给了两条路径，你可以按需选择：

- **自底向上**：老老实实从第 2 章线性代数读到第 7 章优化，再进入第二部分——适合系统学习；
- **按需跳读**：直接从第二部分挑一个感兴趣的问题（比如 PCA），遇到不懂的数学再回第一部分查——适合带着问题学。

---

## 🛠 自行编译

本仓库只包含**源文件**（不含 PDF 与中间产物），你可以完整复现这本书。

### 环境要求

- **XeLaTeX**（TeX Live 2023 已验证；需 `ctex`、`amsmath`、`mdframed`、`adjustbox`、`multicol` 等标准宏包）
- **Python 3.8+**，以及 `Pillow`（用于读取插图尺寸）
- 中文字体：**SimSun / SimHei / KaiTi / FangSong**（Windows 自带；其他平台可在 `gen_main.py` 中换字体）

### 一条命令

```bash
python make_book.py
```

它会**反复编译直到页码与索引都收敛**——因为索引里写的是硬页码，索引自身的长度又会影响其后的页码，必须迭代到不动点。成品在 `build/main.pdf`。

### 手工分步

```bash
python md2tex.py       # Markdown -> chapters/*.tex
python gen_main.py     # 生成 main.tex
xelatex main.tex       # 连编 4 次
python build_index.py  # 依据编译结果生成带真实页码的索引
xelatex main.tex       # 再连编 4 次
```

### 验收

```bash
python verify.py
```

会检查：编译错误、未解析引用、缺字、公式编号是否全部落进 PDF。当前基线：

```
pages               : 408
compile errors      : 0
undefined refs      : 0
missing chars       : 2
"Rerun to get"      : 0   ← 完全收敛
source \tag count   : 1203
tags missing in PDF : 0
RESULT: PASS
```

---

## 📂 仓库结构

```
.
├── main.tex              # 书籍主文件（由 gen_main.py 生成，勿手工编辑）
├── md2tex.py             # Markdown -> LaTeX 转换器，全部排版规则都在这里
├── gen_main.py           # 生成 main.tex：封面、前言、两部分正文、参考文献、索引
├── build_index.py        # 扫描成品 PDF，为 459 条术语生成真实页码
├── make_book.py          # 迭代编译至收敛
├── verify.py             # 成品验收
├── _manifest.json        # 99 个源文件的转换清单
├── chapters/             # 99 个转换后的 LaTeX 章节
└── docs/images/          # 144 幅插图
```

> `chapters/` 与 `main.tex` 是**生成产物**（约 1.1 MB），一并提交是为了让不想装 Python 的人也能直接 `xelatex main.tex` 编译。真正的源文件在上游译本仓库。

---

## 🤝 欢迎拉取校验

译文难免存在误译、术语不统一、公式笔误等问题。如果你发现任何问题，非常欢迎反馈：

## 📄 许可

- **译文与插图**：沿用上游译本 [dxxzst/mml-book-chinese](https://github.com/dxxzst/mml-book-chinese) 的 **MIT License**（Copyright © 2021 Grazing Wind），详见 [LICENSE](LICENSE)。
- **原著**：*Mathematics for Machine Learning* © 2020 Marc Peter Deisenroth, A. Aldo Faisal, Cheng Soon Ong，Cambridge University Press。作者在 [mml-book.com](https://mml-book.com) 免费公开全书，请以该官方版本为准。
- **本仓库的转换脚本与 LaTeX 工程**：同样以 MIT License 发布。

---

