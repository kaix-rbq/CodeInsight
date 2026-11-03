"""业务处理层：输入校验、模型/演示分发、报告生成。"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from langchain_core.language_models.chat_models import BaseChatModel

from core.chains import ReportChain
from core.config import (
    PROVIDER_DEMO,
    PROVIDER_OLLAMA,
    PROVIDER_OPENAI,
    STRUCTURED_OUTPUT_NATIVE,
    Settings,
)
from core.demo import resolve_demo_report
from core.errors import ConfigurationError
from core.llm import build_chat_model, describe_model
from core.modes import AnalysisMode
from core.reporting import report_to_markdown
from core.schemas import ReportModel
from core.validation import prepare_code, validate_mode


@dataclass(frozen=True)
class AnalysisResult:
    """一次分析的完整结果，供界面展示与导出。"""

    mode: AnalysisMode
    language: str
    code: str
    report: ReportModel
    markdown: str
    provider: str
    model: str
    demo: bool
    elapsed_ms: int
    created_at: datetime
    demo_sample_title: str | None = None
    raw_output: str | None = None


@dataclass(frozen=True)
class EnvironmentStatus:
    ready: bool
    demo: bool
    headline: str
    detail: str


LLMFactory = Callable[[Settings], BaseChatModel]


class AnalysisService:
    """聚合四类分析流程，界面只依赖本类。"""

    def __init__(
        self,
        settings: Settings,
        *,
        llm_factory: LLMFactory = build_chat_model,
    ) -> None:
        self.settings = settings
        self._llm_factory = llm_factory
        self._chains: dict[AnalysisMode, ReportChain] = {}

    # ------------------------------------------------------------------
    # 对外接口
    # ------------------------------------------------------------------

    def analyze(
        self,
        code: str,
        language: str,
        mode: AnalysisMode | str,
    ) -> AnalysisResult:
        started = time.perf_counter()
        mode_enum = validate_mode(mode)
        prepared = prepare_code(code, language, self.settings.max_code_chars)

        if self.settings.provider == PROVIDER_DEMO:
            match = resolve_demo_report(prepared, language, mode_enum)
            report = match.report
            demo = True
            demo_sample_title = match.sample.title
            provider_label = "离线演示 · 内置样例"
            model_name = "预置报告（未调用大模型）"
            raw_output = report.model_dump_json(indent=2)
        else:
            self._validate_live_provider()
            chain = self._get_chain(mode_enum)
            outcome = chain.invoke(prepared, language)
            report = outcome.report
            demo = False
            demo_sample_title = None
            provider_label = self.settings.provider_label
            model_name = describe_model(self.settings)
            raw_output = outcome.raw_output

        elapsed_ms = int(round((time.perf_counter() - started) * 1000))
        created_at = datetime.now()

        markdown = report_to_markdown(
            mode_enum,
            report,
            code=prepared,
            language=language,
            provider=provider_label,
            model=model_name,
            demo=demo,
            created_at=created_at,
            elapsed_ms=elapsed_ms,
        )

        return AnalysisResult(
            mode=mode_enum,
            language=language,
            code=prepared,
            report=report,
            markdown=markdown,
            provider=provider_label,
            model=model_name,
            demo=demo,
            elapsed_ms=elapsed_ms,
            created_at=created_at,
            demo_sample_title=demo_sample_title,
            raw_output=raw_output,
        )

    # ------------------------------------------------------------------
    # 内部实现
    # ------------------------------------------------------------------

    def _validate_live_provider(self) -> None:
        if self.settings.provider == PROVIDER_OPENAI and not self.settings.api_key:
            raise ConfigurationError(
                "在线模型缺少 API Key。请在 .env 中设置 CODEINSIGHT_API_KEY，"
                "或将 CODEINSIGHT_PROVIDER 设为 demo 使用离线演示。"
            )
        if self.settings.provider not in (PROVIDER_OPENAI, PROVIDER_OLLAMA):
            raise ConfigurationError(
                f"未知的模型提供方 {self.settings.provider!r}。"
                "可选值为 openai、ollama、demo。"
            )

    def _get_chain(self, mode: AnalysisMode) -> ReportChain:
        chain = self._chains.get(mode)
        if chain is not None:
            return chain

        llm = self._llm_factory(self.settings)
        chain = ReportChain(
            llm,
            mode,
            parse_retries=self.settings.parse_retries,
            transport_retries=self.settings.transport_retries,
            native_structured_output=(
                self.settings.structured_output == STRUCTURED_OUTPUT_NATIVE
            ),
        )
        self._chains[mode] = chain
        return chain


def environment_status(settings: Settings) -> EnvironmentStatus:
    """返回侧边栏所需的运行环境说明。"""

    if settings.provider == PROVIDER_DEMO:
        return EnvironmentStatus(
            ready=True,
            demo=True,
            headline="离线演示模式",
            detail=(
                "未检测到在线模型 API Key，当前仅内置三份示例代码的预置报告。"
                "在 .env 中配置 CODEINSIGHT_API_KEY 后可分析任意代码。"
            ),
        )
    if settings.provider == PROVIDER_OPENAI:
        return EnvironmentStatus(
            ready=bool(settings.api_key),
            demo=False,
            headline=f"在线模型 · {settings.model}",
            detail=(
                "API Key 已配置（"
                f"{settings.masked_api_key}），分析请求将发送到所选模型服务。"
            ),
        )
    return EnvironmentStatus(
        ready=True,
        demo=False,
        headline=f"本地模型 · {settings.model}",
        detail=f"请确认 Ollama 服务已在 {settings.ollama_base_url} 启动。",
    )


def build_service(settings: Settings) -> AnalysisService:
    return AnalysisService(settings)
