#!/usr/bin/env python3
"""
项目分级与审批流管理模块
负责：
1. 项目等级判定（B/A/S）
2. 根据等级动态确定审批者
3. 自动艾特审批者
4. 审批状态跟踪
5. 超时兜底规则
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Literal

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from workspace_utils import detect_workspace_from_project

# 项目等级定义
PROJECT_GRADES = {
    'B': {
        'name': '日常项目',
        'reviewers': ['copywriter', 'designer'],
        'description': '常规海报、节日营销物料等日常需求'
    },
    'A': {
        'name': '重要项目',
        'reviewers': ['copywriter', 'designer', 'creative_director'],
        'description': '重要产品发布、品牌战役等需要总监审核的项目'
    },
    'S': {
        'name': '战略项目',
        'reviewers': ['copywriter', 'designer', 'creative_director', 'boss'],
        'description': '年度品牌战役、重大发布会等需要最高决策者审批的项目'
    }
}

# 审批节点与审批者映射
APPROVAL_MILESTONES = {
    'copywriting': {
        'title': '文案策划完成',
        'reviewer_role': 'copywriter',
        'artifact': 'copywriting.json',
        'required_grades': ['B', 'A', 'S']
    },
    'design': {
        'title': '设计初稿完成',
        'reviewer_role': 'designer',
        'artifact': 'generation_result.json',
        'required_grades': ['B', 'A', 'S']
    },
    'creative_direction': {
        'title': '创意总监审核',
        'reviewer_role': 'creative_director',
        'artifact': 'creative_direction.json',
        'required_grades': ['A', 'S']
    },
    'final_approval': {
        'title': '老板最终决策',
        'reviewer_role': 'boss',
        'artifact': None,  # 基于前序审批通过后触发
        'required_grades': ['S']
    }
}

# 审批超时规则（分钟）
APPROVAL_TIMEOUT = {
    'B': 60,      # B级项目：1小时
    'A': 120,     # A级项目：2小时
    'S': 240      # S级项目：4小时
}


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


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a', encoding='utf-8') as f:
        f.write(json.dumps(payload, ensure_ascii=False) + '\n')


def query_feishu_user(name: str) -> dict[str, str] | None:
    """
    查询飞书用户信息
    调用 feishu_search_user 工具（通过 OpenClaw）

    返回格式：
    {
        "name": "用户姓名",
        "open_id": "ou_xxxxx"
    }
    """
    # 实际实现中，这个函数会被 SKILL.md 中的主 agent 调用 feishu_search_user 工具
    # 这里只是占位符，实际逻辑在 SKILL.md 的流程中
    # 主 agent 会先调用工具获取 open_id，然后传入本脚本
    return None


def generate_mention_tag(name: str, open_id: str) -> str:
    """
    生成飞书艾特标签
    格式：<at user_id="ou_xxx">name</at>
    """
    return f'<at user_id="{open_id}">{name}</at>'


def init_project_grading(
    project_dir: Path,
    grade: Literal['B', 'A', 'S'],
    reviewers: dict[str, dict[str, str]]
) -> dict[str, Any]:
    """
    初始化项目分级信息

    Args:
        project_dir: 项目目录
        grade: 项目等级 (B/A/S)
        reviewers: 审批者信息
            {
                "copywriter": {"name": "张三", "open_id": "ou_xxx"},
                "designer": {"name": "李四", "open_id": "ou_yyy"},
                "creative_director": {"name": "王五", "open_id": "ou_zzz"},
                "boss": {"name": "赵六", "open_id": "ou_www"}
            }

    Returns:
        项目分级配置
    """
    if grade not in PROJECT_GRADES:
        raise ValueError(f"Invalid grade: {grade}. Must be one of B, A, S")

    grade_info = PROJECT_GRADES[grade]
    required_roles = grade_info['reviewers']

    # 验证必需的审批者
    missing_roles = [role for role in required_roles if role not in reviewers]
    if missing_roles:
        raise ValueError(f"Missing required reviewers for grade {grade}: {missing_roles}")

    # 构建项目分级配置
    grading_config = {
        'grade': grade,
        'grade_name': grade_info['name'],
        'description': grade_info['description'],
        'reviewers': {},
        'approval_flow': [],
        'created_at': now_iso()
    }

    # 只记录当前等级需要的审批者
    for role in required_roles:
        if role in reviewers:
            grading_config['reviewers'][role] = reviewers[role]

    # 构建审批流程
    for milestone, config in APPROVAL_MILESTONES.items():
        if grade in config['required_grades']:
            grading_config['approval_flow'].append({
                'milestone': milestone,
                'title': config['title'],
                'reviewer_role': config['reviewer_role'],
                'status': 'pending',
                'timeout_minutes': APPROVAL_TIMEOUT[grade]
            })

    # 保存到 project_grading.json
    grading_file = project_dir / 'project_grading.json'
    write_json(grading_file, grading_config)

    # 记录审计日志
    audit_log = project_dir / 'audit_log.jsonl'
    append_jsonl(audit_log, {
        'timestamp': now_iso(),
        'event': 'project_grading_initialized',
        'grade': grade,
        'reviewers': list(grading_config['reviewers'].keys()),
        'approval_flow_length': len(grading_config['approval_flow'])
    })

    return grading_config


def request_approval(
    project_dir: Path,
    milestone: str,
    artifact_path: str | None = None
) -> dict[str, Any]:
    """
    请求审批（触发艾特）

    Args:
        project_dir: 项目目录
        milestone: 审批节点 (copywriting, design, creative_direction, final_approval)
        artifact_path: 产物文件路径（用于展示）

    Returns:
        审批请求信息（包含艾特消息）
    """
    grading_file = project_dir / 'project_grading.json'
    grading_config = load_json(grading_file)

    if not grading_config:
        raise FileNotFoundError(f"Project grading config not found: {grading_file}")

    # 查找对应的审批节点
    approval_step = None
    for step in grading_config['approval_flow']:
        if step['milestone'] == milestone:
            approval_step = step
            break

    if not approval_step:
        raise ValueError(f"Milestone '{milestone}' not found in approval flow")

    if approval_step['status'] != 'pending':
        raise ValueError(f"Milestone '{milestone}' is not pending (current status: {approval_step['status']})")

    # 获取审批者信息
    reviewer_role = approval_step['reviewer_role']
    reviewer_info = grading_config['reviewers'].get(reviewer_role)

    if not reviewer_info:
        raise ValueError(f"Reviewer info not found for role: {reviewer_role}")

    # 更新审批状态为 "waiting"
    approval_step['status'] = 'waiting'
    approval_step['requested_at'] = now_iso()
    approval_step['timeout_at'] = (
        datetime.now(timezone.utc) + timedelta(minutes=approval_step['timeout_minutes'])
    ).isoformat().replace('+00:00', 'Z')

    write_json(grading_file, grading_config)

    # 生成艾特消息
    mention_tag = generate_mention_tag(reviewer_info['name'], reviewer_info['open_id'])

    approval_request = {
        'milestone': milestone,
        'title': approval_step['title'],
        'reviewer': reviewer_info,
        'mention_tag': mention_tag,
        'artifact_path': artifact_path,
        'timeout_at': approval_step['timeout_at'],
        'message': f"{mention_tag} {approval_step['title']}，请审核确认"
    }

    # 记录审计日志
    audit_log = project_dir / 'audit_log.jsonl'
    append_jsonl(audit_log, {
        'timestamp': now_iso(),
        'event': 'approval_requested',
        'milestone': milestone,
        'reviewer_role': reviewer_role,
        'reviewer_name': reviewer_info['name'],
        'timeout_at': approval_step['timeout_at']
    })

    return approval_request


def record_approval_response(
    project_dir: Path,
    milestone: str,
    decision: Literal['approved', 'rejected', 'revision_needed'],
    feedback: str = '',
    responder_open_id: str = ''
) -> dict[str, Any]:
    """
    记录审批响应

    Args:
        project_dir: 项目目录
        milestone: 审批节点
        decision: 审批决策 (approved, rejected, revision_needed)
        feedback: 反馈意见
        responder_open_id: 响应者的 open_id（用于验证身份）

    Returns:
        审批结果
    """
    grading_file = project_dir / 'project_grading.json'
    grading_config = load_json(grading_file)

    if not grading_config:
        raise FileNotFoundError(f"Project grading config not found: {grading_file}")

    # 查找对应的审批节点
    approval_step = None
    step_index = None
    for i, step in enumerate(grading_config['approval_flow']):
        if step['milestone'] == milestone:
            approval_step = step
            step_index = i
            break

    if not approval_step:
        raise ValueError(f"Milestone '{milestone}' not found in approval flow")

    # 验证身份（可选）
    reviewer_role = approval_step['reviewer_role']
    expected_reviewer = grading_config['reviewers'].get(reviewer_role)

    if responder_open_id and expected_reviewer:
        if responder_open_id != expected_reviewer['open_id']:
            raise PermissionError(
                f"Responder {responder_open_id} is not authorized to approve milestone '{milestone}'. "
                f"Expected: {expected_reviewer['open_id']}"
            )

    # 更新审批状态
    approval_step['status'] = decision
    approval_step['responded_at'] = now_iso()
    approval_step['feedback'] = feedback

    # 计算响应时长
    if 'requested_at' in approval_step:
        requested = datetime.fromisoformat(approval_step['requested_at'].replace('Z', '+00:00'))
        responded = datetime.now(timezone.utc)
        response_time_seconds = (responded - requested).total_seconds()
        approval_step['response_time_seconds'] = int(response_time_seconds)

    write_json(grading_file, grading_config)

    # 记录审计日志
    audit_log = project_dir / 'audit_log.jsonl'
    append_jsonl(audit_log, {
        'timestamp': now_iso(),
        'event': 'approval_responded',
        'milestone': milestone,
        'decision': decision,
        'feedback': feedback,
        'response_time_seconds': approval_step.get('response_time_seconds', 0),
        'responder_verified': bool(responder_open_id and expected_reviewer)
    })

    return {
        'milestone': milestone,
        'decision': decision,
        'feedback': feedback,
        'next_action': _determine_next_action(grading_config, step_index, decision)
    }


def _determine_next_action(
    grading_config: dict[str, Any],
    current_step_index: int,
    decision: str
) -> str:
    """
    根据审批结果决定下一步行动
    """
    if decision == 'rejected':
        return 'terminate_project'
    elif decision == 'revision_needed':
        return 'revise_and_resubmit'
    elif decision == 'approved':
        # 检查是否还有后续审批节点
        if current_step_index < len(grading_config['approval_flow']) - 1:
            next_step = grading_config['approval_flow'][current_step_index + 1]
            return f"proceed_to_{next_step['milestone']}"
        else:
            return 'proceed_to_delivery'
    else:
        return 'unknown'


def check_timeout(project_dir: Path) -> list[dict[str, Any]]:
    """
    检查是否有超时的审批节点

    Returns:
        超时的审批节点列表
    """
    grading_file = project_dir / 'project_grading.json'
    grading_config = load_json(grading_file)

    if not grading_config:
        return []

    now = datetime.now(timezone.utc)
    timeout_steps = []

    for step in grading_config['approval_flow']:
        if step['status'] == 'waiting' and 'timeout_at' in step:
            timeout_at = datetime.fromisoformat(step['timeout_at'].replace('Z', '+00:00'))
            if now > timeout_at:
                timeout_steps.append({
                    'milestone': step['milestone'],
                    'title': step['title'],
                    'reviewer_role': step['reviewer_role'],
                    'timeout_at': step['timeout_at'],
                    'overdue_minutes': int((now - timeout_at).total_seconds() / 60)
                })

    return timeout_steps


def handle_timeout(
    project_dir: Path,
    milestone: str,
    action: Literal['remind', 'auto_approve', 'escalate'] = 'remind'
) -> dict[str, Any]:
    """
    处理审批超时

    Args:
        project_dir: 项目目录
        milestone: 审批节点
        action: 处理方式
            - remind: 再次提醒审批者
            - auto_approve: 自动通过（B级项目可用）
            - escalate: 升级到上级审批者（A/S级项目）

    Returns:
        处理结果
    """
    grading_file = project_dir / 'project_grading.json'
    grading_config = load_json(grading_file)

    if not grading_config:
        raise FileNotFoundError(f"Project grading config not found: {grading_file}")

    grade = grading_config['grade']

    # 查找对应的审批节点
    approval_step = None
    for step in grading_config['approval_flow']:
        if step['milestone'] == milestone:
            approval_step = step
            break

    if not approval_step:
        raise ValueError(f"Milestone '{milestone}' not found in approval flow")

    result = {'action': action, 'milestone': milestone}

    if action == 'remind':
        # 再次艾特提醒
        reviewer_info = grading_config['reviewers'][approval_step['reviewer_role']]
        mention_tag = generate_mention_tag(reviewer_info['name'], reviewer_info['open_id'])
        result['message'] = f"{mention_tag} 提醒：{approval_step['title']}已超时，请尽快审核"

    elif action == 'auto_approve':
        # 仅B级项目允许自动通过
        if grade != 'B':
            raise ValueError(f"Auto-approve is only allowed for grade B projects (current: {grade})")

        approval_step['status'] = 'approved'
        approval_step['responded_at'] = now_iso()
        approval_step['feedback'] = '超时自动通过'
        approval_step['auto_approved'] = True
        write_json(grading_file, grading_config)

        result['approved'] = True
        result['message'] = f"B级项目超时，已自动通过：{approval_step['title']}"

    elif action == 'escalate':
        # A/S级项目升级到项目经理处理
        result['message'] = f"⚠️ {approval_step['title']}已超时，请项目经理协调处理"

    # 记录审计日志
    audit_log = project_dir / 'audit_log.jsonl'
    append_jsonl(audit_log, {
        'timestamp': now_iso(),
        'event': 'timeout_handled',
        'milestone': milestone,
        'action': action,
        'grade': grade
    })

    return result


def get_approval_status(project_dir: Path) -> dict[str, Any]:
    """
    获取当前审批状态

    Returns:
        {
            'grade': 'B',
            'current_milestone': 'copywriting',
            'approval_flow': [...],
            'pending_count': 2,
            'completed_count': 1
        }
    """
    grading_file = project_dir / 'project_grading.json'
    grading_config = load_json(grading_file)

    if not grading_config:
        return {'error': 'Project grading not initialized'}

    pending = [s for s in grading_config['approval_flow'] if s['status'] in ['pending', 'waiting']]
    completed = [s for s in grading_config['approval_flow'] if s['status'] == 'approved']

    current_milestone = None
    for step in grading_config['approval_flow']:
        if step['status'] in ['pending', 'waiting']:
            current_milestone = step['milestone']
            break

    return {
        'grade': grading_config['grade'],
        'grade_name': grading_config['grade_name'],
        'current_milestone': current_milestone,
        'approval_flow': grading_config['approval_flow'],
        'pending_count': len(pending),
        'completed_count': len(completed),
        'total_count': len(grading_config['approval_flow'])
    }


def main():
    parser = argparse.ArgumentParser(description='项目分级与审批流管理')
    parser.add_argument('action', choices=[
        'init',
        'request',
        'respond',
        'status',
        'check_timeout',
        'handle_timeout'
    ])
    parser.add_argument('--project-dir', required=True, help='项目目录')
    parser.add_argument('--grade', choices=['B', 'A', 'S'], help='项目等级')
    parser.add_argument('--reviewers-json', help='审批者信息（JSON格式）')
    parser.add_argument('--milestone', help='审批节点')
    parser.add_argument('--artifact', help='产物文件路径')
    parser.add_argument('--decision', choices=['approved', 'rejected', 'revision_needed'], help='审批决策')
    parser.add_argument('--feedback', default='', help='反馈意见')
    parser.add_argument('--responder-open-id', help='响应者 open_id')
    parser.add_argument('--timeout-action', choices=['remind', 'auto_approve', 'escalate'], default='remind')

    args = parser.parse_args()
    project_dir = Path(args.project_dir)

    try:
        if args.action == 'init':
            if not args.grade or not args.reviewers_json:
                print(json.dumps({'error': 'Missing required arguments: --grade, --reviewers-json'}))
                sys.exit(1)

            reviewers = json.loads(args.reviewers_json)
            result = init_project_grading(project_dir, args.grade, reviewers)
            print(json.dumps(result, ensure_ascii=False, indent=2))

        elif args.action == 'request':
            if not args.milestone:
                print(json.dumps({'error': 'Missing required argument: --milestone'}))
                sys.exit(1)

            result = request_approval(project_dir, args.milestone, args.artifact)
            print(json.dumps(result, ensure_ascii=False, indent=2))

        elif args.action == 'respond':
            if not args.milestone or not args.decision:
                print(json.dumps({'error': 'Missing required arguments: --milestone, --decision'}))
                sys.exit(1)

            result = record_approval_response(
                project_dir,
                args.milestone,
                args.decision,
                args.feedback,
                args.responder_open_id or ''
            )
            print(json.dumps(result, ensure_ascii=False, indent=2))

        elif args.action == 'status':
            result = get_approval_status(project_dir)
            print(json.dumps(result, ensure_ascii=False, indent=2))

        elif args.action == 'check_timeout':
            result = check_timeout(project_dir)
            print(json.dumps({'timeout_steps': result}, ensure_ascii=False, indent=2))

        elif args.action == 'handle_timeout':
            if not args.milestone:
                print(json.dumps({'error': 'Missing required argument: --milestone'}))
                sys.exit(1)

            result = handle_timeout(project_dir, args.milestone, args.timeout_action)
            print(json.dumps(result, ensure_ascii=False, indent=2))

    except Exception as e:
        print(json.dumps({'error': str(e)}, ensure_ascii=False))
        sys.exit(1)


if __name__ == '__main__':
    main()
