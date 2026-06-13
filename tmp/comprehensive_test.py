#!/usr/bin/env python3
"""综合压力测试：Boss skill 项目记忆系统自动增长与冲突处理"""

from pathlib import Path
from agency_project import (
    create_agency_project,
    find_brand_profile,
    detect_conflicts,
    update_brand_profile_field
)
import json
import shutil

def cleanup_test_brands():
    """清理测试数据"""
    workspace = Path('/Users/a123/.openclaw/workspace')
    registry_path = workspace / 'projects' / '_registry.json'

    test_brands = [
        '压力测试品牌A',
        '压力测试品牌B',
        '压力测试品牌C',
        '边界测试品牌',
        '空值测试品牌',
        '中文测试品牌',
        '特殊字符测试_Brand@123'
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

def test_1_empty_values():
    """测试1：空值和None处理"""
    print('\n' + '='*80)
    print('测试1：空值和None处理')
    print('='*80)

    workspace = Path('/Users/a123/.openclaw/workspace')
    brand_name = '空值测试品牌'

    # 创建品牌档案（部分字段为空）
    project_dir = create_agency_project(
        workspace_root=workspace,
        brand_name=brand_name,
        campaign_name='测试项目',
        brand_info={
            'industry': '',  # 空字符串
            'target_audience': '',
            'core_values': [],  # 空列表
        }
    )

    profile_path = find_brand_profile(workspace, brand_name)
    assert profile_path is not None, '档案应该存在'

    # 测试：检测空值冲突
    result = detect_conflicts(workspace, brand_name, {
        'industry': '',  # 空对空
        'target_audience': '25-35岁女性',  # 空对有值
        'core_values': ['新价值'],  # 空对有值
    })

    print(f'空值冲突检测结果: has_conflict={result["has_conflict"]}')
    print(f'补充信息数: {len(result["supplements"])}')

    # 验证：空对有值应该是补充信息，不是冲突
    assert result['has_conflict'] == False, '空对有值不应该是冲突'
    assert len(result['supplements']) >= 2, '应该有补充信息'

    print('✅ 测试1通过：空值处理正确')

def test_2_unicode_and_special_chars():
    """测试2：Unicode和特殊字符处理"""
    print('\n' + '='*80)
    print('测试2：Unicode和特殊字符处理')
    print('='*80)

    workspace = Path('/Users/a123/.openclaw/workspace')
    brand_name = '中文测试品牌'

    # 创建包含特殊字符的档案
    project_dir = create_agency_project(
        workspace_root=workspace,
        brand_name=brand_name,
        campaign_name='测试项目',
        brand_info={
            'industry': '烘焙 & 餐饮',
            'target_audience': '25-35岁女性（一线城市）',
            'core_values': ['新鲜、手作', '用心❤️'],
        }
    )

    profile_path = find_brand_profile(workspace, brand_name)
    profile = json.loads(profile_path.read_text(encoding='utf-8'))

    # 验证Unicode字符正确保存
    assert '❤️' in profile['core_values'][1], 'Emoji应该正确保存'
    assert '（' in profile['target_audience'], '中文括号应该正确保存'

    # 测试冲突检测
    result = detect_conflicts(workspace, brand_name, {
        'industry': '烘焙 & 餐饮',  # 完全一致
        'core_values': ['新鲜、手作', '用心❤️', '品质✨'],  # 扩展
    })

    print(f'Unicode冲突检测结果: has_conflict={result["has_conflict"]}')
    assert result['has_conflict'] == False, '扩展不应该是冲突'

    print('✅ 测试2通过：Unicode和特殊字符处理正确')

def test_3_concurrent_updates():
    """测试3：并发更新（模拟）"""
    print('\n' + '='*80)
    print('测试3：连续快速更新')
    print('='*80)

    workspace = Path('/Users/a123/.openclaw/workspace')
    brand_name = '压力测试品牌A'

    project_dir = create_agency_project(
        workspace_root=workspace,
        brand_name=brand_name,
        campaign_name='测试项目',
        brand_info={'industry': '初始行业'}
    )

    # 连续快速更新10次
    for i in range(10):
        result = update_brand_profile_field(
            workspace_root=workspace,
            brand_name=brand_name,
            field='core_values',
            value=[f'价值观{i}'],
            operation='append'
        )
        assert result['success'] == True, f'第{i+1}次更新失败'

    # 验证所有更新都成功
    profile_path = find_brand_profile(workspace, brand_name)
    profile = json.loads(profile_path.read_text(encoding='utf-8'))

    assert len(profile['core_values']) == 10, f'应该有10个价值观，实际有{len(profile["core_values"])}个'

    print('✅ 测试3通过：连续快速更新正确')

def test_4_nested_field_edge_cases():
    """测试4：嵌套字段边界情况"""
    print('\n' + '='*80)
    print('测试4：嵌套字段边界情况')
    print('='*80)

    workspace = Path('/Users/a123/.openclaw/workspace')
    brand_name = '边界测试品牌'

    project_dir = create_agency_project(
        workspace_root=workspace,
        brand_name=brand_name,
        campaign_name='测试项目',
        brand_info={}
    )

    # 测试：更新不存在的嵌套字段
    result = update_brand_profile_field(
        workspace_root=workspace,
        brand_name=brand_name,
        field='vi_guidelines.primary_colors',
        value=['#FF0000'],
        operation='replace'
    )
    assert result['success'] == True, '更新不存在的嵌套字段应该成功'

    # 验证嵌套字段已创建
    profile_path = find_brand_profile(workspace, brand_name)
    profile = json.loads(profile_path.read_text(encoding='utf-8'))
    assert profile['vi_guidelines']['primary_colors'] == ['#FF0000'], '嵌套字段应该正确创建'

    # 测试：append 到嵌套列表
    result = update_brand_profile_field(
        workspace_root=workspace,
        brand_name=brand_name,
        field='vi_guidelines.primary_colors',
        value=['#00FF00'],
        operation='append'
    )
    assert result['success'] == True, 'append到嵌套列表应该成功'

    profile = json.loads(find_brand_profile(workspace, brand_name).read_text(encoding='utf-8'))
    assert len(profile['vi_guidelines']['primary_colors']) == 2, '应该有2个颜色'

    print('✅ 测试4通过：嵌套字段边界情况处理正确')

def test_5_large_data():
    """测试5：大数据量处理"""
    print('\n' + '='*80)
    print('测试5：大数据量处理')
    print('='*80)

    workspace = Path('/Users/a123/.openclaw/workspace')
    brand_name = '压力测试品牌B'

    project_dir = create_agency_project(
        workspace_root=workspace,
        brand_name=brand_name,
        campaign_name='测试项目',
        brand_info={}
    )

    # 添加100个竞品
    large_list = [f'竞品{i}' for i in range(100)]
    result = update_brand_profile_field(
        workspace_root=workspace,
        brand_name=brand_name,
        field='competitors',
        value=large_list,
        operation='append'
    )
    assert result['success'] == True, '添加100个竞品应该成功'

    # 验证数据完整性
    profile_path = find_brand_profile(workspace, brand_name)
    profile = json.loads(profile_path.read_text(encoding='utf-8'))
    assert len(profile.get('competitors', [])) == 100, '应该有100个竞品'

    # 测试冲突检测性能
    result = detect_conflicts(workspace, brand_name, {
        'competitors': large_list + [f'新竞品{i}' for i in range(50)]
    })
    print(f'大数据冲突检测: 补充信息数={len(result["supplements"])}')

    print('✅ 测试5通过：大数据量处理正确')

def test_6_conflict_detection_accuracy():
    """测试6：冲突检测准确性"""
    print('\n' + '='*80)
    print('测试6：冲突检测准确性')
    print('='*80)

    workspace = Path('/Users/a123/.openclaw/workspace')
    brand_name = '压力测试品牌C'

    project_dir = create_agency_project(
        workspace_root=workspace,
        brand_name=brand_name,
        campaign_name='测试项目',
        brand_info={
            'industry': '烘焙',
            'positioning': '高端连锁',
            'brand_tone': '温暖亲切',
            'core_values': ['新鲜', '手作'],
            'target_audience': '25-35岁女性'
        }
    )

    # 添加视觉规范
    update_brand_profile_field(workspace, brand_name, 'vi_guidelines.primary_colors', ['#FF6B6B'], 'replace')

    test_cases = [
        {
            'name': '无冲突（完全一致）',
            'new_info': {'industry': '烘焙', 'brand_tone': '温暖亲切'},
            'expected_conflict': False,
        },
        {
            'name': '高严重性冲突（行业）',
            'new_info': {'industry': '餐饮'},
            'expected_conflict': True,
        },
        {
            'name': '高严重性冲突（定位）',
            'new_info': {'positioning': '社区亲民'},
            'expected_conflict': True,
        },
        {
            'name': '高严重性冲突（视觉规范）',
            'new_info': {'vi_guidelines': {'primary_colors': ['#0000FF']}},
            'expected_conflict': True,
        },
        {
            'name': '低严重性（扩展价值观）',
            'new_info': {'core_values': ['新鲜', '手作', '品质']},
            'expected_conflict': False,
        },
        {
            'name': '低严重性（目标受众扩展）',
            'new_info': {'target_audience': '25-45岁女性'},
            'expected_conflict': False,
        },
        {
            'name': '混合冲突（高+低）',
            'new_info': {
                'industry': '餐饮',  # 高
                'core_values': ['新鲜', '手作', '品质']  # 低
            },
            'expected_conflict': True,
        },
    ]

    for i, case in enumerate(test_cases, 1):
        result = detect_conflicts(workspace, brand_name, case['new_info'])
        actual_conflict = result['has_conflict']

        print(f'  测试用例{i}: {case["name"]}')
        print(f'    预期冲突: {case["expected_conflict"]}, 实际冲突: {actual_conflict}')

        assert actual_conflict == case['expected_conflict'], \
            f'用例"{case["name"]}"冲突检测错误: expected={case["expected_conflict"]}, actual={actual_conflict}'

    print('✅ 测试6通过：冲突检测准确性正确')

def test_7_error_handling():
    """测试7：错误处理"""
    print('\n' + '='*80)
    print('测试7：错误处理')
    print('='*80)

    workspace = Path('/Users/a123/.openclaw/workspace')

    # 测试：查询不存在的品牌
    profile_path = find_brand_profile(workspace, '不存在的品牌XYZ')
    assert profile_path is None, '不存在的品牌应该返回None'
    print('  ✓ 查询不存在的品牌：正确返回None')

    # 测试：更新不存在的品牌
    result = update_brand_profile_field(
        workspace_root=workspace,
        brand_name='不存在的品牌XYZ',
        field='industry',
        value='测试',
        operation='replace'
    )
    assert result['success'] == False, '更新不存在的品牌应该失败'
    print('  ✓ 更新不存在的品牌：正确返回失败')

    # 测试：检测不存在品牌的冲突
    result = detect_conflicts(workspace, '不存在的品牌XYZ', {'industry': '测试'})
    assert result['has_conflict'] == False, '不存在的品牌应该返回无冲突'
    assert len(result['conflicts']) == 0, '冲突列表应该为空'
    print('  ✓ 检测不存在品牌的冲突：正确返回无冲突')

    print('✅ 测试7通过：错误处理正确')

def run_all_tests():
    """运行所有测试"""
    print('\n')
    print('╔' + '═'*78 + '╗')
    print('║' + ' '*20 + 'Boss Skill 综合压力测试' + ' '*33 + '║')
    print('╚' + '═'*78 + '╝')

    try:
        # 清理测试数据
        cleanup_test_brands()

        # 运行测试
        test_1_empty_values()
        test_2_unicode_and_special_chars()
        test_3_concurrent_updates()
        test_4_nested_field_edge_cases()
        test_5_large_data()
        test_6_conflict_detection_accuracy()
        test_7_error_handling()

        # 清理测试数据
        cleanup_test_brands()

        print('\n' + '='*80)
        print('✅ 所有测试通过！无 bug 发现。')
        print('='*80)
        return True

    except AssertionError as e:
        print(f'\n❌ 测试失败: {e}')
        return False
    except Exception as e:
        print(f'\n❌ 测试异常: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = run_all_tests()
    exit(0 if success else 1)
