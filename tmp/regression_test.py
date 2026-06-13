#!/usr/bin/env python3
"""回归测试：确保新功能不破坏现有功能"""

from pathlib import Path
from agency_project import (
    create_agency_project,
    find_brand_profile,
    find_active_project,
    archive_material,
    update_stage_checkpoint,
    create_or_get_brand
)
import json
import shutil
import tempfile

def test_existing_function_create_agency_project():
    """回归测试1：create_agency_project 不受影响"""
    print('\n' + '='*80)
    print('回归测试1：create_agency_project 原有功能')
    print('='*80)

    workspace = Path('/Users/a123/.openclaw/workspace')
    brand_name = '回归测试品牌A'

    # 测试：不传 brand_info（原有用法）
    project_dir = create_agency_project(
        workspace_root=workspace,
        brand_name=brand_name,
        campaign_name='项目1',
    )

    assert project_dir.exists(), '项目目录应该存在'
    assert (project_dir / 'project.json').exists(), 'project.json应该存在'
    assert (project_dir / 'brief.json').exists(), 'brief.json应该存在'

    print('✓ 不传brand_info的用法正常')

    # 测试：传空 brand_info
    project_dir2 = create_agency_project(
        workspace_root=workspace,
        brand_name=brand_name,
        campaign_name='项目2',
        brand_info={}
    )

    assert project_dir2.exists(), '项目目录2应该存在'

    print('✓ 传空brand_info的用法正常')

    # 清理
    brand_dir = workspace / 'projects' / brand_name
    if brand_dir.exists():
        shutil.rmtree(brand_dir)

    print('✅ 回归测试1通过：create_agency_project 不受影响')

def test_existing_function_find_brand_profile():
    """回归测试2：find_brand_profile 不受影响"""
    print('\n' + '='*80)
    print('回归测试2：find_brand_profile 原有功能')
    print('='*80)

    workspace = Path('/Users/a123/.openclaw/workspace')
    brand_name = '回归测试品牌B'

    # 创建品牌
    project_dir = create_agency_project(
        workspace_root=workspace,
        brand_name=brand_name,
        campaign_name='项目1',
    )

    # 测试：查询存在的品牌
    profile_path = find_brand_profile(workspace, brand_name)
    assert profile_path is not None, '应该找到品牌档案'
    assert profile_path.exists(), '品牌档案文件应该存在'

    print('✓ 查询存在的品牌：正常')

    # 测试：查询不存在的品牌
    profile_path = find_brand_profile(workspace, '不存在的品牌XYZ')
    assert profile_path is None, '不应该找到品牌档案'

    print('✓ 查询不存在的品牌：正常')

    # 清理
    brand_dir = workspace / 'projects' / brand_name
    if brand_dir.exists():
        shutil.rmtree(brand_dir)

    print('✅ 回归测试2通过：find_brand_profile 不受影响')

def test_existing_function_find_active_project():
    """回归测试3：find_active_project 不受影响"""
    print('\n' + '='*80)
    print('回归测试3：find_active_project 原有功能')
    print('='*80)

    workspace = Path('/Users/a123/.openclaw/workspace')
    brand_name = '回归测试品牌C'

    # 创建项目
    project_dir = create_agency_project(
        workspace_root=workspace,
        brand_name=brand_name,
        campaign_name='活跃项目',
    )

    # 测试：查询活跃项目
    active_project = find_active_project(workspace, brand_name)
    assert active_project is not None, '应该找到活跃项目'
    assert active_project.name == '活跃项目', '项目名称应该匹配'

    print('✓ 查询活跃项目：正常')

    # 清理
    brand_dir = workspace / 'projects' / brand_name
    if brand_dir.exists():
        shutil.rmtree(brand_dir)

    print('✅ 回归测试3通过：find_active_project 不受影响')

def test_existing_function_archive_material():
    """回归测试4：archive_material 不受影响"""
    print('\n' + '='*80)
    print('回归测试4：archive_material 原有功能')
    print('='*80)

    workspace = Path('/Users/a123/.openclaw/workspace')
    brand_name = '回归测试品牌D'

    # 创建项目
    project_dir = create_agency_project(
        workspace_root=workspace,
        brand_name=brand_name,
        campaign_name='归档测试',
    )

    # 创建测试文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write('测试材料内容')
        temp_file = Path(f.name)

    try:
        # 测试：归档材料
        archived_path = archive_material(
            project_dir=project_dir,
            source_path=temp_file,
            material_type='research'
        )

        assert archived_path.exists(), '归档文件应该存在'
        assert archived_path.parent.name == 'research', '应该归档到research目录'

        print('✓ 归档材料：正常')

    finally:
        temp_file.unlink(missing_ok=True)

    # 清理
    brand_dir = workspace / 'projects' / brand_name
    if brand_dir.exists():
        shutil.rmtree(brand_dir)

    print('✅ 回归测试4通过：archive_material 不受影响')

def test_existing_function_update_stage_checkpoint():
    """回归测试5：update_stage_checkpoint 不受影响"""
    print('\n' + '='*80)
    print('回归测试5：update_stage_checkpoint 原有功能')
    print('='*80)

    workspace = Path('/Users/a123/.openclaw/workspace')
    brand_name = '回归测试品牌E'

    # 创建项目
    project_dir = create_agency_project(
        workspace_root=workspace,
        brand_name=brand_name,
        campaign_name='阶段测试',
    )

    # 测试：更新阶段
    update_stage_checkpoint(
        project_dir=project_dir,
        stage='brief_intake',
        status='completed',
        user_confirmed=True
    )

    # 验证
    project_json = project_dir / 'project.json'
    project_data = json.loads(project_json.read_text(encoding='utf-8'))

    assert project_data['stage_checkpoints']['brief_intake']['status'] == 'completed', '阶段状态应该更新'
    assert project_data['stage_checkpoints']['brief_intake']['user_confirmed'] == True, '用户确认状态应该更新'

    print('✓ 更新阶段检查点：正常')

    # 清理
    brand_dir = workspace / 'projects' / brand_name
    if brand_dir.exists():
        shutil.rmtree(brand_dir)

    print('✅ 回归测试5通过：update_stage_checkpoint 不受影响')

def test_existing_function_create_or_get_brand():
    """回归测试6：create_or_get_brand 不受影响"""
    print('\n' + '='*80)
    print('回归测试6：create_or_get_brand 原有功能')
    print('='*80)

    workspace = Path('/Users/a123/.openclaw/workspace')
    brand_name = '回归测试品牌F'

    # 测试：创建新品牌
    brand_dir1 = create_or_get_brand(
        workspace_root=workspace,
        brand_name=brand_name,
        industry='测试行业'
    )

    assert brand_dir1.exists(), '品牌目录应该存在'
    assert (brand_dir1 / '_brand-profile.json').exists(), '品牌档案应该存在'

    print('✓ 创建新品牌：正常')

    # 测试：获取已存在的品牌（应该返回相同目录）
    brand_dir2 = create_or_get_brand(
        workspace_root=workspace,
        brand_name=brand_name,
    )

    assert brand_dir1 == brand_dir2, '应该返回相同的品牌目录'

    print('✓ 获取已存在品牌：正常')

    # 清理
    if brand_dir1.exists():
        shutil.rmtree(brand_dir1)

    print('✅ 回归测试6通过：create_or_get_brand 不受影响')

def test_brand_profile_schema_unchanged():
    """回归测试7：品牌档案 schema 不变"""
    print('\n' + '='*80)
    print('回归测试7：品牌档案 schema 不变')
    print('='*80)

    workspace = Path('/Users/a123/.openclaw/workspace')
    brand_name = '回归测试品牌G'

    # 创建品牌
    project_dir = create_agency_project(
        workspace_root=workspace,
        brand_name=brand_name,
        campaign_name='schema测试',
    )

    # 读取品牌档案
    profile_path = find_brand_profile(workspace, brand_name)
    profile = json.loads(profile_path.read_text(encoding='utf-8'))

    # 验证必需字段存在
    required_fields = [
        'schema_version', 'brand_id', 'brand_name', 'industry',
        'category', 'positioning', 'core_values', 'brand_tone',
        'target_audience', 'vi_guidelines', 'brand_assets_dir',
        'historical_campaigns', 'key_contacts', 'notes',
        'created_at', 'updated_at'
    ]

    for field in required_fields:
        assert field in profile, f'必需字段 {field} 缺失'

    print(f'✓ 所有必需字段存在（共{len(required_fields)}个）')

    # 验证 vi_guidelines 子结构
    vi_fields = ['primary_colors', 'secondary_colors', 'fonts', 'logo_usage_notes']
    for field in vi_fields:
        assert field in profile['vi_guidelines'], f'vi_guidelines.{field} 缺失'

    print(f'✓ vi_guidelines 子结构完整')

    # 清理
    brand_dir = workspace / 'projects' / brand_name
    if brand_dir.exists():
        shutil.rmtree(brand_dir)

    print('✅ 回归测试7通过：品牌档案 schema 不变')

def cleanup_all_regression_test_brands():
    """清理所有回归测试品牌"""
    workspace = Path('/Users/a123/.openclaw/workspace')
    registry_path = workspace / 'projects' / '_registry.json'

    test_brands = [
        '回归测试品牌A', '回归测试品牌B', '回归测试品牌C',
        '回归测试品牌D', '回归测试品牌E', '回归测试品牌F', '回归测试品牌G'
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

def run_all_regression_tests():
    """运行所有回归测试"""
    print('\n')
    print('╔' + '═'*78 + '╗')
    print('║' + ' '*22 + '回归测试 - 现有功能验证' + ' '*29 + '║')
    print('╚' + '═'*78 + '╝')

    try:
        cleanup_all_regression_test_brands()

        test_existing_function_create_agency_project()
        test_existing_function_find_brand_profile()
        test_existing_function_find_active_project()
        test_existing_function_archive_material()
        test_existing_function_update_stage_checkpoint()
        test_existing_function_create_or_get_brand()
        test_brand_profile_schema_unchanged()

        cleanup_all_regression_test_brands()

        print('\n' + '='*80)
        print('✅ 所有回归测试通过！新功能不破坏现有功能。')
        print('='*80)
        return True

    except AssertionError as e:
        print(f'\n❌ 回归测试失败: {e}')
        return False
    except Exception as e:
        print(f'\n❌ 回归测试异常: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = run_all_regression_tests()
    exit(0 if success else 1)
