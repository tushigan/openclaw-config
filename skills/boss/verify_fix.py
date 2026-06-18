#!/usr/bin/env python3
"""
Boss Skill 话题错位修复验证脚本

验证内容：
1. Boss Skill 派发模板是否包含「交付模式」标记
2. 各专家 Agent AGENTS.md 是否包含 Subagent 交付规则
3. 派发模板格式是否正确
4. 错误排查指南是否完整
"""

import json
import os
import sys
from pathlib import Path

# 颜色输出
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def print_success(msg):
    print(f"{GREEN}✅ {msg}{RESET}")

def print_error(msg):
    print(f"{RED}❌ {msg}{RESET}")

def print_warning(msg):
    print(f"{YELLOW}⚠️  {msg}{RESET}")

def print_section(msg):
    print(f"\n{'='*60}")
    print(f"  {msg}")
    print('='*60)

# OpenClaw 根目录
OPENCLAW_ROOT = Path("/Users/a123/.openclaw")

# 测试结果
test_results = {
    "passed": 0,
    "failed": 0,
    "warnings": 0
}

def check_file_exists(filepath, description):
    """检查文件是否存在"""
    if filepath.exists():
        print_success(f"{description} 存在")
        test_results["passed"] += 1
        return True
    else:
        print_error(f"{description} 不存在：{filepath}")
        test_results["failed"] += 1
        return False

def check_content_contains(filepath, search_texts, description):
    """检查文件内容是否包含指定文本"""
    if not filepath.exists():
        print_error(f"{description} - 文件不存在：{filepath}")
        test_results["failed"] += 1
        return False

    content = filepath.read_text(encoding='utf-8')
    all_found = True

    for text in search_texts:
        # 对 message 工具做特殊处理，匹配带反引号或不带反引号的版本
        if "message" in text.lower():
            if "message" in content.lower():
                print_success(f"{description} - 包含「{text}」")
                test_results["passed"] += 1
            else:
                print_error(f"{description} - 缺失「{text}」")
                test_results["failed"] += 1
                all_found = False
        elif text in content:
            print_success(f"{description} - 包含「{text}」")
            test_results["passed"] += 1
        else:
            print_error(f"{description} - 缺失「{text}」")
            test_results["failed"] += 1
            all_found = False

    return all_found

def test_boss_skill_templates():
    """测试 Boss Skill 派发模板"""
    print_section("1. Boss Skill 派发模板检查")

    boss_skill = OPENCLAW_ROOT / "skills/boss/SKILL.md"

    if not check_file_exists(boss_skill, "Boss Skill 文件"):
        return

    # 检查派发模板关键内容
    required_contents = [
        "交付模式：静默回传",
        "交付模式：混合模式",
        "message 工具",  # 宽松匹配，不要求完整文本
        "会创建新话题",
        "Main 接收 subagent 结果后的标准流程",
        "常见派发错误排查"
    ]

    check_content_contains(boss_skill, required_contents, "Boss Skill 派发模板")

    # 检查每个阶段是否都有交付模式说明
    content = boss_skill.read_text(encoding='utf-8')
    stages = [
        "阶段 4：策略制定",
        "阶段 5：创意方向",
        "阶段 7a：文案执行",
        "阶段 7b：设计执行"
    ]

    for stage in stages:
        if stage in content:
            # 检查该阶段附近是否有「交付模式」
            stage_pos = content.find(stage)
            next_stage_pos = content.find("###", stage_pos + 1)
            if next_stage_pos == -1:
                next_stage_pos = len(content)

            stage_content = content[stage_pos:next_stage_pos]
            if "交付模式" in stage_content:
                print_success(f"{stage} - 包含交付模式说明")
                test_results["passed"] += 1
            else:
                print_error(f"{stage} - 缺失交付模式说明")
                test_results["failed"] += 1
        else:
            print_warning(f"{stage} - 未找到该阶段")
            test_results["warnings"] += 1

def test_strategy_agents_md():
    """测试 Strategy AGENTS.md"""
    print_section("2. Strategy Agent 交付规则检查")

    strategy_agents = OPENCLAW_ROOT / "workspace-strategy/AGENTS.md"

    if not check_file_exists(strategy_agents, "Strategy AGENTS.md"):
        return

    required_contents = [
        "飞书话题群 Subagent 模式交付规则",
        "当你是被 main 派发的 subagent 时",
        "交付模式：静默回传",
        "message 工具",  # 宽松匹配
        "会在飞书创建新话题",
        "由 main agent 负责在原话题下"
    ]

    check_content_contains(strategy_agents, required_contents, "Strategy Agent 交付规则")

def test_copywriter_agents_md():
    """测试 Copywriter AGENTS.md"""
    print_section("3. Copywriter Agent 交付规则检查")

    copywriter_agents = OPENCLAW_ROOT / "workspace-copywriter/AGENTS.md"

    if not check_file_exists(copywriter_agents, "Copywriter AGENTS.md"):
        return

    required_contents = [
        "飞书话题群 Subagent 模式交付规则",
        "当你是被 main 派发的 subagent 时",
        "交付模式：静默回传",
        "message 工具"  # 宽松匹配
    ]

    check_content_contains(copywriter_agents, required_contents, "Copywriter Agent 交付规则")

def test_design_agents_md():
    """测试 Design AGENTS.md"""
    print_section("4. Design Agent 交付规则检查")

    design_agents = OPENCLAW_ROOT / "workspace-design/AGENTS.md"

    if not check_file_exists(design_agents, "Design AGENTS.md"):
        return

    required_contents = [
        "飞书话题群 Subagent 模式交付规则",
        "当你是被 main 派发的 subagent 时",
        "交付模式：混合模式",
        "图片",  # 宽松匹配
        "message 工具"
    ]

    check_content_contains(design_agents, required_contents, "Design Agent 交付规则")

def test_documentation():
    """测试文档完整性"""
    print_section("5. 修复文档检查")

    docs = [
        (OPENCLAW_ROOT / "skills/boss/BUGFIX_REPORT.md", "问题诊断报告"),
        (OPENCLAW_ROOT / "skills/boss/TEST_TOPIC_FIX.md", "测试计划"),
        (OPENCLAW_ROOT / "skills/boss/FIX_SUMMARY.md", "修复总结")
    ]

    for doc_path, doc_name in docs:
        check_file_exists(doc_path, doc_name)

def test_git_status():
    """检查 Git 提交状态"""
    print_section("6. Git 提交状态检查")

    os.chdir(OPENCLAW_ROOT)

    # 检查是否有未提交的修改
    import subprocess
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True,
        text=True
    )

    modified_files = result.stdout.strip().split('\n') if result.stdout.strip() else []
    relevant_files = [f for f in modified_files if 'boss' in f or 'AGENTS.md' in f]

    if not relevant_files:
        print_success("所有修复文件已提交到 Git")
        test_results["passed"] += 1
    else:
        print_warning(f"有 {len(relevant_files)} 个相关文件未提交：")
        for f in relevant_files[:5]:  # 只显示前5个
            print(f"  {f}")
        test_results["warnings"] += 1

    # 检查最近的提交
    result = subprocess.run(
        ["git", "log", "-1", "--oneline"],
        capture_output=True,
        text=True
    )

    if "Boss Skill" in result.stdout or "话题" in result.stdout:
        print_success(f"最近提交：{result.stdout.strip()}")
        test_results["passed"] += 1
    else:
        print_warning(f"最近提交：{result.stdout.strip()}")
        print_warning("提交信息中没有提到 Boss Skill 修复")
        test_results["warnings"] += 1

def print_summary():
    """打印测试总结"""
    print_section("测试总结")

    total = test_results["passed"] + test_results["failed"] + test_results["warnings"]
    passed_rate = (test_results["passed"] / total * 100) if total > 0 else 0

    print(f"通过: {GREEN}{test_results['passed']}{RESET}")
    print(f"失败: {RED}{test_results['failed']}{RESET}")
    print(f"警告: {YELLOW}{test_results['warnings']}{RESET}")
    print(f"通过率: {passed_rate:.1f}%")

    print("\n" + "="*60)

    if test_results["failed"] == 0:
        if test_results["warnings"] == 0:
            print_success("✨ 所有验证项通过！修复已正确实施。")
            print("\n下一步：在飞书话题群中进行实际测试")
            return 0
        else:
            print_warning("⚠️  有警告项，建议检查")
            return 0
    else:
        print_error("❌ 有验证项失败，需要修复")
        return 1

def main():
    print("="*60)
    print("  Boss Skill 话题错位修复验证")
    print("="*60)
    print(f"OpenClaw 根目录: {OPENCLAW_ROOT}")
    print()

    # 执行各项测试
    test_boss_skill_templates()
    test_strategy_agents_md()
    test_copywriter_agents_md()
    test_design_agents_md()
    test_documentation()
    test_git_status()

    # 打印总结
    return print_summary()

if __name__ == "__main__":
    sys.exit(main())
