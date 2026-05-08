#!/usr/bin/env python3
"""Project manager for detail page generation.

Manages project directory structure, version control, status board,
and Feishu report generation.

Usage:
  # Initialize project
  python project_manager.py init "卡宾熊法式可丽饼" \
    --segments A,B,C,D,E,F --output outputs/

  # Store file (auto versioning)
  python project_manager.py put 手稿 A --file wf_A.png --project-dir outputs/卡宾熊...

  # Update status
  python project_manager.py status A approved --project-dir outputs/卡宾熊...
  python project_manager.py status C revision "产品图太小" --project-dir outputs/卡宾熊...

  # View status
  python project_manager.py report --project-dir outputs/卡宾熊...

  # Get current file path
  python project_manager.py get 手稿 A --project-dir outputs/卡宾熊...

  # Feishu report
  python project_manager.py feishu-report --phase 2 --project-dir outputs/卡宾熊...
"""
import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path


# Status icons
STATUS_ICONS = {
    'approved': '✅',
    'revision': '🔄',
    'pending': '⏳',
    'generating': '⚙️',
    'rejected': '❌',
}

# Category directory names
CATEGORY_DIRS = {
    '策划': 'copywriting',
    '手稿': 'wireframes',
    '设计': 'designs',
    '参考': 'references',
}


class ProjectManager:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.progress_file = project_dir / 'progress.json'
        self.progress = self._load_progress()

    def _load_progress(self) -> dict:
        if self.progress_file.exists():
            progress = json.loads(self.progress_file.read_text(encoding='utf-8'))
            self.progress = progress
            self._workflow_flags()
            return self.progress
        return None

    def _save_progress(self):
        self.progress_file.write_text(
            json.dumps(self.progress, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )

    def _workflow_flags(self) -> dict:
        flags = self.progress.setdefault('workflow_flags', {})
        flags.setdefault('head_images_required', True)
        flags.setdefault('head_images_asked', False)
        flags.setdefault('head_images_generated', False)
        flags.setdefault('head_images_delivered', False)
        flags.setdefault('long_image_required', True)
        flags.setdefault('long_image_generated', False)
        flags.setdefault('long_image_delivered', False)
        flags.setdefault('copywriting_confirmed', False)
        flags.setdefault('delivery_mode', 'zip_file')
        flags.setdefault('delivery_ready', False)
        flags.setdefault('delivery_packaged', False)
        flags.setdefault('delivery_confirmed', False)
        flags.setdefault('delivered', False)
        flags.setdefault('closeout_blocked', False)
        flags.setdefault('closeout_note', '')
        flags.setdefault('brand_assets_discovered', False)
        flags.setdefault('brand_assets_confirmed', False)
        flags.setdefault('brand_knowledge_discovered', False)
        flags.setdefault('brand_knowledge_confirmed', False)
        return flags

    def _read_json_file(self, path: Path) -> dict:
        if not path.exists():
            return {}
        try:
            return json.loads(path.read_text(encoding='utf-8'))
        except Exception:
            return {}

    def _asset_retrieval_summary(self) -> tuple[str, int, int]:
        flags = self._workflow_flags()
        candidate_path = self.project_dir / '参考' / 'brand_asset_candidates.json'
        confirmed_path = self.project_dir / '参考' / 'brand_asset_confirmed.json'
        candidates = self._read_json_file(candidate_path).get('candidates', []) if candidate_path.exists() else []
        confirmed = self._read_json_file(confirmed_path).get('confirmed_assets', []) if confirmed_path.exists() else []
        flags['brand_assets_discovered'] = len(candidates) > 0
        flags['brand_assets_confirmed'] = len(confirmed) > 0
        if confirmed:
            return '已确认', len(candidates), len(confirmed)
        if candidates:
            return '待确认', len(candidates), 0
        return '未检索', 0, 0

    def _knowledge_retrieval_summary(self) -> tuple[str, str, int, int]:
        flags = self._workflow_flags()
        candidate_path = self.project_dir / '策划' / 'brand_knowledge_candidates.json'
        confirmed_path = self.project_dir / '策划' / 'brand_knowledge_confirmed.json'
        candidate_data = self._read_json_file(candidate_path)
        confirmed_data = self._read_json_file(confirmed_path)
        queries = candidate_data.get('queries', []) if candidate_path.exists() else []
        confirmed_items = confirmed_data.get('confirmed_items', []) if confirmed_path.exists() else []
        dataset_name = confirmed_data.get('matched_dataset_name') or candidate_data.get('matched_dataset_name') or '未匹配'
        flags['brand_knowledge_discovered'] = len(queries) > 0
        flags['brand_knowledge_confirmed'] = len(confirmed_items) > 0
        if confirmed_items:
            return '已确认', dataset_name, len(queries), len(confirmed_items)
        if queries:
            return '待确认', dataset_name, len(queries), 0
        return '未检索', dataset_name, 0, 0

    def _head_image_summary(self) -> tuple[str, int]:
        flags = self._workflow_flags()
        if not flags.get('head_images_required', True):
            flags['head_images_generated'] = False
            return '不要求', 0
        head_dir = self.project_dir / '头图'
        if not head_dir.exists():
            flags['head_images_generated'] = False
            return '待生成', 0
        head_files = sorted(head_dir.glob('v*/head_*.png'))
        if not head_files:
            head_files = sorted(head_dir.glob('head_*.png'))
        count = len(head_files)
        if count == 0:
            flags['head_images_generated'] = False
            return '待生成', 0
        flags['head_images_generated'] = True
        return '已生成', count

    def _long_image_summary(self) -> tuple[str, int]:
        flags = self._workflow_flags()
        if not flags.get('long_image_required', True):
            flags['long_image_generated'] = False
            return '不要求', 0
        candidates = [
            self.project_dir / '设计' / 'merged_final.png',
            self.project_dir / '交付' / 'merged_final.png',
        ]
        design_dir = self.project_dir / '设计'
        if design_dir.exists():
            candidates.extend(sorted(design_dir.glob('v*/merged_final*.png')))
        deliver_dir = self.project_dir / '交付'
        if deliver_dir.exists():
            candidates.extend(sorted(deliver_dir.glob('**/merged_final*.png')))
        existing = [path for path in candidates if path.exists()]
        if not existing:
            flags['long_image_generated'] = False
            return '待生成', 0
        flags['long_image_generated'] = True
        return '已生成', len(existing)

    def _cut_confirmation_summary(self) -> tuple[str, list[str]]:
        notes = []
        wireframe_dir = self.project_dir / '手稿'
        if not wireframe_dir.exists():
            return '未准备', notes
        manifests = sorted(wireframe_dir.glob('v*/cut_preview/cut_manifest.json'))
        if not manifests:
            manifests = sorted(wireframe_dir.glob('cut_preview_*/cut_manifest.json'))
        if not manifests:
            return '未准备', notes
        manifest_path = manifests[-1]
        data = self._read_json_file(manifest_path)
        status = data.get('status') or 'unknown'
        segments = data.get('segments', []) if isinstance(data.get('segments'), list) else []
        sources = sorted({str(item.get('source') or 'unknown') for item in segments if isinstance(item, dict)})
        if sources:
            notes.append('切点来源: ' + ' / '.join(sources))
        notes.append(f'确认清单: {manifest_path.relative_to(self.project_dir)}')
        if status == 'confirmed':
            return '已确认', notes
        return '待确认', notes

    def _delivery_summary(self) -> tuple[str, list[str]]:
        flags = self._workflow_flags()
        deliver_dir = self.project_dir / '交付'
        notes = []
        if not deliver_dir.exists():
            return '未准备', notes
        zip_files = sorted(deliver_dir.glob('*.zip'))
        split_files = sorted(deliver_dir.glob('*.z[0-9][0-9]'))
        if zip_files or split_files:
            flags['delivery_packaged'] = True
            notes.append(f'交付包 {len(zip_files)} 个 ZIP / {len(split_files)} 个分卷')
            return '已打包', notes
        confirmed_pngs = sorted(deliver_dir.glob('*confirmed*.png'))
        if confirmed_pngs:
            notes.append(f'已整理确认稿 {len(confirmed_pngs)} 个')
            return '待打包', notes
        return '未准备', notes

    def init_project(self, name: str, segments: list[str], output_dir: Path = None):
        """Initialize project directory structure."""
        timestamp = datetime.now().strftime('%Y%m%d')
        project_name = f'{name}_{timestamp}'
        if output_dir:
            self.project_dir = Path(output_dir) / project_name
        else:
            self.project_dir = Path(project_name)

        self.project_dir.mkdir(parents=True, exist_ok=True)
        self.progress_file = self.project_dir / 'progress.json'

        # Create category directories
        for cat in CATEGORY_DIRS:
            (self.project_dir / cat).mkdir(exist_ok=True)

        # Create references subfolder
        (self.project_dir / '参考').mkdir(exist_ok=True)

        # Initialize progress
        self.progress = {
            'project': name,
            'created': datetime.now().isoformat(),
            'phase': 'planning',  # planning → wireframe → design → done
            'workflow_flags': {
                'head_images_required': True,
                'head_images_generated': False,
                'head_images_delivered': False,
                'long_image_required': True,
                'long_image_generated': False,
                'long_image_delivered': False,
                'delivery_mode': 'zip_file',
                'delivery_ready': False,
                'delivery_packaged': False,
                'delivery_confirmed': False,
                'delivered': False,
                'closeout_blocked': False,
                'closeout_note': '',
                'brand_assets_discovered': False,
                'brand_assets_confirmed': False,
                'brand_knowledge_discovered': False,
                'brand_knowledge_confirmed': False,
            },
            'segments': {},
            'deliverables': {
                'facts': None,
                'strategy': None,
                'copywriting': None,
                'style_guide': None,
                'typography_ref': None,
                'merged_final': None,
            },
        }
        for seg in segments:
            self.progress['segments'][seg] = {
                'status': 'pending',
                'version': 0,
                'wireframe': None,
                'design': None,
                'feedback': None,
            }
        self._save_progress()
        print(f'项目已创建: {self.project_dir}')
        print(f'分段: {", ".join(segments)}')
        print(f'目录结构:')
        for f in sorted(self.project_dir.rglob('*')):
            if f.is_dir():
                indent = '  ' * (len(f.parts) - len(self.project_dir.parts))
                print(f'{indent}{f.name}/')

    def get_next_version(self, category: str) -> int:
        """Get next version number for a category."""
        cat_dir = self.project_dir / category
        if not cat_dir.exists():
            return 1
        versions = [int(d.name[1:]) for d in cat_dir.iterdir()
                   if d.is_dir() and d.name.startswith('v') and d.name[1:].isdigit()]
        return max(versions, default=0) + 1

    def put_file(self, category: str, segment_id: str, file_path: str,
                 is_global: bool = False):
        """Store file with auto versioning."""
        src = Path(file_path)
        if not src.exists():
            print(f'错误: 文件不存在 {file_path}')
            return None

        if is_global:
            # Global files go directly to project root
            dest = self.project_dir / src.name
            shutil.copy2(src, dest)
            print(f'已保存: {dest}')
            return str(dest)

        # Get next version
        version = self.get_next_version(category)

        # Create version directory
        version_dir = self.project_dir / category / f'v{version}'
        version_dir.mkdir(parents=True, exist_ok=True)

        # Copy file
        dest = version_dir / src.name
        shutil.copy2(src, dest)

        # Update progress
        if segment_id in self.progress.get('segments', {}):
            seg = self.progress['segments'][segment_id]
            seg['version'] = version
            if category == '手稿':
                seg['wireframe'] = str(dest.relative_to(self.project_dir))
            elif category == '设计':
                seg['design'] = str(dest.relative_to(self.project_dir))

        self._save_progress()
        print(f'已保存: {dest} (版本 v{version})')
        return str(dest)

    def update_status(self, segment_id: str, status: str, feedback: str = None):
        """Update segment status."""
        if segment_id not in self.progress.get('segments', {}):
            print(f'错误: 分段 {segment_id} 不存在')
            return

        seg = self.progress['segments'][segment_id]
        seg['status'] = status
        if feedback:
            seg['feedback'] = feedback
        self._save_progress()
        icon = STATUS_ICONS.get(status, '?')
        msg = f'{segment_id}: {icon} {status}'
        if feedback:
            msg += f' — {feedback}'
        print(msg)

    def get_file(self, category: str, segment_id: str) -> str:
        """Get current confirmed file path for a segment."""
        if segment_id not in self.progress.get('segments', {}):
            print(f'错误: 分段 {segment_id} 不存在')
            return None

        seg = self.progress['segments'][segment_id]
        if category == '手稿':
            return seg.get('wireframe')
        elif category == '设计':
            return seg.get('design')
        return None

    def report(self) -> str:
        """Generate status report."""
        if not self.progress:
            return '项目未初始化'

        flags = self._workflow_flags()
        head_status, head_count = self._head_image_summary()
        long_image_status, long_image_count = self._long_image_summary()
        cut_status, cut_notes = self._cut_confirmation_summary()
        delivery_status, delivery_notes = self._delivery_summary()
        asset_status, asset_candidates, asset_confirmed = self._asset_retrieval_summary()
        knowledge_status, knowledge_dataset, knowledge_queries, knowledge_confirmed = self._knowledge_retrieval_summary()

        lines = []
        phase = self.progress.get('phase', 'unknown')
        lines.append(f'项目: {self.progress.get("project", "?")}')
        lines.append(f'阶段: {phase}')
        lines.append('')

        status_parts = []
        for seg_id, seg in self.progress.get('segments', {}).items():
            icon = STATUS_ICONS.get(seg['status'], '?')
            version = seg.get('version', 0)
            status_parts.append(f'{seg_id}{icon}(v{version})')
            if seg.get('feedback'):
                status_parts[-1] += f' {seg["feedback"]}'

        lines.append('状态: ' + '  '.join(status_parts))
        lines.append(f'品牌资产: {asset_status}（候选 {asset_candidates} / 已确认 {asset_confirmed}）')
        lines.append(f'品牌知识: {knowledge_status}（知识库: {knowledge_dataset}；检索 {knowledge_queries} / 已确认 {knowledge_confirmed}）')
        lines.append(f'切段确认: {cut_status}')
        lines.append(f'逐屏文案: {"已确认" if flags.get("copywriting_confirmed", False) else "待确认"}')
        lines.append(f'长图: {long_image_status}' + (f'（{long_image_count} 个候选）' if long_image_count else ''))
        lines.append(f'头图: {head_status}' + (f'（{head_count} 张）' if head_count else ''))
        lines.append(f'最终交付: {delivery_status}（模式: {flags.get("delivery_mode", "zip_file")}）')
        lines.append('阶段重读门禁: 进入手稿/成稿/头图/交付前，必须重新读取项目标准文件')
        lines.append('成稿阶段入口: 先生成设计段 prompt，再执行分段成稿脚本')
        for note in cut_notes + delivery_notes:
            lines.append(f'- {note}')

        dels = self.progress.get('deliverables', {})
        available = [k for k, v in dels.items() if v]
        if available:
            lines.append(f'产出物: {", ".join(available)}')

        segments = self.progress.get('segments', {})
        approved = sum(1 for s in segments.values() if s['status'] == 'approved')
        total = len(segments)
        lines.append(f'进度: {approved}/{total} 段已确认')
        if cut_status != '已确认':
            lines.append('提醒: 切段尚未完成 confirmed 清单，不能进入正式成稿。')
        if flags.get('long_image_required', True) and not flags.get('long_image_generated', False):
            lines.append('提醒: 本项目仍缺最终长图产物，不能按整套完成收口。')
        if flags.get('head_images_required', True) and head_count == 0:
            lines.append('提醒: 本项目仍缺头图交付，不能按整套完成收口。')

        return '\n'.join(lines)

    def feishu_report(self, phase: int = None) -> str:
        """Generate Feishu-formatted report."""
        if not self.progress:
            return '项目未初始化'

        flags = self._workflow_flags()
        head_status, head_count = self._head_image_summary()
        long_image_status, long_image_count = self._long_image_summary()
        cut_status, cut_notes = self._cut_confirmation_summary()
        delivery_status, delivery_notes = self._delivery_summary()
        asset_status, asset_candidates, asset_confirmed = self._asset_retrieval_summary()
        knowledge_status, knowledge_dataset, knowledge_queries, knowledge_confirmed = self._knowledge_retrieval_summary()

        current_phase = self.progress.get('phase', 'unknown')
        if phase:
            phase_names = {1: '策略确认', 2: '手稿确认', 3: '成稿确认'}
            phase_name = phase_names.get(phase, current_phase)
        else:
            phase_name = current_phase

        lines = []
        lines.append(f'【阶段 {phase or "?"}：{phase_name}】')

        status_parts = []
        for seg_id, seg in self.progress.get('segments', {}).items():
            icon = STATUS_ICONS.get(seg['status'], '?')
            version = seg.get('version', 0)
            part = f'{seg_id}{icon}(v{version})'
            if seg.get('feedback') and seg['status'] == 'revision':
                part += f' {seg["feedback"]}'
            status_parts.append(part)
        lines.append('状态: ' + '  '.join(status_parts))
        lines.append(f'品牌资产: {asset_status}（候选 {asset_candidates} / 已确认 {asset_confirmed}）')
        lines.append(f'品牌知识: {knowledge_status}（知识库: {knowledge_dataset}；检索 {knowledge_queries} / 已确认 {knowledge_confirmed}）')
        lines.append(f'切段确认: {cut_status}')
        lines.append(f'逐屏文案: {"已确认" if flags.get("copywriting_confirmed", False) else "待确认"}')
        lines.append(f'长图: {long_image_status}' + (f'（{long_image_count} 个候选）' if long_image_count else ''))
        lines.append(f'头图: {head_status}' + (f'（{head_count} 张）' if head_count else ''))
        lines.append(f'最终交付: {delivery_status}（模式: {flags.get("delivery_mode", "zip_file")}）')
        lines.append('阶段重读门禁: 进入手稿/成稿/头图/交付前，必须重新读取项目标准文件')
        lines.append('成稿阶段入口: 先生成设计段 prompt，再执行分段成稿脚本')
        for note in cut_notes + delivery_notes:
            lines.append(f'- {note}')

        lines.append('本次产出:')
        dels = self.progress.get('deliverables', {})
        for key, val in dels.items():
            if val:
                lines.append(f'- {val}')

        for cat in ['手稿', '设计', '头图']:
            cat_dir = self.project_dir / cat
            if cat_dir.exists():
                versions = sorted([d for d in cat_dir.iterdir()
                                  if d.is_dir() and d.name.startswith('v')],
                                 key=lambda x: int(x.name[1:]))
                if versions:
                    latest = versions[-1]
                    for f in latest.iterdir():
                        if f.is_file():
                            lines.append(f'- {cat}/{latest.name}/{f.name}')

        segments = self.progress.get('segments', {})
        approved = sum(1 for s in segments.values() if s['status'] == 'approved')
        total = len(segments)
        lines.append(f'进度: {approved}/{total} 段已确认')
        if cut_status != '已确认':
            lines.append('提醒: 切段尚未完成 confirmed 清单，不能进入正式成稿。')
        if flags.get('long_image_required', True) and not flags.get('long_image_generated', False):
            lines.append('提醒: 本项目仍缺最终长图产物，不能按整套完成收口。')
        if flags.get('head_images_required', True) and head_count == 0:
            lines.append('提醒: 本项目仍缺头图交付，不能按整套完成收口。')
        if asset_status == '待确认':
            lines.append('提醒: 已检索到品牌资产候选，用户确认前不得写入正式素材注册表。')
        if knowledge_status == '待确认':
            lines.append('提醒: 已检索到品牌知识候选，用户确认前不得写入正式 prompt package。')
        if delivery_status != '已打包':
            lines.append('提醒: 最终交付仍需走 ZIP/分卷文件发送。')
        lines.append('请确认或反馈 →')

        return '\n'.join(lines)

    def update_phase(self, phase: str):
        """Update project phase, with hard gate checks."""
        if phase == 'wireframe':
            planning_dir = self.project_dir / '策划'
            cw_files = list(planning_dir.glob('copywriting_v*.md')) if planning_dir.exists() else []
            if not cw_files:
                print('门禁拦截: 缺少逐屏文案文件 (策划/copywriting_v*.md)，不能进入手稿阶段')
                print('请先完成阶段 1.2 逐屏文案，再进入阶段 2 手稿')
                return
            flags = self._workflow_flags()
            if not flags.get('copywriting_confirmed', False):
                print('门禁拦截: 逐屏文案尚未得到用户确认，不能进入手稿阶段')
                print('请先将逐屏文案全文发给用户确认，确认后再进入阶段 2 手稿')
                return
            head_dir = self.project_dir / '头图'
            head_strategy = planning_dir / 'head_image_strategy_v1.md' if planning_dir.exists() else None
            if flags.get('head_images_required', True):
                head_asked = flags.get('head_images_asked', False)
                if not head_asked:
                    print('门禁提醒: 头图需求尚未确认，默认 head_images_required=true')
                    print('请在手稿开始前明确是否需要配套头图')

        self.progress['phase'] = phase
        self._save_progress()
        print(f'阶段已更新: {phase}')

    def update_deliverable(self, name: str, file_path: str):
        """Update a global deliverable."""
        if 'deliverables' not in self.progress:
            self.progress['deliverables'] = {}

        src = Path(file_path)
        if src.exists():
            dest = self.project_dir / src.name
            shutil.copy2(src, dest)
            self.progress['deliverables'][name] = str(dest.relative_to(self.project_dir))
            self._save_progress()
            print(f'产出物已保存: {name} -> {dest}')
        else:
            self.progress['deliverables'][name] = file_path
            self._save_progress()
            print(f'产出物路径已记录: {name} -> {file_path}')


def main():
    ap = argparse.ArgumentParser(description='Detail page project manager')
    ap.add_argument('--project-dir', default='',
                    help='Project directory path')

    sub = ap.add_subparsers(dest='command')

    # init
    p_init = sub.add_parser('init', help='Initialize project')
    p_init.add_argument('name', help='Project name')
    p_init.add_argument('--segments', required=True,
                        help='Comma-separated segment IDs (e.g. A,B,C,D,E,F)')
    p_init.add_argument('--output', default='outputs',
                        help='Output base directory (default outputs)')

    # put
    p_put = sub.add_parser('put', help='Store file with auto versioning')
    p_put.add_argument('--project-dir', required=True, help='Project directory path')
    p_put.add_argument('category', choices=['手稿', '设计', '策划', '参考'],
                       help='File category')
    p_put.add_argument('segment', help='Segment ID (or "global" for global files)')
    p_put.add_argument('--file', required=True, help='Source file path')

    # status
    p_status = sub.add_parser('status', help='Update segment status')
    p_status.add_argument('--project-dir', required=True, help='Project directory path')
    p_status.add_argument('segment', help='Segment ID')
    p_status.add_argument('state',
                          choices=['approved', 'revision', 'pending', 'generating', 'rejected'])
    p_status.add_argument('--feedback', default='', help='Feedback text')

    # get
    p_get = sub.add_parser('get', help='Get current file path')
    p_get.add_argument('--project-dir', required=True, help='Project directory path')
    p_get.add_argument('category', choices=['手稿', '设计'],
                       help='File category')
    p_get.add_argument('segment', help='Segment ID')

    # report
    p_report = sub.add_parser('report', help='Generate status report')
    p_report.add_argument('--project-dir', required=True, help='Project directory path')

    # feishu-report
    p_feishu = sub.add_parser('feishu-report', help='Generate Feishu report')
    p_feishu.add_argument('--project-dir', required=True, help='Project directory path')
    p_feishu.add_argument('--phase', type=int, default=0,
                          help='Phase number (1/2/3)')

    # update-phase
    p_uphase = sub.add_parser('update-phase', help='Update project phase')
    p_uphase.add_argument('--project-dir', required=True, help='Project directory path')
    p_uphase.add_argument('phase',
                          choices=['planning', 'wireframe', 'design', 'done'])

    # update-deliverable
    p_updel = sub.add_parser('update-deliverable', help='Update global deliverable')
    p_updel.add_argument('--project-dir', required=True, help='Project directory path')
    p_updel.add_argument('name', help='Deliverable name')
    p_updel.add_argument('--file', required=True, help='Source file path')

    # set-head-flag
    p_head = sub.add_parser('set-head-flag', help='Set head image requirement flag')
    p_head.add_argument('--project-dir', required=True, help='Project directory path')
    p_head.add_argument('--required', action='store_true', help='Head images are required')
    p_head.add_argument('--not-required', action='store_true', help='Head images are not required for this project')

    # set-copywriting-flag
    p_cw = sub.add_parser('set-copywriting-flag', help='Mark copywriting as confirmed by user')
    p_cw.add_argument('--project-dir', required=True, help='Project directory path')
    p_cw.add_argument('--confirmed', action='store_true', help='User has confirmed the copywriting')

    args = ap.parse_args()

    if args.command == 'init':
        segments = [s.strip() for s in args.segments.split(',') if s.strip()]
        pm = ProjectManager(Path('.'))
        pm.init_project(args.name, segments, args.output)
        return

    pm = ProjectManager(Path(args.project_dir))

    if args.command == 'put':
        is_global = args.segment == 'global'
        pm.put_file(args.category, args.segment, args.file, is_global)
    elif args.command == 'status':
        pm.update_status(args.segment, args.state, args.feedback or None)
    elif args.command == 'get':
        path = pm.get_file(args.category, args.segment)
        if path:
            print(path)
    elif args.command == 'report':
        print(pm.report())
    elif args.command == 'feishu-report':
        print(pm.feishu_report(args.phase if args.phase > 0 else None))
    elif args.command == 'update-phase':
        pm.update_phase(args.phase)
    elif args.command == 'update-deliverable':
        pm.update_deliverable(args.name, args.file)
    elif args.command == 'set-head-flag':
        flags = pm._workflow_flags()
        if args.not_required:
            flags['head_images_required'] = False
            flags['head_images_asked'] = True
            pm._save_progress()
            print('头图要求已设置为 false（用户明确不需要头图）')
        elif args.required:
            flags['head_images_required'] = True
            flags['head_images_asked'] = True
            pm._save_progress()
            print('头图要求已设置为 true，请继续生成头图策略与头图')
        else:
            print('必须指定 --required 或 --not-required')
    elif args.command == 'set-copywriting-flag':
        flags = pm._workflow_flags()
        if args.confirmed:
            flags['copywriting_confirmed'] = True
            pm._save_progress()
            print('逐屏文案已标记为用户确认，可进入后续阶段')
        else:
            print('必须指定 --confirmed')
    else:
        ap.print_help()


if __name__ == '__main__':
    main()
