#!/usr/bin/env python3
"""
时间记录与复盘分析模块
负责：
1. 记录每个阶段的 AI 处理时间和人工审核时间
2. 生成项目时间线
3. 生成复盘报告
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


def load_json(path: Path, default: Any = None):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except json.JSONDecodeError:
        return default


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')


def parse_iso_time(iso_str: str) -> datetime:
    """解析 ISO 格式时间字符串"""
    return datetime.fromisoformat(iso_str.replace('Z', '+00:00'))


def calculate_duration_seconds(start_iso: str, end_iso: str) -> int:
    """计算两个时间点之间的秒数"""
    start = parse_iso_time(start_iso)
    end = parse_iso_time(end_iso)
    return int((end - start).total_seconds())


def record_stage_time(
    project_dir: Path,
    stage: str,
    event_type: str,
    actor: str = 'ai'
) -> dict[str, Any]:
    """
    记录阶段时间事件

    Args:
        project_dir: 项目目录
        stage: 阶段名称 (copywriting, design, creative_direction, etc.)
        event_type: 事件类型 (start, complete)
        actor: 执行者 (ai, human)

    Returns:
        记录结果
    """
    timeline_file = project_dir / 'project_timeline.json'
    timeline = load_json(timeline_file, {
        'project_id': project_dir.name,
        'created_at': now_iso(),
        'stages': {}
    })

    if stage not in timeline['stages']:
        timeline['stages'][stage] = {
            'events': [],
            'ai_time_seconds': 0,
            'human_time_seconds': 0,
            'total_time_seconds': 0
        }

    stage_data = timeline['stages'][stage]

    # 记录事件
    event = {
        'event_type': event_type,
        'actor': actor,
        'timestamp': now_iso()
    }
    stage_data['events'].append(event)

    # 如果是 complete 事件，计算耗时
    if event_type == 'complete':
        start_event = None
        for e in reversed(stage_data['events']):
            if e['event_type'] == 'start' and e['actor'] == actor:
                start_event = e
                break

        if start_event:
            duration = calculate_duration_seconds(start_event['timestamp'], event['timestamp'])
            event['duration_seconds'] = duration

            # 更新累计时间
            if actor == 'ai':
                stage_data['ai_time_seconds'] += duration
            elif actor == 'human':
                stage_data['human_time_seconds'] += duration

            stage_data['total_time_seconds'] = (
                stage_data['ai_time_seconds'] + stage_data['human_time_seconds']
            )

    write_json(timeline_file, timeline)

    return {
        'stage': stage,
        'event': event,
        'stage_summary': {
            'ai_time': stage_data['ai_time_seconds'],
            'human_time': stage_data['human_time_seconds'],
            'total_time': stage_data['total_time_seconds']
        }
    }


def generate_timeline_report(project_dir: Path) -> dict[str, Any]:
    """
    生成项目时间线报告

    Returns:
        {
            'project_id': 'BP-20260613-001',
            'total_ai_time': 1200,
            'total_human_time': 3600,
            'total_project_time': 4800,
            'ai_percentage': 25.0,
            'human_percentage': 75.0,
            'stages': [...]
        }
    """
    timeline_file = project_dir / 'project_timeline.json'
    timeline = load_json(timeline_file)

    if not timeline:
        return {'error': 'Timeline not found'}

    total_ai = 0
    total_human = 0
    stage_summaries = []

    for stage_name, stage_data in timeline['stages'].items():
        ai_time = stage_data.get('ai_time_seconds', 0)
        human_time = stage_data.get('human_time_seconds', 0)
        total_time = stage_data.get('total_time_seconds', 0)

        total_ai += ai_time
        total_human += human_time

        stage_summaries.append({
            'stage': stage_name,
            'ai_time_seconds': ai_time,
            'human_time_seconds': human_time,
            'total_time_seconds': total_time,
            'ai_percentage': round(ai_time / total_time * 100, 1) if total_time > 0 else 0,
            'human_percentage': round(human_time / total_time * 100, 1) if total_time > 0 else 0
        })

    total_project_time = total_ai + total_human

    return {
        'project_id': timeline['project_id'],
        'created_at': timeline.get('created_at', ''),
        'total_ai_time_seconds': total_ai,
        'total_human_time_seconds': total_human,
        'total_project_time_seconds': total_project_time,
        'ai_percentage': round(total_ai / total_project_time * 100, 1) if total_project_time > 0 else 0,
        'human_percentage': round(total_human / total_project_time * 100, 1) if total_project_time > 0 else 0,
        'stages': stage_summaries
    }


def generate_retrospective_report(project_dir: Path) -> str:
    """
    生成复盘报告（Markdown格式）

    Returns:
        复盘报告内容
    """
    timeline_report = generate_timeline_report(project_dir)

    if 'error' in timeline_report:
        return f"# 复盘报告生成失败\n\n{timeline_report['error']}"

    # 读取审批状态
    grading_file = project_dir / 'project_grading.json'
    grading_config = load_json(grading_file, {})

    # 读取审计日志
    audit_log_file = project_dir / 'audit_log.jsonl'
    audit_events = []
    if audit_log_file.exists():
        with audit_log_file.open('r', encoding='utf-8') as f:
            for line in f:
                try:
                    audit_events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    # 构建报告
    report_lines = []
    report_lines.append(f"# 项目复盘报告")
    report_lines.append(f"")
    report_lines.append(f"**项目ID**: {timeline_report['project_id']}")
    report_lines.append(f"**创建时间**: {timeline_report.get('created_at', 'N/A')}")
    report_lines.append(f"**项目等级**: {grading_config.get('grade', 'N/A')} - {grading_config.get('grade_name', 'N/A')}")
    report_lines.append(f"")

    # 时间分析
    report_lines.append(f"## ⏱️ 时间分析")
    report_lines.append(f"")
    report_lines.append(f"| 维度 | 耗时（秒） | 耗时（分钟） | 占比 |")
    report_lines.append(f"|------|-----------|------------|------|")

    total_seconds = timeline_report['total_project_time_seconds']
    ai_seconds = timeline_report['total_ai_time_seconds']
    human_seconds = timeline_report['total_human_time_seconds']

    report_lines.append(
        f"| AI 处理时间 | {ai_seconds} | {ai_seconds // 60} | {timeline_report['ai_percentage']}% |"
    )
    report_lines.append(
        f"| 人工审核时间 | {human_seconds} | {human_seconds // 60} | {timeline_report['human_percentage']}% |"
    )
    report_lines.append(
        f"| **总耗时** | **{total_seconds}** | **{total_seconds // 60}** | **100%** |"
    )
    report_lines.append(f"")

    # 各阶段耗时
    report_lines.append(f"## 📊 各阶段耗时明细")
    report_lines.append(f"")
    report_lines.append(f"| 阶段 | AI 耗时 | 人工耗时 | 总耗时 | AI占比 | 人工占比 |")
    report_lines.append(f"|------|---------|---------|--------|--------|---------|")

    for stage in timeline_report['stages']:
        ai_min = stage['ai_time_seconds'] // 60
        human_min = stage['human_time_seconds'] // 60
        total_min = stage['total_time_seconds'] // 60

        report_lines.append(
            f"| {stage['stage']} | {ai_min}分 | {human_min}分 | {total_min}分 | "
            f"{stage['ai_percentage']}% | {stage['human_percentage']}% |"
        )

    report_lines.append(f"")

    # 审批流程分析
    if grading_config and 'approval_flow' in grading_config:
        report_lines.append(f"## ✅ 审批流程分析")
        report_lines.append(f"")
        report_lines.append(f"| 节点 | 审批者 | 状态 | 响应时长 | 反馈 |")
        report_lines.append(f"|------|--------|------|----------|------|")

        for step in grading_config['approval_flow']:
            reviewer_role = step.get('reviewer_role', 'N/A')
            reviewer_name = grading_config.get('reviewers', {}).get(reviewer_role, {}).get('name', 'N/A')
            status = step.get('status', 'pending')
            response_time = step.get('response_time_seconds', 0)
            feedback = step.get('feedback', '')

            status_emoji = {
                'pending': '⏳',
                'waiting': '⏰',
                'approved': '✅',
                'rejected': '❌',
                'revision_needed': '🔄'
            }.get(status, '❓')

            response_time_str = f"{response_time // 60}分钟" if response_time > 0 else '-'

            report_lines.append(
                f"| {step.get('title', 'N/A')} | {reviewer_name} | {status_emoji} {status} | "
                f"{response_time_str} | {feedback[:20]}... |"
            )

        report_lines.append(f"")

    # 关键事件时间线
    report_lines.append(f"## 📅 关键事件时间线")
    report_lines.append(f"")

    key_events = [e for e in audit_events if e.get('event') in [
        'project_grading_initialized',
        'approval_requested',
        'approval_responded',
        'timeout_handled'
    ]]

    for event in key_events[-10:]:  # 只显示最近10条
        timestamp = event.get('timestamp', 'N/A')
        event_type = event.get('event', 'unknown')
        milestone = event.get('milestone', '')

        try:
            dt = parse_iso_time(timestamp)
            time_str = dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            time_str = timestamp

        report_lines.append(f"- **{time_str}** - {event_type} {milestone}")

    report_lines.append(f"")

    # 优化建议
    report_lines.append(f"## 💡 优化建议")
    report_lines.append(f"")

    if timeline_report['human_percentage'] > 70:
        report_lines.append(f"- ⚠️ 人工审核时间占比 {timeline_report['human_percentage']}%，建议优化审批响应速度")

    if timeline_report['ai_percentage'] > 70:
        report_lines.append(f"- ⚠️ AI 处理时间占比 {timeline_report['ai_percentage']}%，可能存在生成效率问题")

    # 检查超时情况
    timeout_events = [e for e in audit_events if e.get('event') == 'timeout_handled']
    if timeout_events:
        report_lines.append(f"- ⚠️ 发现 {len(timeout_events)} 次审批超时，建议调整超时阈值或优化协作流程")

    report_lines.append(f"")

    return '\n'.join(report_lines)


def main():
    parser = argparse.ArgumentParser(description='时间记录与复盘分析')
    parser.add_argument('action', choices=[
        'record',
        'timeline',
        'retrospective'
    ])
    parser.add_argument('--project-dir', required=True, help='项目目录')
    parser.add_argument('--stage', help='阶段名称')
    parser.add_argument('--event-type', choices=['start', 'complete'], help='事件类型')
    parser.add_argument('--actor', choices=['ai', 'human'], default='ai', help='执行者')
    parser.add_argument('--output', help='输出文件路径（用于 retrospective）')

    args = parser.parse_args()
    project_dir = Path(args.project_dir)

    try:
        if args.action == 'record':
            if not args.stage or not args.event_type:
                print(json.dumps({'error': 'Missing required arguments: --stage, --event-type'}))
                sys.exit(1)

            result = record_stage_time(project_dir, args.stage, args.event_type, args.actor)
            print(json.dumps(result, ensure_ascii=False, indent=2))

        elif args.action == 'timeline':
            result = generate_timeline_report(project_dir)
            print(json.dumps(result, ensure_ascii=False, indent=2))

        elif args.action == 'retrospective':
            report = generate_retrospective_report(project_dir)

            if args.output:
                output_path = Path(args.output)
                output_path.write_text(report, encoding='utf-8')
                print(json.dumps({'success': True, 'output_path': str(output_path)}, ensure_ascii=False))
            else:
                print(report)

    except Exception as e:
        print(json.dumps({'error': str(e)}, ensure_ascii=False))
        sys.exit(1)


if __name__ == '__main__':
    main()
