#!/usr/bin/env python3
"""
测试精简版提示词是否能解决 ProxyError 问题
"""

def build_compact_constraint_header(identity_structure: list[str], identity_forbidden: list[str]) -> str:
    """构建精简版约束头部"""
    if not identity_forbidden and not identity_structure:
        return ""

    parts = []

    if identity_forbidden:
        parts.append("**核心约束**：")
        # 合并所有禁止项为一行
        forbidden_text = "；".join(identity_forbidden)
        parts.append(f"严禁：{forbidden_text}")

    if identity_structure:
        parts.append("")
        # 合并结构真相为一段
        structure_text = "；".join(identity_structure)
        parts.append(f"**结构**：{structure_text}")

    if parts:
        parts.append("")

    return "\n".join(parts)


def build_compact_storyboard_prompt(brief: dict) -> str:
    """构建精简版故事板提示词"""

    # 精简版约束头部
    constraint_header = build_compact_constraint_header(
        brief.get("identity_structure", []),
        brief.get("identity_forbidden", [])
    )

    subject = brief["subject"]
    action = brief["action"]
    scene = brief["scene"]
    ratio = brief["ratio"]
    panel_count = brief["storyboard_panel_count"]
    anchor_text = "、".join(brief["anchor_elements"]) if brief["anchor_elements"] else "保留空间地标"

    # 关键帧简化
    beats = brief.get("storyboard_beats", [])
    beats_text = "\n".join([f"{i+1}. {b['description']}" for i, b in enumerate(beats)])

    # 精简版提示词
    prompt = f"""{constraint_header}故事板：{panel_count}格黑白分镜，{ratio}画幅
主体：{subject}
行为：{action}
场景：{scene}
锚点：{anchor_text}

要求：
1. {panel_count}格独立{ratio}画幅，带文字标注和箭头
2. 连续空间，保持角色一致
3. 关键帧：
{beats_text}
""".strip()

    return prompt


# 测试用例
if __name__ == "__main__":
    # 模拟当前的 brief 数据
    test_brief = {
        "subject": "黄小咕 IP，一只黄色鸡，整体外轮廓为拇指体块鸡形吉祥物的拟物角色",
        "action": "前 3 秒环境建立与镜头缓推，第 3 秒主体从画外欢快走入，后段在定版海报场景中站定，最后 2 秒文字与版式元素逐步出现，形成品牌收尾",
        "scene": "霜降节气海报世界：高山远景、晨光日出、红枫林、带霜前景岩石，空气通透，活泼元气而有秋日诗意",
        "ratio": "9:16",
        "storyboard_panel_count": 6,
        "anchor_elements": ["高山远景", "红枫林", "带霜岩石"],
        "identity_structure": [
            "整体外轮廓必须是拇指体块与黄色小鸡融合的一体化造型",
            "正面和背面视角都应看到尾巴呈现",
            "侧面视角可以看不到尾巴，这是正常结构",
            "角色没有手，也没有额外翅膀，只有脚",
            "鸡冠、黄色主体、橙色嘴和橙色脚必须稳定保留",
            "角色要保持圆润、玩具感、可爱且有品牌吉祥物完成度"
        ],
        "identity_forbidden": [
            "禁止长出手臂、手掌、人类手指",
            "禁止长出额外翅膀或常规鸡翅",
            "禁止把角色变成普通圆鸡而失去拇指体块轮廓",
            "禁止正面或背面视角尾巴消失",
            "禁止脸部五官漂移、比例突变、材质突变",
            "禁止写实动物羽毛质感，保持干净 3D 吉祥物质感"
        ],
        "storyboard_beats": [
            {"description": "建立空间：霜降节气海报世界"},
            {"description": "动作推进：前 3 秒环境建立与镜头缓推"},
            {"description": "动作推进：第 3 秒主体从画外欢快走入"},
            {"description": "收束定格：后段在定版海报场景中站定"},
            {"description": "动作推进：2 秒文字与版式元素逐步出现"},
            {"description": "收束定格：形成品牌收尾"}
        ]
    }

    # 生成原版提示词（模拟）
    print("=" * 80)
    print("原版提示词大小估算：~6500 字节")
    print("=" * 80)
    print()

    # 生成精简版提示词
    compact_prompt = build_compact_storyboard_prompt(test_brief)

    print("=" * 80)
    print("精简版提示词")
    print("=" * 80)
    print(compact_prompt)
    print()
    print("=" * 80)
    print(f"精简版大小：{len(compact_prompt.encode('utf-8'))} 字节")
    print(f"压缩率：{(1 - len(compact_prompt.encode('utf-8')) / 6500) * 100:.1f}%")
    print("=" * 80)
