"""Markdown 报告渲染测试（F-35、T-01 报告完整性）。"""

from __future__ import annotations

from datetime import datetime

import pytest

from core.demo import SAMPLES
from core.modes import MODE_LABELS, AnalysisMode
from core.reporting import report_to_markdown
from core.schemas import (
    TestCase as SampleCase,
    TestCaseType as CaseKind,
    TestReport as SampleTestReport,
)


def _markdown(mode: AnalysisMode, sample_index: int = 0, code: str | None = None) -> str:
    sample = SAMPLES[sample_index]
    return report_to_markdown(
        mode,
        sample.report_for(mode),
        code=code if code is not None else sample.code,
        language=sample.language,
        provider="离线演示 · 内置样例",
        model="预置报告（未调用大模型）",
        demo=True,
        created_at=datetime(2026, 11, 1, 12, 0, 0),
        elapsed_ms=1500,
    )


@pytest.mark.parametrize("sample", SAMPLES, ids=[sample.id for sample in SAMPLES])
@pytest.mark.parametrize("mode", list(AnalysisMode))
def test_markdown_has_common_metadata(sample, mode: AnalysisMode) -> None:
    text = _markdown(mode, SAMPLES.index(sample))
    assert text.startswith("# CodeInsight 分析报告")
    assert MODE_LABELS[mode] in text
    assert sample.language in text
    assert "生成时间" in text
    assert "1.50 秒" in text
    assert "离线演示模式" in text
    assert "输入代码" in text
    assert sample.code.splitlines()[0] in text


def test_explanation_markdown_has_all_sections() -> None:
    text = _markdown(AnalysisMode.EXPLAIN)
    for section in ["整体功能", "执行流程", "关键语句", "输入与输出", "算法思路", "分析假设"]:
        assert section in text


def test_review_markdown_lists_every_issue() -> None:
    sample = SAMPLES[1]
    text = _markdown(AnalysisMode.REVIEW, 1)
    for issue in sample.review.issues:
        assert issue.title in text
    assert "问题详情" in text
    assert "静态阅读发现的潜在问题" in text


def test_complexity_markdown_has_derivation() -> None:
    text = _markdown(AnalysisMode.COMPLEXITY, 2)
    report = SAMPLES[2].complexity
    assert report.time_complexity in text
    assert "推导过程" in text
    assert "优化建议" in text


def test_tests_markdown_lists_cases_and_escapes_pipes() -> None:
    sample = SAMPLES[0]
    text = _markdown(AnalysisMode.TESTS, 0)
    for case in sample.tests.cases:
        assert case.title in text
    assert "覆盖说明" in text
    custom = SampleTestReport(
        function_signature="f(x)",
        assumptions=[],
        cases=[
            SampleCase(
                case_type=CaseKind.NORMAL,
                title="含竖线",
                input="a | b",
                expected="ok",
                purpose="验证表格转义",
            )
        ],
        coverage_summary="单用例",
    )
    escaped = report_to_markdown(
        AnalysisMode.TESTS,
        custom,
        code="f(x)",
        language="Python",
        provider="测试",
        model="测试",
        demo=False,
        created_at=datetime(2026, 11, 1),
        elapsed_ms=1,
    )
    assert "a \\| b" in escaped


def test_markdown_uses_longer_fence_for_nested_backticks() -> None:
    code = "def f():\n    ```\n    pass\n"
    text = _markdown(AnalysisMode.EXPLAIN, code=code)
    assert "````python" in text
