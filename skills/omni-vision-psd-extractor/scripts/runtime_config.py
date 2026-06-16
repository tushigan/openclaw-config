#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
import json
import random
import urllib.request
import urllib.error
from pathlib import Path


def find_openclaw_root(start: Path | None = None) -> Path:
    current = (start or Path(__file__)).resolve()
    if current.is_file():
        current = current.parent

    for candidate in [current, *current.parents]:
        if (candidate / "openclaw.json").exists():
            return candidate

    return Path.home() / ".openclaw"


OPENCLAW_ROOT = find_openclaw_root()
WORKSPACE_DESIGN = OPENCLAW_ROOT / "workspace-design"
WORKSPACE_MAIN = OPENCLAW_ROOT / "workspace"


def _read_dotenv(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            values[key] = value
    return values


def load_runtime_env() -> dict[str, str]:
    env = os.environ.copy()
    for dotenv in [
        OPENCLAW_ROOT / ".env",
        WORKSPACE_DESIGN / ".env",
        Path(__file__).resolve().parents[1] / ".env",
    ]:
        for key, value in _read_dotenv(dotenv).items():
            env.setdefault(key, value)

    # This skill has its own model binding. Keep it local to omni and let it
    # override generic OpenClaw env values without touching global config.
    for dotenv in [
        Path(__file__).resolve().parents[2] / ".env",
        Path(__file__).resolve().parents[1] / ".env",
    ]:
        for key, value in _read_dotenv(dotenv).items():
            if key.startswith("OPENCLAW_BOUND_"):
                env[key] = value

    # 🔥 v5.2: 默认使用海报 skill 的 gpt-image2-gen（支持 failover、兼容 URL/base64、智能模型路由）
    # 如需强制使用旧的 Gemini 直连，设置环境变量 OMNI_FORCE_BOUND_GEMINI=1
    env.setdefault("OMNI_FORCE_BOUND_GEMINI", "0")

    extra_path = [
        "/opt/homebrew/bin",
        "/usr/local/bin",
        "/opt/local/bin",
        str(WORKSPACE_DESIGN / "node_modules" / ".bin"),
    ]
    env["PATH"] = os.pathsep.join([*extra_path, env.get("PATH", "")])
    env.setdefault("PYTHONIOENCODING", "utf-8")
    return env


def candidate_workspaces() -> list[Path]:
    return [WORKSPACE_DESIGN, WORKSPACE_MAIN, OPENCLAW_ROOT]


def resolve_gpt_image_generator() -> Path | None:
    relative_candidates = [
        "skills/gpt-image2-gen/scripts/generate_failover.py",
        "skills/gpt-image2-gen/scripts/generate.py",
        "PSD-SKILL/gpt-image2-gen/gpt-image2-gen/scripts/generate_failover.py",
        "PSD-SKILL/gpt-image2-gen/gpt-image2-gen/scripts/generate.py",
    ]
    for workspace in candidate_workspaces():
        for rel in relative_candidates:
            candidate = workspace / rel
            if candidate.exists():
                return candidate
    return None


def resolve_nano_banana_generator() -> Path | None:
    relative_candidates = [
        "skills/nano-banana-image-gen/scripts/generate.mjs",
        ".agents/skills/nano-banana-image-gen/scripts/generate.mjs",
    ]
    for workspace in candidate_workspaces():
        for rel in relative_candidates:
            candidate = workspace / rel
            if candidate.exists():
                return candidate
    return None


def resolve_bound_gemini_config(env: dict[str, str] | None = None) -> dict[str, str]:
    runtime_env = env or load_runtime_env()
    base_url = runtime_env.get("OPENCLAW_BOUND_BASE_URL", "https://n.lconai.com/").rstrip("/")
    model = (
        runtime_env.get("OPENCLAW_BOUND_MODEL_ID")
        or runtime_env.get("OPENCLAW_BOUND_MODEL")
        or runtime_env.get("OPENCLAW_BOUND_MODEL_NAME")
        or "gpt-image-2-pro"
    )
    api_key = runtime_env.get("OPENCLAW_BOUND_API_KEY", "")
    protocol = runtime_env.get("OPENCLAW_BOUND_PROTOCOL", "openai").lower()

    # 根据协议类型返回不同的配置
    if protocol == "openai":
        # OpenAI /v1/images/edits 格式（gpt-image-2-pro）
        return {
            "base_url": base_url,
            "model": model,
            "api_key": api_key,
            "endpoint": f"{base_url}/v1/images/edits",
            "provider": "openai",
            "protocol": "openai",
        }
    else:
        # Gemini API 格式
        return {
            "base_url": base_url,
            "model": model,
            "api_key": api_key,
            "endpoint": f"{base_url}/v1beta/models/{model}:generateContent",
            "provider": "gemini",
            "protocol": "gemini",
        }


def default_output_base() -> Path:
    return WORKSPACE_DESIGN / "outputs" / "omni-vision-psd-extractor"


# ──────────────────────────────────────────────
# Cloudinary 图床上传
# ──────────────────────────────────────────────

CLOUDINARY_URL = "https://api.cloudinary.com/v1_1/dc6kesgub/image/upload"
CLOUDINARY_PRESET = "my_n8n_upload"


def upload_to_cloudinary(file_path: Path | str) -> str:
    """
    将本地图片上传到 Cloudinary 图床，返回 secure_url。

    **v5.1 新增**：上传前自动缩放到 2K（最长边 2048px）

    参数:
        file_path: 本地图片文件路径

    返回:
        str: Cloudinary 图片 URL (https://res.cloudinary.com/...)

    异常:
        SystemExit: 上传失败时退出
    """
    file_path = Path(file_path)

    # 🔥 新增：上传前缩放到 2K
    try:
        from PIL import Image

        with Image.open(file_path) as img:
            orig_w, orig_h = img.size
            max_edge = max(orig_w, orig_h)

            # 如果超过 2048px，则缩放
            if max_edge > 2048:
                print(f"[Cloudinary] 图片尺寸 {orig_w}×{orig_h} 超过 2K，正在缩放...")

                scale = 2048 / max_edge
                new_w = int(orig_w * scale)
                new_h = int(orig_h * scale)

                # 对齐到 16 的倍数
                new_w = max(16, ((new_w + 15) // 16) * 16)
                new_h = max(16, ((new_h + 15) // 16) * 16)

                # 转换色彩模式
                if img.mode not in ('RGB', 'RGBA'):
                    img = img.convert('RGBA')

                # 缩放
                img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

                # 保存到临时文件
                import tempfile
                fd, temp_path = tempfile.mkstemp(suffix='.png', prefix='cloudinary_2k_')
                import os
                os.close(fd)

                img_resized.save(temp_path, 'PNG')
                print(f"[Cloudinary] 已缩放到 {new_w}×{new_h}，临时文件: {temp_path}")

                # 使用缩放后的文件上传
                file_path = Path(temp_path)
                should_cleanup = True
            else:
                print(f"[Cloudinary] 图片尺寸 {orig_w}×{orig_h} 已在 2K 范围内，无需缩放")
                should_cleanup = False

    except Exception as e:
        print(f"[Cloudinary] 缩放失败: {e}，将使用原图上传")
        should_cleanup = False

    # 生成随机 boundary
    boundary = '----WebKitFormBoundary' + ''.join(
        random.choice('abcdefghijklmnopqrstuvwxyz0123456789') for _ in range(16)
    )

    # 读取文件内容
    with open(file_path, 'rb') as f:
        file_content = f.read()

    filename = file_path.name
    ext = file_path.suffix.lower()
    mime_map = {
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.webp': 'image/webp',
        '.gif': 'image/gif',
    }
    file_mime = mime_map.get(ext, 'image/png')

    # 构建 multipart/form-data 请求体
    body = bytearray()

    # upload_preset 字段
    body.extend(f'--{boundary}\r\n'.encode('utf-8'))
    body.extend(b'Content-Disposition: form-data; name="upload_preset"\r\n\r\n')
    body.extend(f'{CLOUDINARY_PRESET}\r\n'.encode('utf-8'))

    # file 字段
    body.extend(f'--{boundary}\r\n'.encode('utf-8'))
    body.extend(f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.encode('utf-8'))
    body.extend(f'Content-Type: {file_mime}\r\n\r\n'.encode('utf-8'))
    body.extend(file_content)
    body.extend(b'\r\n')
    body.extend(f'--{boundary}--\r\n'.encode('utf-8'))

    # 发送请求
    req = urllib.request.Request(CLOUDINARY_URL, data=bytes(body))
    req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')

    try:
        print(f"[Cloudinary] 正在上传图片: {filename} ({len(file_content) / 1024:.1f} KB)")
        resp = urllib.request.urlopen(req, timeout=120)
        data = json.loads(resp.read().decode('utf-8'))

        url = data.get('secure_url')
        if not url:
            print(f"[错误] Cloudinary 未返回 secure_url: {data}", file=sys.stderr)
            raise RuntimeError("Cloudinary upload failed: no secure_url in response")

        print(f"[Cloudinary] 上传成功: {url}")

        # 清理临时文件
        if should_cleanup:
            try:
                file_path.unlink()
                print(f"[Cloudinary] 已清理临时文件: {file_path}")
            except Exception:
                pass

        return url

    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8', errors='replace') if hasattr(e, 'read') else ''
        print(f"[错误] Cloudinary 上传失败 HTTP {e.code}: {err_body[:500]}", file=sys.stderr)

        # 清理临时文件
        if should_cleanup:
            try:
                file_path.unlink()
            except Exception:
                pass

        raise

    except urllib.error.URLError as e:
        print(f"[错误] Cloudinary 网络请求失败: {e}", file=sys.stderr)

        # 清理临时文件
        if should_cleanup:
            try:
                file_path.unlink()
            except Exception:
                pass

        raise
