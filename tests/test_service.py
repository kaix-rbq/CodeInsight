"""业务层测试：模式分发、演示模式、错误处理（T-01 ~ T-03、T-05、T-08、T-09）。"""

from __future__ import annotations

import pytest
from langchain_core.language_models.fake_chat_models import FakeListChatModel

from core.config import Settings
from core.demo import SAMPLES
from core.errors import ConfigurationError, DemoNotAvailableError, ResultParseError, ValidationError
from core.modes import AnalysisMode, MODE_LABELS, MODE_SCHEMAS
from core.service import AnalysisService


def _live_settings(**overrides: object) -> Settings:
    base = dict(
        provider="openai",
        api_key="sk-test-key",
        model="fake-model",
        base_url=None,
        parse_retries=0,
        transport_retries=0,
    )
    base.update(overrides)
    return Settings(**base)


def _live_service(mode: AnalysisMode, response: str | None = None, **overrides: object) -> AnalysisService:
    payload = response if response is not None else SAMPLES[0].report_for(mode).model_dump_json()
    settings = _live_settings(**overrides)
    return AnalysisService(
        settings,
        llm_factory=lambda _settings: FakeListChatModel(responses=[payload]),
    )


@pytest.mark.parametrize("mode", list(AnalysisMode))
def test_live_service_returns_typed_report(mode: AnalysisMode) -> None:
    service = _live_service(mode)
    result = service.analyze("def add(a, b):\n    return a + b\n", "Python", mode)
    assert isinstance(result.report, MODE_SCHEMAS[mode])
    assert result.demo is False
    assert result.mode is mode
    assert result.provider
    assert result.elapsed_ms >= 0
    assert result.raw_output
    assert MODE_LABELS[mode] in result.markdown
    assert "def add(a, b)" in result.markdown


def test_live_service_accepts_mode_string() -> None:
    service = _live_service(AnalysisMode.REVIEW)
    result = service.analyze("x = 1", "Python", "review")
    assert result.mode is AnalysisMode.REVIEW


def test_live_service_requires_api_key() -> None:
    settings = _live_settings(api_key=None)
    service = AnalysisService(
        settings, llm_factory=lambda _settings: FakeListChatModel(responses=["{}"])
    )
    with pytest.raises(ConfigurationError) as exc_info:
        service.analyze("print(1)", "Python", AnalysisMode.EXPLAIN)
    assert "API Key" in str(exc_info.value)


def test_live_service_parse_error_is_reported() -> None:
    service = _live_service(AnalysisMode.EXPLAIN, response="not-json")
    with pytest.raises(ResultParseError) as exc_info:
        service.analyze("print(1)", "Python", AnalysisMode.EXPLAIN)
    assert exc_info.value.raw_output == "not-json"


def test_service_rejects_empty_code() -> None:
    service = _live_service(AnalysisMode.EXPLAIN)
    with pytest.raises(ValidationError):
        service.analyze("   ", "Python", AnalysisMode.EXPLAIN)


def test_service_rejects_unknown_mode() -> None:
    service = _live_service(AnalysisMode.EXPLAIN)
    with pytest.raises(ValidationError) as exc_info:
        service.analyze("print(1)", "Python", "unknown")
    assert "未知分析模式" in str(exc_info.value)


def test_service_enforces_length_limit() -> None:
    service = _live_service(AnalysisMode.EXPLAIN, max_code_chars=100)
    with pytest.raises(ValidationError):
        service.analyze("x" * 101, "Python", AnalysisMode.EXPLAIN)


@pytest.mark.parametrize("mode", list(AnalysisMode))
def test_demo_mode_returns_preset_report(mode: AnalysisMode) -> None:
    service = AnalysisService(Settings(provider="demo"))
    result = service.analyze(SAMPLES[0].code, "Python", mode)
    assert result.demo is True
    assert isinstance(result.report, MODE_SCHEMAS[mode])
    assert result.demo_sample_title == SAMPLES[0].title
    assert "离线演示模式" in result.markdown
    assert result.raw_output


def test_demo_mode_accepts_whitespace_variations() -> None:
    service = AnalysisService(Settings(provider="demo"))
    code = "\r\n" + SAMPLES[0].code.replace("\n", "  \r\n") + "\r\n"
    result = service.analyze(code, "Python", AnalysisMode.EXPLAIN)
    assert result.code == SAMPLES[0].code


def test_demo_mode_rejects_custom_code() -> None:
    service = AnalysisService(Settings(provider="demo"))
    with pytest.raises(DemoNotAvailableError) as exc_info:
        service.analyze("print('hello')", "Python", AnalysisMode.EXPLAIN)
    assert "离线演示模式" in str(exc_info.value)


def test_demo_mode_rejects_language_mismatch() -> None:
    service = AnalysisService(Settings(provider="demo"))
    with pytest.raises(DemoNotAvailableError) as exc_info:
        service.analyze(SAMPLES[0].code, "Java", AnalysisMode.EXPLAIN)
    assert "Python" in str(exc_info.value)


def test_environment_status_for_demo() -> None:
    from core.service import environment_status

    status = environment_status(Settings(provider="demo"))
    assert status.ready is True
    assert status.demo is True
    assert "离线演示" in status.headline
