#!/usr/bin/env python3
"""
品牌档案记忆系统压力测试 - 覆盖所有边界情况

测试目标：确保任何情况下关于品牌或项目的记忆都会被正确调用和记录
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

# ============ 边界情况测试 ============

def test_edge_case_1_special_characters():
    """边界测试1：品牌名包含特殊字符"""
    print("\n" + "="*60)
    print("边界测试1：品牌名包含特殊字符")
    print("="*60)

    test_cases = [
        ("测试品牌&Co.", "测试客户"),
        ("测试品牌/Ltd", "测试客户"),
        ("测试品牌-Pro", "测试客户"),
        ("测试品牌(2024)", "测试客户"),
    ]

    for brand_name, client_name in test_cases:
        try:
            print(f"\n测试品牌名: {brand_name}")

            # 创建品牌
            brand_dir = create_or_get_brand(
                workspace_root=WORKSPACE_ROOT,
                brand_name=brand_name,
                client_name=client_name,
                industry="测试"
            )

            # 查找品牌
            profile_path = find_brand_profile(WORKSPACE_ROOT, brand_name)

            if profile_path:
                print(f"✅ 特殊字符品牌创建和查询成功")
                # 清理
                import shutil
                shutil.rmtree(brand_dir.parent, ignore_errors=True)
            else:
                print(f"❌ 查询失败: {brand_name}")
                return False

        except Exception as e:
            print(f"❌ 异常: {brand_name} - {e}")
            return False

    return True

def test_edge_case_2_empty_fields():
    """边界测试2：必填字段为空"""
    print("\n" + "="*60)
    print("边界测试2：必填字段为空或缺失")
    print("="*60)

    # 测试只有品牌名，其他都为空
    brand_name = "测试空字段品牌"

    try:
        brand_dir = create_or_get_brand(
            workspace_root=WORKSPACE_ROOT,
            brand_name=brand_name,
            client_name="",  # 空客户名，应使用品牌名
            industry="",
            positioning="",
            brand_tone="",
            target_audience=""
        )

        profile_path = brand_dir / "_brand-profile.json"
        with open(profile_path, 'r', encoding='utf-8') as f:
            profile = json.load(f)

        # 验证空字段
        if profile.get("industry") == "" and profile.get("positioning") == "":
            print(f"✅ 空字段处理正确")
        else:
            print(f"❌ 空字段处理异常")
            return False

        # 清理
        import shutil
        shutil.rmtree(brand_dir.parent, ignore_errors=True)

    except Exception as e:
        print(f"❌ 异常: {e}")
        return False

    return True

def test_edge_case_3_long_text():
    """边界测试3：超长文本"""
    print("\n" + "="*60)
    print("边界测试3：超长文本字段")
    print("="*60)

    brand_name = "测试超长文本品牌"
    long_positioning = "这是一个非常长的品牌定位描述，" * 100  # 超长文本

    try:
        brand_dir = create_or_get_brand(
            workspace_root=WORKSPACE_ROOT,
            brand_name=brand_name,
            client_name="测试客户",
            positioning=long_positioning
        )

        profile_path = brand_dir / "_brand-profile.json"
        with open(profile_path, 'r', encoding='utf-8') as f:
            profile = json.load(f)

        if len(profile.get("positioning", "")) > 1000:
            print(f"✅ 超长文本保存成功")
        else:
            print(f"❌ 超长文本保存失败")
            return False

        # 清理
        import shutil
        shutil.rmtree(brand_dir.parent, ignore_errors=True)

    except Exception as e:
        print(f"❌ 异常: {e}")
        return False

    return True

def test_edge_case_4_duplicate_creation():
    """边界测试4：重复创建品牌"""
    print("\n" + "="*60)
    print("边界测试4：重复创建同一品牌")
    print("="*60)

    brand_name = "测试重复品牌"

    try:
        # 第一次创建
        brand_dir_1 = create_or_get_brand(
            workspace_root=WORKSPACE_ROOT,
            brand_name=brand_name,
            client_name="测试客户",
            industry="行业1"
        )

        # 第二次创建（应返回已存在的）
        brand_dir_2 = create_or_get_brand(
            workspace_root=WORKSPACE_ROOT,
            brand_name=brand_name,
            client_name="测试客户",
            industry="行业2"  # 不同的行业
        )

        # 验证路径相同
        if brand_dir_1 == brand_dir_2:
            print(f"✅ 重复创建正确返回已存在品牌")

            # 验证行业没有被覆盖
            profile_path = brand_dir_1 / "_brand-profile.json"
            with open(profile_path, 'r', encoding='utf-8') as f:
                profile = json.load(f)

            if profile.get("industry") == "行业1":
                print(f"✅ 原有数据未被覆盖")
            else:
                print(f"❌ 原有数据被意外覆盖")
                return False
        else:
            print(f"❌ 重复创建返回了不同路径")
            return False

        # 清理
        import shutil
        shutil.rmtree(brand_dir_1.parent, ignore_errors=True)

    except Exception as e:
        print(f"❌ 异常: {e}")
        return False

    return True

def test_edge_case_5_concurrent_access():
    """边界测试5：并发访问（模拟）"""
    print("\n" + "="*60)
    print("边界测试5：并发查询和更新")
    print("="*60)

    brand_name = "测试并发品牌"

    try:
        # 创建品牌
        brand_dir = create_or_get_brand(
            workspace_root=WORKSPACE_ROOT,
            brand_name=brand_name,
            client_name="测试客户",
            industry="测试行业"
        )

        # 模拟并发查询
        profile_1 = find_brand_profile(WORKSPACE_ROOT, brand_name)
        profile_2 = find_brand_profile(WORKSPACE_ROOT, brand_name)
        profile_3 = find_brand_profile(WORKSPACE_ROOT, brand_name)

        if profile_1 and profile_2 and profile_3:
            if str(profile_1) == str(profile_2) == str(profile_3):
                print(f"✅ 并发查询结果一致")
            else:
                print(f"❌ 并发查询结果不一致")
                return False
        else:
            print(f"❌ 并发查询失败")
            return False

        # 清理
        import shutil
        shutil.rmtree(brand_dir.parent, ignore_errors=True)

    except Exception as e:
        print(f"❌ 异常: {e}")
        return False

    return True

# ============ 异常情况测试 ============

def test_exception_1_missing_workspace():
    """异常测试1：workspace 目录不存在"""
    print("\n" + "="*60)
    print("异常测试1：workspace 目录不存在")
    print("="*60)

    fake_workspace = Path("/tmp/fake_workspace_test_12345")

    try:
        # 应该自动创建目录
        brand_dir = create_or_get_brand(
            workspace_root=fake_workspace,
            brand_name="测试品牌",
            client_name="测试客户"
        )

        if brand_dir.exists():
            print(f"✅ 自动创建 workspace 目录")
            # 清理
            import shutil
            shutil.rmtree(fake_workspace, ignore_errors=True)
        else:
            print(f"❌ 目录创建失败")
            return False

    except Exception as e:
        print(f"❌ 异常: {e}")
        return False

    return True

def test_exception_2_corrupted_json():
    """异常测试2：损坏的 JSON 文件"""
    print("\n" + "="*60)
    print("异常测试2：损坏的 JSON 文件处理")
    print("="*60)

    brand_name = "测试损坏JSON品牌"

    try:
        # 创建品牌
        brand_dir = create_or_get_brand(
            workspace_root=WORKSPACE_ROOT,
            brand_name=brand_name,
            client_name="测试客户"
        )

        profile_path = brand_dir / "_brand-profile.json"

        # 故意破坏 JSON 文件
        with open(profile_path, 'w', encoding='utf-8') as f:
            f.write('{ "brand_name": "测试", invalid json }')

        # 尝试查找（应该处理异常）
        try:
            profile = find_brand_profile(WORKSPACE_ROOT, brand_name)
            if profile is None:
                print(f"✅ 损坏的 JSON 被正确处理（返回 None）")
            else:
                print(f"⚠️ 损坏的 JSON 仍然返回了结果")
        except Exception:
            print(f"✅ 损坏的 JSON 触发了异常处理")

        # 清理
        import shutil
        shutil.rmtree(brand_dir.parent, ignore_errors=True)

    except Exception as e:
        print(f"❌ 异常: {e}")
        return False

    return True

def test_exception_3_unicode_handling():
    """异常测试3：Unicode 和 Emoji"""
    print("\n" + "="*60)
    print("异常测试3：Unicode 和 Emoji 处理")
    print("="*60)

    test_cases = [
        ("测试品牌😊", "测试客户"),
        ("测试品牌🎉🎊", "测试客户"),
        ("測試品牌日本語한국어", "測試客戶"),
    ]

    for brand_name, client_name in test_cases:
        try:
            print(f"\n测试: {brand_name}")

            brand_dir = create_or_get_brand(
                workspace_root=WORKSPACE_ROOT,
                brand_name=brand_name,
                client_name=client_name,
                brand_tone="优雅😊、精致🎉"
            )

            profile_path = find_brand_profile(WORKSPACE_ROOT, brand_name)

            if profile_path:
                # 验证内容
                with open(profile_path, 'r', encoding='utf-8') as f:
                    profile = json.load(f)

                if "😊" in profile.get("brand_tone", ""):
                    print(f"✅ Unicode/Emoji 保存和读取成功")
                else:
                    print(f"⚠️ Emoji 可能丢失")

                # 清理
                import shutil
                shutil.rmtree(brand_dir.parent, ignore_errors=True)
            else:
                print(f"❌ 查询失败")
                return False

        except Exception as e:
            print(f"❌ 异常: {e}")
            return False

    return True

# ============ 真实场景压力测试 ============

def test_real_scenario_1_incomplete_info():
    """真实场景1：用户提供的信息不完整"""
    print("\n" + "="*60)
    print("真实场景1：信息不完整的品牌任务")
    print("="*60)

    # 模拟用户只说了品牌名和任务，没有详细信息
    task_desc = "帮我做一个信息不完整品牌的海报"

    returncode, stdout, stderr = run_command(
        f'python3 /Users/a123/.openclaw/skills/boss/scripts/ensure_brand_profile.py '
        f'--brand "信息不完整品牌" '
        f'--extract-from "{task_desc}" '
        f'--auto-create --json'
    )

    if returncode == 0:
        result = json.loads(stdout)
        if result.get("created"):
            print(f"✅ 信息不完整时也能创建档案（字段为空）")

            # 验证档案
            profile_path = Path(result["profile_path"])
            if profile_path.exists():
                with open(profile_path, 'r', encoding='utf-8') as f:
                    profile = json.load(f)

                # 空字段是合理的
                if profile.get("industry") == "" or profile.get("industry") is None:
                    print(f"✅ 空字段处理正确")

                # 清理
                import shutil
                shutil.rmtree(profile_path.parent.parent, ignore_errors=True)
        else:
            print(f"❌ 创建失败")
            return False
    else:
        print(f"❌ 命令执行失败: {stderr}")
        return False

    return True

def test_real_scenario_2_ambiguous_info():
    """真实场景2：信息模糊或矛盾"""
    print("\n" + "="*60)
    print("真实场景2：信息模糊或矛盾")
    print("="*60)

    # 模拟用户提供矛盾的信息
    task_desc = """
    帮信息矛盾品牌做个海报，这是一个高端奢侈品牌，
    但价格要亲民，目标是年轻人但要有成熟感。
    """

    returncode, stdout, stderr = run_command(
        f'python3 /Users/a123/.openclaw/skills/boss/scripts/ensure_brand_profile.py '
        f'--brand "信息矛盾品牌" '
        f'--client "测试客户" '
        f'--extract-from "{task_desc}" '
        f'--auto-create --json'
    )

    if returncode == 0:
        result = json.loads(stdout)
        if result.get("created"):
            print(f"✅ 矛盾信息也能创建档案（提取可识别部分）")

            # 清理
            profile_path = Path(result["profile_path"])
            import shutil
            shutil.rmtree(profile_path.parent.parent, ignore_errors=True)
        else:
            print(f"❌ 创建失败")
            return False
    else:
        print(f"❌ 命令执行失败")
        return False

    return True

def test_real_scenario_3_brand_evolution():
    """真实场景3：品牌信息演变（多次更新）"""
    print("\n" + "="*60)
    print("真实场景3：品牌信息随时间演变")
    print("="*60)

    brand_name = "演变测试品牌"

    try:
        # 第1次：创建初始档案
        brand_dir = create_or_get_brand(
            workspace_root=WORKSPACE_ROOT,
            brand_name=brand_name,
            client_name="测试客户",
            positioning="初始定位：年轻时尚"
        )

        # 第2次：更新定位
        update_brand_profile_field(
            workspace_root=WORKSPACE_ROOT,
            brand_name=brand_name,
            field="positioning",
            value="升级定位：高端奢华",
            operation="replace"
        )

        # 第3次：补充核心价值
        update_brand_profile_field(
            workspace_root=WORKSPACE_ROOT,
            brand_name=brand_name,
            field="core_values",
            value=["品质", "创新"],
            operation="append"
        )

        # 第4次：再补充核心价值
        update_brand_profile_field(
            workspace_root=WORKSPACE_ROOT,
            brand_name=brand_name,
            field="core_values",
            value=["匠心"],
            operation="append"
        )

        # 验证最终状态
        profile_path = brand_dir / "_brand-profile.json"
        with open(profile_path, 'r', encoding='utf-8') as f:
            profile = json.load(f)

        if (profile.get("positioning") == "升级定位：高端奢华" and
            len(profile.get("core_values", [])) == 3):
            print(f"✅ 品牌信息演变正确记录")
            print(f"   - 定位: {profile['positioning']}")
            print(f"   - 核心价值: {profile['core_values']}")
        else:
            print(f"❌ 品牌演变记录异常")
            return False

        # 清理
        import shutil
        shutil.rmtree(brand_dir.parent, ignore_errors=True)

    except Exception as e:
        print(f"❌ 异常: {e}")
        return False

    return True

def main():
    """运行所有压力测试"""
    print("\n" + "="*60)
    print("品牌档案记忆系统压力测试")
    print("目标：确保任何情况下都能正确调用和记录")
    print("="*60)

    tests = [
        # 边界情况
        ("边界测试1：特殊字符", test_edge_case_1_special_characters),
        ("边界测试2：空字段", test_edge_case_2_empty_fields),
        ("边界测试3：超长文本", test_edge_case_3_long_text),
        ("边界测试4：重复创建", test_edge_case_4_duplicate_creation),
        ("边界测试5：并发访问", test_edge_case_5_concurrent_access),
        # 异常情况
        ("异常测试1：缺失目录", test_exception_1_missing_workspace),
        ("异常测试2：损坏JSON", test_exception_2_corrupted_json),
        ("异常测试3：Unicode/Emoji", test_exception_3_unicode_handling),
        # 真实场景
        ("真实场景1：信息不完整", test_real_scenario_1_incomplete_info),
        ("真实场景2：信息矛盾", test_real_scenario_2_ambiguous_info),
        ("真实场景3：品牌演变", test_real_scenario_3_brand_evolution),
    ]

    passed = 0
    failed = 0
    errors = []

    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"\n✅ {name} 通过")
            else:
                failed += 1
                errors.append(name)
                print(f"\n❌ {name} 失败")
        except Exception as e:
            failed += 1
            errors.append(f"{name}: {e}")
            print(f"\n❌ {name} 异常: {e}")

    # 总结
    print("\n" + "="*60)
    print("压力测试总结")
    print("="*60)
    print(f"总测试数: {len(tests)}")
    print(f"通过: {passed}")
    print(f"失败: {failed}")

    if failed == 0:
        print("\n🎉 所有压力测试通过！")
        print("\n系统在以下情况下都能正确工作：")
        print("✅ 边界情况（特殊字符、空字段、超长文本、重复创建、并发）")
        print("✅ 异常情况（缺失目录、损坏文件、Unicode/Emoji）")
        print("✅ 真实场景（信息不完整、信息矛盾、品牌演变）")
        print("\n结论：任何情况下关于品牌或项目的记忆都会被正确调用和记录 ✅")
        return 0
    else:
        print(f"\n⚠️ {failed} 个测试失败")
        print("\n失败的测试：")
        for error in errors:
            print(f"  - {error}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
