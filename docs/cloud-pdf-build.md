# 云环境中的中文 PDF 构建

## 当前环境怎么构建

在 Bash 中运行：

```bash
source /workspace/least-squares-state/activate.sh
cd /workspace/Least-Squares-Methods-in-Python
python tools/build.py --pdf --test
```

这会用已保存、已验证的 Notebook 结果生成 PDF，并运行测试。若改了正文、计算代码或输入数据，要先重新执行相关章节，或使用：

```bash
python tools/build.py --execute --pdf --test
```

`--execute` 会更新 Notebook 中的保存输出与执行指纹；`--pdf` 会更新 PDF 和 `docs/validation.json`。这些是实际文件修改，请在预期要同步结果时执行。

输出为 `pdf/Least-Squares-Methods-in-Python-zh.pdf`，中间文件在 `.build/book/`，编译输出在 `.build/book/compile-output.txt`。环境快照不保留 shell 的激活状态，新任务先重新 `source`。

## 这次为什么失败

环境已有 Pandoc、XeLaTeX、latexmk、常用 LaTeX 包和拉丁字体，但模板使用的 `ctexbook` 中文文档类不存在。首个实际错误是 `File 'ctexbook.cls' not found`。仅有 `xelatex` 命令并不意味着中文工具链齐全。

当前账号没有 sudo，不能按普通系统安装命令写入系统目录。因此采用工作区 TeX 树：

- 从 `https://deb.debian.org/debian` 获取 trixie 的签名软件包索引，使用系统 Debian 归档密钥验证。
- 下载 `texlive-lang-chinese` 和 `texlive-lang-cjk`，均固定为 `2024.20250309-1`；下载时由 APT 校验包，同时用官方索引提供的 SHA256 再核对本地文件。
- 用 `dpkg-deb -x` 解包，不执行系统安装和提权操作；将包中的 TeX 树放入 `/workspace/least-squares-state/texmf`。
- 通过 `TEXMFHOME` 让 TeX 找到中文类、xeCJK 与 Fandol 字体，把 `TEXMFVAR` 和 `TEXMFCONFIG` 放在可写工作区；运行 `mktexlsr` 建索引。

保留了 HTTPS、软件源签名和包哈希校验，没有使用 `trusted=yes`、不安全下载选项或修改预期校验和。只提取所需 TeX 数据，未把这两个包注册为系统已安装；所需 TeX 引擎与通用依赖使用云镜像已有版本。

## 检查中文支持是否生效

```bash
source /workspace/least-squares-state/activate.sh
kpsewhich ctexbook.cls
kpsewhich xeCJK.sty
kpsewhich FandolSong-Regular.otf
python -m unittest discover -s tests -p test_build.py -v
```

前三条应返回工作区内的真实文件。构建测试中的 `test_pdf_template_handles_real_inline_code_and_math` 应实际通过，不应以中文组件缺失为由跳过。该测试会真实调用 Pandoc/XeLaTeX，并检查嵌入图片的宽高比。

本地重装脚本保存在 `/workspace/least-squares-state/install-tex.sh`，完整依赖安装与环境激活步骤也已保存到云环境配置草稿，供环境设置中审阅与发布。脚本使用当前云平台代理，不是其他机器通用的代理配置。普通 Debian/Ubuntu 管理员可直接使用 README 中的系统包安装命令。

## 校验的官方包

| 包 | SHA256 |
|---|---|
| `texlive-lang-chinese_2024.20250309-1_all.deb` | `583cd26483b79d32191a8d0a198e80546415d6eca4f23a4bedd253ebdb661291` |
| `texlive-lang-cjk_2024.20250309-1_all.deb` | `56c795c17b392766c66132f469aab024c374eb92848685ab1d66072a14115b66` |

这些值来自已验证的 Debian 索引。未来若源中不再提供固定版本，应重新核对官方发布版本及其完整性，再有意识地更新安装配置；不要为了让下载通过而随意换校验和。
