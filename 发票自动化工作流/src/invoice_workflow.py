#!/usr/bin/env python3
"""
发票自动化工作流工具 v2.0
========================
发票PDF/图片的完整处理流程：识别 → 分类 → 待复核分组 → Excel登记 → 归档

【⚠️ 必读 — 接手必看】
========================
本脚本用于 IncepVision Law 发票自动化工作流。
接手前必读以下全部规则，不懂就问，不要猜。

工作流总览：
    收集 → 解析(PyMuPDF/Vision) → 识别信息 → 分类 → 待复核分组 → 人工复核 → 归档 → Excel登记

批次管理：
    新批次目录命名：YYYYMMDD-名称-v版本（如 20260611-Receipts-v1）
    每次新批次只移动 00-待处理 和 00-待复核，不动 00-已确认

分组规则：
    每20个普通发票一组，文件夹命名为：第01组、第02组...（两位前导零！macOS按字母排序不加前导零会错）

Excel登记（9列）：
    序号 | 状态 | 凭证文件名 | 日期时间(12位) | 费用类型 | 收款方 | 付款方 | 金额 | 备注
    状态列：绿色背景(#C6EFCE)深绿文字(#006100)居中
    表头：微软雅黑11号加粗白字，蓝底(#4472C4)居中
    数据行：微软雅黑10号，细线边框
    金额列：右对齐#,##0.00
    写入后必须用load_workbook重新读取验证行数和金额

铁律：
    1. 所有文件都要经过识别和判断去向，不能跳过
    2. 普通发票不能跳过待复核，必须人工确认
    3. 个人发票和律所发票虽然不分组，也要识别登记Excel
    4. 不能把文件直接从待处理跳到已确认

费用别名映射（已内置见ALIAS_MAP）：
    fiilng fee/fling fee/filing → Filing Fee
    ca statement of information → Filing Fee
    tax payment → Tax Payment
    car rental → Travel Expense
    gas → Gas
    meal and entertainment → Meal and Entertainment
    taix fee → Taxi Fee

分类去向规则（已内置见CATEGORY_RULES）：
    律所发票 → 00-已确认/00-律所发票/
    个人发票 → 00-已确认/00-个人发票/
    USPS跳过 → 00-已确认/00-USPS跳过/
    普通发票 → 进入待复核流程

【坑点记录 — 处理时特别注意】
========================
1. Wave Financial: 收款方是 Wave Financial Inc.，不是 The Wave Team（Stripe商家名）
   分类：Computer-Software

2. LSCO: AI经常分错，$98.8 应该是 Shipping-Fee，必须人工判断

3. Filing ID反查问题: 通过Filing ID查询州务卿数据库反查的公司名 不放入文件名
   例: Acous LLC 是反查的，原始PDF没有这个名称

4. 政府收据(MA State/NY State/DE State):
   收款方 = 政府机构（Commonwealth of Massachusetts）
   付款方 = 实际付款人（如 Xiaoxiao Liu）
   Filing ID反查的公司名不放入文件名

5. 律所发票(WUKONG等): 律所自开发票不参与客户发票识别流程，单独存放00-已确认/00-律所发票/

6. 重复文件: 同一Invoice号的不同命名视为重复，保留一份删除其余

7. 金额提取: 注意全角$（＄），金额可能是NTD等其他货币

命名规则（PDF可直接从文件名提取）：
    YYYYMMDDHHMM-分类-收款方-付款方-$金额.扩展名
    日期12位，扩展名保持原文件类型(pdf/jpg/png/jpeg)

用法：
    python invoice_workflow.py <command> [options]

命令：
    audit           审计当前工作流状态（接手前必做）
    parse           从文件名解析所有待处理文件信息
    classify        按规则判断文件去向
    group-review    分组到待复核
    report          生成状态报告
    vision-recognize  用 Agnes AI Vision API 批量识别发票图片/PDF

示例：
    python invoice_workflow.py audit
    python invoice_workflow.py parse --dir "00-待处理"
    python invoice_workflow.py classify
    python invoice_workflow.py group-review --batch-size 20
    python invoice_workflow.py report
    python invoice_workflow.py vision-recognize --dir "00-待处理"

配置 Agnes AI API：
    export AGNES_API_KEY=***
    export AGNES_API_URL=https://apihub.agnes-ai.com/v1/chat/completions
    export AGNES_MODEL=agnes-2.0-flash

作者：Hermes Agent
日期：2026-06-15
"""

import os
import re
import json
import csv
import sys
import shutil
import time
import base64
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime


# ============================================================
# 配置
# ============================================================

PROJECT_DIR = Path("/Users/xinban/IncepVision Law/20260611-Receipts-v1")
INDEX_FILE = PROJECT_DIR / f"00-发票总索引-{datetime.now().strftime('%Y%m%d')}.csv"

# Agnes AI Vision API 配置（不依赖 Hermes，独立可调）
AGNES_API_KEY = os.environ.get("AGNES_API_KEY", "")
AGNES_API_URL = os.environ.get("AGNES_API_URL", "https://apihub.agnes-ai.com/v1/chat/completions")
AGNES_MODEL = os.environ.get("AGNES_MODEL", "agnes-2.0-flash")

# 发票识别 Prompt
INVOICE_PROMPT = (
    "请识别这张发票图片中的以下信息，用JSON格式返回，不要有其他文字："
    '{"收款方":"","付款方":"","金额":"","日期":"","费用类型":""}'
)

# 批量处理参数
VISION_BATCH_SIZE = 5  # 每批保存次数
VISION_DELAY = 1.0     # 每张之间的延迟（秒）

# 文件夹结构
DIRS = {
    "待处理": PROJECT_DIR / "00-待处理",
    "待复核": PROJECT_DIR / "00-待复核",
    "已确认": PROJECT_DIR / "00-已确认",
    "律所发票": PROJECT_DIR / "00-已确认" / "00-律所发票",
    "个人发票": PROJECT_DIR / "00-已确认" / "00-个人发票",
    "USPS跳过": PROJECT_DIR / "00-已确认" / "00-USPS跳过",
}

# ============================================================
# 坑点记录（接手必读！处理时特别注意）
# ============================================================
# 1. Wave Financial: 原始PDF收款方=Wave Financial Inc.，不是The Wave Team（Stripe商家名）
#    分类：Computer-Software
# 2. LSCO: AI经常分错，$98.8应该是Shipping-Fee，必须人工判断
# 3. Filing ID反查: 通过Filing ID查州务卿数据库反查的公司名 不放入文件名
#    例: Acous LLC是反查的，原始PDF没有这个名称
# 4. 政府收据(MA State/NY State/DE State):
#    收款方=政府机构（如Commonwealth of Massachusetts）
#    付款方=实际付款人（如Xiaoxiao Liu）
#    Filing ID反查的公司名不放入文件名
# 5. 律所发票(WUKONG等): 律所自开发票不参与客户发票流程，单独存放00-已确认/00-律所发票/
# 6. 重复文件: 同一Invoice号的不同命名文件视为重复，保留一份删除其余
# 7. 金额提取: 注意全角$（＄），金额可能是NTD等其他货币，不是所有都是USD
# ============================================================

# 费用类型别名映射
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

# 分类规则：哪些类型直接归入特定文件夹
CATEGORY_RULES = {
    "律所发票": [
        # 律所自开发票（不参与客户发票流程）
        "Professional Fee", "Attorney Fee", "Legal Fee",
        "Referral Fee", "Agent Fee", "Software Fee",
        "Computer-Software",
    ],
    "个人发票": [
        # 个人消费性质
        "Currency Exchange", "Cash Withdraw", "Personal Tax",
        "Retainer Refund",
    ],
    "USPS跳过": [
        # 无法处理或特殊标记
        "USPS", "Postage",
    ],
}


# ============================================================
# 工具函数
# ============================================================

def clean_amount(raw):
    """清理金额字符串
    
    注意：
    - 处理全角$（＄）
    - 可能不是USD（如NTD），但金额提取方式一样
    - 注意带空格的情况
    """
    if not raw:
        return None
    s = str(raw).replace('＄', '$')  # 全角美元
    s = re.sub(r'[^\d.\-]', '', s.replace('$', '').replace(',', ''))
    try:
        return float(s) if s else None
    except ValueError:
        return None


def parse_filename(name):
    """从文件名解析字段"""
    # 去掉扩展名
    ext = ""
    for e in ['.pdf', '.jpg', '.png', '.jpeg']:
        if name.lower().endswith(e):
            ext = e
            name = name[:-len(e)]
            break

    name_lower = name.lower()

    # 日期前缀（8-14位数字）
    m = re.match(r'^(\d{8,14})-', name)
    date_prefix = m.group(1) if m else None

    # 金额（从右往左找 $数字）
    amount_raw = None
    m = re.search(r'-?\$?\s*([\d,.]+)', name[::-1])
    if m:
        amount_raw = m.group(1)
    amount = clean_amount(amount_raw) if amount_raw else None

    # 中间部分：分类-收款方-付款方
    category = ""
    payee = ""
    payer = ""

    if '-' in name:
        parts = name.split('-', 2)
        if len(parts) >= 3:
            rest = parts[2]
            rest_parts = rest.split('-')
            category = rest_parts[0] if rest_parts else ""
            payee = rest_parts[1] if len(rest_parts) > 1 else ""
            payer = rest_parts[2] if len(rest_parts) > 2 else ""

    # 别名映射
    cat_lower = category.lower().strip()
    if cat_lower in ALIAS_MAP:
        category = ALIAS_MAP[cat_lower]

    return {
        'original_name': name + ext,
        'extension': ext,
        'date_prefix': date_prefix,
        'amount': amount,
        'category': category,
        'payee': payee,
        'payer': payer,
    }


def detect_file_type(filepath):
    """通过文件头判断真实文件类型"""
    try:
        with open(filepath, 'rb') as f:
            header = f.read(10)
        if header[:5] == b'%PDF-':
            return '.pdf'
        elif header[:3] == b'\xff\xd8\xff':
            return '.jpg'
        elif header[:8] == b'\x89PNG\r\n\x1a\n':
            return '.png'
        elif header[:4] == b'PK\x03\x04':
            return '.docx'
        return ''
    except Exception:
        return ''


def get_files_recursive(directory, extensions=None):
    """递归获取目录下所有文件"""
    if not directory.exists():
        return []
    if extensions:
        return [f for f in directory.rglob('*')
                if f.is_file() and f.suffix.lower() in extensions]
    return [f for f in directory.rglob('*') if f.is_file()]


def count_files(directory, extensions=None):
    """统计目录下文件数"""
    files = get_files_recursive(directory, extensions)
    return len(files)


# ============================================================
# Agnes AI Vision API 调用
# ============================================================

def image_to_base64(image_path):
    """将图片文件转为 base64 编码"""
    with open(image_path, 'rb') as f:
        return base64.b64encode(f.read()).decode()


def pdf_page_to_image(pdf_path, page_num=0, scale=2.0):
    """将 PDF 页面渲染为 PNG 图片字节数据"""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        print("  ⚠️  需要安装 pymupdf: pip install pymupdf")
        return None
    doc = fitz.open(pdf_path)
    page = doc[page_num]
    mat = fitz.Matrix(scale, scale)
    pix = page.get_pixmap(matrix=mat)
    img_bytes = pix.tobytes("png")
    doc.close()
    return img_bytes


def recognize_with_agnes(image_path, prompt=None):
    """
    用 Agnes AI Vision API 识别图片
    
    Args:
        image_path: 图片文件路径
        prompt: 识别提示词，默认用发票模板
    
    Returns:
        (result_dict, error_string) - 成功返回 (dict, None)，失败返回 (None, error)
    """
    if prompt is None:
        prompt = INVOICE_PROMPT
    
    if not AGNES_API_KEY:
        return None, "AGNES_API_KEY 未设置。请设置环境变量或修改脚本顶部配置。"
    
    # 判断文件类型，决定读取方式
    if image_path.lower().endswith('.pdf'):
        img_bytes = pdf_page_to_image(image_path)
        if img_bytes is None:
            return None, "PDF 渲染失败（需要 pymupdf）"
        img_b64 = base64.b64encode(img_bytes).decode()
        mime_type = "image/png"
    else:
        img_b64 = image_to_base64(image_path)
        ext = image_path.lower().split('.')[-1]
        mime_type = f"image/{ext}"
    
    headers = {
        "Authorization": f"Bearer {AGNES_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": AGNES_MODEL,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime_type};base64,{img_b64}"
                    }
                }
            ]
        }],
        "max_tokens": 500,
        "temperature": 0.1
    }
    
    try:
        import urllib.request
        req = urllib.request.Request(AGNES_API_URL, headers=headers, method="POST")
        data = json.dumps(payload).encode()
        resp = urllib.request.urlopen(req, data=data, timeout=30)
        result = json.loads(resp.read())
        content = result["choices"][0]["message"]["content"]
        
        # 尝试解析 JSON
        try:
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            return json.loads(content), None
        except json.JSONDecodeError:
            return {"raw": content}, None
        
    except Exception as e:
        return None, str(e)


def batch_recognize(image_files, prompt=None):
    """
    批量图片识别，支持阶段性保存（防中断丢数据）
    
    Args:
        image_files: 图片文件路径列表
        prompt: 识别提示词
    
    Returns:
        results 列表
    """
    results = []
    total = len(image_files)
    
    print(f"  批量识别 {total} 个文件...")
    print(f"  每 {VISION_BATCH_SIZE} 个保存一次进度")
    print()
    
    for i, img_path in enumerate(image_files):
        rel_path = str(Path(img_path).relative_to(PROJECT_DIR)) if PROJECT_DIR in img_path.parents else str(img_path)
        print(f"  [{i+1}/{total}] {rel_path}")
        
        recognized, error = recognize_with_agnes(img_path, prompt)
        
        if recognized:
            results.append({
                "file": img_path,
                "status": "success",
                "data": recognized,
            })
        else:
            results.append({
                "file": img_path,
                "status": "error",
                "error": error,
            })
        
        # 阶段性保存
        if (i + 1) % VISION_BATCH_SIZE == 0:
            output_path = PROJECT_DIR / "vision_partial_results.json"
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"    → 已保存进度 ({len(results)} 个)")
        
        # 延迟避免限流
        time.sleep(VISION_DELAY)
    
    # 最终保存
    output_path = PROJECT_DIR / "vision_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    success = sum(1 for r in results if r["status"] == "success")
    failed = total - success
    print(f"\n  ✅ 完成！成功 {success}/{total}，失败 {failed}/{total}")
    print(f"  结果保存在: {output_path}")
    print(f"  部分结果保存在: {PROJECT_DIR}/vision_partial_results.json")
    
    return results


# ============================================================
# 命令实现
# ============================================================

def cmd_vision_recognize(args):
    """用 Agnes AI Vision API 识别发票图片/PDF"""
    target_dir = args.get('dir', '00-待处理')
    target_path = PROJECT_DIR / target_dir
    
    if not target_path.exists():
        print(f"❌ 目录不存在: {target_path}")
        return
    
    # 检查 API Key
    if not AGNES_API_KEY:
        print("❌ AGNES_API_KEY 未设置")
        print("  设置方式（任选一种）:")
        print("    export AGNES_API_KEY=sk-xxxxxxx")
        print("    或者在脚本顶部修改 AGNES_API_KEY 变量")
        return
    
    # 找所有需要识别的文件
    image_files = []
    for ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.pdf']:
        image_files.extend(target_path.rglob(f'*{ext}'))
    
    # 去掉子目录中的非文件项
    image_files = [f for f in image_files if f.is_file()]
    
    if not image_files:
        print(f"❌ 没有在 {target_dir} 找到图片/PDF 文件")
        return
    
    print("=" * 50)
    print(f"Agnes AI Vision 发票识别")
    print(f"目标目录: {target_dir}")
    print(f"文件数: {len(image_files)}")
    print(f"模型: {AGNES_MODEL}")
    print(f"API: {AGNES_API_URL}")
    print("=" * 50)
    print()
    
    # 执行批量识别
    results = batch_recognize(image_files)
    
    # 统计
    success = sum(1 for r in results if r["status"] == "success")
    failed = len(results) - success
    
    if failed > 0:
        print(f"\n⚠️  有 {failed} 个文件识别失败，请检查 vision_results.json")
    
    return results


def cmd_audit(args):
    """审计当前工作流状态"""
    print("=" * 60)
    print("发票工作流审计")
    print("=" * 60)
    print()

    # 1. 项目目录
    print("【项目目录】")
    print(f"  路径: {PROJECT_DIR}")
    if PROJECT_DIR.exists():
        items = list(PROJECT_DIR.iterdir())
        dirs = [f.name for f in items if f.is_dir()]
        files = [f.name for f in items if f.is_file()]
        print(f"  子目录: {len(dirs)}")
        for d in sorted(dirs):
            print(f"    - {d}")
        print(f"  根文件: {len(files)}")
        for f in sorted(files):
            print(f"    - {f}")
    else:
        print("  ❌ 项目目录不存在！")
    print()

    # 2. 待处理
    print("【待处理】")
    dp = DIRS["待处理"]
    if dp.exists():
        subdirs = [d for d in dp.iterdir() if d.is_dir()]
        print(f"  子目录数: {len(subdirs)}")
        total_files = 0
        ext_counter = Counter()
        for sd in subdirs:
            for f in sd.iterdir():
                if f.is_file():
                    total_files += 1
                    ext_counter[f.suffix.lower() or '(无扩展名)'] += 1
        print(f"  文件总数: {total_files}")
        if ext_counter:
            for ext, cnt in ext_counter.most_common():
                print(f"    - {ext}: {cnt}")
    else:
        print("  ❌ 不存在")
    print()

    # 3. 待复核
    print("【待复核】")
    dr = DIRS["待复核"]
    if dr.exists():
        groups = [d for d in dr.iterdir() if d.is_dir()]
        print(f"  组数: {len(groups)}")
        total_pdf = 0
        total_any = 0
        for g in groups:
            pdfs = list(g.glob('*.pdf'))
            total_pdf += len(pdfs)
            total_any += len(list(g.iterdir()))
        print(f"  PDF总数: {total_pdf}")
        print(f"  所有文件总数: {total_any}")
    else:
        print("  ❌ 不存在")
    print()

    # 4. 已确认
    print("【已确认】")
    dc = DIRS["已确认"]
    if dc.exists():
        items = list(dc.iterdir())
        subdirs = [d for d in items if d.is_dir()]
        print(f"  子目录数: {len(subdirs)}")
        for sd in sorted(subdirs):
            cnt = len(list(sd.iterdir()))
            print(f"    - {sd.name}: {cnt}个文件")
    else:
        print("  ❌ 不存在")
    print()

    # 5. 总索引
    print("【总索引】")
    if INDEX_FILE.exists():
        with open(INDEX_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        print(f"  文件: {INDEX_FILE.name}")
        print(f"  总行数: {len(lines)}")
        if len(lines) > 1:
            # 统计状态分布
            status_counter = Counter()
            for line in lines[1:]:
                parts = line.strip().split(',')
                if len(parts) >= 2:
                    status_counter[parts[1].strip()] += 1
            print("  状态分布:")
            for status, cnt in status_counter.most_common():
                print(f"    - {status}: {cnt}")
    else:
        print("  ❌ 不存在")
    print()

    print("=" * 60)
    print("审计完成")
    print("=" * 60)


def cmd_parse(args):
    """从文件名解析所有待处理文件"""
    target_dir = args.get('dir', '00-待处理')
    target_path = PROJECT_DIR / target_dir

    print(f"解析目录: {target_path}")
    print()

    results = []
    ext_counter = Counter()

    for subdir in sorted(target_path.iterdir()):
        if not subdir.is_dir():
            continue
        for filepath in sorted(subdir.iterdir()):
            if not filepath.is_file():
                continue

            ext_counter[filepath.suffix.lower() or '(无)'] += 1
            parsed = parse_filename(filepath.name)

            results.append({
                'subdir': subdir.name,
                'filename': filepath.name,
                'parsed': parsed,
                'real_type': detect_file_type(filepath),
            })

    print(f"共解析 {len(results)} 个文件")
    print(f"文件类型分布: {dict(ext_counter)}")
    print()

    # 输出解析结果
    for r in results[:20]:  # 只显示前20条
        p = r['parsed']
        print(f"[{r['subdir']}] {r['filename']}")
        print(f"  日期: {p['date_prefix'] or '❌ 无'}")
        print(f"  分类: {p['category'] or '❌ 无'}")
        print(f"  收款方: {p['payee'] or '❌ 无'}")
        print(f"  付款方: {p['payer'] or '❌ 无'}")
        print(f"  金额: {p['amount'] if p['amount'] else '❌ 无'}")
        print(f"  真实类型: {r['real_type'] or '未知'}")
        print()

    if len(results) > 20:
        print(f"... 还有 {len(results) - 20} 条结果")

    # 保存完整结果
    output_path = PROJECT_DIR / "parse_results.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"完整结果已保存到: {output_path}")


def cmd_classify(args):
    """按分类规则判断文件去向"""
    results_path = PROJECT_DIR / "parse_results.json"

    if not results_path.exists():
        print("❌ 请先运行 parse 命令生成解析结果")
        return

    with open(results_path, 'r', encoding='utf-8') as f:
        results = json.load(f)

    # 分类统计
    category_dest = defaultdict(list)
    dest_counter = Counter()

    for r in results:
        p = r['parsed']
        category = p['category'].lower().strip()

        # 判断去向
        destination = "待复核"  # 默认

        for dest, cats in CATEGORY_RULES.items():
            for cat in cats:
                if cat.lower() in category or category in cat.lower():
                    destination = dest
                    break

        category_dest[destination].append(r)
        dest_counter[destination] += 1

    print("分类结果:")
    print("-" * 40)
    for dest, files in category_dest.items():
        print(f"\n【{dest}】 ({len(files)}个)")
        for f in files[:5]:
            p = f['parsed']
            print(f"  - {f['filename']}")
            if len(files) > 5:
                print(f"  ... 还有 {len(files) - 5} 个")
    print()
    print("去向统计:")
    for dest, cnt in dest_counter.most_common():
        print(f"  {dest}: {cnt}")

    # 保存结果
    output_path = PROJECT_DIR / "classify_results.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            'destinations': dict(dest_counter),
            'files': category_dest,
        }, f, ensure_ascii=False, indent=2)
    print(f"\n分类结果已保存到: {output_path}")


def cmd_group_review(args):
    """将普通发票分组到待复核文件夹"""
    batch_size = args.get('batch_size', 20)
    classify_path = PROJECT_DIR / "classify_results.json"

    if not classify_path.exists():
        print("❌ 请先运行 classify 命令")
        return

    with open(classify_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    review_files = data.get('files', {}).get('待复核', [])
    total = len(review_files)
    print(f"待复核文件总数: {total}")
    print(f"每组大小: {batch_size}")
    print(f"预计组数: {(total + batch_size - 1) // batch_size}")
    print()

    # 按类别排序
    category_order = Counter()
    for f in review_files:
        cat = f['parsed']['category']
        category_order[cat] += 1

    sorted_files = sorted(review_files,
                         key=lambda x: (-category_order[x['parsed']['category']],
                                       x['filename']))

    # 创建分组文件夹
    review_dir = DIRS["待复核"]
    review_dir.mkdir(parents=True, exist_ok=True)

    groups = []
    for i in range(0, total, batch_size):
        batch = sorted_files[i:i + batch_size]
        group_num = (i // batch_size) + 1
        group_name = f"第{group_num:02d}组"
        group_dir = review_dir / group_name

        group_dir.mkdir(parents=True, exist_ok=True)

        for f in batch:
            src = PROJECT_DIR / "00-待处理" / f['subdir'] / f['filename']
            dst = group_dir / f['filename']
            if src.exists():
                shutil.move(str(src), str(dst))

        groups.append({
            'group': group_name,
            'start': i + 1,
            'end': min(i + batch_size, total),
            'count': len(batch),
            'path': str(group_dir),
        })

    print(f"✅ 分组完成！共 {len(groups)} 组")
    for g in groups[:5]:
        print(f"  {g['group']}: {g['count']}个文件")
    if len(groups) > 5:
        print(f"  ... 还有 {len(groups) - 5} 组")
    print()
    print(f"结果已保存到: {review_dir}")

    # 保存分组结果
    output_path = PROJECT_DIR / "group_review_results.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(groups, f, ensure_ascii=False, indent=2)


def cmd_report(args):
    """生成当前工作流状态报告"""
    print("=" * 60)
    print("发票工作流状态报告")
    print(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()

    # 各文件夹统计
    stats = {}

    for name, path in DIRS.items():
        if name == "已确认":
            stats[name] = {
                'total': count_files(path),
                'subdirs': {}
            }
            if path.exists():
                for sd in path.iterdir():
                    if sd.is_dir():
                        stats[name]['subdirs'][sd.name] = count_files(sd)
        else:
            stats[name] = {
                'total': count_files(path),
            }
            if name == "待处理" and path.exists():
                # 统计子目录
                subdirs = [d for d in path.iterdir() if d.is_dir()]
                stats[name]['subdir_count'] = len(subdirs)
                ext_counter = Counter()
                for sd in subdirs:
                    for f in sd.iterdir():
                        if f.is_file():
                            ext_counter[f.suffix.lower() or '(无)'] += 1
                stats[name]['extensions'] = dict(ext_counter)
            elif name == "待复核" and path.exists():
                groups = [d for d in path.iterdir() if d.is_dir()]
                stats[name]['group_count'] = len(groups)

    # 打印统计
    print("【文件夹统计】")
    print(f"  待处理: {stats['待处理']['total']}个文件")
    if 'subdir_count' in stats['待处理']:
        print(f"    子目录: {stats['待处理']['subdir_count']}")
    if 'extensions' in stats['待处理']:
        for ext, cnt in stats['待处理']['extensions'].items():
            print(f"    {ext}: {cnt}")

    print(f"  待复核: {stats['待复核']['total']}个文件")
    if 'group_count' in stats['待复核']:
        print(f"    组数: {stats['待复核']['group_count']}")

    print(f"  已确认: {stats['已确认']['total']}个文件")
    for sub, cnt in stats['已确认'].get('subdirs', {}).items():
        print(f"    {sub}: {cnt}")

    # 总索引
    print()
    print("【总索引】")
    if INDEX_FILE.exists():
        with open(INDEX_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        print(f"  文件: {INDEX_FILE.name}")
        print(f"  总行数: {len(lines)} (含表头)")
    else:
        print("  不存在")

    print()
    print("=" * 60)


# ============================================================
# 主程序
# ============================================================

def print_usage():
    print(__doc__)


def main():
    if len(sys.argv) < 2:
        print_usage()
        return

    command = sys.argv[1]
    args = {}

    # 解析命令行参数
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == '--dir' and i + 1 < len(sys.argv):
            args['dir'] = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == '--batch-size' and i + 1 < len(sys.argv):
            args['batch_size'] = int(sys.argv[i + 1])
            i += 2
        else:
            i += 1

    commands = {
        'audit': cmd_audit,
        'parse': cmd_parse,
        'classify': cmd_classify,
        'group-review': cmd_group_review,
        'report': cmd_report,
        'vision-recognize': cmd_vision_recognize,
    }

    if command in commands:
        commands[command](args)
    else:
        print(f"❌ 未知命令: {command}")
        print_usage()


if __name__ == '__main__':
    main()
