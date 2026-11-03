"""用户输入校验与规范化。"""

from __future__ import annotations

from core.config import SUPPORTED_LANGUAGES
from core.errors import ValidationError
from core.modes import AnalysisMode, coerce_mode

MIN_VISIBLE_CHARS = 1


def normalize_code(code: str) -> str:
    """统一换行符，移除末尾空白行，保留代码缩进与行号结构。"""

    normalized = code.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in normalized.split("\n")]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return "\n".join(lines)


def prepare_code(code: str | None, language: str | None, max_chars: int) -> str:
    """校验代码并返回规范化后的文本。

    校验顺序：空输入 → 超长输入 → 语言合法性。
    """

    if code is None:
        raise ValidationError("请输入需要分析的代码后再提交。")
    if not isinstance(code, str):
        raise ValidationError("代码格式无效，请以纯文本形式粘贴代码。")

    normalized = normalize_code(code)
    if len(normalized.strip()) < MIN_VISIBLE_CHARS:
        raise ValidationError("请输入需要分析的代码后再提交。代码不能为空或仅包含空白字符。")

    if max_chars <= 0:
        raise ValidationError("输入长度上限配置无效，请检查 CODEINSIGHT_MAX_CODE_CHARS。")

    if len(normalized) > max_chars:
        raise ValidationError(
            f"代码长度约为 {len(normalized):,} 字符，超过上限 {max_chars:,} 字符。"
            "请精简代码或分多次分析。"
        )

    if not language or language not in SUPPORTED_LANGUAGES:
        supported = "、".join(SUPPORTED_LANGUAGES)
        raise ValidationError(f"不支持的语言 {language!r}，当前仅支持：{supported}。")

    return normalized


def validate_mode(mode: str | AnalysisMode) -> AnalysisMode:
    try:
        return coerce_mode(mode)
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc


def code_stats(code: str) -> dict[str, int]:
    """返回供界面展示的代码规模统计。"""

    normalized = code.replace("\r\n", "\n").replace("\r", "\n")
    return {
        "chars": len(normalized),
        "lines": normalized.count("\n") + 1 if normalized else 0,
    }
