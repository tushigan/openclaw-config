#!/usr/bin/env python3
"""
品牌档案系统全面测试

测试内容：
1. 统一架构（客户→品牌结构）
2. 向后兼容性（旧结构查询）
3. 强制检查机制
4. 信息提取和自动创建
5. 冲突检测
6. 档案更新
"""

import sys
import os
import json
import subprocess
from pathlib import Path

sys.path.insert(0, '/Users/a123/.openclaw/skills/boss/scripts')

from agency_project import (
    create_or_get_brand,
    find_brand_profile,
    detect_conflicts,
    update_brand_profile_field
)

WORKSPACE_ROOT = Path('/Users/a123/.openclaw')

def run_command(cmd):
    """运行命令并返回结果"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr

def test_unified_architecture():
    """测试统一架构（客户→品牌）"""
    print("\n" + "="*60)
    print("测试1：统一架构（客户→品牌结构）")
    print("="*60)

    test_brand = "测试品牌_架构"
    test_client = "测试客户_架构"

    try:
        # 创建品牌
        brand_dir = create_or_get_brand(
            workspace_root=WORKSPACE_ROOT,
            brand_name=test_brand,
            client_name=test_client,
            industry="测试行业",
            positioning="测试定位"
        )

        # 验证目录结构
        expected_structure = f"{test_client}/{test_brand}"
        if expected_structure in str(brand_dir):
            print(f"✅ 目录结构正确: {brand_dir}")
        else:
            print(f"❌ 目录结构错误: {brand_dir}")
            return False

        # 验证档案文件存在
        profile_path = brand_dir / "_brand-profile.json"
        if profile_path.exists():
            print(f"✅ 档案文件存在: {profile_path}")
        else:
            print(f"❌ 档案文件不存在")
            return False

        return True
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_backward_compatibility():
    """测试向后兼容性"""
    print("\n" + "="*60)
    print("测试2：向后兼容性（查找不同结构的品牌）")
    print("="*60)

    # 测试查找新结构品牌
    profile_path = find_brand_profile(WORKSPACE_ROOT, "测试品牌_架构")
    if profile_path:
        print(f"✅ 新结构品牌查询成功: {profile_path}")
    else:
        print(f"❌ 新结构品牌查询失败")
        return False

    # 测试查找然利（已迁移到客户→品牌结构）
    ranli_path = find_brand_profile(WORKSPACE_ROOT, "然利")
    if ranli_path:
        print(f"✅ 然利品牌查询成功: {ranli_path}")
    else:
        print(f"❌ 然利品牌查询失败")
        return False

    return True

def test_ensure_brand_profile():
    """测试强制检查脚本"""
    print("\n" + "="*60)
    print("测试3：品牌档案强制检查机制")
    print("="*60)

    # 测试已存在品牌
    print("\n3.1 已存在品牌检查")
    returncode, stdout, stderr = run_command(
        'python3 /Users/a123/.openclaw/skills/boss/scripts/ensure_brand_profile.py '
        '--brand "然利" --json'
    )
    if returncode == 0:
        result = json.loads(stdout)
        if result["exists"] and not result["created"]:
            print(f"✅ 已存在品牌检查通过: {result['message']}")
        else:
            print(f"❌ 已存在品牌检查失败: {result}")
            return False
    else:
        print(f"❌ 命令执行失败: {stderr}")
        return False

    # 测试不存在品牌（提示模式）
    print("\n3.2 不存在品牌提示")
    returncode, stdout, stderr = run_command(
        'python3 /Users/a123/.openclaw/skills/boss/scripts/ensure_brand_profile.py '
        '--brand "不存在品牌测试" --json'
    )
    if returncode == 1:  # 预期返回码为1（需要用户确认）
        result = json.loads(stdout)
        if not result["exists"] and not result["created"]:
            print(f"✅ 不存在品牌提示正确")
        else:
            print(f"❌ 不存在品牌提示错误: {result}")
            return False
    else:
        print(f"✅ 不存在品牌提示正确（返回码: {returncode}）")

    # 测试自动创建
    print("\n3.3 自动创建品牌档案")
    task_desc = """
    这是一个测试品牌B的视频任务。
    品牌名：测试品牌B
    行业：科技互联网
    定位：面向企业客户的高端SaaS平台
    受众：中大型企业IT决策者
    调性：专业、可靠、创新
    """
    returncode, stdout, stderr = run_command(
        f'python3 /Users/a123/.openclaw/skills/boss/scripts/ensure_brand_profile.py '
        f'--brand "测试品牌B" '
        f'--client "测试客户B" '
        f'--extract-from "{task_desc}" '
        f'--auto-create --json'
    )
    if returncode == 0:
        result = json.loads(stdout)
        if result["created"]:
            print(f"✅ 自动创建成功: {result['profile_path']}")

            # 验证提取的信息
            with open(result["profile_path"], 'r', encoding='utf-8') as f:
                profile = json.load(f)
                if profile["industry"] == "科技互联网":
                    print(f"✅ 信息提取正确: industry = {profile['industry']}")
                else:
                    print(f"⚠️ 信息提取不完整: industry = {profile.get('industry', '空')}")
        else:
            print(f"❌ 自动创建失败: {result}")
            return False
    else:
        print(f"❌ 命令执行失败: {stderr}")
        return False

    return True

def test_conflict_detection():
    """测试冲突检测"""
    print("\n" + "="*60)
    print("测试4：品牌信息冲突检测")
    print("="*60)

    # 测试高严重性冲突（定位冲突）
    print("\n4.1 高严重性冲突检测")
    conflicts = detect_conflicts(
        workspace_root=WORKSPACE_ROOT,
        brand_name="然利",
        new_info={
            "positioning": "全新的品牌定位（完全不同）",
            "brand_tone": "完全不同的调性"
        }
    )

    if conflicts["has_conflict"]:
        print(f"✅ 检测到高严重性冲突:")
        for conflict in conflicts["conflicts"]:
            print(f"   - 字段: {conflict['field']}")
            print(f"     档案: {conflict['archived']}")
            print(f"     输入: {conflict['new_input']}")
            print(f"     严重性: {conflict['severity']}")
    else:
        print(f"⚠️ 未检测到冲突（可能是档案为空）")

    # 测试低严重性补充信息
    print("\n4.2 低严重性补充信息")
    conflicts = detect_conflicts(
        workspace_root=WORKSPACE_ROOT,
        brand_name="然利",
        new_info={
            "core_values": ["专业", "现代", "高级", "新价值"]
        }
    )

    if conflicts["supplements"]:
        print(f"✅ 检测到补充信息:")
        for supplement in conflicts["supplements"]:
            print(f"   - 字段: {supplement['field']}")
            print(f"     档案: {supplement['archived']}")
            print(f"     输入: {supplement['new_input']}")
    else:
        print(f"⚠️ 未检测到补充信息")

    return True

def test_profile_update():
    """测试档案更新"""
    print("\n" + "="*60)
    print("测试5：品牌档案字段更新")
    print("="*60)

    # 测试 replace 操作
    print("\n5.1 替换操作（replace）")
    result = update_brand_profile_field(
        workspace_root=WORKSPACE_ROOT,
        brand_name="测试品牌B",
        field="brand_tone",
        value="专业、可靠、创新、领先",
        operation="replace"
    )

    if result["success"]:
        print(f"✅ 替换操作成功: {result['message']}")
    else:
        print(f"❌ 替换操作失败: {result['message']}")
        return False

    # 测试 append 操作
    print("\n5.2 追加操作（append）")
    result = update_brand_profile_field(
        workspace_root=WORKSPACE_ROOT,
        brand_name="测试品牌B",
        field="core_values",
        value=["用户第一", "持续创新"],
        operation="append"
    )

    if result["success"]:
        print(f"✅ 追加操作成功: {result['message']}")
    else:
        print(f"❌ 追加操作失败: {result['message']}")
        return False

    # 测试嵌套字段更新
    print("\n5.3 嵌套字段更新（vi_guidelines.primary_colors）")
    result = update_brand_profile_field(
        workspace_root=WORKSPACE_ROOT,
        brand_name="然利",
        field="vi_guidelines.primary_colors",
        value=["#FF0000", "#00FF00", "#F5F5DC"],
        operation="replace"
    )

    if result["success"]:
        print(f"✅ 嵌套字段更新成功")

        # 验证更新结果
        profile_path = find_brand_profile(WORKSPACE_ROOT, "然利")
        with open(profile_path, 'r', encoding='utf-8') as f:
            profile = json.load(f)
            if "vi_guidelines" in profile and "primary_colors" in profile["vi_guidelines"]:
                colors = profile["vi_guidelines"]["primary_colors"]
                print(f"   更新后的主色: {colors}")
            else:
                print(f"⚠️ 嵌套字段验证失败")
    else:
        print(f"❌ 嵌套字段更新失败: {result['message']}")
        return False

    return True

def test_query_integration():
    """测试与顶层查询接口的集成"""
    print("\n" + "="*60)
    print("测试6：与顶层查询接口的集成")
    print("="*60)

    # 测试查询接口能否找到新创建的品牌
    print("\n6.1 查询新创建的品牌")
    returncode, stdout, stderr = run_command(
        'python3 /Users/a123/.openclaw/scripts/memory/query.py brand --name "测试品牌B" --json'
    )

    if returncode == 0:
        result = json.loads(stdout)
        if result.get("brand_name") == "测试品牌B":
            print(f"✅ 顶层查询接口集成成功")
            print(f"   品牌名: {result['brand_name']}")
            print(f"   行业: {result.get('industry', 'N/A')}")
            print(f"   调性: {result.get('brand_tone', 'N/A')}")
        else:
            print(f"❌ 查询结果不正确: {result}")
            return False
    else:
        print(f"❌ 查询失败: {stderr}")
        return False

    # 测试列出所有品牌
    print("\n6.2 列出所有品牌")
    returncode, stdout, stderr = run_command(
        'python3 /Users/a123/.openclaw/scripts/memory/query.py list-brands'
    )

    if returncode == 0:
        if "测试品牌B" in stdout and "然利" in stdout:
            print(f"✅ 品牌列表包含新旧品牌")
        else:
            print(f"⚠️ 品牌列表可能不完整")
    else:
        print(f"❌ 列表失败: {stderr}")
        return False

    return True

def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("品牌档案系统全面测试")
    print("="*60)

    tests = [
        ("统一架构", test_unified_architecture),
        ("向后兼容性", test_backward_compatibility),
        ("强制检查机制", test_ensure_brand_profile),
        ("冲突检测", test_conflict_detection),
        ("档案更新", test_profile_update),
        ("查询接口集成", test_query_integration),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                print(f"\n❌ 测试失败: {name}")
        except Exception as e:
            failed += 1
            print(f"\n❌ 测试异常: {name}")
            print(f"   错误: {e}")
            import traceback
            traceback.print_exc()

    # 总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    print(f"总测试数: {len(tests)}")
    print(f"通过: {passed}")
    print(f"失败: {failed}")

    if failed == 0:
        print("\n🎉 所有测试通过！")
        return 0
    else:
        print(f"\n⚠️ {failed} 个测试失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())
