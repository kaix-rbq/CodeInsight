"""把结构化报告渲染为 Markdown，用于复制、导出与测试报告。

同一份 Markdown 既可供用户下载，也可以在界面“复制结果”标签中直接复制。
"""

from __future__ import annotations

from datetime import datetime

from core.modes import MODE_LABELS, AnalysisMode
from core.schemas import (
    CONFIDENCE_LABELS,
    SEVERITY_LABELS,
    TEST_TYPE_LABELS,
    ComplexityReport,
    ExplanationReport,
    ReportModel,
    ReviewReport,
    TestReport,
)

_LANGUAGE_HINTS: dict[str, str] = {
    "Python": "python",
    "Java": "java",
    "C++": "cpp",
}

_LANGUAGE_ALIASES: dict[str, str] = {
    "Python": "python",
    "Java": "java",
    "C++": "cpp",
    "cpp": "cpp",
    "c++": "cpp",
    "java": "java",
    "python": "python",
    "": "",
}


def _fenced(code: str, language_hint: str = "") -> str:
    fence = "````" if "```" in code else "```"
    return f"{fence}{language_hint}\n{code}\n{fence}"


def _cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", "<br>")


def _bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items) if items else "- 无"


def _section_header(index: int, title: str) -> str:
    return f"## {index}、{title}"


def _build_header(
    mode: AnalysisMode,
    *,
    language: str,
    provider: str,
    model: str,
    demo: bool,
    created_at: datetime,
    elapsed_ms: int,
    code: str,
) -> str:
    lines_count = code.count("\n") + 1 if code else 0
    lines = [
        "# CodeInsight 分析报告",
        "",
        f"- **分析模式**：{MODE_LABELS[mode]}",
        f"- **编程语言**：{language}",
        f"- **模型服务**：{provider}",
        f"- **模型**：{model}",
        f"- **生成时间**：{created_at.strftime('%Y-%m-%d %H:%M:%S')}",
        f"- **分析耗时**：{elapsed_ms / 1000:.2f} 秒",
        f"- **代码规模**：{lines_count} 行 / {len(code)} 字符",
    ]
    if demo:
        lines.append("")
        lines.append(
            "> ⚠️ **离线演示模式**：本报告为内置示例代码的预置结果，未调用大模型，"
            "仅用于展示报告结构，请勿视为对自定义代码的真实分析。"
        )
    return "\n".join(lines)


def _render_explanation(report: ExplanationReport) -> str:
    key_rows = "\n".join(
        "| {location} | {line} | {snippet} | {explanation} |".format(
            location=_cell(item.location),
            line=item.line if item.line is not None else "—",
            snippet=_cell(f"`{item.snippet}`"),
            explanation=_cell(item.explanation),
        )
        for item in report.key_statements
    )
    return "\n".join(
        [
            _section_header(2, "代码解释"),
            "",
            "### 整体功能",
            "",
            report.overall_purpose,
            "",
            "### 执行流程",
            "",
            "\n".join(
                f"{index}. {step}"
                for index, step in enumerate(report.execution_flow, start=1)
            ),
            "",
            "### 关键语句",
            "",
            "| 位置 | 行号 | 代码片段 | 说明 |",
            "|---|---|---|---|",
            key_rows,
            "",
            "### 输入与输出",
            "",
            "**输入**",
            "",
            _bullets(report.input_output.inputs),
            "",
            "**输出**",
            "",
            _bullets(report.input_output.outputs),
            "",
            f"**补充说明**：{report.input_output.notes}",
            "",
            "### 算法思路",
            "",
            report.algorithm_idea,
            "",
            "### 分析假设",
            "",
            _bullets(report.assumptions),
            "",
        ]
    )


def _render_review(report: ReviewReport) -> str:
    if report.issues:
        overview = "\n".join(
            "| {index} | {title} | {category} | {severity} | {location} |".format(
                index=index,
                title=_cell(issue.title),
                category=_cell(issue.category),
                severity=SEVERITY_LABELS[issue.severity],
                location=_cell(issue.location.name)
                + (f"（第 {issue.location.line} 行）" if issue.location.line else ""),
            )
            for index, issue in enumerate(report.issues, start=1)
        )
    else:
        overview = "| — | 未发现潜在问题 | — | — | — |"

    detail_blocks: list[str] = []
    for index, issue in enumerate(report.issues, start=1):
        detail_blocks.append(
            "\n".join(
                [
                    f"### 问题 {index}：{issue.title}",
                    "",
                    f"- **类型**：{issue.category}",
                    f"- **严重程度**：{SEVERITY_LABELS[issue.severity]}",
                    f"- **位置**：{issue.location.name}"
                    + (f"（第 {issue.location.line} 行）" if issue.location.line else ""),
                    "",
                    "**相关代码**",
                    "",
                    _fenced(issue.snippet),
                    "",
                    f"**问题原因**：{issue.reason}",
                    "",
                    f"**可能影响**：{issue.impact}",
                    "",
                    f"**修改建议**：{issue.suggestion}",
                    "",
                    f"**验证方法**：{issue.verification}",
                    "",
                ]
            )
        )

    return "\n".join(
        [
            _section_header(2, "代码审查"),
            "",
            "### 审查总结",
            "",
            report.summary,
            "",
            "### 问题概览",
            "",
            "| # | 问题 | 类型 | 严重程度 | 位置 |",
            "|---|---|---|---|---|",
            overview,
            "",
            "### 问题详情",
            "",
            "\n".join(detail_blocks) if detail_blocks else "未发现潜在问题。",
            "> 以上为静态阅读发现的潜在问题，不等同于实际运行验证结果。",
            "",
        ]
    )


def _render_complexity(report: ComplexityReport) -> str:
    optimization_blocks: list[str] = []
    for index, item in enumerate(report.optimizations, start=1):
        optimization_blocks.append(
            "\n".join(
                [
                    f"#### 优化 {index}：{item.title}",
                    "",
                    f"- **当前实现**：{item.current}",
                    f"- **优化后**：{item.optimized}",
                    f"- **说明**：{item.explanation}",
                    "",
                ]
            )
        )

    return "\n".join(
        [
            _section_header(2, "复杂度分析"),
            "",
            "| 项目 | 结论 |",
            "|---|---|",
            f"| 时间复杂度 | {_cell(report.time_complexity)} |",
            f"| 空间复杂度 | {_cell(report.space_complexity)} |",
            f"| 置信程度 | {CONFIDENCE_LABELS[report.confidence]} |",
            "",
            "### 推导过程",
            "",
            "\n".join(
                f"{index}. {step}"
                for index, step in enumerate(report.derivation, start=1)
            ),
            "",
            "### 前提与假设",
            "",
            _bullets(report.assumptions),
            "",
            "### 优化建议",
            "",
            "\n".join(optimization_blocks) if optimization_blocks else "暂无明显优化空间。",
            "> 复杂度分析属于静态推理，不等同于实际运行性能测试。",
            "",
        ]
    )


def _render_tests(report: TestReport) -> str:
    rows = "\n".join(
        "| {type} | {title} | {input} | {expected} | {purpose} |".format(
            type=TEST_TYPE_LABELS[case.case_type],
            title=_cell(case.title),
            input=_cell(case.input),
            expected=_cell(case.expected),
            purpose=_cell(case.purpose),
        )
        for case in report.cases
    )
    note_blocks = [
        f"- **{case.title}**：{case.notes}"
        for case in report.cases
        if case.notes
    ]

    return "\n".join(
        [
            _section_header(2, "测试用例"),
            "",
            f"**被测接口**：`{report.function_signature}`",
            "",
            "### 用例列表",
            "",
            "| 测试类型 | 用例名称 | 输入 | 预期结果 | 测试目的 |",
            "|---|---|---|---|---|",
            rows,
            "",
            "### 覆盖说明",
            "",
            report.coverage_summary,
            "",
            "### 生成假设",
            "",
            _bullets(report.assumptions),
            "",
            "### 用例备注",
            "",
            "\n".join(note_blocks) if note_blocks else "- 无",
            "",
        ]
    )


def report_to_markdown(
    mode: AnalysisMode,
    report: ReportModel,
    *,
    code: str,
    language: str,
    provider: str,
    model: str,
    demo: bool,
    created_at: datetime,
    elapsed_ms: int,
) -> str:
    """生成完整的 Markdown 报告。"""

    header = _build_header(
        mode,
        language=language,
        provider=provider,
        model=model,
        demo=demo,
        created_at=created_at,
        elapsed_ms=elapsed_ms,
        code=code,
    )

    if mode is AnalysisMode.EXPLAIN:
        body = _render_explanation(report)  # type: ignore[arg-type]
    elif mode is AnalysisMode.REVIEW:
        body = _render_review(report)  # type: ignore[arg-type]
    elif mode is AnalysisMode.COMPLEXITY:
        body = _render_complexity(report)  # type: ignore[arg-type]
    else:
        body = _render_tests(report)  # type: ignore[arg-type]

    code_section = "\n".join(
        [
            _section_header(1, "输入代码"),
            "",
            _fenced(code, _LANGUAGE_HINTS.get(language, "")),
            "",
        ]
    )

    return "\n".join([header, "", code_section, body]).strip() + "\n"


def language_hint(language: str) -> str:
    """返回用于代码高亮的语言标识。"""

    return _LANGUAGE_ALIASES.get(language, "")
