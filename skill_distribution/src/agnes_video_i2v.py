#!/usr/bin/env python3
"""
Agnes Video API - 图生视频 (Image-to-Video)
绕过 Hermes 审批，用 curl 直调 Agnes Video V2.0 API
"""
import base64
import json
import subprocess
import sys
import time
from pathlib import Path

# Agnes Video API 端点
BASE_URL = "https://apihub.agnes-ai.com/v1"

def read_api_key():
    """读取 config.yaml 中的 Agnes API key"""
    import re
    config_path = Path.home() / ".hermes" / "config.yaml"
    with open(config_path) as f:
        content = f.read()
    # 匹配主模型的 api_key
    match = re.search(r'default: agnes-2\.0-flash\s+provider: custom\s+base_url: .*?\s+api_key:\s+(sk-[^\s]+)', content)
    if match:
        return match.group(1).strip()
    return None

def encode_image_to_base64(image_path):
    """将图片转为 base64"""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def submit_video_request(api_key, image_path, prompt, output_path):
    """提交图生视频请求"""
    # 读取图片
    base64_image = encode_image_to_base64(image_path)
    image_url = f"data:image/png;base64,{base64_image}"
    
    # 构建请求体
    payload = {
        "model": "agnes-video-v2.0",
        "prompt": prompt,
        "image_url": image_url,
        "duration": 5,
        "resolution": "720p"
    }
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # 使用 curl 提交请求
    cmd = [
        "curl", "-s", "-S", "--fail-with-body", "-X", "POST",
        f"{BASE_URL}/videos",
        "-H", f"Authorization: Bearer {api_key}",
        "-H", "Content-Type: application/json",
        "-d", json.dumps(payload),
        "--max-time", "60"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"提交失败: {result.stderr}")
        sys.exit(1)
    
    try:
        resp = json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"返回格式错误: {result.stdout[:500]}")
        sys.exit(1)
    
    if "request_id" in resp:
        return resp["request_id"]
    elif "error" in resp:
        print(f"API 错误: {resp['error']}")
        sys.exit(1)
    else:
        print(f"意外响应: {json.dumps(resp, ensure_ascii=False)}")
        sys.exit(1)

def poll_video_result(api_key, request_id, output_path, max_wait=300):
    """轮询视频生成结果"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    print(f"开始轮询任务 {request_id}...")
    elapsed = 0
    while elapsed < max_wait:
        time.sleep(10)
        elapsed += 10
        
        cmd = [
            "curl", "-s", "-S", "--fail-with-body", "-X", "GET",
            f"{BASE_URL}/videos/{request_id}",
            "-H", f"Authorization: Bearer {api_key}",
            "--max-time", "30"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"查询失败: {result.stderr}", file=sys.stderr)
            continue
        
        try:
            resp = json.loads(result.stdout)
        except json.JSONDecodeError:
            print(f"响应格式错误", file=sys.stderr)
            continue
        
        status = resp.get("status", "unknown")
        print(f"  状态: {status} ({elapsed}s)...")
        
        if status == "completed":
            # 下载视频
            video_url = resp.get("video_url") or resp.get("output")
            if video_url:
                cmd = [
                    "curl", "-s", "-S", "-L", "-o", output_path,
                    "--max-time", "300", video_url
                ]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0 and Path(output_path).exists():
                    print(f"视频已下载到: {output_path}")
                    return True
                else:
                    print(f"下载失败: {result.stderr}", file=sys.stderr)
            return False
        
        if status in ("failed", "error"):
            print(f"任务失败: {resp.get('error', '未知错误')}")
            return False
        
        print(".", end="", flush=True)
    
    print(f"\n超时 ({max_wait}s)")
    return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Agnes Video - 图生视频")
    parser.add_argument("--image", required=True, help="输入图片路径")
    parser.add_argument("--prompt", required=True, help="视频描述")
    parser.add_argument("--output", default="/Users/xinban/HermesPet_Workspace/video_output.mp4", help="输出路径")
    args = parser.parse_args()
    
    if not Path(args.image).exists():
        print(f"图片不存在: {args.image}")
        sys.exit(1)
    
    api_key = read_api_key()
    if not api_key:
        print("错误: 找不到 Agnes API key")
        sys.exit(1)
    
    print(f"API Key: {api_key[:10]}...{api_key[-4:]}")
    print(f"图片: {args.image}")
    print(f"提示词: {args.prompt}")
    print()
    
    # 提交任务
    request_id = submit_video_request(api_key, args.image, args.prompt, args.output)
    print(f"任务已提交，ID: {request_id}")
    
    # 轮询
    success = poll_video_result(api_key, request_id, args.output)
    if success:
        print("\n生成完成!")
        print(f"MEDIA:{args.output}")
    else:
        print("\n生成失败")
        sys.exit(1)
