#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECTS_ROOT = Path('/Users/a123/.openclaw/workspace/brand-poster-projects')
ROLE_KEYS = ['initiator', 'design_lead', 'planning_lead', 'project_manager']
STAGE_CONFIRMATION_MAP = {
    'assets': 'project_manager',
    'copywriting': 'planning_lead',
    'creative_direction': 'design_lead',
    'delivery': 'project_manager',
}
STAGE_ORDER = [
    'intake',
    'distill',
    'assets',
    'gap_check',
    'copywriting',
    'style_profile',
    'creative_direction',
    'prompt',
    'generation',
    'delivery',
    'cleanup',
]
MANIFEST_BY_STAGE = {
    'intake': 'intake_manifest.json',
    'distill': 'distill_manifest.json',
    'assets': 'assets_manifest.json',
    'gap_check': 'gap_check_manifest.json',
    'copywriting': 'copywriting_manifest.json',
    'style_profile': 'style_profile_manifest.json',
    'creative_direction': 'creative_direction_manifest.json',
    'prompt': 'prompt_manifest.json',
    'generation': 'generation_manifest.json',
    'delivery': 'delivery_manifest.json',
    'cleanup': 'cleanup_manifest.json',
}
ARTIFACT_FILES = {
    'brief': 'brief.json',
    'distill': 'distill_card.json',
    'copywriting': 'copywriting.json',
    'style_profile': 'style_profile.json',
    'creative_direction': 'creative_direction.json',
    'prompt': 'prompt_draft.md',
    'ref_order': 'ref_order.json',
    'generation': 'generation_result.json',
    'delivery': 'delivery_manifest.json',
    'cleanup': 'cleanup_manifest.json',
}
DELIVERY_SUCCESS_STATUSES = {'sent', 'delivered', 'success'}


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


class ProjectManager:
    def __init__(self, project_dir: str | Path):
        self.project_dir = Path(project_dir).resolve()
        self.project_dir.mkdir(parents=True, exist_ok=True)
        self.state_path = self.project_dir / 'project_state.json'
        self.audit_path = self.project_dir / 'audit_log.jsonl'
        self.state = self._load_or_init_state()

    @property
    def project_id(self) -> str:
        return self.project_dir.name

    def _default_stage_status(self) -> dict[str, str]:
        return {stage: 'pending' for stage in STAGE_ORDER}

    def _default_attempts(self) -> dict[str, int]:
        return {stage: 0 for stage in STAGE_ORDER}

    def _default_workflow_flags(self) -> dict[str, Any]:
        return {
            'distill_available': False,
            'distill_fallback': False,
            'assets_retrieved': False,
            'assets_confirmed': False,
            'gap_check_completed': False,
            'copywriting_ready': False,
            'copy_confirmed': False,
            'style_profile_ready': False,
            'creative_direction_ready': False,
            'creative_direction_confirmed': False,
            'prompt_ready': False,
            'generation_ready': False,
            'delivery_ready': False,
            'cleanup_ready': False,
        }

    def _default_role_contacts(self) -> dict[str, dict[str, str]]:
        return {
            key: {
                'feishu_user_id': '',
                'name': '',
                'source': '',
                'match_status': '',
                'raw_input': '',
            }
            for key in ROLE_KEYS
        }

    def _default_stage_confirmation_map(self) -> dict[str, str]:
        return dict(STAGE_CONFIRMATION_MAP)

    def _default_resume(self) -> dict[str, Any]:
        return {
            'auto_resume_stage': 'intake',
            'forced_resume_stage': '',
            'resume_reason': '项目已初始化，等待录入需求。',
            'override_by': '',
            'override_note': '',
            'updated_at': now_iso(),
        }

    def _default_state(self) -> dict[str, Any]:
        ts = now_iso()
        return {
            'project_id': self.project_id,
            'project_dir': str(self.project_dir),
            'created_at': ts,
            'updated_at': ts,
            'current_stage': 'intake',
            'stage_status': self._default_stage_status(),
            'workflow_flags': self._default_workflow_flags(),
            'attempts': self._default_attempts(),
            'resume': self._default_resume(),
            'role_contacts': self._default_role_contacts(),
            'stage_confirmation_map': self._default_stage_confirmation_map(),
            'last_error_stage': '',
            'last_error': '',
            'artifacts': {},
        }

    def _load_or_init_state(self) -> dict[str, Any]:
        state = load_json(self.state_path)
        if not isinstance(state, dict):
            state = self._default_state()
            write_json(self.state_path, state)
            return state
        state.setdefault('project_id', self.project_id)
        state.setdefault('project_dir', str(self.project_dir))
        state.setdefault('created_at', now_iso())
        state.setdefault('updated_at', now_iso())
        state.setdefault('current_stage', 'intake')
        stage_status = state.setdefault('stage_status', {})
        for stage, status in self._default_stage_status().items():
            stage_status.setdefault(stage, status)
        workflow_flags = state.setdefault('workflow_flags', {})
        for key, value in self._default_workflow_flags().items():
            workflow_flags.setdefault(key, value)
        attempts = state.setdefault('attempts', {})
        for key, value in self._default_attempts().items():
            attempts.setdefault(key, value)
        resume = state.setdefault('resume', {})
        for key, value in self._default_resume().items():
            resume.setdefault(key, value)
        role_contacts = state.setdefault('role_contacts', {})
        for key, value in self._default_role_contacts().items():
            role_contacts.setdefault(key, value)
            if not isinstance(role_contacts[key], dict):
                role_contacts[key] = value.copy()
            else:
                for field, default_value in value.items():
                    role_contacts[key].setdefault(field, default_value)
        stage_confirmation_map = state.setdefault('stage_confirmation_map', {})
        for stage, role in self._default_stage_confirmation_map().items():
            stage_confirmation_map.setdefault(stage, role)
        state.setdefault('last_error_stage', '')
        state.setdefault('last_error', '')
        state.setdefault('artifacts', {})
        write_json(self.state_path, state)
        return state

    def save(self) -> None:
        self.state['updated_at'] = now_iso()
        write_json(self.state_path, self.state)

    def audit(self, event: str, stage: str = '', status: str = '', actor: str = 'script', reason: str = '', files: list[str] | None = None, attempt: int | None = None, extra: dict[str, Any] | None = None) -> None:
        payload = {
            'ts': now_iso(),
            'event': event,
            'stage': stage,
            'status': status,
            'actor': actor,
            'reason': reason,
            'files': files or [],
            'attempt': attempt,
            'extra': extra or {},
        }
        append_jsonl(self.audit_path, payload)

    def _relative(self, path: str | Path) -> str:
        p = Path(path)
        try:
            return str(p.resolve().relative_to(self.project_dir))
        except Exception:
            return str(p)

    def _normalize_role_contacts(self, contacts: dict[str, Any] | None) -> dict[str, dict[str, str]]:
        normalized = self._default_role_contacts()
        if not isinstance(contacts, dict):
            return normalized
        for key in ROLE_KEYS:
            raw = contacts.get(key)
            if isinstance(raw, dict):
                for field in normalized[key]:
                    normalized[key][field] = str(raw.get(field, '') or '').strip()
            elif raw is not None:
                normalized[key]['feishu_user_id'] = str(raw).strip()
        return normalized

    def _confirmation_target_for_stage(self, stage: str) -> dict[str, str]:
        role = str(self.state.get('stage_confirmation_map', {}).get(stage, '') or '').strip()
        contact = self.state.get('role_contacts', {}).get(role, {}) if role else {}
        return {
            'role': role,
            'feishu_user_id': str((contact or {}).get('feishu_user_id', '') or '').strip(),
            'name': str((contact or {}).get('name', '') or '').strip(),
            'source': str((contact or {}).get('source', '') or '').strip(),
            'match_status': str((contact or {}).get('match_status', '') or '').strip(),
        }

    def init_project(self, brief_payload: dict[str, Any] | None = None, reason: str = '自动立项') -> dict[str, Any]:
        (self.project_dir / 'images').mkdir(parents=True, exist_ok=True)
        (self.project_dir / 'logs').mkdir(parents=True, exist_ok=True)
        brief_path = self.project_dir / 'brief.json'
        if brief_payload is not None or not brief_path.exists():
            write_json(brief_path, brief_payload or {})
        brief_data = (brief_payload or load_json(brief_path, {}) or {})
        role_contacts = self._normalize_role_contacts(brief_data.get('contacts'))
        self.state['role_contacts'] = role_contacts
        intake_manifest = {
            'project_id': self.project_id,
            'status': 'initialized',
            'created_at': now_iso(),
            'updated_at': now_iso(),
            'user_confirmed': False,
            'brief_path': str(brief_path),
            'fields_present': sorted(brief_data.keys()),
            'contacts_snapshot': role_contacts,
            'history': [
                {
                    'ts': now_iso(),
                    'event': 'project_initialized',
                    'reason': reason,
                }
            ],
        }
        write_json(self.project_dir / 'intake_manifest.json', intake_manifest)
        self.state['current_stage'] = 'intake'
        self.state['stage_status']['intake'] = 'done'
        self.state['artifacts']['brief'] = str(brief_path)
        self.state['resume']['auto_resume_stage'] = 'distill'
        self.state['resume']['resume_reason'] = '项目已初始化，下一步可进入蒸馏卡检查或继续补全需求。'
        self.save()
        self.audit('project_initialized', stage='intake', status='done', reason=reason, files=[self._relative(brief_path), 'intake_manifest.json'])
        return self.state

    def increment_attempt(self, stage: str) -> int:
        self.state['attempts'][stage] = int(self.state['attempts'].get(stage, 0) or 0) + 1
        self.save()
        return self.state['attempts'][stage]

    def set_current_stage(self, stage: str) -> None:
        if stage in STAGE_ORDER:
            self.state['current_stage'] = stage
            self.save()

    def set_flags(self, **flags: Any) -> None:
        self.state['workflow_flags'].update(flags)
        self.save()

    def set_artifacts(self, **artifacts: str) -> None:
        self.state['artifacts'].update({k: v for k, v in artifacts.items() if v})
        self.save()

    def start_stage(self, stage: str, reason: str = '', actor: str = 'script', attempt: int | None = None) -> int:
        if stage not in STAGE_ORDER:
            raise ValueError(f'未知阶段: {stage}')
        if attempt is None:
            attempt = self.increment_attempt(stage)
        else:
            self.state['attempts'][stage] = max(int(attempt), int(self.state['attempts'].get(stage, 0) or 0))
        self.state['current_stage'] = stage
        self.state['stage_status'][stage] = 'running'
        self.save()
        self.audit('stage_started', stage=stage, status='running', actor=actor, reason=reason, attempt=attempt)
        return attempt

    def write_stage_manifest(self, stage: str, payload: dict[str, Any]) -> Path:
        manifest_name = MANIFEST_BY_STAGE[stage]
        manifest_path = self.project_dir / manifest_name
        current = load_json(manifest_path, {}) or {}
        current.update(payload)
        current.setdefault('project_id', self.project_id)
        current.setdefault('stage', stage)
        target = self._confirmation_target_for_stage(stage)
        if target['role']:
            current['confirmation_target'] = target
        current.setdefault('confirmed_by', {})
        current['updated_at'] = now_iso()
        write_json(manifest_path, current)
        return manifest_path

    def _normalize_payload(self, raw: dict[str, Any] | None) -> dict[str, Any] | None:
        if raw is None:
            return None
        return raw

    def _default_manifest_payload(self, stage: str, status: str, attempt: int | None = None, reason: str = '', extra: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = {
            'status': status,
            'attempt': attempt if attempt is not None else self.state['attempts'].get(stage, 0),
            'reason': reason,
            'user_confirmed': False,
            'history': [{
                'ts': now_iso(),
                'event': f'{stage}_{status}',
                'reason': reason,
            }],
        }
        if extra:
            payload.update(extra)
        return payload

    def complete_stage(self, stage: str, reason: str = '', actor: str = 'script', manifest_payload: dict[str, Any] | None = None, flags: dict[str, Any] | None = None, artifacts: dict[str, str] | None = None, files: list[str] | None = None, extra: dict[str, Any] | None = None) -> None:
        self.state['stage_status'][stage] = 'done'
        self.state['current_stage'] = self.next_stage(stage) or stage
        self.state['last_error_stage'] = ''
        self.state['last_error'] = ''
        if flags:
            self.state['workflow_flags'].update(flags)
        if artifacts:
            self.state['artifacts'].update(artifacts)
        manifest_path = None
        if manifest_payload is not None:
            manifest_path = self.write_stage_manifest(stage, manifest_payload)
        self.state['resume']['auto_resume_stage'] = self.next_stage(stage) or stage
        self.state['resume']['resume_reason'] = reason or f'{stage} 阶段已完成。'
        self.state['resume']['updated_at'] = now_iso()
        self.save()
        event_files = list(files or [])
        if manifest_path:
            event_files.append(self._relative(manifest_path))
        self.audit('stage_succeeded', stage=stage, status='done', actor=actor, reason=reason, files=event_files, attempt=self.state['attempts'].get(stage), extra=extra)

    def skip_stage(self, stage: str, reason: str = '', actor: str = 'script', manifest_payload: dict[str, Any] | None = None, flags: dict[str, Any] | None = None, artifacts: dict[str, str] | None = None, files: list[str] | None = None, extra: dict[str, Any] | None = None) -> None:
        self.state['stage_status'][stage] = 'skipped'
        self.state['current_stage'] = self.next_stage(stage) or stage
        if flags:
            self.state['workflow_flags'].update(flags)
        if artifacts:
            self.state['artifacts'].update(artifacts)
        manifest_path = None
        if manifest_payload is not None:
            manifest_path = self.write_stage_manifest(stage, manifest_payload)
        self.state['resume']['auto_resume_stage'] = self.next_stage(stage) or stage
        self.state['resume']['resume_reason'] = reason or f'{stage} 阶段已跳过。'
        self.state['resume']['updated_at'] = now_iso()
        self.save()
        event_files = list(files or [])
        if manifest_path:
            event_files.append(self._relative(manifest_path))
        self.audit('stage_skipped', stage=stage, status='skipped', actor=actor, reason=reason, files=event_files, attempt=self.state['attempts'].get(stage), extra=extra)

    def fail_stage(self, stage: str, error: str, actor: str = 'script', manifest_payload: dict[str, Any] | None = None, files: list[str] | None = None, extra: dict[str, Any] | None = None) -> None:
        self.state['stage_status'][stage] = 'failed'
        self.state['current_stage'] = stage
        self.state['last_error_stage'] = stage
        self.state['last_error'] = error
        manifest_path = None
        if manifest_payload is not None:
            manifest_path = self.write_stage_manifest(stage, manifest_payload)
        self.state['resume']['auto_resume_stage'] = stage
        self.state['resume']['resume_reason'] = error
        self.state['resume']['updated_at'] = now_iso()
        self.save()
        event_files = list(files or [])
        if manifest_path:
            event_files.append(self._relative(manifest_path))
        self.audit('stage_failed', stage=stage, status='failed', actor=actor, reason=error, files=event_files, attempt=self.state['attempts'].get(stage), extra=extra)

    def record_user_confirmation(self, stage: str, confirmed: bool, note: str = '', actor: str = 'user', confirmed_by_role: str = '', confirmed_by_id: str = '') -> None:
        manifest_name = MANIFEST_BY_STAGE.get(stage)
        manifest_path = self.project_dir / manifest_name if manifest_name else None
        manifest = load_json(manifest_path, {}) if manifest_path and manifest_path.exists() else {}
        target = self._confirmation_target_for_stage(stage)
        confirmed_by = {
            'role': confirmed_by_role.strip(),
            'feishu_user_id': confirmed_by_id.strip(),
        }
        manifest['user_confirmed'] = bool(confirmed)
        if target['role']:
            manifest['confirmation_target'] = target
        manifest['confirmed_by'] = confirmed_by if confirmed else {}
        history = manifest.setdefault('history', [])
        history.append({
            'ts': now_iso(),
            'event': 'user_confirmed' if confirmed else 'user_rejected',
            'note': note,
            'confirmed_by_role': confirmed_by['role'],
            'confirmed_by_id': confirmed_by['feishu_user_id'],
            'target_role': target['role'],
            'target_feishu_user_id': target['feishu_user_id'],
        })
        if manifest_path:
            write_json(manifest_path, manifest)
        if stage == 'creative_direction':
            self.state['workflow_flags']['creative_direction_confirmed'] = bool(confirmed)
        if stage == 'assets':
            self.state['workflow_flags']['assets_confirmed'] = bool(confirmed)
        if stage == 'copywriting':
            self.state['workflow_flags']['copy_confirmed'] = bool(confirmed)
        self.state['resume']['auto_resume_stage'] = self.next_stage(stage) if confirmed else stage
        self.state['resume']['resume_reason'] = note or ('用户已确认阶段结果。' if confirmed else '用户要求继续修改该阶段结果。')
        self.state['resume']['updated_at'] = now_iso()
        self.save()
        self.audit(
            'user_confirmed' if confirmed else 'user_requested_retry',
            stage=stage,
            status='done' if confirmed else 'running',
            actor=actor,
            reason=note,
            files=[manifest_name] if manifest_name else [],
            extra={
                'target_role': target['role'],
                'target_feishu_user_id': target['feishu_user_id'],
                'confirmed_by_role': confirmed_by['role'],
                'confirmed_by_id': confirmed_by['feishu_user_id'],
            },
        )

    def force_resume(self, stage: str, note: str = '', actor: str = 'user') -> dict[str, Any]:
        if stage not in STAGE_ORDER:
            raise ValueError(f'未知阶段: {stage}')
        self.state['current_stage'] = stage
        self.state['resume']['forced_resume_stage'] = stage
        self.state['resume']['auto_resume_stage'] = stage
        self.state['resume']['resume_reason'] = note or f'人工强制从 {stage} 续跑。'
        self.state['resume']['override_by'] = actor
        self.state['resume']['override_note'] = note
        self.state['resume']['updated_at'] = now_iso()
        self.save()
        self.audit('stage_forced', stage=stage, status='running', actor=actor, reason=note)
        return self.state

    def next_stage(self, stage: str) -> str:
        try:
            idx = STAGE_ORDER.index(stage)
        except ValueError:
            return stage
        return STAGE_ORDER[idx + 1] if idx + 1 < len(STAGE_ORDER) else stage

    def _delivery_manifest_payload(self) -> dict[str, Any]:
        return load_json(self.project_dir / MANIFEST_BY_STAGE['delivery'], {}) or {}

    def _delivery_is_complete(self) -> bool:
        manifest = self._delivery_manifest_payload()
        status = str(manifest.get('delivery_status', '') or '').strip().lower()
        attempted = bool(manifest.get('delivery_attempted'))
        fallback_required = bool(manifest.get('fallback_required'))
        return attempted and not fallback_required and status in DELIVERY_SUCCESS_STATUSES

    def reconcile(self) -> dict[str, Any]:
        statuses = self.state['stage_status']
        flags = self.state['workflow_flags']
        artifacts = self.state['artifacts']

        def exists(name: str) -> bool:
            file_name = ARTIFACT_FILES[name]
            path = self.project_dir / file_name
            return path.exists() and path.stat().st_size > 0

        def manifest_exists(stage: str) -> bool:
            path = self.project_dir / MANIFEST_BY_STAGE[stage]
            return path.exists() and path.stat().st_size > 0

        statuses['intake'] = 'done' if exists('brief') else 'pending'
        statuses['distill'] = 'done' if exists('distill') or manifest_exists('distill') else ('skipped' if flags.get('distill_fallback') else statuses.get('distill', 'pending'))
        statuses['assets'] = 'done' if manifest_exists('assets') and (flags.get('assets_retrieved') or statuses.get('assets') == 'done') else statuses.get('assets', 'pending')
        statuses['gap_check'] = 'done' if manifest_exists('gap_check') or flags.get('gap_check_completed') else statuses.get('gap_check', 'pending')
        statuses['copywriting'] = 'done' if exists('copywriting') or manifest_exists('copywriting') or flags.get('copywriting_ready') else statuses.get('copywriting', 'pending')
        statuses['style_profile'] = 'done' if exists('style_profile') or manifest_exists('style_profile') or flags.get('style_profile_ready') else statuses.get('style_profile', 'pending')
        statuses['creative_direction'] = 'done' if exists('creative_direction') or manifest_exists('creative_direction') else statuses.get('creative_direction', 'pending')
        statuses['prompt'] = 'done' if (exists('prompt') and exists('ref_order')) or manifest_exists('prompt') or flags.get('prompt_ready') else statuses.get('prompt', 'pending')
        statuses['generation'] = 'done' if (exists('generation') and bool(load_json(self.project_dir / ARTIFACT_FILES['generation'], {}).get('ok'))) or manifest_exists('generation') and flags.get('generation_ready') else statuses.get('generation', 'pending')
        delivery_manifest_present = exists('delivery') or manifest_exists('delivery')
        delivery_complete = self._delivery_is_complete()
        if delivery_complete:
            statuses['delivery'] = 'done'
        elif delivery_manifest_present or flags.get('delivery_ready'):
            statuses['delivery'] = 'running'
        else:
            statuses['delivery'] = statuses.get('delivery', 'pending')
        statuses['cleanup'] = 'done' if exists('cleanup') or manifest_exists('cleanup') or flags.get('cleanup_ready') else statuses.get('cleanup', 'pending')

        flags['copywriting_ready'] = bool(flags.get('copywriting_ready')) or exists('copywriting') or manifest_exists('copywriting')
        flags['style_profile_ready'] = bool(flags.get('style_profile_ready')) or exists('style_profile') or manifest_exists('style_profile')
        flags['creative_direction_ready'] = bool(flags.get('creative_direction_ready')) or exists('creative_direction') or manifest_exists('creative_direction')
        flags['prompt_ready'] = bool(flags.get('prompt_ready')) or (exists('prompt') and exists('ref_order')) or manifest_exists('prompt')
        flags['generation_ready'] = bool(flags.get('generation_ready')) or (bool(load_json(self.project_dir / ARTIFACT_FILES['generation'], {}).get('ok')) if exists('generation') else False)
        flags['delivery_ready'] = delivery_complete
        flags['cleanup_ready'] = bool(flags.get('cleanup_ready')) or exists('cleanup') or manifest_exists('cleanup')

        if flags['cleanup_ready']:
            stage = 'cleanup'
            reason = '已存在 cleanup_manifest.json。'
        elif flags['delivery_ready'] and statuses.get('delivery') == 'done':
            stage = 'cleanup'
            reason = '交付已完成，可进入清理确认。'
        elif flags['generation_ready'] and statuses.get('prompt') == 'done':
            stage = 'delivery'
            reason = '生图成功，下一步应进入交付。'
        elif flags['prompt_ready']:
            stage = 'generation'
            reason = 'prompt_draft.md 与 ref_order.json 已就绪，可继续生图。'
        elif flags['creative_direction_ready']:
            stage = 'creative_direction' if not flags.get('creative_direction_confirmed') else 'prompt'
            reason = '创意表达方案已生成。' if not flags.get('creative_direction_confirmed') else '创意已确认，可继续组装 prompt。'
        elif flags['style_profile_ready']:
            stage = 'creative_direction'
            reason = '风格提炼已完成，可继续生成创意表达方案。'
        elif flags['copywriting_ready']:
            stage = 'style_profile'
            reason = '文案已生成，可继续风格提炼或创意表达。'
        elif statuses.get('gap_check') == 'done':
            stage = 'copywriting'
            reason = '信息缺口检查已完成，下一步应进入文案策划。'
        elif statuses.get('assets') == 'done':
            stage = 'gap_check'
            reason = '素材阶段已完成，下一步应进行信息缺口检查。'
        elif statuses.get('distill') in {'done', 'skipped'}:
            stage = 'assets'
            reason = '蒸馏卡阶段已结束，下一步应进行素材检索。'
        elif statuses.get('intake') == 'done':
            stage = 'distill'
            reason = '需求已立项，下一步应检查蒸馏卡。'
        else:
            stage = 'intake'
            reason = '尚未检测到完整项目输入，应先完成立项与需求录入。'

        if self.state.get('last_error_stage'):
            stage = self.state['last_error_stage']
            reason = self.state.get('last_error') or reason

        self.state['current_stage'] = stage
        self.state['resume']['auto_resume_stage'] = stage
        self.state['resume']['resume_reason'] = reason
        self.state['resume']['updated_at'] = now_iso()

        for artifact_name, file_name in ARTIFACT_FILES.items():
            path = self.project_dir / file_name
            if path.exists():
                artifacts[artifact_name] = str(path)

        self.save()
        return {
            'project_id': self.project_id,
            'project_dir': str(self.project_dir),
            'current_stage': stage,
            'resume_reason': reason,
            'stage_status': self.state['stage_status'],
            'workflow_flags': self.state['workflow_flags'],
            'artifacts': self.state['artifacts'],
        }



def parse_json_arg(raw: str) -> dict[str, Any]:
    if not raw:
        return {}
    return json.loads(raw)


def parse_json_list_arg(raw: str) -> list[str]:
    if not raw:
        return []
    data = json.loads(raw)
    if not isinstance(data, list):
        raise ValueError('files 参数必须是 JSON 数组')
    return [str(item) for item in data]



def main() -> int:
    parser = argparse.ArgumentParser(description='品牌海报项目状态管理器')
    subparsers = parser.add_subparsers(dest='command', required=True)

    init_parser = subparsers.add_parser('init', help='初始化项目状态')
    init_parser.add_argument('--project-dir', required=True)
    init_parser.add_argument('--brief-json', default='')
    init_parser.add_argument('--reason', default='自动立项')

    status_parser = subparsers.add_parser('status', help='查看当前状态')
    status_parser.add_argument('--project-dir', required=True)

    reconcile_parser = subparsers.add_parser('reconcile', help='自动推断续跑阶段')
    reconcile_parser.add_argument('--project-dir', required=True)

    stage_parser = subparsers.add_parser('stage', help='直接记录阶段结果')
    stage_parser.add_argument('--project-dir', required=True)
    stage_parser.add_argument('--stage', required=True, choices=STAGE_ORDER)
    stage_parser.add_argument('--action', required=True, choices=['start', 'complete', 'skip', 'fail'])
    stage_parser.add_argument('--reason', default='')
    stage_parser.add_argument('--actor', default='script')
    stage_parser.add_argument('--error', default='')
    stage_parser.add_argument('--manifest-json', default='')
    stage_parser.add_argument('--flags-json', default='')
    stage_parser.add_argument('--artifacts-json', default='')
    stage_parser.add_argument('--extra-json', default='')
    stage_parser.add_argument('--files-json', default='')
    stage_parser.add_argument('--attempt', type=int, default=0)

    confirm_parser = subparsers.add_parser('confirm', help='记录用户确认')
    confirm_parser.add_argument('--project-dir', required=True)
    confirm_parser.add_argument('--stage', required=True, choices=STAGE_ORDER)
    confirm_parser.add_argument('--confirmed', required=True, choices=['true', 'false'])
    confirm_parser.add_argument('--note', default='')
    confirm_parser.add_argument('--actor', default='user')
    confirm_parser.add_argument('--confirmed-by-role', default='')
    confirm_parser.add_argument('--confirmed-by-id', default='')

    force_parser = subparsers.add_parser('force-resume', help='人工指定阶段强制续跑')
    force_parser.add_argument('--project-dir', required=True)
    force_parser.add_argument('--stage', required=True, choices=STAGE_ORDER)
    force_parser.add_argument('--note', default='')
    force_parser.add_argument('--actor', default='user')

    args = parser.parse_args()
    manager = ProjectManager(args.project_dir)

    if args.command == 'init':
        brief_payload = load_json(Path(args.brief_json), {}) if args.brief_json else None
        result = manager.init_project(brief_payload=brief_payload, reason=args.reason)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == 'status':
        print(json.dumps(manager.state, ensure_ascii=False, indent=2))
        return 0

    if args.command == 'reconcile':
        print(json.dumps(manager.reconcile(), ensure_ascii=False, indent=2))
        return 0

    if args.command == 'stage':
        manifest_payload = parse_json_arg(args.manifest_json) if args.manifest_json else None
        flags = parse_json_arg(args.flags_json) if args.flags_json else None
        artifacts = parse_json_arg(args.artifacts_json) if args.artifacts_json else None
        extra = parse_json_arg(args.extra_json) if args.extra_json else None
        files = parse_json_list_arg(args.files_json) if args.files_json else None
        attempt = args.attempt or None
        if args.action == 'start':
            result = manager.start_stage(args.stage, reason=args.reason, actor=args.actor, attempt=attempt)
            print(json.dumps({'attempt': result, 'state': manager.state}, ensure_ascii=False, indent=2))
            return 0
        if args.action == 'complete':
            manager.complete_stage(args.stage, reason=args.reason, actor=args.actor, manifest_payload=manifest_payload, flags=flags, artifacts=artifacts, files=files, extra=extra)
            print(json.dumps(manager.state, ensure_ascii=False, indent=2))
            return 0
        if args.action == 'skip':
            manager.skip_stage(args.stage, reason=args.reason, actor=args.actor, manifest_payload=manifest_payload, flags=flags, files=files, extra=extra)
            print(json.dumps(manager.state, ensure_ascii=False, indent=2))
            return 0
        if args.action == 'fail':
            manager.fail_stage(args.stage, error=args.error or args.reason, actor=args.actor, manifest_payload=manifest_payload, files=files, extra=extra)
            print(json.dumps(manager.state, ensure_ascii=False, indent=2))
            return 0

    if args.command == 'confirm':
        manager.record_user_confirmation(
            stage=args.stage,
            confirmed=args.confirmed == 'true',
            note=args.note,
            actor=args.actor,
            confirmed_by_role=args.confirmed_by_role,
            confirmed_by_id=args.confirmed_by_id,
        )
        print(json.dumps(manager.state, ensure_ascii=False, indent=2))
        return 0

    if args.command == 'force-resume':
        print(json.dumps(manager.force_resume(args.stage, note=args.note, actor=args.actor), ensure_ascii=False, indent=2))
        return 0

    return 1


if __name__ == '__main__':
    sys.exit(main())
