# PDF/图片/发票识别技能调研报告

> 2026-06-10 调研 | 目标：对比 GitHub 上热门工具，找到我们现有技能的提升空间

---

## 一、PDF 拆分/提取

### 热门工具排名

| 工具 | ⭐ | 核心能力 | 语言 |
|------|-----|---------|------|
| **opendataloader-pdf** | 24.3k | PDF → AI-ready 数据，表格、OCR、标注框 | Java |
| **kreuzberg** | 8.5k | 多语言文档提取（PDF/Office/图片），含图片提取、元数据、结构化信息，有 CLI/REST API/MCP Server | Rust 核心 |
| **Zipstack/unstract** | 6.6k | LLM 驱动的无结构数据提取，支持 OCR 和结构化输出，适合 ETL 流程 | Python |
| **firecrawl/pdf-inspector** | 1.4k | 快速 PDF 分类（扫描件 vs 文本），智能路由 | Rust |
| **torakiki/pdfsam** | 4.4k | 桌面级 PDF 拆分/合并/旋转 | Java |
| **markitdown**（已有） | 149k | 万能转换器（PDF/Word/PPT/Excel→MD） | Python |

### 我们的现状
- ✅ **markitdown** — 万能格式转换已覆盖
- ❌ **PDF 智能路由** — 不知道 PDF 是扫描件还是文本，统一当文本处理
- ❌ **图片提取** — 没有单独的 PDF 图片提取能力
- ❌ **表格提取** — markitdown 转出来的表格格式不够结构化

---

## 二、图片识别/OCR

### 热门工具排名

| 工具 | ⭐ | 核心能力 | 备注 |
|------|-----|---------|------|
| **marker-pdf** | — | PDF/扫描件转 Markdown，内置 OCR | 已安装在我们技能里 |
| **pymupdf** | — | PDF 基础处理（文本/图片提取） | 已安装 |
| **enoch3712/ExtractThinker** | 1.5k | LLM + PDF/OCR 结构化提取 | 偏研究 |
| **bhimrazy/receipt-ocr** | 343 | 收据图片 OCR（Tesseract + LLM） | 轻量 |

### 我们的现状
- ✅ **vision_analyze 工具** — 图片识别由辅助模型完成（agnes-2.0-flash-vision）
- ✅ **pymupdf/pymupdf4llm** — PDF 基础处理
- ✅ **marker-pdf** — 扫描件转 Markdown（已安装）
- ⚠️ **OCR 依赖** — 目前 OCR 主要靠 vision_analyze（辅助模型），成本高且速度慢

---

## 三、发票识别

### 热门工具排名

| 工具 | ⭐ | 核心能力 | 备注 |
|------|-----|---------|------|
| **WellApp-ai/Well** | 331 | 金融数据提取（发票/收据），FinOps 集成 | 商业导向 |
| **InvoiceScan** | 3 | NestJS + Gemini + Tesseract 全栈方案 | 参考架构 |
| **chiupam/invoiceOCR** | 49 | 腾讯云 OCR 中文发票识别 | 国内友好 |

### 我们的现状
- ✅ **invoice-pdf-automation 技能** — 自建端到端流水线（PDF→提取→分类→命名→Excel）
- ✅ **命名规则** — `YYYYMMDDHHMMSS-分类-收款方-付款方-金额.pdf`
- ⚠️ **识别精度** — 完全依赖 vision_analyze + pymupdf，速度慢
- ⚠️ **结构化输出** — 没有统一的 schema，每次需要手动整理

---

## 四、提升建议（按优先级）

### 🔥 优先 1：引入 Kreuzberg（跨文档提取框架）

**为什么：** 8.5k⭐，Rust 核心速度快，支持 PDF/Office/图片 97+ 格式，有 CLI 和 MCP Server。最关键的是它**专门做图片提取和结构化信息提取**，正好补我们的短板。

**能解决什么：**
- PDF 里的图片提取（我们目前没有）
- 文档结构化信息提取（标题、段落、表格）
- 支持 MCP Server（可以直接集成到 Hermes 工具链）

**代价：** Rust 编译 + Python bindings，需要安装

### 🔥 优先 2：引入 pdf-inspector（PDF 智能分类）

**为什么：** 1.4k⭐，专门做 PDF 分类——自动判断是**扫描件**还是**文本型** PDF，然后智能路由。

**能解决什么：**
- 避免对扫描 PDF 做无用文本提取
- 节省时间和 API 调用
- 对发票 PDF 特别有用（有些是扫描件需要 OCR，有些是文本型直接提取）

**代价：** 很小，Rust + Python bindings

### 🔥 优先 3：自建发票识别 schema + 结构化输出

**为什么：** 现有 invoice-pdf-automation 技能没有统一 schema，每次结果格式可能不同。

**建议方案：**
```json
{
  "type": "invoice",
  "fields": {
    "date": "YYYY-MM-DD",
    "seller": "公司全称",
    "buyer": "公司全称",
    "amount": "数字",
    "tax": "数字",
    "invoice_number": "号码",
    "category": "分类标签"
  }
}
```
- 用 LLM 做结构化输出（vision_analyze 的结果转 JSON）
- 统一字段名和格式
- 后续 Excel 生成直接消费这个 schema

### 🔥 优先 4：建立 OCR 流水线（低成本方案）

**为什么：** 目前 OCR 依赖 vision_analyze（辅助模型），贵且慢。

**低成本替代：**
1. 先用 `pdf-inspector` 判断是不是扫描件
2. 如果是扫描件 → 用 `marker-pdf` 做批量 OCR
3. 如果是文本型 PDF → 直接用 pymupdf 提取文本
4. 只对**识别不清**的页面调用 vision_analyze

这样可以大幅降低 OCR 成本。

---

## 五、总结

| 领域 | 我们当前 | 推荐提升 | 预期效果 |
|------|---------|---------|---------|
| PDF 处理 | markitdown 万能转换 | + Kreuzberg 结构化提取 | 表格/图片提取能力提升 |
| OCR | vision_analyze（辅助模型） | + pdf-inspector 智能路由 + marker-pdf 批量 | 成本降低 70%+ |
| 发票 | invoice-pdf-automation | 统一 schema + 结构化输出 | 准确率提升，Excel 生成自动化 |
| 整体 | 手动调度 | Kreuzberg MCP Server | 集成到 Hermes 工具链，自动发现 |

**下一步：** 先装 Kreuzberg 和 pdf-inspector 试试效果，看能不能直接集成到 Hermes 工具链。
