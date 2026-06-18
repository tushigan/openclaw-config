#!/usr/bin/env python3
"""
测试 final_frame_poster 自动复用为 original 的逻辑
"""

import json
import shutil
import tempfile
from pathlib import Path
import sys

# 添加 scripts 目录到路径
scripts_dir = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))

# 直接导入模块而不是相对导入
import importlib.util
spec = importlib.util.spec_from_file_location("workflow", scripts_dir / "workflow.py")
workflow = importlib.util.module_from_spec(spec)
sys.modules["workflow"] = workflow
spec.loader.exec_module(workflow)

materialize_existing_references = workflow.materialize_existing_references
REFERENCE_FILE_MAP = workflow.REFERENCE_FILE_MAP


def test_final_frame_poster_reuse():
    """测试当提供 final_frame_poster 时，自动复用为 original"""

    with tempfile.TemporaryDirectory() as tmpdir:
        run_dir = Path(tmpdir) / "test_run"
        run_dir.mkdir()

        # 创建一个假的 final_frame_poster 图片
        test_image_dir = Path(tmpdir) / "test_images"
        test_image_dir.mkdir()
        final_poster = test_image_dir / "final_poster.png"
        final_poster.write_bytes(b"fake_png_data_final_poster")

        # 创建 brief，只提供 final_frame_poster
        brief = {
            "existing_references": {
                "final_frame_poster": str(final_poster)
            },
            "normalize_references": False  # 关闭归一化以简化测试
        }

        # 执行 materialize
        resolved = materialize_existing_references(brief, run_dir)

        # 验证结果
        assert "final_frame_poster" in resolved, "应该解析 final_frame_poster"
        assert "original" in resolved, "应该自动创建 original"

        # 验证文件存在
        final_poster_path = Path(resolved["final_frame_poster"])
        original_path = Path(resolved["original"])

        assert final_poster_path.exists(), "final_frame_poster 文件应该存在"
        assert original_path.exists(), "original 文件应该存在"

        # 验证 original 是 final_frame_poster 的副本
        assert final_poster_path.read_bytes() == original_path.read_bytes(), \
            "original 应该是 final_frame_poster 的副本"

        print("✅ 测试通过：final_frame_poster 自动复用为 original")


def test_final_frame_poster_with_identity_source():
    """测试同时提供 final_frame_poster 和 identity_source"""

    with tempfile.TemporaryDirectory() as tmpdir:
        run_dir = Path(tmpdir) / "test_run"
        run_dir.mkdir()

        # 创建假图片
        test_image_dir = Path(tmpdir) / "test_images"
        test_image_dir.mkdir()
        final_poster = test_image_dir / "final_poster.png"
        final_poster.write_bytes(b"fake_png_data_final_poster")
        identity_source = test_image_dir / "identity_source.png"
        identity_source.write_bytes(b"fake_png_data_identity_source")

        # 创建 brief
        brief = {
            "existing_references": {
                "final_frame_poster": str(final_poster),
                "identity_source": str(identity_source)
            },
            "identity_strategy": "reuse_exact",
            "normalize_references": False
        }

        # 执行 materialize
        resolved = materialize_existing_references(brief, run_dir)

        # 验证结果
        assert "final_frame_poster" in resolved
        assert "identity_source" in resolved
        assert "original" in resolved
        assert "identity_board" in resolved  # reuse_exact 应该复制 identity_source 为 identity_board

        # 验证 original 是 final_frame_poster 的副本
        original_path = Path(resolved["original"])
        assert original_path.read_bytes() == b"fake_png_data_final_poster", \
            "original 应该是 final_frame_poster 的副本"

        # 验证 identity_board 是 identity_source 的副本
        identity_board_path = Path(resolved["identity_board"])
        assert identity_board_path.read_bytes() == b"fake_png_data_identity_source", \
            "identity_board 应该是 identity_source 的副本"

        print("✅ 测试通过：同时提供 final_frame_poster 和 identity_source")


def test_no_final_frame_poster():
    """测试不提供 final_frame_poster 时，不自动创建 original"""

    with tempfile.TemporaryDirectory() as tmpdir:
        run_dir = Path(tmpdir) / "test_run"
        run_dir.mkdir()

        # 创建假图片
        test_image_dir = Path(tmpdir) / "test_images"
        test_image_dir.mkdir()
        identity_source = test_image_dir / "identity_source.png"
        identity_source.write_bytes(b"fake_png_data_identity_source")

        # 创建 brief，只提供 identity_source
        brief = {
            "existing_references": {
                "identity_source": str(identity_source)
            },
            "normalize_references": False
        }

        # 执行 materialize
        resolved = materialize_existing_references(brief, run_dir)

        # 验证结果
        assert "identity_source" in resolved
        assert "original" not in resolved, "不应该自动创建 original"

        print("✅ 测试通过：不提供 final_frame_poster 时不自动创建 original")


if __name__ == "__main__":
    test_final_frame_poster_reuse()
    test_final_frame_poster_with_identity_source()
    test_no_final_frame_poster()
    print("\n✅ 所有测试通过")
