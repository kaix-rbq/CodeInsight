"""界面主题与品牌样式。"""

from __future__ import annotations

import streamlit as st

_CSS = """
<style>
:root {
    --ci-ink: #0f172a;
    --ci-muted: #64748b;
    --ci-primary: #0f766e;
    --ci-accent: #0e7490;
    --ci-border: #e2e8f0;
    --ci-surface: #ffffff;
}

.stApp {
    background:
        radial-gradient(900px 480px at 8% -8%, rgba(204, 251, 241, 0.55) 0%, transparent 60%),
        radial-gradient(720px 420px at 98% 2%, rgba(219, 234, 254, 0.55) 0%, transparent 55%),
        #f7f9fc;
}

[data-testid="stHeader"] {
    background: transparent;
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1480px;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #effaf8 0%, #f8fafc 30%, #ffffff 100%);
    border-right: 1px solid var(--ci-border);
}

[data-testid="stSidebar"] .block-container {
    padding-top: 1.4rem;
}

/* ---------- Hero ---------- */
.ci-hero {
    position: relative;
    padding: 1.5rem 1.7rem 1.6rem;
    border-radius: 24px;
    background: linear-gradient(130deg, #0b1220 0%, #123f3b 55%, #0e7490 100%);
    color: #f8fafc;
    overflow: hidden;
    margin-bottom: 1.3rem;
    box-shadow: 0 28px 60px -38px rgba(15, 23, 42, 0.75);
}

.ci-hero::after {
    content: "";
    position: absolute;
    inset: 0;
    background:
        radial-gradient(520px 220px at 88% -12%, rgba(45, 212, 191, 0.38) 0%, transparent 62%),
        radial-gradient(420px 200px at 4% 120%, rgba(14, 165, 233, 0.22) 0%, transparent 60%);
    pointer-events: none;
}

.ci-eyebrow {
    position: relative;
    z-index: 1;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: #99f6e4;
}

.ci-hero-title {
    position: relative;
    z-index: 1;
    margin: 0.35rem 0 0.45rem;
    font-size: clamp(2rem, 3.4vw, 2.75rem);
    line-height: 1.05;
    font-weight: 800;
    letter-spacing: -0.03em;
    background: linear-gradient(92deg, #ffffff 0%, #ccfbf1 58%, #a5f3fc 100%);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
}

.ci-hero-sub {
    position: relative;
    z-index: 1;
    max-width: 760px;
    color: #dbe4ee;
    font-size: 0.98rem;
    line-height: 1.7;
}

.ci-chips {
    position: relative;
    z-index: 1;
    display: flex;
    flex-wrap: wrap;
    gap: 0.45rem;
    margin-top: 0.9rem;
}

.ci-chip {
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    padding: 0.24rem 0.62rem;
    border-radius: 999px;
    border: 1px solid rgba(255, 255, 255, 0.18);
    background: rgba(255, 255, 255, 0.08);
    color: #e2e8f0;
    font-size: 0.76rem;
    font-weight: 600;
    letter-spacing: 0.01em;
}

/* ---------- Sidebar ---------- */
.ci-brand {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    margin-bottom: 0.9rem;
}

.ci-brand-mark {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 2.4rem;
    height: 2.4rem;
    border-radius: 12px;
    background: linear-gradient(135deg, #0f766e, #0e7490);
    color: #ffffff;
    font-weight: 800;
    font-size: 1rem;
    box-shadow: 0 10px 22px -12px rgba(13, 148, 136, 0.9);
}

.ci-brand-name {
    font-size: 1.02rem;
    font-weight: 800;
    color: var(--ci-ink);
    letter-spacing: -0.01em;
}

.ci-brand-tag {
    font-size: 0.72rem;
    color: var(--ci-muted);
}

.ci-status-headline {
    font-size: 0.9rem;
    font-weight: 700;
    color: var(--ci-ink);
    margin-bottom: 0.2rem;
}

.ci-status-detail {
    font-size: 0.8rem;
    line-height: 1.6;
    color: var(--ci-muted);
}

/* ---------- Badges ---------- */
.ci-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.28rem;
    padding: 0.18rem 0.56rem;
    border-radius: 999px;
    font-size: 0.73rem;
    font-weight: 700;
    letter-spacing: 0.01em;
    white-space: nowrap;
}

.ci-badge-mode {
    background: #ecfdf5;
    color: #047857;
    border: 1px solid #a7f3d0;
}

.ci-badge-info {
    background: #eff6ff;
    color: #1d4ed8;
    border: 1px solid #bfdbfe;
}

.ci-badge-demo {
    background: #fffbeb;
    color: #b45309;
    border: 1px solid #fde68a;
}

.ci-badge-high {
    background: #fef2f2;
    color: #b91c1c;
    border: 1px solid #fecaca;
}

.ci-badge-medium {
    background: #fff7ed;
    color: #c2410c;
    border: 1px solid #fed7aa;
}

.ci-badge-low {
    background: #fefce8;
    color: #a16207;
    border: 1px solid #fef08a;
}

.ci-badge-type {
    background: #f1f5f9;
    color: #334155;
    border: 1px solid #e2e8f0;
}

.ci-meta-row {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.42rem;
    margin-bottom: 0.5rem;
}

/* ---------- Metrics / cards ---------- */
.ci-metric {
    height: 100%;
    padding: 0.85rem 1rem;
    border-radius: 16px;
    border: 1px solid var(--ci-border);
    background: linear-gradient(180deg, #ffffff 0%, #fbfdff 100%);
    box-shadow: 0 10px 30px -26px rgba(15, 23, 42, 0.45);
}

.ci-metric-label {
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--ci-muted);
    margin-bottom: 0.3rem;
}

.ci-metric-value {
    font-size: 1.02rem;
    font-weight: 750;
    color: var(--ci-ink);
    line-height: 1.4;
    word-break: break-word;
}

.ci-metric-sub {
    margin-top: 0.3rem;
    font-size: 0.76rem;
    color: var(--ci-muted);
}

.ci-steps {
    margin: 0.2rem 0 0.4rem 1.1rem;
    padding: 0;
    color: #1e293b;
    line-height: 1.85;
}

.ci-steps li {
    margin-bottom: 0.25rem;
}

.ci-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    margin: 0.5rem 0 0.8rem;
    font-size: 0.84rem;
    border: 1px solid var(--ci-border);
    border-radius: 14px;
    overflow: hidden;
}

.ci-table th {
    background: #f1f5f9;
    color: #334155;
    text-align: left;
    font-weight: 700;
    padding: 0.55rem 0.7rem;
    border-bottom: 1px solid var(--ci-border);
    white-space: nowrap;
}

.ci-table td {
    padding: 0.55rem 0.7rem;
    vertical-align: top;
    border-bottom: 1px solid #f1f5f9;
    color: #1e293b;
    line-height: 1.6;
}

.ci-table tr:last-child td {
    border-bottom: none;
}

.ci-table code {
    font-size: 0.78rem;
    color: #0f766e;
    background: #f0fdfa;
    padding: 0.1rem 0.28rem;
    border-radius: 5px;
}

.ci-callout {
    padding: 0.9rem 1rem;
    border-radius: 14px;
    border: 1px solid #e0f2fe;
    background: #f0f9ff;
    color: #0c4a6e;
    font-size: 0.86rem;
    line-height: 1.65;
}

.ci-note {
    font-size: 0.8rem;
    color: var(--ci-muted);
    line-height: 1.6;
}

.ci-footer {
    margin-top: 1.4rem;
    padding-top: 0.9rem;
    border-top: 1px solid var(--ci-border);
    font-size: 0.75rem;
    color: var(--ci-muted);
    line-height: 1.7;
}

/* ---------- Streamlit widgets ---------- */
textarea {
    font-family: "Cascadia Code", "JetBrains Mono", Consolas, "Courier New", monospace !important;
    font-size: 0.86rem !important;
    line-height: 1.55 !important;
}

[data-testid="stTextArea"] textarea {
    background: #fbfdff;
    border-radius: 12px;
}

.stButton > button {
    border-radius: 10px;
    font-weight: 650;
    border: 1px solid #d8e2ea;
    transition: transform 0.12s ease, box-shadow 0.12s ease;
}

.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 10px 20px -16px rgba(15, 23, 42, 0.6);
}

button[data-testid="baseButton-primary"] {
    background: linear-gradient(135deg, #0f766e 0%, #0e7490 100%);
    border: none;
    color: #ffffff;
    box-shadow: 0 12px 26px -16px rgba(13, 148, 136, 0.95);
}

button[data-testid="baseButton-primary"]:hover {
    box-shadow: 0 16px 30px -14px rgba(13, 148, 136, 0.9);
    color: #ffffff;
}

div[data-testid="stExpander"] {
    border: 1px solid var(--ci-border);
    border-radius: 14px;
    background: #ffffff;
    box-shadow: 0 8px 26px -24px rgba(15, 23, 42, 0.4);
}

div[data-testid="stExpander"] summary {
    font-weight: 650;
}

div[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 18px;
}

[data-testid="stFileUploader"],
[data-testid="stTextArea"] {
    margin-bottom: 0.2rem;
}

div[data-testid="stTabs"] button {
    font-weight: 650;
}

.stDownloadButton > button {
    border-radius: 10px;
    font-weight: 650;
    border: 1px solid #a7f3d0;
    color: #047857;
    background: #ecfdf5;
}

hr {
    border-color: #e8eef4;
}
</style>
"""


def inject_styles() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


def render_hero() -> None:
    st.markdown(
        """
<div class="ci-hero">
  <div class="ci-eyebrow">LangChain · 智能代码分析</div>
  <div class="ci-hero-title">CodeInsight</div>
  <div class="ci-hero-sub">
    粘贴一段代码，让模型替你解释它、审查它、推导复杂度，并生成可直接使用的测试用例。
    四类分析共享统一的结构化报告，便于阅读、复制与导出。
  </div>
  <div class="ci-chips">
    <span class="ci-chip">🐍 Python</span>
    <span class="ci-chip">☕ Java</span>
    <span class="ci-chip">⚙️ C++</span>
    <span class="ci-chip">📖 代码解释</span>
    <span class="ci-chip">🔍 代码审查</span>
    <span class="ci-chip">📈 复杂度分析</span>
    <span class="ci-chip">🧪 测试用例</span>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_footer() -> None:
    st.markdown(
        """
<div class="ci-footer">
  CodeInsight 第一版 · 分析结果由大模型生成，仅供学习与初步排查参考；
  它不能替代编译器、测试框架或人工代码评审。请勿提交密码、密钥等敏感代码。
</div>
""",
        unsafe_allow_html=True,
    )
