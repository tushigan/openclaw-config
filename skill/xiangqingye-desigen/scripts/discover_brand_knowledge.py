#!/usr/bin/env python3
"""为详情页项目执行 Dify 品牌知识候选检索。"""

import argparse
import json
import subprocess
from datetime import datetime
from pathlib import Path

ROOT = Path('/Users/a123/.openclaw')
AUTO_DISCOVER = ROOT / 'skills-store' / 'dify-rag' / 'scripts' / 'auto_discover.py'

DEFAULT_QUERIES = [
    '品牌视觉规范 主色调 视觉关键词',
    '品牌文案风格 语气语调 禁忌表达',
    '品牌历史卖点 口号 Slogan',
]


def run_query(brand: str, query_suffix: str, top_k: int) -> dict:
    query = f'{brand} {query_suffix}'
    result = subprocess.run(
        [
            'python3', str(AUTO_DISCOVER),
            '--query', query,
            '--context-brand', brand,
            '--top-k', str(top_k),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return {
            'query': query,
            'records': [],
            'message': result.stderr.strip() or 'auto_discover 执行失败',
        }
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        data = {
            'records': [],
            'message': 'auto_discover 输出不是合法 JSON',
            'raw_output': result.stdout[:500],
        }
    data['query'] = query
    return data


def main():
    parser = argparse.ArgumentParser(description='生成项目级品牌知识候选结果')
    parser.add_argument('--project-dir', required=True, help='项目目录')
    parser.add_argument('--brand', required=True, help='品牌名')
    parser.add_argument('--top-k', type=int, default=5, help='每个查询返回条数')
    args = parser.parse_args()

    project_dir = Path(args.project_dir)
    if not project_dir.exists():
        raise SystemExit(f'项目目录不存在: {project_dir}')

    queries = [run_query(args.brand, suffix, args.top_k) for suffix in DEFAULT_QUERIES]
    matched = next((q.get('matched_dataset') for q in queries if q.get('matched_dataset')), {}) or {}
    output_dir = project_dir / '策划'
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / 'brand_knowledge_candidates.json'
    payload = {
        'project': project_dir.name,
        'brand': args.brand,
        'generated_at': datetime.now().isoformat(),
        'matched_dataset_name': matched.get('name', '未匹配'),
        'matched_dataset_id': matched.get('id'),
        'match_score': matched.get('match_score'),
        'queries': queries,
        'message': '候选知识仅供确认，未确认前不得写入正式 prompt package。',
    }
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    print(output_path)
    print(f'queries={len(queries)}')


if __name__ == '__main__':
    main()
