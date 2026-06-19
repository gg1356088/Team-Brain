# PDF/图片/发票识别技能调研结果

> 2026-06-10 调研 | 目标：对比 GitHub 上热门工具，找到我们现有技能的提升空间

---

## 调研结果

### PDF 提取/拆分

| 工具 | ⭐ | 核心能力 | 语言 |
|------|-----|---------|------|
| **opendataloader-pdf** | 24.3k | PDF → AI-ready 数据，表格、OCR、标注框 | Java |
| **kreuzberg** | 8.5k | 多语言文档提取（PDF/Office/图片），有 CLI/REST API/MCP Server | Rust 核心 |
| **Zipstack/unstract** | 6.6k | LLM 驱动的无结构数据提取，支持 OCR | Python |
| **firecrawl/pdf-inspector** | 1.4k | 快速 PDF 分类（扫描件 vs 文本），智能路由 | Rust |
| **markitdown**（已有） | 149k | 万能转换器（PDF/Word/PPT/Excel→MD） | Python |

### 我们缺失的能力
- ❌ PDF 图片提取（没有单独的图片提取能力）
- ❌ PDF 智能分类（不知道 PDF 是扫描件还是文本型）
- ❌ 表格结构化提取（markitdown 转出来的表格不够结构化）

### OCR/图片识别

| 工具 | ⭐ | 核心能力 |
|------|-----|---------|
| **marker-pdf**（已有） | — | PDF/扫描件转 Markdown，内置 OCR |
| **pymupdf**（已有） | — | PDF 基础处理 |
| **enoch3712/ExtractThinker** | 1.5k | LLM + PDF/OCR 结构化提取 |
| **bhimrazy/receipt-ocr** | 343 | 收据图片 OCR（Tesseract + LLM） |

### 发票识别

| 工具 | ⭐ | 核心能力 |
|------|-----|---------|
| **WellApp-ai/Well** | 331 | 金融数据提取（发票/收据），FinOps 集成 |
| **chiupam/invoiceOCR** | 49 | 腾讯云 OCR 中文发票识别 |

### 我们缺失的能力
- ⚠️ OCR 成本太高（依赖 vision_analyze 辅助模型）
- ⚠️ 没有统一的发票结构化 schema
- ⚠️ 没有智能路由（先判断 PDF 类型再选方案）

---

## 提升建议

### 优先 1：引入 Kreuzberg（8.5k⭐）

**补什么短板：** PDF/Office/图片 97+ 格式提取，自带 MCP Server 可直接集成 Hermes 工具链。

### 优先 2：引入 pdf-inspector（1.4k⭐）

**补什么短板：** 自动判断 PDF 是扫描件还是文本型，然后智能路由。节省 OCR 时间和成本。

### 优先 3：统一发票 schema

定义统一 JSON schema，vision_analyze 输出结构化结果，后续 Excel 直接消费。

### 优先 4：建立 OCR 流水线

pdf-inspector 判断类型 → 文本型用 pymupdf，扫描件用 marker-pdf 批量 OCR → 只有识别不清的才调 vision_analyze。
