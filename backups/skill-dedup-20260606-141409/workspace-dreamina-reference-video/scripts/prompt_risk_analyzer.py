#!/usr/bin/env python3
"""Prompt 风险分析器：检测 prompt 中的潜在风险并提供改写建议"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class PromptRisk:
    """Prompt 风险"""
    risk_type: str  # action_body_confusion, conceptual_description, excessive_negation, conflict_constraint
    severity: str  # high, medium, low
    location: str  # 风险位置描述
    original_text: str
    reason: str
    suggestion: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "risk_type": self.risk_type,
            "severity": self.severity,
            "location": self.location,
            "original_text": self.original_text,
            "reason": self.reason,
            "suggestion": self.suggestion,
        }


@dataclass
class PromptRiskReport:
    """Prompt 风险报告"""
    prompt_name: str
    risks: list[PromptRisk] = field(default_factory=list)
    rewrite_suggestions: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "prompt_name": self.prompt_name,
            "risks": [risk.to_dict() for risk in self.risks],
            "rewrite_suggestions": self.rewrite_suggestions,
        }

    def add_risk(self, risk: PromptRisk) -> None:
        """添加风险"""
        self.risks.append(risk)


class PromptRiskAnalyzer:
    """Prompt 风险分析器"""

    # 动作词 + 身体部位的危险组合
    ACTION_BODY_PATTERNS = [
        (r"点赞", r"大拇指|手指|手"),
        (r"竖起", r"大拇指|手指|手"),
        (r"挥手", r"手|手臂"),
        (r"招手", r"手|手臂"),
        (r"握拳", r"拳头|手"),
        (r"比心", r"手|手指"),
        (r"鞠躬", r"腰|身体"),
    ]

    # 概念型描述关键词
    CONCEPTUAL_KEYWORDS = [
        "读成", "看起来像", "像", "类似", "仿佛", "好像", "整体呈现", "整体读成",
    ]

    # 否定词
    NEGATION_KEYWORDS = [
        "不要", "不能", "不可", "禁止", "避免", "别", "勿", "不", "无",
    ]

    def analyze_prompt(self, prompt_name: str, prompt_text: str) -> PromptRiskReport:
        """
        分析 prompt 中的风险

        Args:
            prompt_name: prompt 名称
            prompt_text: prompt 文本

        Returns:
            风险报告
        """
        report = PromptRiskReport(prompt_name=prompt_name)

        # 检查动作 + 身体部位混淆
        self._check_action_body_confusion(prompt_text, report)

        # 检查概念型描述
        self._check_conceptual_description(prompt_text, report)

        # 检查否定句堆叠
        self._check_excessive_negation(prompt_text, report)

        # 生成改写建议
        if report.risks:
            self._generate_rewrite_suggestions(prompt_text, report)

        return report

    def _check_action_body_confusion(self, prompt_text: str, report: PromptRiskReport) -> None:
        """检查动作词 + 身体部位混淆"""
        for action_pattern, body_pattern in self.ACTION_BODY_PATTERNS:
            # 检查是否同时出现动作词和身体部位
            action_matches = list(re.finditer(action_pattern, prompt_text))
            body_matches = list(re.finditer(body_pattern, prompt_text))

            if action_matches and body_matches:
                # 检查它们是否在同一句话中
                for action_match in action_matches:
                    for body_match in body_matches:
                        # 如果距离小于 50 个字符，认为是同一句话
                        distance = abs(action_match.start() - body_match.start())
                        if distance < 50:
                            # 提取上下文
                            start = max(0, action_match.start() - 20)
                            end = min(len(prompt_text), body_match.end() + 20)
                            context = prompt_text[start:end]

                            report.add_risk(PromptRisk(
                                risk_type="action_body_confusion",
                                severity="high",
                                location=f"位置 {action_match.start()}-{body_match.end()}",
                                original_text=context,
                                reason=f"'{action_match.group()}' 和 '{body_match.group()}' 同时出现，可能被模型理解为动作指令而非形状描述",
                                suggestion=f"将 '{action_match.group()}' 改为形状描述，如'造型'、'形状'、'体块'等，避免动作动词",
                            ))

    def _check_conceptual_description(self, prompt_text: str, report: PromptRiskReport) -> None:
        """检查概念型描述"""
        for keyword in self.CONCEPTUAL_KEYWORDS:
            matches = list(re.finditer(re.escape(keyword), prompt_text))
            for match in matches:
                # 提取上下文
                start = max(0, match.start() - 30)
                end = min(len(prompt_text), match.end() + 30)
                context = prompt_text[start:end]

                report.add_risk(PromptRisk(
                    risk_type="conceptual_description",
                    severity="medium",
                    location=f"位置 {match.start()}",
                    original_text=context,
                    reason=f"使用了概念型描述词 '{keyword}'，可能导致模型理解不准确",
                    suggestion="改用具体的视觉特征描述，如'外轮廓是'、'体块结构是'、'关键特征包括'等",
                ))

    def _check_excessive_negation(self, prompt_text: str, report: PromptRiskReport) -> None:
        """检查否定句堆叠"""
        negation_count = 0
        negation_positions = []

        for keyword in self.NEGATION_KEYWORDS:
            matches = list(re.finditer(re.escape(keyword), prompt_text))
            negation_count += len(matches)
            negation_positions.extend([match.start() for match in matches])

        # 如果否定词超过 3 个，报警
        if negation_count > 3:
            report.add_risk(PromptRisk(
                risk_type="excessive_negation",
                severity="medium",
                location=f"共 {negation_count} 处否定词",
                original_text=f"否定词位置: {negation_positions[:5]}...",
                reason=f"prompt 中有 {negation_count} 个否定词，过多的否定描述可能降低模型理解准确度",
                suggestion="将部分否定描述改为正面描述，如'不要圆润'改为'保持棱角分明'",
            ))

    def _generate_rewrite_suggestions(self, prompt_text: str, report: PromptRiskReport) -> None:
        """生成改写建议"""
        rewritten = prompt_text

        # 针对每个风险生成改写
        for risk in report.risks:
            if risk.risk_type == "action_body_confusion":
                # 替换动作词为形状描述
                for action_pattern, _ in self.ACTION_BODY_PATTERNS:
                    rewritten = re.sub(
                        action_pattern,
                        lambda m: self._suggest_shape_term(m.group()),
                        rewritten
                    )

            elif risk.risk_type == "conceptual_description":
                # 替换概念型描述
                for keyword in self.CONCEPTUAL_KEYWORDS:
                    if keyword in ["读成", "整体读成"]:
                        rewritten = rewritten.replace(keyword, "外轮廓是")
                    elif keyword in ["看起来像", "像", "类似", "仿佛", "好像"]:
                        rewritten = rewritten.replace(keyword, "具体特征是")

        report.rewrite_suggestions["auto_rewrite"] = rewritten

    def _suggest_shape_term(self, action_word: str) -> str:
        """为动作词建议形状描述词"""
        mapping = {
            "点赞": "点赞造型",
            "竖起": "竖立形状",
            "挥手": "挥手姿态",
            "招手": "招手姿态",
            "握拳": "握拳形状",
            "比心": "比心造型",
            "鞠躬": "鞠躬姿态",
        }
        return mapping.get(action_word, f"{action_word}造型")


def analyze_prompts(prompts: dict[str, str]) -> dict[str, PromptRiskReport]:
    """
    分析所有 prompts

    Args:
        prompts: prompt 字典 {name: text}

    Returns:
        风险报告字典 {name: report}
    """
    analyzer = PromptRiskAnalyzer()
    reports = {}

    for name, text in prompts.items():
        reports[name] = analyzer.analyze_prompt(name, text)

    return reports
