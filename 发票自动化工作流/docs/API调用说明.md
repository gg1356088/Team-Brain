# 发票自动化工作流 — Agnes AI API 调用说明

> 版本：v1.0 | 日期：2026-06-15
> 适用对象：需要操作发票识别的 AI Agent 或开发者
> 不依赖 Hermes，只需要一个 Agnes AI API Key

---

## 一、你需要准备什么

1. **一个 Agnes AI API Key**
   - 从 Agnes AI 平台获取（去 agnes-ai.com 注册申请）
   - Key 格式类似：`sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

2. **Python 3.9+**（自带 `requests` 库或 `urllib`）

3. **发票文件**（PDF / JPG / PNG 等）

---

## 二、API 基本信息

| 项目 | 值 |
|------|-----|
| Base URL | `https://apihub.agnes-ai.com/v1` |
| 模型 | `agnes-2.0-flash` |
| 认证方式 | Bearer Token（API Key） |
| 兼容格式 | OpenAI Chat Completions API |

---

## 三、图片识别（Vision）调用方法

### 核心思路

Agnes AI 的 vision 能力走的是 **OpenAI 兼容的多模态接口**，也就是说：
- 用 `/chat/completions` 端点
- 消息里同时传文字和图片
- 模型会返回识别结果

### 方式 A：Base64 编码图片（最通用）

```python
import requests
import base64

API_KEY = "你的API_KEY"
API_URL = "https://apihub.agnes-ai.com/v1/chat/completions"

# 读取图片并转为 base64
with open("发票.jpg", "rb") as f:
    img_b64 = base64.b64encode(f.read()).decode()

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

payload = {
    "model": "agnes-2.0-flash",
    "messages": [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "请识别这张发票图片中的以下信息，用JSON格式返回：收款方、付款方、金额、日期、费用类型。"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{img_b64}"
                    }
                }
            ]
        }
    ],
    "max_tokens": 500,
    "temperature": 0.1
}

response = requests.post(API_URL, headers=headers, json=payload)
result = response.json()

# 提取识别结果
content = result["choices"][0]["message"]["content"]
print(content)
```

### 方式 B：图片 URL（如果图片在网上）

```python
payload = {
    "model": "agnes-2.0-flash",
    "messages": [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "请识别这张发票图片中的收款方、付款方、金额、日期、费用类型。"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://example.com/invoice.jpg"
                    }
                }
            ]
        }
    ],
    "max_tokens": 500,
    "temperature": 0.1
}
```

### 方式 C：用 curl 命令行

```bash
curl -X POST "https://apihub.agnes-ai.com/v1/chat/completions" \
  -H "Authorization: Bearer 你的API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "agnes-2.0-flash",
    "messages": [
      {
        "role": "user",
        "content": [
          {
            "type": "text",
            "text": "请识别这张发票中的收款方、付款方、金额、日期、费用类型，用JSON返回。"
          },
          {
            "type": "image_url",
            "image_url": {
              "url": "data:image/jpeg;base64,这里放base64编码的图片"
            }
          }
        ]
      }
    ],
    "max_tokens": 500,
    "temperature": 0.1
  }'
```

---

## 四、纯文本调用（不需要图片时）

有些 PDF 已经有完整文件名，可以直接从文件名提取信息，不需要调用 vision。

但如果需要让模型做其他文字处理（比如分类、格式化），也可以用同样的接口：

```python
payload = {
    "model": "agnes-2.0-flash",
    "messages": [
        {"role": "user", "content": "把 '崇德盈加油站' 归类到合适的费用类型"}
    ],
    "max_tokens": 100,
    "temperature": 0.5
}
```

---

## 五、发票工作流完整步骤

### 步骤 1：扫描待处理文件夹

找到所有需要处理的文件（PDF、JPG、PNG 等）。

### 步骤 2：判断是否需要 Vision 识别

| 情况 | 处理方式 |
|------|---------|
| 文件名格式完整（如 `20240804-Gas-崇德盈加油站-General-NTD584.jpg`） | 用正则解析文件名，秒级提取，**不调用 API** |
| 文件名缺字段 / 只有 PDF 没有图片 | 用 PyMuPDF 提取 PDF 文本 |
| PDF 是扫描件 / 图片格式文件 | **调用 Agnes AI Vision API** 识别 |

### 步骤 3：Vision 识别批量处理

```python
import os
import glob

# 遍历所有待处理图片
image_files = glob.glob("00-待处理/**/*.jpg", recursive=True)
image_files += glob.glob("00-待处理/**/*.png", recursive=True)

results = []
for img_path in image_files:
    # 读取图片转 base64
    with open(img_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode()
    
    # 调用 API
    payload = {
        "model": "agnes-2.0-flash",
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": "请识别这张发票图片中的收款方、付款方、金额、日期、费用类型，用JSON返回。"},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
            ]
        }],
        "max_tokens": 500,
        "temperature": 0.1
    }
    
    response = requests.post(API_URL, headers=headers, json=payload)
    result = response.json()["choices"][0]["message"]["content"]
    results.append({"file": img_path, "识别结果": result})
    
    # 建议加个延迟，避免请求过快
    time.sleep(0.5)
```

### 步骤 4：分类判断

识别出费用类型后，按规则判断去向：

| 费用类型特征 | 归入 |
|-------------|------|
| 律所相关（WUKONG、律师费等） | `00-已确认/00-律所发票/` |
| 个人消费（currency exchange、cash withdraw） | `00-已确认/00-个人发票/` |
| USPS、Postage | `00-已确认/00-USPS跳过/` |
| 其他（Filing Fee、Gas、Meal 等） | `00-待复核/` |

### 步骤 5：待复核分组

普通发票每 20 个一组，放入 `第01组`、`第02组`... 文件夹。

### 步骤 6：Excel 登记

所有文件的信息登记到总索引表（CSV 或 Excel），包含：
- 序号、状态、文件名、日期、费用类型、收款方、付款方、金额、备注

---

## 六、费用类型分类参考

| 关键词 | 费用类型 |
|--------|---------|
| filing, fee, ca statement | Filing Fee |
| gas, fuel, 加油站 | Gas |
| car rental, hotel, flight | Travel Expense |
| meal, restaurant, lunch, dinner | Meal and Entertainment |
| taxi, uber, lyft | Taxi Fee |
| printing, office supplies | Office Supplies |
| software, computer, subscription | Computer-Software |
| postage, usps, shipping | Shipping-Fee |
| currency exchange, cash withdraw | Personal（个人发票） |

---

## 七、注意事项

1. **温度设置**：发票识别建议 `temperature=0.1`，越低越稳定
2. **max_tokens**：设 500 足够，识别结果一般不超过 300 字
3. **并发控制**：批量处理时建议加 `time.sleep(0.5)` 避免请求过快
4. **错误处理**：API 可能超时或返回 429（限流），需要重试机制
5. **base64 大小限制**：单张图片不宜超过 20MB，建议先压缩
6. **PDF 处理**：PDF 不能直接传给 vision，需要先转图片或用 PyMuPDF 提取文本

---

## 八、完整示例脚本

下面是一个可以直接跑的完整脚本框架：

```python
#!/usr/bin/env python3
"""
发票识别工具 — 独立运行，不依赖 Hermes
只需要 Agnes AI API Key
"""

import os
import json
import time
import glob
import requests
from pathlib import Path

# ===== 配置 =====
API_KEY = os.environ.get("AGNES_API_KEY", "你的API_KEY")
API_URL = "https://apihub.agnes-ai.com/v1/chat/completions"
PROJECT_DIR = Path("./发票凭证文件")

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# ===== 核心函数 =====
def recognize_invoice(image_path):
    """识别一张发票图片"""
    with open(image_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode()
    
    payload = {
        "model": "agnes-2.0-flash",
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": "请识别这张发票图片中的收款方、付款方、金额、日期、费用类型，用JSON格式返回。"},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
            ]
        }],
        "max_tokens": 500,
        "temperature": 0.1
    }
    
    response = requests.post(API_URL, headers=headers, json=payload)
    result = response.json()
    return result["choices"][0]["message"]["content"]

def classify_invoice(recognized_json):
    """根据识别结果分类"""
    # 解析 JSON，判断费用类型，返回去向
    pass

def main():
    """主流程"""
    # 1. 找到所有待处理的图片
    image_files = glob.glob(str(PROJECT_DIR / "**/*.jpg"), recursive=True)
    image_files += glob.glob(str(PROJECT_DIR / "**/*.png"), recursive=True)
    
    # 2. 逐个识别
    results = []
    for img_path in image_files:
        print(f"正在识别: {img_path}")
        try:
            recognized = recognize_invoice(img_path)
            results.append({"file": img_path, "result": recognized})
        except Exception as e:
            results.append({"file": img_path, "error": str(e)})
        time.sleep(0.5)  # 避免请求过快
    
    # 3. 保存结果
    with open("识别结果.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"完成！共处理 {len(results)} 张图片")

if __name__ == "__main__":
    main()
```

---

## 九、常见问题

**Q: API 返回 401？**
A: 检查 API Key 是否正确，确保格式是 `sk-xxxxxxxx`。

**Q: API 返回 429？**
A: 请求太快被限流了，增加 `time.sleep()` 延迟。

**Q: 图片识别不准确？**
A: 尝试提高图片分辨率，或者用 `temperature=0.05` 更保守。

**Q: PDF 怎么处理？**
A: 用 PyMuPDF（pip install pymupdf）提取文本层，如果是扫描件则需要先转图片再调用 vision。

**Q: 怎么批量处理几千个文件？**
A: 加个队列或线程池，控制并发数在 3-5 个，避免触发限流。
