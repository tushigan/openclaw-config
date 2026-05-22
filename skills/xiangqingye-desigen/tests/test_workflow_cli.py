#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import tempfile
import unittest
from importlib import util as importlib_util
from pathlib import Path
from typing import Optional

from PIL import Image


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = SKILL_DIR / "scripts"
PYTHON = sys.executable


def run_cmd(*args: str, env: Optional[dict] = None, cwd: Optional[Path] = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [PYTHON, *args],
        cwd=str(cwd) if cwd else None,
        env=env,
        capture_output=True,
        text=True,
    )


def run_shell(script: Path, *args: str, env: Optional[dict] = None, cwd: Optional[Path] = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(script), *args],
        cwd=str(cwd) if cwd else None,
        env=env,
        capture_output=True,
        text=True,
    )


def write_png(path: Path, size: tuple[int, int], color: tuple[int, int, int] = (255, 255, 255)) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, color).save(path)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


class DetailPageWorkflowCliTests(unittest.TestCase):
    maxDiff = None

    def test_validate_dimensions_supports_documented_presets(self) -> None:
        preset = run_cmd(str(SCRIPTS_DIR / "validate_dimensions.py"), "--preset", "4k_1_1")
        self.assertEqual(preset.returncode, 0, preset.stderr)
        self.assertIn("2880x2880", preset.stdout)

        listing = run_cmd(str(SCRIPTS_DIR / "validate_dimensions.py"), "--list-presets")
        self.assertEqual(listing.returncode, 0, listing.stderr)
        self.assertIn("4k_1_1", listing.stdout)

        square = run_cmd(str(SCRIPTS_DIR / "validate_dimensions.py"), "--canvas", "square")
        self.assertEqual(square.returncode, 0, square.stderr)
        self.assertIn("2880x2880", square.stdout)

    def test_build_prompt_package_accepts_documented_confirmed_knowledge_schema(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir) / "project"
            (project_dir / "策划").mkdir(parents=True)

            write_json(
                project_dir / "facts.json",
                {
                    "brand": "测试品牌",
                    "product": "测试产品",
                    "category": "食品",
                    "sellpoints": ["酥脆"],
                },
            )
            write_json(project_dir / "platform_profile.json", {"name": "淘宝/天猫/京东移动端"})
            write_json(project_dir / "category_profile.json", {"name": "食品/烘焙/零食"})
            write_json(
                project_dir / "asset_registry.json",
                {
                    "assets": [
                        {
                            "role": "product_main",
                            "path": "参考/product.png",
                            "lock_level": "strict",
                            "usage": "商品主体",
                        }
                    ]
                },
            )
            write_json(
                project_dir / "策划" / "brand_knowledge_confirmed.json",
                {
                    "matched_dataset_name": "知识库A",
                    "confirmed_knowledge": [
                        {"title": "品牌调性", "summary": "偏法式、轻甜、克制表达"}
                    ],
                },
            )

            result = run_cmd(str(SCRIPTS_DIR / "build_prompt_package.py"), "--project-dir", str(project_dir))
            self.assertEqual(result.returncode, 0, result.stderr)

            content = (project_dir / "策划" / "prompt_package" / "wireframe_base.txt").read_text(encoding="utf-8")
            self.assertIn("品牌调性", content)
            self.assertIn("偏法式、轻甜、克制表达", content)

    def test_deliver_package_allows_headless_project_when_flagged_not_required(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir) / "project_20260515"
            (project_dir / "设计" / "v1").mkdir(parents=True)
            (project_dir / "策划").mkdir(parents=True)

            write_json(
                project_dir / "progress.json",
                {
                    "project": "测试项目",
                    "phase": "delivery_checked",
                    "workflow_flags": {"head_images_required": False},
                },
            )
            write_json(project_dir / "facts.json", {"brand": "测试品牌"})
            write_json(project_dir / "asset_registry.json", {"assets": []})
            write_json(project_dir / "platform_profile.json", {"name": "淘宝/天猫/京东移动端"})
            write_json(project_dir / "category_profile.json", {"name": "食品/烘焙/零食"})
            (project_dir / "策划" / "strategy_v1.md").write_text("# strategy\n", encoding="utf-8")
            (project_dir / "策划" / "copywriting_v1.md").write_text("# copywriting\n", encoding="utf-8")
            write_png(project_dir / "设计" / "v1" / "merged_final.png", (64, 128))
            write_png(project_dir / "设计" / "v1" / "segment_A.png", (64, 128))
            write_json(project_dir / "设计" / "v1" / "boundary_check_report.json", {"passed": True})

            validate = run_cmd(str(SCRIPTS_DIR / "validate_delivery.py"), "--project-dir", str(project_dir))
            self.assertEqual(validate.returncode, 0, validate.stderr)

            package = run_shell(SCRIPTS_DIR / "deliver_package.sh", "--project-dir", str(project_dir))
            self.assertEqual(package.returncode, 0, package.stderr)
            self.assertIn("交付.zip", package.stdout)
            self.assertTrue(any((project_dir / "交付").glob("*.zip")))

    def test_discover_brand_knowledge_resolves_existing_auto_discover_script(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            fake_auto_discover = root / "auto_discover.py"
            fake_auto_discover.write_text(
                "\n".join(
                    [
                        "#!/usr/bin/env python3",
                        "import json",
                        "print(json.dumps({'matched_dataset': {'name': 'FakeKB', 'id': 'kb-1', 'match_score': 0.8}, 'records': []}, ensure_ascii=False))",
                    ]
                ),
                encoding="utf-8",
            )
            os.chmod(fake_auto_discover, 0o755)

            spec = importlib_util.spec_from_file_location(
                "discover_brand_knowledge",
                SCRIPTS_DIR / "discover_brand_knowledge.py",
            )
            module = importlib_util.module_from_spec(spec)
            assert spec.loader is not None
            spec.loader.exec_module(module)
            module.AUTO_DISCOVER_CANDIDATES = [root / "missing.py", fake_auto_discover]

            result = module.run_query("测试品牌", "品牌文案风格", 3)
            self.assertEqual(result["query"], "测试品牌 品牌文案风格")
            self.assertEqual(result.get("matched_dataset", {}).get("name"), "FakeKB")
            self.assertNotIn("无法执行品牌知识自动检索", result.get("message", ""))

    def test_offline_smoke_flow_runs_with_fake_generator(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            fake_generator = root / "fake_generate.py"
            fake_generator.write_text(
                "\n".join(
                    [
                        "#!/usr/bin/env python3",
                        "import argparse",
                        "from pathlib import Path",
                        "from PIL import Image",
                        "ap = argparse.ArgumentParser()",
                        "ap.add_argument('--prompt-file')",
                        "ap.add_argument('--prompt')",
                        "ap.add_argument('-s', '--size', required=True)",
                        "ap.add_argument('-o', '--output', required=True)",
                        "ap.add_argument('-r', '--ref-wireframe')",
                        "ap.add_argument('--ref-style', action='append', default=[])",
                        "ap.add_argument('--ref-product')",
                        "ap.add_argument('--ref-logo')",
                        "ap.add_argument('--ref-element', action='append', default=[])",
                        "args = ap.parse_args()",
                        "w, h = [int(x) for x in args.size.split('x')]",
                        "Path(args.output).parent.mkdir(parents=True, exist_ok=True)",
                        "Image.new('RGB', (w, h), (240, 240, 240)).save(args.output)",
                        "print(args.output)",
                    ]
                ),
                encoding="utf-8",
            )
            os.chmod(fake_generator, 0o755)

            init = run_cmd(
                str(SCRIPTS_DIR / "project_manager.py"),
                "init",
                "离线闭环测试",
                "--segments",
                "A",
                "--output",
                str(root / "outputs"),
            )
            self.assertEqual(init.returncode, 0, init.stderr)

            projects = list((root / "outputs").glob("离线闭环测试_*"))
            self.assertEqual(len(projects), 1)
            project_dir = projects[0]

            profiles = run_cmd(
                str(SCRIPTS_DIR / "create_project_profiles.py"),
                "--project-dir",
                str(project_dir),
                "--platform",
                "tmall_mobile",
                "--category",
                "food_bakery",
            )
            self.assertEqual(profiles.returncode, 0, profiles.stderr)

            facts = run_cmd(
                str(SCRIPTS_DIR / "lock_product_facts.py"),
                "--output",
                str(project_dir / "facts.json"),
                "--brand",
                "测试品牌",
                "--product",
                "测试产品",
                "--category",
                "食品",
                "--structure",
                "clamped",
                "--layers",
                "3",
                "--flavors",
                "原味,可可",
                "--main-flavor",
                "原味",
                "--emboss",
                "bear_face",
                "--packaging-required",
            )
            self.assertEqual(facts.returncode, 0, facts.stderr)

            ref_dir = project_dir / "参考"
            write_png(ref_dir / "产品图_main.png", (1440, 1440))
            write_png(ref_dir / "logo.png", (400, 400))
            write_png(ref_dir / "packaging.png", (1440, 1440))
            write_json(
                ref_dir / "brand_asset_confirmed.json",
                {
                    "confirmed_assets": [
                        {"role": "product_main", "path": str(ref_dir / "产品图_main.png")},
                        {"role": "brand_logo", "path": str(ref_dir / "logo.png")},
                        {"role": "packaging", "path": str(ref_dir / "packaging.png")},
                    ]
                },
            )
            write_json(
                project_dir / "策划" / "brand_knowledge_confirmed.json",
                {
                    "matched_dataset_name": "知识库A",
                    "confirmed_knowledge": [
                        {"title": "品牌调性", "summary": "温暖、克制、食欲感"}
                    ],
                },
            )

            registry = run_cmd(str(SCRIPTS_DIR / "create_asset_registry.py"), "--project-dir", str(project_dir))
            self.assertEqual(registry.returncode, 0, registry.stderr)

            (project_dir / "策划" / "strategy_v1.md").write_text("一句话总策略：先食欲后证明。\n", encoding="utf-8")
            (project_dir / "策划" / "copywriting_v1.md").write_text(
                "所属连续段：A\n主标题：先看到好吃\n副标题：再相信靠谱\n关键信息点：酥脆、独立包装\n建议视觉内容：产品特写\n信息层级：主标题优先\n与前后屏的过渡关系：自然收口\n这屏任务：完成首屏认知\n",
                encoding="utf-8",
            )
            write_png(project_dir / "style_guide.png", (768, 768))

            prompt_package = run_cmd(str(SCRIPTS_DIR / "build_prompt_package.py"), "--project-dir", str(project_dir))
            self.assertEqual(prompt_package.returncode, 0, prompt_package.stderr)

            copy_confirm = run_cmd(
                str(SCRIPTS_DIR / "project_manager.py"),
                "set-copywriting-flag",
                "--project-dir",
                str(project_dir),
                "--confirmed",
            )
            self.assertEqual(copy_confirm.returncode, 0, copy_confirm.stderr)

            head_not_required = run_cmd(
                str(SCRIPTS_DIR / "project_manager.py"),
                "set-head-flag",
                "--project-dir",
                str(project_dir),
                "--not-required",
            )
            self.assertEqual(head_not_required.returncode, 0, head_not_required.stderr)

            head_prompts = run_cmd(str(SCRIPTS_DIR / "create_head_prompts.py"), "--project-dir", str(project_dir))
            self.assertEqual(head_prompts.returncode, 0, head_prompts.stderr)
            head_strategy = (project_dir / "策划" / "head_image_strategy_v1.md").read_text(encoding="utf-8")
            self.assertIn("1440x1440", head_strategy)

            wireframe_dir = project_dir / "手稿" / "v1"
            write_png(wireframe_dir / "wireframe_all.png", (2880, 2880))
            write_json(wireframe_dir / "wireframe_qa_report.json", {"passed": True})
            cut_dir = wireframe_dir / "cut_preview"
            write_png(cut_dir / "segment_A_confirmed.png", (1152, 3456))
            write_json(
                cut_dir / "cut_manifest.json",
                {
                    "status": "confirmed",
                    "segments": [
                        {"key": "A", "confirmed_file": "segment_A_confirmed.png", "source": "manual"}
                    ],
                },
            )

            phase_wireframe = run_cmd(
                str(SCRIPTS_DIR / "project_manager.py"),
                "update-phase",
                "--project-dir",
                str(project_dir),
                "wireframe_cut_approved",
            )
            self.assertEqual(phase_wireframe.returncode, 0, phase_wireframe.stderr)

            design_prompts = run_cmd(
                str(SCRIPTS_DIR / "create_design_segment_prompts.py"),
                "--project-dir",
                str(project_dir),
                "--version",
                "v1",
            )
            self.assertEqual(design_prompts.returncode, 0, design_prompts.stderr)

            env = os.environ.copy()
            env["DETAIL_PAGE_GEN_SCRIPT"] = str(fake_generator)
            generate_segments = run_shell(
                SCRIPTS_DIR / "generate_segment_batch.sh",
                "--project-dir",
                str(project_dir),
                "--version",
                "v1",
                "--size",
                "1152x3456",
                env=env,
            )
            self.assertEqual(generate_segments.returncode, 0, generate_segments.stderr)

            generate_heads = run_shell(
                SCRIPTS_DIR / "generate_head_images.sh",
                str(project_dir),
                "v1",
                env=env,
            )
            self.assertEqual(generate_heads.returncode, 0, generate_heads.stderr)

            write_json(project_dir / "设计" / "v1" / "boundary_check_report.json", {"passed": True})
            write_png(project_dir / "设计" / "v1" / "merged_final.png", (1152, 3456))

            validate = run_cmd(str(SCRIPTS_DIR / "validate_delivery.py"), "--project-dir", str(project_dir))
            self.assertEqual(validate.returncode, 0, validate.stderr)

            package = run_shell(SCRIPTS_DIR / "deliver_package.sh", "--project-dir", str(project_dir))
            self.assertEqual(package.returncode, 0, package.stderr)


if __name__ == "__main__":
    unittest.main()
