#!/usr/bin/env python3
"""测试约束优化功能"""

import sys
from pathlib import Path

# 直接定义测试函数（复制自 workflow.py）
def enhance_constraint_expression(forbidden_list: list[str]) -> dict[str, list[str]]:
    """将负向约束改写为更有效的表达"""
    enhanced = {
        'positive_alternative': [],
        'strong_negative': [],
        'contrast': []
    }

    for constraint in forbidden_list:
        constraint_lower = constraint.lower()

        if '翅膀' in constraint or 'wing' in constraint_lower:
            enhanced['positive_alternative'].append(
                "身体两侧是主体造型的侧面轮廓，不是独立肢体"
            )
            enhanced['strong_negative'].append(
                "严禁添加任何翅膀、翼状结构或类似飞行器官"
            )
            enhanced['contrast'].append(
                "不是：普通动物 + 翅膀；而是：特定造型的完整体块"
            )

        elif '手' in constraint or 'hand' in constraint_lower or 'arm' in constraint_lower:
            enhanced['positive_alternative'].append(
                "只有脚部作为肢体，身体是完整造型体块"
            )
            enhanced['strong_negative'].append(
                "严禁添加任何手臂、手掌、手指或上肢结构"
            )
            enhanced['contrast'].append(
                "不是：身体 + 手臂；而是：造型本身就是完整体"
            )

        elif '尾巴' in constraint or 'tail' in constraint_lower:
            enhanced['strong_negative'].append(
                constraint.replace('禁止', '严禁').replace('不能', '绝对不能')
            )

        else:
            enhanced['strong_negative'].append(
                constraint.replace('禁止', '严禁').replace('不能', '绝对不能')
            )

    return enhanced


def build_constraint_header(identity_structure: list[str], identity_forbidden: list[str]) -> str:
    """构建约束头部"""
    if not identity_forbidden and not identity_structure:
        return ""

    header_parts = []

    if identity_forbidden:
        enhanced = enhance_constraint_expression(identity_forbidden)

        header_parts.append("**关键约束（最高优先级）**：")

        if enhanced['positive_alternative']:
            header_parts.append("正确理解：")
            for item in enhanced['positive_alternative']:
                header_parts.append(f"- {item}")

        if enhanced['strong_negative']:
            header_parts.append("严格禁止：")
            for item in enhanced['strong_negative']:
                header_parts.append(f"- {item}")

        if enhanced['contrast']:
            header_parts.append("对比说明：")
            for item in enhanced['contrast']:
                header_parts.append(f"- {item}")

    if identity_structure:
        if header_parts:
            header_parts.append("")
        header_parts.append("**结构真相**：")
        for item in identity_structure:
            header_parts.append(f"- {item}")

    if header_parts:
        header_parts.append("")

    return "\n".join(header_parts)


def generate_constraint_checklist(identity_structure: list[str], identity_forbidden: list[str]) -> list[str]:
    """根据约束生成具体的检查清单"""
    checklist = []

    if identity_forbidden:
        checklist.append("### 2. IP 约束检查（最重要）")
        checklist.append("")
        checklist.append("**⚠️ 关键**：如果参考图违反了约束，后续视频必然违反约束！")
        checklist.append("")
        checklist.append("**禁止变形检查**（以下特征应该全部没有出现）：")

        for constraint in identity_forbidden:
            constraint_lower = constraint.lower()

            if '翅膀' in constraint or 'wing' in constraint_lower:
                checklist.extend([
                    f"- [ ] ❌ 身份板中角色两侧是否出现了翅膀状结构？（约束：{constraint}）",
                    f"- [ ] ❌ 故事板每一格中角色是否保持了无翅膀状态？",
                    f"- [ ] ❌ 侧面视角时是否错误地出现了翅膀轮廓？"
                ])

            elif '手' in constraint or 'hand' in constraint_lower or 'arm' in constraint_lower:
                checklist.extend([
                    f"- [ ] ❌ 身份板中是否出现了手臂、手掌或手指？（约束：{constraint}）",
                    f"- [ ] ❌ 故事板中角色的肢体是否只有脚部？"
                ])

            elif '尾巴' in constraint or 'tail' in constraint_lower:
                checklist.extend([
                    f"- [ ] ❌ 是否在不应该出现尾巴的视角出现了尾巴？（约束：{constraint}）"
                ])

            else:
                checklist.append(f"- [ ] ❌ 是否违反了约束：{constraint}？")

        checklist.extend([
            "",
            "**如果发现违反约束，必须重新生成对应参考图！**",
            ""
        ])

    if identity_structure:
        checklist.append("### 3. 结构真相检查")
        checklist.append("")
        for item in identity_structure:
            checklist.append(f"- [ ] ✅ {item}")
        checklist.append("")

    return checklist


def test_enhance_constraint_expression():
    """测试约束表达优化"""
    print("=" * 60)
    print("测试 1: 约束表达优化")
    print("=" * 60)

    forbidden_list = [
        "禁止长出额外翅膀",
        "禁止长出手臂、手掌或手指",
        "禁止侧面错误露出尾巴"
    ]

    enhanced = enhance_constraint_expression(forbidden_list)

    print("\n原始约束:")
    for item in forbidden_list:
        print(f"  - {item}")

    print("\n优化后:")
    if enhanced['positive_alternative']:
        print("\n正向替代描述:")
        for item in enhanced['positive_alternative']:
            print(f"  - {item}")

    if enhanced['strong_negative']:
        print("\n强化负向:")
        for item in enhanced['strong_negative']:
            print(f"  - {item}")

    if enhanced['contrast']:
        print("\n对比说明:")
        for item in enhanced['contrast']:
            print(f"  - {item}")


def test_build_constraint_header():
    """测试约束头部生成"""
    print("\n" + "=" * 60)
    print("测试 2: 约束头部生成")
    print("=" * 60)

    identity_structure = [
        "整体必须读成点赞大拇指体块",
        "只有脚部，没有其他肢体"
    ]

    identity_forbidden = [
        "禁止长出额外翅膀",
        "禁止长出手臂、手掌或手指"
    ]

    header = build_constraint_header(identity_structure, identity_forbidden)

    print("\n生成的约束头部:")
    print("-" * 60)
    print(header)
    print("-" * 60)


def test_generate_constraint_checklist():
    """测试检查清单生成"""
    print("\n" + "=" * 60)
    print("测试 3: 检查清单生成")
    print("=" * 60)

    identity_structure = [
        "整体必须读成点赞大拇指体块",
        "只有脚部，没有其他肢体"
    ]

    identity_forbidden = [
        "禁止长出额外翅膀",
        "禁止长出手臂、手掌或手指",
        "禁止侧面错误露出尾巴"
    ]

    checklist = generate_constraint_checklist(identity_structure, identity_forbidden)

    print("\n生成的检查清单:")
    print("-" * 60)
    for line in checklist:
        print(line)
    print("-" * 60)


if __name__ == "__main__":
    test_enhance_constraint_expression()
    test_build_constraint_header()
    test_generate_constraint_checklist()

    print("\n" + "=" * 60)
    print("✅ 所有测试完成")
    print("=" * 60)
