#!/usr/bin/env python3
import pymupdf4llm
import re
import os

base = '/Users/xinban/IncepVision Law/20260603-发票分类文件完成版/IncepVision-office邮箱-2025-2026-发票凭证/凭证文件'

files_to_check = [
    '202605280414-Shipping-Fee-The Wave Team-IncepVision-$19.pdf',
    '202605180154-Credit-Note-Anthropic-IncepVision Law-$98.17.pdf',
    '202604280415-Shipping-Fee-The Wave Team-IncepVision-$19.pdf',
    '202603280416-Shipping-Fee-The Wave Team-IncepVision-$19.pdf',
    # 也检查已经确定要改的
    '202604291946-Meals-and-Entertainment-Story Coffee Tea LLC-IncepVision Law-$360.pdf',
    '202604251738-Computer-Software-Anthropic-Xiaoxiao Liu-$90.pdf',
]

for fname in files_to_check:
    path = os.path.join(base, fname)
    if not os.path.exists(path):
        print(f'=== {fname} === 文件不存在于凭证文件目录，跳过')
        print()
        continue
    
    try:
        text = pymupdf4llm.to_markdown(path)
        print(f'=== {fname} ===')
        print(f'提取字数: {len(text)}')
        
        # 找关键信息
        # 收款方关键词
        for keyword in ['Seller', 'Merchant', 'Bill From', 'Vendor', 'From:', 'From ', 'Issuer']:
            idx = text.find(keyword)
            if idx > 0 and idx < 500:
                print(f'  [{keyword}] ...{text[max(0,idx-10):idx+60]}...')
        
        # 付款方关键词
        for keyword in ['Bill To', 'Payer', 'Customer', 'Client', 'Billed To', 'Remit To']:
            idx = text.find(keyword)
            if idx > 0 and idx < 500:
                print(f'  [{keyword}] ...{text[max(0,idx-10):idx+60]}...')
        
        # 金额关键词
        for keyword in ['Total', 'Amount Due', 'Total Amount', 'Balance Due']:
            idx = text.find(keyword)
            if idx > 0:
                # 找附近100字符
                chunk = text[max(0,idx-30):idx+80]
                print(f'  [{keyword}] ...{chunk}...')
        
        # 分类关键词
        for kw in ['rent', 'Rent', 'lease', 'shipping', 'Shipping', 'software', 'Software', 'subscription', 'Credit', 'refund']:
            if kw in text:
                # 显示包含该词的1行
                lines = text.split('\n')
                for i, l in enumerate(lines):
                    if kw in l:
                        print(f'  行[{i}]: {l.strip()}')
        
        # 输出前30行完整内容
        lines = text.split('\n')
        print('  --- 前15行 ---')
        for l in lines[:15]:
            print(f'  {l}')
        print()
        
    except Exception as e:
        print(f'=== {fname} === 提取失败: {e}')
        print()
