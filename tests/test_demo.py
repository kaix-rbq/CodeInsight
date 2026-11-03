"""离线演示样例完整性测试。"""

from __future__ import annotations

import pytest

from core.demo import SAMPLES, SAMPLE_BY_ID, SAMPLE_BY_CODE, resolve_demo_report
from core.errors import DemoNotAvailableError
from core.modes import AnalysisMode, MODE_SCHEMAS


def test_three_language_samples_exist() -> None:
    assert {sample.language for sample in SAMPLES} == {"Python", "Java", "C++"}
    assert len(SAMPLES) == 3
    assert len(SAMPLE_BY_ID) == 3


@pytest.mark.parametrize("sample", SAMPLES, ids=[sample.id for sample in SAMPLES])
@pytest.mark.parametrize("mode", list(AnalysisMode))
def test_every_sample_has_valid_report_for_every_mode(sample, mode: AnalysisMode) -> None:
    match = resolve_demo_report(sample.code, sample.language, mode)
    assert match.sample is sample
    assert isinstance(match.report, MODE_SCHEMAS[mode])


@pytest.mark.parametrize("sample", SAMPLES, ids=[sample.id for sample in SAMPLES])
def test_key_lines_stay_within_code_range(sample) -> None:
    line_count = sample.code.count("\n") + 1
    explanation_lines = [
        item.line for item in sample.explanation.key_statements if item.line is not None
    ]
    review_lines = [
        issue.location.line
        for issue in sample.review.issues
        if issue.location.line is not None
    ]
    assert all(1 <= line <= line_count for line in explanation_lines)
    assert all(1 <= line <= line_count for line in review_lines)


@pytest.mark.parametrize("sample", SAMPLES, ids=[sample.id for sample in SAMPLES])
def test_sample_codes_are_unique_after_normalization(sample) -> None:
    assert SAMPLE_BY_CODE[sample.code] is sample


def test_resolve_demo_report_rejects_custom_code() -> None:
    with pytest.raises(DemoNotAvailableError):
        resolve_demo_report("print('hello world')", "Python", AnalysisMode.EXPLAIN)


def test_resolve_demo_report_rejects_wrong_language() -> None:
    with pytest.raises(DemoNotAvailableError) as exc_info:
        resolve_demo_report(SAMPLES[2].code, "Python", AnalysisMode.EXPLAIN)
    assert "C++" in str(exc_info.value)
