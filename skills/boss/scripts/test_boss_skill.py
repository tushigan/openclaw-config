#!/usr/bin/env python3
"""
Boss Skill 品牌记忆集成测试

测试场景：
1. ensure_brand_profile 自动创建品牌
2. find_brand_profile 查找品牌
3. update_brand_profile 更新品牌
4. detect_brand_conflicts 冲突检测
5. create_agency_project 创建项目（包含品牌创建）
"""

import os
import sys
import json
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

# 添加 memory/lib 到路径
memory_lib_path = "/Users/a123/.openclaw/scripts/memory/lib"
sys.path.insert(0, memory_lib_path)

# 从 lib 包中导入
from utils import get_project_root, read_json, write_json, get_timestamp


class BossSkillTester:
    def __init__(self):
        self.results = {
            "timestamp": get_timestamp(),
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "errors": [],
            "details": []
        }
        self.test_brand = f"Boss测试品牌_{datetime.now().strftime('%H%M%S')}"
        self.test_client = f"Boss测试客户_{datetime.now().strftime('%H%M%S')}"
        self.test_project = f"Boss测试项目_{datetime.now().strftime('%H%M%S')}"
        self.project_root = Path(get_project_root())
        self.boss_scripts = Path("/Users/a123/.openclaw/skills/boss/scripts")

    def run_command(self, cmd, description):
        """执行命令并返回结果"""
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(self.boss_scripts)
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": "Command timeout",
                "returncode": -1
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "returncode": -1
            }

    def test(self, name, func):
        """执行单个测试"""
        self.results["total_tests"] += 1
        print(f"\n{'='*60}")
        print(f"测试 {self.results['total_tests']}: {name}")
        print(f"{'='*60}")

        try:
            result = func()
            if result["success"]:
                self.results["passed"] += 1
                print(f"✅ 通过: {result['message']}")
            else:
                self.results["failed"] += 1
                self.results["errors"].append({
                    "test": name,
                    "error": result["message"]
                })
                print(f"❌ 失败: {result['message']}")

            self.results["details"].append({
                "test": name,
                "success": result["success"],
                "message": result["message"]
            })

            return result["success"]
        except Exception as e:
            self.results["failed"] += 1
            self.results["errors"].append({
                "test": name,
                "error": str(e)
            })
            print(f"❌ 异常: {str(e)}")
            return False

    def teardown(self):
        """清理测试数据"""
        print("\n🧹 测试清理...")

        # 清理测试客户目录
        test_client_dir = self.project_root / self.test_client
        if test_client_dir.exists():
            shutil.rmtree(test_client_dir)
            print(f"   ✅ 已删除测试客户目录")

        # 清理注册表中的测试记录
        registry_path = self.project_root / "_registry.json"
        if registry_path.exists():
            registry = read_json(str(registry_path))

            # 清理测试客户和品牌
            registry["clients"] = [c for c in registry.get("clients", []) if not c["name"].startswith("Boss测试")]
            registry["brands"] = [b for b in registry.get("brands", []) if not b["name"].startswith("Boss测试")]

            registry["last_updated"] = get_timestamp()
            write_json(str(registry_path), registry)
            print(f"   🧹 已清理注册表中的测试记录")

    # ========== 测试用例 ==========

    def test_ensure_brand_profile_auto_create(self):
        """测试1: ensure_brand_profile 自动创建品牌"""
        cmd = f'python3 ensure_brand_profile.py --brand "{self.test_brand}" --client "{self.test_client}" --auto-create --json'
        result = self.run_command(cmd, "自动创建品牌")

        if not result["success"]:
            return {
                "success": False,
                "message": f"ensure_brand_profile 失败: {result['stderr']}"
            }

        try:
            data = json.loads(result["stdout"])
            if data.get("created") or data.get("exists"):
                # 验证注册表
                registry = read_json(str(self.project_root / "_registry.json"))
                brand_names = [b["name"] for b in registry.get("brands", [])]

                if self.test_brand in brand_names:
                    return {
                        "success": True,
                        "message": "ensure_brand_profile 成功且已自动注册"
                    }
                else:
                    return {
                        "success": False,
                        "message": "品牌创建成功但未注册"
                    }
            else:
                return {
                    "success": False,
                    "message": f"品牌未创建: {data}"
                }
        except json.JSONDecodeError:
            return {
                "success": False,
                "message": f"返回数据格式错误: {result['stdout']}"
            }

    def test_find_brand_profile(self):
        """测试2: find_brand_profile 查找品牌"""
        cmd = f'python3 find_brand_profile.py --brand-name "{self.test_brand}"'
        result = self.run_command(cmd, "查找品牌")

        if result["success"] and self.test_brand in result["stdout"]:
            return {
                "success": True,
                "message": "find_brand_profile 成功找到品牌"
            }
        else:
            return {
                "success": False,
                "message": f"find_brand_profile 未找到品牌: {result['stderr']}"
            }

    def test_update_brand_profile(self):
        """测试3: update_brand_profile 更新品牌字段"""
        cmd = f'python3 update_brand_profile.py --brand-name "{self.test_brand}" --field industry --value "测试行业"'
        result = self.run_command(cmd, "更新品牌字段")

        if result["success"]:
            # 验证更新
            brand_dir = self.project_root / self.test_client / self.test_brand
            profile_path = brand_dir / "_brand-profile.json"

            if profile_path.exists():
                profile = read_json(str(profile_path))
                if profile.get("industry") == "测试行业":
                    return {
                        "success": True,
                        "message": "update_brand_profile 成功更新字段"
                    }
                else:
                    return {
                        "success": False,
                        "message": "字段更新未生效"
                    }
            else:
                return {
                    "success": False,
                    "message": "品牌档案文件不存在"
                }
        else:
            return {
                "success": False,
                "message": f"update_brand_profile 失败: {result['stderr']}"
            }

    def test_detect_brand_conflicts(self):
        """测试4: detect_brand_conflicts 冲突检测"""
        # detect_brand_conflicts 需要 --new-info 参数，传递 JSON
        new_info = json.dumps({"brand_tone": "新调性"})
        cmd = f'python3 detect_brand_conflicts.py --brand-name "{self.test_brand}" --new-info \'{new_info}\''
        result = self.run_command(cmd, "冲突检测")

        # 冲突检测应该成功执行
        if result["success"] or "conflict" in result["stdout"].lower() or "no conflicts" in result["stdout"].lower():
            return {
                "success": True,
                "message": "detect_brand_conflicts 正常工作"
            }
        else:
            return {
                "success": False,
                "message": f"detect_brand_conflicts 失败: {result['stderr']}"
            }

    def test_create_agency_project(self):
        """测试5: create_agency_project 创建项目（含品牌创建）"""
        test_brand_2 = f"Boss测试品牌2_{datetime.now().strftime('%H%M%S')}"

        # 使用 Python 直接调用（避免命令行复杂性）
        import sys
        sys.path.insert(0, str(self.boss_scripts))

        try:
            from agency_project import create_agency_project

            project_dir = create_agency_project(
                workspace_root=self.project_root,
                brand_name=test_brand_2,
                campaign_name=self.test_project,
                brand_info={
                    "client_name": self.test_client,
                    "brand_tone": "测试调性",
                    "positioning": "测试定位",
                    "core_values": ["价值1", "价值2"]  # 传递列表而不是字符串
                }
            )

            # 验证项目创建
            if project_dir.exists():
                # 验证注册表
                registry = read_json(str(self.project_root / "_registry.json"))
                brand_names = [b["name"] for b in registry.get("brands", [])]

                if test_brand_2 in brand_names:
                    return {
                        "success": True,
                        "message": "create_agency_project 成功创建项目和品牌，且已注册"
                    }
                else:
                    return {
                        "success": False,
                        "message": "项目创建成功但品牌未注册"
                    }
            else:
                return {
                    "success": False,
                    "message": "项目目录未创建"
                }
        except Exception as e:
            import traceback
            return {
                "success": False,
                "message": f"create_agency_project 异常: {str(e)}\n{traceback.format_exc()}"
            }

    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 Boss Skill 品牌记忆集成测试")
        print("="*60)

        # 执行测试
        self.test("ensure_brand_profile 自动创建", self.test_ensure_brand_profile_auto_create)
        self.test("find_brand_profile 查找品牌", self.test_find_brand_profile)
        self.test("update_brand_profile 更新字段", self.test_update_brand_profile)
        self.test("detect_brand_conflicts 冲突检测", self.test_detect_brand_conflicts)
        self.test("create_agency_project 创建项目", self.test_create_agency_project)

        self.teardown()

        # 生成报告
        self.print_report()
        self.save_report()

    def print_report(self):
        """打印测试报告"""
        print("\n" + "="*60)
        print("📊 Boss Skill 测试报告")
        print("="*60)
        print(f"总测试数: {self.results['total_tests']}")
        print(f"✅ 通过: {self.results['passed']}")
        print(f"❌ 失败: {self.results['failed']}")
        print(f"通过率: {self.results['passed']/self.results['total_tests']*100:.1f}%")

        if self.results["errors"]:
            print("\n❌ 失败的测试：")
            for error in self.results["errors"]:
                print(f"   • {error['test']}: {error['error']}")

    def save_report(self):
        """保存测试报告"""
        report_path = "/Users/a123/.openclaw/skills/boss/scripts/test_boss_skill_report.json"
        write_json(report_path, self.results)
        print(f"\n📄 详细报告已保存: {report_path}")


def main():
    tester = BossSkillTester()
    tester.run_all_tests()

    # 返回状态码
    if tester.results["failed"] == 0:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
