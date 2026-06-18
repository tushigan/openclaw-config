#!/usr/bin/env python3
"""集成测试：验证 CLI 脚本在实际环境中的调用"""

import subprocess
import json
from pathlib import Path
import shutil

def run_command(cmd):
    """运行命令并返回结果"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr

def test_cli_find_brand_profile():
    """测试 CLI：find_brand_profile.py"""
    print('\n' + '='*80)
    print('集成测试1：find_brand_profile.py CLI')
    print('='*80)

    workspace = '/Users/a123/.openclaw/workspace'

    # 创建测试品牌
    from pathlib import Path
    import sys
    sys.path.insert(0, '/Users/a123/.openclaw/skills/boss/scripts')
    from agency_project import create_agency_project

    test_brand = '集成测试品牌_CLI'
    project_dir = create_agency_project(
        workspace_root=Path(workspace),
        brand_name=test_brand,
        campaign_name='测试项目',
        brand_info={'industry': '测试行业'}
    )

    # 测试 CLI 查询
    cmd = f'python3 /Users/a123/.openclaw/skills/boss/scripts/find_brand_profile.py --workspace-root {workspace} --brand-name "{test_brand}"'
    code, stdout, stderr = run_command(cmd)

    assert code == 0, f'命令执行失败: {stderr}'
    result = json.loads(stdout)
    assert result['found'] == True, '应该找到品牌档案'
    assert result['profile']['industry'] == '测试行业', '行业信息不匹配'

    print(f'✓ CLI 查询成功: found={result["found"]}')
    print(f'✓ 品牌信息: {result["profile"]["brand_name"]} - {result["profile"]["industry"]}')

    # 清理
    brand_dir = Path(workspace) / 'projects' / test_brand
    if brand_dir.exists():
        shutil.rmtree(brand_dir)

    print('✅ 集成测试1通过：find_brand_profile.py CLI 正常工作')

def test_cli_detect_conflicts():
    """测试 CLI：detect_brand_conflicts.py"""
    print('\n' + '='*80)
    print('集成测试2：detect_brand_conflicts.py CLI')
    print('='*80)

    workspace = '/Users/a123/.openclaw/workspace'

    # 创建测试品牌
    from pathlib import Path
    import sys
    sys.path.insert(0, '/Users/a123/.openclaw/skills/boss/scripts')
    from agency_project import create_agency_project

    test_brand = '集成测试品牌_冲突检测'
    project_dir = create_agency_project(
        workspace_root=Path(workspace),
        brand_name=test_brand,
        campaign_name='测试项目',
        brand_info={
            'industry': '烘焙',
            'brand_tone': '温暖',
            'core_values': ['新鲜']
        }
    )

    # 测试 CLI 检测冲突
    new_info_json = json.dumps({
        'industry': '餐饮',
        'core_values': ['新鲜', '品质']
    })

    cmd = f'python3 /Users/a123/.openclaw/skills/boss/scripts/detect_brand_conflicts.py --workspace-root {workspace} --brand-name "{test_brand}" --new-info \'{new_info_json}\''
    code, stdout, stderr = run_command(cmd)

    assert code == 0, f'命令执行失败: {stderr}'
    result = json.loads(stdout)

    assert result['has_conflict'] == True, '应该检测到冲突'
    assert len(result['conflicts']) >= 1, '应该有冲突记录'

    # 验证冲突详情
    industry_conflict = [c for c in result['conflicts'] if c['field'] == 'industry']
    assert len(industry_conflict) == 1, '应该检测到行业冲突'
    assert industry_conflict[0]['severity'] == 'high', '行业冲突应该是高严重性'

    print(f'✓ CLI 冲突检测成功: has_conflict={result["has_conflict"]}')
    print(f'✓ 冲突数量: {len(result["conflicts"])}')
    print(f'✓ 补充信息数量: {len(result["supplements"])}')

    # 清理
    brand_dir = Path(workspace) / 'projects' / test_brand
    if brand_dir.exists():
        shutil.rmtree(brand_dir)

    print('✅ 集成测试2通过：detect_brand_conflicts.py CLI 正常工作')

def test_cli_update_brand_profile():
    """测试 CLI：update_brand_profile.py"""
    print('\n' + '='*80)
    print('集成测试3：update_brand_profile.py CLI')
    print('='*80)

    workspace = '/Users/a123/.openclaw/workspace'

    # 创建测试品牌
    from pathlib import Path
    import sys
    sys.path.insert(0, '/Users/a123/.openclaw/skills/boss/scripts')
    from agency_project import create_agency_project, find_brand_profile

    test_brand = '集成测试品牌_更新'
    project_dir = create_agency_project(
        workspace_root=Path(workspace),
        brand_name=test_brand,
        campaign_name='测试项目',
        brand_info={'industry': '初始行业'}
    )

    # 测试 CLI replace 操作
    cmd = f'python3 /Users/a123/.openclaw/skills/boss/scripts/update_brand_profile.py --workspace-root {workspace} --brand-name "{test_brand}" --field "industry" --value "更新后行业" --operation replace'
    code, stdout, stderr = run_command(cmd)

    assert code == 0, f'replace命令执行失败: {stderr}'
    result = json.loads(stdout)
    assert result['success'] == True, 'replace操作应该成功'

    # 验证更新结果
    profile_path = find_brand_profile(Path(workspace), test_brand)
    profile = json.loads(profile_path.read_text(encoding='utf-8'))
    assert profile['industry'] == '更新后行业', 'replace操作未生效'

    print(f'✓ CLI replace 操作成功')

    # 测试 CLI append 操作
    value_json = json.dumps(['价值观1', '价值观2'])
    cmd = f'python3 /Users/a123/.openclaw/skills/boss/scripts/update_brand_profile.py --workspace-root {workspace} --brand-name "{test_brand}" --field "core_values" --value \'{value_json}\' --operation append'
    code, stdout, stderr = run_command(cmd)

    assert code == 0, f'append命令执行失败: {stderr}'
    result = json.loads(stdout)
    assert result['success'] == True, 'append操作应该成功'

    # 验证append结果
    profile_path = find_brand_profile(Path(workspace), test_brand)
    profile = json.loads(profile_path.read_text(encoding='utf-8'))
    assert len(profile['core_values']) == 2, 'append操作未生效'

    print(f'✓ CLI append 操作成功')

    # 清理
    brand_dir = Path(workspace) / 'projects' / test_brand
    if brand_dir.exists():
        shutil.rmtree(brand_dir)

    print('✅ 集成测试3通过：update_brand_profile.py CLI 正常工作')

def test_init_agency_project():
    """测试：init_agency_project.py 集成"""
    print('\n' + '='*80)
    print('集成测试4：init_agency_project.py 集成')
    print('='*80)

    workspace = '/Users/a123/.openclaw/workspace'
    test_brand = '集成测试品牌_立项'

    # 测试 CLI 创建项目
    cmd = f'''python3 /Users/a123/.openclaw/skills/boss/scripts/init_agency_project.py \
        --workspace-root {workspace} \
        --brand-name "{test_brand}" \
        --campaign-name "春节项目" \
        --industry "烘焙" \
        --target-audience "25-35岁女性" \
        --core-values "新鲜,手作,用心"'''

    code, stdout, stderr = run_command(cmd)

    assert code == 0, f'命令执行失败: {stderr}'
    result = json.loads(stdout)

    print(f'✓ 项目创建成功: {result["project_dir"]}')

    # 验证品牌档案已创建
    from pathlib import Path
    import sys
    sys.path.insert(0, '/Users/a123/.openclaw/skills/boss/scripts')
    from agency_project import find_brand_profile

    profile_path = find_brand_profile(Path(workspace), test_brand)
    assert profile_path is not None, '品牌档案应该存在'

    profile = json.loads(profile_path.read_text(encoding='utf-8'))
    assert profile['industry'] == '烘焙', '行业信息不匹配'
    assert profile['target_audience'] == '25-35岁女性', '目标受众不匹配'
    assert set(profile['core_values']) == {'新鲜', '手作', '用心'}, '核心价值观不匹配'

    print(f'✓ 品牌档案验证通过')

    # 清理
    brand_dir = Path(workspace) / 'projects' / test_brand
    if brand_dir.exists():
        shutil.rmtree(brand_dir)

    print('✅ 集成测试4通过：init_agency_project.py 集成正常')

def cleanup_all_test_brands():
    """清理所有测试品牌"""
    workspace = Path('/Users/a123/.openclaw/workspace')
    registry_path = workspace / 'projects' / '_registry.json'

    test_brands = [
        '集成测试品牌_CLI',
        '集成测试品牌_冲突检测',
        '集成测试品牌_更新',
        '集成测试品牌_立项'
    ]

    for brand_name in test_brands:
        brand_dir = workspace / 'projects' / brand_name
        if brand_dir.exists():
            shutil.rmtree(brand_dir)

    if registry_path.exists():
        registry = json.loads(registry_path.read_text(encoding='utf-8'))
        registry['brands'] = {k: v for k, v in registry['brands'].items()
                              if not any(test in k for test in test_brands)}
        registry['projects'] = {k: v for k, v in registry['projects'].items()
                                if not any(test in v.get('brand_name', '') for test in test_brands)}
        registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2), encoding='utf-8')

def run_all_integration_tests():
    """运行所有集成测试"""
    print('\n')
    print('╔' + '═'*78 + '╗')
    print('║' + ' '*25 + 'CLI 集成测试' + ' '*39 + '║')
    print('╚' + '═'*78 + '╝')

    try:
        cleanup_all_test_brands()

        test_cli_find_brand_profile()
        test_cli_detect_conflicts()
        test_cli_update_brand_profile()
        test_init_agency_project()

        cleanup_all_test_brands()

        print('\n' + '='*80)
        print('✅ 所有集成测试通过！CLI 脚本在实际环境中正常工作。')
        print('='*80)
        return True

    except AssertionError as e:
        print(f'\n❌ 集成测试失败: {e}')
        return False
    except Exception as e:
        print(f'\n❌ 集成测试异常: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = run_all_integration_tests()
    exit(0 if success else 1)
