#!/usr/bin/env python3
"""
统一配置模块 — 供 loop_dispatch.py 和 loop_monitor.py 共用

配置优先级（从高到低）：
  1. CLI 参数（cli_overrides）
  2. 环境变量（HERMES_SKILLS_WORKSPACE 等）
  3. config.json（workspace 目录下）
  4. .env 文件（workspace 目录下）
  5. 默认值
"""

import json
import os
from pathlib import Path


def _load_env_file(env_path):
    """加载 .env 文件，返回键值对字典。"""
    env_vars = {}
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, val = line.split("=", 1)
                    env_vars[key.strip()] = val.strip()
    return env_vars


def load_config(cli_overrides=None):
    """加载完整配置。
    
    Args:
        cli_overrides: dict，来自 CLI 参数的覆盖值（优先级最高）
    
    Returns:
        dict 包含所有配置项
    """
    cli_overrides = cli_overrides or {}
    
    # 默认值
    defaults = {
        "workspace": str(Path.home() / "HermesWorkspaces"),
        "feishu_chat_id": "",
        "claude_cmd": "claude",
        "codex_cmd": "/Applications/Codex.app/Contents/Resources/codex",
    }
    
    # 1. 从环境变量读取基础值（用于确定 workspace 路径）
    workspace = os.environ.get("HERMES_SKILLS_WORKSPACE", defaults["workspace"])
    
    # 2. 从 .env 文件读取
    env_path = Path(workspace) / ".env"
    env_file = _load_env_file(env_path)
    
    # 3. 从 config.json 读取
    config_json_path = Path(workspace) / "config.json"
    cfg = {}
    if config_json_path.exists():
        with open(config_json_path) as f:
            cfg = json.load(f)
    
    # 4. 组装最终值，按优先级叠加
    env = {
        "workspace": workspace,
        "feishu_chat_id": os.environ.get("FEISHU_CHAT_ID", 
                  env_file.get("FEISHU_CHAT_ID",
                  cfg.get("feishu", {}).get("chat_id", ""))),
        "claude_cmd": os.environ.get("CLAUDE_CMD",
                  env_file.get("CLAUDE_CMD",
                  cfg.get("workers", {}).get("claude_cmd", defaults["claude_cmd"]))),
        "codex_cmd": os.environ.get("CODEX_CMD",
                  env_file.get("CODEX_CMD",
                  cfg.get("workers", {}).get("codex_cmd", defaults["codex_cmd"]))),
    }
    
    # 5. CLI 参数覆盖（最高优先级）
    for key in defaults:
        if key in cli_overrides and cli_overrides[key]:
            env[key] = cli_overrides[key]
    
    return env
