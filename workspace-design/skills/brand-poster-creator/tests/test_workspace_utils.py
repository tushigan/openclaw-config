#!/usr/bin/env python3
"""
单元测试：workspace_utils 模块

验证跨 workspace 路径检测和解析功能
"""
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent.parent / 'scripts'
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from workspace_utils import (
    detect_workspace_from_project,
    get_projects_root,
    get_delivery_dir,
    get_distiller_root,
    get_distiller_cards_dir,
    infer_workspace_from_project_dir,
)


def test_detect_workspace():
    """测试 workspace 检测"""
    test_cases = [
        (
            Path('/Users/a123/.openclaw/workspace/brand-poster-projects/BP-20260610-001'),
            'workspace'
        ),
        (
            Path('/Users/a123/.openclaw/workspace-design/brand-poster-projects/BP-20260610-001'),
            'workspace-design'
        ),
        (
            Path('/Users/a123/.openclaw/workspace-strategy/brand-poster-projects/BP-001'),
            'workspace-strategy'
        ),
        (
            Path('/Users/a123/.openclaw/workspace-research/brand-poster-projects/BP-001'),
            'workspace-research'
        ),
    ]

    for project_path, expected_workspace in test_cases:
        result = detect_workspace_from_project(project_path)
        assert result == expected_workspace, \
            f"Expected {expected_workspace}, got {result} for {project_path}"
        print(f"✅ {project_path.parts[-3]} → {result}")


def test_get_projects_root():
    """测试项目根目录获取"""
    test_cases = [
        ('workspace', Path('/Users/a123/.openclaw/workspace/brand-poster-projects')),
        ('workspace-design', Path('/Users/a123/.openclaw/workspace-design/brand-poster-projects')),
    ]

    for workspace, expected_path in test_cases:
        result = get_projects_root(workspace)
        assert result == expected_path, \
            f"Expected {expected_path}, got {result} for workspace={workspace}"
        print(f"✅ {workspace} → {result}")


def test_get_delivery_dir():
    """测试交付目录获取"""
    test_cases = [
        ('workspace', Path('/Users/a123/.openclaw/workspace/feishu-deliver')),
        ('workspace-design', Path('/Users/a123/.openclaw/workspace-design/feishu-deliver')),
    ]

    for workspace, expected_path in test_cases:
        result = get_delivery_dir(workspace)
        assert result == expected_path, \
            f"Expected {expected_path}, got {result} for workspace={workspace}"
        print(f"✅ {workspace} → {result}")


def test_get_distiller_root():
    """测试蒸馏卡根目录获取"""
    test_cases = [
        ('workspace', Path('/Users/a123/.openclaw/workspace/skills/brand-poster-distiller')),
        ('workspace-design', Path('/Users/a123/.openclaw/workspace-design/skills/brand-poster-distiller')),
    ]

    for workspace, expected_path in test_cases:
        result = get_distiller_root(workspace)
        assert result == expected_path, \
            f"Expected {expected_path}, got {result} for workspace={workspace}"
        print(f"✅ {workspace} → {result}")


def test_infer_workspace_from_project_dir():
    """测试从项目目录推断完整路径"""
    project_dir = Path('/Users/a123/.openclaw/workspace-design/brand-poster-projects/BP-20260610-001')
    workspace, projects_root, delivery_dir = infer_workspace_from_project_dir(project_dir)

    assert workspace == 'workspace-design'
    assert projects_root == Path('/Users/a123/.openclaw/workspace-design/brand-poster-projects')
    assert delivery_dir == Path('/Users/a123/.openclaw/workspace-design/feishu-deliver')

    print(f"✅ 推断结果：")
    print(f"  workspace: {workspace}")
    print(f"  projects_root: {projects_root}")
    print(f"  delivery_dir: {delivery_dir}")


def test_real_case():
    """测试真实问题案例"""
    # 这是导致问题的真实场景：
    # design-shared agent 在 workspace-design 生成海报
    # 但旧代码硬编码 workspace 路径，导致发送错误文件

    project_dir = Path('/Users/a123/.openclaw/workspace-design/brand-poster-projects/BP-20260610-001-V01')
    workspace, projects_root, delivery_dir = infer_workspace_from_project_dir(project_dir)

    print(f"\n✅ 真实案例测试：")
    print(f"  项目目录: {project_dir}")
    print(f"  检测到的 workspace: {workspace}")
    print(f"  应该使用的交付目录: {delivery_dir}")
    print(f"  ❌ 旧代码会错误使用: /Users/a123/.openclaw/workspace/feishu-deliver")
    print(f"  ✅ 新代码正确使用: {delivery_dir}")

    # 验证修复后的行为
    assert workspace == 'workspace-design', "应该检测到 workspace-design"
    assert delivery_dir == Path('/Users/a123/.openclaw/workspace-design/feishu-deliver'), \
        "应该使用 workspace-design 的交付目录"


if __name__ == '__main__':
    print("=" * 60)
    print("开始测试 workspace_utils 模块")
    print("=" * 60)

    print("\n1. 测试 workspace 检测")
    test_detect_workspace()

    print("\n2. 测试项目根目录获取")
    test_get_projects_root()

    print("\n3. 测试交付目录获取")
    test_get_delivery_dir()

    print("\n4. 测试蒸馏卡根目录获取")
    test_get_distiller_root()

    print("\n5. 测试从项目目录推断完整路径")
    test_infer_workspace_from_project_dir()

    print("\n6. 测试真实问题案例")
    test_real_case()

    print("\n" + "=" * 60)
    print("✅ 所有测试通过！")
    print("=" * 60)
