#!/usr/bin/env python3
"""迭代引擎：决策是否继续、停止或询问用户"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class IterationDecision:
    """迭代决策"""
    decision: str  # proceed, iterate, ask_user
    reason: str
    suggested_action: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision,
            "reason": self.reason,
            "suggested_action": self.suggested_action,
        }


class IterationEngine:
    """迭代引擎：根据验证结果和迭代历史决定下一步动作"""

    def __init__(self, strategy: dict[str, Any]):
        self.max_iterations = strategy.get("max_iterations", 3)
        self.max_same_error_repeats = strategy.get("max_same_error_repeats", 2)
        self.improvement_threshold = strategy.get("improvement_threshold", 0.15)
        self.ask_user_on_manual_checks = strategy.get("ask_user_on_manual_checks", True)

    def decide_next_action(
        self,
        validation_report: dict[str, Any],
        iterations: list[dict[str, Any]],
        stage: str,
    ) -> IterationDecision:
        """
        决定下一步动作

        Args:
            validation_report: 验证报告
            iterations: 迭代历史
            stage: 当前阶段

        Returns:
            迭代决策
        """
        if not validation_report:
            return IterationDecision(
                decision="ask_user",
                reason="还没有验证报告",
                suggested_action="请先执行 validate-run",
            )

        current_iteration = len(iterations)
        prior_iterations = iterations[:-1] if iterations else []

        # 检查是否有 manual 检查项未完成
        manual_checks = validation_report.get("manual_checks", [])
        if manual_checks and self.ask_user_on_manual_checks:
            unchecked = [check for check in manual_checks if not check.get("checked", False)]
            if unchecked:
                return IterationDecision(
                    decision="ask_user",
                    reason=f"存在 {len(unchecked)} 项人工检查未完成",
                    suggested_action="请完成人工检查清单后再继续",
                )

        # 检查是否通过验证
        if validation_report.get("passed", False):
            return IterationDecision(
                decision="proceed",
                reason="验证通过",
                suggested_action="可以继续下一阶段",
            )

        # 检查迭代次数
        if current_iteration >= self.max_iterations:
            return IterationDecision(
                decision="ask_user",
                reason=f"已达到最大迭代次数 ({self.max_iterations})",
                suggested_action="建议人工介入调整策略",
            )

        # 检查相同错误重复次数
        issues = validation_report.get("issues", [])
        if issues:
            error_signatures = self._extract_error_signatures(issues)
            repeat_count = self._count_error_repeats(error_signatures, prior_iterations)
            if repeat_count >= self.max_same_error_repeats:
                return IterationDecision(
                    decision="ask_user",
                    reason=f"相同错误重复 {repeat_count} 次",
                    suggested_action="建议人工介入调整 prompt 或约束",
                )

        # 检查改进幅度
        if prior_iterations:
            current_score = validation_report.get("score", 0.0)
            previous_score = prior_iterations[-1].get("validation_score", 0.0)
            improvement = current_score - previous_score

            if improvement < self.improvement_threshold:
                return IterationDecision(
                    decision="ask_user",
                    reason=f"改进幅度过小 ({improvement:.2f} < {self.improvement_threshold})",
                    suggested_action="建议人工介入调整策略",
                )

        # 检查是否所有错误都可以自动重试
        auto_retryable = all(issue.get("auto_retry", False) for issue in issues if issue.get("severity") == "error")
        if auto_retryable and current_iteration < self.max_iterations:
            return IterationDecision(
                decision="iterate",
                reason="所有错误都可以自动重试",
                suggested_action="建议自动重试一次",
            )

        # 默认：询问用户
        return IterationDecision(
            decision="ask_user",
            reason="存在无法自动修复的错误",
            suggested_action="建议人工检查验证报告并决定下一步",
        )

    def _extract_error_signatures(self, issues: list[dict[str, Any]]) -> list[str]:
        """提取错误签名"""
        signatures = []
        for issue in issues:
            if issue.get("severity") == "error":
                # 使用 rule_id 作为错误签名
                signatures.append(issue.get("rule_id", "unknown"))
        return signatures

    def _count_error_repeats(self, error_signatures: list[str], iterations: list[dict[str, Any]]) -> int:
        """统计相同错误的重复次数"""
        if not error_signatures:
            return 0

        # 检查最近的迭代中是否有相同的错误
        repeat_count = 1
        for iteration in reversed(iterations):
            iteration_issues = iteration.get("issues", [])
            iteration_signatures = [
                issue.get("rule_id", "unknown")
                for issue in iteration_issues
                if issue.get("severity") == "error"
            ]

            # 检查是否有交集
            if set(error_signatures) & set(iteration_signatures):
                repeat_count += 1
            else:
                break

        return repeat_count
