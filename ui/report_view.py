"""分析报告的结构化展示。"""

from __future__ import annotations

import html

import streamlit as st

from core.errors import CodeInsightError, ResultParseError
from core.modes import MODE_ICONS, MODE_LABELS
from core.reporting import language_hint
from core.schemas import (
    CONFIDENCE_LABELS,
    SEVERITY_LABELS,
    TEST_TYPE_LABELS,
    ComplexityReport,
    ExplanationReport,
    ReviewReport,
    Severity,
    TestReport,
)
from core.service import AnalysisResult

_SEVERITY_ICONS: dict[Severity, str] = {
    Severity.HIGH: "🔴",
    Severity.MEDIUM: "🟠",
    Severity.LOW: "🟡",
}


def _badge(text: str, kind: str) -> str:
    return f'<span class="ci-badge ci-badge-{kind}">{html.escape(text)}</span>'


def _cell(value: object) -> str:
    return html.escape(str(value)).replace("\n", "<br>")


def _render_meta(result: AnalysisResult) -> None:
    chips = [
        _badge(f"{MODE_ICONS[result.mode]} {MODE_LABELS[result.mode]}", "mode"),
        _badge(result.language, "info"),
    ]
    if result.demo:
        chips.append(_badge("离线演示", "demo"))
    st.markdown(f'<div class="ci-meta-row">{"".join(chips)}</div>', unsafe_allow_html=True)
    st.caption(
        f"生成于 {result.created_at.strftime('%Y-%m-%d %H:%M:%S')} · "
        f"耗时 {result.elapsed_ms / 1000:.2f} 秒 · "
        f"服务：{result.provider} · 模型：{result.model}"
    )
    if result.demo:
        sample = f"（样例：{result.demo_sample_title}）" if result.demo_sample_title else ""
        st.warning(
            "当前为离线演示模式：本报告是内置示例代码的预置结果，未调用大模型。"
            f"{sample}配置 API Key 后可分析自定义代码。",
            icon="⚠️",
        )


def _render_explanation(report: ExplanationReport, language: str) -> None:
    st.markdown("#### 整体功能")
    st.markdown(report.overall_purpose)

    st.markdown("#### 执行流程")
    steps = "".join(f"<li>{html.escape(step)}</li>" for step in report.execution_flow)
    st.markdown(f'<ol class="ci-steps">{steps}</ol>', unsafe_allow_html=True)

    st.markdown("#### 关键语句")
    for index, item in enumerate(report.key_statements):
        line_text = f" · 第 {item.line} 行" if item.line is not None else ""
        with st.expander(
            f"{item.location}{line_text}",
            expanded=index == 0,
        ):
            st.code(item.snippet, language=language_hint(language))
            st.markdown(item.explanation)

    st.markdown("#### 输入与输出")
    input_col, output_col = st.columns(2)
    with input_col:
        st.markdown("**输入**")
        for item in report.input_output.inputs:
            st.markdown(f"- {item}")
    with output_col:
        st.markdown("**输出**")
        for item in report.input_output.outputs:
            st.markdown(f"- {item}")
    st.caption(f"补充说明：{report.input_output.notes}")

    st.markdown("#### 算法思路")
    st.markdown(report.algorithm_idea)

    st.markdown("#### 分析假设")
    if report.assumptions:
        for item in report.assumptions:
            st.markdown(f"- {item}")
    else:
        st.caption("无额外假设。")


def _render_review(report: ReviewReport) -> None:
    st.markdown("#### 审查总结")
    st.markdown(report.summary)

    counts = {
        severity: sum(1 for issue in report.issues if issue.severity is severity)
        for severity in Severity
    }
    metric_cols = st.columns(3)
    for col, severity in zip(metric_cols, [Severity.HIGH, Severity.MEDIUM, Severity.LOW]):
        with col:
            st.markdown(
                f"""
<div class="ci-metric">
  <div class="ci-metric-label">{_SEVERITY_ICONS[severity]} {SEVERITY_LABELS[severity]}优先级</div>
  <div class="ci-metric-value">{counts[severity]} 个</div>
  <div class="ci-metric-sub">潜在问题数量</div>
</div>
""",
                unsafe_allow_html=True,
            )

    st.markdown(f"#### 潜在问题（{len(report.issues)}）")
    if not report.issues:
        st.success("在本次静态审查范围内未发现明显的潜在问题。")
    else:
        for index, issue in enumerate(report.issues):
            label = (
                f"{_SEVERITY_ICONS[issue.severity]} "
                f"{SEVERITY_LABELS[issue.severity]}优先级 · {issue.title}"
            )
            with st.expander(label, expanded=index == 0):
                location = issue.location.name
                if issue.location.line is not None:
                    location += f"（第 {issue.location.line} 行）"
                st.markdown(
                    '<div class="ci-meta-row">'
                    + _badge(f"类型：{issue.category}", "type")
                    + _badge(f"严重程度：{SEVERITY_LABELS[issue.severity]}", issue.severity.value)
                    + _badge(location, "info")
                    + "</div>",
                    unsafe_allow_html=True,
                )
                st.code(issue.snippet, language="")
                st.markdown(f"**问题原因**：{issue.reason}")
                st.markdown(f"**可能影响**：{issue.impact}")
                st.markdown(f"**修改建议**：{issue.suggestion}")
                st.markdown(f"**验证方法**：{issue.verification}")

    st.info(
        "以上为模型静态阅读发现的潜在问题，不等同于实际运行验证结果。"
        "请结合测试用例、编译器和人工评审确认。",
        icon="ℹ️",
    )


def _render_complexity(report: ComplexityReport) -> None:
    metric_cols = st.columns(3)
    metrics = [
        ("时间复杂度", report.time_complexity, "随输入规模增长的趋势"),
        ("空间复杂度", report.space_complexity, "额外空间与递归调用栈"),
        ("置信程度", CONFIDENCE_LABELS[report.confidence], "基于静态推理的把握程度"),
    ]
    for col, (label, value, sub) in zip(metric_cols, metrics):
        with col:
            st.markdown(
                f"""
<div class="ci-metric">
  <div class="ci-metric-label">{html.escape(label)}</div>
  <div class="ci-metric-value">{html.escape(value)}</div>
  <div class="ci-metric-sub">{html.escape(sub)}</div>
</div>
""",
                unsafe_allow_html=True,
            )

    st.markdown("#### 推导过程")
    steps = "".join(f"<li>{html.escape(step)}</li>" for step in report.derivation)
    st.markdown(f'<ol class="ci-steps">{steps}</ol>', unsafe_allow_html=True)

    st.markdown("#### 前提与假设")
    if report.assumptions:
        for item in report.assumptions:
            st.markdown(f"- {item}")
    else:
        st.caption("未声明额外前提。")

    st.markdown("#### 优化建议")
    if not report.optimizations:
        st.caption("在当前算法框架下未发现明显的渐进复杂度优化空间。")
    for index, item in enumerate(report.optimizations, start=1):
        with st.container(border=True):
            st.markdown(f"**优化 {index}：{item.title}**")
            current_col, optimized_col = st.columns(2)
            with current_col:
                st.markdown("**当前实现**")
                st.markdown(item.current)
            with optimized_col:
                st.markdown("**优化后**")
                st.markdown(item.optimized)
            st.caption(item.explanation)

    st.caption("复杂度分析属于静态推理，不等同于实际运行性能测试。")


def _render_tests(report: TestReport) -> None:
    st.markdown("#### 被测接口")
    st.code(report.function_signature, language="")

    st.markdown(f"#### 测试用例（{len(report.cases)}）")
    rows: list[str] = []
    for case in report.cases:
        rows.append(
            "<tr>"
            f"<td>{_badge(TEST_TYPE_LABELS[case.case_type], 'type')}</td>"
            f"<td><strong>{_cell(case.title)}</strong></td>"
            f"<td><code>{_cell(case.input)}</code></td>"
            f"<td>{_cell(case.expected)}</td>"
            f"<td>{_cell(case.purpose)}</td>"
            "</tr>"
        )
    st.markdown(
        """
<table class="ci-table">
  <thead>
    <tr><th>类型</th><th>用例</th><th>输入</th><th>预期结果</th><th>测试目的</th></tr>
  </thead>
  <tbody>
"""
        + "".join(rows)
        + """
  </tbody>
</table>
""",
        unsafe_allow_html=True,
    )

    notes = [case for case in report.cases if case.notes]
    if notes:
        with st.expander(f"用例备注（{len(notes)}）"):
            for case in notes:
                st.markdown(f"**{case.title}**：{case.notes}")

    st.markdown("#### 覆盖说明")
    st.markdown(
        f'<div class="ci-callout">{html.escape(report.coverage_summary)}</div>',
        unsafe_allow_html=True,
    )

    st.markdown("#### 生成假设")
    if report.assumptions:
        for item in report.assumptions:
            st.markdown(f"- {item}")
    else:
        st.caption("无额外假设。")


def _render_export(result: AnalysisResult) -> None:
    filename = (
        f"codeinsight_{result.mode.value}_{result.created_at.strftime('%Y%m%d_%H%M%S')}.md"
    )
    st.download_button(
        "⬇️ 下载 Markdown 报告",
        data=result.markdown,
        file_name=filename,
        mime="text/markdown",
        width="stretch",
    )
    st.caption("也可以直接点击下方代码块右上角的复制按钮。")
    st.code(result.markdown, language="markdown")


def _render_raw(result: AnalysisResult) -> None:
    st.markdown("#### 结构化数据")
    st.json(result.report.model_dump(mode="json"), expanded=True)
    if result.raw_output:
        with st.expander("模型原始输出"):
            st.code(result.raw_output, language="json")
    st.caption(
        f"模式：{result.mode.value} · 语言：{result.language} · "
        f"提供方：{result.provider} · 模型：{result.model}"
    )


def render_result(result: AnalysisResult) -> None:
    """渲染完整结果（元信息 + 三个标签页）。"""

    _render_meta(result)
    report_tab, export_tab, raw_tab = st.tabs(
        ["📋 结构化报告", "📄 复制 / 导出", "🧾 原始数据"]
    )
    with report_tab:
        if result.mode.value == "explain":
            _render_explanation(result.report, result.language)  # type: ignore[arg-type]
        elif result.mode.value == "review":
            _render_review(result.report)  # type: ignore[arg-type]
        elif result.mode.value == "complexity":
            _render_complexity(result.report)  # type: ignore[arg-type]
        else:
            _render_tests(result.report)  # type: ignore[arg-type]
    with export_tab:
        _render_export(result)
    with raw_tab:
        _render_raw(result)


def render_error(error: CodeInsightError) -> None:
    """展示可恢复错误及排查信息。"""

    st.markdown(
        '<div class="ci-meta-row">'
        + _badge("分析失败", "high")
        + "</div>",
        unsafe_allow_html=True,
    )
    st.error(str(error))
    if isinstance(error, ResultParseError) and error.raw_output:
        with st.expander("查看模型原始输出"):
            st.code(error.raw_output, language="json")
    if error.detail:
        with st.expander("技术详情（供排查）"):
            st.code(error.detail, language="text")
    st.caption("输入内容仍然保留，可以调整配置或代码后重试。")


def render_unexpected_error(error: Exception) -> None:
    st.error("分析过程中出现未预期错误，页面已安全降级，请重试或查看详情。")
    with st.expander("技术详情"):
        st.code(f"{type(error).__name__}: {error}", language="text")


def render_empty_state() -> None:
    """尚未分析时的引导区域。"""

    st.markdown(
        """
<div class="ci-callout">
  <strong>报告将在这里生成。</strong><br>
  推荐流程：点击左侧示例按钮载入代码 → 选择分析模式 → 点击「开始分析」。
  四种模式都返回结构化报告，可在「复制 / 导出」标签中获取 Markdown。
</div>
""",
        unsafe_allow_html=True,
    )
    st.markdown("#### 支持的分析模式")
    modes = [
        ("📖", "代码解释", "整体功能、执行流程、关键语句、输入输出与算法思路。"),
        ("🔍", "代码审查", "逻辑、边界、异常、质量与性能问题，按严重程度分类并给出修复建议。"),
        ("📈", "复杂度分析", "时间与空间复杂度、推导过程、成立前提与优化方向。"),
        ("🧪", "测试用例", "正常、边界与异常用例，给出预期结果与覆盖目的。"),
    ]
    for start in range(0, len(modes), 2):
        cols = st.columns(2)
        for col, (icon, title, desc) in zip(cols, modes[start : start + 2]):
            with col:
                st.markdown(
                    f"""
<div class="ci-metric">
  <div class="ci-metric-value">{icon} {html.escape(title)}</div>
  <div class="ci-metric-sub">{html.escape(desc)}</div>
</div>
""",
                    unsafe_allow_html=True,
                )
    st.caption("提示：模型输出可能存在偏差，请结合运行结果与人工评审判断。")
