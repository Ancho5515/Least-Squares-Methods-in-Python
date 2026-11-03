# 用户提供的最小二乘参考资料

原著：K. Madsen、H. B. Nielsen、O. Tingleff，Methods for Non-Linear Least Squares Problems，第二版，2004年4月。

- `source/`：用户提供的完整中文版 LaTeX 工程，逐文件解压保留全部44项内容，包括字体及其许可、图形、audit 和工程自带的 `main.pdf`。
- `source/reference/original.pdf`：英文原件（30张双页），与用户单独提供的英文文件逐字节相同。
- `translated-supplied.pdf`：用户另外提供的当前中文版（45页），未经改写。
- `SHA256SUMS.json`：上述全部文件的实际SHA256。

两份中文PDF均为45页，字节和SHA256不同。旧检查报告只对应工程自带的 `source/main.pdf`，不能作为单独提供的PDF的完整复核证据。本次保留两个版本，未把版本差异当作已解决的校对问题。

在 `source/` 中运行：

```sh
latexmk -xelatex -interaction=nonstopmode -halt-on-error main.tex
python tools/verify_project.py
```

编译方式、历史检查记录和原书疑点见原工程README、Full_Check_Report.md及audit/。本文档只说明归档和校验范围；本次教材制作不重新逐段校对整个译本。

原著入口：https://orbit.dtu.dk/en/publications/methods-for-non-linear-least-squares-problems-2nd-ed/

本目录是用户提供的第三方参考资料，原作者权利及随附字体许可保留，不适用本仓库原创教材/代码的许可。译本是学习参考，不代表原作者审定。
