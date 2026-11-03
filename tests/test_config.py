"""配置加载测试。"""

from __future__ import annotations

import pytest

from core.config import Settings, load_settings
from core.errors import ConfigurationError

_ENV_KEYS = [
    "CODEINSIGHT_PROVIDER",
    "CODEINSIGHT_API_KEY",
    "OPENAI_API_KEY",
    "CODEINSIGHT_MODEL",
    "CODEINSIGHT_BASE_URL",
    "CODEINSIGHT_OLLAMA_BASE_URL",
    "CODEINSIGHT_TEMPERATURE",
    "CODEINSIGHT_TIMEOUT",
    "CODEINSIGHT_MAX_CODE_CHARS",
    "CODEINSIGHT_TRANSPORT_RETRIES",
    "CODEINSIGHT_PARSE_RETRIES",
    "CODEINSIGHT_STRUCTURED_OUTPUT",
]


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in _ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


def test_auto_without_key_falls_back_to_demo() -> None:
    settings = load_settings()
    assert settings.provider == "demo"
    assert settings.is_demo is True
    assert settings.model == "内置样例报告"


def test_auto_with_api_key_uses_openai(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CODEINSIGHT_API_KEY", "sk-secret-key-1234")
    settings = load_settings()
    assert settings.provider == "openai"
    assert settings.model == "gpt-4o-mini"
    assert settings.api_key == "sk-secret-key-1234"


def test_openai_provider_without_key_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CODEINSIGHT_PROVIDER", "openai")
    with pytest.raises(ConfigurationError) as exc_info:
        load_settings()
    assert "API Key" in str(exc_info.value)


def test_demo_provider_hides_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CODEINSIGHT_PROVIDER", "demo")
    monkeypatch.setenv("CODEINSIGHT_API_KEY", "sk-secret")
    settings = load_settings()
    assert settings.provider == "demo"
    assert settings.api_key is None


def test_invalid_provider_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CODEINSIGHT_PROVIDER", "unknown")
    with pytest.raises(ConfigurationError) as exc_info:
        load_settings()
    assert "CODEINSIGHT_PROVIDER" in str(exc_info.value)


def test_invalid_numeric_env_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CODEINSIGHT_TEMPERATURE", "hot")
    with pytest.raises(ConfigurationError) as exc_info:
        load_settings()
    assert "CODEINSIGHT_TEMPERATURE" in str(exc_info.value)


def test_custom_values_are_loaded(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CODEINSIGHT_PROVIDER", "ollama")
    monkeypatch.setenv("CODEINSIGHT_MODEL", "custom-model")
    monkeypatch.setenv("CODEINSIGHT_OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    monkeypatch.setenv("CODEINSIGHT_MAX_CODE_CHARS", "1234")
    monkeypatch.setenv("CODEINSIGHT_STRUCTURED_OUTPUT", "native")
    settings = load_settings()
    assert settings.provider == "ollama"
    assert settings.model == "custom-model"
    assert settings.max_code_chars == 1234
    assert settings.structured_output == "native"


def test_masked_api_key_never_exposes_full_secret() -> None:
    settings = Settings(provider="openai", api_key="sk-1234567890abcdef")
    masked = settings.masked_api_key
    assert "…" in masked
    assert settings.api_key not in masked


def test_with_updates_returns_new_settings() -> None:
    base = Settings(provider="demo")
    updated = base.with_updates(provider="openai", api_key="sk-test")
    assert base.provider == "demo"
    assert updated.provider == "openai"
    assert updated.api_key == "sk-test"
