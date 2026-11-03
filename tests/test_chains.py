"""LangChain 分析链测试：正常解析、修复重试、异常兜底（T-01、T-09）。"""

from __future__ import annotations

import pytest
from langchain_core.language_models.fake_chat_models import FakeListChatModel

from core.chains import ReportChain
from core.demo import SAMPLES
from core.errors import ModelCallError, ResultParseError
from core.modes import AnalysisMode
from core.prompts import build_prompt
from core.schemas import ReportModel


def _good_json(mode: AnalysisMode) -> str:
    return SAMPLES[0].report_for(mode).model_dump_json()


@pytest.mark.parametrize("mode", list(AnalysisMode))
def test_chain_parses_valid_json(mode: AnalysisMode) -> None:
    chain = ReportChain(
        FakeListChatModel(responses=[_good_json(mode)]),
        mode,
        parse_retries=0,
        transport_retries=0,
    )
    result = chain.invoke(SAMPLES[0].code, "Python")
    assert isinstance(result.report, ReportModel)
    assert result.used_native_output is False
    assert result.raw_output == _good_json(mode)


@pytest.mark.parametrize("mode", list(AnalysisMode))
def test_chain_repairs_invalid_json_once(mode: AnalysisMode) -> None:
    chain = ReportChain(
        FakeListChatModel(responses=["这不是合法的 JSON", _good_json(mode)]),
        mode,
        parse_retries=1,
        transport_retries=0,
    )
    result = chain.invoke("int x = 1;", "C++")
    assert isinstance(result.report, ReportModel)
    assert result.raw_output == _good_json(mode)


def test_chain_raises_parse_error_with_raw_output() -> None:
    chain = ReportChain(
        FakeListChatModel(responses=["not json"]),
        AnalysisMode.EXPLAIN,
        parse_retries=0,
        transport_retries=0,
    )
    with pytest.raises(ResultParseError) as exc_info:
        chain.invoke("print(1)", "Python")
    assert exc_info.value.raw_output == "not json"
    assert "无法解析" in str(exc_info.value)


def test_chain_rejects_empty_model_output() -> None:
    chain = ReportChain(
        FakeListChatModel(responses=["   "]),
        AnalysisMode.REVIEW,
        parse_retries=0,
        transport_retries=0,
    )
    with pytest.raises(ResultParseError) as exc_info:
        chain.invoke("print(1)", "Python")
    assert "空内容" in str(exc_info.value)


class _TimeoutModel:
    def invoke(self, _messages):  # pragma: no cover - 仅用于异常分支
        raise TimeoutError("request timed out")


def test_chain_wraps_transport_error() -> None:
    chain = ReportChain(
        _TimeoutModel(),  # type: ignore[arg-type]
        AnalysisMode.COMPLEXITY,
        parse_retries=0,
        transport_retries=0,
        retry_backoff=0,
    )
    with pytest.raises(ModelCallError) as exc_info:
        chain.invoke("for i in range(n): pass", "Python")
    assert "超时" in str(exc_info.value)


def test_chain_retries_transport_error_then_succeeds() -> None:
    class _FlakyModel:
        def __init__(self) -> None:
            self.calls = 0
            self._fake = FakeListChatModel(responses=[_good_json(AnalysisMode.EXPLAIN)])

        def invoke(self, messages):
            self.calls += 1
            if self.calls == 1:
                raise ConnectionError("connection refused")
            return self._fake.invoke(messages)

    model = _FlakyModel()
    chain = ReportChain(
        model,  # type: ignore[arg-type]
        AnalysisMode.EXPLAIN,
        parse_retries=0,
        transport_retries=1,
        retry_backoff=0,
    )
    result = chain.invoke(SAMPLES[0].code, "Python")
    assert model.calls == 2
    assert isinstance(result.report, ReportModel)


def test_native_structured_output_falls_back_to_json() -> None:
    chain = ReportChain(
        FakeListChatModel(responses=[_good_json(AnalysisMode.TESTS)]),
        AnalysisMode.TESTS,
        parse_retries=0,
        transport_retries=0,
        native_structured_output=True,
    )
    result = chain.invoke("def f(x): return x", "Python")
    assert result.report.function_signature  # type: ignore[attr-defined]


@pytest.mark.parametrize("mode", list(AnalysisMode))
def test_prompt_contains_code_and_language(mode: AnalysisMode) -> None:
    prompt = build_prompt(mode)
    messages = prompt.format_messages(
        language="Java",
        code="public class A {}",
        format_instructions="{}",
    )
    system_text = messages[0].content
    human_text = messages[1].content
    assert "JSON" in system_text
    assert "Java" in human_text
    assert "public class A" in human_text
    assert "输出要求" in human_text


def test_prompt_has_mode_specific_requirements() -> None:
    review_prompt = build_prompt(AnalysisMode.REVIEW)
    tests_prompt = build_prompt(AnalysisMode.TESTS)
    review_human = review_prompt.format_messages(
        language="Python", code="x = 1", format_instructions="{}"
    )[1].content
    tests_human = tests_prompt.format_messages(
        language="Python", code="x = 1", format_instructions="{}"
    )[1].content
    assert "严重程度" in review_human
    assert "测试用例" in tests_human
