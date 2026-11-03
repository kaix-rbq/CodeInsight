"""分析模式定义及其与报告模型的映射。"""

from __future__ import annotations

from enum import Enum

from core.schemas import (
    ComplexityReport,
    ExplanationReport,
    ReportModel,
    ReviewReport,
    TestReport,
)


class AnalysisMode(str, Enum):
    EXPLAIN = "explain"
    REVIEW = "review"
    COMPLEXITY = "complexity"
    TESTS = "tests"


MODE_LABELS: dict[AnalysisMode, str] = {
    AnalysisMode.EXPLAIN: "代码解释",
    AnalysisMode.REVIEW: "代码审查",
    AnalysisMode.COMPLEXITY: "复杂度分析",
    AnalysisMode.TESTS: "测试用例",
}

MODE_DESCRIPTIONS: dict[AnalysisMode, str] = {
    AnalysisMode.EXPLAIN: "说明整体功能、执行流程、关键语句、输入输出与算法思路。",
    AnalysisMode.REVIEW: "找出潜在的逻辑、边界、异常、质量与性能问题，并给出修复建议。",
    AnalysisMode.COMPLEXITY: "估算时间与空间复杂度，说明推导依据、前提和优化方向。",
    AnalysisMode.TESTS: "生成正常、边界与异常测试用例，给出预期结果与覆盖目的。",
}

MODE_ICONS: dict[AnalysisMode, str] = {
    AnalysisMode.EXPLAIN: "📖",
    AnalysisMode.REVIEW: "🔍",
    AnalysisMode.COMPLEXITY: "📈",
    AnalysisMode.TESTS: "🧪",
}

MODE_SCHEMAS: dict[AnalysisMode, type[ReportModel]] = {
    AnalysisMode.EXPLAIN: ExplanationReport,
    AnalysisMode.REVIEW: ReviewReport,
    AnalysisMode.COMPLEXITY: ComplexityReport,
    AnalysisMode.TESTS: TestReport,
}


def coerce_mode(value: str | AnalysisMode) -> AnalysisMode:
    """把字符串转换为枚举，非法值抛出可读错误。"""

    if isinstance(value, AnalysisMode):
        return value
    try:
        return AnalysisMode(value)
    except ValueError as exc:
        supported = "、".join(mode.value for mode in AnalysisMode)
        raise ValueError(f"未知分析模式 {value!r}，可选值为：{supported}") from exc
