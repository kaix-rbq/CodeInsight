"""LangChain 聊天模型工厂。

在线模型与本地模型都通过 LangChain 集成包创建，业务层只接触统一的
``BaseChatModel`` 接口，便于扩展其他 OpenAI 兼容服务。
"""

from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel

from core.config import (
    PROVIDER_OLLAMA,
    PROVIDER_OPENAI,
    Settings,
)
from core.errors import ConfigurationError


def build_chat_model(settings: Settings) -> BaseChatModel:
    """根据配置创建聊天模型实例。"""

    if settings.provider == PROVIDER_OPENAI:
        return _build_openai_model(settings)
    if settings.provider == PROVIDER_OLLAMA:
        return _build_ollama_model(settings)
    raise ConfigurationError(
        f"当前提供方 {settings.provider!r} 不支持直接创建聊天模型。"
        "离线演示模式不会调用大模型。"
    )


def _build_openai_model(settings: Settings) -> BaseChatModel:
    try:
        from langchain_openai import ChatOpenAI
    except ImportError as exc:  # pragma: no cover - 依赖缺失时的友好提示
        raise ConfigurationError(
            "缺少 langchain-openai 依赖，请先执行 pip install -r requirements.txt",
            detail=str(exc),
        ) from exc

    if not settings.api_key:
        raise ConfigurationError(
            "未配置在线模型 API Key。请在 .env 中设置 CODEINSIGHT_API_KEY，"
            "或将 CODEINSIGHT_PROVIDER 改为 demo 使用离线演示。"
        )

    return ChatOpenAI(
        model=settings.model,
        api_key=settings.api_key,
        base_url=settings.base_url,
        temperature=settings.temperature,
        timeout=settings.timeout,
        max_retries=settings.transport_retries,
    )


def _build_ollama_model(settings: Settings) -> BaseChatModel:
    try:
        from langchain_ollama import ChatOllama
    except ImportError as exc:  # pragma: no cover - 依赖缺失时的友好提示
        raise ConfigurationError(
            "缺少 langchain-ollama 依赖，请先执行 pip install -r requirements.txt",
            detail=str(exc),
        ) from exc

    return ChatOllama(
        model=settings.model,
        base_url=settings.ollama_base_url,
        temperature=settings.temperature,
        num_predict=4096,
    )


def describe_model(settings: Settings) -> str:
    """返回界面展示用的模型描述。"""

    if settings.provider == PROVIDER_OPENAI:
        location = settings.base_url or "OpenAI 官方接口"
        return f"{settings.model} · {location}"
    if settings.provider == PROVIDER_OLLAMA:
        return f"{settings.model} · {settings.ollama_base_url}"
    return "内置样例预置报告（未调用大模型）"
