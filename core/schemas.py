"""结构化报告的数据模型。

四类分析都通过 Pydantic 模型约束输出字段，既作为提示词中的 JSON Schema，
也用于对模型返回结果进行校验。字段描述会由 ``PydanticOutputParser``
注入提示词，因此描述文字应同时面向模型与开发者。
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class ReportModel(BaseModel):
    """报告模型基类：忽略多余字段，去除字符串首尾空白，提升模型输出兼容性。"""

    model_config = ConfigDict(
        extra="ignore",
        str_strip_whitespace=True,
        populate_by_name=True,
    )


class Severity(str, Enum):
    """代码审查问题的严重程度。"""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

    @classmethod
    def _missing_(cls, value: object) -> "Severity | None":
        """兼容模型偶尔输出的中文或大小写变体。"""

        if not isinstance(value, str):
            return None
        aliases = {
            "high": cls.HIGH,
            "medium": cls.MEDIUM,
            "low": cls.LOW,
            "高": cls.HIGH,
            "高优先级": cls.HIGH,
            "严重": cls.HIGH,
            "中": cls.MEDIUM,
            "中等": cls.MEDIUM,
            "中优先级": cls.MEDIUM,
            "低": cls.LOW,
            "低优先级": cls.LOW,
            "轻微": cls.LOW,
        }
        return aliases.get(value.strip().lower())


class Confidence(str, Enum):
    """复杂度分析的置信程度。"""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

    @classmethod
    def _missing_(cls, value: object) -> "Confidence | None":
        if not isinstance(value, str):
            return None
        aliases = {
            "high": cls.HIGH,
            "medium": cls.MEDIUM,
            "low": cls.LOW,
            "确定": cls.HIGH,
            "较确定": cls.HIGH,
            "部分确定": cls.MEDIUM,
            "不确定": cls.LOW,
            "无法确定": cls.LOW,
        }
        return aliases.get(value.strip().lower())


class TestCaseType(str, Enum):
    """测试用例的类别。"""

    NORMAL = "normal"
    BOUNDARY = "boundary"
    INVALID = "invalid"

    @classmethod
    def _missing_(cls, value: object) -> "TestCaseType | None":
        if not isinstance(value, str):
            return None
        aliases = {
            "normal": cls.NORMAL,
            "boundary": cls.BOUNDARY,
            "invalid": cls.INVALID,
            "正常": cls.NORMAL,
            "正常用例": cls.NORMAL,
            "普通": cls.NORMAL,
            "边界": cls.BOUNDARY,
            "边界用例": cls.BOUNDARY,
            "边缘": cls.BOUNDARY,
            "edge": cls.BOUNDARY,
            "异常": cls.INVALID,
            "异常用例": cls.INVALID,
            "非法": cls.INVALID,
        }
        return aliases.get(value.strip().lower())


SEVERITY_LABELS: dict[Severity, str] = {
    Severity.HIGH: "高",
    Severity.MEDIUM: "中",
    Severity.LOW: "低",
}

CONFIDENCE_LABELS: dict[Confidence, str] = {
    Confidence.HIGH: "较确定",
    Confidence.MEDIUM: "部分确定",
    Confidence.LOW: "不确定",
}

TEST_TYPE_LABELS: dict[TestCaseType, str] = {
    TestCaseType.NORMAL: "正常",
    TestCaseType.BOUNDARY: "边界",
    TestCaseType.INVALID: "异常",
}


# ---------------------------------------------------------------------------
# 代码解释（F-07 ~ F-12）
# ---------------------------------------------------------------------------


class KeyStatement(ReportModel):
    location: str = Field(
        description="关键语句所属的函数、类或代码位置标识；无法定位时填写“整段代码”"
    )
    line: int | None = Field(
        default=None,
        ge=1,
        description="关键语句在原始代码中的行号（从 1 开始）；无法确定时为 null",
    )
    snippet: str = Field(description="与说明对应的原始代码片段，保持原样")
    explanation: str = Field(description="该语句的作用及其在整体流程中的意义")


class InputOutputAnalysis(ReportModel):
    inputs: list[str] = Field(
        min_length=1, description="代码期望的输入，每项说明一个输入参数或数据来源"
    )
    outputs: list[str] = Field(
        min_length=1, description="代码产生的结果，每项说明一个返回值、输出语句或副作用"
    )
    notes: str = Field(
        description="输入输出格式、取值范围或必要假设；无特殊约定时可说明“未显式约定”"
    )


class ExplanationReport(ReportModel):
    overall_purpose: str = Field(description="用一段自然语言说明代码的整体功能与用途")
    execution_flow: list[str] = Field(
        min_length=1,
        description="按程序实际执行顺序描述的主要步骤，每项为一个简短步骤",
    )
    key_statements: list[KeyStatement] = Field(
        min_length=1, description="重要变量、函数、循环、条件分支的逐条解释"
    )
    input_output: InputOutputAnalysis = Field(description="输入与输出分析")
    algorithm_idea: str = Field(
        description="代码采用的主要算法或处理思路；若只是普通流程可说明其处理策略"
    )
    assumptions: list[str] = Field(
        default_factory=list,
        description="理解代码时依赖的前提或未在代码中体现的假设，没有则为空数组",
    )


# ---------------------------------------------------------------------------
# 代码审查（F-13 ~ F-20）
# ---------------------------------------------------------------------------


class CodeLocation(ReportModel):
    name: str = Field(
        description="问题所在的函数名、类名或代码区域；无法定位时填写“整段代码”"
    )
    line: int | None = Field(
        default=None,
        ge=1,
        description="问题所在行号（从 1 开始）；只能给出范围或无法确定时为 null",
    )


class ReviewIssue(ReportModel):
    title: str = Field(description="简洁的问题标题")
    category: str = Field(
        description="问题类型，例如逻辑、边界、异常处理、代码质量、性能"
    )
    severity: Severity = Field(
        description="严重程度：high 表示可能导致错误结果、崩溃或越界；"
        "medium 表示特定输入下出错或明显性能问题；low 表示可读性或轻微性能问题"
    )
    location: CodeLocation = Field(description="问题定位信息")
    snippet: str = Field(description="与问题相关的原始代码片段，保持原样")
    reason: str = Field(description="问题产生的原因")
    impact: str = Field(description="可能造成的影响或触发条件")
    suggestion: str = Field(description="具体、可操作的修改建议")
    verification: str = Field(description="验证该问题是否真实存在的方法，例如输入样例或测试")


class ReviewReport(ReportModel):
    summary: str = Field(description="对代码整体风险与主要问题的简要总结")
    issues: list[ReviewIssue] = Field(
        default_factory=list,
        description="发现的潜在问题列表；未发现问题时为空数组并在 summary 中说明",
    )


# ---------------------------------------------------------------------------
# 复杂度分析（F-21 ~ F-24）
# ---------------------------------------------------------------------------


class ComplexityOptimization(ReportModel):
    title: str = Field(description="优化建议的标题")
    current: str = Field(description="当前实现及其复杂度")
    optimized: str = Field(description="优化后的做法及其复杂度")
    explanation: str = Field(description="优化思路说明及其前提条件")


class ComplexityReport(ReportModel):
    time_complexity: str = Field(
        description="时间复杂度，例如 O(n)、O(n log n)；无法可靠分析时写“不确定”并说明原因"
    )
    space_complexity: str = Field(
        description="额外空间复杂度，说明是否计入输入数据与递归调用栈"
    )
    confidence: Confidence = Field(description="结论的置信程度")
    derivation: list[str] = Field(
        min_length=1, description="复杂度推导过程，逐步说明循环、递归或关键操作的开销"
    )
    assumptions: list[str] = Field(
        default_factory=list, description="结论成立所依赖的前提或假设，没有则为空数组"
    )
    optimizations: list[ComplexityOptimization] = Field(
        default_factory=list, description="可行的优化建议；没有明显优化空间时为空数组"
    )


# ---------------------------------------------------------------------------
# 测试用例生成（F-25 ~ F-29）
# ---------------------------------------------------------------------------


class TestCase(ReportModel):
    case_type: TestCaseType = Field(description="用例类别：normal 正常、boundary 边界、invalid 异常")
    title: str = Field(description="简短的用例名称")
    input: str = Field(description="具体的测试输入，尽可能与代码的接口和输入格式一致")
    expected: str = Field(description="预期输出、返回值或预期行为")
    purpose: str = Field(description="该用例验证的行为或覆盖的风险点")
    notes: str = Field(default="", description="执行前置条件、补充说明；没有则为空字符串")


class TestReport(ReportModel):
    function_signature: str = Field(
        description="被测函数或程序的签名，例如 sum_array(arr)；无法识别时说明入口"
    )
    assumptions: list[str] = Field(
        default_factory=list, description="生成测试用例所依赖的接口约定或假设"
    )
    cases: list[TestCase] = Field(
        min_length=1, description="测试用例列表，至少覆盖正常、边界和异常场景（若适用）"
    )
    coverage_summary: str = Field(description="说明这些用例共同覆盖了哪些行为与风险")
