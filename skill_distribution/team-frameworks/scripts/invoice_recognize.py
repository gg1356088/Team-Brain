#!/usr/bin/env python3
"""
发票识别工具 v2.0
==================
独立运行，不依赖 Hermes。只需要 Agnes AI API Key 就能跑。

【⚠️ 接手必读 — 业务规则】
========================
本脚本用于 IncepVision 发票自动化工作流。
接手前必读以下全部规则，不懂就问，不要猜。

工作流总览：
    收集 → 解析(PyMuPDF/Vision) → 识别信息 → 分类 → 待复核分组 → 人工复核 → 归档 → Excel登记

批次管理：
    新批次目录命名：YYYYMMDD-名称-v版本（如 20260611-Receipts-v1）
    每次新批次只移动 00-待处理 和 00-待复核，不动 00-已确认

分组规则：
    每20个普通发票一组，文件夹命名为：第01组、第02组...（两位前导零！macOS按字母排序不加前导零会错）

命名规则：
    YYYYMMDDHHMM-分类-收款方-付款方-$金额.扩展名
    日期12位，扩展名保持原文件类型(pdf/jpg/png/jpeg)

费用类型别名映射（脚本内已内置）：
    fiilng fee/fling fee/filing → Filing Fee
    ca statement of information → Filing Fee
    annual filing fee → Filing Fee
    business registration → Filing Fee
    incorporation → Filing Fee
    trademark → Filing Fee
    tax payment → Tax Payment
    personal tax → Tax Payment
    car rental/car-rental → Travel Expense
    gas → Gas
    fuel → Gas
    parking → Travel Expense
    taxi/uber/lyft → Taxi Fee
    taix fee → Taxi Fee
    meal and entertainment/meals/lunch/dinner/coffee → Meal and Entertainment
    shipping fee/shipping → Shipping-Fee
    professional fee → Professional Fee
    attorney fee → Attorney Fee
    legal fee → Professional Fee
    referral fee → Referral Fee
    agent fee/registered agent fee → Agent Fee
    software fee/software → Software Fee
    computer-software/computer software → Computer-Software
    currency exchange/forex → Currency Exchange
    cash withdraw/cash withdrawal → Cash Withdraw
    retainer refund/retainer → Retainer Refund

分类去向规则：
    律所发票 → 00-已确认/00-律所发票/
        (Professional Fee, Attorney Fee, Legal Fee, Referral Fee, Agent Fee, Software Fee, Computer-Software)
    个人发票 → 00-已确认/00-个人发票/
        (Currency Exchange, Cash Withdraw, Personal Tax, Retainer Refund)
    USPS跳过 → 00-已确认/00-USPS跳过/
        (USPS, Postage)
    普通发票 → 进入待复核流程
        (Filing Fee, Tax Payment, Travel Expense, Gas, Taxi Fee, Meal and Entertainment, Shipping-Fee)

【坑点记录 — 处理时特别注意】
    1. Wave Financial: 收款方是 Wave Financial Inc.，不是 The Wave Team（Stripe商家名）
       分类：Computer-Software
    2. LSCO: AI经常分错，$98.8应该是Shipping-Fee，必须人工判断
    3. Filing ID反查: 通过Filing ID查州务卿数据库反查的公司名 不放入文件名
       例: Acous LLC 是反查的，原始PDF没有这个名称
    4. 政府收据(MA State/NY State/DE State):
       收款方 = 政府机构（如 Commonwealth of Massachusetts）
       付款方 = 实际付款人（如 Xiaoxiao Liu）
       Filing ID反查的公司名不放入文件名
    5. 律所发票(WUKONG等): 律所自开发票不参与客户发票流程，单独存放00-已确认/00-律所发票/
    6. 重复文件: 同一Invoice号的不同命名视为重复，保留一份删除其余
    7. 金额提取: 注意全角$（＄），金额可能是NTD等其他货币，不是所有都是USD

铁律：
    1. 所有文件都要经过识别和判断去向，不能跳过
    2. 普通发票不能跳过待复核，必须人工确认
    3. 个人发票和律所发票虽然不分组，也要识别登记Excel
    4. 不能把文件直接从待处理跳到已确认

用法：
    pip install requests pymupdf
    python invoice_recognize.py

配置：
    在脚本顶部修改 API_KEY 和 PROJECT_DIR
"""

import os
import json
import time
import glob
import requests
from pathlib import Path
from datetime import datetime

# ============================================================
# 配置区 —— 改这里！
# ============================================================

# Agnes AI API Key（去 agnes-ai.com 申请）
API_KEY = "你的API_KEY"

# API 地址
API_URL = "https://apihub.agnes-ai.com/v1/chat/completions"

# 发票项目目录（改成你的实际路径）
PROJECT_DIR = Path("./发票凭证文件")

# 输出目录
OUTPUT_DIR = PROJECT_DIR / "识别结果"

# ============================================================
# 核心功能
# ============================================================

def recognize_image(image_path, prompt=None):
    """
    用 Agnes AI Vision 识别一张图片
    
    Args:
        image_path: 图片文件路径
        prompt: 识别提示词，默认用发票识别模板
    
    Returns:
        识别结果的 JSON 字符串
    """
    if prompt is None:
        prompt = "请识别这张发票图片中的以下信息，用JSON格式返回：收款方、付款方、金额、日期、费用类型。"
    
    # 读取图片并转为 base64
    with open(image_path, "rb") as f:
        img_bytes = f.read()
        img_b64 = __import__('base64').b64encode(img_bytes).decode()
    
    # 动态 MIME 类型
    ext = image_path.lower().split('.')[-1]
    mime_map = {'jpg': 'jpeg', 'jpeg': 'jpeg', 'png': 'png', 'bmp': 'bmp', 'tiff': 'tiff'}
    mime_type = mime_map.get(ext, 'jpeg')
    
    # 构建请求
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
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/{mime_type};base64,{img_b64}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 500,
        "temperature": 0.1
    }
    
    # 发送请求
    response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    
    result = response.json()
    return result["choices"][0]["message"]["content"]


def recognize_pdf_as_image(pdf_path, page_num=0, prompt=None):
    """
    把 PDF 的第一页转成图片，然后用 Vision 识别
    
    需要先安装：pip install pymupdf
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        return None, "需要安装 pymupdf: pip install pymupdf"
    
    # 打开 PDF 并渲染第一页为图片
    doc = fitz.open(pdf_path)
    page = doc[page_num]
    mat = fitz.Matrix(2.0, 2.0)  # 2倍清晰度
    pix = page.get_pixmap(matrix=mat)
    img_data = pix.tobytes("png")
    doc.close()
    
    # 临时保存图片
    tmp_path = "/tmp/pdf_page.png"
    with open(tmp_path, "wb") as f:
        f.write(img_data)
    
    # 用 Vision 识别
    try:
        result = recognize_image(tmp_path, prompt)
        os.remove(tmp_path)
        return result, None
    except Exception as e:
        os.remove(tmp_path)
        return None, str(e)


# ============================================================
# 费用类型别名映射
# ============================================================
ALIAS_MAP = {
    # Filing Fee 别名
    "fiilng fee": "Filing Fee",
    "fling fee": "Filing Fee",
    "filing": "Filing Fee",
    "ca statement of information": "Filing Fee",
    "annual filing fee": "Filing Fee",
    "business registration": "Filing Fee",
    "incorporation": "Filing Fee",
    "trademark": "Filing Fee",
    # Tax Payment 别名
    "tax payment": "Tax Payment",
    "personal tax": "Personal Tax",
    # Travel Expense 别名
    "car rental": "Travel Expense",
    "car-rental": "Travel Expense",
    "gas": "Gas",
    "fuel": "Gas",
    "parking": "Travel Expense",
    "taxi": "Taxi Fee",
    "taix fee": "Taxi Fee",
    "uber": "Taxi Fee",
    "lyft": "Taxi Fee",
    # Meal 别名
    "meal and entertainment": "Meal and Entertainment",
    "meals": "Meal and Entertainment",
    "lunch": "Meal and Entertainment",
    "dinner": "Meal and Entertainment",
    "coffee": "Meal and Entertainment",
    # Shipping 别名
    "shipping fee": "Shipping-Fee",
    "shipping": "Shipping-Fee",
    "usps": "USPS",
    "postage": "Postage",
    # Professional Fee 别名
    "professional fee": "Professional Fee",
    "attorney fee": "Attorney Fee",
    "legal fee": "Professional Fee",
    "referral fee": "Referral Fee",
    "agent fee": "Agent Fee",
    "registered agent fee": "Agent Fee",
    # Software 别名
    "software fee": "Software Fee",
    "software": "Software Fee",
    # Computer-Software 别名
    "computer-software": "Computer-Software",
    "computer software": "Computer-Software",
    # Currency Exchange 别名
    "currency exchange": "Currency Exchange",
    "forex": "Currency Exchange",
    # Cash Withdraw 别名
    "cash withdraw": "Cash Withdraw",
    "cash withdrawal": "Cash Withdraw",
    # Retainer Refund 别名
    "retainer refund": "Retainer Refund",
    "retainer": "Retainer Refund",
}

# ============================================================
# 坑点记录（处理时特别注意）
# ============================================================
PITFALLS = {
    "wave financial": {
        "note": "收款方是 Wave Financial Inc.，不是 The Wave Team（Stripe商家名）",
        "correct_payee": "Wave Financial Inc.",
        "category": "Computer-Software",
    },
    "lscopacific": {
        "note": "AI经常分错，$98.8应该是Shipping-Fee，必须人工判断",
        "suggested_category": "Shipping-Fee",
    },
}

# ============================================================
# 分类规则
# ============================================================
CATEGORY_RULES = {
    "律所发票": [
        "Professional Fee", "Attorney Fee", "Legal Fee",
        "Referral Fee", "Agent Fee", "Software Fee",
        "Computer-Software",
    ],
    "个人发票": [
        "Currency Exchange", "Cash Withdraw", "Personal Tax",
        "Retainer Refund",
    ],
    "USPS跳过": [
        "USPS", "Postage",
    ],
}


def normalize_fee_type(raw_type):
    """标准化费用类型，应用别名映射"""
    if not raw_type:
        return raw_type
    t = raw_type.strip().lower()
    if t in ALIAS_MAP:
        return ALIAS_MAP[t]
    # 模糊匹配：别名包含在原始类型中
    for alias, normalized in ALIAS_MAP.items():
        if alias in t or t in alias:
            return normalized
    return raw_type.strip()


def classify_invoice(data):
    """
    根据识别结果分类文件去向
    
    Args:
        data: 识别结果字典，包含费用类型、收款方等信息
    
    Returns:
        目标文件夹名
    """
    fee_type = normalize_fee_type(data.get("费用类型", ""))
    payee = data.get("收款方", "").lower()
    
    # 检查坑点记录 — 子串匹配
    for pitfall_key, pf in PITFALLS.items():
        if pitfall_key in payee:
            pf = PITFALLS[pitfall_key]
            if "suggested_category" in pf:
                data["费用类型"] = pf["suggested_category"]
                fee_type = pf["suggested_category"]
            if "correct_payee" in pf:
                data["收款方"] = pf["correct_payee"]
    
    # 按分类规则判断
    for dest, cats in CATEGORY_RULES.items():
        for cat in cats:
            if cat.lower() in fee_type.lower() or fee_type.lower() in cat.lower():
                return dest
    
    # 默认 → 待复核
    return "待复核"


# ============================================================
# 批量处理
# ============================================================

def scan_image_files(directory):
    """扫描目录下的所有图片文件"""
    extensions = ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.tiff']
    files = []
    for ext in extensions:
        files.extend(glob.glob(os.path.join(directory, '**', ext), recursive=True))
    return files


def scan_pdf_files(directory):
    """扫描目录下的所有 PDF 文件"""
    return glob.glob(os.path.join(directory, '**', '*.pdf'), recursive=True)


def process_batch(image_files, output_file, batch_size=10, delay=1.0):
    """
    批量处理图片文件
    
    Args:
        image_files: 图片文件路径列表
        output_file: 输出 JSON 文件路径
        batch_size: 每批处理数量（用于分阶段保存）
        delay: 每张之间的延迟（秒）
    """
    results = []
    total = len(image_files)
    
    print(f"开始处理 {total} 个文件...")
    print(f"每批 {batch_size} 个，间隔 {delay}s\n")
    
    for i, img_path in enumerate(image_files):
        print(f"[{i+1}/{total}] 处理: {img_path}")
        
        try:
            recognized = recognize_image(img_path)
            
            # 尝试解析为 JSON
            try:
                parsed = json.loads(recognized)
            except json.JSONDecodeError:
                # 如果不是 JSON，尝试从文本中提取
                parsed = {"raw": recognized}
            
            result = {
                "file": img_path,
                "status": "success",
                "recognized": parsed,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            result = {
                "file": img_path,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        
        results.append(result)
        
        # 阶段性保存，防止中断丢失
        if (i + 1) % batch_size == 0:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"  → 已保存进度 ({len(results)} 个)")
        
        # 延迟
        time.sleep(delay)
    
    # 最终保存
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    # 统计
    success = sum(1 for r in results if r["status"] == "success")
    failed = total - success
    
    print(f"\n{'='*50}")
    print(f"处理完成！")
    print(f"  成功: {success}/{total}")
    print(f"  失败: {failed}/{total}")
    print(f"  结果保存在: {output_file}")
    print(f"{'='*50}")
    
    return results


# ============================================================
# 主入口
# ============================================================

def main():
    print("=" * 50)
    print("发票识别工具 v2.0")
    print("=" * 50)
    
    # 检查 API Key
    if API_KEY == "你的API_KEY":
        print("\n⚠️  请先修改脚本顶部的 API_KEY！")
        print("   去 agnes-ai.com 申请一个 API Key")
        return
    
    # 检查项目目录
    if not PROJECT_DIR.exists():
        print(f"\n⚠️  项目目录不存在: {PROJECT_DIR}")
        print("   请在脚本中修改 PROJECT_DIR 为你的实际路径")
        return
    
    # 创建输出目录
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    # 扫描文件
    print(f"\n扫描目录: {PROJECT_DIR}")
    
    image_files = scan_image_files(PROJECT_DIR)
    pdf_files = scan_pdf_files(PROJECT_DIR)
    
    print(f"  图片文件: {len(image_files)} 个")
    print(f"  PDF 文件: {len(pdf_files)} 个")
    
    if not image_files and not pdf_files:
        print("\n没有找到任何文件！")
        return
    
    # 处理图片
    if image_files:
        print("\n--- 开始处理图片 ---")
        output_file = str(OUTPUT_DIR / "识别结果.json")
        process_batch(image_files, output_file, batch_size=5, delay=1.0)
    
    # 处理 PDF（如果需要）
    if pdf_files:
        print("\n--- 开始处理 PDF ---")
        print("PDF 需要先转图片再用 Vision 识别")
        print("建议先用 PyMuPDF 提取文本层，扫描件才用 Vision")
    
    print("\n完成！")


if __name__ == "__main__":
    main()
