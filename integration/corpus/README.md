# 文献语料工具链

把本机书库（D:\书、D:\兵棋）里的 PDF 变成可检索的文本，再和游戏词库交叉比对。
不联网、不依赖外部服务；扫描件用本机 Tesseract OCR。

## 步骤

1. **探测**：判断每份 PDF 是文字版还是扫描件
   ```
   python integration/corpus/probe_pdfs.py
   ```
   输出 `pdf_probe2.jsonl`（页数、每页字符数、语言、关键词）。

2. **抽取文字版**：把有文字层的 PDF 抽成逐页文本（保留页码，便于引用）
   ```
   python integration/corpus/extract_text.py sel.jsonl D:\Tool\WITE2\corpus
   ```
   `sel.jsonl` 每行 `{"path": "..."}`；输出 `corpus/<书名>/pages.jsonl` + `full.txt`。

3. **OCR 扫描件**：逐页渲染 300dpi 后交给 Tesseract（chi_sim+eng）
   ```
   python integration/corpus/ocr_pdf.py "D:\书\军事\泥足巨人.pdf" "D:\Tool\WITE2\corpus\泥足巨人" 300 "chi_sim+eng"
   ```
   页面已有文字层时直接取文字，不重复 OCR。

4. **统计**：中文语料里番号怎么写
   ```
   python integration/corpus/count_usage.py
   ```

5. **出对照表**
   ```
   python integration/build_reference_table.py
   ```
   生成 `docs/权威对照表.md`。

## 约定

- OCR 结果只用来**核对与举证**，不直接灌进游戏词典；进词典必须经过
  `glossary/reference_overrides.json`（每条带出处）。
- 语料存放在仓库外（`D:\Tool\WITE2\corpus`），不随包分发。
- 文字版优先，扫描件才 OCR；已 OCR 过的 PDF（页内自带文字层）不会二次 OCR。
