# 视觉复核与 OCR 识别框架

> 团队内部共享版本。剥离了具体 API key、个人路径、具体样本数据，保留工具链选型和方法论。

---

## 一、识别工具链（分层）

### 第一层：PDF 文本抽取
| 工具 | 适用场景 | 成本 |
|------|---------|------|
| PyMuPDF (fitz) | 有文本层的 PDF | 免费，本地 |
| pymupdf4llm | PDF → Markdown 结构化 | 免费，本地 |

### 第二层：离线 OCR
| 工具 | 特点 | 优先级 |
|------|------|--------|
| PaddleOCR | 中文识别好，速度快 | 优先 |
| Tesseract | 简单备选，多语言 | 备选 |

### 第三层：文档解析
| 工具 | 用途 |
|------|------|
| MarkItDown | 附件和普通文档文本化 |
| Docling | 复杂格式文档解析 |

### 第四层：视觉模型复核（用于复杂版式/扫描件）
| 模型 | 用途 | 接入方式 |
|------|------|---------|
| Agnes Vision | 多模态视觉识别 | OpenAI 兼容 API |
| Gemini Vision | 备选视觉模型 | Google API |
| GPT Vision | 备选视觉模型 | OpenAI API |

### 调用方式（Agnes Vision 为例）
```
Base URL: https://apihub.agnes-ai.com/v1
端点: /chat/completions
模型: agnes-2.0-flash
认证: Bearer Token
兼容格式: OpenAI Chat Completions API（同时传 text + image_url）
```

参数建议：
- `temperature: 0.1`（越低越稳定）
- `max_tokens: 500`（够了）
- 图片建议 < 5MB
- 每张之间加 `time.sleep(0.5~1.0)` 避免限流
- 每 5-10 张保存一次进度

### PDF 转图片再识别
```python
import fitz
doc = fitz.open("发票.pdf")
page = doc[0]
mat = fitz.Matrix(2.0, 2.0)  # 2倍清晰度
pix = page.get_pixmap(matrix=mat)
img_data = pix.tobytes("png")
doc.close()
# img_data → 调 Vision API
```

---

## 二、高风险类别识别规则

以下类别必须重点复核收款方和客户主体：

- Filing Fee — 收款方通常是政府机构，不是邮件发件人
- Agent Fee — 注意是代理费还是注册费
- Shipping — AI 分类容易和 Software 混淆
- Professional Fees — 检查是否律所自开还是客户相关
- Consulting Fee — 确认咨询内容归属哪个客户
- Travel Expense - Lodge — 检查住宿日期和地点是否匹配出差
- Meals and Entertainment — 确认是否有合规的用餐人数和说明

### Filing Fee 特殊规则
- 收款方通常是政府机构（州务卿、税务部门）或官方注册系统
- 文档上出现 "Secretary of State"、"Commonwealth"、"Division of Corporations" → 优先作为收款方
- 系统简称（如 "osos"、"BC Registry Services"）要结合 PDF 画面确认正式机构名
- 客户主体通常藏在 filing/entity/company/account/transaction details 里
- 反查出的公司名不放入文件名

---

## 三、AI Agent 接手流程

1. 确认凭证目录和 Excel 是否存在
2. 读取 Excel 的复核清单和凭证文件夹
3. 检查文件名和表格是否一一对应
4. 筛出高风险类别，不要直接全量操作
5. **先跑 5-10 个视觉复核样本**，确认准确后再批量
6. 比对视觉结果与 Excel 原字段
7. 只修改有明确证据支持的字段
8. 修改文件名时同步更新 Excel
9. 检查无金额文件、重复文件、杂乱附件混入
10. 清理临时 JSON、OCR 坐标、渲染图片

---

## 四、常见 API 问题

| 错误 | 原因 | 解决 |
|------|------|------|
| 401 Unauthorized | API Key 缺失或不正确 | 确认环境变量已设置 |
| 404 | 用了错误的模型名 | 确认模型名（不要用 image-gen 模型做识别） |
| 429 Too Many Requests | 请求太快 | 增加延迟或降低并发 |
| Timeout | 图片太大或网络问题 | 图片 < 5MB，加超时重试 |

### API Key 安全规则
- ❌ 不要写进代码
- ❌ 不要写进 README
- ❌ 不要写进知识库笔记
- ❌ 不要写进 Excel
- ✅ 只通过环境变量传入

---

## 五、禁止事项

- ❌ 不要把无金额文件当作发票处理
- ❌ 不要用错误的模型导致 API 404 后继续批量跑
- ❌ 不要让金额出现重复标记如 `(1)`
- ❌ 不要在没有用户确认前大规模改名
- ❌ 不要把邮件发件人当作收款方
- ❌ 不要把客户主体和付款人混成同一个字段
