#!/usr/bin/env python3
"""
模型托底机制补丁脚本
在 extract_layers.py 的第 636-663 行之后插入托底逻辑
"""

import sys
from pathlib import Path

def apply_fallback_patch():
    """
    为 extract_layers.py 添加托底机制
    主模型: gpt-image-2-pro (OpenAI)
    托底模型: gemini-3.1-flash-image-preview (Gemini)
    """

    extract_layers_path = Path(__file__).parent / "extract_layers.py"

    if not extract_layers_path.exists():
        print(f"❌ 文件不存在: {extract_layers_path}")
        return False

    # 读取原文件
    content = extract_layers_path.read_text(encoding='utf-8')

    # 检查是否已经打补丁
    if "托底模型" in content or "FALLBACK" in content:
        print("✅ 托底机制已存在，无需重复打补丁")
        return True

    # 查找插入点（在主模型重试之后）
    marker = "            if attempt < attempts:\n                time.sleep(max(0.0, args.retry_delay))"

    if marker not in content:
        print("❌ 无法找到插入点，请手动添加托底机制")
        return False

    # 托底机制代码
    fallback_code = '''
        # 🔥 托底机制：主模型失败后，切换到 gemini-3.1-flash-image-preview
        if not generation_success:
            safe_log(f"⚠️  [主模型] 所有尝试均失败，启动托底机制...")
            safe_log(f"🔄 [托底模型] 切换到 gemini-3.1-flash-image-preview (Gemini 协议)")

            # 构建托底模型的环境配置
            fallback_env = env.copy()
            fallback_env["OPENCLAW_BOUND_PROTOCOL"] = "gemini"
            fallback_env["OPENCLAW_BOUND_MODEL_ID"] = "gemini-3.1-flash-image-preview"

            # Gemini 协议需要 Cloudinary URL
            fallback_source_url = source_url
            if not fallback_source_url:
                try:
                    safe_log(f"[托底模型] 上传原图到 Cloudinary...")
                    fallback_source_url = upload_to_cloudinary(source_path)
                    safe_log(f"[托底模型] ✅ 上传成功")
                except Exception as e:
                    safe_log(f"[托底模型] ⚠️ Cloudinary 上传失败，将使用 Base64: {e}")

            fallback_config = resolve_bound_gemini_config(fallback_env)
            fallback_attempts = max(1, args.api_retries)

            safe_log(f"[托底模型] 使用 {fallback_config['model']} at {fallback_config['base_url']}")

            for attempt in range(1, fallback_attempts + 1):
                if raw_out.exists():
                    raw_out.unlink()
                safe_log(f"[托底模型] API 尝试 {attempt}/{fallback_attempts}")

                res = run_bound_gemini(prompt, source_path, raw_out, fallback_env, suggested_size, source_url=fallback_source_url)

                if res.returncode == 0 and raw_out.exists():
                    generation_success = True
                    safe_log(f"✅ [托底模型] 图片生成成功: {raw_out}")
                    break

                safe_log(f"❌ [托底模型] 尝试 {attempt}/{fallback_attempts} 失败: {res.stderr[:200]}")

                if attempt < fallback_attempts:
                    time.sleep(max(0.0, args.retry_delay))
'''

    # 插入托底代码
    new_content = content.replace(marker, marker + fallback_code)

    # 备份原文件
    backup_path = extract_layers_path.with_suffix('.py.backup')
    extract_layers_path.rename(backup_path)
    print(f"✅ 原文件已备份到: {backup_path}")

    # 写入新文件
    extract_layers_path.write_text(new_content, encoding='utf-8')
    print(f"✅ 托底机制已添加到: {extract_layers_path}")

    return True


if __name__ == "__main__":
    print("========================================")
    print("模型托底机制补丁脚本")
    print("========================================")
    print("")
    print("将为 extract_layers.py 添加托底机制:")
    print("  主模型: gpt-image-2-pro (OpenAI)")
    print("  托底模型: gemini-3.1-flash-image-preview (Gemini)")
    print("")

    result = apply_fallback_patch()

    if result:
        print("")
        print("========================================")
        print("✅ 补丁应用成功！")
        print("========================================")
        print("")
        print("现在的重试逻辑:")
        print("  1. 主模型尝试 3 次")
        print("  2. 主模型失败 → 托底模型尝试 3 次")
        print("  3. 托底模型失败 → 任务失败")
        print("")
        print("最多 API 请求次数:")
        print("  每个图层: 6 次 (3 次主 + 3 次托底)")
        print("  两个图层: 12 次")
        print("")
        sys.exit(0)
    else:
        print("")
        print("========================================")
        print("❌ 补丁应用失败")
        print("========================================")
        sys.exit(1)
