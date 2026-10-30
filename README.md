# Skills

个人可复用的 Qoder 技能集合。每个技能一个目录，核心文件是 `SKILL.md`，按需附带脚本和参考文档。

## 技能列表

### paper-translator

把英文论文 PDF 翻译成自然、好读的中文 Markdown，保留图、表、公式和图注。

适合这些场景：

- 单篇论文翻译
- 批量论文翻译
- 按统一风格重译已有译文
- 检查译文的翻译腔、图片缺失、公式配对

主要能力：

- **母语风格**：短句、主动语态、中文语序；禁用“使得”“值得注意的是”“本文提出”“通过……来”等英文骨架
- **结构保留**：按原文顺序翻译标题、摘要、正文、附录；图注翻译，表格重排，公式用 LaTeX
- **按图注裁图**：用 PyMuPDF 找 `Fig. N:` / `Figure N:`，自动裁出 300 DPI 图片
- **文字标签补偿**：`--include-text` 把百分比、坐标轴、图例等文字对象纳入裁切
- **依赖检查**：缺 PyMuPDF / poppler 时给出安装提示，并提供纯文本回退
- **译文校验**：检查禁用句式、图片路径、`$$` 配对
- **贴边审计**：扫描所有图片，标出内容贴边的图，避免裁掉标签

#### 安装

```bash
mkdir -p ~/.qoder/skills
cp -r paper-translator ~/.qoder/skills/
```

也可以从 Release 或打包文件安装：

```bash
tar -xzf paper-translator-skill.tar.gz -C ~/.qoder/skills/
# 或
unzip paper-translator-skill.zip -d ~/.qoder/skills/
```

安装后重启 Qoder，直接说“把这篇论文翻译成中文”，或调用 `/paper-translator`。

#### 依赖

```bash
python3 paper-translator/scripts/check_deps.py
```

- 必需：Python 3.9+、PyMuPDF
- 推荐：poppler-utils（`pdftotext` / `pdfinfo`）
- 可选：Pillow（手动裁图）

```bash
pip install pymupdf
sudo apt install poppler-utils   # 可选
```

没有 poppler 也能跑，脚本会回退到 `extract_text.py`。

#### 使用

```bash
# 1. 看结构：页数、章节、图注、公式
python3 paper-translator/scripts/inspect_pdf.py "paper.pdf"

# 2. 抽文本；没有 pdftotext 时用回退
pdftotext -layout "paper.pdf" /tmp/paper.txt
python3 paper-translator/scripts/extract_text.py "paper.pdf" --out /tmp/paper.txt

# 3. 裁图，建议带上 --include-text
python3 paper-translator/scripts/extract_figures.py \
  "paper.pdf" "translations/assets/example" --include-text

# 4. 只重裁某几张
python3 paper-translator/scripts/extract_figures.py \
  "paper.pdf" "translations/assets/example" --include-text --only 3,6

# 5. 手动指定边界（PDF 坐标点）
python3 paper-translator/scripts/extract_figures.py \
  "paper.pdf" "translations/assets/example" --override 6:304,310,566,441

# 6. 校验译文
python3 paper-translator/scripts/check_translation.py "translations/example-中文翻译.md"

# 7. 扫描图片贴边
python3 paper-translator/scripts/audit_figures.py translations
```

#### 输出约定

```text
translations/
├── <Paper>-中文翻译.md
└── assets/
    └── <slug>/
        ├── fig1.png
        ├── fig2.png
        └── manifest.json
```

#### 目录结构

```text
paper-translator/
├── SKILL.md
├── requirements.txt
├── reference/
│   ├── style-guide.md          # 风格规范与替换表
│   └── subagent-prompt.md      # 批量翻译的子任务提示词
└── scripts/
    ├── check_deps.py           # 依赖检查
    ├── inspect_pdf.py          # 章节、图注、公式
    ├── extract_text.py         # PyMuPDF 文本回退
    ├── extract_figures.py      # 按图注裁图
    ├── check_translation.py    # 译文校验
    └── audit_figures.py        # 图片贴边审计
```

#### 翻译风格速查

| 不要写 | 改成 |
|---|---|
| 使得…… | 让…… / 结果…… / 于是…… / 直接删掉 |
| 让……成为可能 | 已经能做到 / 有了现实基础 |
| 本文提出一种……的方法，它…… | 我们做了…… / 我们提出…… |
| 值得注意的是 | 直接说结论 |
| 具体来说 | 做法是 / 拆开看 |
| 通过……来…… | 靠…… / 用…… |
| 由……组成 | 包含…… / 分三块 |

完整规则见 [`paper-translator/reference/style-guide.md`](paper-translator/reference/style-guide.md)。

## 新增技能

1. 在仓库根目录新建一个 kebab-case 目录，例如 `my-skill/`。
2. 写 `SKILL.md`，开头加 frontmatter：

```yaml
---
name: my-skill
description: 一句话说明这个技能做什么、什么时候用。
---
```

3. 需要脚本就放 `scripts/`，需要参考文档就放 `reference/`。
4. 本地测试通过后提交并推送。

## 说明

- 技能按目录独立，互不依赖。
- 脚本尽量只依赖 Python 标准库 + 一个明确声明的主力库。
- 涉及联网、写文件、安装系统包的操作，要在 `SKILL.md` 里写清楚边界和确认要求。
