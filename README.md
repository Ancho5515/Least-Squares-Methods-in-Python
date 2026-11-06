# Least-Squares-Methods-in-Python

**最小二乘方法：Python交互学习**，从“几次读数不一样，该信多少”开始。

给同一个物体称几次，读数会变；给一辆小车拍几次照，位置也不会恰好排成直线。我们怎样从这些不完美的读数里，找到一个有用的重量、速度或响应规律？本书用可以运行的 Python 实验逐步回答。

“最小二乘”先做两件事：用一个模型算预测，把预测与读数的差各自平方再相加；然后找出让这个总分最低的设置。它能帮你拟合数据，还需要你检查单位、模型和测量条件。

数学基础较少也可以开始：先读生活问题、运行实验、解释图，再按需读推导。独立改代码仍需要一点 Python 和数组基础，入口指南会指出要补哪些知识。

- [零起点阅读指南：先跑哪一格、卡住怎么办](docs/reading-guide.md)
- [白话词典：残差、雅可比、置信区间是什么意思](docs/plain-language-glossary.md)
- [章节目录与 Notebook](docs/outline.md)
- [与 Labbe 教材的对比分析及本轮改写范围](docs/teaching-comparison.md)
- [阅读最新中文 PDF（包含本轮表达改写）](pdf/Least-Squares-Methods-in-Python-zh.pdf)
- [原书、中文版 PDF 和完整 LaTeX 工程](references/nonlinear-least-squares/)
- [本轮改写验证记录](docs/editorial-validation.json)
- [初版执行与构建记录](docs/validation.json)
- [初版审阅说明](docs/REVIEW.md)

正文按“问题—直觉—实验—解释—按需推导”组织，为现有图补充读图提示，保留必要数学条件。参考 Roger Labbe 的[可执行教材组织方式](https://github.com/rlabbe/Kalman-and-Bayesian-Filters-in-Python)，非线性理论主要参考 Madsen、Nielsen、Tingleff（2004）。具体来源和原书疑点见附录D。

## 不知道从哪里开始

先读 [00](notebooks/00-guide.ipynb)、[01](notebooks/01-mean-and-line.ipynb)、[02](notebooks/02-models-and-residuals.ipynb)。先做到能说明“调什么、怎么评分、图里画了什么”，再读加权和过拟合。矩阵、非线性算法及工程案例的后续路线见[阅读指南](docs/reading-guide.md)。

遇到公式可以先读紧邻的白话解释，再看每个符号表示什么。推导帮助你知道方法在什么条件下成立；可以第二遍再读，但自行改算法或解释不确定性时需要回头核对。

## 安装与阅读

要求 **Python 3.11+，推荐已验证的 Python 3.12**。所有章节离线执行；安装依赖时需要网络。

    python -m venv .venv

Windows PowerShell 激活：.venv\Scripts\Activate.ps1。macOS/Linux 激活：source .venv/bin/activate。

    python -m pip install -r requirements.txt
    python -m pip install jupyterlab
    python -m jupyterlab

打开 notebooks/ 中的章节，每章从头执行即可。选中代码格后按 Shift+Enter。Notebook已有真实运行结果，GitHub也能静态预览；所有图形都可通过相邻代码重新生成。图内使用英文标签，正文解释关键标签与读法。修改前建议另存自己的实验副本。

## 本地测试与 PDF 构建

    python -m unittest discover -s tests -v
    python tools/build.py --execute --pdf --test

第二条命令逐章启动独立IPython进程执行代码、保存真实输出，再由同一份Notebook生成整本PDF。运行时不依赖本地通信端口，不需要在线服务。普通Jupyter交互阅读仍使用你本机的标准内核。

编译PDF还需安装 Pandoc 和带中文组件的 TeX Live（包含 XeLaTeX、latexmk、ctex、Fandol、listings、fancyhdr等）。Windows建议安装完整TeX Live和Pandoc；Debian/Ubuntu可使用：

    sudo apt-get install pandoc latexmk texlive-xetex texlive-lang-chinese texlive-latex-extra texlive-fonts-recommended

只执行并验证Notebook：

    python tools/build.py --execute --test

只用已保存结果重新生成PDF：

    python tools/build.py --pdf

输出为 pdf/Least-Squares-Methods-in-Python-zh.pdf。构建脚本核验正文、保存输出和共享求解器/CSV输入的指纹；拒绝错误、未执行、输出被清空或依赖变化后结果过期的Notebook。中间文件和编译日志位于 .build/book/，不纳入Git。

2026-11-06 已同步重建中文 PDF，包含本轮通俗表达改写。云环境已在工作区补齐 `ctex`、xeCJK 和 Fandol 字体；后续构建先运行 `source /workspace/least-squares-state/activate.sh`，再执行上述命令。无 sudo 的安装方式和检查步骤见 [云环境 PDF 构建说明](docs/cloud-pdf-build.md)。

## 数据和数值约定

- 统一残差为“模型减观测”，目标为半平方和。
- data/ 中的文件及工程案例均为明确标注的合成数据；不代表真实屏幕、仪器或客户测量。
- lsq/ 是小型密集问题的教学实现，返回停止原因和历史；实际工程优先考虑成熟求解器及相应验证。
- 每个Notebook独立初始化并固定随机种子。最后几位浮点数可能因平台和BLAS不同而变化。
- 核心Notebook为正文唯一来源；PDF、已执行Notebook、数据、参考工程和验证记录均保存在普通Git中。
- 不使用Git LFS、GitHub Actions或Artifact。每阶段和bug修复单独提交。

## 初版范围

已包含16篇主线Notebook（00—15）及4篇附录；附录C提供变量投影和割线更新实验，完整混合/割线求解器与大规模稀疏实现是后续扩展。中文参考译本保持原工程及原始文件，其版本差异和历史勘误不等于在本次重新全部校对过。

原创教材正文采用CC BY 4.0，原创代码采用MIT；第三方参考资料和字体按各自权利与许可保留，详见 [LICENSE.md](LICENSE.md)。
