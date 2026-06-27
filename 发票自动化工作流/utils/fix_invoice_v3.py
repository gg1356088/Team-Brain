#!/usr/bin/env python3
"""
发票凭证整理 - 带纠错规则
纠正: Shipping Fee(邮寄费)误标为Professional-Fees/Computer-Software
排除: 个人费用(Filoli) + 发出去的发票(WUKONG)
分批: 20个一批
"""

import os
import re

BASE = "/Users/xinban/IncepVision Law/20260603-发票分类文件完成版/IncepVision-office邮箱-2025-2026-发票凭证"
VOUCHER_DIR = os.path.join(BASE, "凭证文件")

def clean_filename(original_name, new_category, new_payee, new_payer, amount=None):
    """生成正确的新文件名"""
    # 金额从原始文件名提取
    if amount is None:
        match = re.search(r'\$[\d,]+\.?\d*', original_name)
        amount = match.group(0).replace(',', '').rstrip('.')
    
    # 日期时间戳是12位: YYYYMMDDHHMM
    dt = original_name[:12]
    
    # 分类: 空格变短横
    category = new_category.replace(' ', '-')
    
    return f"{dt}-{category}-{new_payee}-{new_payer}-{amount}.pdf"

def main():
    files = sorted([f for f in os.listdir(VOUCHER_DIR) if f.endswith('.pdf')])
    
    corrections = {}
    
    # Shipping Fee - The Wave Team ($19) -> 是邮寄费，不是Computer-Software
    for dt in ['202605280414', '202604280415', '202603280416']:
        corrections[f"{dt}-Computer-Software-The Wave Team-IncepVision-$19.pdf"] = {
            'category': 'Shipping-Fee', 'payee': 'The Wave Team', 'payer': 'IncepVision',
        }
    
    # Shipping Fee - LSCO Holding LLC -> 是邮寄费，不是Professional-Fees
    corrections['202605090303-Professional-Fees-LSCO Holding LLC-IncepVision-$90.43.pdf'] = {
        'category': 'Shipping-Fee', 'payee': 'LSCO Holding LLC', 'payer': 'IncepVision',
    }
    corrections['202604221630-Professional-Fees-LSCO Holding LLC-IncepVision-$95.63.pdf'] = {
        'category': 'Shipping-Fee', 'payee': 'LSCO Holding LLC', 'payer': 'IncepVision',
    }
    corrections['202604220341-Professional-Fees-LSCO Holding LLC-IncepVision-$102.39.pdf'] = {
        'category': 'Shipping-Fee', 'payee': 'LSCO Holding LLC', 'payer': 'IncepVision',
    }
    corrections['202605140511-Professional-Fees-LSCO Holding LLC-IncepVision-$97.19.pdf'] = {
        'category': 'Shipping-Fee', 'payee': 'LSCO Holding LLC', 'payer': 'IncepVision',
    }
    
    # 排除 - 个人费用
    corrections['202605100000-Meals-and-Entertainment-Filoli-Xiaoxiao Liu-$186.pdf'] = {
        'action': 'exclude', 'reason': '个人费用，不进企业凭证',
    }
    
    # 排除 - 我们发出去的发票
    corrections['202512231603-Agent-Fee-WUKONG International Hong Kong-IncepVision Law-$150.pdf'] = {
        'action': 'exclude', 'reason': '我们发出去的发票，不收录',
    }
    
    included = []
    excluded = []
    corrected = []
    
    for f in files:
        if f in corrections:
            rule = corrections[f]
            if rule.get('action') == 'exclude':
                excluded.append((f, rule['reason']))
            else:
                new_name = clean_filename(f, rule['category'], rule['payee'], rule['payer'])
                if f != new_name:
                    corrected.append((f, new_name, rule['category']))
                included.append(new_name)
        else:
            included.append(f)
    
    print("=" * 70)
    print("纠正结果汇总")
    print("=" * 70)
    print(f"总文件数: {len(files)}")
    print(f"纳入企业凭证: {len(included)}")
    print(f"排除: {len(excluded)}")
    print(f"修正命名: {len(corrected)}")
    
    print("\n--- 排除的文件 ---")
    for f, reason in excluded:
        print(f"  ❌ {f}")
        print(f"     原因: {reason}")
    
    print("\n--- 修正命名的文件 ---")
    for old, new, cat in corrected:
        print(f"  {old}")
        print(f"    → {new}")
    
    print(f"\n--- 纳入的企业凭证 ({len(included)}) ---")
    for f in included:
        print(f"  ✓ {f}")
    
    batches = []
    for i in range(0, len(included), 20):
        batches.append(included[i:i+20])
    
    print(f"\n--- 分批结果 ---")
    for i, batch in enumerate(batches, 1):
        print(f"\nbatch_{i:03d}: {len(batch)} 个文件")
        for f in batch:
            print(f"    {f}")
    
    return included, excluded, corrected, batches

if __name__ == '__main__':
    included, excluded, corrected, batches = main()
