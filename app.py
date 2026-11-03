"""CodeInsight Streamlit 应用入口。"""

from __future__ import annotations

import streamlit as st

from core.config import (
    SUPPORTED_LANGUAGES,
    Settings,
    load_settings,
)
from core.demo import SAMPLE_BY_ID, SAMPLES
from core.errors import CodeInsightError, ConfigurationError
from core.modes import (
    AnalysisMode,
    MODE_DESCRIPTIONS,
    MODE_ICONS,
    MODE_LABELS,
)
from core.service import (
    AnalysisResult,
    AnalysisService,
    build_service,
    environment_status,
)
from core.validation import code_stats, normalize_code
from ui.report_view import (
    render_empty_state,
    render_error,
    render_result,
)
from ui.sidebar import render_sidebar
from ui.theme import inject_styles, render_footer, render_hero

st.set_page_config(
    page_title="CodeInsight · 智能代码解释与审查",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

_SESSION_DEFAULTS: dict[str, object] = {
    "code_input": "",
    "language": SUPPORTED_LANGUAGES[0],
    "analysis_mode": AnalysisMode.EXPLAIN,
    "last_result": None,
    "last_error": None,
}


@st.cache_resource(show_spinner=False)
def _get_service(settings: Settings) -> AnalysisService:
    return build_service(settings)


def _init_session() -> None:
    for key, default in _SESSION_DEFAULTS.items():
        st.session_state.setdefault(key, default)


def _load_sample(sample_id: str) -> None:
    sample = SAMPLE_BY_ID[sample_id]
    st.session_state["code_input"] = sample.code
    st.session_state["language"] = sample.language
    st.session_state["last_error"] = None


def _clear_code() -> None:
    st.session_state["code_input"] = ""
    st.session_state["last_error"] = None


def _execute_analysis(service: AnalysisService, settings: Settings) -> None:
    """执行一次分析并写入会话状态。异常不会向上抛出，避免页面崩溃。"""

    code = st.session_state.get("code_input", "")
    language = st.session_state.get("language", SUPPORTED_LANGUAGES[0])
    mode = st.session_state.get("analysis_mode", AnalysisMode.EXPLAIN)
    st.session_state["last_error"] = None

    spinner_text = (
        "正在载入内置示例报告…"
        if settings.is_demo
        else f"正在调用 {settings.model} 分析代码，请稍候…"
    )
    try:
        with st.spinner(spinner_text):
            result = service.analyze(code, language, mode)
    except CodeInsightError as exc:
        st.session_state["last_result"] = None
        st.session_state["last_error"] = exc
        return
    except Exception as exc:  # 兜底：模型 SDK 抛出的非预期异常也不让页面崩溃
        st.session_state["last_result"] = None
        st.session_state["last_error"] = CodeInsightError(
            "分析过程中出现未预期错误，页面已安全降级。请重试或查看技术详情。",
            detail=f"{type(exc).__name__}: {exc}",
        )
        return

    st.session_state["last_result"] = result
    st.session_state["last_error"] = None
    st.toast("分析完成，报告已生成。", icon="✅")


def _result_matches_current_input(result: object) -> bool:
    if not isinstance(result, AnalysisResult):
        return False
    current_code = normalize_code(st.session_state.get("code_input", ""))
    current_language = st.session_state.get("language")
    current_mode = st.session_state.get("analysis_mode")
    return (
        result.code == current_code
        and result.language == current_language
        and result.mode is current_mode
    )


def _render_config_error(error: Exception) -> None:
    render_hero()
    st.error(f"配置加载失败：{error}")
    if isinstance(error, CodeInsightError) and error.detail:
        with st.expander("技术详情"):
            st.code(error.detail, language="text")
    st.markdown("#### 修复方式")
    st.markdown("在项目根目录创建或修改 `.env` 文件，然后重启应用：")
    st.code(
        "# 方案一：使用离线演示（无需 API Key）\n"
        "CODEINSIGHT_PROVIDER=demo\n\n"
        "# 方案二：使用在线模型\n"
        "CODEINSIGHT_PROVIDER=openai\n"
        "CODEINSIGHT_API_KEY=sk-your-key\n"
        "CODEINSIGHT_MODEL=gpt-4o-mini",
        language="bash",
    )
    st.caption("也可以参考 `.env.example` 与 README 中的完整配置说明。")
    st.stop()


def _render_input_panel(settings: Settings) -> bool:
    """渲染左侧输入区，返回是否点击了“开始分析”。"""

    with st.container(border=True):
        st.markdown("#### ① 输入代码")

        language = st.radio(
            "编程语言",
            options=list(SUPPORTED_LANGUAGES),
            horizontal=True,
            key="language",
            width="stretch",
        )

        st.markdown("**载入示例**")
        sample_cols = st.columns(len(SAMPLES))
        for col, sample in zip(sample_cols, SAMPLES):
            with col:
                st.button(
                    f"{sample.language} 示例",
                    key=f"load_sample_{sample.id}",
                    on_click=_load_sample,
                    args=(sample.id,),
                    help=f"{sample.title}：{sample.description}",
                    width="stretch",
                )
        st.caption("示例会覆盖编辑区并自动切换语言；分析模式保持不变。")

        code = st.text_area(
            "代码内容",
            key="code_input",
            height=380,
            placeholder="在此粘贴 Python / Java / C++ 代码…",
            label_visibility="collapsed",
        )

        stats = code_stats(code)
        limit = settings.max_code_chars
        if stats["chars"] > limit:
            st.error(
                f"代码约 {stats['chars']:,} 字符，已超过上限 {limit:,} 字符，"
                "请精简后再提交。"
            )
        else:
            st.caption(
                f"{stats['lines']} 行 · {stats['chars']:,} / {limit:,} 字符"
                + (" · 按 Ctrl+Enter 不会自动提交，请点击下方按钮" if stats["chars"] else "")
            )

        mode: AnalysisMode = st.radio(
            "分析模式",
            options=list(AnalysisMode),
            format_func=lambda value: f"{MODE_ICONS[value]} {MODE_LABELS[value]}",
            horizontal=True,
            key="analysis_mode",
            width="stretch",
        )
        st.caption(MODE_DESCRIPTIONS[mode])

        action_col, clear_col = st.columns([3, 1])
        with action_col:
            analyze_clicked = st.button(
                "🚀 开始分析",
                type="primary",
                key="analyze_button",
                width="stretch",
            )
        with clear_col:
            st.button(
                "清空",
                key="clear_button",
                on_click=_clear_code,
                width="stretch",
            )

        if not str(st.session_state.get("code_input", "")).strip():
            st.caption("请输入代码，或点击上方示例按钮载入内置样例。")

        return analyze_clicked


def _render_report_panel(
    service: AnalysisService,
    settings: Settings,
) -> None:
    st.markdown("#### ② 分析报告")

    result = st.session_state.get("last_result")
    error = st.session_state.get("last_error")

    if result is not None:
        if not _result_matches_current_input(result):
            st.warning(
                "输入代码、语言或分析模式已更改，下方展示的是上一次分析结果。",
                icon="✏️",
            )
            if st.button(
                "🔄 重新分析",
                key="reanalyze_button",
                type="primary",
                width="stretch",
            ):
                _execute_analysis(service, settings)
                st.rerun()
        render_result(result)
        return

    if error is not None:
        render_error(error)
        if st.button(
            "🔄 重试分析",
            key="retry_button",
            type="primary",
            width="stretch",
        ):
            _execute_analysis(service, settings)
            st.rerun()
        return

    render_empty_state()


def main() -> None:
    inject_styles()
    try:
        settings = load_settings()
    except ConfigurationError as exc:
        _render_config_error(exc)

    status = environment_status(settings)
    _init_session()
    render_sidebar(settings, status)
    render_hero()

    service = _get_service(settings)

    input_col, report_col = st.columns([1.02, 0.98], gap="large")
    with input_col:
        analyze_clicked = _render_input_panel(settings)
        if analyze_clicked:
            _execute_analysis(service, settings)

    with report_col:
        _render_report_panel(service, settings)

    render_footer()


if __name__ == "__main__":
    main()
