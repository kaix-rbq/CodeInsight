"""LangChain 分析链：提示词 → 模型调用 → 结构化解析 → 失败修复。

每条分析链都执行相同的骨架流程，仅在提示词任务和 Pydantic 目标模型上不同。
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.output_parsers import PydanticOutputParser

from core.errors import ConfigurationError, ModelCallError, ResultParseError
from core.modes import AnalysisMode, MODE_SCHEMAS
from core.prompts import REPAIR_TEMPLATE, build_prompt
from core.schemas import ReportModel

_MAX_REPAIR_OUTPUT_CHARS = 4_000


@dataclass
class ChainResult:
    """分析链的返回结果。"""

    report: ReportModel
    raw_output: str
    used_native_output: bool = False


def _friendly_model_error(exc: Exception) -> str:
    text = f"{type(exc).__name__}: {exc}".lower()
    if "401" in text or "unauthorized" in text or "invalid api key" in text or "api key" in text:
        return "模型服务鉴权失败，请检查 API Key 是否正确、是否有权访问该模型。"
    if "403" in text or "permission" in text:
        return "模型服务拒绝访问，请检查账号权限或模型名称是否正确。"
    if "429" in text or "rate limit" in text:
        return "模型服务请求过于频繁（429），请稍后重试。"
    if "timeout" in text or "timed out" in text:
        return "模型调用超时，请检查网络或适当调大 CODEINSIGHT_TIMEOUT 后重试。"
    if "connection" in text or "connect" in text or "network" in text:
        return "无法连接模型服务，请检查网络、Base URL 或本地模型是否已启动。"
    if "404" in text or "model not found" in text:
        return "未找到指定模型，请检查 CODEINSIGHT_MODEL 配置。"
    return "模型调用失败，请检查模型配置与网络状态后重试。"


def _content_to_text(message: BaseMessage) -> str:
    """兼容字符串内容和多段内容（部分模型以 content blocks 返回）。"""

    content = message.content
    if isinstance(content, str):
        return content

    chunks: list[str] = []
    if isinstance(content, list):
        for item in content:
            if isinstance(item, str):
                chunks.append(item)
            elif isinstance(item, dict):
                text = item.get("text") or item.get("content")
                if isinstance(text, str):
                    chunks.append(text)
            else:
                text = getattr(item, "text", None)
                if isinstance(text, str):
                    chunks.append(text)
    return "\n".join(chunks) if chunks else str(content)


class ReportChain:
    """单个分析模式对应的可调用链。"""

    def __init__(
        self,
        llm: BaseChatModel,
        mode: AnalysisMode,
        *,
        parse_retries: int = 1,
        transport_retries: int = 2,
        native_structured_output: bool = False,
        retry_backoff: float = 1.0,
    ) -> None:
        self.llm = llm
        self.mode = mode
        self.schema = MODE_SCHEMAS[mode]
        self.prompt = build_prompt(mode)
        self.parser = PydanticOutputParser(pydantic_object=self.schema)
        self.parse_retries = max(0, parse_retries)
        self.transport_retries = max(0, transport_retries)
        self.native_structured_output = native_structured_output
        self.retry_backoff = max(0.0, retry_backoff)

    # ------------------------------------------------------------------
    # 公共入口
    # ------------------------------------------------------------------

    def invoke(self, code: str, language: str) -> ChainResult:
        """执行分析链。"""

        try:
            messages = self.prompt.format_messages(
                language=language,
                code=code,
                format_instructions=self.parser.get_format_instructions(),
            )
        except Exception as exc:  # 模板变量缺失等内部错误
            raise ConfigurationError("提示词模板渲染失败，请检查提示词配置。", detail=str(exc)) from exc

        if self.native_structured_output:
            native_result = self._try_native_structured_output(messages)
            if native_result is not None:
                return native_result

        return self._invoke_with_json_repair(messages)

    # ------------------------------------------------------------------
    # 原生结构化输出（可选）
    # ------------------------------------------------------------------

    def _try_native_structured_output(
        self, messages: list[BaseMessage]
    ) -> ChainResult | None:
        try:
            structured_llm = self.llm.with_structured_output(self.schema)
        except (AttributeError, NotImplementedError):
            return None

        try:
            raw: Any = structured_llm.invoke(messages)
        except Exception:
            # 原生结构化输出在不同服务商间兼容性不一，失败后回退到 JSON 解析流程。
            return None

        if isinstance(raw, self.schema):
            return ChainResult(
                report=raw,
                raw_output=raw.model_dump_json(indent=2),
                used_native_output=True,
            )

        try:
            report = self.schema.model_validate(raw)
        except Exception:
            return None
        return ChainResult(
            report=report,
            raw_output=report.model_dump_json(indent=2),
            used_native_output=True,
        )

    # ------------------------------------------------------------------
    # JSON 输出 + 解析修复
    # ------------------------------------------------------------------

    def _invoke_with_json_repair(self, messages: list[BaseMessage]) -> ChainResult:
        raw_output = self._invoke_text(messages)
        last_error: Exception | None = None

        for attempt in range(self.parse_retries + 1):
            try:
                report = self.parser.parse(raw_output)
                return ChainResult(report=report, raw_output=raw_output)
            except Exception as exc:  # 解析失败或字段校验失败
                last_error = exc
                if attempt >= self.parse_retries:
                    break
                messages = [
                    *messages,
                    AIMessage(content=raw_output),
                    HumanMessage(
                        content=REPAIR_TEMPLATE.format(
                            error=str(exc)[:_MAX_REPAIR_OUTPUT_CHARS],
                            previous_output=raw_output[:_MAX_REPAIR_OUTPUT_CHARS],
                        )
                    ),
                ]
                raw_output = self._invoke_text(messages)

        raise ResultParseError(
            "模型返回的内容无法解析为约定结构，已保留原始输出以便排查。请重试或更换模型。",
            raw_output=raw_output,
            detail=f"{type(last_error).__name__}: {last_error}",
        )

    def _invoke_text(self, messages: list[BaseMessage]) -> str:
        message = self._invoke_with_retry(self.llm.invoke, messages)
        text = _content_to_text(message).strip()
        if not text:
            raise ResultParseError("模型返回了空内容，请重试或更换模型。", raw_output="")
        return text

    def _invoke_with_retry(self, target: Any, messages: list[BaseMessage]) -> Any:
        attempts = self.transport_retries + 1
        last_exc: Exception | None = None
        for attempt in range(attempts):
            try:
                return target(messages)
            except Exception as exc:
                last_exc = exc
                if attempt >= attempts - 1:
                    break
                time.sleep(self.retry_backoff * (2**attempt) * 0.5)

        raise ModelCallError(
            _friendly_model_error(last_exc) if last_exc else "模型调用失败。",
            detail=f"{type(last_exc).__name__}: {last_exc}" if last_exc else None,
        ) from last_exc
