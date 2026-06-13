#!/usr/bin/env python3
"""测试双审批流程和AI驱动者权限"""
import json
import tempfile
from pathlib import Path
import sys

# 添加脚本目录到路径
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from project_grading import init_project_grading, request_approval, record_approval_response


def test_creative_direction_dual():
    """测试创意方向双审"""
    print("\n" + "="*60)
    print("测试1：创意方向双审批流程")
    print("="*60)

    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)

        # 初始化项目分级
        reviewers = {
            'ai_driver': {'name': '涂是淦', 'open_id': 'ou_driver'},
            'copywriter': {'name': '肖宁劼', 'open_id': 'ou_copy'},
            'designer': {'name': '林育丰', 'open_id': 'ou_design'}
        }

        print("\n1. 初始化 B 级项目...")
        config = init_project_grading(project_dir, 'B', reviewers)
        print("✓ 初始化成功")
        print(f"  - 项目等级: {config['grade']}")
        print(f"  - AI驱动者: {config['reviewers']['ai_driver']['name']}")
        print(f"  - 审批流程数: {len(config['approval_flow'])}")

        # 查找 creative_direction_dual 节点
        cd_dual = None
        for step in config['approval_flow']:
            if step['milestone'] == 'creative_direction_dual':
                cd_dual = step
                break

        assert cd_dual is not None, "未找到 creative_direction_dual 节点"
        print(f"  - 找到创意方向双审节点: {cd_dual['title']}")
        print(f"  - 审批模式: {cd_dual['approval_mode']}")
        print(f"  - 审批者角色: {cd_dual['reviewer_roles']}")

        # 请求创意方向审批
        print("\n2. 请求创意方向审批...")
        approval_req = request_approval(project_dir, 'creative_direction_dual', 'creative_direction.json')
        print("✓ 请求审批成功")
        print(f"  - 审批标题: {approval_req['title']}")
        print(f"  - 审批者数量: {len(approval_req['reviewers'])}")
        print(f"  - 艾特标签数量: {len(approval_req['mention_tags'])}")
        print(f"  - 艾特消息: {approval_req['message']}")
        print(f"  - 说明: {approval_req['note']}")

        # 测试：文案判断者确认
        print("\n3. 文案判断者确认...")
        result1 = record_approval_response(
            project_dir,
            'creative_direction_dual',
            'approved',
            '文案表达准确',
            'ou_copy'
        )
        print("✓ 文案判断者确认成功")
        print(f"  - 决策: {result1['decision']}")
        print(f"  - 状态: {result1['status']}")
        print(f"  - 确认状态: {json.dumps(result1['confirmations'], ensure_ascii=False, indent=4)}")
        assert result1['status'] == 'waiting', "应该还在等待设计判断者"

        # 测试：设计判断者确认
        print("\n4. 设计判断者确认...")
        result2 = record_approval_response(
            project_dir,
            'creative_direction_dual',
            'approved',
            '视觉呈现可行',
            'ou_design'
        )
        print("✓ 设计判断者确认成功")
        print(f"  - 决策: {result2['decision']}")
        print(f"  - 状态: {result2['status']}")
        print(f"  - 确认状态: {json.dumps(result2['confirmations'], ensure_ascii=False, indent=4)}")
        assert result2['status'] == 'completed', "应该全部通过"
        assert result2['decision'] == 'approved', "最终决策应该是 approved"

        print("\n✅ 测试1通过：双审批者都确认后才能通过")


def test_ai_driver_override():
    """测试 AI 驱动者覆盖权限"""
    print("\n" + "="*60)
    print("测试2：AI驱动者覆盖权限")
    print("="*60)

    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)

        reviewers = {
            'ai_driver': {'name': '涂是淦', 'open_id': 'ou_driver'},
            'copywriter': {'name': '肖宁劼', 'open_id': 'ou_copy'},
            'designer': {'name': '林育丰', 'open_id': 'ou_design'}
        }

        print("\n1. 初始化项目并请求审批...")
        init_project_grading(project_dir, 'B', reviewers)
        request_approval(project_dir, 'creative_direction_dual', 'creative_direction.json')

        # AI 驱动者直接确认（跳过双审）
        print("\n2. AI驱动者直接确认...")
        result = record_approval_response(
            project_dir,
            'creative_direction_dual',
            'approved',
            'AI驱动者线下已确认',
            'ou_driver'
        )
        print("✓ AI驱动者确认成功")
        print(f"  - 决策: {result['decision']}")
        print(f"  - 状态: {result['status']}")
        print(f"  - 响应者: {result['responder']}")
        assert result['status'] == 'completed', "AI驱动者应该能直接通过"
        assert result['responder'] == 'ai_driver', "响应者应该是 ai_driver"

        print("\n✅ 测试2通过：AI驱动者拥有最高决策权")


def test_single_approval_with_ai_driver():
    """测试单审批者节点的 AI 驱动者权限"""
    print("\n" + "="*60)
    print("测试3：单审批者节点的AI驱动者权限")
    print("="*60)

    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)

        reviewers = {
            'ai_driver': {'name': '涂是淦', 'open_id': 'ou_driver'},
            'copywriter': {'name': '肖宁劼', 'open_id': 'ou_copy'},
            'designer': {'name': '林育丰', 'open_id': 'ou_design'}
        }

        print("\n1. 初始化项目...")
        init_project_grading(project_dir, 'B', reviewers)

        # 请求文案审批
        print("\n2. 请求文案审批...")
        approval_req = request_approval(project_dir, 'copywriting', 'copywriting.json')
        print("✓ 请求成功")
        print(f"  - 艾特标签: {approval_req['mention_tags']}")
        assert len(approval_req['mention_tags']) == 2, "应该艾特文案判断者和AI驱动者"

        # AI 驱动者代替文案判断者确认
        print("\n3. AI驱动者代替文案判断者确认...")
        result = record_approval_response(
            project_dir,
            'copywriting',
            'approved',
            'AI驱动者确认',
            'ou_driver'
        )
        print("✓ 确认成功")
        print(f"  - 响应者: {result['responder']}")
        print(f"  - 状态: {result['status']}")
        assert result['responder'] == 'ai_driver', "响应者应该是 ai_driver"
        assert result['status'] == 'completed', "应该完成"

        print("\n✅ 测试3通过：AI驱动者可以代替任何审批者")


def test_missing_ai_driver():
    """测试缺少 AI 驱动者的错误处理"""
    print("\n" + "="*60)
    print("测试4：缺少AI驱动者的错误处理")
    print("="*60)

    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)

        # 故意不提供 ai_driver
        reviewers = {
            'copywriter': {'name': '肖宁劼', 'open_id': 'ou_copy'},
            'designer': {'name': '林育丰', 'open_id': 'ou_design'}
        }

        print("\n1. 尝试初始化项目（缺少 ai_driver）...")
        try:
            init_project_grading(project_dir, 'B', reviewers)
            print("❌ 应该抛出异常")
            assert False, "应该抛出 ValueError"
        except ValueError as e:
            print(f"✓ 正确抛出异常: {e}")
            assert "ai_driver" in str(e), "异常信息应该提到 ai_driver"

        print("\n✅ 测试4通过：缺少AI驱动者会被检测")


if __name__ == '__main__':
    print("\n" + "🧪 开始测试 brand-poster-creator 审批流程优化")
    print("="*60)

    try:
        test_creative_direction_dual()
        test_ai_driver_override()
        test_single_approval_with_ai_driver()
        test_missing_ai_driver()

        print("\n" + "="*60)
        print("🎉 所有测试通过！")
        print("="*60)
        print("\n总结：")
        print("  ✅ 创意方向双审流程正常")
        print("  ✅ AI驱动者覆盖权限正常")
        print("  ✅ 单审批者节点AI驱动者权限正常")
        print("  ✅ 缺少AI驱动者会被检测")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
