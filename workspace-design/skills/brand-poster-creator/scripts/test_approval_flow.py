#!/usr/bin/env python3
"""
审批流程完整测试脚本
模拟 B/A/S 三级项目的完整审批流程，验证所有功能
"""
from __future__ import annotations

import json
import sys
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# 添加脚本目录到 PATH
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from project_grading import (
    init_project_grading,
    request_approval,
    record_approval_response,
    get_approval_status,
    check_timeout,
    handle_timeout
)
from time_tracking import (
    record_stage_time,
    generate_timeline_report,
    generate_retrospective_report
)


def print_section(title: str):
    """打印测试章节标题"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def print_result(success: bool, message: str):
    """打印测试结果"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status}: {message}")


def test_b_grade_project(test_dir: Path) -> bool:
    """测试 B 级项目完整流程"""
    print_section("测试 B 级项目")

    project_dir = test_dir / "BP-20260613-001"
    project_dir.mkdir(parents=True)

    # 创建必要的文件
    (project_dir / "brief.json").write_text(json.dumps({
        "task_id": "BP-20260613-001",
        "brand_name": "测试品牌",
        "type": "节日海报"
    }, ensure_ascii=False, indent=2))

    (project_dir / "images").mkdir(exist_ok=True)
    (project_dir / "images/final_poster.png").touch()

    try:
        # 1. 初始化项目分级
        print("1. 初始化 B 级项目...")
        reviewers = {
            "copywriter": {"name": "张三", "open_id": "ou_copywriter_test"},
            "designer": {"name": "李四", "open_id": "ou_designer_test"}
        }

        grading_config = init_project_grading(project_dir, 'B', reviewers)

        assert grading_config['grade'] == 'B', "项目等级应为 B"
        assert len(grading_config['approval_flow']) == 2, "B 级项目应有 2 个审批节点"
        print_result(True, "B 级项目初始化成功")

        # 2. 模拟文案阶段
        print("\n2. 模拟文案策划阶段...")
        record_stage_time(project_dir, 'copywriting', 'start', 'ai')

        # 模拟 AI 处理 60 秒
        import time
        time.sleep(1)  # 实际测试中缩短时间

        record_stage_time(project_dir, 'copywriting', 'complete', 'ai')

        # 请求文案审批
        approval_request = request_approval(project_dir, 'copywriting', 'copywriting.json')

        assert 'mention_tag' in approval_request, "应包含艾特标签"
        assert '张三' in approval_request['mention_tag'], "应艾特文案判断者"
        print_result(True, f"文案审批请求成功: {approval_request['message']}")

        # 3. 记录文案审批响应
        print("\n3. 记录文案审批响应...")
        record_stage_time(project_dir, 'copywriting', 'start', 'human')
        time.sleep(1)
        record_stage_time(project_dir, 'copywriting', 'complete', 'human')

        response = record_approval_response(
            project_dir,
            'copywriting',
            'approved',
            '文案符合品牌调性',
            'ou_copywriter_test'
        )

        assert response['decision'] == 'approved', "审批决策应为 approved"
        print_result(True, f"文案审批通过，下一步: {response['next_action']}")

        # 4. 模拟设计阶段
        print("\n4. 模拟设计阶段...")
        record_stage_time(project_dir, 'design', 'start', 'ai')
        time.sleep(1)
        record_stage_time(project_dir, 'design', 'complete', 'ai')

        approval_request = request_approval(project_dir, 'design', 'images/final_poster.png')

        assert '李四' in approval_request['mention_tag'], "应艾特设计判断者"
        print_result(True, f"设计审批请求成功: {approval_request['message']}")

        # 5. 记录设计审批响应
        print("\n5. 记录设计审批响应...")
        record_stage_time(project_dir, 'design', 'start', 'human')
        time.sleep(1)
        record_stage_time(project_dir, 'design', 'complete', 'human')

        response = record_approval_response(
            project_dir,
            'design',
            'approved',
            '设计效果符合预期',
            'ou_designer_test'
        )

        assert response['next_action'] == 'proceed_to_delivery', "B 级项目应直接进入交付"
        print_result(True, f"设计审批通过，下一步: {response['next_action']}")

        # 6. 查看审批状态
        print("\n6. 查看最终审批状态...")
        status = get_approval_status(project_dir)

        assert status['completed_count'] == 2, "应完成 2 个审批节点"
        assert status['pending_count'] == 0, "不应有待审批节点"
        print_result(True, f"审批状态: {status['completed_count']}/{status['total_count']} 完成")

        # 7. 生成时间线报告
        print("\n7. 生成时间线报告...")
        timeline_report = generate_timeline_report(project_dir)

        assert 'total_ai_time_seconds' in timeline_report, "应包含 AI 时间"
        assert 'total_human_time_seconds' in timeline_report, "应包含人工时间"
        print_result(True, f"时间线报告生成成功")
        print(f"   AI 时间: {timeline_report['total_ai_time_seconds']}s")
        print(f"   人工时间: {timeline_report['total_human_time_seconds']}s")

        # 8. 生成复盘报告
        print("\n8. 生成复盘报告...")
        report = generate_retrospective_report(project_dir)

        assert '项目复盘报告' in report, "应包含复盘报告标题"
        assert 'B' in report or '日常项目' in report, "应显示项目等级"
        print_result(True, "复盘报告生成成功")

        # 保存报告到文件
        report_path = project_dir / "test_retrospective.md"
        report_path.write_text(report, encoding='utf-8')
        print(f"   报告已保存: {report_path}")

        return True

    except Exception as e:
        print_result(False, f"B 级项目测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_a_grade_project(test_dir: Path) -> bool:
    """测试 A 级项目完整流程"""
    print_section("测试 A 级项目")

    project_dir = test_dir / "BP-20260613-002"
    project_dir.mkdir(parents=True)

    (project_dir / "brief.json").write_text(json.dumps({
        "task_id": "BP-20260613-002",
        "brand_name": "重要品牌",
        "type": "产品推广"
    }, ensure_ascii=False, indent=2))

    (project_dir / "images").mkdir(exist_ok=True)
    (project_dir / "images/final_poster.png").touch()

    try:
        # 1. 初始化 A 级项目
        print("1. 初始化 A 级项目...")
        reviewers = {
            "copywriter": {"name": "张三", "open_id": "ou_copywriter_test"},
            "designer": {"name": "李四", "open_id": "ou_designer_test"},
            "creative_director": {"name": "王五", "open_id": "ou_director_test"}
        }

        grading_config = init_project_grading(project_dir, 'A', reviewers)

        assert grading_config['grade'] == 'A', "项目等级应为 A"
        assert len(grading_config['approval_flow']) == 3, "A 级项目应有 3 个审批节点"
        print_result(True, "A 级项目初始化成功")

        # 2-3. 文案审批（同 B 级）
        print("\n2. 执行文案审批...")
        record_stage_time(project_dir, 'copywriting', 'start', 'ai')
        import time
        time.sleep(1)
        record_stage_time(project_dir, 'copywriting', 'complete', 'ai')

        request_approval(project_dir, 'copywriting')
        record_stage_time(project_dir, 'copywriting', 'start', 'human')
        time.sleep(1)
        record_stage_time(project_dir, 'copywriting', 'complete', 'human')
        record_approval_response(project_dir, 'copywriting', 'approved', '通过')
        print_result(True, "文案审批通过")

        # 4-5. 设计审批（同 B 级）
        print("\n3. 执行设计审批...")
        record_stage_time(project_dir, 'design', 'start', 'ai')
        time.sleep(1)
        record_stage_time(project_dir, 'design', 'complete', 'ai')

        request_approval(project_dir, 'design')
        record_stage_time(project_dir, 'design', 'start', 'human')
        time.sleep(1)
        record_stage_time(project_dir, 'design', 'complete', 'human')
        record_approval_response(project_dir, 'design', 'approved', '通过')
        print_result(True, "设计审批通过")

        # 6. 创意总监审批（A 级特有）
        print("\n4. 执行创意总监审批...")
        approval_request = request_approval(project_dir, 'creative_direction')

        assert '王五' in approval_request['mention_tag'], "应艾特创意总监"
        print_result(True, f"创意总监审批请求成功: {approval_request['message']}")

        record_stage_time(project_dir, 'creative_direction', 'start', 'human')
        time.sleep(1)
        record_stage_time(project_dir, 'creative_direction', 'complete', 'human')

        response = record_approval_response(
            project_dir,
            'creative_direction',
            'approved',
            '创意方向符合战略',
            'ou_director_test'
        )

        assert response['next_action'] == 'proceed_to_delivery', "A 级项目总监通过后应进入交付"
        print_result(True, f"创意总监审批通过，下一步: {response['next_action']}")

        # 7. 验证最终状态
        print("\n5. 验证最终状态...")
        status = get_approval_status(project_dir)

        assert status['completed_count'] == 3, "应完成 3 个审批节点"
        print_result(True, f"A 级项目审批流程完成: {status['completed_count']}/{status['total_count']}")

        return True

    except Exception as e:
        print_result(False, f"A 级项目测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_s_grade_project(test_dir: Path) -> bool:
    """测试 S 级项目完整流程"""
    print_section("测试 S 级项目")

    project_dir = test_dir / "BP-20260613-003"
    project_dir.mkdir(parents=True)

    (project_dir / "brief.json").write_text(json.dumps({
        "task_id": "BP-20260613-003",
        "brand_name": "战略品牌",
        "type": "品牌发声"
    }, ensure_ascii=False, indent=2))

    (project_dir / "images").mkdir(exist_ok=True)
    (project_dir / "images/final_poster.png").touch()

    try:
        # 1. 初始化 S 级项目
        print("1. 初始化 S 级项目...")
        reviewers = {
            "copywriter": {"name": "张三", "open_id": "ou_copywriter_test"},
            "designer": {"name": "李四", "open_id": "ou_designer_test"},
            "creative_director": {"name": "王五", "open_id": "ou_director_test"},
            "boss": {"name": "赵六", "open_id": "ou_boss_test"}
        }

        grading_config = init_project_grading(project_dir, 'S', reviewers)

        assert grading_config['grade'] == 'S', "项目等级应为 S"
        assert len(grading_config['approval_flow']) == 4, "S 级项目应有 4 个审批节点"
        print_result(True, "S 级项目初始化成功")

        # 2-5. 文案、设计、创意总监审批
        print("\n2. 执行前三轮审批...")
        import time

        for milestone in ['copywriting', 'design', 'creative_direction']:
            record_stage_time(project_dir, milestone, 'start', 'ai')
            time.sleep(1)
            record_stage_time(project_dir, milestone, 'complete', 'ai')
            request_approval(project_dir, milestone)
            record_stage_time(project_dir, milestone, 'start', 'human')
            time.sleep(1)
            record_stage_time(project_dir, milestone, 'complete', 'human')
            record_approval_response(project_dir, milestone, 'approved', '通过')

        print_result(True, "前三轮审批全部通过")

        # 6. 老板最终审批（S 级特有）
        print("\n3. 执行老板最终审批...")
        approval_request = request_approval(project_dir, 'final_approval')

        assert '赵六' in approval_request['mention_tag'], "应艾特老板"
        print_result(True, f"老板审批请求成功: {approval_request['message']}")

        record_stage_time(project_dir, 'final_approval', 'start', 'human')
        time.sleep(1)
        record_stage_time(project_dir, 'final_approval', 'complete', 'human')

        response = record_approval_response(
            project_dir,
            'final_approval',
            'approved',
            '符合战略目标，批准上线',
            'ou_boss_test'
        )

        assert response['next_action'] == 'proceed_to_delivery', "S 级项目老板通过后应进入交付"
        print_result(True, f"老板最终审批通过，下一步: {response['next_action']}")

        # 7. 验证最终状态
        print("\n4. 验证最终状态...")
        status = get_approval_status(project_dir)

        assert status['completed_count'] == 4, "应完成 4 个审批节点"
        print_result(True, f"S 级项目审批流程完成: {status['completed_count']}/{status['total_count']}")

        return True

    except Exception as e:
        print_result(False, f"S 级项目测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_timeout_handling(test_dir: Path) -> bool:
    """测试超时处理逻辑"""
    print_section("测试超时处理")

    project_dir = test_dir / "BP-20260613-004"
    project_dir.mkdir(parents=True)

    (project_dir / "brief.json").write_text(json.dumps({
        "task_id": "BP-20260613-004",
        "brand_name": "测试品牌",
        "type": "节日海报"
    }, ensure_ascii=False, indent=2))

    try:
        # 1. 初始化项目
        print("1. 初始化 B 级项目...")
        reviewers = {
            "copywriter": {"name": "张三", "open_id": "ou_copywriter_test"},
            "designer": {"name": "李四", "open_id": "ou_designer_test"}
        }

        init_project_grading(project_dir, 'B', reviewers)
        print_result(True, "项目初始化成功")

        # 2. 请求审批但不响应（模拟超时）
        print("\n2. 请求审批（模拟超时场景）...")
        request_approval(project_dir, 'copywriting')
        print_result(True, "审批请求已发送")

        # 3. 手动修改超时时间为已过期（用于测试）
        grading_file = project_dir / 'project_grading.json'
        grading_config = json.loads(grading_file.read_text())
        grading_config['approval_flow'][0]['timeout_at'] = '2020-01-01T00:00:00Z'
        grading_file.write_text(json.dumps(grading_config, ensure_ascii=False, indent=2))

        # 4. 检查超时
        print("\n3. 检查超时...")
        timeout_steps = check_timeout(project_dir)

        assert len(timeout_steps) > 0, "应检测到超时"
        print_result(True, f"检测到 {len(timeout_steps)} 个超时节点")

        # 5. B 级项目自动通过
        print("\n4. B 级项目超时自动通过...")
        result = handle_timeout(project_dir, 'copywriting', 'auto_approve')

        assert result['approved'] == True, "应自动通过"
        print_result(True, f"超时处理成功: {result['message']}")

        return True

    except Exception as e:
        print_result(False, f"超时处理测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print_section("品牌海报审批流程完整测试")
    print(f"测试开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # 创建临时测试目录
    test_dir = Path(tempfile.mkdtemp(prefix="brand_poster_test_"))
    print(f"测试目录: {test_dir}\n")

    results = {}

    try:
        # 运行所有测试
        results['B级项目'] = test_b_grade_project(test_dir)
        results['A级项目'] = test_a_grade_project(test_dir)
        results['S级项目'] = test_s_grade_project(test_dir)
        results['超时处理'] = test_timeout_handling(test_dir)

        # 打印测试总结
        print_section("测试总结")

        passed = sum(1 for v in results.values() if v)
        total = len(results)

        for test_name, result in results.items():
            status = "✅ 通过" if result else "❌ 失败"
            print(f"{status}: {test_name}")

        print(f"\n总计: {passed}/{total} 测试通过")

        if passed == total:
            print("\n🎉 所有测试通过！审批流程功能正常。")
            return 0
        else:
            print(f"\n⚠️  {total - passed} 个测试失败，请检查错误信息。")
            return 1

    finally:
        # 清理测试目录（可选）
        # shutil.rmtree(test_dir)
        print(f"\n测试文件保留在: {test_dir}")
        print("如需清理，请手动删除该目录")


if __name__ == '__main__':
    sys.exit(main())
