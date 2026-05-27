#!/usr/bin/env python3
"""验证引擎：实现 deterministic 和 manual 验证规则"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    from PIL import Image
except ImportError:
    Image = None


@dataclass
class ValidationIssue:
    """验证问题"""
    rule_id: str
    severity: str  # error, warning, info
    message: str
    validation_mode: str  # deterministic, manual
    auto_retry: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "severity": self.severity,
            "message": self.message,
            "validation_mode": self.validation_mode,
            "auto_retry": self.auto_retry,
        }


@dataclass
class ValidationReport:
    """验证报告"""
    stage: str  # reference_system, storyboard, video
    passed: bool = True
    score: float = 1.0
    issues: list[ValidationIssue] = field(default_factory=list)
    manual_checks: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage": self.stage,
            "passed": self.passed,
            "score": self.score,
            "issues": [issue.to_dict() for issue in self.issues],
            "manual_checks": self.manual_checks,
        }

    def add_issue(self, issue: ValidationIssue) -> None:
        """添加验证问题"""
        self.issues.append(issue)
        if issue.severity == "error":
            self.passed = False

    def calculate_score(self) -> float:
        """计算验证分数"""
        if not self.issues:
            return 1.0

        error_count = sum(1 for issue in self.issues if issue.severity == "error")
        warning_count = sum(1 for issue in self.issues if issue.severity == "warning")

        # 简单的加权计算：error -0.3, warning -0.1
        penalty = error_count * 0.3 + warning_count * 0.1
        score = max(0.0, 1.0 - penalty)
        self.score = score
        return score


class DeterministicValidator:
    """确定性验证器：检查文件存在、尺寸、比例等"""

    def __init__(self, run_dir: Path, brief: dict[str, Any]):
        self.run_dir = run_dir
        self.brief = brief

    def validate_reference_system(self) -> ValidationReport:
        """验证参考图系统"""
        report = ValidationReport(stage="reference_system")

        # 检查必需的参考图文件
        required_refs = ["original", "storyboard"]
        identity_strategy = self.brief.get("identity_strategy")

        if identity_strategy != "reuse_exact":
            required_refs.append("identity_board")

        if self.brief.get("existing_references", {}).get("identity_source"):
            required_refs.append("identity_source")

        ref_map = {
            "original": "original.png",
            "identity_source": "identity-source.png",
            "identity_board": "identity-board.png",
            "storyboard": "storyboard.png",
        }

        for ref_key in required_refs:
            ref_file = self.run_dir / "refs" / ref_map[ref_key]
            if not ref_file.exists():
                report.add_issue(ValidationIssue(
                    rule_id=f"ref_missing_{ref_key}",
                    severity="error",
                    message=f"缺少必需的参考图: {ref_map[ref_key]}",
                    validation_mode="deterministic",
                    auto_retry=False,
                ))

        # 检查参考图尺寸
        if Image is not None:
            for ref_key in required_refs:
                ref_file = self.run_dir / "refs" / ref_map[ref_key]
                if ref_file.exists():
                    try:
                        img = Image.open(ref_file)
                        width, height = img.size

                        # 检查是否太小
                        if width < 512 or height < 512:
                            report.add_issue(ValidationIssue(
                                rule_id=f"ref_too_small_{ref_key}",
                                severity="warning",
                                message=f"参考图 {ref_map[ref_key]} 尺寸过小: {width}x{height}",
                                validation_mode="deterministic",
                                auto_retry=False,
                            ))

                        # 检查是否太大（超过归一化阈值）
                        if width > 4096 or height > 4096:
                            report.add_issue(ValidationIssue(
                                rule_id=f"ref_too_large_{ref_key}",
                                severity="warning",
                                message=f"参考图 {ref_map[ref_key]} 尺寸过大: {width}x{height}，可能导致超时",
                                validation_mode="deterministic",
                                auto_retry=False,
                            ))
                    except Exception as e:
                        report.add_issue(ValidationIssue(
                            rule_id=f"ref_invalid_{ref_key}",
                            severity="error",
                            message=f"参考图 {ref_map[ref_key]} 无法读取: {e}",
                            validation_mode="deterministic",
                            auto_retry=False,
                        ))

        # 检查 prompt 文件
        prompt_files = ["original.txt", "identity-board.txt", "storyboard.txt", "video.txt"]
        for prompt_file in prompt_files:
            prompt_path = self.run_dir / "prompts" / prompt_file
            if not prompt_path.exists():
                report.add_issue(ValidationIssue(
                    rule_id=f"prompt_missing_{prompt_file}",
                    severity="error",
                    message=f"缺少提示词文件: {prompt_file}",
                    validation_mode="deterministic",
                    auto_retry=False,
                ))

        report.calculate_score()
        return report

    def validate_storyboard(self) -> ValidationReport:
        """验证故事板"""
        report = ValidationReport(stage="storyboard")

        # 检查故事板文件存在
        storyboard_file = self.run_dir / "refs" / "storyboard.png"
        if not storyboard_file.exists():
            report.add_issue(ValidationIssue(
                rule_id="storyboard_missing",
                severity="error",
                message="故事板文件不存在",
                validation_mode="deterministic",
                auto_retry=False,
            ))
            report.calculate_score()
            return report

        # 检查故事板关键依赖是否齐套
        supporting_refs = {
            "original": self.run_dir / "refs" / "original.png",
        }
        identity_source = self.run_dir / "refs" / "identity-source.png"
        identity_board = self.run_dir / "refs" / "identity-board.png"
        if self.brief.get("existing_references", {}).get("identity_source"):
            supporting_refs["identity_source"] = identity_source
        elif identity_source.exists():
            supporting_refs["identity_source"] = identity_source
        else:
            supporting_refs["identity_board"] = identity_board

        for ref_name, ref_path in supporting_refs.items():
            if not ref_path.exists():
                report.add_issue(ValidationIssue(
                    rule_id=f"storyboard_support_missing_{ref_name}",
                    severity="error",
                    message=f"故事板依赖文件缺失: {ref_path.name}",
                    validation_mode="deterministic",
                    auto_retry=False,
                ))

        storyboard_prompt = self.run_dir / "prompts" / "storyboard.txt"
        if not storyboard_prompt.exists():
            report.add_issue(ValidationIssue(
                rule_id="storyboard_prompt_missing",
                severity="error",
                message="故事板提示词文件不存在",
                validation_mode="deterministic",
                auto_retry=False,
            ))

        # 检查故事板可读性和最小尺寸
        if Image is not None:
            try:
                img = Image.open(storyboard_file)
                width, height = img.size

                if width < 512 or height < 512:
                    report.add_issue(ValidationIssue(
                        rule_id="storyboard_too_small",
                        severity="warning",
                        message=f"故事板尺寸过小: {width}x{height}",
                        validation_mode="deterministic",
                        auto_retry=False,
                    ))

            except Exception as e:
                report.add_issue(ValidationIssue(
                    rule_id="storyboard_invalid",
                    severity="error",
                    message=f"故事板文件无法读取: {e}",
                    validation_mode="deterministic",
                    auto_retry=False,
                ))

        # 添加 manual 检查项
        panel_count = self.brief.get("storyboard_panel_count", 5)
        ratio = self.brief.get("ratio", "16:9")
        report.manual_checks.append({
            "id": "storyboard_panel_aspect",
            "description": f"故事板每一格是否都是 {ratio} 画幅？（不是横向长条）",
            "checked": False,
        })
        report.manual_checks.append({
            "id": "storyboard_panel_count",
            "description": f"故事板是否有 {panel_count} 格？",
            "checked": False,
        })
        report.manual_checks.append({
            "id": "storyboard_continuity",
            "description": "故事板是否保持连续空间？（不是每格重造世界）",
            "checked": False,
        })

        report.calculate_score()
        return report

    def validate_video(self) -> ValidationReport:
        """验证视频"""
        report = ValidationReport(stage="video")

        # 检查 dreamina 结果文件
        result_file = self.run_dir / "dreamina" / "result.json"
        if not result_file.exists():
            report.add_issue(ValidationIssue(
                rule_id="video_result_missing",
                severity="error",
                message="视频结果文件不存在",
                validation_mode="deterministic",
                auto_retry=False,
            ))

        # 检查 submit_id
        submit_id_file = self.run_dir / "dreamina" / "submit_id.txt"
        if not submit_id_file.exists():
            report.add_issue(ValidationIssue(
                rule_id="video_submit_id_missing",
                severity="error",
                message="视频提交 ID 不存在",
                validation_mode="deterministic",
                auto_retry=False,
            ))

        # 添加 manual 检查项
        report.manual_checks.append({
            "id": "video_character_consistency",
            "description": "视频中角色身份是否和参考图一致？",
            "checked": False,
        })
        report.manual_checks.append({
            "id": "video_storyboard_match",
            "description": "视频是否按照故事板的镜头顺序和动作推进？",
            "checked": False,
        })

        report.calculate_score()
        return report


class ManualChecklistGenerator:
    """人工检查清单生成器"""

    def __init__(self, brief: dict[str, Any]):
        self.brief = brief

    def generate_reference_checklist(self) -> list[dict[str, Any]]:
        """生成参考图检查清单"""
        checklist = []

        # 基础检查
        checklist.append({
            "id": "ref_style_consistency",
            "description": "原图、身份板、故事板的风格是否一致？",
            "category": "style",
            "checked": False,
        })

        # 角色一致性检查
        identity_reference = "identity-source.png" if self.brief.get("existing_references", {}).get("identity_source") else "identity-board.png"
        checklist.append({
            "id": "character_consistency",
            "description": f"故事板中的角色是否和 {identity_reference} 一致？（脸、服装、比例、姿态）",
            "category": "character",
            "checked": False,
        })

        # IP 约束检查
        identity_structure = self.brief.get("identity_structure", [])
        identity_forbidden = self.brief.get("identity_forbidden", [])

        if identity_structure:
            for idx, constraint in enumerate(identity_structure):
                checklist.append({
                    "id": f"structure_{idx}",
                    "description": f"结构真相：{constraint}",
                    "category": "structure",
                    "checked": False,
                })

        if identity_forbidden:
            for idx, constraint in enumerate(identity_forbidden):
                checklist.append({
                    "id": f"forbidden_{idx}",
                    "description": f"禁止变形：{constraint}（应该没有出现）",
                    "category": "forbidden",
                    "checked": False,
                })

        return checklist

    def generate_storyboard_checklist(self) -> list[dict[str, Any]]:
        """生成故事板检查清单"""
        checklist = []

        ratio = self.brief.get("ratio", "16:9")
        panel_count = self.brief.get("storyboard_panel_count", 5)

        checklist.append({
            "id": "storyboard_panel_aspect",
            "description": f"每一格是否都是 {ratio} 画幅？（不是横向长条）",
            "category": "format",
            "checked": False,
        })

        checklist.append({
            "id": "storyboard_panel_count",
            "description": f"是否有 {panel_count} 格？",
            "category": "format",
            "checked": False,
        })

        checklist.append({
            "id": "storyboard_annotations",
            "description": "是否有动态箭头和文字说明？",
            "category": "format",
            "checked": False,
        })

        return checklist

    def generate_video_checklist(self) -> list[dict[str, Any]]:
        """生成视频检查清单"""
        checklist = []

        checklist.append({
            "id": "video_character_consistency",
            "description": "角色身份是否和参考图一致？",
            "category": "character",
            "checked": False,
        })

        checklist.append({
            "id": "video_storyboard_match",
            "description": "是否按照故事板的镜头顺序和动作推进？",
            "category": "storyboard",
            "checked": False,
        })

        checklist.append({
            "id": "video_style_match",
            "description": "风格是否和原图一致？",
            "category": "style",
            "checked": False,
        })

        return checklist


def validate_run(run_dir: Path, brief: dict[str, Any], stage: str) -> ValidationReport:
    """
    验证运行结果

    Args:
        run_dir: 运行目录
        brief: brief 配置
        stage: 验证阶段（reference_system, storyboard, video）

    Returns:
        验证报告
    """
    validator = DeterministicValidator(run_dir, brief)

    if stage == "reference_system":
        return validator.validate_reference_system()
    elif stage == "storyboard":
        return validator.validate_storyboard()
    elif stage == "video":
        return validator.validate_video()
    else:
        raise ValueError(f"未知的验证阶段: {stage}")
