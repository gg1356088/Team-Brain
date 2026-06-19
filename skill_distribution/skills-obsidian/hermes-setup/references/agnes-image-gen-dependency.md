# Agnes 图片生成插件：API Key 依赖分析

## 代码位置
`~/.hermes/plugins/image_gen/agnes/__init__.py`

## 核心发现

Agnes 图片生成插件通过 `_load_model_config()` 读取 API key，来源是 `config.yaml` 中的 `model.api_key` 字段，**不是**环境变量也不是 `.env` 文件。

```python
def _load_model_config() -> Dict[str, Any]:
    from hermes_cli.config import load_config
    cfg = load_config()
    model_cfg = cfg.get("model") if isinstance(cfg, dict) else None
    return model_cfg if isinstance(model_cfg, dict) else {}

def is_available(self) -> bool:
    cfg = _load_model_config()
    return bool(str(cfg.get("api_key") or "").strip())

def generate(self, prompt, aspect_ratio, **kwargs):
    cfg = _load_model_config()
    api_key = str(cfg.get("api_key") or "").strip()
    if not api_key:
        return error_response(
            error="Agnes API key not set. Run `hermes config set model.api_key <KEY>`.",
            ...
        )
```

## 为什么主模型切换会导致生图失效

1. 主模型是 `agnes-2.0-flash` 时：`model.api_key` = Agnes API key
2. 切换到 `deepseek-v4-pro` 后：`model.api_key` = DeepSeek API key（或被清空）
3. 图片生成插件读不到 Agnes key → `is_available()` 返回 False → 工具不可用

## 解决方案

```bash
# 确保 model.api_key 设置的是 Agnes 的 key
hermes config set model.api_key <YOUR_AGNES_KEY>
```

注意：这会同时影响主模型的认证（如果主模型是 agnes 的话）。但当前主模型是 deepseek，deepseek 通过 `DEEPSEEK_API_KEY` 环境变量认证，不受 `model.api_key` 影响。

## 验证方法

```python
import sys
sys.path.insert(0, '/Users/xinban/.hermes/hermes-agent')
from plugins.image_gen.agnes import AgnesImageGenProvider
p = AgnesImageGenProvider()
print('Available:', p.is_available())  # 应为 True
print('Model:', p.default_model())      # agnes-image-2.1-flash
```

## 环境变量（不可用）

以下方式**不起作用**：
- `AGNES_API_KEY` 环境变量 — 插件不读
- `~/.hermes/.env` 中的 Agnes 变量 — 插件不读
- `providers.agnes.api_key` — config 中没有这个段

唯一有效的方式：`model.api_key`。
