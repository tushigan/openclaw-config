#!/usr/bin/env python3
"""
记忆系统全量集成测试

测试所有核心功能：
1. 项目管理（创建、查询、更新）
2. 任务管理（创建、查询、更新）
3. 产出归档（保存、版本管理）
4. Skill 集成验证
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime

OPENCLAW_ROOT = Path("/Users/a123/.openclaw")
SCRIPTS_DIR = OPENCLAW_ROOT / "scripts/memory"

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def run_command(cmd, description=""):
    """运行命令并返回结果"""
    if description:
        print(f"  🔧 {description}")

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def test_project_management():
    """测试项目管理"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}")
    print("测试 1: 项目管理")
    print(f"{'='*80}{Colors.ENDC}\n")

    test_client = f"测试客户_{datetime.now().strftime('%H%M%S')}"
    test_brand = f"测试品牌_{datetime.now().strftime('%H%M%S')}"
    test_project = f"测试项目_{datetime.now().strftime('%H%M%S')}"

    tests = []
    project_id = None

    # 测试 1.1: 创建项目
    success, stdout, stderr = run_command(
        f'python3 {SCRIPTS_DIR}/project.py get-or-create '
        f'--client "{test_client}" --brand "{test_brand}" --project "{test_project}" '
        f'--campaign-type "测试" --json',
        "创建测试项目"
    )

    if success and stdout:
        try:
            # 过滤掉非 JSON 输出行
            json_lines = []
            for line in stdout.split('\n'):
                line = line.strip()
                if line.startswith('{') or (json_lines and not line.startswith('✅') and not line.startswith('   ')):
                    json_lines.append(line)

            json_str = '\n'.join(json_lines)
            data = json.loads(json_str)
            project_id = data.get("project_id")
            if project_id:
                tests.append(("创建项目", True, f"项目 ID: {project_id}"))
            else:
                tests.append(("创建项目", False, "未返回 project_id"))
        except Exception as e:
            tests.append(("创建项目", False, f"JSON 解析失败: {str(e)}"))
    else:
        tests.append(("创建项目", False, stderr))

    # 测试 1.2: 查询项目
    if project_id:
        success, stdout, stderr = run_command(
            f'python3 {SCRIPTS_DIR}/project.py get --project-id "{project_id}" --json',
            "查询项目信息"
        )

        if success and stdout:
            try:
                data = json.loads(stdout)
                if data.get("project_id") == project_id:
                    tests.append(("查询项目", True, f"成功查询项目"))
                else:
                    tests.append(("查询项目", False, "项目 ID 不匹配"))
            except:
                tests.append(("查询项目", False, "JSON 解析失败"))
        else:
            tests.append(("查询项目", False, stderr))

    # 测试 1.3: 更新项目阶段
    if project_id:
        success, stdout, stderr = run_command(
            f'python3 {SCRIPTS_DIR}/project.py update-stage --project-id "{project_id}" --stage "策略制定"',
            "更新项目阶段"
        )
        tests.append(("更新项目阶段", success, "阶段已更新" if success else stderr))

    # 测试 1.4: 列出项目
    success, stdout, stderr = run_command(
        f'python3 {SCRIPTS_DIR}/project.py list --client "{test_client}" --json',
        "列出客户的所有项目"
    )

    if success and stdout:
        try:
            projects = json.loads(stdout)
            if len(projects) > 0:
                tests.append(("列出项目", True, f"找到 {len(projects)} 个项目"))
            else:
                tests.append(("列出项目", False, "未找到项目"))
        except:
            tests.append(("列出项目", False, "JSON 解析失败"))
    else:
        tests.append(("列出项目", False, stderr))

    # 输出结果
    for test_name, success, message in tests:
        status = f"{Colors.OKGREEN}✅" if success else f"{Colors.FAIL}❌"
        print(f"{status} {test_name}: {message}{Colors.ENDC}")

    return all(t[1] for t in tests), project_id, test_client, test_brand, test_project

def test_task_management(project_id):
    """测试任务管理"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}")
    print("测试 2: 任务管理")
    print(f"{'='*80}{Colors.ENDC}\n")

    tests = []
    task_id = None

    # 测试 2.1: 创建任务
    task_name = f"测试任务_{datetime.now().strftime('%H%M%S')}"
    success, stdout, stderr = run_command(
        f'python3 {SCRIPTS_DIR}/task.py create '
        f'--project-id "{project_id}" '
        f'--name "{task_name}" '
        f'--type "test" '
        f'--agent "main" '
        f'--skill "test-skill" '
        f'--brief "这是一个测试任务" '
        f'--json',
        "创建测试任务"
    )

    if success and stdout:
        try:
            data = json.loads(stdout)
            task_id = data.get("task_id")
            if task_id:
                tests.append(("创建任务", True, f"任务 ID: {task_id}"))
            else:
                tests.append(("创建任务", False, "未返回 task_id"))
        except:
            tests.append(("创建任务", False, "JSON 解析失败"))
    else:
        tests.append(("创建任务", False, stderr))

    # 测试 2.2: 查询任务
    if task_id:
        success, stdout, stderr = run_command(
            f'python3 {SCRIPTS_DIR}/task.py get --task-id "{task_id}" --json',
            "查询任务信息"
        )

        if success and stdout:
            try:
                data = json.loads(stdout)
                if data.get("task_id") == task_id:
                    tests.append(("查询任务", True, "成功查询任务"))
                else:
                    tests.append(("查询任务", False, "任务 ID 不匹配"))
            except:
                tests.append(("查询任务", False, "JSON 解析失败"))
        else:
            tests.append(("查询任务", False, stderr))

    # 测试 2.3: 更新任务状态
    if task_id:
        success, stdout, stderr = run_command(
            f'python3 {SCRIPTS_DIR}/task.py update-status --task-id "{task_id}" --status "in-progress"',
            "更新任务状态"
        )
        tests.append(("更新任务状态", success, "状态已更新" if success else stderr))

    # 测试 2.4: 列出项目任务
    success, stdout, stderr = run_command(
        f'python3 {SCRIPTS_DIR}/task.py list --project-id "{project_id}" --json',
        "列出项目的所有任务"
    )

    if success and stdout:
        try:
            tasks = json.loads(stdout)
            if len(tasks) > 0:
                tests.append(("列出任务", True, f"找到 {len(tasks)} 个任务"))
            else:
                tests.append(("列出任务", False, "未找到任务"))
        except:
            tests.append(("列出任务", False, "JSON 解析失败"))
    else:
        tests.append(("列出任务", False, stderr))

    # 输出结果
    for test_name, success, message in tests:
        status = f"{Colors.OKGREEN}✅" if success else f"{Colors.FAIL}❌"
        print(f"{status} {test_name}: {message}{Colors.ENDC}")

    return all(t[1] for t in tests), task_id

def test_output_archive(task_id):
    """测试产出归档"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}")
    print("测试 3: 产出归档与版本管理")
    print(f"{'='*80}{Colors.ENDC}\n")

    tests = []

    # 创建测试文件
    test_file = Path(f"/tmp/test_output_{datetime.now().strftime('%H%M%S')}.txt")
    test_file.write_text("测试产出内容\n这是第一版")

    # 测试 3.1: 保存产出 v1
    success, stdout, stderr = run_command(
        f'python3 {SCRIPTS_DIR}/task.py save-output '
        f'--task-id "{task_id}" '
        f'--file "{test_file}" '
        f'--note "第一版" '
        f'--expire-days 30 '
        f'--prompt "测试 prompt" '
        f'--model "test-model"',
        "保存产出 v1"
    )
    tests.append(("保存产出 v1", success, "v1 已保存" if success else stderr))

    # 测试 3.2: 保存产出 v2
    test_file.write_text("测试产出内容\n这是第二版（修订）")
    success, stdout, stderr = run_command(
        f'python3 {SCRIPTS_DIR}/task.py save-output '
        f'--task-id "{task_id}" '
        f'--file "{test_file}" '
        f'--note "第二版（根据反馈修改）" '
        f'--expire-days 30',
        "保存产出 v2"
    )
    tests.append(("保存产出 v2", success, "v2 已保存" if success else stderr))

    # 测试 3.3: 列出所有版本
    success, stdout, stderr = run_command(
        f'python3 {SCRIPTS_DIR}/task.py list-iterations --task-id "{task_id}" --json',
        "列出所有版本"
    )

    if success and stdout:
        try:
            iterations = json.loads(stdout)
            if len(iterations) >= 2:
                tests.append(("列出版本", True, f"找到 {len(iterations)} 个版本"))
            else:
                tests.append(("列出版本", False, f"只找到 {len(iterations)} 个版本"))
        except:
            tests.append(("列出版本", False, "JSON 解析失败"))
    else:
        tests.append(("列出版本", False, stderr))

    # 清理测试文件
    test_file.unlink(missing_ok=True)

    # 输出结果
    for test_name, success, message in tests:
        status = f"{Colors.OKGREEN}✅" if success else f"{Colors.FAIL}❌"
        print(f"{status} {test_name}: {message}{Colors.ENDC}")

    return all(t[1] for t in tests)

def test_skill_integration():
    """测试 Skill 集成验证"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}")
    print("测试 4: Skill 集成验证")
    print(f"{'='*80}{Colors.ENDC}\n")

    audit_report = OPENCLAW_ROOT / "scripts/memory/skill_integration_audit.json"

    if not audit_report.exists():
        print(f"{Colors.FAIL}❌ 审计报告不存在{Colors.ENDC}")
        return False

    with open(audit_report, 'r', encoding='utf-8') as f:
        audit_data = json.load(f)

    # 重新扫描集成状态
    print(f"  🔍 重新扫描 skill 集成状态...")
    success, stdout, stderr = run_command(
        f'python3 {SCRIPTS_DIR}/audit_project_skills.py',
        ""
    )

    if not success:
        print(f"{Colors.FAIL}❌ 重新扫描失败{Colors.ENDC}")
        return False

    # 重新加载报告
    with open(audit_report, 'r', encoding='utf-8') as f:
        new_audit_data = json.load(f)

    total = new_audit_data.get("total", 0)
    fully_integrated = new_audit_data.get("fully_integrated", 0)
    partially_integrated = new_audit_data.get("partially_integrated", 0)
    not_integrated = new_audit_data.get("not_integrated", 0)

    print(f"\n  📊 集成状态统计:")
    print(f"  {Colors.OKGREEN}✅ 完全集成: {fully_integrated}/{total}{Colors.ENDC}")
    print(f"  {Colors.WARNING}⚠️  部分集成: {partially_integrated}/{total}{Colors.ENDC}")
    print(f"  {Colors.FAIL}❌ 未集成: {not_integrated}/{total}{Colors.ENDC}")

    # 检查是否所有 skill 都已完全集成
    if fully_integrated == total:
        print(f"\n{Colors.OKGREEN}✅ 所有 skill 已完全集成记忆系统！{Colors.ENDC}")
        return True
    else:
        print(f"\n{Colors.WARNING}⚠️  仍有 {total - fully_integrated} 个 skill 未完全集成{Colors.ENDC}")
        return False

def main():
    print(f"{Colors.HEADER}{Colors.BOLD}")
    print("="*80)
    print("OpenClaw 记忆系统全量集成测试")
    print("="*80)
    print(f"{Colors.ENDC}\n")

    results = {}

    # 测试 1: 项目管理
    success, project_id, client, brand, project = test_project_management()
    results["项目管理"] = success

    if not success:
        print(f"\n{Colors.FAIL}❌ 项目管理测试失败，停止后续测试{Colors.ENDC}")
        sys.exit(1)

    # 测试 2: 任务管理
    success, task_id = test_task_management(project_id)
    results["任务管理"] = success

    if not success:
        print(f"\n{Colors.FAIL}❌ 任务管理测试失败，停止后续测试{Colors.ENDC}")
        sys.exit(1)

    # 测试 3: 产出归档
    success = test_output_archive(task_id)
    results["产出归档"] = success

    # 测试 4: Skill 集成验证
    success = test_skill_integration()
    results["Skill集成"] = success

    # 总结
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}")
    print("测试总结")
    print(f"{'='*80}{Colors.ENDC}\n")

    all_passed = True
    for test_name, success in results.items():
        status = f"{Colors.OKGREEN}✅ 通过" if success else f"{Colors.FAIL}❌ 失败"
        print(f"{status}: {test_name}{Colors.ENDC}")
        if not success:
            all_passed = False

    print()
    if all_passed:
        print(f"{Colors.OKGREEN}{Colors.BOLD}🎉 所有测试通过！记忆系统全量集成成功！{Colors.ENDC}")
        return 0
    else:
        print(f"{Colors.FAIL}{Colors.BOLD}⚠️  部分测试失败，请检查上述错误信息{Colors.ENDC}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
