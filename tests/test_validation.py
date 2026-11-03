"""输入校验与规范化测试（对应 F-01 ~ F-03、T-06、T-07）。"""

from __future__ import annotations

import pytest

from core.config import Settings
from core.errors import ValidationError
from core.validation import code_stats, normalize_code, prepare_code, validate_mode


def test_empty_code_is_rejected() -> None:
    with pytest.raises(ValidationError) as exc_info:
        prepare_code("", "Python", 20_000)
    assert "不能为空" in str(exc_info.value)


def test_whitespace_only_code_is_rejected() -> None:
    with pytest.raises(ValidationError):
        prepare_code(" \n\t\n ", "Java", 20_000)


def test_none_code_is_rejected() -> None:
    with pytest.raises(ValidationError):
        prepare_code(None, "Python", 20_000)


def test_overlength_code_has_clear_message() -> None:
    limit = 100
    code = "x" * (limit + 1)
    with pytest.raises(ValidationError) as exc_info:
        prepare_code(code, "C++", limit)
    message = str(exc_info.value)
    assert "超过上限" in message
    assert "100" in message


def test_code_at_limit_is_accepted() -> None:
    code = "x" * 100
    assert prepare_code(code, "Python", 100) == code


def test_unsupported_language_is_rejected() -> None:
    with pytest.raises(ValidationError) as exc_info:
        prepare_code("print(1)", "Ruby", 20_000)
    assert "仅支持" in str(exc_info.value)


@pytest.mark.parametrize("language", ["Python", "Java", "C++"])
def test_supported_languages_are_accepted(language: str) -> None:
    assert prepare_code("int main() { return 0; }", language, 20_000)


def test_normalize_code_handles_crlf_and_blank_edges() -> None:
    code = "\r\n  def f():\r\n    return 1  \r\n\r\n"
    assert normalize_code(code) == "  def f():\n    return 1"


def test_code_stats_counts_lines_and_chars() -> None:
    stats = code_stats("a = 1\nb = 2")
    assert stats == {"chars": 11, "lines": 2}
    assert code_stats("") == {"chars": 0, "lines": 0}


def test_validate_mode_returns_enum() -> None:
    from core.modes import AnalysisMode

    assert validate_mode("review") is AnalysisMode.REVIEW
    assert validate_mode(AnalysisMode.TESTS) is AnalysisMode.TESTS


def test_validate_mode_rejects_unknown_value() -> None:
    with pytest.raises(ValidationError) as exc_info:
        validate_mode("unknown")
    assert "未知分析模式" in str(exc_info.value)


def test_settings_max_code_chars_is_used_by_service_validation() -> None:
    settings = Settings(max_code_chars=100)
    assert settings.max_code_chars == 100
