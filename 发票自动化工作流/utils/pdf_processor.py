#!/usr/bin/env python3
"""
PDF拆分和提取工具
对每个PDF：1)拆分为单页PDF 2)提取文字 3)提取图片
按batch处理，每批输出提取结果JSON
"""

import os
import fitz  # PyMuPDF
import json
import base64

def extract_images_from_page(doc, page, img_dir):
    """提取页面中的图片"""
    images = []
    image_list = page.get_images()
    for i, img in enumerate(image_list):
        xref = img[0]
        pix = fitz.Pixmap(doc, xref)
        if pix.n - pix.alpha < 4:  # 非CMYK
            img_path = os.path.join(img_dir, f"img_page_{page.number}_{i}.png")
            pix.save(img_path)
            images.append(img_path)
        else:
            pix = fitz.Pixmap(fitz.csRGB, pix)
            img_path = os.path.join(img_dir, f"img_page_{page.number}_{i}.png")
            pix.save(img_path)
            images.append(img_path)
    return images

def process_pdf(pdf_path, output_dir):
    """处理单个PDF：拆分、提取文字和图片"""
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    
    # 创建输出子目录
    basename = os.path.splitext(os.path.basename(pdf_path))[0]
    pdf_out_dir = os.path.join(output_dir, basename)
    os.makedirs(pdf_out_dir, exist_ok=True)
    
    result = {
        "filename": os.path.basename(pdf_path),
        "total_pages": total_pages,
        "pages": []
    }
    
    # 提取全文（逐页拼接）
    full_text = ""
    for page in doc:
        full_text += page.get_text()
    result["full_text"] = full_text
    
    # 逐页处理
    for page_num in range(total_pages):
        page = doc[page_num]
        page_text = page.get_text()
        
        # 拆分为单页PDF
        new_doc = fitz.open()
        new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
        single_page_pdf = os.path.join(pdf_out_dir, f"page_{page_num + 1:03d}.pdf")
        new_doc.save(single_page_pdf)
        new_doc.close()
        
        # 提取图片
        images = extract_images_from_page(doc, page, pdf_out_dir)
        
        result["pages"].append({
            "page_number": page_num + 1,
            "text": page_text,
            "image_count": len(images),
            "image_paths": images
        })
    
    doc.close()
    return result

def process_batch(batch_name, batch_dir, results_dir):
    """处理一个batch"""
    batch_dir_full = os.path.join("/Users/xinban/IncepVision Law/20260603-发票分类文件完成版/IncepVision-office邮箱-2025-2026-发票凭证/凭证文件", batch_dir)
    
    results = []
    pdf_files = sorted([f for f in os.listdir(batch_dir_full) if f.endswith('.pdf')])
    
    print(f"\n处理 {batch_name}: {len(pdf_files)} 个PDF")
    
    for i, pdf_file in enumerate(pdf_files, 1):
        pdf_path = os.path.join(batch_dir_full, pdf_file)
        
        # 创建批次结果目录
        batch_result_dir = os.path.join(results_dir, batch_name)
        os.makedirs(batch_result_dir, exist_ok=True)
        
        result = process_pdf(pdf_path, batch_result_dir)
        results.append(result)
        
        # 打印进度
        pages = result["total_pages"]
        text_len = len(result["full_text"])
        print(f"  [{i}/{len(pdf_files)}] {pdf_file}: {pages}页, 文字{text_len}字符")
    
    # 保存批次汇总JSON
    summary_path = os.path.join(batch_result_dir, "_summary.json")
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"  ✅ {batch_name} 完成! 结果保存到: {batch_result_dir}")
    return results

def main():
    BASE = "/Users/xinban/IncepVision Law/20260603-发票分类文件完成版/IncepVision-office邮箱-2025-2026-发票凭证/凭证文件"
    results_base = os.path.join(BASE, "_提取结果")
    
    batches = ["batch_001", "batch_002", "batch_003"]
    
    for batch in batches:
        process_batch(batch, batch, results_base)

if __name__ == '__main__':
    main()
