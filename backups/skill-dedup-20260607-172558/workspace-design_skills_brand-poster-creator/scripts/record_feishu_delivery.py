#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from project_manager import DELIVERY_SUCCESS_STATUSES, MANIFEST_BY_STAGE, ProjectManager, load_json, now_iso, write_json


def record_delivery(
    project_dir: str | Path,
    sent_path: str | Path,
    message_id: str,
    chat_id: str,
    method: str = 'message(media)',
    status: str = 'sent',
) -> Path:
    project_dir = Path(project_dir).resolve()
    sent_path = str(Path(sent_path).resolve())
    message_id = str(message_id or '').strip()
    chat_id = str(chat_id or '').strip()
    method = str(method or 'message(media)').strip()
    status = str(status or 'sent').strip().lower()

    if status not in DELIVERY_SUCCESS_STATUSES:
        raise ValueError(f'交付状态不是成功状态: {status}')
    if not message_id:
        raise ValueError('缺少飞书发送成功返回的 message_id')
    if not chat_id:
        raise ValueError('缺少飞书发送成功返回的 chat_id')
    if not Path(sent_path).exists():
        raise FileNotFoundError(f'已发送文件不存在: {sent_path}')

    manifest_path = project_dir / MANIFEST_BY_STAGE['delivery']
    manifest = load_json(manifest_path, {}) or {}
    if not manifest:
        raise FileNotFoundError(f'缺少 delivery_manifest.json: {manifest_path}')

    evidence = manifest.setdefault('delivery_evidence', {})
    sent_paths = list(evidence.get('sent_paths') or [])
    if sent_path not in sent_paths:
        sent_paths.append(sent_path)

    manifest['delivery_attempted'] = True
    manifest['delivery_attempted_at'] = now_iso()
    manifest['delivery_status'] = status
    manifest['delivery_method'] = method
    manifest['fallback_required'] = False
    manifest['fallback_reason'] = ''
    manifest['user_report'] = ''
    manifest['updated_at'] = now_iso()
    evidence.update({
        'return_code': 0,
        'stdout_tail': '',
        'stderr_tail': '',
        'sent_paths': sent_paths,
        'message_id': message_id,
        'chat_id': chat_id,
        'method': method,
    })
    write_json(manifest_path, manifest)

    manager = ProjectManager(project_dir)
    manager.state['stage_status']['delivery'] = 'done'
    manager.state['workflow_flags']['delivery_ready'] = True
    manager.state['current_stage'] = 'cleanup'
    manager.state['artifacts']['delivery'] = str(manifest_path)
    manager.state['resume']['auto_resume_stage'] = 'cleanup'
    manager.state['resume']['resume_reason'] = '飞书真实发送成功，可等待定稿确认或进入清理。'
    manager.state['resume']['updated_at'] = now_iso()
    manager.save()
    manager.audit(
        'stage_succeeded',
        stage='delivery',
        status='done',
        actor='record_feishu_delivery.py',
        reason='飞书真实发送成功。',
        files=[manager._relative(manifest_path)],
        attempt=manager.state['attempts'].get('delivery'),
        extra={
            'message_id': message_id,
            'chat_id': chat_id,
            'sent_path': sent_path,
            'method': method,
        },
    )
    return manifest_path


def main() -> int:
    parser = argparse.ArgumentParser(description='Record successful Feishu delivery for a brand poster project')
    parser.add_argument('--project-dir', required=True, help='Brand poster project directory')
    parser.add_argument('--sent-path', required=True, help='Path that was sent through Feishu')
    parser.add_argument('--message-id', required=True, help='Feishu messageId returned by the send tool')
    parser.add_argument('--chat-id', required=True, help='Feishu chatId returned by the send tool')
    parser.add_argument('--method', default='message(media)', help='Delivery method/tool used')
    parser.add_argument('--status', default='sent', choices=sorted(DELIVERY_SUCCESS_STATUSES), help='Successful delivery status')
    args = parser.parse_args()

    manifest_path = record_delivery(
        project_dir=args.project_dir,
        sent_path=args.sent_path,
        message_id=args.message_id,
        chat_id=args.chat_id,
        method=args.method,
        status=args.status,
    )
    print(str(manifest_path))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
