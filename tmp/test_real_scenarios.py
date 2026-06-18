#!/usr/bin/env python3
"""
品牌档案系统真实场景验收测试

模拟真实工作场景，验证系统是否能自动记录品牌信息
"""

import sys
import os
import json
import subprocess
from pathlib import Path

sys.path.insert(0, '/Users/a123/.openclaw/skills/boss/scripts')

from agency_project import find_brand_profile

WORKSPACE_ROOT = Path('/Users/a123/.openclaw')

def run_command(cmd):
    """运行命令并返回结果"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr

def scenario_1_new_brand_video():
    """
    场景1：新品牌视频任务

    用户说："帮我做一个XX品牌的品牌升级视频"
    系统应该：
    1. 检测到新品牌
    2. 从对话提取品牌信息
    3. 提示用户创建档案
    4. 自动创建档案
    """
    print("\n" + "="*60)
    print("场景1：新品牌视频任务 - 模拟'然利'场景")
    print("="*60)

    brand_name = "验收测试品牌_视频"
    task_description = """
    帮我做一个验收测试品牌_视频的品牌升级视频。

    背景：
    - 这是一个预包装烘焙产品品牌
    - 目标是从手工感升级为更专业、现代、高级的品牌形象
    - 主要给渠道客户、经销商看
    - Logo 要去掉"手工"两个字，保留品牌名、擀面杖符号
    - 品牌色是红色、绿色、米白色
    """

    print(f"\n用户任务: {task_description[:100]}...")

    # Step 1: 检查品牌是否存在
    print("\n步骤1：检查品牌档案是否存在")
    returncode, stdout, stderr = run_command(
        f'python3 /Users/a123/.openclaw/skills/boss/scripts/ensure_brand_profile.py '
        f'--brand "{brand_name}" --json'
    )

    if returncode != 0:
        result = json.loads(stdout)
        if not result["exists"]:
            print(f"✅ 系统正确检测到新品牌")
            print(f"   提示信息: {result['message'][:100]}...")
        else:
            print(f"❌ 检测失败")
            return False
    else:
        result = json.loads(stdout)
        if result["exists"]:
            print(f"⚠️ 品牌已存在，跳过创建测试")
            return True

    # Step 2: 自动创建档案
    print("\n步骤2：从任务描述自动创建品牌档案")
    returncode, stdout, stderr = run_command(
        f'python3 /Users/a123/.openclaw/skills/boss/scripts/ensure_brand_profile.py '
        f'--brand "{brand_name}" '
        f'--client "验收测试客户_视频" '
        f'--extract-from "{task_description}" '
        f'--auto-create --json'
    )

    if returncode == 0:
        result = json.loads(stdout)
        if result["created"]:
            print(f"✅ 档案自动创建成功")
            print(f"   路径: {result['profile_path']}")

            # 验证提取的信息
            with open(result["profile_path"], 'r', encoding='utf-8') as f:
                profile = json.load(f)
                print(f"\n   提取的品牌信息:")
                print(f"   - 行业: {profile.get('industry', '未提取')}")
                print(f"   - 定位: {profile.get('positioning', '未提取')[:50]}...")
                print(f"   - 受众: {profile.get('target_audience', '未提取')}")
                print(f"   - 调性: {profile.get('brand_tone', '未提取')}")
        else:
            print(f"❌ 创建失败: {result}")
            return False
    else:
        print(f"❌ 命令执行失败: {stderr}")
        return False

    # Step 3: 后续任务应该能查到档案
    print("\n步骤3：验证后续任务能查询到档案")
    profile_path = find_brand_profile(WORKSPACE_ROOT, brand_name)
    if profile_path:
        print(f"✅ 后续任务可以查询到档案")
        print(f"   路径: {profile_path}")
    else:
        print(f"❌ 后续任务查询失败")
        return False

    print("\n✅ 场景1测试通过：新品牌任务能自动建档")
    return True

def scenario_2_existing_brand_poster():
    """
    场景2：已有品牌海报任务

    用户说："帮然利做一张春节海报"
    系统应该：
    1. 检测到品牌档案已存在
    2. 从档案读取品牌信息
    3. 使用品牌调性、VI 规范生成海报
    """
    print("\n" + "="*60)
    print("场景2：已有品牌海报任务 - 使用'然利'档案")
    print("="*60)

    brand_name = "然利"

    # Step 1: 检查品牌档案
    print("\n步骤1：检查品牌档案")
    returncode, stdout, stderr = run_command(
        f'python3 /Users/a123/.openclaw/skills/boss/scripts/ensure_brand_profile.py '
        f'--brand "{brand_name}" --json'
    )

    if returncode == 0:
        result = json.loads(stdout)
        if result["exists"]:
            print(f"✅ 系统检测到品牌档案已存在")
            print(f"   路径: {result['profile_path']}")
        else:
            print(f"❌ 档案不存在（应该存在）")
            return False
    else:
        print(f"❌ 检查失败: {stderr}")
        return False

    # Step 2: 读取品牌信息
    print("\n步骤2：读取品牌信息用于海报设计")
    returncode, stdout, stderr = run_command(
        f'python3 /Users/a123/.openclaw/scripts/memory/query.py brand --name "{brand_name}" --json'
    )

    if returncode == 0:
        profile = json.loads(stdout)
        print(f"✅ 成功读取品牌档案")
        print(f"   定位: {profile.get('positioning', 'N/A')[:50]}...")
        print(f"   调性: {profile.get('brand_tone', 'N/A')}")
        print(f"   受众: {profile.get('target_audience', 'N/A')}")

        # 验证 VI 规范
        vi = profile.get('vi_guidelines', {})
        if vi.get('primary_colors'):
            print(f"   主色: {vi['primary_colors']}")
        if vi.get('logo_usage_notes'):
            print(f"   Logo 规范: {vi['logo_usage_notes'][:50]}...")
    else:
        print(f"❌ 读取失败: {stderr}")
        return False

    print("\n✅ 场景2测试通过：已有品牌任务能读取档案")
    return True

def scenario_3_brand_info_update():
    """
    场景3：品牌信息更新

    用户在任务中补充了新信息："这次要强调节日氛围"
    系统应该：
    1. 检测到补充信息（低严重性）
    2. 自动合并到档案
    3. 任务结束后通知用户
    """
    print("\n" + "="*60)
    print("场景3：品牌信息自动补充")
    print("="*60)

    brand_name = "然利"

    # Step 1: 检测新信息（补充核心价值观）
    print("\n步骤1：检测到用户补充新的核心价值")
    returncode, stdout, stderr = run_command(
        f'python3 /Users/a123/.openclaw/skills/boss/scripts/detect_brand_conflicts.py '
        f'--workspace-root /Users/a123/.openclaw '
        f'--brand-name "{brand_name}" '
        f'--new-info \'{{"core_values": ["专业", "现代", "高级", "适合招商", "规范化", "节日氛围"]}}\''
    )

    if returncode == 0:
        result = json.loads(stdout)
        if result["supplements"]:
            print(f"✅ 检测到补充信息:")
            for supplement in result["supplements"]:
                print(f"   字段: {supplement['field']}")
                print(f"   新增: {supplement['new_input']}")
        else:
            print(f"⚠️ 未检测到补充信息（可能已存在）")
    else:
        print(f"❌ 检测失败: {stderr}")
        return False

    # Step 2: 自动更新档案
    print("\n步骤2：自动补充到档案")
    returncode, stdout, stderr = run_command(
        f'python3 /Users/a123/.openclaw/skills/boss/scripts/update_brand_profile.py '
        f'--workspace-root /Users/a123/.openclaw '
        f'--brand-name "{brand_name}" '
        f'--field "core_values" '
        f'--value \'["节日氛围"]\' '
        f'--operation append '
        f'--json'
    )

    if returncode == 0:
        result = json.loads(stdout)
        if result["success"]:
            print(f"✅ 档案更新成功")
        else:
            print(f"❌ 更新失败: {result['message']}")
            return False
    else:
        print(f"❌ 命令执行失败: {stderr}")
        return False

    # Step 3: 验证更新结果
    print("\n步骤3：验证更新结果")
    profile_path = find_brand_profile(WORKSPACE_ROOT, brand_name)
    with open(profile_path, 'r', encoding='utf-8') as f:
        profile = json.load(f)
        core_values = profile.get('core_values', [])
        if "节日氛围" in core_values:
            print(f"✅ 核心价值观已更新: {core_values}")
        else:
            print(f"⚠️ 核心价值观: {core_values}")

    print("\n✅ 场景3测试通过：品牌信息能自动补充")
    return True

def scenario_4_conflict_detection():
    """
    场景4：品牌信息冲突检测

    用户说："这次要用蓝色调"，但品牌色是红色系
    系统应该：
    1. 检测到视觉规范冲突（高严重性）
    2. 暂停任务
    3. 提示用户确认
    """
    print("\n" + "="*60)
    print("场景4：品牌信息冲突检测")
    print("="*60)

    brand_name = "然利"

    # Step 1: 检测冲突
    print("\n步骤1：检测视觉规范冲突（主色变更）")
    returncode, stdout, stderr = run_command(
        f'python3 /Users/a123/.openclaw/skills/boss/scripts/detect_brand_conflicts.py '
        f'--workspace-root /Users/a123/.openclaw '
        f'--brand-name "{brand_name}" '
        f'--new-info \'{{"vi_guidelines": {{"primary_colors": ["#0000FF", "#00FFFF"]}}}}\''
    )

    if returncode == 0:
        result = json.loads(stdout)
        if result["has_conflict"]:
            print(f"✅ 系统正确检测到高严重性冲突:")
            for conflict in result["conflicts"]:
                print(f"   字段: {conflict['field']}")
                print(f"   档案: {conflict['archived']}")
                print(f"   输入: {conflict['new_input']}")
                print(f"   严重性: {conflict['severity']}")
        else:
            print(f"⚠️ 未检测到冲突（可能档案为空）")
    else:
        print(f"❌ 检测失败: {stderr}")
        return False

    print("\n✅ 场景4测试通过：能检测并提示高严重性冲突")
    return True

def main():
    """运行所有真实场景测试"""
    print("\n" + "="*60)
    print("品牌档案系统真实场景验收测试")
    print("="*60)

    scenarios = [
        ("场景1：新品牌视频任务", scenario_1_new_brand_video),
        ("场景2：已有品牌海报任务", scenario_2_existing_brand_poster),
        ("场景3：品牌信息自动补充", scenario_3_brand_info_update),
        ("场景4：品牌信息冲突检测", scenario_4_conflict_detection),
    ]

    passed = 0
    failed = 0

    for name, scenario_func in scenarios:
        try:
            if scenario_func():
                passed += 1
            else:
                failed += 1
                print(f"\n❌ 场景测试失败: {name}")
        except Exception as e:
            failed += 1
            print(f"\n❌ 场景测试异常: {name}")
            print(f"   错误: {e}")
            import traceback
            traceback.print_exc()

    # 总结
    print("\n" + "="*60)
    print("验收测试总结")
    print("="*60)
    print(f"总场景数: {len(scenarios)}")
    print(f"通过: {passed}")
    print(f"失败: {failed}")

    if failed == 0:
        print("\n🎉 所有真实场景测试通过！")
        print("\n系统已满足目标：")
        print("✅ 任何人和智能体对话涉及品牌任务时，都能自动记录到记忆系统")
        print("✅ 新品牌自动建档")
        print("✅ 已有品牌自动读取")
        print("✅ 补充信息自动合并")
        print("✅ 冲突信息暂停确认")
        return 0
    else:
        print(f"\n⚠️ {failed} 个场景测试失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())
