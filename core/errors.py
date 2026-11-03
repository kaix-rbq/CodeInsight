"""业务异常定义。

所有可预期错误都转换为 :class:`CodeInsightError` 的子类，由界面层统一捕获，
避免模型调用、解析失败等异常直接导致页面崩溃。
"""

from __future__ import annotations


class CodeInsightError(Exception):
    """可展示给用户的业务异常。"""

    def __init__(self, message: str, *, detail: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.detail = detail

    def __str__(self) -> str:
        return self.message


class ConfigurationError(CodeInsightError):
    """配置缺失或非法。"""


class ValidationError(CodeInsightError):
    """用户输入未通过校验。"""


class ModelCallError(CodeInsightError):
    """模型服务调用失败（网络、鉴权、超时等）。"""


class ResultParseError(CodeInsightError):
    """模型输出无法解析为约定的数据结构。"""

    def __init__(
        self,
        message: str,
        *,
        raw_output: str | None = None,
        detail: str | None = None,
    ) -> None:
        super().__init__(message, detail=detail)
        self.raw_output = raw_output


class DemoNotAvailableError(CodeInsightError):
    """离线演示模式下请求了未内置的代码。"""
