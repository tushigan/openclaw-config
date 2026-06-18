#!/usr/bin/env python3
"""
OpenClaw 记忆系统集成测试脚本

测试所有 agent 和 skill 是否能正确读取和写入记忆系统。
"""

import subprocess
import json
import sys
import os
from datetime import datetime

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def run_command(cmd, check=True):
    """执行命令并返回结果"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            check=check
        )
        return result.stdout, result.stderr, result.returncode
    except subprocess.CalledProcessError as e:
        return e.stdout, e.stderr, e.returncode

def print_test(name, passed, details=""):
    """打印测试结果"""
    status = f"{Colors.GREEN}✅ PASS{Colors.END}" if passed else f"{Colors.RED}❌ FAIL{Colors.END}"
    print(f"{status} {name}")
    if details:
        print(f"    {details}")

def test_memory_scripts_exist():
    """测试 1: 验证记忆系统脚本是否存在"""
    print(f"\n{Colors.BLUE}=== 测试 1: 验证记忆系统脚本 ==={Colors.END}\n")

    scripts = [
        "/Users/a123/.openclaw/scripts/memory/query.py",
        "/Users/a123/.openclaw/scripts/memory/client.py",
        "/Users/a123/.openclaw/scripts/memory/brand.py",
        "/Users/a123/.openclaw/scripts/memory/project.py",
        "/Users/a123/.openclaw/scripts/memory/task.py",
    ]

    all_exist = True
    for script in scripts:
        exists = os.path.exists(script)
        print_test(f"脚本存在: {os.path.basename(script)}", exists)
        all_exist = all_exist and exists

    return all_exist

def test_brand_query():
    """测试 2: 测试品牌档案查询"""
    print(f"\n{Colors.BLUE}=== 测试 2: 品牌档案查询 ==={Colors.END}\n")

    # 列出所有品牌
    stdout, stderr, code = run_command(
        'python3 /Users/a123/.openclaw/scripts/memory/query.py list-brands 2>/dev/null | head -5',
        check=False
    )

    if code == 0 and stdout:
        print_test("列出品牌", True, f"找到品牌列表")

        # 提取第一个品牌名称进行查询测试
        lines = stdout.strip().split('\n')
        for line in lines:
            if '•' in line:
                # 提取品牌名（格式：   • brand_name (client) - tone）
                parts = line.split('•')[1].split('(')[0].strip()
                if parts:
                    stdout2, stderr2, code2 = run_command(
                        f'python3 /Users/a123/.openclaw/scripts/memory/query.py brand --name "{parts}" --json 2>/dev/null',
                        check=False
                    )

                    if code2 == 0:
                        try:
                            data = json.loads(stdout2)
                            has_required = 'brand_id' in data and 'brand_tone' in data
                            print_test(f"查询品牌档案: {parts}", has_required,
                                     f"品牌ID: {data.get('brand_id', 'N/A')}")
                            return has_required
                        except json.JSONDecodeError:
                            print_test(f"查询品牌档案: {parts}", False, "JSON 解析失败")
                            return False
                    break

    print_test("品牌查询", False, "无法获取品牌列表")
    return False

def test_brand_assets_query():
    """测试 3: 测试品牌资产查询"""
    print(f"\n{Colors.BLUE}=== 测试 3: 品牌资产查询 ==={Colors.END}\n")

    # 使用已知品牌测试
    stdout, stderr, code = run_command(
        'python3 /Users/a123/.openclaw/scripts/memory/query.py list-brands 2>/dev/null | head -5',
        check=False
    )

    if code == 0 and stdout:
        lines = stdout.strip().split('\n')
        for line in lines:
            if '•' in line:
                parts = line.split('•')[1].split('(')[0].strip()
                if parts:
                    stdout2, stderr2, code2 = run_command(
                        f'python3 /Users/a123/.openclaw/scripts/memory/query.py assets --brand "{parts}" 2>&1',
                        check=False
                    )

                    # 品牌资产查询的行为：
                    # 1. 如果资产存在：返回 JSON 或详情，code=0
                    # 2. 如果资产目录存在但为空：可能无输出，code=1（这是正常的）
                    # 3. 如果品牌不存在：返回错误信息

                    # 只要不是明确的错误（如"不存在"、"failed"等），就算通过
                    is_error = (
                        '不存在' in stdout2 or
                        '不存在' in stderr2 or
                        'failed' in stdout2.lower() or
                        'error' in stdout2.lower()
                    )

                    # 如果输出为空但 code 非 0，检查是否有资产目录
                    if not stdout2.strip() and code2 != 0:
                        # 检查品牌资产目录是否存在
                        check_cmd = f'ls /Users/a123/.openclaw/projects/*/{parts}/_brand-assets/ 2>/dev/null | wc -l'
                        check_out, _, check_code = run_command(check_cmd, check=False)
                        dir_exists = check_code == 0 and int(check_out.strip() or 0) > 0

                        passed = dir_exists
                        details = "品牌资产目录存在但为空（正常）" if dir_exists else "品牌或资产目录不存在"
                    else:
                        passed = not is_error
                        details = "查询成功" if passed else f"查询错误: {stdout2[:50]}"

                    print_test(f"查询品牌资产: {parts}", passed, details)
                    return passed

    print_test("品牌资产查询", False, "无法获取品牌列表")
    return False

def test_project_query():
    """测试 4: 测试项目查询"""
    print(f"\n{Colors.BLUE}=== 测试 4: 项目查询 ==={Colors.END}\n")

    stdout, stderr, code = run_command(
        'python3 /Users/a123/.openclaw/scripts/memory/query.py list-projects 2>/dev/null | head -5',
        check=False
    )

    passed = code == 0 and stdout and '项目' in stdout
    details = "找到项目列表" if passed else "无法获取项目列表"
    print_test("列出项目", passed, details)

    return passed

def test_skill_integration():
    """测试 5: 验证 skill 集成状态"""
    print(f"\n{Colors.BLUE}=== 测试 5: Skill 集成状态 ==={Colors.END}\n")

    skills = [
        ("boss", "/Users/a123/.openclaw/skills/boss/SKILL.md"),
        ("business-project-intake", "/Users/a123/.openclaw/workspace-business/skills/business-project-intake/SKILL.md"),
        ("wenan", "/Users/a123/.openclaw/workspace-copywriter/skills/wenan/SKILL.md"),
        ("brand-poster-creator", "/Users/a123/.openclaw/workspace-design/skills/brand-poster-creator/SKILL.md"),
        ("celue-zj", "/Users/a123/.openclaw/workspace-strategy/skills/celue-zj/SKILL.md"),
    ]

    all_integrated = True
    for skill_name, skill_path in skills:
        if os.path.exists(skill_path):
            with open(skill_path, 'r', encoding='utf-8') as f:
                content = f.read()

            has_memory_section = '## 🔴 记忆系统集成（执行前必读）' in content
            has_step0 = '### Step 0: 项目立项与任务创建' in content
            has_boundary = '# 0. 验证必填变量' in content
            has_error_handling = 'jq -e' in content

            passed = has_memory_section and has_step0 and has_boundary and has_error_handling

            details_parts = []
            if not has_memory_section:
                details_parts.append("缺少记忆集成章节")
            if not has_step0:
                details_parts.append("缺少 Step 0")
            if not has_boundary:
                details_parts.append("缺少边界验证")
            if not has_error_handling:
                details_parts.append("缺少错误处理")

            details = "集成完整" if passed else ", ".join(details_parts)
            print_test(f"Skill 集成: {skill_name}", passed, details)
            all_integrated = all_integrated and passed
        else:
            print_test(f"Skill 集成: {skill_name}", False, "文件不存在")
            all_integrated = False

    return all_integrated

def test_agents_md():
    """测试 6: 验证 AGENTS.md 规则"""
    print(f"\n{Colors.BLUE}=== 测试 6: AGENTS.md 规则 ==={Colors.END}\n")

    workspaces = [
        "workspace",
        "workspace-strategy",
        "workspace-design",
        "workspace-copywriter",
        "workspace-business",
    ]

    all_have_rule = True
    for workspace in workspaces:
        agents_path = f"/Users/a123/.openclaw/{workspace}/AGENTS.md"

        if os.path.exists(agents_path):
            with open(agents_path, 'r', encoding='utf-8') as f:
                content = f.read()

            has_rule = '## 规则 0.1.1: 品牌任务必须先查询记忆' in content
            has_query_examples = 'query.py brand' in content

            passed = has_rule and has_query_examples
            details = "规则完整" if passed else "缺少规则 0.1.1"
            print_test(f"{workspace}/AGENTS.md", passed, details)
            all_have_rule = all_have_rule and passed
        else:
            print_test(f"{workspace}/AGENTS.md", False, "文件不存在")
            all_have_rule = False

    return all_have_rule

def test_create_test_project():
    """测试 7: 创建测试项目"""
    print(f"\n{Colors.BLUE}=== 测试 7: 创建测试项目 ==={Colors.END}\n")

    test_client = "测试客户_集成测试"
    test_brand = "测试品牌_集成测试"
    test_project = f"集成测试项目_{datetime.now().strftime('%Y%m%d%H%M%S')}"

    # 创建项目
    cmd = f'''python3 /Users/a123/.openclaw/scripts/memory/project.py get-or-create \
      --client "{test_client}" \
      --brand "{test_brand}" \
      --project "{test_project}" \
      --campaign-type "测试" \
      --json 2>&1 | grep -A 100 '^{{'  '''

    stdout, stderr, code = run_command(cmd, check=False)

    if code == 0 and stdout:
        try:
            data = json.loads(stdout)
            project_id = data.get('project_id')
            project_path = data.get('project_path')

            passed = project_id and project_path and os.path.exists(project_path)
            details = f"项目ID: {project_id}" if passed else "项目创建失败"
            print_test("创建测试项目", passed, details)

            if passed:
                # 测试任务创建
                task_cmd = f'''python3 /Users/a123/.openclaw/scripts/memory/task.py create \
                  --project-id "{project_id}" \
                  --name "测试任务" \
                  --type "test" \
                  --agent "main" \
                  --skill "test-skill" \
                  --brief "集成测试任务" \
                  --json 2>/dev/null'''

                stdout2, stderr2, code2 = run_command(task_cmd, check=False)

                if code2 == 0:
                    try:
                        task_data = json.loads(stdout2)
                        task_id = task_data.get('task_id')
                        print_test("创建测试任务", task_id is not None, f"任务ID: {task_id}")
                        return True
                    except json.JSONDecodeError:
                        print_test("创建测试任务", False, "JSON 解析失败")
                else:
                    print_test("创建测试任务", False, stderr2[:100])

            return passed
        except json.JSONDecodeError:
            print_test("创建测试项目", False, "JSON 解析失败")
            return False
    else:
        print_test("创建测试项目", False, stderr[:100])
        return False

def main():
    """主测试流程"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}OpenClaw 记忆系统集成测试{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")

    results = []

    # 执行所有测试
    results.append(("记忆脚本存在", test_memory_scripts_exist()))
    results.append(("品牌档案查询", test_brand_query()))
    results.append(("品牌资产查询", test_brand_assets_query()))
    results.append(("项目查询", test_project_query()))
    results.append(("Skill 集成", test_skill_integration()))
    results.append(("AGENTS.md 规则", test_agents_md()))
    results.append(("创建测试项目", test_create_test_project()))

    # 汇总结果
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}测试汇总{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}\n")

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    for name, passed in results:
        status = f"{Colors.GREEN}✅ PASS{Colors.END}" if passed else f"{Colors.RED}❌ FAIL{Colors.END}"
        print(f"{status} {name}")

    print(f"\n{Colors.BLUE}总计: {passed_count}/{total_count} 通过{Colors.END}")

    if passed_count == total_count:
        print(f"\n{Colors.GREEN}✅ 所有测试通过！记忆系统集成成功。{Colors.END}\n")
        return 0
    else:
        print(f"\n{Colors.RED}❌ 部分测试失败，请检查上述错误。{Colors.END}\n")
        return 1

if __name__ == '__main__':
    sys.exit(main())
