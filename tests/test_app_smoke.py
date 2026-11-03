"""Streamlit 界面冒烟与端到端测试（T-06、T-08 的界面表现）。"""

from __future__ import annotations

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from core.modes import AnalysisMode

APP_PATH = Path(__file__).resolve().parent.parent / "app.py"
_ENV_KEYS = [
    "CODEINSIGHT_PROVIDER",
    "CODEINSIGHT_API_KEY",
    "OPENAI_API_KEY",
    "CODEINSIGHT_MODEL",
    "CODEINSIGHT_BASE_URL",
    "CODEINSIGHT_MAX_CODE_CHARS",
]


@pytest.fixture(autouse=True)
def _force_demo_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in _ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


def _run() -> AppTest:
    at = AppTest.from_file(str(APP_PATH), default_timeout=30).run()
    assert len(at.exception) == 0
    return at


def _analyze_button(at: AppTest):
    return at.button[3]


def test_initial_page_renders_controls() -> None:
    at = _run()
    assert any(button.label == "🚀 开始分析" for button in at.button)
    assert [radio.label for radio in at.radio] == ["编程语言", "分析模式"]
    assert at.text_area[0].value == ""
    assert len(at.error) == 0


def test_python_demo_analysis_end_to_end() -> None:
    at = _run()
    at.button[0].click().run()
    assert at.radio[0].value == "Python"
    assert at.text_area[0].value.startswith("def find_two_sum")
    _analyze_button(at).click().run()

    assert len(at.exception) == 0
    assert len(at.error) == 0
    assert [tab.label for tab in at.tabs] == [
        "📋 结构化报告",
        "📄 复制 / 导出",
        "🧾 原始数据",
    ]
    assert any("离线演示模式" in warning.value for warning in at.warning)
    assert any("整体功能" in markdown.value for markdown in at.markdown)


def test_java_review_mode_renders_issues() -> None:
    at = _run()
    at.button[1].click().run()
    assert at.radio[0].value == "Java"
    at.radio[1].set_value(AnalysisMode.REVIEW).run()
    _analyze_button(at).click().run()

    assert len(at.exception) == 0
    assert len(at.expander) > 0
    assert any("高优先级" in markdown.value for markdown in at.markdown)


def test_cpp_tests_mode_renders_table() -> None:
    at = _run()
    at.button[2].click().run()
    assert at.radio[0].value == "C++"
    at.radio[1].set_value(AnalysisMode.TESTS).run()
    _analyze_button(at).click().run()

    assert len(at.exception) == 0
    assert any("ci-table" in markdown.value for markdown in at.markdown)
    assert any("覆盖说明" in markdown.value for markdown in at.markdown)


def test_empty_code_submission_shows_validation_error() -> None:
    at = _run()
    _analyze_button(at).click().run()

    assert len(at.exception) == 0
    assert any("不能为空" in error.value for error in at.error)


def test_custom_code_in_demo_mode_shows_guidance_and_retry() -> None:
    at = _run()
    at.text_area[0].input("print('hello')").run()
    _analyze_button(at).click().run()

    assert len(at.exception) == 0
    assert any("离线演示模式" in error.value for error in at.error)
    assert any(button.label == "🔄 重试分析" for button in at.button)


def test_overlength_code_is_blocked(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CODEINSIGHT_MAX_CODE_CHARS", "300")
    at = _run()
    at.text_area[0].input("x" * 400).run()
    assert any("超过上限" in error.value for error in at.error)

    _analyze_button(at).click().run()
    assert len(at.exception) == 0
    assert any("超过上限" in error.value for error in at.error)


def test_stale_result_banner_and_reanalyze_button() -> None:
    at = _run()
    at.button[0].click().run()
    _analyze_button(at).click().run()
    at.text_area[0].input(at.text_area[0].value + "\n# 修改后的代码").run()

    assert any("已更改" in warning.value for warning in at.warning)
    assert any(button.label == "🔄 重新分析" for button in at.button)
    assert len(at.exception) == 0


def test_clear_button_resets_editor() -> None:
    at = _run()
    at.button[0].click().run()
    at.button[4].click().run()
    assert at.text_area[0].value == ""
