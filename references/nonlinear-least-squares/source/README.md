# 非线性最小二乘问题的求解方法：中文 LaTeX 工程

原著：K. Madsen、H. B. Nielsen、O. Tingleff，第二版，2004 年 4 月。

## 编译

推荐使用包含中文组件的 TeX Live 2023 或更新版本（Windows 可用完整 TeX Live），安装 `ctex`、`xeCJK`、`fandol`、`amsmath`、`mathtools`、`tcolorbox`、`hyperref`、`bookmark`、`zref`、`latexmk`。不需要系统安装 Noto 或 FreeSerif。

进入本文件所在目录运行：

```sh
latexmk -xelatex -interaction=nonstopmode -halt-on-error main.tex
```

输出为 `main.pdf`。如果不使用 latexmk，连续运行 XeLaTeX 至交叉引用与目录稳定，通常需要 3 遍：

```sh
xelatex -interaction=nonstopmode -halt-on-error main.tex
xelatex -interaction=nonstopmode -halt-on-error main.tex
xelatex -interaction=nonstopmode -halt-on-error main.tex
```

所有源码为 UTF-8。数学采用 Computer Modern；拉丁正文字体 Nimbus Roman/Sans 已随工程提供 OTF 文件及许可，中文采用 TeX Live 自带 Fandol 字体。请勿改用 pdfLaTeX。

## 文件

- `main.tex`：文档样式、目录、书签、环境和章节装配。
- `chapters/`：按章节拆分的完整译文、可编辑公式及算法；第 3 章为便于维护拆为四个文件。
- `assets/figures/`：10 个矢量图形面板，仅供图形使用；公式和算法不依赖 PDF 裁片。
- `fonts/`：随附拉丁 OTF 字体与许可。
- `reference/original.pdf`：用户提供的英文原版，保留作核对依据。
- `audit/`：按原著印刷页码记录的逐页内容检查。
- `tools/verify_project.py`：检查页源覆盖、编号、对象完整性与引用的辅助脚本。

`\sourcepage{n}` 只建立不可见的原著页源标签，不显示“原书第 n 页”，也不强制译本分页。正文及索引通过 `\pageref{src:n}` 指向重排后的译本页码。带编号公式采用显式 `\tag`；增加内容时请保留原著编号，并同步维护检查记录。

辅助检查在编译后执行：

```sh
python3 tools/verify_project.py
```

脚本通过不等于翻译和视觉校验通过；实际检查范围与限制以全文检查报告为准。
