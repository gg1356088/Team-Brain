#!/usr/bin/env python3
"""
发票自动化工作流索引修复脚本
以实际文件夹为 truth source，重建总索引
"""

import csv
import re
import os
from pathlib import Path
from datetime import datetime

WORKDIR = Path("/Users/xinban/IncepVision Law/20260611-Receipts-v1")
REVIEW_DIR = WORKDIR / "00-待复核"
IDX_FILE = WORKDIR / "00-发票总索引-20260615.csv"
BACKUP_FILE = WORKDIR / "00-发票总索引-20260615-备份.csv"

def parse_filename(filename):
    """从文件名提取字段"""
    # 去掉扩展名
    stem = Path(filename).stem
    
    # 提取日期（前8-14位数字）
    date_match = re.match(r'^(\d{8,14})', stem)
    date = date_match.group(1) if date_match else "00000000"
    
    # 去掉日期部分
    rest = stem[len(date):]
    if rest.startswith('-'):
        rest = rest[1:]
    
    # 提取金额（从右侧找 -$XX.XX 或 -$XX）
    amount_match = re.search(r'-\$([\d,.]+)$', rest)
    amount = amount_match.group(1) if amount_match else ""
    
    # 提取费用类型（第一个 '-' 后的部分）
    parts = rest.split('-')
    expense_type = parts[0] if parts else ""
    
    # 剩余部分：收款方、付款方
    remaining = '-'.join(parts[1:]) if len(parts) > 1 else ""
    
    # 付款方通常是最后一个 '-' 前的部分（如果金额前有逗号+Inc.等）
    # 收款方是第一个 '-' 后的部分
    # 需要更精细的解析
    
    # 简化策略：从右往左找
    # 格式：日期-费用类型-收款方-付款方-$金额
    # 但有些文件只有：日期-费用类型-收款方-$金额（无付款方）
    
    # 重新解析
    # 去掉金额
    if amount:
        remaining = remaining.rsplit('-', 1)[0] if '-' in remaining else remaining
    
    # 去掉费用类型
    if expense_type:
        remaining = remaining[len(expense_type):]
        if remaining.startswith('-'):
            remaining = remaining[1:]
    
    # 现在 remaining 是 "收款方-付款方" 或 "收款方"
    if '-' in remaining:
        # 判断哪个是收款方哪个是付款方
        # 收款方通常较短，付款方通常有 Inc./LLC/Co 等
        segments = remaining.split('-')
        if len(segments) == 2:
            payee = segments[0]
            company = segments[1]
        elif len(segments) > 2:
            # 收款方可能包含逗号（如 "Harvard Business Services, Inc"）
            # 但逗号不是 '-'，所以 segments 不会分割逗号部分
            # 取前一个为收款方，最后一个为付款方
            payee = segments[0]
            company = '-'.join(segments[1:])
        else:
            payee = remaining
            company = ""
    else:
        payee = remaining
        company = ""
    
    return {
        'date': date,
        'expense_type': expense_type.strip(),
        'payee': payee.strip(),
        'company': company.strip(),
        'amount': f"${amount}" if amount else "",
    }


def main():
    print("=" * 60)
    print("发票自动化工作流索引修复")
    print("=" * 60)
    
    # 1. 备份原索引
    if IDX_FILE.exists():
        import shutil
        shutil.copy2(IDX_FILE, BACKUP_FILE)
        print(f"\n[OK] 原索引已备份到: {BACKUP_FILE.name}")
    
    # 2. 统计实际文件
    groups = sorted([d for d in REVIEW_DIR.iterdir() if d.is_dir()])
    print(f"\n[INFO] 待复核分组数: {len(groups)}")
    
    all_files = []
    for g in groups:
        for f in g.iterdir():
            if f.name != '.DS_Store':
                all_files.append((g.name, f.name))
    
    print(f"[INFO] 实际文件总数: {len(all_files)}")
    
    # 3. 解析每个文件
    records = []
    for group_name, filename in all_files:
        parsed = parse_filename(filename)
        records.append({
            'group': group_name,
            'filename': filename,
            **parsed
        })
    
    # 4. 写入新索引
    new_idx = WORKDIR / "00-发票总索引-20260616.csv"
    with open(new_idx, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(['序号', '状态', '凭证文件名', '日期', '费用类型', '收款方', '付款方', '金额', '备注'])
        for i, rec in enumerate(records, 1):
            writer.writerow([
                i,
                rec['group'],
                rec['filename'],
                rec['date'],
                rec['expense_type'],
                rec['payee'],
                rec['company'],
                rec['amount'],
                ''
            ])
    
    print(f"\n[OK] 新索引已写入: {new_idx.name}")
    print(f"[OK] 新索引记录数: {len(records)}")
    
    # 5. 验证
    # 统计各组的记录数
    group_counts = {}
    for rec in records:
        g = rec['group']
        group_counts[g] = group_counts.get(g, 0) + 1
    
    print(f"\n=== 验证结果 ===")
    mismatch = 0
    for g in groups:
        group_name = g.name
        actual_files = len([f for f in g.iterdir() if f.name != '.DS_Store'])
        idx_count = group_counts.get(group_name, 0)
        if actual_files != idx_count:
            print(f"  ⚠️ {group_name}: 索引={idx_count}, 实际={actual_files}")
            mismatch += 1
        else:
            print(f"  ✓ {group_name}: {idx_count}")
    
    if mismatch == 0:
        print(f"\n✅ 所有组索引与实际文件数一致！")
    else:
        print(f"\n⚠️ {mismatch} 组不匹配")
    
    # 6. 对比新旧索引
    if IDX_FILE.exists():
        old_count = 0
        with open(IDX_FILE, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            next(reader)
            old_count = sum(1 for _ in reader)
        
        print(f"\n=== 修复统计 ===")
        print(f"  旧索引记录数: {old_count}")
        print(f"  新索引记录数: {len(records)}")
        print(f"  差异: {len(records) - old_count}")


if __name__ == '__main__':
    main()
