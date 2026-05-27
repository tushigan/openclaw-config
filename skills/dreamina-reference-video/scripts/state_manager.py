#!/usr/bin/env python3
"""状态管理模块：处理 project.json 和 run_state.json 的读写和更新"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


def now_iso() -> str:
    """返回当前时间的 ISO 格式字符串"""
    return datetime.now().astimezone().isoformat(timespec="seconds")


def compute_prompt_hash(prompt: str) -> str:
    """计算 prompt 的哈希值"""
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:16]


@dataclass
class Constraint:
    """约束规则"""
    id: str
    type: str  # must_have, must_not_have, prefer
    description: str
    strength: float = 0.9
    applies_to: list[str] = field(default_factory=lambda: ["identity_board", "storyboard", "video"])
    validation_mode: str = "manual"  # manual, deterministic

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "description": self.description,
            "strength": self.strength,
            "applies_to": self.applies_to,
            "validation_mode": self.validation_mode,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Constraint:
        return cls(
            id=data["id"],
            type=data["type"],
            description=data["description"],
            strength=data.get("strength", 0.9),
            applies_to=data.get("applies_to", ["identity_board", "storyboard", "video"]),
            validation_mode=data.get("validation_mode", "manual"),
        )


@dataclass
class ProjectConfig:
    """项目配置"""
    schema_version: int = 2
    project_id: str = ""
    project_name: str = ""
    project_slug: str = ""
    project_dir: str = ""

    # 默认配置
    defaults: dict[str, Any] = field(default_factory=dict)

    # 约束规则
    constraints: dict[str, list[dict[str, Any]]] = field(default_factory=lambda: {
        "must_have": [],
        "must_not_have": [],
        "prefer": []
    })

    # 验证规则
    validation_rules: dict[str, list[dict[str, Any]]] = field(default_factory=lambda: {
        "reference_system": [],
        "storyboard": [],
        "video": []
    })

    # 迭代策略
    iteration_strategy: dict[str, Any] = field(default_factory=lambda: {
        "max_iterations": 3,
        "max_same_error_repeats": 2,
        "improvement_threshold": 0.15,
        "ask_user_on_manual_checks": True
    })

    # 关键文件
    canonical_files: dict[str, str] = field(default_factory=dict)

    # 项目状态
    state: dict[str, Any] = field(default_factory=lambda: {
        "status": "ready_for_ref_generation",
        "current_phase": "prepare",
        "latest_run_id": "",
        "latest_run_dir": "",
        "updated_at": ""
    })

    # 运行历史（只存摘要）
    runs: list[dict[str, Any]] = field(default_factory=list)

    # 元数据
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "schema_version": self.schema_version,
            "project_id": self.project_id,
            "project_name": self.project_name,
            "project_slug": self.project_slug,
            "project_dir": self.project_dir,
            "defaults": self.defaults,
            "constraints": self.constraints,
            "validation_rules": self.validation_rules,
            "iteration_strategy": self.iteration_strategy,
            "canonical_files": self.canonical_files,
            "state": self.state,
            "runs": self.runs,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        payload.update({
            "status": self.state.get("status", ""),
            "current_phase": self.state.get("current_phase", ""),
            "latest_run_id": self.state.get("latest_run_id", ""),
            "latest_run_dir": self.state.get("latest_run_dir", ""),
        })
        return payload

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProjectConfig:
        """从字典创建 ProjectConfig，自动处理版本升级"""
        schema_version = data.get("schema_version", 1)

        # 如果是旧版本，自动升级
        if schema_version == 1:
            data = cls._upgrade_from_v1(data)

        return cls(
            schema_version=data.get("schema_version", 2),
            project_id=data.get("project_id", ""),
            project_name=data.get("project_name", ""),
            project_slug=data.get("project_slug", ""),
            project_dir=data.get("project_dir", ""),
            defaults=data.get("defaults", {}),
            constraints=data.get("constraints", {
                "must_have": [],
                "must_not_have": [],
                "prefer": []
            }),
            validation_rules=data.get("validation_rules", {
                "reference_system": [],
                "storyboard": [],
                "video": []
            }),
            iteration_strategy=data.get("iteration_strategy", {
                "max_iterations": 3,
                "max_same_error_repeats": 2,
                "improvement_threshold": 0.15,
                "ask_user_on_manual_checks": True
            }),
            canonical_files=data.get("canonical_files", {}),
            state=data.get("state", {
                "status": data.get("status", "ready_for_ref_generation"),
                "current_phase": data.get("current_phase", "prepare"),
                "latest_run_id": data.get("latest_run_id", ""),
                "latest_run_dir": data.get("latest_run_dir", ""),
                "updated_at": data.get("updated_at", "")
            }),
            runs=data.get("runs", []),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
        )

    @classmethod
    def _upgrade_from_v1(cls, data: dict[str, Any]) -> dict[str, Any]:
        """从 v1 升级到 v2"""
        upgraded = data.copy()
        upgraded["schema_version"] = 2

        # 提取 defaults
        if "defaults" not in upgraded:
            upgraded["defaults"] = {
                "ratio": data.get("ratio", "16:9"),
                "duration": data.get("duration", 5),
                "quality_tier": data.get("quality_tier", "draft"),
                "storyboard_strategy": data.get("storyboard_strategy", "auto_beats"),
                "normalize_references": data.get("normalize_references", True),
            }

        # 转换约束
        if "constraints" not in upgraded:
            constraints = {
                "must_have": [],
                "must_not_have": [],
                "prefer": []
            }

            # 从 identity_structure 和 identity_forbidden 迁移
            identity_structure = data.get("identity_structure", [])
            identity_forbidden = data.get("identity_forbidden", [])

            for idx, desc in enumerate(identity_structure):
                constraints["must_have"].append({
                    "id": f"structure-{idx}",
                    "type": "must_have",
                    "description": desc,
                    "strength": 0.9,
                    "applies_to": ["identity_board", "storyboard", "video"],
                    "validation_mode": "manual"
                })

            for idx, desc in enumerate(identity_forbidden):
                constraints["must_not_have"].append({
                    "id": f"forbidden-{idx}",
                    "type": "must_not_have",
                    "description": desc,
                    "strength": 0.9,
                    "applies_to": ["identity_board", "storyboard", "video"],
                    "validation_mode": "manual"
                })

            upgraded["constraints"] = constraints

        # 提取 state
        if "state" not in upgraded:
            upgraded["state"] = {
                "status": data.get("status", "ready_for_ref_generation"),
                "current_phase": data.get("current_phase", "prepare"),
                "latest_run_id": data.get("latest_run_id", ""),
                "latest_run_dir": data.get("latest_run_dir", ""),
                "updated_at": data.get("updated_at", "")
            }

        return upgraded


@dataclass
class RunState:
    """单轮运行状态"""
    schema_version: int = 1
    run_id: str = ""
    project_id: str = ""
    stage: str = "prepare"  # prepare, generate_refs, submit_video, fetch_result
    status: str = "pending"
    created_at: str = ""
    updated_at: str = ""

    # 配置快照
    config_snapshot: dict[str, Any] = field(default_factory=dict)

    # 文件路径
    prompt_files: dict[str, str] = field(default_factory=dict)
    reference_files: dict[str, str] = field(default_factory=dict)
    artifacts: dict[str, str] = field(default_factory=dict)

    # 风险分析报告
    prompt_risk_report: dict[str, Any] = field(default_factory=dict)

    # 验证报告
    validation_report: dict[str, Any] = field(default_factory=dict)

    # 下一步动作
    next_action: dict[str, str] = field(default_factory=lambda: {
        "decision": "continue",
        "reason": ""
    })

    # 迭代历史
    iterations: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "project_id": self.project_id,
            "stage": self.stage,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "config_snapshot": self.config_snapshot,
            "prompt_files": self.prompt_files,
            "reference_files": self.reference_files,
            "artifacts": self.artifacts,
            "prompt_risk_report": self.prompt_risk_report,
            "validation_report": self.validation_report,
            "next_action": self.next_action,
            "iterations": self.iterations,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RunState:
        return cls(
            schema_version=data.get("schema_version", 1),
            run_id=data.get("run_id", ""),
            project_id=data.get("project_id", ""),
            stage=data.get("stage", "prepare"),
            status=data.get("status", "pending"),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            config_snapshot=data.get("config_snapshot", {}),
            prompt_files=data.get("prompt_files", {}),
            reference_files=data.get("reference_files", {}),
            artifacts=data.get("artifacts", {}),
            prompt_risk_report=data.get("prompt_risk_report", {}),
            validation_report=data.get("validation_report", {}),
            next_action=data.get("next_action", {"decision": "continue", "reason": ""}),
            iterations=data.get("iterations", []),
        )

    def add_iteration(
        self,
        artifact_type: str,
        prompt: str,
        issues: list[str] | None = None,
        validation_score: float = 0.0,
        cost: float | None = None,
    ) -> None:
        """添加一次迭代记录"""
        version = len(self.iterations) + 1
        self.iterations.append({
            "version": version,
            "artifact_type": artifact_type,
            "prompt_hash": compute_prompt_hash(prompt),
            "issues": issues or [],
            "validation_score": validation_score,
            "cost": cost,
            "created_at": now_iso(),
        })


class StateManager:
    """状态管理器"""

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.project_file = project_dir / "project.json"

    def load_project(self) -> ProjectConfig | None:
        """加载项目配置"""
        if not self.project_file.exists():
            return None
        data = json.loads(self.project_file.read_text(encoding="utf-8"))
        return ProjectConfig.from_dict(data)

    def save_project(self, config: ProjectConfig) -> None:
        """保存项目配置"""
        config.updated_at = now_iso()
        config.state["updated_at"] = config.updated_at
        self.project_dir.mkdir(parents=True, exist_ok=True)
        self.project_file.write_text(
            json.dumps(config.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

    def create_project(
        self,
        project_id: str,
        project_name: str,
        project_slug: str,
        defaults: dict[str, Any] | None = None,
    ) -> ProjectConfig:
        """创建新项目"""
        now = now_iso()
        config = ProjectConfig(
            project_id=project_id,
            project_name=project_name,
            project_slug=project_slug,
            project_dir=str(self.project_dir),
            defaults=defaults or {},
            created_at=now,
            updated_at=now,
        )
        config.state["updated_at"] = now
        self.save_project(config)
        return config

    def update_project_state(
        self,
        status: str | None = None,
        current_phase: str | None = None,
        latest_run_id: str | None = None,
        latest_run_dir: str | None = None,
    ) -> None:
        """更新项目状态"""
        config = self.load_project()
        if config is None:
            raise ValueError("项目不存在")

        if status is not None:
            config.state["status"] = status
        if current_phase is not None:
            config.state["current_phase"] = current_phase
        if latest_run_id is not None:
            config.state["latest_run_id"] = latest_run_id
        if latest_run_dir is not None:
            config.state["latest_run_dir"] = latest_run_dir

        config.state["updated_at"] = now_iso()
        self.save_project(config)

    def add_run_record(self, run_record: dict[str, Any]) -> None:
        """添加运行记录"""
        config = self.load_project()
        if config is None:
            raise ValueError("项目不存在")

        run_id = run_record.get("run_id")
        existing = next((r for r in config.runs if r.get("run_id") == run_id), None)

        if existing is None:
            run_record["created_at"] = now_iso()
            config.runs.append(run_record)
        else:
            created_at = existing.get("created_at", now_iso())
            existing.update(run_record)
            existing["created_at"] = created_at

        run_record["updated_at"] = now_iso()
        self.save_project(config)

    def load_run_state(self, run_dir: Path) -> RunState | None:
        """加载运行状态"""
        run_state_file = run_dir / "run_state.json"
        if not run_state_file.exists():
            return None
        data = json.loads(run_state_file.read_text(encoding="utf-8"))
        return RunState.from_dict(data)

    def save_run_state(self, run_dir: Path, state: RunState) -> None:
        """保存运行状态"""
        state.updated_at = now_iso()
        run_state_file = run_dir / "run_state.json"
        run_state_file.write_text(
            json.dumps(state.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

    def create_run_state(
        self,
        run_dir: Path,
        run_id: str,
        project_id: str,
        config_snapshot: dict[str, Any],
    ) -> RunState:
        """创建新的运行状态"""
        now = now_iso()
        state = RunState(
            run_id=run_id,
            project_id=project_id,
            stage="prepare",
            status="pending",
            created_at=now,
            updated_at=now,
            config_snapshot=config_snapshot,
        )
        self.save_run_state(run_dir, state)
        return state

    def update_run_state(
        self,
        run_dir: Path,
        stage: str | None = None,
        status: str | None = None,
        prompt_files: dict[str, str] | None = None,
        reference_files: dict[str, str] | None = None,
        artifacts: dict[str, str] | None = None,
        prompt_risk_report: dict[str, Any] | None = None,
        validation_report: dict[str, Any] | None = None,
        next_action: dict[str, str] | None = None,
    ) -> RunState:
        """更新运行状态"""
        state = self.load_run_state(run_dir)
        if state is None:
            raise ValueError(f"运行状态不存在: {run_dir}")

        if stage is not None:
            state.stage = stage
        if status is not None:
            state.status = status
        if prompt_files is not None:
            state.prompt_files.update(prompt_files)
        if reference_files is not None:
            state.reference_files.update(reference_files)
        if artifacts is not None:
            state.artifacts.update(artifacts)
        if prompt_risk_report is not None:
            state.prompt_risk_report = prompt_risk_report
        if validation_report is not None:
            state.validation_report = validation_report
        if next_action is not None:
            state.next_action = next_action

        self.save_run_state(run_dir, state)
        return state
