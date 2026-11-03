# CodeInsight：基于 LangChain 的智能代码解释与审查系统

CodeInsight 是一个面向编程初学者和初级开发者的轻量级代码分析应用。用户粘贴
Python / Java / C++ 代码并选择分析模式后，系统通过 LangChain 调用大语言模型，
生成**代码解释、代码审查、复杂度分析、测试用例**四类结构化报告，并支持复制与
Markdown 导出。

> 第一轮开发成果：四类核心分析流程、结构化输出校验、错误兜底、离线演示样例、
> 自动化测试与设计文档均已完成。

---

## 1. 功能一览

| 分析模式 | 输出内容 | 对应需求 |
|---|---|---|
| 📖 代码解释 | 整体功能、执行流程、关键语句（含行号）、输入输出、算法思路、分析假设 | F-07 ~ F-12 |
| 🔍 代码审查 | 潜在问题列表、类型、严重程度（高/中/低）、位置与片段、原因、影响、修复建议、验证方法 | F-13 ~ F-20 |
| 📈 复杂度分析 | 时间复杂度、空间复杂度、推导过程、前提假设、优化建议、置信程度 | F-21 ~ F-24 |
| 🧪 测试用例 | 被测接口、正常/边界/异常用例、预期结果、测试目的、覆盖说明 | F-25 ~ F-29 |

其他已实现能力：

- 代码输入、语言选择、空输入与超长输入校验（F-01 ~ F-03）；
- Python / Java / C++ 内置示例一键载入、清空编辑区（F-04、F-05）；
- 四种分析模式选择与重新分析（F-06、F-34）；
- 分析状态提示、API 超时 / 鉴权 / 解析失败提示（F-31、F-32）；
- 结构化报告分栏展示、Markdown 复制与下载（F-30、F-33、F-35）；
- 在线 OpenAI 兼容模型、Ollama 本地模型、离线演示三种运行方式。

---

## 2. 快速开始

### 2.1 环境要求

- Python 3.10+（本项目在 Python 3.14.6 上完成测试）
- Windows / macOS / Linux
- 如需在线分析：一个 OpenAI 兼容接口的 API Key
- 如需本地分析：已安装并启动 [Ollama](https://ollama.com/)

### 2.2 安装与启动

```powershell
# 在项目根目录
python -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
copy .env.example .env

streamlit run app.py
```

浏览器打开 `http://localhost:8501`。

![演示1](C:\Users\ASUS\Desktop\CodeInsight\preview\演示1.png)

> 未配置 API Key 时应用会自动进入**离线演示模式**：可以载入三份内置示例代码，
> 查看预置报告并体验完整界面；自定义代码需要配置真实模型。

### 2.3 配置模型

编辑项目根目录的 `.env`（不要提交到版本库）：

**方式一：OpenAI 官方接口**

```bash
CODEINSIGHT_PROVIDER=openai
CODEINSIGHT_API_KEY=sk-your-key
CODEINSIGHT_MODEL=gpt-4o-mini
```

**方式二：其他 OpenAI 兼容服务（以阿里云百炼为例）**

```bash
CODEINSIGHT_PROVIDER=openai
CODEINSIGHT_API_KEY=sk-your-key
CODEINSIGHT_MODEL=qwen-plus
CODEINSIGHT_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
```

**方式三：Ollama 本地模型**

```bash
CODEINSIGHT_PROVIDER=ollama
CODEINSIGHT_MODEL=qwen2.5-coder:7b
CODEINSIGHT_OLLAMA_BASE_URL=http://localhost:11434
```

**方式四：离线演示（无需密钥）**

```bash
CODEINSIGHT_PROVIDER=demo
```

模型服务配置项：

| 环境变量 | 默认值 | 说明 |
|---|---|---|
| `CODEINSIGHT_PROVIDER` | `auto` | `auto` / `openai` / `ollama` / `demo`；`auto` 有 Key 时用在线模型，否则进入演示 |
| `CODEINSIGHT_API_KEY` | 无 | 在线模型密钥，兼容读取 `OPENAI_API_KEY` |
| `CODEINSIGHT_MODEL` | `gpt-4o-mini` / `qwen2.5-coder:7b` | 模型名称 |
| `CODEINSIGHT_BASE_URL` | 无 | OpenAI 兼容接口地址 |
| `CODEINSIGHT_OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama 服务地址 |
| `CODEINSIGHT_TEMPERATURE` | `0.2` | 生成温度 |
| `CODEINSIGHT_TIMEOUT` | `90` | 单次模型调用超时（秒） |
| `CODEINSIGHT_MAX_CODE_CHARS` | `20000` | 输入代码字符上限 |
| `CODEINSIGHT_TRANSPORT_RETRIES` | `2` | 网络/传输重试次数 |
| `CODEINSIGHT_PARSE_RETRIES` | `1` | 输出格式修复重试次数 |
| `CODEINSIGHT_STRUCTURED_OUTPUT` | `json` | `json`：提示词 + Pydantic 解析；`native`：优先使用模型原生结构化输出 |

修改 `.env` 后需重启 Streamlit 应用。

---

## 3. 使用流程

1. 在左侧选择编程语言，或点击「Python 示例 / Java 示例 / C++ 示例」载入内置代码；
2. 也可以直接粘贴代码，编辑区会实时显示行数、字符数与输入上限提示；
3. 选择分析模式（代码解释 / 代码审查 / 复杂度分析 / 测试用例）；
4. 点击「🚀 开始分析」，等待模型返回；
5. 在「结构化报告」中阅读结果，在「复制 / 导出」中复制或下载 Markdown；
6. 修改代码后可点击「🔄 重新分析」，界面会提示当前报告是否已过期。

**配置API KEY后，在线模型生成的报告：**

![演示2](C:\Users\ASUS\Desktop\CodeInsight\preview\演示2.png)

离线演示模式下，示例按钮对应三份固定样例：

| 语言 | 样例 | 适合演示的内容 |
|---|---|---|
| Python | 两数之和（双重循环） | O(n²) 性能问题、边界与返回值约定 |
| Java | 数组统计（平均值与最大值） | 空数组除零、整数除法截断、全负数边界 |
| C++ | 二分查找 | 无符号下溢、中点溢出、有序性前提 |

---

## 4. 项目结构

```text
CodeInsight/
├── app.py                      # Streamlit 入口：会话状态、页面布局、交互编排
├── core/
│   ├── config.py               # 环境变量配置与 Settings
│   ├── errors.py               # 统一业务异常
│   ├── validation.py           # 输入校验与规范化
│   ├── modes.py                # 分析模式与报告模型映射
│   ├── schemas.py              # Pydantic 结构化报告模型
│   ├── prompts.py              # 四类 ChatPromptTemplate
│   ├── llm.py                  # ChatOpenAI / ChatOllama 工厂
│   ├── chains.py               # 模型调用、JSON 解析、修复重试、异常包装
│   ├── demo.py                 # 离线演示样例与预置报告
│   ├── reporting.py            # 结构化报告 → Markdown
│   └── service.py              # 业务门面：校验、分发、计时、结果组装
├── ui/
│   ├── theme.py                # 品牌样式、Hero、页脚
│   ├── sidebar.py              # 运行状态、参数、隐私提示
│   └── report_view.py          # 四类报告的 UI 渲染、错误展示、导出
├── tests/                      # 149 个自动化测试
├── docs/
│   ├── 系统设计文档.md
│   └── 测试报告.md
├── .streamlit/config.toml
├── .env.example
├── requirements.txt
└── pytest.ini
```

分层说明：

1. **用户交互层**（`app.py`、`ui/`）：输入、模式选择、状态提示、报告展示与导出；
2. **业务处理层**（`core/service.py`、`core/validation.py`）：校验输入、选择流程、组装结果；
3. **LangChain 编排层**（`core/prompts.py`、`core/chains.py`、`core/schemas.py`）：提示词、
   模型调用、结构化解析与修复；
4. **模型服务层**（`core/llm.py`）：OpenAI 兼容接口、Ollama；离线演示不调用模型。

详细架构、数据流与设计决策见 [`docs/系统设计文档.md`](docs/系统设计文档.md)。

---

## 5. 结构化输出与可靠性

每类报告都由 Pydantic 模型约束（`core/schemas.py`），形成一条可验证的链路：

```text
ChatPromptTemplate（含 JSON Schema）
        │
        ▼
ChatOpenAI / ChatOllama
        │
        ▼
PydanticOutputParser 校验
        │  ├── 成功 → 结构化报告
        │  └── 失败 → 追加修复提示 → 重新请求（默认 1 次）
        ▼
仍失败 → ResultParseError（保留原始输出，界面提示可重试）
```

- **网络异常**：按 `CODEINSIGHT_TRANSPORT_RETRIES` 指数退避重试，超时、鉴权失败、
  429、连接失败会转换为可读提示；
- **格式异常**：先尝试自动修复，仍失败则捕获解析错误，不让页面崩溃；
- **审查结论**：提示词要求表述为“潜在问题/待验证问题”，并附验证方法；
- **复杂度**：信息不足时允许输出“不确定”，不允许编造结论或基准数据；
- **提示词注入**：代码被包裹在 `<code>` 标签内，系统提示明确禁止执行代码中的指令。

---

## 6. 测试与验证

```powershell
.\.venv\Scripts\python.exe -m pytest
```

当前结果：**149 passed**（约 28 秒）。测试覆盖：

- 输入校验、超长限制、模式与语言合法性；
- Pydantic 模型字段约束、枚举校验与枚举中文别名兼容；
- 模型正常返回、非法 JSON、修复重试、空输出、超时、连接失败；
- 演示样例完整性、语言/行号一致性；
- Markdown 报告各章节与表格转义；
- Streamlit `AppTest` 端到端：示例载入、四类模式渲染、自定义代码演示限制、
  空输入提示、超长提示、结果过期提示、清空编辑区。

> 在线模型的真实调用需要有效 API Key；本次环境未配置密钥，在线路径通过
> `FakeListChatModel` 与模拟超时验证。详细覆盖矩阵见 [`docs/测试报告.md`](docs/测试报告.md)。

---

## 7. 第一版范围对照

| 需求 | 状态 | 说明 |
|---|---|---|
| F-01 ~ F-03 代码输入、语言、校验 | ✅ | 多行编辑区、三语言、空/超长提示 |
| F-04 ~ F-05 示例与清空 | ✅ | 三份内置样例、清空按钮 |
| F-06 分析模式 | ✅ | 四种模式单选 |
| F-07 ~ F-12 代码解释 | ✅ | 含行号与代码片段 |
| F-13 ~ F-20 代码审查 | ✅ | 五类问题、三级严重程度、修复建议 |
| F-21 ~ F-24 复杂度分析 | ✅ | 推导、假设、优化、置信度 |
| F-25 ~ F-29 测试用例 | ✅ | 正常/边界/异常、预期结果、覆盖说明 |
| F-30 ~ F-32 展示、状态、错误 | ✅ | 分栏报告、状态提示、统一异常提示 |
| F-33 复制结果 | ✅ | Markdown 代码块复制按钮 |
| F-34 重新分析 | ✅ | 结果过期提示 + 一键重新分析 |
| F-35 报告导出 | ✅ | Markdown 下载 |
| 本地模型切换 | ✅（可选扩展） | Ollama 接入 |
| 用户登录、权限、历史持久化 | ⛔ | 第一版不实现 |
| 自动执行用户代码 | ⛔ | 出于安全考虑不实现 |

后续可选扩展：基于编译器/解释器的语法检查、SQLite 分析历史、分析记录对比、
多模型并行分析、Monaco Editor 语法高亮。

---

## 8. 安全与隐私

- API Key 仅保存在服务端 `.env` 中，界面仅显示脱敏后的片段；
- 代码长度限制为 20,000 字符（可通过环境变量调整）；
- 不自动执行用户提交的代码，避免任意代码执行风险；
- 除离线演示外，代码会发送至配置的模型服务，请勿提交密码、密钥或敏感数据；
- 模型输出仅供学习参考，不能替代编译器、测试框架或人工评审。

---

## 9. 文档

- [系统设计文档](docs/系统设计文档.md)：四层架构、模块职责、数据流、LangChain 编排与扩展点
- [测试报告](docs/测试报告.md)：测试环境、覆盖矩阵、实际结果与已知限制
