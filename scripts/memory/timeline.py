#!/usr/bin/env python3
"""
海报项目时间线记录系统

功能：
1. 记录每个工作流节点的时间点
2. 计算每个阶段的耗时
3. 区分等待时间 vs 执行时间
4. 支持导出为飞书文档格式
5. 集成到记忆系统的任务层级
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List

# 添加 lib 路径
sys.path.insert(0, str(Path(__file__).parent / "lib"))

from utils import get_timestamp, read_json, write_json, get_projects_root

# 时间线节点定义
TIMELINE_NODES = {
    "project_init": {
        "name": "项目立项",
        "description": "项目分级和基础信息收集",
        "category": "setup"
    },
    "requirement_collected": {
        "name": "需求收集完成",
        "description": "品牌档案查询、蒸馏卡检查完成",
        "category": "preparation"
    },
    "copywriting_start": {
        "name": "文案策划开始",
        "description": "派发 copywriter subagent",
        "category": "execution"
    },
    "copywriting_done": {
        "name": "文案策划完成",
        "description": "文案策略和具体文案生成完毕",
        "category": "execution"
    },
    "copywriting_approval_request": {
        "name": "文案审批请求",
        "description": "向客户发送文案审批请求",
        "category": "waiting"
    },
    "copywriting_approved": {
        "name": "文案审批通过",
        "description": "客户确认文案",
        "category": "approval"
    },
    "creative_direction_start": {
        "name": "创意方向开始",
        "description": "生成创意方向描述",
        "category": "execution"
    },
    "creative_direction_done": {
        "name": "创意方向完成",
        "description": "创意方向文档生成完毕",
        "category": "execution"
    },
    "creative_approval_request": {
        "name": "创意方向审批请求",
        "description": "向双审判断者发送审批请求",
        "category": "waiting"
    },
    "creative_approved": {
        "name": "创意方向审批通过",
        "description": "文案+设计判断者确认创意方向",
        "category": "approval"
    },
    "generation_start": {
        "name": "生图开始",
        "description": "派发 design subagent 生图",
        "category": "execution"
    },
    "generation_done": {
        "name": "生图完成",
        "description": "海报图片生成完毕",
        "category": "execution"
    },
    "design_approval_request": {
        "name": "设计审批请求",
        "description": "向客户发送设计审批请求",
        "category": "waiting"
    },
    "design_approved": {
        "name": "设计审批通过",
        "description": "客户确认设计",
        "category": "approval"
    },
    "advanced_approval_request": {
        "name": "高级审批请求",
        "description": "向创意总监/老板发送审批请求（仅A/S级）",
        "category": "waiting"
    },
    "advanced_approved": {
        "name": "高级审批通过",
        "description": "创意总监/老板确认（仅A/S级）",
        "category": "approval"
    },
    "delivery": {
        "name": "交付完成",
        "description": "成品图发送给客户",
        "category": "delivery"
    },
    "project_completed": {
        "name": "项目完结",
        "description": "复盘报告生成，项目归档",
        "category": "completion"
    }
}

# 问题类型定义
ISSUE_TYPES = {
    "approval_delay": "审批延迟（人为因素）",
    "technical_error": "技术错误（AI/系统问题）",
    "revision_request": "修改请求（客户反馈）",
    "resource_unavailable": "资源不可用（品牌资产缺失等）",
    "communication_delay": "沟通延迟",
    "other": "其他"
}


class TimelineRecorder:
    """时间线记录器"""

    def __init__(self, task_id: str):
        """
        初始化时间线记录器

        Args:
            task_id: 任务 ID
        """
        self.task_id = task_id
        self.task_dir = self._find_task_dir()
        self.timeline_file = self.task_dir / "timeline.json"
        self.timeline_data = self._load_timeline()

    def _find_task_dir(self) -> Path:
        """查找任务目录"""
        projects_root = get_projects_root()

        for client_dir in projects_root.iterdir():
            if not client_dir.is_dir() or client_dir.name.startswith("_"):
                continue

            for brand_dir in client_dir.iterdir():
                if not brand_dir.is_dir() or brand_dir.name.startswith("_"):
                    continue

                for project_dir in brand_dir.iterdir():
                    if not project_dir.is_dir():
                        continue

                    task_dir = project_dir / "tasks" / self.task_id
                    if task_dir.exists():
                        return task_dir

        raise FileNotFoundError(f"任务目录不存在: {self.task_id}")

    def _load_timeline(self) -> dict:
        """加载时间线数据"""
        if self.timeline_file.exists():
            return read_json(self.timeline_file)

        # 初始化时间线结构
        return {
            "task_id": self.task_id,
            "created_at": get_timestamp(),
            "nodes": {},  # {node_name: {timestamp, notes, metadata}}
            "issues": [],  # [{type, description, timestamp, resolved_at, impact_minutes}]
            "revisions": []  # [{stage, reason, requested_at, completed_at}]
        }

    def _save_timeline(self):
        """保存时间线数据"""
        write_json(self.timeline_file, self.timeline_data)

    def record_node(self, node_name: str, notes: str = "", metadata: dict = None):
        """
        记录时间节点

        Args:
            node_name: 节点名称（必须在 TIMELINE_NODES 中定义）
            notes: 备注说明
            metadata: 额外元数据（如审批者、子任务ID等）
        """
        if node_name not in TIMELINE_NODES:
            raise ValueError(f"未定义的节点: {node_name}")

        timestamp = get_timestamp()

        self.timeline_data["nodes"][node_name] = {
            "timestamp": timestamp,
            "notes": notes,
            "metadata": metadata or {}
        }

        self._save_timeline()

        print(f"✅ 时间节点已记录: {TIMELINE_NODES[node_name]['name']} ({timestamp})")

    def record_issue(self, issue_type: str, description: str, impact_minutes: int = 0):
        """
        记录问题/延迟

        Args:
            issue_type: 问题类型（approval_delay/technical_error等）
            description: 问题描述
            impact_minutes: 影响时长（分钟）
        """
        if issue_type not in ISSUE_TYPES:
            raise ValueError(f"未定义的问题类型: {issue_type}")

        issue = {
            "issue_id": f"ISSUE-{len(self.timeline_data['issues']) + 1}",
            "type": issue_type,
            "type_name": ISSUE_TYPES[issue_type],
            "description": description,
            "timestamp": get_timestamp(),
            "resolved_at": None,
            "impact_minutes": impact_minutes
        }

        self.timeline_data["issues"].append(issue)
        self._save_timeline()

        print(f"⚠️ 问题已记录: {ISSUE_TYPES[issue_type]} - {description}")

    def resolve_issue(self, issue_id: str):
        """
        标记问题已解决

        Args:
            issue_id: 问题 ID
        """
        for issue in self.timeline_data["issues"]:
            if issue["issue_id"] == issue_id:
                issue["resolved_at"] = get_timestamp()
                self._save_timeline()
                print(f"✅ 问题已解决: {issue_id}")
                return

        raise ValueError(f"问题不存在: {issue_id}")

    def record_revision(self, stage: str, reason: str):
        """
        记录修改请求

        Args:
            stage: 修改阶段（copywriting/creative_direction/design）
            reason: 修改原因
        """
        revision = {
            "revision_id": f"REV-{len(self.timeline_data['revisions']) + 1}",
            "stage": stage,
            "reason": reason,
            "requested_at": get_timestamp(),
            "completed_at": None
        }

        self.timeline_data["revisions"].append(revision)
        self._save_timeline()

        print(f"📝 修改请求已记录: {stage} - {reason}")

    def complete_revision(self, revision_id: str):
        """
        标记修改完成

        Args:
            revision_id: 修改 ID
        """
        for revision in self.timeline_data["revisions"]:
            if revision["revision_id"] == revision_id:
                revision["completed_at"] = get_timestamp()
                self._save_timeline()
                print(f"✅ 修改完成: {revision_id}")
                return

        raise ValueError(f"修改记录不存在: {revision_id}")

    def calculate_durations(self) -> dict:
        """
        计算各阶段耗时

        Returns:
            各阶段耗时统计（分钟）
        """
        nodes = self.timeline_data["nodes"]

        def get_timestamp_obj(node_name):
            if node_name in nodes:
                ts_str = nodes[node_name]["timestamp"]
                return datetime.fromisoformat(ts_str)
            return None

        def calculate_minutes(start_node, end_node):
            start = get_timestamp_obj(start_node)
            end = get_timestamp_obj(end_node)
            if start and end:
                return (end - start).total_seconds() / 60
            return None

        durations = {
            "preparation": {
                "name": "准备阶段（立项→需求收集完成）",
                "minutes": calculate_minutes("project_init", "requirement_collected"),
                "category": "execution"
            },
            "copywriting_execution": {
                "name": "文案执行（开始→完成）",
                "minutes": calculate_minutes("copywriting_start", "copywriting_done"),
                "category": "execution"
            },
            "copywriting_approval_wait": {
                "name": "文案审批等待（请求→通过）",
                "minutes": calculate_minutes("copywriting_approval_request", "copywriting_approved"),
                "category": "waiting"
            },
            "creative_execution": {
                "name": "创意方向执行（开始→完成）",
                "minutes": calculate_minutes("creative_direction_start", "creative_direction_done"),
                "category": "execution"
            },
            "creative_approval_wait": {
                "name": "创意审批等待（请求→通过）",
                "minutes": calculate_minutes("creative_approval_request", "creative_approved"),
                "category": "waiting"
            },
            "generation_execution": {
                "name": "生图执行（开始→完成）",
                "minutes": calculate_minutes("generation_start", "generation_done"),
                "category": "execution"
            },
            "design_approval_wait": {
                "name": "设计审批等待（请求→通过）",
                "minutes": calculate_minutes("design_approval_request", "design_approved"),
                "category": "waiting"
            },
            "advanced_approval_wait": {
                "name": "高级审批等待（请求→通过）",
                "minutes": calculate_minutes("advanced_approval_request", "advanced_approved"),
                "category": "waiting"
            },
            "total_project": {
                "name": "项目总耗时（立项→完结）",
                "minutes": calculate_minutes("project_init", "project_completed"),
                "category": "total"
            }
        }

        return durations

    def generate_report(self) -> dict:
        """
        生成完整的时间线报告

        Returns:
            完整的报告数据
        """
        durations = self.calculate_durations()

        # 统计执行时间 vs 等待时间
        execution_time = sum(
            d["minutes"] for d in durations.values()
            if d["category"] == "execution" and d["minutes"] is not None
        )

        waiting_time = sum(
            d["minutes"] for d in durations.values()
            if d["category"] == "waiting" and d["minutes"] is not None
        )

        # 统计问题影响
        issue_impact = sum(issue["impact_minutes"] for issue in self.timeline_data["issues"])

        # 统计修改次数
        revision_count = len(self.timeline_data["revisions"])

        # 计算百分比（安全处理）
        total_min = durations["total_project"]["minutes"]
        if total_min and total_min > 0:
            exec_pct = (execution_time / total_min * 100)
            wait_pct = (waiting_time / total_min * 100)
        else:
            exec_pct = 0
            wait_pct = 0

        return {
            "task_id": self.task_id,
            "timeline": self.timeline_data,
            "durations": durations,
            "summary": {
                "total_minutes": total_min,
                "execution_minutes": execution_time,
                "waiting_minutes": waiting_time,
                "issue_impact_minutes": issue_impact,
                "revision_count": revision_count,
                "execution_percentage": exec_pct,
                "waiting_percentage": wait_pct
            }
        }

    def export_feishu_doc(self) -> str:
        """
        导出为飞书文档格式（Markdown）

        Returns:
            飞书文档 Markdown 内容
        """
        report = self.generate_report()
        summary = report["summary"]
        durations = report["durations"]

        # 构建 Markdown
        lines = []
        lines.append(f"# 海报项目时间线报告")
        lines.append(f"")
        lines.append(f"**任务 ID**: {self.task_id}")
        lines.append(f"**生成时间**: {get_timestamp()}")
        lines.append(f"")

        # 总览
        lines.append(f"## 📊 项目总览")
        lines.append(f"")

        total_min = summary.get('total_minutes')
        if total_min:
            lines.append(f"- **项目总耗时**: {total_min:.1f} 分钟 ({total_min/60:.1f} 小时)")
        else:
            lines.append(f"- **项目总耗时**: 进行中（未完结）")

        lines.append(f"- **AI执行时间**: {summary['execution_minutes']:.1f} 分钟 ({summary['execution_percentage']:.1f}%)")
        lines.append(f"- **人工审批等待时间**: {summary['waiting_minutes']:.1f} 分钟 ({summary['waiting_percentage']:.1f}%)")
        lines.append(f"- **问题影响时间**: {summary['issue_impact_minutes']} 分钟")
        lines.append(f"- **修改次数**: {summary['revision_count']} 次")
        lines.append(f"")

        # 详细时间线
        lines.append(f"## ⏱️ 详细时间线")
        lines.append(f"")

        nodes = self.timeline_data["nodes"]
        for node_name in sorted(nodes.keys(), key=lambda n: nodes[n]["timestamp"]):
            node_info = TIMELINE_NODES[node_name]
            node_data = nodes[node_name]

            lines.append(f"### {node_info['name']}")
            lines.append(f"")
            lines.append(f"- **时间**: {node_data['timestamp']}")
            lines.append(f"- **描述**: {node_info['description']}")
            if node_data.get("notes"):
                lines.append(f"- **备注**: {node_data['notes']}")
            lines.append(f"")

        # 阶段耗时
        lines.append(f"## 📈 阶段耗时分析")
        lines.append(f"")

        for stage_key, stage_data in durations.items():
            if stage_data["minutes"] is not None:
                lines.append(f"### {stage_data['name']}")
                lines.append(f"")
                lines.append(f"- **耗时**: {stage_data['minutes']:.1f} 分钟 ({stage_data['minutes']/60:.1f} 小时)")
                lines.append(f"- **类型**: {stage_data['category']}")
                lines.append(f"")

        # 问题记录
        if self.timeline_data["issues"]:
            lines.append(f"## ⚠️ 问题记录")
            lines.append(f"")

            for issue in self.timeline_data["issues"]:
                status = "✅ 已解决" if issue["resolved_at"] else "❌ 未解决"
                lines.append(f"### {issue['issue_id']}: {issue['type_name']}")
                lines.append(f"")
                lines.append(f"- **状态**: {status}")
                lines.append(f"- **发生时间**: {issue['timestamp']}")
                if issue["resolved_at"]:
                    lines.append(f"- **解决时间**: {issue['resolved_at']}")
                lines.append(f"- **影响时长**: {issue['impact_minutes']} 分钟")
                lines.append(f"- **描述**: {issue['description']}")
                lines.append(f"")

        # 修改记录
        if self.timeline_data["revisions"]:
            lines.append(f"## 📝 修改记录")
            lines.append(f"")

            for revision in self.timeline_data["revisions"]:
                status = "✅ 已完成" if revision["completed_at"] else "🔄 进行中"
                lines.append(f"### {revision['revision_id']}: {revision['stage']}")
                lines.append(f"")
                lines.append(f"- **状态**: {status}")
                lines.append(f"- **请求时间**: {revision['requested_at']}")
                if revision["completed_at"]:
                    lines.append(f"- **完成时间**: {revision['completed_at']}")
                lines.append(f"- **原因**: {revision['reason']}")
                lines.append(f"")

        # 绩效分析
        lines.append(f"## 🎯 绩效分析")
        lines.append(f"")
        lines.append(f"### AI 执行效率")
        lines.append(f"- AI 执行时间占比：{summary['execution_percentage']:.1f}%")
        lines.append(f"- 平均每个执行阶段：{summary['execution_minutes']/3:.1f} 分钟（文案+创意+生图）")
        lines.append(f"")
        lines.append(f"### 人工审批效率")
        lines.append(f"- 审批等待时间占比：{summary['waiting_percentage']:.1f}%")
        lines.append(f"- 平均每个审批节点：{summary['waiting_minutes']/len([d for d in durations.values() if d['category']=='waiting' and d['minutes']]):.1f} 分钟")
        lines.append(f"")
        lines.append(f"### 改进建议")
        if summary["waiting_percentage"] > 50:
            lines.append(f"- ⚠️ 审批等待时间过长（{summary['waiting_percentage']:.1f}%），建议：")
            lines.append(f"  - 优化审批流程")
            lines.append(f"  - 设置审批时效提醒")
            lines.append(f"  - 考虑并行审批机制")
        if summary["revision_count"] > 2:
            lines.append(f"- ⚠️ 修改次数较多（{summary['revision_count']} 次），建议：")
            lines.append(f"  - 加强前期需求确认")
            lines.append(f"  - 提升创意方向沟通")
        if summary["issue_impact_minutes"] > 30:
            lines.append(f"- ⚠️ 问题影响时间较长（{summary['issue_impact_minutes']} 分钟），建议：")
            lines.append(f"  - 优化技术稳定性")
            lines.append(f"  - 完善资源准备流程")

        return "\n".join(lines)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="海报项目时间线记录系统")
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # record-node 命令
    node_parser = subparsers.add_parser("record-node", help="记录时间节点")
    node_parser.add_argument("--task-id", required=True, help="任务 ID")
    node_parser.add_argument("--node", required=True, help="节点名称")
    node_parser.add_argument("--notes", default="", help="备注说明")

    # record-issue 命令
    issue_parser = subparsers.add_parser("record-issue", help="记录问题")
    issue_parser.add_argument("--task-id", required=True, help="任务 ID")
    issue_parser.add_argument("--type", required=True, choices=list(ISSUE_TYPES.keys()), help="问题类型")
    issue_parser.add_argument("--description", required=True, help="问题描述")
    issue_parser.add_argument("--impact", type=int, default=0, help="影响时长（分钟）")

    # record-revision 命令
    revision_parser = subparsers.add_parser("record-revision", help="记录修改请求")
    revision_parser.add_argument("--task-id", required=True, help="任务 ID")
    revision_parser.add_argument("--stage", required=True, help="修改阶段")
    revision_parser.add_argument("--reason", required=True, help="修改原因")

    # generate-report 命令
    report_parser = subparsers.add_parser("generate-report", help="生成报告")
    report_parser.add_argument("--task-id", required=True, help="任务 ID")
    report_parser.add_argument("--format", choices=["json", "markdown"], default="markdown", help="输出格式")
    report_parser.add_argument("--output", help="输出文件路径")

    args = parser.parse_args()

    if args.command == "record-node":
        recorder = TimelineRecorder(args.task_id)
        recorder.record_node(args.node, args.notes)

    elif args.command == "record-issue":
        recorder = TimelineRecorder(args.task_id)
        recorder.record_issue(args.type, args.description, args.impact)

    elif args.command == "record-revision":
        recorder = TimelineRecorder(args.task_id)
        recorder.record_revision(args.stage, args.reason)

    elif args.command == "generate-report":
        recorder = TimelineRecorder(args.task_id)

        if args.format == "json":
            report = recorder.generate_report()
            output = json.dumps(report, ensure_ascii=False, indent=2)
        else:
            output = recorder.export_feishu_doc()

        if args.output:
            Path(args.output).write_text(output, encoding='utf-8')
            print(f"✅ 报告已保存: {args.output}")
        else:
            print(output)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
