"""侧边栏：运行状态、配置提示与安全说明。"""

from __future__ import annotations

import html

import streamlit as st

from core.config import (
    PROVIDER_DEMO,
    PROVIDER_OLLAMA,
    STRUCTURED_OUTPUT_NATIVE,
    Settings,
)
from core.service import EnvironmentStatus


def _render_brand() -> None:
    st.markdown(
        """
<div class="ci-brand">
  <div class="ci-brand-mark">CI</div>
  <div>
    <div class="ci-brand-name">CodeInsight</div>
    <div class="ci-brand-tag">智能代码解释与审查</div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


def _status_badge(settings: Settings, status: EnvironmentStatus) -> str:
    if not status.ready:
        return '<span class="ci-badge ci-badge-high">配置异常</span>'
    if settings.provider == PROVIDER_DEMO:
        return '<span class="ci-badge ci-badge-demo">离线演示</span>'
    if settings.provider == PROVIDER_OLLAMA:
        return '<span class="ci-badge ci-badge-info">本地模型</span>'
    return '<span class="ci-badge ci-badge-mode">在线模型</span>'


def _render_status(settings: Settings, status: EnvironmentStatus) -> None:
    st.markdown("#### 运行状态")
    st.markdown(
        f"""
<div class="ci-metric">
  <div class="ci-meta-row" style="margin-bottom:0.35rem;">
    {_status_badge(settings, status)}
  </div>
  <div class="ci-status-headline">{html.escape(status.headline)}</div>
  <div class="ci-status-detail">{html.escape(status.detail)}</div>
</div>
""",
        unsafe_allow_html=True,
    )

    if settings.provider == PROVIDER_DEMO:
        with st.expander("如何接入真实模型？", expanded=False):
            st.markdown("在项目根目录创建 `.env`，写入以下配置后重启应用：")
            st.code(
                "CODEINSIGHT_PROVIDER=openai\n"
                "CODEINSIGHT_API_KEY=sk-your-key\n"
                "CODEINSIGHT_MODEL=gpt-4o-mini\n"
                "# 若使用其他 OpenAI 兼容服务，填写对应 Base URL：\n"
                "CODEINSIGHT_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1",
                language="bash",
            )
            st.caption(
                "也支持 Ollama 本地模型：设置 CODEINSIGHT_PROVIDER=ollama 与 "
                "CODEINSIGHT_MODEL=qwen2.5-coder:7b。"
            )
    elif not status.ready:
        st.error("当前模型配置不可用，请检查 .env 后重启应用。")


def _render_parameters(settings: Settings) -> None:
    st.markdown("#### 运行参数")
    output_mode = (
        "原生结构化输出"
        if settings.structured_output == STRUCTURED_OUTPUT_NATIVE
        else "JSON + Pydantic 校验"
    )
    st.markdown(
        f"""
<div class="ci-note">
  输入上限：<strong>{settings.max_code_chars:,}</strong> 字符<br>
  温度：<strong>{settings.temperature}</strong> · 超时：<strong>{settings.timeout:g}</strong> 秒<br>
  输出方式：<strong>{html.escape(output_mode)}</strong><br>
  传输重试：<strong>{settings.transport_retries}</strong> 次 · 解析修复：<strong>{settings.parse_retries}</strong> 次
</div>
""",
        unsafe_allow_html=True,
    )
    st.caption("以上参数读取自 .env，可通过环境变量覆盖。")


def _render_privacy() -> None:
    st.markdown("#### 隐私提醒")
    st.markdown(
        """
<div class="ci-callout" style="border-color:#fde68a;background:#fffbeb;color:#92400e;">
  🔒 请勿提交密码、密钥、个人信息或其他敏感代码。<br>
  除离线演示外，代码内容会发送至你配置的模型服务。
</div>
""",
        unsafe_allow_html=True,
    )


def _render_about() -> None:
    with st.expander("关于第一版"):
        st.markdown(
            "- 已覆盖四类核心分析：解释、审查、复杂度、测试用例。\n"
            "- 支持 Python / Java / C++ 代码输入与长度校验。\n"
            "- 结构化报告、复制与 Markdown 导出。\n"
            "- 模型失败、超时与解析异常均有明确提示。\n"
            "- 暂不包含用户登录、数据库持久化与代码自动执行。"
        )
        st.caption("分析结果仅供学习参考，不能替代编译器或人工评审。")


def render_sidebar(settings: Settings, status: EnvironmentStatus) -> None:
    with st.sidebar:
        _render_brand()
        _render_status(settings, status)
        st.divider()
        _render_parameters(settings)
        st.divider()
        _render_privacy()
        st.divider()
        _render_about()
        st.caption("CodeInsight · 第一轮开发 · v0.1")
