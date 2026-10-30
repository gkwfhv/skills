你在 /home/gavin/X2Robot/semantic 工作。任务：把一篇英文论文完整翻译成中文 Markdown，供中文读者阅读。不要写摘要式概括，要按原文顺序翻译正文、附录、图注、表格和公式；参考文献不逐条翻译，只留一句说明和 arXiv 链接。

输入文件：
"<PDF_PATH>"（<PAGE_COUNT> 页）

输出：
- translations/<ShortName>-中文翻译.md
- 图片放 translations/assets/<slug>/fig1.png 等

先跑依赖检查：
`python3 ~/.qoder/skills/paper-translator/scripts/check_deps.py`
缺 PyMuPDF 就 `pip install pymupdf`；缺 poppler 先别装系统包，改用
`scripts/extract_text.py` 抽文本，或者告诉用户需要 `sudo apt install poppler-utils`。

风格是硬要求，先读这两个文件找语感（只学写法，不要抄内容）：
- translations/DynaMem-中文翻译.md
- translations/LT-Mem-中文翻译.md

风格规则：
- 按中文母语习惯写，不逐句对译。多用短句、主动语态，一句话只讲一件事。
- 禁用这些英文骨架："使得"、"让……成为可能"、"本文提出一种……的方法，它……"、"值得注意的是"、"具体来说"、"另一方面"、"通过……来"、"由……组成"。
- 术语首次出现给"中文（English）"，之后只用中文；session、token、benchmark 这类约定俗成的词可以保留。
- 长句先拆开，再按中文逻辑重组：先背景/条件，后结论/动作。不要连续堆定语。

图和公式的处理流程：
1. 用 `pdftotext -layout` 提取全文；如果没有，就用
   `python3 ~/.qoder/skills/paper-translator/scripts/extract_text.py "<PDF_PATH>" --out /tmp/paper.txt`。
   按页读完，先列出章节、图、表、公式。
2. 运行：
   `python3 ~/.qoder/skills/paper-translator/scripts/extract_figures.py "<PDF_PATH>" "translations/assets/<slug>"`
   脚本会用 PyMuPDF 找图注、裁图，并生成 manifest.json。
3. 每张裁完必须用 Read 工具查看，确认图完整、没有把图注或正文裁进去、没有截断。不行就用 `--override N:x0,y0,x1,y1` 重裁（PDF 坐标点）。
4. 表格用 Markdown 表格重排；公式用 LaTeX，`$$` 必须成对；图注要翻译。

写作与校验：
- 文档顺序：标题、作者、摘要、正文各节、附录、图表公式，和原文一致。
- 正文和附录都要翻，不要跳过实现细节；长文可以分批写同一个文件，但最终必须完整。
- 完成后运行：
  `python3 ~/.qoder/skills/paper-translator/scripts/check_translation.py "translations/<ShortName>-中文翻译.md"`
  修掉所有报错。再通读一遍，把不像中文的句子重写。
- 不要改动其他论文的文件。

完成后用不超过 150 字汇报：文件路径、覆盖页数、图片数、有没有未翻译部分。不要粘贴译文。
