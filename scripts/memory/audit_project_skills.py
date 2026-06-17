#!/usr/bin/env python3
"""
审计所有项目相关 skill 的记忆系统集成状态

检查规则：
1. 是否查询品牌档案
2. 是否创建/查询项目
3. 是否创建任务
4. 是否归档产出到任务系统
"""

import os
import json
from pathlib import Path

# 颜色输出
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def check_memory_integration(skill_md_path):
    """检查 SKILL.md 是否集成了记忆系统"""
    with open(skill_md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    results = {
        'has_brand_query': False,
        'has_project_query': False,
        'has_task_create': False,
        'has_output_archive': False,
        'mentions_brand': False,
        'mentions_project': False,
        'uses_old_path': False,
        'old_paths': []
    }

    # 检查是否查询品牌档案
    if 'query.py brand' in content or 'brand.py' in content or 'BRAND_INFO' in content or 'BRAND_TONE' in content:
        results['has_brand_query'] = True

    # 检查是否查询/创建项目
    if 'project.py get-or-create' in content or 'project.py get' in content or 'PROJECT_ID' in content or 'PROJECT_INFO' in content:
        results['has_project_query'] = True

    # 检查是否创建任务
    if 'task.py create' in content or 'TASK_ID' in content or 'TASK_INFO' in content:
        results['has_task_create'] = True

    # 检查是否归档产出
    if 'task.py save-output' in content or 'save-output' in content:
        results['has_output_archive'] = True

    # 检查是否提及品牌/项目关键词
    if any(kw in content.lower() for kw in ['品牌', 'brand', '档案', 'profile']):
        results['mentions_brand'] = True

    if any(kw in content.lower() for kw in ['项目', 'project', '立项']):
        results['mentions_project'] = True

    # 检查是否使用旧路径
    old_path_patterns = [
        'workspace/projects',
        'workspace-business/projects',
        'workspace-design/projects',
        'workspace-strategy/projects'
    ]

    for pattern in old_path_patterns:
        if pattern in content:
            results['uses_old_path'] = True
            results['old_paths'].append(pattern)

    return results

def categorize_skill(skill_name, skill_path):
    """根据 skill 名称和路径判断类别"""
    categories = []

    # 业务对接类
    if any(kw in skill_name for kw in ['business', 'intake', 'quote', 'kefu']):
        categories.append('业务对接')

    # 海报设计类
    if any(kw in skill_name for kw in ['poster', 'brand-poster']):
        categories.append('海报设计')

    # 视频生成类
    if any(kw in skill_name for kw in ['video', 'dreamina', 'tvc']):
        categories.append('视频生成')

    # 详情页设计类
    if any(kw in skill_name for kw in ['xiangqingye', 'detail-page']):
        categories.append('详情页设计')

    # 产品摄影类
    if any(kw in skill_name for kw in ['product-photography', 'photography']):
        categories.append('产品摄影')

    # 通用设计类
    if any(kw in skill_name for kw in ['sheji', 'design', 'image', 'gpt-image']):
        categories.append('通用设计')

    # 文案创作类
    if any(kw in skill_name for kw in ['wenan', 'copy']):
        categories.append('文案创作')

    # 策略类
    if any(kw in skill_name for kw in ['celue', 'strategy', 'chuangyi', 'creative']):
        categories.append('策略创意')

    # 全案类
    if 'boss' in skill_name:
        categories.append('品牌全案')

    return categories if categories else ['其他']

def main():
    openclaw_root = Path('/Users/a123/.openclaw')

    # 收集所有项目相关的 skill
    project_related_skills = []

    # 定义要检查的 skill 目录
    skill_dirs = [
        openclaw_root / 'skills',
        openclaw_root / 'workspace-business' / 'skills',
        openclaw_root / 'workspace-design' / 'skills',
        openclaw_root / 'workspace-copywriter' / 'skills',
        openclaw_root / 'workspace-strategy' / 'skills',
    ]

    for skill_dir in skill_dirs:
        if not skill_dir.exists():
            continue

        for skill_path in skill_dir.iterdir():
            if not skill_path.is_dir():
                continue

            skill_md = skill_path / 'SKILL.md'
            if not skill_md.exists():
                continue

            # 跳过 node_modules
            if 'node_modules' in str(skill_path):
                continue

            skill_name = skill_path.name
            categories = categorize_skill(skill_name, str(skill_path))

            # 只关注项目推进相关的 skill
            relevant_categories = [
                '业务对接', '海报设计', '视频生成', '详情页设计',
                '产品摄影', '通用设计', '文案创作', '策略创意', '品牌全案'
            ]

            if any(cat in relevant_categories for cat in categories):
                integration_status = check_memory_integration(skill_md)

                project_related_skills.append({
                    'name': skill_name,
                    'path': str(skill_path.relative_to(openclaw_root)),
                    'categories': categories,
                    'integration': integration_status
                })

    # 按类别分组并输出报告
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}")
    print(f"OpenClaw 项目推进相关 Skill 记忆系统集成审计报告")
    print(f"{'='*80}{Colors.ENDC}\n")

    # 按类别分组
    by_category = {}
    for skill in project_related_skills:
        for cat in skill['categories']:
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(skill)

    # 输出每个类别的集成状态
    for category in sorted(by_category.keys()):
        skills = by_category[category]
        print(f"\n{Colors.OKBLUE}{Colors.BOLD}## {category} ({len(skills)} 个 skill){Colors.ENDC}")
        print(f"{Colors.OKBLUE}{'─'*80}{Colors.ENDC}\n")

        for skill in skills:
            name = skill['name']
            integration = skill['integration']

            # 计算集成分数
            score = 0
            max_score = 4

            if integration['has_brand_query']:
                score += 1
            if integration['has_project_query']:
                score += 1
            if integration['has_task_create']:
                score += 1
            if integration['has_output_archive']:
                score += 1

            # 根据分数显示颜色
            if score == max_score:
                status_color = Colors.OKGREEN
                status = "✅ 完全集成"
            elif score >= 2:
                status_color = Colors.WARNING
                status = "⚠️  部分集成"
            elif integration['mentions_brand'] or integration['mentions_project']:
                status_color = Colors.WARNING
                status = "⚠️  待集成"
            else:
                status_color = Colors.FAIL
                status = "❌ 未集成"

            print(f"{status_color}{Colors.BOLD}{name}{Colors.ENDC} - {status_color}{status} ({score}/{max_score}){Colors.ENDC}")
            print(f"  路径: {skill['path']}")

            # 显示集成详情
            details = []
            if integration['has_brand_query']:
                details.append(f"{Colors.OKGREEN}✓ 品牌查询{Colors.ENDC}")
            else:
                details.append(f"{Colors.FAIL}✗ 品牌查询{Colors.ENDC}")

            if integration['has_project_query']:
                details.append(f"{Colors.OKGREEN}✓ 项目查询{Colors.ENDC}")
            else:
                details.append(f"{Colors.FAIL}✗ 项目查询{Colors.ENDC}")

            if integration['has_task_create']:
                details.append(f"{Colors.OKGREEN}✓ 任务创建{Colors.ENDC}")
            else:
                details.append(f"{Colors.FAIL}✗ 任务创建{Colors.ENDC}")

            if integration['has_output_archive']:
                details.append(f"{Colors.OKGREEN}✓ 产出归档{Colors.ENDC}")
            else:
                details.append(f"{Colors.FAIL}✗ 产出归档{Colors.ENDC}")

            print(f"  集成状态: {' | '.join(details)}")

            # 显示警告
            if integration['uses_old_path']:
                print(f"  {Colors.WARNING}⚠️  使用旧路径: {', '.join(integration['old_paths'])}{Colors.ENDC}")

            print()

    # 统计汇总
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}")
    print(f"统计汇总")
    print(f"{'='*80}{Colors.ENDC}\n")

    total = len(project_related_skills)
    fully_integrated = sum(1 for s in project_related_skills
                          if s['integration']['has_brand_query']
                          and s['integration']['has_project_query']
                          and s['integration']['has_task_create']
                          and s['integration']['has_output_archive'])
    partially_integrated = sum(1 for s in project_related_skills
                               if (s['integration']['has_brand_query']
                                   or s['integration']['has_project_query'])
                               and not (s['integration']['has_brand_query']
                                       and s['integration']['has_project_query']
                                       and s['integration']['has_task_create']
                                       and s['integration']['has_output_archive']))
    not_integrated = total - fully_integrated - partially_integrated

    print(f"总计: {total} 个项目推进相关 skill")
    print(f"{Colors.OKGREEN}✅ 完全集成: {fully_integrated}{Colors.ENDC}")
    print(f"{Colors.WARNING}⚠️  部分集成: {partially_integrated}{Colors.ENDC}")
    print(f"{Colors.FAIL}❌ 未集成: {not_integrated}{Colors.ENDC}")

    # 生成待办清单
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}")
    print(f"待办清单（优先级排序）")
    print(f"{'='*80}{Colors.ENDC}\n")

    # 按优先级排序（未集成但提及品牌/项目的优先）
    needs_integration = []
    for skill in project_related_skills:
        integration = skill['integration']
        score = sum([
            integration['has_brand_query'],
            integration['has_project_query'],
            integration['has_task_create'],
            integration['has_output_archive']
        ])

        if score < 4:
            priority = 0
            if integration['mentions_brand'] or integration['mentions_project']:
                priority = 1
            if score >= 1:
                priority = 2

            needs_integration.append({
                'skill': skill,
                'priority': priority,
                'score': score
            })

    needs_integration.sort(key=lambda x: (-x['priority'], -x['score']))

    priority_labels = {
        2: f"{Colors.WARNING}高优先级{Colors.ENDC}",
        1: f"{Colors.OKCYAN}中优先级{Colors.ENDC}",
        0: f"{Colors.OKBLUE}低优先级{Colors.ENDC}"
    }

    for item in needs_integration:
        skill = item['skill']
        priority = item['priority']
        score = item['score']

        print(f"{priority_labels[priority]} - {Colors.BOLD}{skill['name']}{Colors.ENDC} ({score}/4)")
        print(f"  类别: {', '.join(skill['categories'])}")

        # 列出缺失的集成点
        missing = []
        if not skill['integration']['has_brand_query']:
            missing.append("品牌查询")
        if not skill['integration']['has_project_query']:
            missing.append("项目查询")
        if not skill['integration']['has_task_create']:
            missing.append("任务创建")
        if not skill['integration']['has_output_archive']:
            missing.append("产出归档")

        print(f"  需要补充: {', '.join(missing)}")
        print()

    # 生成 JSON 报告
    report = {
        'total': total,
        'fully_integrated': fully_integrated,
        'partially_integrated': partially_integrated,
        'not_integrated': not_integrated,
        'skills': project_related_skills,
        'needs_integration': [
            {
                'name': item['skill']['name'],
                'path': item['skill']['path'],
                'categories': item['skill']['categories'],
                'priority': item['priority'],
                'score': item['score'],
                'missing': [
                    k for k, v in {
                        'brand_query': item['skill']['integration']['has_brand_query'],
                        'project_query': item['skill']['integration']['has_project_query'],
                        'task_create': item['skill']['integration']['has_task_create'],
                        'output_archive': item['skill']['integration']['has_output_archive']
                    }.items() if not v
                ]
            }
            for item in needs_integration
        ]
    }

    report_path = openclaw_root / 'scripts' / 'memory' / 'skill_integration_audit.json'
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n{Colors.OKGREEN}✅ 详细报告已保存到: {report_path}{Colors.ENDC}\n")

if __name__ == '__main__':
    main()
