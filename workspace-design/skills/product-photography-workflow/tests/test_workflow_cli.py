#!/usr/bin/env python3
from __future__ import annotations

import base64
import json
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = SKILL_DIR / "scripts"
PYTHON = sys.executable

TINY_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO8B9x8AAAAASUVORK5CYII="
)


def run_cmd(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [PYTHON, *args],
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
    )


def write_png(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(TINY_PNG)


def write_fake_generator(path: Path) -> None:
    path.write_text(
        textwrap.dedent(
            """\
            #!/usr/bin/env python3
            import argparse
            import base64
            from pathlib import Path

            PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO8B9x8AAAAASUVORK5CYII=")

            parser = argparse.ArgumentParser()
            parser.add_argument("--prompt-file")
            parser.add_argument("--size", required=True)
            parser.add_argument("--output", required=True)
            parser.add_argument("--model", default="")
            parser.add_argument("--count", type=int, default=1)
            parser.add_argument("--reference", action="append", default=[])
            parser.add_argument("--ref-base", action="append", default=[])
            parser.add_argument("--ref-product", action="append", default=[])
            parser.add_argument("--ref-layout", action="append", default=[])
            parser.add_argument("--ref-style", action="append", default=[])
            parser.add_argument("--ref-background", action="append", default=[])
            args = parser.parse_args()

            output = Path(args.output)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(PNG)
            print(output)
            """
        ),
        encoding="utf-8",
    )
    path.chmod(0o755)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_kv(stdout: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in stdout.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        result[key.strip()] = value.strip()
    return result


class ProductPhotographyWorkflowCliTests(unittest.TestCase):
    maxDiff = None

    def init_project(self, output_root: Path, name: str = "毛毛虫面包项目") -> Path:
        init = run_cmd(
            str(SCRIPTS_DIR / "init_project.py"),
            name,
            "--output-root",
            str(output_root),
        )
        self.assertEqual(init.returncode, 0, init.stderr)
        init_data = parse_kv(init.stdout)
        project_dir = Path(init_data["project_dir"])
        self.assertTrue(project_dir.exists())
        return project_dir

    def register_base_assets(self, project_dir: Path, asset_root: Path) -> None:
        front = asset_root / "front.png"
        side = asset_root / "side.png"
        cut = asset_root / "cut.png"
        style = asset_root / "style.png"
        for item in [front, side, cut, style]:
            write_png(item)

        result = run_cmd(
            str(SCRIPTS_DIR / "register_assets.py"),
            "--project-dir",
            str(project_dir),
            "--no-copy-assets",
            "--product-front",
            str(front),
            "--product-side",
            str(side),
            "--product-cross-section",
            str(cut),
            "--reference-style",
            str(style),
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def build_base_product_profile(self, project_dir: Path) -> None:
        result = run_cmd(
            str(SCRIPTS_DIR / "build_product_profile.py"),
            "--project-dir",
            str(project_dir),
            "--product-name",
            "毛毛虫面包",
            "--brand-name",
            "测试品牌",
            "--category",
            "烘焙",
            "--outer-shape",
            "长条软面包，顶部奶油波纹",
            "--structure-type",
            "filled",
            "--cross-section-required",
            "yes",
            "--cross-section-state",
            "掰开后可见白色奶油夹心",
            "--filling-type",
            "奶油夹心",
            "--filling-texture",
            "厚实顺滑",
            "--shell-texture",
            "松软烘焙表皮",
            "--must-show-detail",
            "整根形态",
            "--must-show-detail",
            "掰开后夹心质地",
            "--must-not-fake-detail",
            "不要把奶油画成果酱流心",
            "--deformation-rule",
            "不能画成蛋糕卷",
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def create_task_with_assets(
        self,
        project_dir: Path,
        asset_root: Path,
        task_name: str = "详情页首图摆拍",
        *,
        extra_layout_refs: int = 0,
        extra_storyboard_refs: int = 0,
        include_task_style_refs: bool = False,
        include_storyboard_refs: bool = False,
        include_texture_refs: bool = False,
        include_package_material_refs: bool = False,
    ) -> tuple[str, Path]:
        create = run_cmd(
            str(SCRIPTS_DIR / "create_task.py"),
            "--project-dir",
            str(project_dir),
            "--task-name",
            task_name,
            "--task-type",
            "product_display",
            "--output-ratio",
            "3:4",
            "--goal",
            "生成详情页使用的摆拍主图",
            "--tag",
            "detail-page",
        )
        self.assertEqual(create.returncode, 0, create.stderr)
        task_data = parse_kv(create.stdout)
        task_id = task_data["task_id"]
        task_dir = Path(task_data["task_dir"])

        page_draft = asset_root / f"{task_id}_page.png"
        comp = asset_root / f"{task_id}_comp.png"
        scene = asset_root / f"{task_id}_scene.png"
        product_state = asset_root / f"{task_id}_state.png"
        other = asset_root / f"{task_id}_other.png"
        extra_comps = [asset_root / f"{task_id}_comp_extra_{idx + 1}.png" for idx in range(extra_layout_refs)]
        storyboard = asset_root / f"{task_id}_storyboard.png"
        extra_storyboards = [asset_root / f"{task_id}_storyboard_extra_{idx + 1}.png" for idx in range(extra_storyboard_refs)]
        task_style = asset_root / f"{task_id}_style.png"
        task_lighting = asset_root / f"{task_id}_lighting.png"
        texture = asset_root / f"{task_id}_texture.png"
        package_material = asset_root / f"{task_id}_package_material.png"
        items = [page_draft, comp, scene, product_state, other, *extra_comps]
        if include_storyboard_refs:
            items.extend([storyboard, *extra_storyboards])
        if include_task_style_refs:
            items.extend([task_style, task_lighting])
        if include_texture_refs:
            items.append(texture)
        if include_package_material_refs:
            items.append(package_material)
        for item in items:
            write_png(item)

        register_args = [
            str(SCRIPTS_DIR / "register_task_assets.py"),
            "--project-dir",
            str(project_dir),
            "--task-id",
            task_id,
            "--no-copy-assets",
            "--page-draft",
            str(page_draft),
            "--composition-reference",
            str(comp),
            "--scene-reference",
            str(scene),
            "--product-state-reference",
            str(product_state),
            "--other-reference",
            str(other),
        ]
        for extra in extra_comps:
            register_args.extend(["--composition-reference", str(extra)])
        if include_storyboard_refs:
            register_args.extend(["--camera-storyboard-reference", str(storyboard)])
            for extra in extra_storyboards:
                register_args.extend(["--camera-storyboard-reference", str(extra)])
        if include_task_style_refs:
            register_args.extend(
                [
                    "--style-reference",
                    str(task_style),
                    "--lighting-reference",
                    str(task_lighting),
                ]
            )
        if include_texture_refs:
            register_args.extend(
                [
                    "--texture-identity-reference",
                    str(texture),
                ]
            )
        if include_package_material_refs:
            register_args.extend(
                [
                    "--package-material-reference",
                    str(package_material),
                ]
            )

        register = run_cmd(*register_args)
        self.assertEqual(register.returncode, 0, register.stderr)
        return task_id, task_dir

    def confirm_camera_preview(self, project_dir: Path, task_id: str, task_dir: Path, fake_generator: Path) -> Path:
        preview_prompt = run_cmd(
            str(SCRIPTS_DIR / "build_camera_preview_prompt.py"),
            "--project-dir",
            str(project_dir),
            "--task-id",
            task_id,
        )
        self.assertEqual(preview_prompt.returncode, 0, preview_prompt.stderr)

        preview_generate = run_cmd(
            str(SCRIPTS_DIR / "run_camera_preview.py"),
            "--project-dir",
            str(project_dir),
            "--task-id",
            task_id,
            "--gpt-image2-script",
            str(fake_generator),
        )
        self.assertEqual(preview_generate.returncode, 0, preview_generate.stderr)

        preview_path = task_dir / "previews" / "CP001" / "preview.png"
        confirm_preview = run_cmd(
            str(SCRIPTS_DIR / "record_confirmation.py"),
            "--project-dir",
            str(project_dir),
            "--task-id",
            task_id,
            "--kind",
            "task_camera_preview",
            "--decision",
            "approve",
            "--note",
            "机位确认通过",
            "--selected-output",
            str(preview_path),
        )
        self.assertEqual(confirm_preview.returncode, 0, confirm_preview.stderr)
        return preview_path

    def test_resume_context_finds_existing_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            project_dir = self.init_project(root / "outputs")
            self.register_base_assets(project_dir, root / "assets")
            self.build_base_product_profile(project_dir)

            result = run_cmd(
                str(SCRIPTS_DIR / "resume_project_context.py"),
                "--query",
                "毛毛虫面包",
                "--output-root",
                str(root / "outputs"),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            data = parse_kv(result.stdout)
            self.assertEqual(data["status"], "matched")
            self.assertEqual(Path(data["project_dir"]), project_dir)
            self.assertEqual(data["product_name"], "毛毛虫面包")

    def test_task_brief_confirmation_builds_task_prompt_and_generation_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            project_dir = self.init_project(root / "outputs")
            self.register_base_assets(project_dir, root / "assets")
            self.build_base_product_profile(project_dir)
            task_id, task_dir = self.create_task_with_assets(project_dir, root / "task-assets")

            brief = run_cmd(
                str(SCRIPTS_DIR / "build_task_brief.py"),
                "--project-dir",
                str(project_dir),
                "--task-id",
                task_id,
                "--task-goal",
                "做一张用于详情页的竖版产品摆拍图",
                "--output-ratio",
                "3:4",
                "--output-kind",
                "detail_page_hero",
                "--page-draft-note",
                "沿用长图草稿里主体居中、上下留白的版式",
                "--composition-note",
                "整根与掰开两半同框，主体偏中上",
                "--scene-note",
                "干净暖色台面，商业食品摄影",
                "--product-state-note",
                "需要同时体现整根与切面夹心",
                "--placement-note",
                "左侧主产品，右下角切面，预留标题位",
                "--must-show",
                "整根形态",
                "--must-show",
                "掰开后的奶油夹心质地",
                "--must-avoid",
                "不要人物",
                "--must-avoid",
                "不要餐盘",
            )
            self.assertEqual(brief.returncode, 0, brief.stderr)

            confirm = run_cmd(
                str(SCRIPTS_DIR / "record_confirmation.py"),
                "--project-dir",
                str(project_dir),
                "--task-id",
                task_id,
                "--kind",
                "task_brief",
                "--decision",
                "approve",
                "--note",
                "任务简报确认，可以进入生图",
            )
            self.assertEqual(confirm.returncode, 0, confirm.stderr)

            fake_generator = root / "fake_generate.py"
            write_fake_generator(fake_generator)
            self.confirm_camera_preview(project_dir, task_id, task_dir, fake_generator)

            prompt = run_cmd(
                str(SCRIPTS_DIR / "build_generation_prompt.py"),
                "--project-dir",
                str(project_dir),
                "--task-id",
                task_id,
                "--custom-constraint",
                "不要文字",
            )
            self.assertEqual(prompt.returncode, 0, prompt.stderr)
            prompt_data = parse_kv(prompt.stdout)
            prompt_path = Path(prompt_data["prompt_file"])
            self.assertTrue(prompt_path.exists())
            self.assertEqual(prompt_path.parent, task_dir / "prompts")
            self.assertIn("V001", prompt_path.name)

            prompt_text = prompt_path.read_text(encoding="utf-8")
            self.assertIn("整根形态", prompt_text)
            self.assertIn("掰开后的奶油夹心质地", prompt_text)
            self.assertIn("不要文字", prompt_text)
            self.assertIn("page draft", prompt_text.lower())
            self.assertIn("scene reference", prompt_text.lower())

            task_state = read_json(task_dir / "task_state.json")
            self.assertTrue(task_state["workflow_flags"]["brief_confirmed"])
            self.assertTrue(task_state["workflow_flags"]["generation_allowed"])
            self.assertEqual(task_state["current_stage"], "task_prompt_ready")

            task_brief = read_json(task_dir / "task_brief.json")
            self.assertEqual(task_brief["status"], "confirmed")
            self.assertEqual(task_brief["confirmation"]["decision"], "approve")
            self.assertTrue(task_brief["planning_warnings"])
            self.assertTrue(any("camera_plan" in item for item in task_brief["planning_warnings"]))
            self.assertTrue(any("texture_plan" in item for item in task_brief["planning_warnings"]))
            self.assertIn("Planning warnings", prompt_text)

    def test_task_brief_warns_when_package_material_plan_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            project_dir = self.init_project(root / "outputs")
            self.register_base_assets(project_dir, root / "assets")
            self.build_base_product_profile(project_dir)
            task_id, task_dir = self.create_task_with_assets(
                project_dir,
                root / "task-assets",
                task_name="包装主图白底",
                include_package_material_refs=True,
            )

            brief = run_cmd(
                str(SCRIPTS_DIR / "build_task_brief.py"),
                "--project-dir",
                str(project_dir),
                "--task-id",
                task_id,
                "--task-goal",
                "做一张白底包装主图，重点锁定包材膜感",
                "--output-ratio",
                "1:1",
                "--output-kind",
                "main_image",
                "--composition-note",
                "主体居中，单包完整",
                "--scene-note",
                "纯白背景包装产品图",
                "--product-state-note",
                "包装正面平躺，封边自然",
                "--placement-note",
                "四周均匀留白",
                "--must-show",
                "包装正面完整",
                "--must-avoid",
                "不要出现第二包",
            )
            self.assertEqual(brief.returncode, 0, brief.stderr)

            brief_data = read_json(task_dir / "task_brief.json")
            self.assertEqual(len(brief_data["reference_paths"]["package_material_reference"]), 1)
            self.assertTrue(any("package_material_plan" in item for item in brief_data["planning_warnings"]))

    def test_task_generation_review_and_revision_keep_versions(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            project_dir = self.init_project(root / "outputs")
            self.register_base_assets(project_dir, root / "assets")
            self.build_base_product_profile(project_dir)
            task_id, task_dir = self.create_task_with_assets(project_dir, root / "task-assets")

            brief = run_cmd(
                str(SCRIPTS_DIR / "build_task_brief.py"),
                "--project-dir",
                str(project_dir),
                "--task-id",
                task_id,
                "--task-goal",
                "详情页长图里的产品摆拍图",
                "--output-ratio",
                "3:4",
                "--output-kind",
                "detail_page_support",
                "--composition-note",
                "整根和切面同框",
                "--scene-note",
                "暖调柔光，白底或浅暖台面",
                "--must-show",
                "夹心切面",
                "--must-avoid",
                "不要人物",
            )
            self.assertEqual(brief.returncode, 0, brief.stderr)

            confirm_brief = run_cmd(
                str(SCRIPTS_DIR / "record_confirmation.py"),
                "--project-dir",
                str(project_dir),
                "--task-id",
                task_id,
                "--kind",
                "task_brief",
                "--decision",
                "approve",
                "--note",
                "进入生图",
            )
            self.assertEqual(confirm_brief.returncode, 0, confirm_brief.stderr)

            fake_generator = root / "fake_generate.py"
            write_fake_generator(fake_generator)
            self.confirm_camera_preview(project_dir, task_id, task_dir, fake_generator)

            prompt = run_cmd(
                str(SCRIPTS_DIR / "build_generation_prompt.py"),
                "--project-dir",
                str(project_dir),
                "--task-id",
                task_id,
            )
            self.assertEqual(prompt.returncode, 0, prompt.stderr)
            generate = run_cmd(
                str(SCRIPTS_DIR / "run_generation.py"),
                "--project-dir",
                str(project_dir),
                "--task-id",
                task_id,
                "--gpt-image2-script",
                str(fake_generator),
                "--count",
                "1",
            )
            self.assertEqual(generate.returncode, 0, generate.stderr)

            generation = read_json(task_dir / "generation_manifest.json")
            self.assertEqual(generation["latest_status"], "succeeded")
            self.assertEqual(generation["latest_version_id"], "V001")
            self.assertEqual(generation["versions"][-1]["version_id"], "V001")
            self.assertEqual(generation["versions"][-1]["status"], "succeeded")
            self.assertTrue((task_dir / "versions" / "V001" / "generated.png").exists())

            review = run_cmd(
                str(SCRIPTS_DIR / "record_confirmation.py"),
                "--project-dir",
                str(project_dir),
                "--task-id",
                task_id,
                "--kind",
                "task_generation_review",
                "--decision",
                "revise",
                "--note",
                "切面位置还需要再明确一点",
                "--selected-output",
                str(task_dir / "versions" / "V001" / "generated.png"),
            )
            self.assertEqual(review.returncode, 0, review.stderr)

            reviewed_generation = read_json(task_dir / "generation_manifest.json")
            self.assertEqual(reviewed_generation["latest_status"], "revision_requested")
            self.assertEqual(reviewed_generation["review"]["decision"], "revise")

            revise = run_cmd(
                str(SCRIPTS_DIR / "revise_task.py"),
                "--project-dir",
                str(project_dir),
                "--task-id",
                task_id,
                "--note",
                "增加切面展示权重",
            )
            self.assertEqual(revise.returncode, 0, revise.stderr)

            revised_task_state = read_json(task_dir / "task_state.json")
            revised_generation = read_json(task_dir / "generation_manifest.json")
            tasks_manifest = read_json(project_dir / "tasks_manifest.json")

            self.assertEqual(revised_task_state["selected_version_id"], "V002")
            self.assertEqual(revised_generation["latest_version_id"], "V002")
            self.assertEqual(revised_generation["versions"][-1]["version_id"], "V002")
            self.assertEqual(revised_generation["versions"][-1]["status"], "draft")
            self.assertTrue((task_dir / "versions" / "V002").exists())
            self.assertEqual(tasks_manifest["summary"]["task_count"], 1)
            self.assertEqual(tasks_manifest["summary"]["revision_count"], 1)
            self.assertEqual(tasks_manifest["tasks"][0]["version_count"], 2)

    def test_multi_reference_authority_routes_layout_and_style_separately(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            project_dir = self.init_project(root / "outputs")
            self.register_base_assets(project_dir, root / "assets")
            self.build_base_product_profile(project_dir)
            task_id, task_dir = self.create_task_with_assets(
                project_dir,
                root / "task-assets",
                extra_layout_refs=1,
                include_task_style_refs=True,
            )

            brief = run_cmd(
                str(SCRIPTS_DIR / "build_task_brief.py"),
                "--project-dir",
                str(project_dir),
                "--task-id",
                task_id,
                "--task-goal",
                "用一个布局参考和一个光影参考生成详情页头图",
                "--output-ratio",
                "9:16",
                "--output-kind",
                "detail_page_hero",
                "--composition-note",
                "布局严格跟主布局参考",
                "--scene-note",
                "氛围借场景和风格参考",
                "--product-state-note",
                "顶部产品破口露馅，底部完整",
                "--must-show",
                "上下双产品摆位跟主布局参考",
                "--must-avoid",
                "不要把风格参考里的主体搬过来",
            )
            self.assertEqual(brief.returncode, 0, brief.stderr)

            brief_data = read_json(task_dir / "task_brief.json")
            self.assertEqual(len(brief_data["reference_paths"]["composition_reference"]), 2)
            self.assertEqual(len(brief_data["reference_paths"]["style_reference"]), 1)
            self.assertEqual(len(brief_data["reference_paths"]["lighting_reference"]), 1)

            confirm = run_cmd(
                str(SCRIPTS_DIR / "record_confirmation.py"),
                "--project-dir",
                str(project_dir),
                "--task-id",
                task_id,
                "--kind",
                "task_brief",
                "--decision",
                "approve",
                "--note",
                "多参考职责确认，可以进入生图",
            )
            self.assertEqual(confirm.returncode, 0, confirm.stderr)

            fake_generator = root / "fake_generate.py"
            write_fake_generator(fake_generator)
            self.confirm_camera_preview(project_dir, task_id, task_dir, fake_generator)

            prompt = run_cmd(
                str(SCRIPTS_DIR / "build_generation_prompt.py"),
                "--project-dir",
                str(project_dir),
                "--task-id",
                task_id,
            )
            self.assertEqual(prompt.returncode, 0, prompt.stderr)
            prompt_path = Path(parse_kv(prompt.stdout)["prompt_file"])
            prompt_text = prompt_path.read_text(encoding="utf-8")
            self.assertIn("Reference authority resolution", prompt_text)
            self.assertIn("Layout authority", prompt_text)
            self.assertIn("Style and lighting authority", prompt_text)

            generate = run_cmd(
                str(SCRIPTS_DIR / "run_generation.py"),
                "--project-dir",
                str(project_dir),
                "--task-id",
                task_id,
                "--gpt-image2-script",
                str(fake_generator),
            )
            self.assertEqual(generate.returncode, 0, generate.stderr)

            generation = read_json(task_dir / "generation_manifest.json")
            version = generation["versions"][-1]
            command_summary = version["command_summary"]

            self.assertIn("--ref-layout", command_summary)
            self.assertIn("/previews/CP001/preview.png", command_summary)
            self.assertNotIn(f"{task_id}_comp_extra_1.png --ref-layout", command_summary)
            self.assertIn("--ref-style", command_summary)
            self.assertIn(f"{task_id}_style.png", command_summary)
            self.assertIn(f"{task_id}_lighting.png", command_summary)
            self.assertNotIn(f"--reference {root / 'task-assets' / f'{task_id}_comp.png'}", command_summary)

    def test_local_edit_task_brief_routes_generation_through_base_image(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            project_dir = self.init_project(root / "outputs")
            self.register_base_assets(project_dir, root / "assets")
            self.build_base_product_profile(project_dir)
            task_id, task_dir = self.create_task_with_assets(
                project_dir,
                root / "task-assets",
                task_name="户外桌面局部替换",
            )

            base_image = task_dir / "versions" / "V001" / "approved-base.png"
            write_png(base_image)

            brief = run_cmd(
                str(SCRIPTS_DIR / "build_task_brief.py"),
                "--project-dir",
                str(project_dir),
                "--task-id",
                task_id,
                "--task-goal",
                "保持母版场景，只改木盘上的顶部剖面产品",
                "--output-ratio",
                "3:4",
                "--output-kind",
                "detail_page_scene",
                "--execution-mode",
                "local_edit",
                "--base-image",
                str(base_image),
                "--editable-target",
                "木盘上的顶部剖面产品",
                "--immutable-element",
                "木桌、葡萄、饮品、底部两个完整面包全部不变",
                "--anchor-object",
                "木盘",
                "--spatial-relation",
                "顶部剖面产品仍叠在底部两个完整面包上",
            )
            self.assertEqual(brief.returncode, 0, brief.stderr)

            confirm = run_cmd(
                str(SCRIPTS_DIR / "record_confirmation.py"),
                "--project-dir",
                str(project_dir),
                "--task-id",
                task_id,
                "--kind",
                "task_brief",
                "--decision",
                "approve",
                "--note",
                "局部替换约束确认",
            )
            self.assertEqual(confirm.returncode, 0, confirm.stderr)

            prompt = run_cmd(
                str(SCRIPTS_DIR / "build_generation_prompt.py"),
                "--project-dir",
                str(project_dir),
                "--task-id",
                task_id,
            )
            self.assertEqual(prompt.returncode, 0, prompt.stderr)

            fake_generator = root / "fake_generate.py"
            write_fake_generator(fake_generator)
            generate = run_cmd(
                str(SCRIPTS_DIR / "run_generation.py"),
                "--project-dir",
                str(project_dir),
                "--task-id",
                task_id,
                "--gpt-image2-script",
                str(fake_generator),
            )
            self.assertEqual(generate.returncode, 0, generate.stderr)

            task_brief = read_json(task_dir / "task_brief.json")
            self.assertEqual(task_brief["execution_mode"], "local_edit")
            self.assertEqual(task_brief["base_image"]["absolute_path"], str(base_image))
            self.assertIn("木盘上的顶部剖面产品", task_brief["edit_scope"]["editable_targets"])
            self.assertIn("木盘", task_brief["edit_scope"]["anchor_objects"])

            prompt_path = task_dir / "prompts" / "prompt_V001.md"
            prompt_text = prompt_path.read_text(encoding="utf-8")
            self.assertIn("Scene-locked local edit mode", prompt_text)
            self.assertIn("Immutable elements", prompt_text)
            self.assertIn("Editable targets", prompt_text)
            self.assertIn("木盘上的顶部剖面产品", prompt_text)

            generation = read_json(task_dir / "generation_manifest.json")
            command_summary = generation["versions"][-1]["command_summary"]
            self.assertIn("--ref-base", command_summary)
            self.assertIn(str(base_image), command_summary)

    def test_storyboard_and_texture_identity_lock_layout_and_texture_authority(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            project_dir = self.init_project(root / "outputs")
            self.register_base_assets(project_dir, root / "assets")
            self.build_base_product_profile(project_dir)
            task_id, task_dir = self.create_task_with_assets(
                project_dir,
                root / "task-assets",
                extra_layout_refs=1,
                extra_storyboard_refs=1,
                include_task_style_refs=True,
                include_storyboard_refs=True,
                include_texture_refs=True,
            )

            brief = run_cmd(
                str(SCRIPTS_DIR / "build_task_brief.py"),
                "--project-dir",
                str(project_dir),
                "--task-id",
                task_id,
                "--task-goal",
                "做一张锁定主机位和切面质感的详情页首图",
                "--output-ratio",
                "3:4",
                "--output-kind",
                "detail_page_hero",
                "--composition-note",
                "普通构图参考只做辅助，不抢主机位",
                "--scene-note",
                "暖调商业食品摄影",
                "--product-state-note",
                "顶部切面必须真实露出夹心",
                "--placement-note",
                "主产品偏左，右侧留标题位",
                "--hero-shot-intent",
                "详情页首图主机位稳定锁定在三分之二侧前方",
                "--shot-priority",
                "先保证主图机位和留白",
                "--shot-priority",
                "再保证切面特写信息真实",
                "--camera-angle-lock",
                "以角度故事板的最新一张为唯一主机位 authority",
                "--crop-and-whitespace-lock",
                "保留右侧标题留白和顶部呼吸空间",
                "--lighting-direction-lock",
                "主光从右上进入，切面受光更强",
                "--focus-anchor",
                "前景主产品切面",
                "--texture-priority",
                "先保住切面孔洞和夹心厚度",
                "--must-match-texture-point",
                "切面孔洞大小和疏密",
                "--must-match-texture-point",
                "外皮松软起皱感",
                "--cross-section-truth-lock",
                "切面细节以真实产品图和质感身份板为准",
                "--surface-finish-lock",
                "外皮微哑光，夹心顺滑不流汤",
                "--fake-texture-risk",
                "不要假孔洞",
                "--fake-texture-risk",
                "不要把奶油画成果酱流心",
                "--must-show",
                "切面孔洞真实",
                "--must-avoid",
                "不要借用风格图里的假切面",
            )
            self.assertEqual(brief.returncode, 0, brief.stderr)

            brief_data = read_json(task_dir / "task_brief.json")
            self.assertEqual(len(brief_data["reference_paths"]["camera_storyboard_reference"]), 2)
            self.assertEqual(len(brief_data["reference_paths"]["texture_identity_reference"]), 1)
            self.assertEqual(
                brief_data["camera_plan"]["camera_angle_lock"],
                "以角度故事板的最新一张为唯一主机位 authority",
            )
            self.assertIn("切面孔洞大小和疏密", brief_data["texture_plan"]["must_match_texture_points"])
            self.assertFalse(brief_data["planning_warnings"])

            confirm = run_cmd(
                str(SCRIPTS_DIR / "record_confirmation.py"),
                "--project-dir",
                str(project_dir),
                "--task-id",
                task_id,
                "--kind",
                "task_brief",
                "--decision",
                "approve",
                "--note",
                "角度故事板和质感身份板确认完成",
            )
            self.assertEqual(confirm.returncode, 0, confirm.stderr)

            fake_generator = root / "fake_generate.py"
            write_fake_generator(fake_generator)
            preview_path = self.confirm_camera_preview(project_dir, task_id, task_dir, fake_generator)

            prompt = run_cmd(
                str(SCRIPTS_DIR / "build_generation_prompt.py"),
                "--project-dir",
                str(project_dir),
                "--task-id",
                task_id,
            )
            self.assertEqual(prompt.returncode, 0, prompt.stderr)

            prompt_path = Path(parse_kv(prompt.stdout)["prompt_file"])
            prompt_text = prompt_path.read_text(encoding="utf-8")
            self.assertIn("Camera storyboard authority", prompt_text)
            self.assertIn("Texture identity authority", prompt_text)
            self.assertIn("Do not borrow fake cross-sections", prompt_text)
            self.assertIn("Do not treat storyboard silhouettes as real product anatomy", prompt_text)
            self.assertIn("Texture details must follow the real product photos and texture identity references.", prompt_text)
            self.assertIn("Camera angle, crop, whitespace, and key focus must follow the confirmed camera preview when it exists.", prompt_text)

            generate = run_cmd(
                str(SCRIPTS_DIR / "run_generation.py"),
                "--project-dir",
                str(project_dir),
                "--task-id",
                task_id,
                "--gpt-image2-script",
                str(fake_generator),
                "--dry-run",
            )
            self.assertEqual(generate.returncode, 0, generate.stderr)

            generation = read_json(task_dir / "generation_manifest.json")
            version = generation["versions"][-1]
            command_summary = version["command_summary"]

            self.assertEqual(version["layout_authority_role"], "confirmed_camera_preview")
            self.assertEqual(version["camera_preview_id"], "CP001")
            self.assertEqual(len(version["camera_storyboard_refs"]), 2)
            self.assertEqual(len(version["texture_identity_refs"]), 1)
            self.assertIn(str(preview_path), command_summary)
            self.assertNotIn(f"{task_id}_comp_extra_1.png --ref-layout", command_summary)
            self.assertIn(f"{task_id}_texture.png", command_summary)
            self.assertIn(f"{task_id}_comp_extra_1.png", command_summary)

    def test_package_material_refs_flow_into_prompt_and_generation_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            project_dir = self.init_project(root / "outputs")
            self.register_base_assets(project_dir, root / "assets")
            self.build_base_product_profile(project_dir)
            task_id, task_dir = self.create_task_with_assets(
                project_dir,
                root / "task-assets",
                task_name="包装主图白底",
                include_storyboard_refs=True,
                include_package_material_refs=True,
            )

            brief = run_cmd(
                str(SCRIPTS_DIR / "build_task_brief.py"),
                "--project-dir",
                str(project_dir),
                "--task-id",
                task_id,
                "--task-goal",
                "做一张白底包装主图，重点锁定哑面铝膜包材",
                "--output-ratio",
                "1:1",
                "--output-kind",
                "main_image",
                "--composition-note",
                "单包居中，四周留白均匀",
                "--scene-note",
                "纯白背景包装产品图",
                "--product-state-note",
                "包装正面平躺，顶底热封边清楚",
                "--placement-note",
                "主体完整入镜",
                "--hero-shot-intent",
                "稳定锁定单包白底主图机位",
                "--shot-priority",
                "先锁定主机位",
                "--camera-angle-lock",
                "最终机位只听机位定稿图",
                "--crop-and-whitespace-lock",
                "四周白边均匀",
                "--lighting-direction-lock",
                "主光从右上进入",
                "--focus-anchor",
                "包装正面中心区域",
                "--package-material-priority",
                "先保住哑面铝膜膜感",
                "--package-material-priority",
                "再保住热封边和鼓包厚度",
                "--package-material-type-lock",
                "包材必须是印刷哑面铝膜软袋，不是普通塑料袋",
                "--package-finish-lock",
                "表面为低饱和、克制的哑面完成度",
                "--package-structure-detail-lock",
                "中封边、顶底热封边和自然鼓包厚度必须真实",
                "--package-reflection-lock",
                "只允许柔和克制的金属膜反射，不要镜面高光",
                "--fake-package-material-risk",
                "不要普通塑料膜感",
                "--fake-package-material-risk",
                "不要纸袋感",
                "--must-show",
                "包装正面完整",
                "--must-avoid",
                "不要出现第二包",
            )
            self.assertEqual(brief.returncode, 0, brief.stderr)

            confirm = run_cmd(
                str(SCRIPTS_DIR / "record_confirmation.py"),
                "--project-dir",
                str(project_dir),
                "--task-id",
                task_id,
                "--kind",
                "task_brief",
                "--decision",
                "approve",
                "--note",
                "开始机位定稿",
            )
            self.assertEqual(confirm.returncode, 0, confirm.stderr)

            fake_generator = root / "fake_generate.py"
            write_fake_generator(fake_generator)
            self.confirm_camera_preview(project_dir, task_id, task_dir, fake_generator)

            prompt = run_cmd(
                str(SCRIPTS_DIR / "build_generation_prompt.py"),
                "--project-dir",
                str(project_dir),
                "--task-id",
                task_id,
            )
            self.assertEqual(prompt.returncode, 0, prompt.stderr)
            prompt_path = Path(parse_kv(prompt.stdout)["prompt_file"])
            prompt_text = prompt_path.read_text(encoding="utf-8")
            self.assertIn("Package material authority", prompt_text)
            self.assertIn("Package material references", prompt_text)
            self.assertIn("Packaging material details must follow the real product photos and package material references.", prompt_text)
            self.assertIn("Do not borrow fake plastic gloss, fake paper texture, or fake seal structure from style references.", prompt_text)

            generate = run_cmd(
                str(SCRIPTS_DIR / "run_generation.py"),
                "--project-dir",
                str(project_dir),
                "--task-id",
                task_id,
                "--gpt-image2-script",
                str(fake_generator),
                "--dry-run",
            )
            self.assertEqual(generate.returncode, 0, generate.stderr)

            generation = read_json(task_dir / "generation_manifest.json")
            version = generation["versions"][-1]
            self.assertEqual(len(version["package_material_refs"]), 1)
            self.assertIn(f"{task_id}_package_material.png", version["command_summary"])

    def test_task_generation_requires_confirmed_camera_preview_for_whole_image(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            project_dir = self.init_project(root / "outputs")
            self.register_base_assets(project_dir, root / "assets")
            self.build_base_product_profile(project_dir)
            task_id, _task_dir = self.create_task_with_assets(
                project_dir,
                root / "task-assets",
                include_storyboard_refs=True,
            )

            brief = run_cmd(
                str(SCRIPTS_DIR / "build_task_brief.py"),
                "--project-dir",
                str(project_dir),
                "--task-id",
                task_id,
                "--task-goal",
                "做一张白底主图",
                "--output-ratio",
                "1:1",
                "--output-kind",
                "main_image",
                "--composition-note",
                "主体居中，木板完整入镜",
                "--scene-note",
                "白底商业产品图",
                "--must-show",
                "主体完整",
                "--must-avoid",
                "不要多余道具",
            )
            self.assertEqual(brief.returncode, 0, brief.stderr)

            confirm = run_cmd(
                str(SCRIPTS_DIR / "record_confirmation.py"),
                "--project-dir",
                str(project_dir),
                "--task-id",
                task_id,
                "--kind",
                "task_brief",
                "--decision",
                "approve",
                "--note",
                "先进入机位定稿阶段",
            )
            self.assertEqual(confirm.returncode, 0, confirm.stderr)

            prompt = run_cmd(
                str(SCRIPTS_DIR / "build_generation_prompt.py"),
                "--project-dir",
                str(project_dir),
                "--task-id",
                task_id,
            )
            self.assertNotEqual(prompt.returncode, 0)
            self.assertIn("机位定稿图", prompt.stderr)

            fake_generator = root / "fake_generate.py"
            write_fake_generator(fake_generator)
            generate = run_cmd(
                str(SCRIPTS_DIR / "run_generation.py"),
                "--project-dir",
                str(project_dir),
                "--task-id",
                task_id,
                "--gpt-image2-script",
                str(fake_generator),
            )
            self.assertNotEqual(generate.returncode, 0)
            self.assertIn("机位定稿图", generate.stderr)

    def test_camera_preview_confirmation_drives_final_layout_authority(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            project_dir = self.init_project(root / "outputs")
            self.register_base_assets(project_dir, root / "assets")
            self.build_base_product_profile(project_dir)
            task_id, task_dir = self.create_task_with_assets(
                project_dir,
                root / "task-assets",
                extra_layout_refs=1,
                extra_storyboard_refs=1,
                include_storyboard_refs=True,
                include_task_style_refs=True,
                include_texture_refs=True,
            )

            brief = run_cmd(
                str(SCRIPTS_DIR / "build_task_brief.py"),
                "--project-dir",
                str(project_dir),
                "--task-id",
                task_id,
                "--task-goal",
                "做一张白底产品主图",
                "--output-ratio",
                "1:1",
                "--output-kind",
                "main_image",
                "--composition-note",
                "整体角度按机位参考图",
                "--scene-note",
                "纯白背景",
                "--hero-shot-intent",
                "锁定稳定主机位",
                "--shot-priority",
                "先锁定角度",
                "--shot-priority",
                "再锁定留白",
                "--camera-angle-lock",
                "机位以后只听机位定稿图",
                "--crop-and-whitespace-lock",
                "主体完整入镜并保留白边",
                "--lighting-direction-lock",
                "主光从右上进入",
                "--focus-anchor",
                "前排主体",
                "--texture-priority",
                "先保住真实表面状态",
                "--must-match-texture-point",
                "表面起伏和焦斑",
                "--cross-section-truth-lock",
                "材质以产品真相图和质感身份图为准",
                "--surface-finish-lock",
                "表面微油润",
                "--fake-texture-risk",
                "不要假拉丝",
                "--must-show",
                "主体完整",
                "--must-avoid",
                "不要借错别的产品结构",
            )
            self.assertEqual(brief.returncode, 0, brief.stderr)

            confirm_brief = run_cmd(
                str(SCRIPTS_DIR / "record_confirmation.py"),
                "--project-dir",
                str(project_dir),
                "--task-id",
                task_id,
                "--kind",
                "task_brief",
                "--decision",
                "approve",
                "--note",
                "开始生成机位定稿图",
            )
            self.assertEqual(confirm_brief.returncode, 0, confirm_brief.stderr)

            preview_prompt = run_cmd(
                str(SCRIPTS_DIR / "build_camera_preview_prompt.py"),
                "--project-dir",
                str(project_dir),
                "--task-id",
                task_id,
            )
            self.assertEqual(preview_prompt.returncode, 0, preview_prompt.stderr)
            preview_data = parse_kv(preview_prompt.stdout)
            self.assertEqual(preview_data["preview_id"], "CP001")
            preview_prompt_path = Path(preview_data["prompt_file"])
            self.assertTrue(preview_prompt_path.exists())
            preview_prompt_text = preview_prompt_path.read_text(encoding="utf-8")
            self.assertIn("机位定稿图", preview_prompt_text)
            self.assertIn("灰度块面", preview_prompt_text)
            self.assertIn("不要表现真实食物质感", preview_prompt_text)

            fake_generator = root / "fake_generate.py"
            write_fake_generator(fake_generator)
            preview_generate = run_cmd(
                str(SCRIPTS_DIR / "run_camera_preview.py"),
                "--project-dir",
                str(project_dir),
                "--task-id",
                task_id,
                "--gpt-image2-script",
                str(fake_generator),
            )
            self.assertEqual(preview_generate.returncode, 0, preview_generate.stderr)

            preview_manifest = read_json(task_dir / "camera_preview_manifest.json")
            self.assertEqual(preview_manifest["latest_preview_id"], "CP001")
            self.assertEqual(preview_manifest["latest_status"], "succeeded")
            self.assertTrue((task_dir / "previews" / "CP001" / "preview.png").exists())

            confirm_preview = run_cmd(
                str(SCRIPTS_DIR / "record_confirmation.py"),
                "--project-dir",
                str(project_dir),
                "--task-id",
                task_id,
                "--kind",
                "task_camera_preview",
                "--decision",
                "approve",
                "--note",
                "机位确认通过",
                "--selected-output",
                str(task_dir / "previews" / "CP001" / "preview.png"),
            )
            self.assertEqual(confirm_preview.returncode, 0, confirm_preview.stderr)

            final_prompt = run_cmd(
                str(SCRIPTS_DIR / "build_generation_prompt.py"),
                "--project-dir",
                str(project_dir),
                "--task-id",
                task_id,
            )
            self.assertEqual(final_prompt.returncode, 0, final_prompt.stderr)
            final_prompt_path = Path(parse_kv(final_prompt.stdout)["prompt_file"])
            final_prompt_text = final_prompt_path.read_text(encoding="utf-8")
            self.assertIn("机位定稿图优先", final_prompt_text)
            self.assertIn("固定提示词骨架", final_prompt_text)

            final_generate = run_cmd(
                str(SCRIPTS_DIR / "run_generation.py"),
                "--project-dir",
                str(project_dir),
                "--task-id",
                task_id,
                "--gpt-image2-script",
                str(fake_generator),
                "--dry-run",
            )
            self.assertEqual(final_generate.returncode, 0, final_generate.stderr)

            generation = read_json(task_dir / "generation_manifest.json")
            version = generation["versions"][-1]
            command_summary = version["command_summary"]
            self.assertEqual(version["layout_authority_role"], "confirmed_camera_preview")
            self.assertEqual(version["camera_preview_id"], "CP001")
            self.assertIn(str(task_dir / "previews" / "CP001" / "preview.png"), version["layout_refs"])
            self.assertIn("--ref-layout", command_summary)
            self.assertIn(str(task_dir / "previews" / "CP001" / "preview.png"), command_summary)
            self.assertNotIn("storyboard_extra_1.png --ref-layout", command_summary)

    def test_revise_task_preserves_camera_preview_by_default_and_can_reset_it(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            project_dir = self.init_project(root / "outputs")
            self.register_base_assets(project_dir, root / "assets")
            self.build_base_product_profile(project_dir)
            task_id, task_dir = self.create_task_with_assets(
                project_dir,
                root / "task-assets",
                include_storyboard_refs=True,
            )

            brief = run_cmd(
                str(SCRIPTS_DIR / "build_task_brief.py"),
                "--project-dir",
                str(project_dir),
                "--task-id",
                task_id,
                "--task-goal",
                "做一张白底主图",
                "--output-ratio",
                "1:1",
                "--output-kind",
                "main_image",
                "--composition-note",
                "主体居中",
                "--scene-note",
                "纯白背景",
                "--hero-shot-intent",
                "稳定锁机位",
                "--shot-priority",
                "先锁定角度",
                "--camera-angle-lock",
                "以后只认机位定稿图",
                "--crop-and-whitespace-lock",
                "保留白边",
                "--lighting-direction-lock",
                "右上主光",
                "--focus-anchor",
                "主体前排",
            )
            self.assertEqual(brief.returncode, 0, brief.stderr)

            confirm_brief = run_cmd(
                str(SCRIPTS_DIR / "record_confirmation.py"),
                "--project-dir",
                str(project_dir),
                "--task-id",
                task_id,
                "--kind",
                "task_brief",
                "--decision",
                "approve",
                "--note",
                "进入机位定稿",
            )
            self.assertEqual(confirm_brief.returncode, 0, confirm_brief.stderr)

            preview_prompt = run_cmd(
                str(SCRIPTS_DIR / "build_camera_preview_prompt.py"),
                "--project-dir",
                str(project_dir),
                "--task-id",
                task_id,
            )
            self.assertEqual(preview_prompt.returncode, 0, preview_prompt.stderr)

            fake_generator = root / "fake_generate.py"
            write_fake_generator(fake_generator)
            preview_generate = run_cmd(
                str(SCRIPTS_DIR / "run_camera_preview.py"),
                "--project-dir",
                str(project_dir),
                "--task-id",
                task_id,
                "--gpt-image2-script",
                str(fake_generator),
            )
            self.assertEqual(preview_generate.returncode, 0, preview_generate.stderr)

            confirm_preview = run_cmd(
                str(SCRIPTS_DIR / "record_confirmation.py"),
                "--project-dir",
                str(project_dir),
                "--task-id",
                task_id,
                "--kind",
                "task_camera_preview",
                "--decision",
                "approve",
                "--note",
                "机位已确认",
                "--selected-output",
                str(task_dir / "previews" / "CP001" / "preview.png"),
            )
            self.assertEqual(confirm_preview.returncode, 0, confirm_preview.stderr)

            revise_keep_preview = run_cmd(
                str(SCRIPTS_DIR / "revise_task.py"),
                "--project-dir",
                str(project_dir),
                "--task-id",
                task_id,
                "--note",
                "只调一下榴莲表面质感",
            )
            self.assertEqual(revise_keep_preview.returncode, 0, revise_keep_preview.stderr)
            task_state = read_json(task_dir / "task_state.json")
            self.assertTrue(task_state["workflow_flags"]["camera_preview_confirmed"])
            self.assertTrue(task_state["workflow_flags"]["generation_allowed"])
            self.assertEqual(task_state["selected_camera_preview_id"], "CP001")

            revise_reset_preview = run_cmd(
                str(SCRIPTS_DIR / "revise_task.py"),
                "--project-dir",
                str(project_dir),
                "--task-id",
                task_id,
                "--note",
                "机位也要一起改",
                "--reset-camera-preview",
            )
            self.assertEqual(revise_reset_preview.returncode, 0, revise_reset_preview.stderr)
            reset_state = read_json(task_dir / "task_state.json")
            self.assertFalse(reset_state["workflow_flags"]["camera_preview_confirmed"])
            self.assertFalse(reset_state["workflow_flags"]["generation_allowed"])
            self.assertEqual(reset_state["current_stage"], "task_camera_preview_ready")
            self.assertEqual(reset_state["selected_camera_preview_id"], "")


if __name__ == "__main__":
    unittest.main()
