#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import zipfile
from pathlib import Path
import sys

from PIL import Image

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from project_manager import ProjectManager, now_iso

FEISHU_LIMIT_BYTES = 10 * 1024 * 1024
PREVIEW_MAX_EDGE = 1600
PREVIEW_JPEG_QUALITY = 88
DELIVERY_DIR = Path('/Users/a123/.openclaw/workspace/feishu-deliver')


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')


def ensure_delivery_dir() -> None:
    DELIVERY_DIR.mkdir(parents=True, exist_ok=True)


def unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    counter = 2
    while True:
        candidate = path.with_name(f'{stem}-v{counter}{suffix}')
        if not candidate.exists():
            return candidate
        counter += 1


def delivery_stem(project_id: str, index: int) -> str:
    return f'{project_id}-final_poster' if index == 1 else f'{project_id}-final_poster-{index}'


def make_preview(source_path: Path, project_id: str, index: int = 1) -> tuple[Path, int]:
    preview_path = unique_path(DELIVERY_DIR / f'{delivery_stem(project_id, index)}-preview.jpg')
    with Image.open(source_path) as img:
        preview = img.convert('RGB')
        preview.thumbnail((PREVIEW_MAX_EDGE, PREVIEW_MAX_EDGE))
        preview.save(preview_path, format='JPEG', quality=PREVIEW_JPEG_QUALITY, optimize=True)
    return preview_path, preview_path.stat().st_size


def copy_original(source_path: Path, project_id: str, index: int = 1) -> tuple[Path, int]:
    target_path = unique_path(DELIVERY_DIR / f'{delivery_stem(project_id, index)}{source_path.suffix.lower()}')
    shutil.copy2(source_path, target_path)
    return target_path, target_path.stat().st_size


def make_zip(source_path: Path, project_id: str, index: int = 1) -> tuple[Path, int]:
    zip_path = unique_path(DELIVERY_DIR / f'{delivery_stem(project_id, index)}-original.zip')
    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        zf.write(source_path, arcname=source_path.name)
    return zip_path, zip_path.stat().st_size


def media_mime_type(path: str) -> str:
    suffix = Path(path).suffix.lower()
    if suffix in {'.jpg', '.jpeg'}:
        return 'image/jpeg'
    if suffix == '.png':
        return 'image/png'
    if suffix == '.webp':
        return 'image/webp'
    return 'application/octet-stream'


def select_send_path(manifest: dict) -> str:
    candidates = (manifest.get('deliverables') or {}).get('candidate_images') or []
    if candidates:
        return str(candidates[0].get('send_path') or '').strip()
    deliverables = manifest.get('deliverables') or {}
    if manifest.get('delivery_mode') == 'preview_and_zip':
        return str(((deliverables.get('preview_image') or {}).get('path') or '')).strip()
    return str(((deliverables.get('original_copy') or {}).get('path') or '')).strip()


def build_agent_delivery_contract(manifest: dict) -> dict:
    send_path = select_send_path(manifest)
    is_preview = manifest.get('delivery_mode') == 'preview_and_zip'
    candidates = (manifest.get('deliverables') or {}).get('candidate_images') or []
    candidate_count = len(candidates) or 1
    caption = (
        f'本次海报抽卡 {candidate_count} 张。当前为压缩预览版，原始高清图已保留；后续修改继续基于原图。'
        if is_preview else
        f'本次海报抽卡 {candidate_count} 张，请确认。'
    )
    project_dir = str(manifest.get('project_dir') or '').strip()
    record_script = SCRIPT_DIR / 'record_feishu_delivery.py'
    message_tool_calls = [
        {
            'action': 'send',
            'channel': 'feishu',
            'accountId': 'main',
            'media': str(item.get('send_path') or ''),
            'mimeType': media_mime_type(str(item.get('send_path') or '')),
            'message': f"候选 {idx}/{candidate_count}。" + ('压缩预览版，原始高清图已保留。' if item.get('delivery_mode') == 'preview_and_zip' else '正式海报原图。'),
            'caption': f"候选 {idx}/{candidate_count}",
        }
        for idx, item in enumerate(candidates, start=1)
        if item.get('send_path')
    ]
    return {
        'status': 'tool_call_required',
        'completion_requires_tool_success': True,
        'target_resolution': 'If delivery_target.chat_id/user_id is empty, use the current Feishu session binding; do not stop or ask for the target.',
        'forbidden_text_delivery_prefixes': ['MEDIA:', '/Users/', 'file://'],
        'forbidden_claims_before_tool_success': ['已发', '发群里了', '已发送', '交付完成'],
        'send_plan': {
            'tool': 'message',
            'path': send_path,
            'paths': [call['media'] for call in message_tool_calls] or [send_path],
            'message_tool_calls': message_tool_calls,
            'message_tool_arguments': {
                'action': 'send',
                'channel': 'feishu',
                'accountId': 'main',
                'media': send_path,
                'mimeType': media_mime_type(send_path),
                'message': caption,
                'caption': caption,
            },
        },
        'success_evidence_required': ['ok=true', 'messageId', 'chatId'],
        'after_success_record_command': (
            f'python3 {record_script} '
            f'--project-dir {project_dir} '
            f'--sent-path {send_path} '
            '--message-id <messageId> '
            '--chat-id <chatId> '
            '--method message(media)'
        ),
    }


def prepare_single_image(image_path: Path, project_id: str, index: int) -> dict:
    original_size = image_path.stat().st_size
    needs_preview = original_size > FEISHU_LIMIT_BYTES
    preview_path = None
    preview_size = None
    original_copy_path = None
    original_copy_size = None
    zip_path = None
    zip_size = None

    if needs_preview:
        preview_path, preview_size = make_preview(image_path, project_id, index)
        original_copy_path, original_copy_size = copy_original(image_path, project_id, index)
        zip_path, zip_size = make_zip(image_path, project_id, index)
        send_path = preview_path
    else:
        original_copy_path, original_copy_size = copy_original(image_path, project_id, index)
        send_path = original_copy_path

    return {
        'index': index,
        'original_image': str(image_path),
        'original_size_bytes': original_size,
        'needs_preview': needs_preview,
        'delivery_mode': 'preview_and_zip' if needs_preview else 'direct_image',
        'send_path': str(send_path),
        'send_mime_type': media_mime_type(str(send_path)),
        'preview_image': {
            'path': str(preview_path) if preview_path else '',
            'size_bytes': preview_size or 0,
        },
        'original_copy': {
            'path': str(original_copy_path) if original_copy_path else '',
            'size_bytes': original_copy_size or 0,
        },
        'original_zip': {
            'path': str(zip_path) if zip_path else '',
            'size_bytes': zip_size or 0,
        },
    }


def build_manifest(project_dir: Path, image_paths: list[Path], prepared_images: list[dict]) -> dict:
    image_path = image_paths[0]
    first = prepared_images[0]
    original_size = first['original_size_bytes']
    needs_preview = first['needs_preview']
    original_copy = first['original_copy']
    preview_image = first['preview_image']
    original_zip = first['original_zip']
    delivery_modes = {item['delivery_mode'] for item in prepared_images}
    aggregate_delivery_mode = prepared_images[0]['delivery_mode'] if len(delivery_modes) == 1 else 'mixed_candidates'
    manifest = {
        'project_dir': str(project_dir),
        'project_id': project_dir.name,
        'original_image': str(image_path),
        'generated_images': [str(p) for p in image_paths],
        'candidate_count': len(prepared_images),
        'original_size_bytes': original_size,
        'feishu_limit_bytes': FEISHU_LIMIT_BYTES,
        'needs_preview': needs_preview,
        'delivery_mode': aggregate_delivery_mode,
        'delivery_target': {
            'channel': 'feishu',
            'user_id': '',
            'chat_id': '',
        },
        'delivery_attempted': False,
        'delivery_attempted_at': None,
        'delivery_status': 'not_attempted',
        'delivery_method': 'feishu-send-image',
        'delivery_evidence': {
            'return_code': None,
            'stdout_tail': '',
            'stderr_tail': '',
            'sent_paths': [],
        },
        'fallback_required': False,
        'fallback_reason': '',
        'user_report': 'IMAGE READY BUT NOT DELIVERED TO USER',
        'deliverables': {
            'candidate_images': prepared_images,
            'preview_image': {
                'path': preview_image['path'],
                'size_bytes': preview_image['size_bytes'],
            },
            'original_copy': {
                'path': original_copy['path'],
                'size_bytes': original_copy['size_bytes'],
            },
            'original_zip': {
                'path': original_zip['path'],
                'size_bytes': original_zip['size_bytes'],
            },
        },
        'edit_source_image': str(image_path),
        'notes': {
            'preview_for_feishu_only': True,
            'edit_from_original_only': True,
            'zip_for_final_delivery_after_confirmation': needs_preview,
        },
        'error': '',
    }
    manifest['agent_delivery_contract'] = build_agent_delivery_contract(manifest)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description='Prepare Feishu delivery assets for brand poster output')
    parser.add_argument('--project-dir', required=True, help='Brand poster project directory')
    parser.add_argument('--image', default='', help='Original image path, defaults to project images/final_poster.png')
    args = parser.parse_args()

    project_dir = Path(args.project_dir).resolve()
    manager = ProjectManager(project_dir)
    if args.image:
        image_paths = [Path(args.image).resolve()]
    else:
        generation_result = {}
        generation_result_path = project_dir / 'generation_result.json'
        if generation_result_path.exists():
            try:
                generation_result = json.loads(generation_result_path.read_text(encoding='utf-8'))
            except json.JSONDecodeError:
                generation_result = {}
        raw_paths = generation_result.get('generated_paths') or generation_result.get('output_paths') or []
        image_paths = [Path(p).resolve() for p in raw_paths if str(p or '').strip()]
        if not image_paths:
            image_paths = [project_dir / 'images' / 'final_poster.png']

    missing = [str(path) for path in image_paths if not path.exists()]
    if missing:
        raise FileNotFoundError(f'原图不存在: {", ".join(missing)}')

    ensure_delivery_dir()

    project_id = project_dir.name

    manager.start_stage('delivery', reason='准备交付产物', actor='prepare_feishu_delivery.py')

    prepared_images = [
        prepare_single_image(image_path, project_id, index)
        for index, image_path in enumerate(image_paths, start=1)
    ]
    manifest = build_manifest(project_dir=project_dir, image_paths=image_paths, prepared_images=prepared_images)
    manifest_path = manager.write_stage_manifest('delivery', manifest)
    manager.state['stage_status']['delivery'] = 'running'
    manager.state['current_stage'] = 'delivery'
    manager.state['workflow_flags']['delivery_ready'] = False
    manager.state['artifacts']['delivery'] = str(manifest_path)
    manager.state['resume']['auto_resume_stage'] = 'delivery'
    manager.state['resume']['resume_reason'] = '交付物已整理完成，但尚未发送给用户。'
    manager.state['resume']['updated_at'] = now_iso()
    manager.save()
    manager.audit(
        'stage_needs_action',
        stage='delivery',
        status='running',
        actor='prepare_feishu_delivery.py',
        reason='交付物已整理完成，等待飞书真实发送。',
        files=[manager._relative(manifest_path)],
        attempt=manager.state['attempts'].get('delivery'),
        extra={'delivery_mode': manifest['delivery_mode'], 'delivery_status': manifest['delivery_status'], 'candidate_count': manifest['candidate_count']},
    )
    print(str(manifest_path))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
