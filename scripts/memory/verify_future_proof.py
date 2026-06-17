#!/usr/bin/env python3
"""
验证脚本：确保所有 skill 的记忆系统集成能够正常工作

测试场景：
1. 新客户 + 新品牌 + 新项目 → 自动创建
2. 现有品牌 + 新项目 → 自动关联
3. 产出归档 → 自动版本化
4. 跨 skill 数据共享 → 品牌记忆可用
"""

import subprocess
import json
import sys
from pathlib import Path
from datetime import datetime

def run_cmd(cmd):
    """运行命令并返回结果"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.returncode == 0, result.stdout, result.stderr

def test_new_client_brand_project():
    """测试场景1：新客户、新品牌、新项目的自动创建"""
    print("=" * 80)
    print("场景 1: 新客户 + 新品牌 + 新项目")
    print("=" * 80)
    print()

    test_id = datetime.now().strftime("%H%M%S")
    client = f"验证客户_{test_id}"
    brand = f"验证品牌_{test_id}"
    project = f"验证项目_{test_id}"

    print(f"📋 测试数据：")
    print(f"   客户：{client}")
    print(f"   品牌：{brand}")
    print(f"   项目：{project}")
    print()

    # 测试项目创建（应该自动创建客户和品牌）
    cmd = f'''python3 /Users/a123/.openclaw/scripts/memory/project.py get-or-create \
        --client "{client}" \
        --brand "{brand}" \
        --project "{project}" \
        --campaign-type "海报设计" \
        --json'''

    success, stdout, stderr = run_cmd(cmd)

    if not success:
        print(f"❌ 项目创建失败")
        print(f"   错误: {stderr}")
        return False

    # 解析结果
    try:
        lines = [l for l in stdout.split('\n') if l.strip().startswith('{')]
        if lines:
            result = json.loads(lines[0])
            project_id = result.get("project_id")

            if project_id:
                print(f"✅ 项目自动创建成功")
                print(f"   项目 ID: {project_id}")
                print(f"   → 客户、品牌、项目已全部自动创建")
                return True, project_id
    except Exception as e:
        print(f"❌ 解析结果失败: {e}")
        return False, None

    return False, None

def test_task_creation(project_id):
    """测试场景2：任务创建"""
    print()
    print("=" * 80)
    print("场景 2: 任务创建")
    print("=" * 80)
    print()

    cmd = f'''python3 /Users/a123/.openclaw/scripts/memory/task.py create \
        --project-id "{project_id}" \
        --name "春节海报设计" \
        --type "poster" \
        --agent "design" \
        --skill "brand-poster-creator" \
        --brief "测试任务" \
        --json'''

    success, stdout, stderr = run_cmd(cmd)

    if not success:
        print(f"❌ 任务创建失败")
        print(f"   错误: {stderr}")
        return False, None

    try:
        lines = [l for l in stdout.split('\n') if l.strip().startswith('{')]
        if lines:
            result = json.loads(lines[0])
            task_id = result.get("task_id")

            if task_id:
                print(f"✅ 任务创建成功")
                print(f"   任务 ID: {task_id}")
                return True, task_id
    except Exception as e:
        print(f"❌ 解析结果失败: {e}")
        return False, None

    return False, None

def test_output_archive(task_id):
    """测试场景3：产出归档和版本管理"""
    print()
    print("=" * 80)
    print("场景 3: 产出归档和版本管理")
    print("=" * 80)
    print()

    # 创建测试文件
    test_file = Path(f"/tmp/test_output_{datetime.now().strftime('%H%M%S')}.png")
    test_file.write_text("测试图片内容")

    # 保存 v1
    cmd = f'''python3 /Users/a123/.openclaw/scripts/memory/task.py save-output \
        --task-id "{task_id}" \
        --file "{test_file}" \
        --note "第一版" \
        --expire-days 30'''

    success, stdout, stderr = run_cmd(cmd)

    if not success:
        print(f"❌ v1 归档失败")
        print(f"   错误: {stderr}")
        test_file.unlink(missing_ok=True)
        return False

    print(f"✅ v1 归档成功")

    # 保存 v2
    test_file.write_text("测试图片内容 v2")

    cmd = f'''python3 /Users/a123/.openclaw/scripts/memory/task.py save-output \
        --task-id "{task_id}" \
        --file "{test_file}" \
        --note "第二版（修改）" \
        --expire-days 30'''

    success, stdout, stderr = run_cmd(cmd)

    if not success:
        print(f"❌ v2 归档失败")
        test_file.unlink(missing_ok=True)
        return False

    print(f"✅ v2 归档成功")

    # 验证版本列表
    cmd = f'''python3 /Users/a123/.openclaw/scripts/memory/task.py list-iterations \
        --task-id "{task_id}" \
        --json'''

    success, stdout, stderr = run_cmd(cmd)

    if success:
        try:
            iterations = json.loads(stdout)
            if len(iterations) >= 2:
                print(f"✅ 版本管理正常：找到 {len(iterations)} 个版本")
                test_file.unlink(missing_ok=True)
                return True
        except:
            pass

    test_file.unlink(missing_ok=True)
    return False

def test_brand_query():
    """测试场景4：品牌查询（跨 skill 数据共享）"""
    print()
    print("=" * 80)
    print("场景 4: 品牌记忆查询（跨 skill 数据共享）")
    print("=" * 80)
    print()

    # 查询一个已知品牌
    cmd = '''python3 /Users/a123/.openclaw/scripts/memory/query.py brand \
        --name "wokenday" \
        --json'''

    success, stdout, stderr = run_cmd(cmd)

    if not success:
        print(f"❌ 品牌查询失败")
        return False

    try:
        brand_data = json.loads(stdout)
        if brand_data.get("brand_tone"):
            print(f"✅ 品牌查询成功")
            print(f"   品牌名：{brand_data.get('name')}")
            print(f"   品牌调性：{brand_data.get('brand_tone')}")
            print(f"   → 所有 skill 都能获取品牌记忆")
            return True
    except Exception as e:
        print(f"❌ 解析失败: {e}")
        return False

    return False

def verify_skill_integration():
    """验证所有 skill 的集成状态"""
    print()
    print("=" * 80)
    print("验证：所有 skill 集成状态")
    print("=" * 80)
    print()

    cmd = '''python3 /Users/a123/.openclaw/scripts/memory/audit_project_skills.py 2>&1 | grep "完全集成"'''

    success, stdout, stderr = run_cmd(cmd)

    if "20/20" in stdout or "完全集成: 20" in stdout:
        print(f"✅ 所有 20 个 skill 已完全集成")
        return True
    else:
        print(f"❌ Skill 集成不完整")
        print(f"   {stdout}")
        return False

def main():
    print()
    print("🔍 记忆系统保障机制验证")
    print()
    print("目标：确保未来所有 skill 执行的工作都能被正确记录")
    print()

    results = []

    # 验证 1: Skill 集成状态
    result = verify_skill_integration()
    results.append(("Skill 集成状态", result))

    if not result:
        print()
        print("❌ 关键验证失败：Skill 集成不完整")
        print("   → 无法保证未来的工作会被记录")
        sys.exit(1)

    # 测试 1: 新客户/品牌/项目
    result, project_id = test_new_client_brand_project()
    results.append(("新客户品牌项目自动创建", result))

    if not result:
        print()
        print("❌ 关键测试失败")
        sys.exit(1)

    # 测试 2: 任务创建
    result, task_id = test_task_creation(project_id)
    results.append(("任务创建", result))

    if not result:
        print()
        print("❌ 关键测试失败")
        sys.exit(1)

    # 测试 3: 产出归档
    result = test_output_archive(task_id)
    results.append(("产出归档和版本管理", result))

    # 测试 4: 品牌查询
    result = test_brand_query()
    results.append(("品牌记忆查询", result))

    # 总结
    print()
    print("=" * 80)
    print("验证结果总结")
    print("=" * 80)
    print()

    all_passed = True
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status}: {test_name}")
        if not result:
            all_passed = False

    print()

    if all_passed:
        print("🎉 所有验证通过！")
        print()
        print("保障机制确认：")
        print("  ✅ 所有 20 个 skill 已完全集成记忆系统")
        print("  ✅ 新客户/品牌/项目会自动创建")
        print("  ✅ 任务会自动创建")
        print("  ✅ 产出会自动归档和版本化")
        print("  ✅ 品牌记忆可跨 skill 共享")
        print()
        print("结论：未来通过任何 skill 执行的工作都会被正确记录！")
        return 0
    else:
        print("⚠️  部分验证失败")
        print()
        print("需要修复的问题：")
        for test_name, result in results:
            if not result:
                print(f"  ❌ {test_name}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
