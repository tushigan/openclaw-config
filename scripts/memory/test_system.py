#!/usr/bin/env python3
"""
OpenClaw 顶层记忆系统 - 综合测试
验证所有核心功能正常工作
"""

import os
import sys
import json
import subprocess

def run_command(cmd, description):
    """运行命令并返回结果"""
    print(f"\n{'='*70}")
    print(f"测试: {description}")
    print(f"命令: {cmd}")
    print('-'*70)

    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    if result.returncode == 0:
        print("✅ 成功")
        if result.stdout:
            print(result.stdout)
        return True, result.stdout
    else:
        print("❌ 失败")
        if result.stderr:
            print(result.stderr)
        return False, result.stderr


def test_memory_system():
    """测试记忆系统核心功能"""

    print("="*70)
    print("OpenClaw 顶层记忆系统 - 综合测试")
    print("="*70)

    results = []

    # 测试 1: 客户管理
    success, output = run_command(
        'python3 scripts/memory/client.py list',
        "客户列表查询"
    )
    results.append(("客户管理", success))

    # 测试 2: 品牌查询
    success, output = run_command(
        'python3 scripts/memory/query.py list-brands',
        "品牌列表查询"
    )
    results.append(("品牌查询", success))

    # 测试 3: 查询特定品牌（测试品牌X）
    success, output = run_command(
        'python3 scripts/memory/query.py brand --name "测试品牌X" --json',
        "单个品牌查询"
    )
    results.append(("品牌详情查询", success))

    if success:
        try:
            data = json.loads(output)
            print(f"   品牌调性: {data.get('brand_tone')}")
            print(f"   定位: {data.get('positioning')}")
            print(f"   目标受众: {data.get('target_audience')}")
        except:
            pass

    # 测试 4: 品牌资产查询
    success, output = run_command(
        'python3 scripts/memory/query.py assets --brand "测试品牌X" --json',
        "品牌资产查询"
    )
    results.append(("品牌资产", success))

    # 测试 5: 活跃项目查询
    success, output = run_command(
        'python3 scripts/memory/query.py list-projects',
        "活跃项目列表"
    )
    results.append(("项目查询", success))

    # 测试 6: 冲突检测（不带确认）
    print(f"\n{'='*70}")
    print("测试: 冲突检测机制")
    print(f"命令: 尝试更新品牌调性（不带确认）")
    print('-'*70)

    result = subprocess.run(
        'python3 scripts/memory/brand.py update --client "测试客户A" --name "测试品牌X" --field "brand_tone" --value "科技、创新" --agent "test-system"',
        shell=True,
        capture_output=True,
        text=True
    )

    if "conflict" in result.stdout or "冲突" in result.stdout:
        print("✅ 冲突检测正常工作")
        results.append(("冲突检测", True))
    else:
        print("❌ 冲突检测未触发")
        results.append(("冲突检测", False))

    # 测试 7: 验证迁移数据
    print(f"\n{'='*70}")
    print("测试: 验证数据迁移完整性")
    print('-'*70)

    migrated_clients = ["泓一", "丹夫", "知是", "傅小姐", "麦初心语"]
    migration_ok = True

    for client in migrated_clients:
        client_dir = f"/Users/a123/.openclaw/projects/{client}"
        if os.path.exists(client_dir):
            print(f"   ✅ {client} - 已迁移")
        else:
            print(f"   ❌ {client} - 未找到")
            migration_ok = False

    results.append(("数据迁移", migration_ok))

    # 测试 8: 检查记忆系统脚本权限
    print(f"\n{'='*70}")
    print("测试: 记忆系统脚本权限")
    print('-'*70)

    scripts = [
        "scripts/memory/client.py",
        "scripts/memory/brand.py",
        "scripts/memory/query.py",
    ]

    scripts_ok = True
    for script in scripts:
        if os.path.exists(script) and os.access(script, os.X_OK):
            print(f"   ✅ {script} - 可执行")
        else:
            print(f"   ❌ {script} - 不可执行或不存在")
            scripts_ok = False

    results.append(("脚本权限", scripts_ok))

    # 汇总结果
    print("\n" + "="*70)
    print("📊 测试结果汇总")
    print("="*70)

    total = len(results)
    passed = sum(1 for _, success in results if success)

    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"   {status} - {test_name}")

    print("\n" + "="*70)
    print(f"总计: {passed}/{total} 通过")

    if passed == total:
        print("✅ 所有测试通过！记忆系统运行正常。")
    else:
        print(f"⚠️ {total - passed} 个测试失败，请检查。")

    print("="*70)

    return passed == total


if __name__ == '__main__':
    success = test_memory_system()
    sys.exit(0 if success else 1)
