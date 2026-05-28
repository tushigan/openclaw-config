import base64
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT))

from scripts.workflow import (
    GTP_IMAGE_SCRIPT,
    REQUIRED_PATHS,
    build_project_dir,
    build_run_dir,
    build_dreamina_command,
    build_gpt_image_jobs,
    build_prompts,
    collect_reference_files,
    ensure_run_layout,
    normalize_brief,
    normalize_reference_image,
    summarize_reusable_fields,
    sync_project_canonical_files,
    update_project_state,
)

SMALL_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO2k4L8AAAAASUVORK5CYII="
)


class WorkflowTests(unittest.TestCase):
    def test_gpt_image_script_resolves_local_openclaw_install(self):
        self.assertTrue(GTP_IMAGE_SCRIPT.exists())
        self.assertEqual(
            GTP_IMAGE_SCRIPT,
            Path("/Users/a123/.openclaw/workspace-design/skills/gpt-image2-gen/scripts/generate.py"),
        )

    def test_normalize_brief_applies_defaults_and_slug(self):
        brief = normalize_brief(
            {
                "subject": "橘猫",
                "action": "在广场跳 breaking",
                "scene": "欧洲老城石板广场",
                "style": "电影感街头纪实",
            }
        )

        self.assertEqual(brief["ratio"], "16:9")
        self.assertEqual(brief["duration"], 5)
        self.assertEqual(brief["quality_tier"], "draft")
        self.assertEqual(brief["language"], "zh-CN")
        self.assertEqual(brief["storyboard_strategy"], "auto_beats")
        self.assertGreaterEqual(brief["storyboard_panel_count"], 3)
        self.assertEqual(brief["storyboard_panel_count"], len(brief["storyboard_beats"]))
        self.assertIn("slug", brief)
        self.assertTrue(brief["slug"])

    def test_normalize_brief_plans_simple_story_with_fewer_panels(self):
        brief = normalize_brief(
            {
                "subject": "黄色小鸡",
                "action": "沿小路走来，看看麦穗，转向镜头咕一声，最后定格",
                "scene": "麦田小路",
                "style": "治愈系3D广告海报",
                "duration": 7,
            }
        )

        self.assertGreaterEqual(brief["storyboard_panel_count"], 4)
        self.assertLessEqual(brief["storyboard_panel_count"], 6)
        self.assertIn("关键动作落点", "\n".join(brief["storyboard_beats"]))

    def test_build_prompts_keeps_role_boundaries(self):
        brief = normalize_brief(
            {
                "subject": "复古卷发女探险家",
                "action": "在废土公路边查看地图后上车远去",
                "scene": "1960年代原子朋克核废土公路",
                "style": "电影级真实感，孤独公路片气质",
                "anchor_elements": ["锈蚀复古汽车", "Skyline Diner", "Nuka Cola 广告牌"],
            }
        )

        prompts = build_prompts(brief)

        self.assertIn("只负责风格与世界", prompts["original"])
        self.assertIn("只负责角色一致性", prompts["identity_board"])
        self.assertIn("关键帧规划", prompts["storyboard"])
        self.assertIn("优先保住角色结构", prompts["storyboard"])
        self.assertIn("不要重新发明", prompts["video"])
        self.assertIn("锈蚀复古汽车", prompts["storyboard"])
        self.assertNotIn("12格", prompts["identity_board"])

    def test_build_prompts_use_identity_source_as_highest_truth(self):
        brief = normalize_brief(
            {
                "subject": "点赞鸡",
                "action": "沿小路走来，看看麦穗，转向镜头咕一声，最后定格",
                "scene": "麦田小路",
                "style": "治愈系3D广告海报",
                "duration": 7,
                "identity_strategy": "reuse_exact",
                "identity_anchor_rules": ["正面可见尾巴", "只有一侧翅膀"],
                "existing_references": {"identity_source": "/tmp/source.png"},
            }
        )

        prompts = build_prompts(brief)

        self.assertIn("identity-source", prompts["storyboard"])
        self.assertIn("正面可见尾巴", prompts["identity_board"])
        self.assertIn("只有一侧翅膀", prompts["video"])
        self.assertIn(f"{brief['storyboard_panel_count']} 格", prompts["video"])

    def test_build_prompts_and_jobs_follow_vertical_ratio(self):
        brief = normalize_brief(
            {
                "subject": "黄色小鸡",
                "action": "沿小路走来后定格",
                "scene": "麦田小路",
                "style": "治愈系3D广告海报",
                "ratio": "9:16",
            }
        )
        prompts = build_prompts(brief)

        self.assertIn("适合 9:16 项目", prompts["identity_board"])
        self.assertIn("每一格都必须是独立的 9:16 成片画幅", prompts["storyboard"])

        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "run"
            ensure_run_layout(run_dir)
            jobs = build_gpt_image_jobs(brief, run_dir, prompts)

        sizes = {job["name"]: job["command"][job["command"].index("--size") + 1] for job in jobs}
        self.assertEqual(sizes["original"], "1440x2560")
        self.assertEqual(sizes["identity_board"], "1440x2560")
        self.assertEqual(sizes["storyboard"], "1440x2560")

    def test_ensure_run_layout_creates_required_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "run"
            ensure_run_layout(run_dir)

            for relative in REQUIRED_PATHS:
                self.assertTrue((run_dir / relative).exists(), relative)

    def test_build_run_dir_accepts_project_root_or_exact_outputs_dir(self):
        brief = normalize_brief(
            {
                "subject": "橘猫",
                "action": "跳舞",
                "scene": "广场",
                "style": "电影感",
            }
        )

        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp)
            exact_output_dir = project_root / "outputs" / "dreamina-reference-video"
            project_dir = build_project_dir(project_root, brief)

            from_project_root = build_run_dir(project_root, brief)
            from_exact_output_dir = build_run_dir(exact_output_dir, brief)

            self.assertEqual(from_project_root.parent, project_dir / "runs")
            self.assertEqual(from_exact_output_dir.parent, project_dir / "runs")

    def test_build_project_dir_uses_project_slug(self):
        brief = normalize_brief(
            {
                "project_name": "黄小咕秋日视频",
                "subject": "黄小咕",
                "action": "跳舞",
                "scene": "秋日林间步道",
                "style": "3D卡通",
            }
        )

        with tempfile.TemporaryDirectory() as tmp:
            project_dir = build_project_dir(Path(tmp), brief)
            self.assertTrue(project_dir.name.startswith("brief-"))
            self.assertIn("projects", str(project_dir))

    def test_build_run_dir_avoids_same_second_collisions(self):
        brief = normalize_brief(
            {
                "subject": "点赞鸡",
                "action": "走来后定格",
                "scene": "麦田小路",
                "style": "治愈系3D广告海报",
            }
        )

        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp)
            first = build_run_dir(project_root, brief)
            first.mkdir(parents=True, exist_ok=True)

            second = build_run_dir(project_root, brief)

            self.assertNotEqual(first, second)
            self.assertTrue(str(second.name).startswith(first.name + "-"))

    def test_update_project_state_writes_project_manifest(self):
        brief = normalize_brief(
            {
                "subject": "黄小咕",
                "action": "跳舞后定格",
                "scene": "林间步道",
                "style": "3D卡通",
            }
        )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project_dir = build_project_dir(root, brief)
            run_dir = build_run_dir(root, brief)
            ensure_run_layout(run_dir)
            (run_dir / "refs" / "identity-source.png").write_bytes(b"png")
            reference_files = collect_reference_files(run_dir)
            canonical_files = sync_project_canonical_files(project_dir, run_dir, ("identity_source",))

            state = update_project_state(
                project_dir,
                brief,
                run_dir,
                stage="prepare",
                status="ready_for_ref_generation",
                reference_files=reference_files,
                canonical_files=canonical_files,
            )

            manifest = json.loads((project_dir / "project.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["project_id"], brief["project_slug"])
            self.assertEqual(manifest["latest_run_dir"], str(run_dir))
            self.assertEqual(manifest["runs"][0]["stage"], "prepare")
            self.assertIn("identity_source", manifest["canonical_files"])
            self.assertEqual(state["project_id"], manifest["project_id"])

    def test_update_project_state_preserves_project_defaults_across_runs(self):
        brief_first = normalize_brief(
            {
                "project_name": "黄小咕品牌视频",
                "project_slug": "huangxiaogu-brand",
                "subject": "黄小咕",
                "action": "跳舞后定格",
                "scene": "林间步道",
                "style": "3D卡通",
                "ratio": "9:16",
                "duration": 8,
                "quality_tier": "final",
            }
        )
        brief_second = normalize_brief(
            {
                "project_name": "黄小咕品牌视频",
                "project_slug": "huangxiaogu-brand",
                "subject": "黄小咕",
                "action": "林间奔跑",
                "scene": "金色麦田",
                "style": "3D卡通",
                "ratio": "16:9",
                "duration": 5,
                "quality_tier": "draft",
            }
        )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project_dir = build_project_dir(root, brief_first)

            first_run_dir = build_run_dir(root, brief_first)
            ensure_run_layout(first_run_dir)
            update_project_state(
                project_dir,
                brief_first,
                first_run_dir,
                stage="prepare",
                status="ready_for_ref_generation",
            )

            second_run_dir = build_run_dir(root, brief_second)
            ensure_run_layout(second_run_dir)
            update_project_state(
                project_dir,
                brief_second,
                second_run_dir,
                stage="prepare",
                status="ready_for_ref_generation",
            )

            manifest = json.loads((project_dir / "project.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["defaults"]["ratio"], "9:16")
            self.assertEqual(manifest["defaults"]["duration"], 8)
            self.assertEqual(manifest["defaults"]["quality_tier"], "final")
            self.assertEqual(manifest["latest_run_dir"], str(second_run_dir))

    def test_build_gpt_image_jobs_skips_existing_references(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "run"
            ensure_run_layout(run_dir)
            existing_storyboard = run_dir / "refs" / "storyboard.png"
            existing_storyboard.write_bytes(b"png")

            brief = normalize_brief(
                {
                    "subject": "橘猫",
                    "action": "跳舞",
                    "scene": "广场",
                    "style": "电影感",
                    "existing_references": {"storyboard": str(existing_storyboard)},
                }
            )
            prompts = build_prompts(brief)

            jobs = build_gpt_image_jobs(brief, run_dir, prompts)

            names = [job["name"] for job in jobs]
            self.assertEqual(names, ["original", "identity_board"])

    def test_reuse_exact_skips_identity_board_generation_and_uses_identity_source(self):
        brief = normalize_brief(
            {
                "subject": "点赞鸡",
                "action": "沿小路轻快走来后转向镜头定格",
                "scene": "麦田小路",
                "style": "治愈系3D广告海报",
                "identity_strategy": "reuse_exact",
                "existing_references": {"identity_source": "/tmp/identity-source.png"},
            }
        )
        prompts = build_prompts(brief)

        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "run"
            ensure_run_layout(run_dir)
            for name in ("original", "identity-source", "identity-board"):
                (run_dir / "refs" / f"{name}.png").write_bytes(b"png")

            jobs = build_gpt_image_jobs(brief, run_dir, prompts)

        storyboard_job = next(job for job in jobs if job["name"] == "storyboard")
        self.assertEqual([job["name"] for job in jobs], ["storyboard"])
        self.assertIn(str(run_dir / "refs" / "identity-source.png"), storyboard_job["command"])

    def test_extend_from_source_generates_identity_board_from_identity_source(self):
        brief = normalize_brief(
            {
                "subject": "点赞鸡",
                "action": "沿小路轻快走来后转向镜头定格",
                "scene": "麦田小路",
                "style": "治愈系3D广告海报",
                "identity_strategy": "extend_from_source",
                "existing_references": {"identity_source": "/tmp/identity-source.png"},
            }
        )
        prompts = build_prompts(brief)

        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "run"
            ensure_run_layout(run_dir)
            (run_dir / "refs" / "original.png").write_bytes(b"png")
            (run_dir / "refs" / "identity-source.png").write_bytes(b"png")

            jobs = build_gpt_image_jobs(brief, run_dir, prompts)

        identity_job = next(job for job in jobs if job["name"] == "identity_board")
        storyboard_job = next(job for job in jobs if job["name"] == "storyboard")
        self.assertIn("--ref-mascot", identity_job["command"])
        self.assertIn(str(run_dir / "refs" / "identity-source.png"), identity_job["command"])
        self.assertIn(str(run_dir / "refs" / "identity-source.png"), storyboard_job["command"])

    def test_storyboard_job_uses_mascot_reference(self):
        brief = normalize_brief(
            {
                "subject": "点赞鸡",
                "action": "沿小路轻快走来后转向镜头定格",
                "scene": "麦田小路",
                "style": "治愈系3D广告海报",
            }
        )
        prompts = build_prompts(brief)

        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "run"
            ensure_run_layout(run_dir)
            (run_dir / "refs" / "original.png").write_bytes(b"png")
            (run_dir / "refs" / "identity-board.png").write_bytes(b"png")

            jobs = build_gpt_image_jobs(brief, run_dir, prompts)

        storyboard_job = next(job for job in jobs if job["name"] == "storyboard")
        self.assertIn("--ref-mascot", storyboard_job["command"])
        self.assertNotIn("--ref-base", storyboard_job["command"])

    def test_build_dreamina_command_switches_by_quality(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "run"
            ensure_run_layout(run_dir)
            for name in ("original", "identity-board", "storyboard"):
                (run_dir / "refs" / f"{name}.png").write_bytes(b"png")

            brief = normalize_brief(
                {
                    "subject": "橘猫",
                    "action": "跳舞",
                    "scene": "广场",
                    "style": "电影感",
                    "quality_tier": "final",
                }
            )
            prompts = build_prompts(brief)
            cmd = build_dreamina_command(run_dir, brief, prompts)

            self.assertIn("dreamina", cmd[0])
            self.assertIn("multimodal2video", cmd)
            self.assertIn("--model_version=seedance2.0_vip", cmd)
            self.assertIn("--video_resolution=1080p", cmd)
            image_flags = [item for item in cmd if item == "--image"]
            self.assertEqual(len(image_flags), 3)

    def test_build_dreamina_command_prefers_identity_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "run"
            ensure_run_layout(run_dir)
            for name in ("original", "identity-board", "identity-source", "storyboard"):
                (run_dir / "refs" / f"{name}.png").write_bytes(b"png")

            brief = normalize_brief(
                {
                    "subject": "点赞鸡",
                    "action": "走来后定格",
                    "scene": "麦田小路",
                    "style": "治愈系3D广告海报",
                    "existing_references": {"identity_source": "/tmp/identity-source.png"},
                    "identity_strategy": "extend_from_source",
                }
            )
            prompts = build_prompts(brief)
            cmd = build_dreamina_command(run_dir, brief, prompts)

            image_paths = [cmd[idx + 1] for idx, item in enumerate(cmd) if item == "--image"]
            self.assertEqual(image_paths[1], str(run_dir / "refs" / "identity-source.png"))

    def test_summarize_reusable_fields_is_human_readable(self):
        brief = normalize_brief(
            {
                "subject": "橘猫",
                "action": "跳舞",
                "scene": "广场",
                "style": "电影感",
            }
        )
        text = summarize_reusable_fields(brief)
        self.assertIn("下次复用重点", text)
        self.assertIn("主体", text)
        self.assertIn("关键帧数", text)

    def test_normalize_brief_migrates_identity_anchor_rules_to_new_fields(self):
        """测试旧的 identity_anchor_rules 自动迁移到新字段"""
        brief = normalize_brief(
            {
                "subject": "黄小咕",
                "action": "跳舞",
                "scene": "广场",
                "style": "3D卡通",
                "identity_anchor_rules": [
                    "整体读成点赞大拇指体块",
                    "正面也能看到尾巴",
                    "禁止普通圆鸡化",
                    "禁止双翅膀",
                    "不要人类手指",
                ],
            }
        )

        # 检查迁移结果
        self.assertIn("整体读成点赞大拇指体块", brief["identity_structure"])
        self.assertIn("正面也能看到尾巴", brief["identity_structure"])
        self.assertIn("禁止普通圆鸡化", brief["identity_forbidden"])
        self.assertIn("禁止双翅膀", brief["identity_forbidden"])
        self.assertIn("不要人类手指", brief["identity_forbidden"])

    def test_build_prompts_uses_new_identity_fields(self):
        """测试新的 identity_structure 和 identity_forbidden 字段在 prompt 中生效"""
        brief = normalize_brief(
            {
                "subject": "黄小咕",
                "action": "跳舞",
                "scene": "广场",
                "style": "3D卡通",
                "identity_structure": ["整体读成点赞大拇指体块", "正面也能看到尾巴"],
                "identity_forbidden": ["禁止普通圆鸡化", "禁止双翅膀"],
            }
        )

        prompts = build_prompts(brief)

        # 检查 identity_board prompt
        self.assertIn("整体读成点赞大拇指体块", prompts["identity_board"])
        self.assertIn("禁止普通圆鸡化", prompts["identity_board"])

        # 检查 storyboard prompt
        self.assertIn("整体读成点赞大拇指体块", prompts["storyboard"])
        self.assertIn("禁止普通圆鸡化", prompts["storyboard"])

        # 检查 video prompt
        self.assertIn("整体读成点赞大拇指体块", prompts["video"])
        self.assertIn("禁止普通圆鸡化", prompts["video"])

    def test_build_prompts_enforces_storyboard_panel_aspect_ratio(self):
        """测试故事板 prompt 明确要求每格画幅"""
        brief = normalize_brief(
            {
                "subject": "黄小咕",
                "action": "跳舞",
                "scene": "广场",
                "style": "3D卡通",
                "ratio": "9:16",
            }
        )

        prompts = build_prompts(brief)

        # 检查故事板 prompt 中是否明确要求每格独立画幅
        self.assertIn("每一格都必须是独立的 9:16 成片画幅", prompts["storyboard"])
        self.assertIn("不要做横向长条单格", prompts["storyboard"])
        self.assertIn("不要把多格画成电影条带", prompts["storyboard"])

    def test_normalize_reference_image_compresses_large_image(self):
        """测试参考图归一化功能"""
        try:
            from PIL import Image
        except ImportError:
            self.skipTest("Pillow not installed")

        with tempfile.TemporaryDirectory() as tmp:
            # 创建一个大图
            source = Path(tmp) / "large.png"
            target = Path(tmp) / "normalized.png"

            img = Image.new("RGB", (2160, 3840), color=(255, 0, 0))
            img.save(source, "PNG")

            # 归一化
            manifest = normalize_reference_image(source, target, max_edge=1920, max_size_mb=3.0)

            # 检查结果
            self.assertTrue(target.exists())
            self.assertEqual(manifest["source_width"], 2160)
            self.assertEqual(manifest["source_height"], 3840)
            self.assertLessEqual(manifest["normalized_width"], 1920)
            self.assertLessEqual(manifest["normalized_height"], 1920)
            self.assertTrue(manifest["changed"])

    def test_normalize_reference_image_keeps_small_image(self):
        """测试小图不会被放大"""
        try:
            from PIL import Image
        except ImportError:
            self.skipTest("Pillow not installed")

        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "small.png"
            target = Path(tmp) / "normalized.png"

            img = Image.new("RGB", (800, 600), color=(0, 255, 0))
            img.save(source, "PNG")

            manifest = normalize_reference_image(source, target, max_edge=1920, max_size_mb=3.0)

            self.assertTrue(target.exists())
            self.assertEqual(manifest["normalized_width"], 800)
            self.assertEqual(manifest["normalized_height"], 600)

    def test_normalize_reference_image_handles_transparency(self):
        """测试透明通道处理"""
        try:
            from PIL import Image
        except ImportError:
            self.skipTest("Pillow not installed")

        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "transparent.png"
            target = Path(tmp) / "normalized.png"

            img = Image.new("RGBA", (1000, 1000), color=(255, 0, 0, 128))
            img.save(source, "PNG")

            manifest = normalize_reference_image(source, target, max_edge=1920, max_size_mb=3.0)

            self.assertTrue(target.exists())
            self.assertTrue(manifest["alpha_flattened"])
            self.assertTrue(manifest["changed"])


class CliSmokeTests(unittest.TestCase):
    def setUp(self):
        self.script = Path(__file__).resolve().parents[1] / "scripts" / "run_workflow.py"

    def _prepare_run(self, tmp_dir: str, brief_payload: dict[str, object]) -> tuple[dict[str, object], Path]:
        input_brief = Path(tmp_dir) / "brief.json"
        input_brief.write_text(json.dumps(brief_payload, ensure_ascii=False), encoding="utf-8")
        result = subprocess.run(
            [
                "python3",
                str(self.script),
                "prepare",
                "--brief-file",
                str(input_brief),
                "--output-root",
                tmp_dir,
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        return payload, Path(payload["run_dir"])

    def _write_refs(self, run_dir: Path, *names: str) -> None:
        for name in names:
            (run_dir / "refs" / f"{name}.png").write_bytes(SMALL_PNG)

    def test_cli_help(self):
        result = subprocess.run(
            ["python3", str(self.script), "--help"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("dreamina", result.stdout)

    def test_prepare_phase_outputs_brief_and_prompts(self):
        with tempfile.TemporaryDirectory() as tmp:
            input_brief = Path(tmp) / "brief.json"
            input_brief.write_text(
                json.dumps(
                    {
                        "subject": "橘猫",
                        "action": "在广场跳 breaking",
                        "scene": "欧洲老城石板广场",
                        "style": "电影感街头纪实",
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    "python3",
                    str(self.script),
                    "prepare",
                    "--brief-file",
                    str(input_brief),
                    "--output-root",
                    tmp,
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            run_dir = Path(payload["run_dir"])
            project_dir = Path(payload["project_dir"])
            brief = json.loads((run_dir / "brief.json").read_text(encoding="utf-8"))
            self.assertTrue((run_dir / "brief.json").exists())
            self.assertTrue((run_dir / "prompts" / "video.txt").exists())
            self.assertTrue((project_dir / "project.json").exists())
            self.assertEqual(run_dir.parent, project_dir / "runs")
            self.assertIn("storyboard_panel_count", brief)
            self.assertIn("storyboard_beats", brief)

    def test_subcommand_help_outputs_exist(self):
        for subcommand in ("validate-run", "review-run", "complete-manual-checks"):
            result = subprocess.run(
                ["python3", str(self.script), subcommand, "--help"],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(subcommand, result.stdout)

    def test_manual_checklist_flow_unblocks_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, run_dir = self._prepare_run(
                tmp,
                {
                    "project_name": "黄小咕品牌视频",
                    "project_slug": "huangxiaogu-brand",
                    "subject": "黄小咕",
                    "action": "在林间走来后定格",
                    "scene": "秋日林间",
                    "style": "3D卡通",
                    "ratio": "9:16",
                },
            )
            self._write_refs(run_dir, "original", "identity-board", "storyboard")

            validate = subprocess.run(
                ["python3", str(self.script), "validate-run", "--run-dir", str(run_dir), "--stage", "storyboard"],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(validate.returncode, 0, validate.stderr)

            run_state = json.loads((run_dir / "run_state.json").read_text(encoding="utf-8"))
            self.assertEqual(len(run_state["iterations"]), 1)

            review_before = subprocess.run(
                ["python3", str(self.script), "review-run", "--run-dir", str(run_dir)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(review_before.returncode, 0, review_before.stderr)
            review_before_payload = json.loads(review_before.stdout)
            self.assertEqual(review_before_payload["decision"], "ask_user")

            complete = subprocess.run(
                [
                    "python3",
                    str(self.script),
                    "complete-manual-checks",
                    "--run-dir",
                    str(run_dir),
                    "--check",
                    "storyboard_panel_aspect=true",
                    "--check",
                    "storyboard_panel_count=true",
                    "--check",
                    "storyboard_continuity=true",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(complete.returncode, 0, complete.stderr)

            review_after = subprocess.run(
                ["python3", str(self.script), "review-run", "--run-dir", str(run_dir)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(review_after.returncode, 0, review_after.stderr)
            review_after_payload = json.loads(review_after.stdout)
            self.assertEqual(review_after_payload["decision"], "proceed")

    def test_repeated_validation_errors_trigger_ask_user(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, run_dir = self._prepare_run(
                tmp,
                {
                    "project_name": "黄小咕品牌视频",
                    "project_slug": "huangxiaogu-brand",
                    "subject": "黄小咕",
                    "action": "在林间走来后定格",
                    "scene": "秋日林间",
                    "style": "3D卡通",
                    "ratio": "9:16",
                },
            )
            self._write_refs(run_dir, "storyboard")

            for _ in range(2):
                validate = subprocess.run(
                    ["python3", str(self.script), "validate-run", "--run-dir", str(run_dir), "--stage", "storyboard"],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(validate.returncode, 1, validate.stderr)

                complete = subprocess.run(
                    [
                        "python3",
                        str(self.script),
                        "complete-manual-checks",
                        "--run-dir",
                        str(run_dir),
                        "--check",
                        "storyboard_panel_aspect=true",
                        "--check",
                        "storyboard_panel_count=true",
                        "--check",
                        "storyboard_continuity=true",
                    ],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(complete.returncode, 0, complete.stderr)

            run_state = json.loads((run_dir / "run_state.json").read_text(encoding="utf-8"))
            self.assertGreaterEqual(len(run_state["iterations"]), 2)

            review = subprocess.run(
                ["python3", str(self.script), "review-run", "--run-dir", str(run_dir)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(review.returncode, 0, review.stderr)
            review_payload = json.loads(review.stdout)
            self.assertEqual(review_payload["decision"], "ask_user")
            self.assertIn("相同错误重复 2 次", review_payload["reason"])

    def test_validate_run_recovers_latest_storyboard_variant(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, run_dir = self._prepare_run(
                tmp,
                {
                    "project_name": "黄小咕品牌视频",
                    "project_slug": "huangxiaogu-brand",
                    "subject": "黄小咕",
                    "action": "在林间走来后定格",
                    "scene": "秋日林间",
                    "style": "3D卡通",
                    "ratio": "9:16",
                },
            )
            self._write_refs(run_dir, "original", "identity-board")
            (run_dir / "refs" / "storyboard-v3.png").write_bytes(SMALL_PNG)
            (run_dir / "refs" / "storyboard-v4.png").write_bytes(SMALL_PNG)
            (run_dir / "refs" / "storyboard-v5-annotated.png").write_bytes(SMALL_PNG)

            validate = subprocess.run(
                ["python3", str(self.script), "validate-run", "--run-dir", str(run_dir), "--stage", "storyboard"],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(validate.returncode, 0, validate.stderr)
            payload = json.loads(validate.stdout)
            self.assertTrue((run_dir / "refs" / "storyboard.png").exists())
            self.assertTrue((run_dir / "validation_reports" / "storyboard.json").exists())
            materialize_action = next(
                action for action in payload["recovery_actions"] if action["action"] == "materialize_standard_reference"
            )
            self.assertEqual(materialize_action["source"], str(run_dir / "refs" / "storyboard-v4.png"))

    def test_submit_video_dry_run_prefers_clean_for_video_storyboard(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, run_dir = self._prepare_run(
                tmp,
                {
                    "project_name": "黄小咕品牌视频",
                    "project_slug": "huangxiaogu-brand",
                    "subject": "黄小咕",
                    "action": "在林间走来后定格",
                    "scene": "秋日林间",
                    "style": "3D卡通",
                    "ratio": "9:16",
                },
            )
            self._write_refs(run_dir, "original", "identity-source", "storyboard")
            (run_dir / "refs" / "storyboard.clean-for-video-v2.png").write_bytes(SMALL_PNG)
            (run_dir / "refs" / "storyboard-v5-annotated.png").write_bytes(SMALL_PNG)

            validate = subprocess.run(
                ["python3", str(self.script), "validate-run", "--run-dir", str(run_dir), "--stage", "storyboard"],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(validate.returncode, 0, validate.stderr)
            complete = subprocess.run(
                ["python3", str(self.script), "complete-manual-checks", "--run-dir", str(run_dir), "--all-passed"],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(complete.returncode, 0, complete.stderr)
            review = subprocess.run(
                ["python3", str(self.script), "review-run", "--run-dir", str(run_dir)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(review.returncode, 0, review.stderr)

            dry_run = subprocess.run(
                ["python3", str(self.script), "submit-video", "--run-dir", str(run_dir), "--dry-run"],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(dry_run.returncode, 0, dry_run.stderr)
            payload = json.loads(dry_run.stdout)
            self.assertEqual(payload["resolved_references"]["storyboard"], str(run_dir / "refs" / "storyboard.clean-for-video-v2.png"))
            self.assertTrue(payload["validation_gate_status"]["can_submit"])

    def test_review_run_recovers_missing_run_state_and_legacy_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, run_dir = self._prepare_run(
                tmp,
                {
                    "project_name": "黄小咕品牌视频",
                    "project_slug": "huangxiaogu-brand",
                    "subject": "黄小咕",
                    "action": "在林间走来后定格",
                    "scene": "秋日林间",
                    "style": "3D卡通",
                    "ratio": "9:16",
                },
            )
            self._write_refs(run_dir, "original", "identity-board", "storyboard")
            legacy_report = {
                "stage": "storyboard",
                "passed": True,
                "score": 1.0,
                "issues": [],
                "manual_checks": [
                    {"id": "storyboard_panel_aspect", "description": "ok", "checked": True},
                    {"id": "storyboard_panel_count", "description": "ok", "checked": True},
                    {"id": "storyboard_continuity", "description": "ok", "checked": True},
                ],
            }
            (run_dir / "validation_report_storyboard.json").write_text(
                json.dumps(legacy_report, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            (run_dir / "run_state.json").unlink()

            review = subprocess.run(
                ["python3", str(self.script), "review-run", "--run-dir", str(run_dir)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(review.returncode, 0, review.stderr)
            payload = json.loads(review.stdout)
            self.assertEqual(payload["decision"], "proceed")
            self.assertTrue((run_dir / "run_state.json").exists())
            self.assertEqual(payload["recovery_actions"][0]["action"], "recover_validation_report")


class RoutingTextTests(unittest.TestCase):
    def test_dreamina_cli_is_scoped_to_low_level_operations(self):
        skill_text = Path("/Users/a123/.openclaw/skills/dreamina-cli/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("inspect Dreamina CLI help", skill_text)
        self.assertIn("query a submit_id result", skill_text)
        self.assertNotIn("image/video generation", skill_text)
        self.assertNotIn("Use this skill only when the user explicitly names `即梦`, `Dreamina`, `dreamina`, `Seedance`", skill_text)

    def test_dreamina_reference_video_is_default_entry(self):
        skill_text = Path("/Users/a123/.openclaw/skills/dreamina-reference-video/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("调用即梦生成视频", skill_text)
        self.assertIn("做一个新的小视频", skill_text)
        self.assertIn("dreamina-cli 只可作为本 skill 内部调用", skill_text)


if __name__ == "__main__":
    unittest.main()
