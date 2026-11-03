"""Pydantic 报告模型校验测试（对应 T-09 的结构约束）。"""

from __future__ import annotations

import pytest
from pydantic import ValidationError as PydanticValidationError

from core.demo import SAMPLES
from core.modes import AnalysisMode, MODE_SCHEMAS
from core.schemas import (
    Confidence,
    ExplanationReport,
    ReviewIssue,
    ReviewReport,
    Severity,
    TestCase as SampleCase,
    TestCaseType as CaseKind,
    TestReport as SampleTestReport,
)


@pytest.mark.parametrize("sample", SAMPLES, ids=[sample.id for sample in SAMPLES])
@pytest.mark.parametrize("mode", list(AnalysisMode))
def test_demo_reports_roundtrip_through_schema(sample, mode: AnalysisMode) -> None:
    report = sample.report_for(mode)
    assert isinstance(report, MODE_SCHEMAS[mode])
    dumped = report.model_dump(mode="json")
    restored = MODE_SCHEMAS[mode].model_validate(dumped)
    assert restored == report


def test_extra_fields_are_ignored() -> None:
    data = SAMPLES[0].explanation.model_dump(mode="json")
    data["unexpected_field"] = "ignored"
    report = ExplanationReport.model_validate(data)
    assert report.overall_purpose


def test_blank_strings_are_stripped() -> None:
    data = SAMPLES[0].explanation.model_dump(mode="json")
    data["overall_purpose"] = "  有空白  "
    assert ExplanationReport.model_validate(data).overall_purpose == "有空白"


def test_invalid_severity_is_rejected() -> None:
    data = SAMPLES[1].review.issues[0].model_dump(mode="json")
    data["severity"] = "critical"
    with pytest.raises(PydanticValidationError):
        ReviewIssue.model_validate(data)


def test_line_number_must_be_positive() -> None:
    data = SAMPLES[0].explanation.key_statements[0].model_dump(mode="json")
    data["line"] = 0
    with pytest.raises(PydanticValidationError):
        ExplanationReport.model_validate(
            {
                **SAMPLES[0].explanation.model_dump(mode="json"),
                "key_statements": [data],
            }
        )


def test_review_report_can_have_no_issues() -> None:
    report = ReviewReport.model_validate(
        {"summary": "未发现明显问题。", "issues": []}
    )
    assert report.issues == []


def test_test_report_requires_cases() -> None:
    with pytest.raises(PydanticValidationError):
        SampleTestReport.model_validate(
            {
                "function_signature": "f()",
                "assumptions": [],
                "cases": [],
                "coverage_summary": "无",
            }
        )


def test_severity_enum_serializes_to_english_values() -> None:
    assert Severity.HIGH.value == "high"
    assert CaseKind.NORMAL.value == "normal"


def test_test_case_defaults_notes_to_empty_string() -> None:
    case = SampleCase(
        case_type=CaseKind.NORMAL,
        title="基本用例",
        input="f(1)",
        expected="1",
        purpose="验证基本行为",
    )
    assert case.notes == ""


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("高", Severity.HIGH),
        ("严重", Severity.HIGH),
        ("中", Severity.MEDIUM),
        ("中等", Severity.MEDIUM),
        ("轻微", Severity.LOW),
        ("HIGH", Severity.HIGH),
        (" High ", Severity.HIGH),
    ],
)
def test_severity_accepts_common_model_variants(value: str, expected: Severity) -> None:
    assert Severity(value) is expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("确定", Confidence.HIGH),
        ("较确定", Confidence.HIGH),
        ("部分确定", Confidence.MEDIUM),
        ("不确定", Confidence.LOW),
        ("无法确定", Confidence.LOW),
        ("MEDIUM", Confidence.MEDIUM),
    ],
)
def test_confidence_accepts_common_model_variants(
    value: str, expected: Confidence
) -> None:
    assert Confidence(value) is expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("正常", CaseKind.NORMAL),
        ("普通", CaseKind.NORMAL),
        ("边界", CaseKind.BOUNDARY),
        ("边缘", CaseKind.BOUNDARY),
        ("edge", CaseKind.BOUNDARY),
        ("异常", CaseKind.INVALID),
        ("非法", CaseKind.INVALID),
        ("BOUNDARY", CaseKind.BOUNDARY),
    ],
)
def test_test_case_type_accepts_common_model_variants(
    value: str, expected: CaseKind
) -> None:
    assert CaseKind(value) is expected


def test_unknown_enum_alias_is_still_rejected() -> None:
    for enum_cls in (Severity, Confidence, CaseKind):
        with pytest.raises(ValueError):
            enum_cls("critical")


def test_review_issue_accepts_chinese_severity() -> None:
    data = SAMPLES[1].review.issues[0].model_dump(mode="json")
    data["severity"] = "严重"
    issue = ReviewIssue.model_validate(data)
    assert issue.severity is Severity.HIGH
    assert issue.model_dump(mode="json")["severity"] == "high"
