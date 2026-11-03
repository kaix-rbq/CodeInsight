"""应用配置中心。

所有模型服务、输入限制等运行参数均从环境变量或 ``.env`` 文件读取，
业务代码只依赖 :class:`Settings`，不直接读取环境变量，便于测试时替换。
"""

from __future__ import annotations

import os
from dataclasses import dataclass, replace
from pathlib import Path

from dotenv import load_dotenv

from core.errors import ConfigurationError

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

# 先加载项目根目录的 .env，再读取真实环境变量；已存在的环境变量优先级更高。
load_dotenv(ENV_FILE, override=False)

SUPPORTED_LANGUAGES: tuple[str, ...] = ("Python", "Java", "C++")

DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
DEFAULT_OLLAMA_MODEL = "qwen2.5-coder:7b"
DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_MAX_CODE_CHARS = 20_000

PROVIDER_OPENAI = "openai"
PROVIDER_OLLAMA = "ollama"
PROVIDER_DEMO = "demo"
SUPPORTED_PROVIDERS = (PROVIDER_OPENAI, PROVIDER_OLLAMA, PROVIDER_DEMO)

PROVIDER_LABELS = {
    PROVIDER_OPENAI: "在线模型（OpenAI 兼容接口）",
    PROVIDER_OLLAMA: "本地模型（Ollama）",
    PROVIDER_DEMO: "离线演示（内置样例）",
}

STRUCTURED_OUTPUT_JSON = "json"
STRUCTURED_OUTPUT_NATIVE = "native"


def _env_str(name: str, default: str = "") -> str:
    value = os.getenv(name)
    return value.strip() if value else default


def _env_float(name: str, default: float) -> float:
    raw = _env_str(name)
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError as exc:
        raise ConfigurationError(f"环境变量 {name} 必须是数字，当前值为 {raw!r}") from exc


def _env_int(name: str, default: int) -> int:
    raw = _env_str(name)
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ConfigurationError(f"环境变量 {name} 必须是整数，当前值为 {raw!r}") from exc


@dataclass(frozen=True)
class Settings:
    """不可变的运行时配置。"""

    provider: str = PROVIDER_DEMO
    model: str = DEFAULT_OPENAI_MODEL
    api_key: str | None = None
    base_url: str | None = None
    ollama_base_url: str = DEFAULT_OLLAMA_BASE_URL
    temperature: float = 0.2
    timeout: float = 90.0
    max_code_chars: int = DEFAULT_MAX_CODE_CHARS
    transport_retries: int = 2
    parse_retries: int = 1
    structured_output: str = STRUCTURED_OUTPUT_JSON

    @property
    def is_demo(self) -> bool:
        return self.provider == PROVIDER_DEMO

    @property
    def provider_label(self) -> str:
        return PROVIDER_LABELS.get(self.provider, self.provider)

    @property
    def masked_api_key(self) -> str:
        if not self.api_key:
            return "未配置"
        if len(self.api_key) <= 8:
            return "****"
        return f"{self.api_key[:4]}…{self.api_key[-4:]}"

    def with_updates(self, **changes: object) -> "Settings":
        return replace(self, **changes)


def load_settings() -> Settings:
    """从环境变量构造配置。

    未显式指定 provider 时采用 ``auto`` 策略：有 API Key 则使用在线模型，
    否则退化为离线演示模式，保证首次运行即可浏览完整界面。
    """

    requested = _env_str("CODEINSIGHT_PROVIDER", "auto").lower()
    if requested not in (*SUPPORTED_PROVIDERS, "auto"):
        raise ConfigurationError(
            "CODEINSIGHT_PROVIDER 仅支持 auto、openai、ollama、demo，"
            f"当前值为 {requested!r}"
        )

    api_key = _env_str("CODEINSIGHT_API_KEY") or _env_str("OPENAI_API_KEY") or None
    base_url = _env_str("CODEINSIGHT_BASE_URL") or None

    if requested == "auto":
        provider = PROVIDER_OPENAI if api_key else PROVIDER_DEMO
    else:
        provider = requested

    if provider == PROVIDER_OPENAI:
        model = _env_str("CODEINSIGHT_MODEL", DEFAULT_OPENAI_MODEL)
    elif provider == PROVIDER_OLLAMA:
        model = _env_str("CODEINSIGHT_MODEL", DEFAULT_OLLAMA_MODEL)
    elif provider == PROVIDER_DEMO:
        model = "内置样例报告"
    else:  # pragma: no cover - 上面已校验
        model = _env_str("CODEINSIGHT_MODEL")

    structured_output = _env_str(
        "CODEINSIGHT_STRUCTURED_OUTPUT", STRUCTURED_OUTPUT_JSON
    ).lower()
    if structured_output not in (STRUCTURED_OUTPUT_JSON, STRUCTURED_OUTPUT_NATIVE):
        raise ConfigurationError(
            "CODEINSIGHT_STRUCTURED_OUTPUT 仅支持 json 或 native，"
            f"当前值为 {structured_output!r}"
        )

    settings = Settings(
        provider=provider,
        model=model,
        api_key=api_key if provider == PROVIDER_OPENAI else None,
        base_url=base_url if provider == PROVIDER_OPENAI else None,
        ollama_base_url=_env_str("CODEINSIGHT_OLLAMA_BASE_URL", DEFAULT_OLLAMA_BASE_URL),
        temperature=_env_float("CODEINSIGHT_TEMPERATURE", 0.2),
        timeout=_env_float("CODEINSIGHT_TIMEOUT", 90.0),
        max_code_chars=_env_int("CODEINSIGHT_MAX_CODE_CHARS", DEFAULT_MAX_CODE_CHARS),
        transport_retries=_env_int("CODEINSIGHT_TRANSPORT_RETRIES", 2),
        parse_retries=_env_int("CODEINSIGHT_PARSE_RETRIES", 1),
        structured_output=structured_output,
    )
    _validate_settings(settings)
    return settings


def _validate_settings(settings: Settings) -> None:
    if settings.max_code_chars < 100:
        raise ConfigurationError("CODEINSIGHT_MAX_CODE_CHARS 不能小于 100")
    if settings.transport_retries < 0:
        raise ConfigurationError("CODEINSIGHT_TRANSPORT_RETRIES 不能为负数")
    if settings.parse_retries < 0:
        raise ConfigurationError("CODEINSIGHT_PARSE_RETRIES 不能为负数")
    if not 0.0 <= settings.temperature <= 2.0:
        raise ConfigurationError("CODEINSIGHT_TEMPERATURE 必须在 0 到 2 之间")
    if settings.timeout <= 0:
        raise ConfigurationError("CODEINSIGHT_TIMEOUT 必须大于 0")
    if settings.provider == PROVIDER_OPENAI and not settings.api_key:
        raise ConfigurationError(
            "已指定使用在线模型，但未找到 API Key（CODEINSIGHT_API_KEY 或 OPENAI_API_KEY）。"
            "请在 .env 中配置密钥，或将 CODEINSIGHT_PROVIDER 设为 demo。"
        )
