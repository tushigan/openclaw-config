#!/usr/bin/env python3
"""
Workspace path utilities for brand-poster-creator skill.

Provides dynamic workspace detection to support multi-agent scenarios where
different agents (main, design, design-shared) work in different workspace directories.

This module solves the cross-workspace path confusion issue where hardcoded paths
caused design-shared agent to send wrong files from workspace instead of workspace-design.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional


def detect_workspace_from_project(project_dir: Path) -> str:
    """
    从项目目录路径推断 workspace 名称。

    Args:
        project_dir: 项目目录路径，例如：
            /Users/a123/.openclaw/workspace/brand-poster-projects/BP-20260610-001
            /Users/a123/.openclaw/workspace-design/brand-poster-projects/BP-20260610-001

    Returns:
        workspace 名称，例如 'workspace' 或 'workspace-design'
        如果无法推断，返回默认值 'workspace'

    Examples:
        >>> detect_workspace_from_project(Path('/Users/a123/.openclaw/workspace/brand-poster-projects/BP-001'))
        'workspace'
        >>> detect_workspace_from_project(Path('/Users/a123/.openclaw/workspace-design/brand-poster-projects/BP-001'))
        'workspace-design'
    """
    try:
        resolved = project_dir.resolve()
        parts = resolved.parts

        # 查找 brand-poster-projects 在路径中的位置
        for i, part in enumerate(parts):
            if part == 'brand-poster-projects' and i > 0:
                # 获取前一个部分，应该是 workspace 或 workspace-*
                prev = parts[i - 1]
                if prev.startswith('workspace'):
                    return prev

        # 如果找不到 brand-poster-projects，尝试查找任何 workspace* 目录
        for part in parts:
            if part.startswith('workspace'):
                return part

    except Exception:
        pass

    # 默认返回 workspace
    return 'workspace'


def get_workspace_root(workspace: Optional[str] = None) -> Path:
    """
    获取指定 workspace 的根目录。

    Args:
        workspace: workspace 名称，如 'workspace' 或 'workspace-design'
                  如果为 None，从环境变量 OPENCLAW_WORKSPACE 读取，默认 'workspace'

    Returns:
        workspace 根目录路径

    Examples:
        >>> get_workspace_root('workspace')
        Path('/Users/a123/.openclaw/workspace')
        >>> get_workspace_root('workspace-design')
        Path('/Users/a123/.openclaw/workspace-design')
    """
    if workspace is None:
        workspace = os.environ.get('OPENCLAW_WORKSPACE', 'workspace')

    return Path(f'/Users/a123/.openclaw/{workspace}')


def get_projects_root(workspace: Optional[str] = None) -> Path:
    """
    获取品牌海报项目根目录。

    Args:
        workspace: workspace 名称，如果为 None 则使用默认值

    Returns:
        项目根目录路径，例如：
        /Users/a123/.openclaw/workspace/brand-poster-projects
        /Users/a123/.openclaw/workspace-design/brand-poster-projects

    Examples:
        >>> get_projects_root('workspace')
        Path('/Users/a123/.openclaw/workspace/brand-poster-projects')
        >>> get_projects_root('workspace-design')
        Path('/Users/a123/.openclaw/workspace-design/brand-poster-projects')
    """
    return get_workspace_root(workspace) / 'brand-poster-projects'


def get_delivery_dir(workspace: Optional[str] = None) -> Path:
    """
    获取飞书交付目录。

    Args:
        workspace: workspace 名称，如果为 None 则使用默认值

    Returns:
        交付目录路径，例如：
        /Users/a123/.openclaw/workspace/feishu-deliver
        /Users/a123/.openclaw/workspace-design/feishu-deliver

    Examples:
        >>> get_delivery_dir('workspace')
        Path('/Users/a123/.openclaw/workspace/feishu-deliver')
        >>> get_delivery_dir('workspace-design')
        Path('/Users/a123/.openclaw/workspace-design/feishu-deliver')
    """
    return get_workspace_root(workspace) / 'feishu-deliver'


def get_skills_root(workspace: Optional[str] = None) -> Path:
    """
    获取 skills 目录。

    Args:
        workspace: workspace 名称，如果为 None 则使用默认值

    Returns:
        skills 目录路径
    """
    return get_workspace_root(workspace) / 'skills'


def infer_workspace_from_project_dir(project_dir: Path) -> tuple[str, Path, Path]:
    """
    从项目目录推断 workspace 并返回相关路径。

    Args:
        project_dir: 项目目录路径

    Returns:
        元组 (workspace_name, projects_root, delivery_dir)

    Examples:
        >>> workspace, projects_root, delivery_dir = infer_workspace_from_project_dir(
        ...     Path('/Users/a123/.openclaw/workspace-design/brand-poster-projects/BP-001')
        ... )
        >>> workspace
        'workspace-design'
        >>> projects_root
        Path('/Users/a123/.openclaw/workspace-design/brand-poster-projects')
        >>> delivery_dir
        Path('/Users/a123/.openclaw/workspace-design/feishu-deliver')
    """
    workspace = detect_workspace_from_project(project_dir)
    projects_root = get_projects_root(workspace)
    delivery_dir = get_delivery_dir(workspace)

    return workspace, projects_root, delivery_dir


def get_distiller_root(workspace: Optional[str] = None) -> Path:
    """
    获取 brand-poster-distiller skill 根目录。

    Args:
        workspace: workspace 名称，如果为 None 则使用默认值

    Returns:
        distiller 根目录路径
    """
    return get_skills_root(workspace) / 'brand-poster-distiller'


def get_distiller_cards_dir(workspace: Optional[str] = None) -> Path:
    """
    获取蒸馏卡存储目录。

    Args:
        workspace: workspace 名称，如果为 None 则使用默认值

    Returns:
        蒸馏卡目录路径
    """
    return get_distiller_root(workspace) / 'cards'


# 向后兼容：保留默认常量供不需要动态检测的场景使用
DEFAULT_WORKSPACE = 'workspace'
DEFAULT_PROJECTS_ROOT = get_projects_root(DEFAULT_WORKSPACE)
DEFAULT_DELIVERY_DIR = get_delivery_dir(DEFAULT_WORKSPACE)
DEFAULT_DISTILLER_ROOT = get_distiller_root(DEFAULT_WORKSPACE)
DEFAULT_DISTILLER_CARDS_DIR = get_distiller_cards_dir(DEFAULT_WORKSPACE)


if __name__ == '__main__':
    # 简单的自测
    import sys

    test_cases = [
        Path('/Users/a123/.openclaw/workspace/brand-poster-projects/BP-20260610-001'),
        Path('/Users/a123/.openclaw/workspace-design/brand-poster-projects/BP-20260610-001'),
        Path('/Users/a123/.openclaw/workspace-strategy/brand-poster-projects/BP-001'),
    ]

    print("=== Workspace Detection Tests ===")
    for test_path in test_cases:
        workspace = detect_workspace_from_project(test_path)
        projects_root = get_projects_root(workspace)
        delivery_dir = get_delivery_dir(workspace)

        print(f"\nInput: {test_path}")
        print(f"  Workspace: {workspace}")
        print(f"  Projects Root: {projects_root}")
        print(f"  Delivery Dir: {delivery_dir}")

    # 验证基本功能
    assert detect_workspace_from_project(test_cases[0]) == 'workspace'
    assert detect_workspace_from_project(test_cases[1]) == 'workspace-design'
    assert detect_workspace_from_project(test_cases[2]) == 'workspace-strategy'

    print("\n✅ All tests passed!")
    sys.exit(0)
