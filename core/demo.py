"""离线演示模式的内置样例与预置报告。

当未配置在线模型（或显式设置 provider=demo）时，界面可以加载三份内置示例代码，
并直接查看预先编写、经过 Pydantic 校验的报告。此模式**不会调用大模型**，
演示时会明确提示；自定义代码需要配置模型服务后才能分析。
"""

from __future__ import annotations

from dataclasses import dataclass
from textwrap import dedent

from core.errors import DemoNotAvailableError
from core.modes import AnalysisMode
from core.schemas import (
    CodeLocation,
    ComplexityOptimization,
    ComplexityReport,
    Confidence,
    ExplanationReport,
    InputOutputAnalysis,
    KeyStatement,
    ReportModel,
    ReviewIssue,
    ReviewReport,
    Severity,
    TestCase,
    TestCaseType,
    TestReport,
)
from core.validation import normalize_code

PYTHON_CODE = dedent(
    """\
    def find_two_sum(nums, target):
        \"\"\"在整数数组 nums 中查找和为 target 的两个元素，返回其下标。\"\"\"
        for i in range(len(nums)):
            for j in range(i + 1, len(nums)):
                if nums[i] + nums[j] == target:
                    return [i, j]
        return None
    """
)

JAVA_CODE = dedent(
    """\
    public class ArrayStats {

        public static double average(int[] values) {
            int sum = 0;
            for (int value : values) {
                sum += value;
            }
            return sum / values.length;
        }

        public static int max(int[] values) {
            int best = 0;
            for (int value : values) {
                if (value > best) {
                    best = value;
                }
            }
            return best;
        }
    }
    """
)

CPP_CODE = dedent(
    """\
    #include <iostream>
    #include <vector>
    using namespace std;

    int binarySearch(const vector<int>& arr, int target) {
        int left = 0, right = arr.size() - 1;
        while (left <= right) {
            int mid = (left + right) / 2;
            if (arr[mid] == target) return mid;
            if (arr[mid] < target) left = mid + 1;
            else right = mid - 1;
        }
        return -1;
    }

    int main() {
        vector<int> arr = {1, 3, 5, 7, 9};
        cout << binarySearch(arr, 7) << endl;
        return 0;
    }
    """
)


def _python_explanation() -> ExplanationReport:
    return ExplanationReport(
        overall_purpose=(
            "函数 find_two_sum 在整数数组 nums 中寻找两个不同下标 i、j，使"
            " nums[i] + nums[j] 等于 target，并返回这两个下标组成的列表；"
            "找不到时返回 None。"
        ),
        execution_flow=[
            "遍历下标 i，从 0 到 len(nums) - 1，作为第一个加数的位置。",
            "对每个 i，再遍历其后的下标 j（从 i + 1 开始），避免重复使用同一元素。",
            "判断 nums[i] + nums[j] 是否等于 target。",
            "一旦相等，立即返回 [i, j]。",
            "两层循环结束后仍未找到，返回 None。",
        ],
        key_statements=[
            KeyStatement(
                location="find_two_sum",
                line=1,
                snippet="def find_two_sum(nums, target):",
                explanation="定义函数并声明两个参数：待查找的整数数组 nums 与目标和 target。",
            ),
            KeyStatement(
                location="find_two_sum",
                line=3,
                snippet="for i in range(len(nums)):",
                explanation="外层循环枚举第一个元素的下标；len(nums) 在循环开始时即确定。",
            ),
            KeyStatement(
                location="find_two_sum",
                line=4,
                snippet="for j in range(i + 1, len(nums)):",
                explanation="内层循环只检查 i 之后的元素，保证两个下标不同且不重复组合。",
            ),
            KeyStatement(
                location="find_two_sum",
                line=5,
                snippet="if nums[i] + nums[j] == target:",
                explanation="核心判断：检查当前两个元素之和是否等于目标值。",
            ),
            KeyStatement(
                location="find_two_sum",
                line=6,
                snippet="return [i, j]",
                explanation="找到第一组满足条件的下标后立即返回，结束整个函数。",
            ),
            KeyStatement(
                location="find_two_sum",
                line=7,
                snippet="return None",
                explanation="所有组合都不满足时返回 None，表示无解。",
            ),
        ],
        input_output=InputOutputAnalysis(
            inputs=[
                "nums：整数数组（列表），函数会读取其长度并按下标访问元素。",
                "target：整数目标值，用于与两个元素之和比较。",
            ],
            outputs=[
                "存在解时返回包含两个下标的列表 [i, j]，其中 i < j。",
                "不存在解时返回 None。",
            ],
            notes=(
                "函数未显式约定空数组、元素不足两个或参数类型非法的行为；"
                "重复元素允许使用两次，但必须是不同下标。"
            ),
        ),
        algorithm_idea=(
            "采用枚举所有下标组合的暴力解法：固定第一个下标后，只在其后寻找第二个下标，"
            "从而将组合数控制在 n(n-1)/2 次比较，思路直接但时间复杂度为 O(n²)。"
        ),
        assumptions=[
            "nums 是支持 len() 与下标访问的整数序列。",
            "每个元素最多被使用一次，即两个下标必须不同。",
            "返回任意一组满足条件的解即可，未约定多组解时的选择顺序。",
        ],
    )


def _python_review() -> ReviewReport:
    return ReviewReport(
        summary=(
            "整体实现可直接用于小规模数据，未发现必然导致崩溃的确定性问题。"
            "主要风险集中在 O(n²) 的时间开销，以及空输入、多解和非法参数缺少明确约定。"
        ),
        issues=[
            ReviewIssue(
                title="双重循环导致 O(n²) 时间开销",
                category="性能",
                severity=Severity.MEDIUM,
                location=CodeLocation(name="find_two_sum", line=3),
                snippet="for i in range(len(nums)):\n        for j in range(i + 1, len(nums)):",
                reason=(
                    "外层循环遍历每个下标，内层循环再次遍历其后的所有元素，"
                    "比较次数约为 n(n-1)/2。"
                ),
                impact=(
                    "数组较大时耗时快速增长，例如 n=10^5 时比较次数可达数十亿级，"
                    "无法满足常见在线评测的时间限制。"
                ),
                suggestion=(
                    "使用哈希表记录已访问元素与下标，对每个 nums[i] 查找 target - nums[i]，"
                    "将平均查找代价降为 O(1)，整体变为一次遍历 O(n)。"
                ),
                verification=(
                    "构造长度递增的数组，统计比较次数或耗时，观察是否接近平方级增长；"
                    "再与哈希表实现对比结果是否一致。"
                ),
            ),
            ReviewIssue(
                title="空数组或元素不足时静默返回 None",
                category="边界",
                severity=Severity.LOW,
                location=CodeLocation(name="find_two_sum", line=7),
                snippet="return None",
                reason=(
                    "函数没有区分“输入非法”和“确实无解”，空数组与单元素输入都会走同一返回路径。"
                ),
                impact=(
                    "调用方无法判断是输入数据不足还是数组中不存在答案，可能掩盖上游数据错误。"
                ),
                suggestion=(
                    "在文档或返回值中区分输入非法与无解，例如抛出 ValueError，"
                    "或返回包含状态的结果对象；若需保持兼容，至少补充输入校验说明。"
                ),
                verification=(
                    "分别传入 []、[5] 和 [1, 2]（target=10），确认返回值均为 None，"
                    "并检查调用方是否依赖该语义。"
                ),
            ),
            ReviewIssue(
                title="多组解时返回顺序未定义",
                category="逻辑",
                severity=Severity.LOW,
                location=CodeLocation(name="find_two_sum", line=6),
                snippet="return [i, j]",
                reason=(
                    "遇到第一组满足条件的组合立即返回，结果取决于遍历顺序；"
                    "存在重复元素或多组解时没有约定返回哪一组。"
                ),
                impact=(
                    "同一输入在不同实现或代码调整后可能得到不同下标，"
                    "使依赖具体下标的测试变得脆弱。"
                ),
                suggestion=(
                    "在文档中明确“返回按下标从小到大枚举到的第一组解”，并在测试中断言该顺序；"
                    "如业务需要全部解，应收集所有组合而不是立即返回。"
                ),
                verification=(
                    "使用 nums=[1, 2, 3, 4]、target=5，检查返回 [0, 3]，再与文档约定比对。"
                ),
            ),
            ReviewIssue(
                title="未校验参数类型与元素类型",
                category="异常处理",
                severity=Severity.LOW,
                location=CodeLocation(name="find_two_sum", line=3),
                snippet="for i in range(len(nums)):",
                reason=(
                    "len(nums) 要求 nums 支持长度查询；传入 None 或非序列会抛出 TypeError，"
                    "元素若不是数字还可能在相加时产生意外行为。"
                ),
                impact=(
                    "非法输入以原始异常形式暴露，调用方缺少明确的错误契约。"
                ),
                suggestion=(
                    "在函数入口校验 nums 为序列且元素为整数，非法时抛出带说明的 ValueError 或 TypeError。"
                ),
                verification=(
                    "传入 nums=None 或 nums=['a', 'b'] 观察异常类型，确认错误信息是否清晰。"
                ),
            ),
        ],
    )


def _python_complexity() -> ComplexityReport:
    return ComplexityReport(
        time_complexity="O(n²)，其中 n = len(nums)。",
        space_complexity="O(1)（不计输入数组；返回的两个下标视为常数空间）。",
        confidence=Confidence.HIGH,
        derivation=[
            "外层循环 i 从 0 到 n-1，共执行 n 次。",
            "当 i 固定时，内层循环从 i+1 到 n-1，执行 n-i-1 次。",
            "总比较次数为 (n-1) + (n-2) + … + 1 = n(n-1)/2。",
            "按大 O 记号保留最高阶项并忽略常数因子，得到 O(n²)。",
            "除循环变量和常数长度的返回列表外，没有依赖输入规模的额外存储，因此额外空间为 O(1)。",
        ],
        assumptions=[
            "n 表示输入数组 nums 的元素个数。",
            "len()、下标访问与整数加法均视为 O(1) 操作。",
            "不计入输入数组本身占用的空间。",
            "返回的 [i, j] 列表长度固定为 2，视为常数空间。",
        ],
        optimizations=[
            ComplexityOptimization(
                title="使用哈希表将查找降为 O(n)",
                current="双重循环枚举所有下标组合，时间 O(n²)，额外空间 O(1)。",
                optimized="遍历一次数组，用哈希表保存 value → index；对每个元素查找 target - 当前值，时间 O(n)，额外空间 O(n)。",
                explanation=(
                    "典型的以空间换时间。需要注意重复值只保留首次出现的下标，"
                    "并保证不把当前元素自身当作答案。"
                ),
            )
        ],
    )


def _python_tests() -> TestReport:
    return TestReport(
        function_signature="find_two_sum(nums, target) -> list[int] | None",
        assumptions=[
            "输入 nums 为整数列表，target 为整数。",
            "题目约定每个有效输入至多需要返回一组解，返回任意一组即可。",
            "返回 None 表示无解，而非输入非法。",
        ],
        cases=[
            TestCase(
                case_type=TestCaseType.NORMAL,
                title="存在一组解",
                input="nums = [2, 7, 11, 15]，target = 9",
                expected="[0, 1]",
                purpose="验证基本查找逻辑：2 + 7 = 9，返回对应下标。",
                notes="假定输入恰好存在一组解。",
            ),
            TestCase(
                case_type=TestCaseType.NORMAL,
                title="重复元素",
                input="nums = [3, 3]，target = 6",
                expected="[0, 1]",
                purpose="验证同一元素不会使用两次，但值相同的不同下标可以组成答案。",
            ),
            TestCase(
                case_type=TestCaseType.BOUNDARY,
                title="空数组",
                input="nums = []，target = 5",
                expected="None",
                purpose="检查空输入处理，确认不会发生下标越界。",
            ),
            TestCase(
                case_type=TestCaseType.BOUNDARY,
                title="单元素",
                input="nums = [5]，target = 5",
                expected="None",
                purpose="检查元素不足两个时的返回值。",
            ),
            TestCase(
                case_type=TestCaseType.BOUNDARY,
                title="无解",
                input="nums = [1, 2]，target = 10",
                expected="None",
                purpose="验证遍历完所有组合后正确返回 None。",
            ),
            TestCase(
                case_type=TestCaseType.INVALID,
                title="非序列输入",
                input="nums = None，target = 5",
                expected="抛出 TypeError（len(None) 不可用）",
                purpose="验证非法参数类型是否给出明确错误。",
                notes="当前实现未做显式类型校验，异常来自内置函数。",
            ),
        ],
        coverage_summary=(
            "覆盖正常有解、重复元素、空数组、单元素、无解与非法参数，"
            "验证返回值约定和边界行为；未覆盖大规模数组下的性能表现。"
        ),
    )


def _java_explanation() -> ExplanationReport:
    return ExplanationReport(
        overall_purpose=(
            "ArrayStats 提供两个静态工具方法：average 计算整型数组的平均值，"
            "max 找出数组中的最大值。两个方法都通过一次线性的遍历完成统计，且不修改输入数组。"
        ),
        execution_flow=[
            "调用 average 时，先把累加变量 sum 初始化为 0。",
            "使用增强 for 循环依次访问 values 的每个元素，并累加到 sum。",
            "average 返回 sum 除以数组长度的结果。",
            "调用 max 时，先把当前最大值 best 初始化为 0。",
            "遍历 values，遇到比 best 更大的元素就更新 best。",
            "遍历结束后 max 返回 best。",
        ],
        key_statements=[
            KeyStatement(
                location="ArrayStats.average",
                line=3,
                snippet="public static double average(int[] values) {",
                explanation="静态方法接收 int 数组并声明返回 double 类型的平均值。",
            ),
            KeyStatement(
                location="ArrayStats.average",
                line=4,
                snippet="int sum = 0;",
                explanation="使用 int 累加所有元素；当元素和超过 int 上限时可能溢出。",
            ),
            KeyStatement(
                location="ArrayStats.average",
                line=6,
                snippet="sum += value;",
                explanation="把当前元素累加到 sum，是求和逻辑的核心。",
            ),
            KeyStatement(
                location="ArrayStats.average",
                line=8,
                snippet="return sum / values.length;",
                explanation=(
                    "先执行 int 除法再转换为 double，会截断小数；"
                    "数组长度为 0 时还会触发除零异常。"
                ),
            ),
            KeyStatement(
                location="ArrayStats.max",
                line=12,
                snippet="int best = 0;",
                explanation="以 0 作为初始最大值，导致全负数数组无法得到正确结果。",
            ),
            KeyStatement(
                location="ArrayStats.max",
                line=14,
                snippet="if (value > best) {",
                explanation="打擂台式比较：仅当当前元素更大时才更新最大值。",
            ),
        ],
        input_output=InputOutputAnalysis(
            inputs=[
                "values：int 数组，average 与 max 都以它作为唯一参数。",
                "调用方通过方法参数直接提供数组，不需要控制台输入。",
            ],
            outputs=[
                "average 返回 double 类型的平均值。",
                "max 返回 int 类型的最大元素。",
            ],
            notes=(
                "代码未规定数组为 null 或长度为 0 时的行为；"
                "average 的返回值还受整数除法截断影响。"
            ),
        ),
        algorithm_idea=(
            "两个方法都是线性扫描：average 采用累加求和，max 采用逐元素打擂台比较。"
            "时间开销都与数组长度成正比，没有使用额外数据结构。"
        ),
        assumptions=[
            "values 非 null 且长度大于 0（代码没有显式保证）。",
            "假设平均值需要保留小数，而当前整数除法会截断。",
            "未考虑 int 累加溢出的极端输入。",
        ],
    )


def _java_review() -> ReviewReport:
    return ReviewReport(
        summary=(
            "两个方法结构简洁，但 average 存在两处高风险问题：空数组除零和整数除法截断；"
            "max 对全负数数组会返回错误结果，sum 还存在 int 溢出风险。"
            "建议优先修复 average 的除法语义和空输入校验。"
        ),
        issues=[
            ReviewIssue(
                title="average 对空数组执行除以 0",
                category="边界",
                severity=Severity.HIGH,
                location=CodeLocation(name="ArrayStats.average", line=8),
                snippet="return sum / values.length;",
                reason="当 values.length 为 0 时，整型除法会抛出 ArithmeticException: / by zero。",
                impact="空数组输入会使程序直接异常终止，无法返回任何结果。",
                suggestion=(
                    "在方法入口检查数组是否为空：可以返回约定的特殊值（如 Double.NaN），"
                    "或抛出带说明的 IllegalArgumentException，并与调用方统一约定。"
                ),
                verification=(
                    "调用 ArrayStats.average(new int[]{})，确认抛出 ArithmeticException；"
                    "加入校验后再次调用，确认返回或抛出约定行为。"
                ),
            ),
            ReviewIssue(
                title="整数除法导致平均值被截断",
                category="逻辑",
                severity=Severity.HIGH,
                location=CodeLocation(name="ArrayStats.average", line=8),
                snippet="return sum / values.length;",
                reason=(
                    "sum 与 values.length 都是 int，先执行整数除法，再把整数结果转换为 double。"
                    "例如 (1 + 2) / 2 得到 1，而不是 1.5。"
                ),
                impact="非整除场景返回值偏离真实平均值，属于正常输入下即可出现的错误结果。",
                suggestion="改为 `(double) sum / values.length` 或 `sum / (double) values.length`，确保执行浮点除法。",
                verification="调用 average(new int[]{1, 2})：期望 1.5，当前实现返回 1.0。",
            ),
            ReviewIssue(
                title="max 以 0 为初始值导致全负数结果错误",
                category="逻辑",
                severity=Severity.MEDIUM,
                location=CodeLocation(name="ArrayStats.max", line=12),
                snippet="int best = 0;",
                reason=(
                    "当所有元素都小于 0 时，没有任何元素能大于 best=0，循环结束后仍返回 0，"
                    "而 0 并不在数组中。"
                ),
                impact="全负数输入返回错误结果，并且无法区分“最大值就是 0”的情况。",
                suggestion=(
                    "使用 values[0] 初始化 best，或使用 Integer.MIN_VALUE 并先校验数组非空。"
                ),
                verification="调用 max(new int[]{-5, -2, -9})：期望 -2，当前返回 0。",
            ),
            ReviewIssue(
                title="sum 使用 int 累加可能溢出",
                category="边界",
                severity=Severity.MEDIUM,
                location=CodeLocation(name="ArrayStats.average", line=4),
                snippet="int sum = 0;",
                reason=(
                    "int 的取值范围约为 -2.1×10^9 到 2.1×10^9，多个较大元素累加可能溢出为负数。"
                ),
                impact="溢出不会抛出异常，平均值会变成完全错误的结果，难以通过异常发现。",
                suggestion="使用 long 累加，最终再转换为 double；必要时校验元素取值范围。",
                verification=(
                    "调用 average(new int[]{Integer.MAX_VALUE, 1})：期望约 1.073741824×10^9；"
                    "当前实现因溢出返回负数。"
                ),
            ),
            ReviewIssue(
                title="未校验 null 数组",
                category="异常处理",
                severity=Severity.HIGH,
                location=CodeLocation(name="ArrayStats", line=5),
                snippet="for (int value : values) {",
                reason="增强 for 循环需要遍历数组对象，values 为 null 时会抛出 NullPointerException。",
                impact="调用方传入 null 时程序异常终止。",
                suggestion=(
                    "在方法入口使用 Objects.requireNonNull(values, \"values\") 校验，"
                    "或显式检查并抛出带说明的 IllegalArgumentException。"
                ),
                verification="调用 average(null) 与 max(null)，确认异常类型；加入校验后确认提示信息。",
            ),
        ],
    )


def _java_complexity() -> ComplexityReport:
    return ComplexityReport(
        time_complexity="O(n)，两个方法各做一次线性遍历，n = values.length。",
        space_complexity="O(1)（不计输入数组，仅使用 sum、best 等常数个变量）。",
        confidence=Confidence.HIGH,
        derivation=[
            "average 的增强 for 循环执行 n 次，每次执行一次加法，循环后除法为 O(1)。",
            "max 的循环同样执行 n 次，每次进行一次比较和最多一次赋值，均为 O(1)。",
            "两个方法各自独立调用时复杂度为 O(n)；顺序调用两次仍为 O(n)（忽略常数 2）。",
            "代码没有嵌套循环和递归，因此不存在更高阶项。",
        ],
        assumptions=[
            "n 表示数组 values 的长度。",
            "数组元素访问、整数加法与比较均按 O(1) 处理。",
            "不计入输入数组本身占用的空间。",
            "整数溢出不影响操作的渐进复杂度，但会影响结果正确性。",
        ],
        optimizations=[
            ComplexityOptimization(
                title="合并 average 与 max 的遍历",
                current="两个方法分别遍历数组，共约 2n 次元素访问，时间 O(n)。",
                optimized="在一次遍历中同时累加求和并更新最大值，时间仍为 O(n)，但元素访问次数约减半。",
                explanation=(
                    "适用于需要同时获得平均值与最大值的场景，可降低常数开销；"
                    "需统一空数组的处理方式。"
                ),
            )
        ],
    )


def _java_tests() -> TestReport:
    return TestReport(
        function_signature="ArrayStats.average(int[] values) / ArrayStats.max(int[] values)",
        assumptions=[
            "两个方法都是 public static，可直接通过类名调用。",
            "代码未约定空数组行为，相关用例按当前实现的实际行为验证风险。",
            "average 的预期值按“精确算术平均”计算，用于暴露整数除法截断问题。",
        ],
        cases=[
            TestCase(
                case_type=TestCaseType.NORMAL,
                title="非整除的平均值",
                input="ArrayStats.average(new int[]{1, 2})",
                expected="1.5（当前实现返回 1.0，说明存在整数除法截断）",
                purpose="验证平均值保留小数部分。",
            ),
            TestCase(
                case_type=TestCaseType.NORMAL,
                title="常规最大值",
                input="ArrayStats.max(new int[]{3, 9, 2})",
                expected="9",
                purpose="验证最大值的基本查找逻辑。",
            ),
            TestCase(
                case_type=TestCaseType.BOUNDARY,
                title="空数组求平均",
                input="ArrayStats.average(new int[]{})",
                expected="抛出 ArithmeticException（当前实现除以 0）",
                purpose="验证空输入是否会崩溃，并检查接口是否应返回约定值。",
            ),
            TestCase(
                case_type=TestCaseType.BOUNDARY,
                title="全负数最大值",
                input="ArrayStats.max(new int[]{-5, -2, -9})",
                expected="-2（当前实现返回 0）",
                purpose="验证 max 的初始值是否能正确处理负数。",
            ),
            TestCase(
                case_type=TestCaseType.INVALID,
                title="null 数组",
                input="ArrayStats.average(null) / ArrayStats.max(null)",
                expected="抛出 NullPointerException（当前实现）",
                purpose="验证空引用输入的错误行为。",
            ),
            TestCase(
                case_type=TestCaseType.INVALID,
                title="总和溢出",
                input="ArrayStats.average(new int[]{Integer.MAX_VALUE, 1})",
                expected="约 1.073741824×10^9（当前实现因 int 溢出返回负数）",
                purpose="验证大数累加时的溢出风险。",
            ),
        ],
        coverage_summary=(
            "覆盖正常平均值、常规最大值、空数组、全负数、null 引用和整数溢出，"
            "重点验证 average 的除法语义与 max 的初始值；未覆盖超大数组的并发或性能场景。"
        ),
    )


def _cpp_explanation() -> ExplanationReport:
    return ExplanationReport(
        overall_purpose=(
            "程序演示在有序整数数组中进行二分查找：binarySearch 返回目标元素的下标，"
            "找不到时返回 -1；main 构造示例数组 {1, 3, 5, 7, 9} 并查找目标 7。"
        ),
        execution_flow=[
            "main 构造有序 vector，元素为 1、3、5、7、9。",
            "main 调用 binarySearch(arr, 7)，进入函数后初始化 left=0、right=4。",
            "循环中计算中点 mid，并读取 arr[mid] 与 target 比较。",
            "若相等则立即返回下标；否则根据大小关系将 left 右移或 right 左移。",
            "当 left > right 时区间为空，返回 -1 表示未找到。",
            "main 将返回结果输出到标准输出，程序结束。",
        ],
        key_statements=[
            KeyStatement(
                location="binarySearch",
                line=6,
                snippet="int left = 0, right = arr.size() - 1;",
                explanation=(
                    "初始化闭区间 [left, right] 覆盖整个数组；"
                    "空数组时 arr.size() - 1 存在无符号下溢风险。"
                ),
            ),
            KeyStatement(
                location="binarySearch",
                line=7,
                snippet="while (left <= right) {",
                explanation="只要区间非空就继续查找；区间为空时退出循环。",
            ),
            KeyStatement(
                location="binarySearch",
                line=8,
                snippet="int mid = (left + right) / 2;",
                explanation="取区间中点作为比较位置；left + right 很大时可能发生有符号溢出。",
            ),
            KeyStatement(
                location="binarySearch",
                line=9,
                snippet="if (arr[mid] == target) return mid;",
                explanation="命中目标时直接返回下标，是查找成功出口。",
            ),
            KeyStatement(
                location="binarySearch",
                line=10,
                snippet="if (arr[mid] < target) left = mid + 1;",
                explanation="中点偏小，目标只可能在右半区间，因此收缩左边界。",
            ),
            KeyStatement(
                location="binarySearch",
                line=11,
                snippet="else right = mid - 1;",
                explanation="中点偏大，目标只可能在左半区间，因此收缩右边界。",
            ),
        ],
        input_output=InputOutputAnalysis(
            inputs=[
                "arr：按升序排列的 int 向量，作为查找范围。",
                "target：待查找的整数；main 中硬编码为 7。",
            ],
            outputs=[
                "binarySearch 返回目标元素的下标（int），未找到时返回 -1。",
                "main 通过 cout 把结果打印到标准输出。",
            ],
            notes=(
                "接口隐含要求 arr 非空且升序，代码未显式校验；"
                "空数组和未排序输入的行为没有在注释或文档中约定。"
            ),
        ),
        algorithm_idea=(
            "经典二分查找：维护一个闭区间，每次取中点与目标比较，"
            "根据大小关系舍弃一半区间，从而将对数级时间复杂度降为 O(log n)。"
        ),
        assumptions=[
            "arr 已按升序排序。",
            "数组长度可安全转换为 int，且用 int 表示下标不会溢出。",
            "下标访问 arr[mid] 始终位于有效范围内。",
        ],
    )


def _cpp_review() -> ReviewReport:
    return ReviewReport(
        summary=(
            "二分查找的主体逻辑正确，常规有序数组可以返回正确下标。"
            "主要风险是空数组的无符号下溢、超大下标的中点加法溢出，"
            "以及对“输入必须有序”这一前置条件缺少校验和说明。"
        ),
        issues=[
            ReviewIssue(
                title="空数组时 arr.size() - 1 发生无符号下溢",
                category="边界",
                severity=Severity.MEDIUM,
                location=CodeLocation(name="binarySearch", line=6),
                snippet="int left = 0, right = arr.size() - 1;",
                reason=(
                    "vector::size() 返回无符号的 size_t；空数组时 0 - 1 下溢为极大值，"
                    "再转换为 int 的结果依赖平台实现。"
                ),
                impact=(
                    "常见平台上 right 会变为 -1，循环被跳过并返回 -1，看似正确；"
                    "但该行为依赖有符号转换，若改用 size_t 保存下标就会越界访问。"
                ),
                suggestion=(
                    "先判断 arr.empty() 并直接返回 -1；"
                    "或使用 `int right = static_cast<int>(arr.size()) - 1` 并在转换前校验长度不超过 int 范围。"
                ),
                verification=(
                    "调用 binarySearch({}, 任意值)，确认返回 -1 且没有越界；"
                    "开启 UBSan 或静态检查观察无符号下溢告警。"
                ),
            ),
            ReviewIssue(
                title="中点计算可能发生有符号整数溢出",
                category="边界",
                severity=Severity.MEDIUM,
                location=CodeLocation(name="binarySearch", line=8),
                snippet="int mid = (left + right) / 2;",
                reason=(
                    "当 left 与 right 都接近 INT_MAX 时，left + right 溢出为负数，"
                    "得到非法或错误的中点。"
                ),
                impact=(
                    "超大数组（长度接近 10^9 以上）可能访问越界或陷入错误循环；"
                    "常规规模下不会触发。"
                ),
                suggestion="改用 `int mid = left + (right - left) / 2;`，避免先对两个大下标求和。",
                verification=(
                    "使用极大下标构造单元测试，或通过静态分析检查加法溢出；"
                    "常规规模下可对比两种写法的计算结果。"
                ),
            ),
            ReviewIssue(
                title="默认输入数组已排序但未校验",
                category="逻辑",
                severity=Severity.MEDIUM,
                location=CodeLocation(name="binarySearch", line=9),
                snippet="if (arr[mid] == target) return mid;",
                reason=(
                    "二分查找只在有序数组上成立；传入无序数组时大小比较会误导区间收缩，"
                    "可能返回 -1 或错误下标。"
                ),
                impact=(
                    "调用方误用接口时难以发现，元素实际存在却可能被报告为不存在。"
                ),
                suggestion=(
                    "在函数入口说明并校验有序性（如 std::is_sorted），"
                    "或改用适用于无序数据的查找方式；至少在注释和文档中写明前置条件。"
                ),
                verification=(
                    "使用未排序数组 {3, 1, 2} 查找 1，观察返回 -1，与该元素实际存在的事实矛盾。"
                ),
            ),
            ReviewIssue(
                title="using namespace std; 污染全局命名空间",
                category="代码质量",
                severity=Severity.LOW,
                location=CodeLocation(name="全局作用域", line=3),
                snippet="using namespace std;",
                reason=(
                    "把 std 命名空间中的大量名称引入全局作用域，可能与自定义函数或类型发生冲突。"
                ),
                impact="在较大项目中增加命名冲突和可读性风险；对当前小示例影响有限。",
                suggestion=(
                    "改用显式 std:: 前缀，或只引入需要的名称，例如 using std::vector; using std::cout;。"
                ),
                verification="在包含同名自定义标识符的场景下编译，观察是否出现二义性；或使用代码规范检查。",
            ),
        ],
    )


def _cpp_complexity() -> ComplexityReport:
    return ComplexityReport(
        time_complexity="O(log n)，其中 n = arr.size()。",
        space_complexity="O(1)，仅使用 left、right、mid 等常数个整型变量；迭代实现没有递归栈开销。",
        confidence=Confidence.HIGH,
        derivation=[
            "循环开始时搜索区间长度为 n；每次迭代要么命中目标，要么舍弃约一半区间。",
            "最坏情况下区间长度依次约为 n、n/2、n/4……直到 0。",
            "区间缩小到 0 最多需要约 ⌈log₂(n+1)⌉ 次迭代。",
            "每次迭代只做常数次下标访问、比较与算术运算，因此总时间为 O(log n)。",
            "main 中构造固定长度数组并调用一次查找，不改变渐进复杂度。",
        ],
        assumptions=[
            "arr 已按升序排列。",
            "vector 的下标访问是 O(1) 的随机访问。",
            "n 表示元素个数，且下标可用 int 安全表示（否则需另行处理溢出）。",
            "不计入输入数组本身占用的空间。",
        ],
        optimizations=[
            ComplexityOptimization(
                title="使用标准库 lower_bound",
                current="手写二分查找，时间 O(log n)，额外空间 O(1)，但边界与溢出处理需要自行维护。",
                optimized="std::lower_bound 同样为 O(log n)、O(1)，可复用经过验证的标准实现，减少边界错误。",
                explanation=(
                    "适合生产代码；需将返回的迭代器转换为下标，"
                    "并额外判断该位置元素是否等于 target。"
                ),
            )
        ],
    )


def _cpp_tests() -> TestReport:
    return TestReport(
        function_signature="int binarySearch(const vector<int>& arr, int target)",
        assumptions=[
            "arr 为按升序排列的 int 向量，target 为 int。",
            "返回值为目标下标，-1 表示未找到；调用方不应把 -1 当作合法下标。",
            "空数组与未排序输入属于接口未明确定义的场景，用例用于验证当前行为。",
        ],
        cases=[
            TestCase(
                case_type=TestCaseType.NORMAL,
                title="目标位于中间",
                input="vector<int> arr = {1, 3, 5, 7, 9}；target = 7",
                expected="3",
                purpose="验证常规二分查找的命中路径。",
            ),
            TestCase(
                case_type=TestCaseType.NORMAL,
                title="目标位于首元素",
                input="vector<int> arr = {1, 3, 5, 7, 9}；target = 1",
                expected="0",
                purpose="验证左边界收缩与首元素命中。",
            ),
            TestCase(
                case_type=TestCaseType.NORMAL,
                title="目标不存在",
                input="vector<int> arr = {1, 3, 5, 7, 9}；target = 4",
                expected="-1",
                purpose="验证区间耗尽后返回 -1。",
            ),
            TestCase(
                case_type=TestCaseType.BOUNDARY,
                title="空数组",
                input="vector<int> arr = {}；target = 5",
                expected="-1",
                purpose="检查空输入是否触发无符号下溢或越界。",
                notes="当前实现依赖 size()-1 转换为 int 的行为。",
            ),
            TestCase(
                case_type=TestCaseType.BOUNDARY,
                title="单元素",
                input="vector<int> arr = {5}；target = 5",
                expected="0",
                purpose="验证最小非空规模下的查找。",
            ),
            TestCase(
                case_type=TestCaseType.INVALID,
                title="未排序输入",
                input="vector<int> arr = {3, 1, 2}；target = 1",
                expected="结果不可靠（当前实现返回 -1）",
                purpose="暴露“输入必须有序”这一未文档化的前置条件。",
                notes="未排序数组不属于二分查找的有效输入，应先排序或改用其他查找方式。",
            ),
        ],
        coverage_summary=(
            "覆盖目标在中间、首元素、不存在、空数组、单元素和未排序输入，"
            "验证二分查找的区间收缩与边界行为；未覆盖超大数组下的加法溢出场景。"
        ),
    )


@dataclass(frozen=True)
class DemoSample:
    id: str
    language: str
    title: str
    description: str
    code: str
    explanation: ExplanationReport
    review: ReviewReport
    complexity: ComplexityReport
    tests: TestReport

    def report_for(self, mode: AnalysisMode) -> ReportModel:
        reports: dict[AnalysisMode, ReportModel] = {
            AnalysisMode.EXPLAIN: self.explanation,
            AnalysisMode.REVIEW: self.review,
            AnalysisMode.COMPLEXITY: self.complexity,
            AnalysisMode.TESTS: self.tests,
        }
        return reports[mode]


SAMPLES: tuple[DemoSample, ...] = (
    DemoSample(
        id="python-two-sum",
        language="Python",
        title="两数之和（双重循环）",
        description="查找数组中两个元素之和等于目标值的下标，包含 O(n²) 性能与边界约定问题。",
        code=normalize_code(PYTHON_CODE),
        explanation=_python_explanation(),
        review=_python_review(),
        complexity=_python_complexity(),
        tests=_python_tests(),
    ),
    DemoSample(
        id="java-array-stats",
        language="Java",
        title="数组统计（平均值与最大值）",
        description="遍历数组求平均值和最大值，可观察除零、整数截断与负数边界问题。",
        code=normalize_code(JAVA_CODE),
        explanation=_java_explanation(),
        review=_java_review(),
        complexity=_java_complexity(),
        tests=_java_tests(),
    ),
    DemoSample(
        id="cpp-binary-search",
        language="C++",
        title="二分查找",
        description="在有序数组中查找目标下标，涉及无符号下溢、中点溢出与有序性假设。",
        code=normalize_code(CPP_CODE),
        explanation=_cpp_explanation(),
        review=_cpp_review(),
        complexity=_cpp_complexity(),
        tests=_cpp_tests(),
    ),
)

SAMPLE_BY_ID: dict[str, DemoSample] = {sample.id: sample for sample in SAMPLES}
SAMPLE_BY_CODE: dict[str, DemoSample] = {
    normalize_code(sample.code): sample for sample in SAMPLES
}


@dataclass(frozen=True)
class DemoMatch:
    sample: DemoSample
    report: ReportModel


def resolve_demo_report(code: str, language: str, mode: AnalysisMode) -> DemoMatch:
    """返回命中内置样例的报告；未命中时给出明确的配置引导。"""

    normalized = normalize_code(code)
    sample = SAMPLE_BY_CODE.get(normalized)
    if sample is None:
        raise DemoNotAvailableError(
            "当前处于离线演示模式，只能查看内置示例代码的预置报告，未调用大模型。"
            "请点击上方示例按钮载入示例，或在 .env 中配置 CODEINSIGHT_API_KEY 后分析自定义代码。"
        )

    if language != sample.language:
        raise DemoNotAvailableError(
            f"该示例代码的内置报告对应 {sample.language}，当前选择的语言是 {language}。"
            "请切换语言为示例对应语言，或配置在线模型后分析其他代码。"
        )

    return DemoMatch(sample=sample, report=sample.report_for(mode))
