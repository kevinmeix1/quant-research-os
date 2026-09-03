#!/usr/bin/env python3
"""Generate bilingual (EN | ZH) Quant Research OS handbook PDF."""

from __future__ import annotations

import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyBboxPatch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch, mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs"
FIG_DIR = OUT_DIR / "_handbook_figures"
OUT_PDF = OUT_DIR / "Quant_Research_OS_Handbook.pdf"

INK = colors.HexColor("#12161d")
MUTED = colors.HexColor("#5a6575")
ACCENT = colors.HexColor("#2f5f9e")
RULE = colors.HexColor("#c5cedb")
SOFT = colors.HexColor("#eef1f5")
CODE_BG = colors.HexColor("#f4f6f9")
ZH_SOFT = colors.HexColor("#f7f8fa")

# Preferred Chinese-capable fonts on macOS
FONT_CANDIDATES = [
    ("SongtiSC", "/System/Library/Fonts/Supplemental/Songti.ttc", 0),
    ("STHeiti", "/System/Library/Fonts/STHeiti Light.ttc", 0),
    ("ArialUnicode", "/Library/Fonts/Arial Unicode.ttf", None),
]

EN_FONT = "Helvetica"
EN_FONT_BOLD = "Helvetica-Bold"
ZH_FONT = "Helvetica"  # overwritten after registration
ZH_FONT_BOLD = "Helvetica-Bold"


def register_fonts() -> tuple[str, str]:
    global ZH_FONT, ZH_FONT_BOLD
    for name, path, idx in FONT_CANDIDATES:
        p = Path(path)
        if not p.exists():
            continue
        try:
            if idx is None:
                pdfmetrics.registerFont(TTFont(name, path))
            else:
                pdfmetrics.registerFont(TTFont(name, path, subfontIndex=idx))
            # Songti/Heiti usually lack a separate bold face in this registration path;
            # use the same face for both to avoid missing glyphs.
            ZH_FONT = name
            ZH_FONT_BOLD = name
            return name, path
        except Exception:
            continue
    raise RuntimeError("No Chinese-capable TrueType font found for PDF generation")


def configure_matplotlib_chinese(font_path: str) -> None:
    try:
        font_manager.fontManager.addfont(font_path)
        prop = font_manager.FontProperties(fname=font_path)
        plt.rcParams["font.family"] = prop.get_name()
        plt.rcParams["axes.unicode_minus"] = False
    except Exception:
        # Figures fall back to English-only labels if font binding fails.
        pass


def ensure_dirs() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)


def styles():
    s = getSampleStyleSheet()
    s.add(
        ParagraphStyle(
            name="CoverTitle",
            fontName=EN_FONT_BOLD,
            fontSize=26,
            leading=32,
            textColor=INK,
            alignment=TA_CENTER,
            spaceAfter=6,
        )
    )
    s.add(
        ParagraphStyle(
            name="CoverTitleZH",
            fontName=ZH_FONT_BOLD,
            fontSize=16,
            leading=22,
            textColor=INK,
            alignment=TA_CENTER,
            spaceAfter=10,
        )
    )
    s.add(
        ParagraphStyle(
            name="CoverSub",
            fontName=EN_FONT,
            fontSize=10,
            leading=14,
            textColor=MUTED,
            alignment=TA_CENTER,
            spaceAfter=4,
        )
    )
    s.add(
        ParagraphStyle(
            name="CoverSubZH",
            fontName=ZH_FONT,
            fontSize=10,
            leading=14,
            textColor=MUTED,
            alignment=TA_CENTER,
            spaceAfter=8,
        )
    )
    s.add(
        ParagraphStyle(
            name="H1EN",
            fontName=EN_FONT_BOLD,
            fontSize=13,
            leading=17,
            textColor=INK,
            spaceBefore=10,
            spaceAfter=2,
        )
    )
    s.add(
        ParagraphStyle(
            name="H1ZH",
            fontName=ZH_FONT_BOLD,
            fontSize=11,
            leading=15,
            textColor=ACCENT,
            spaceBefore=0,
            spaceAfter=8,
        )
    )
    s.add(
        ParagraphStyle(
            name="H2EN",
            fontName=EN_FONT_BOLD,
            fontSize=11,
            leading=14,
            textColor=INK,
            spaceBefore=8,
            spaceAfter=1,
        )
    )
    s.add(
        ParagraphStyle(
            name="H2ZH",
            fontName=ZH_FONT_BOLD,
            fontSize=10,
            leading=13,
            textColor=ACCENT,
            spaceBefore=0,
            spaceAfter=5,
        )
    )
    s.add(
        ParagraphStyle(
            name="BodyEN",
            fontName=EN_FONT,
            fontSize=8.4,
            leading=11.5,
            textColor=INK,
            alignment=TA_JUSTIFY,
        )
    )
    s.add(
        ParagraphStyle(
            name="BodyZH",
            fontName=ZH_FONT,
            fontSize=8.4,
            leading=12,
            textColor=INK,
            alignment=TA_JUSTIFY,
        )
    )
    s.add(
        ParagraphStyle(
            name="BulletEN",
            fontName=EN_FONT,
            fontSize=8.2,
            leading=11,
            textColor=INK,
        )
    )
    s.add(
        ParagraphStyle(
            name="BulletZH",
            fontName=ZH_FONT,
            fontSize=8.2,
            leading=11.5,
            textColor=INK,
        )
    )
    s.add(
        ParagraphStyle(
            name="Caption",
            fontName=ZH_FONT,
            fontSize=7.8,
            leading=10.5,
            textColor=MUTED,
            alignment=TA_CENTER,
            spaceBefore=3,
            spaceAfter=8,
        )
    )
    s.add(
        ParagraphStyle(
            name="CodeBlock",
            fontName="Courier",
            fontSize=7.2,
            leading=9.5,
            textColor=INK,
            backColor=CODE_BG,
            leftIndent=3,
            rightIndent=3,
            spaceBefore=3,
            spaceAfter=6,
        )
    )
    s.add(
        ParagraphStyle(
            name="CalloutEN",
            fontName=EN_FONT,
            fontSize=8.3,
            leading=11.5,
            textColor=INK,
        )
    )
    s.add(
        ParagraphStyle(
            name="CalloutZH",
            fontName=ZH_FONT,
            fontSize=8.3,
            leading=11.5,
            textColor=INK,
        )
    )
    s.add(
        ParagraphStyle(
            name="TableCellEN",
            fontName=EN_FONT,
            fontSize=7.4,
            leading=9.5,
            textColor=INK,
        )
    )
    s.add(
        ParagraphStyle(
            name="TableCellZH",
            fontName=ZH_FONT,
            fontSize=7.4,
            leading=10,
            textColor=INK,
        )
    )
    s.add(
        ParagraphStyle(
            name="TableHead",
            fontName=EN_FONT_BOLD,
            fontSize=7.6,
            leading=9.5,
            textColor=colors.white,
        )
    )
    return s


def bi_row(en: str, zh: str, sty, en_style: str, zh_style: str) -> Table:
    """English (left) | Chinese (right) side-by-side block."""
    t = Table(
        [[Paragraph(en, sty[en_style]), Paragraph(zh, sty[zh_style])]],
        colWidths=[88 * mm, 88 * mm],
    )
    t.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (0, 0), 0),
                ("RIGHTPADDING", (0, 0), (0, 0), 4),
                ("LEFTPADDING", (1, 0), (1, 0), 4),
                ("RIGHTPADDING", (1, 0), (1, 0), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 1),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("BACKGROUND", (1, 0), (1, 0), ZH_SOFT),
                ("BOX", (1, 0), (1, 0), 0.2, RULE),
            ]
        )
    )
    return t


def h1(en: str, zh: str, sty):
    return [
        Paragraph(en, sty["H1EN"]),
        Paragraph(zh, sty["H1ZH"]),
    ]


def h2(en: str, zh: str, sty):
    return [
        Paragraph(en, sty["H2EN"]),
        Paragraph(zh, sty["H2ZH"]),
    ]


def body(en: str, zh: str, sty):
    return bi_row(en, zh, sty, "BodyEN", "BodyZH")


def callout(en: str, zh: str, sty):
    t = Table(
        [[Paragraph(en, sty["CalloutEN"]), Paragraph(zh, sty["CalloutZH"])]],
        colWidths=[88 * mm, 88 * mm],
    )
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), SOFT),
                ("BOX", (0, 0), (-1, -1), 0.6, ACCENT),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LINEBEFORE", (1, 0), (1, 0), 0.4, RULE),
            ]
        )
    )
    return t


def bullets(pairs: list[tuple[str, str]], sty):
    """pairs: list of (en, zh) bullet texts (may include <b> markup)."""
    rows = []
    for en, zh in pairs:
        rows.append(
            [
                Paragraph(f"• {en}", sty["BulletEN"]),
                Paragraph(f"• {zh}", sty["BulletZH"]),
            ]
        )
    t = Table(rows, colWidths=[88 * mm, 88 * mm])
    t.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (0, -1), 0),
                ("RIGHTPADDING", (0, 0), (0, -1), 4),
                ("LEFTPADDING", (1, 0), (1, -1), 4),
                ("RIGHTPADDING", (1, 0), (1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 1),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ("BACKGROUND", (1, 0), (1, -1), ZH_SOFT),
            ]
        )
    )
    return t


def code_block(text: str, sty) -> Preformatted:
    return Preformatted(text.rstrip() + "\n", sty["CodeBlock"])


def bilingual_table(headers: list[tuple[str, str]], rows: list[list[tuple[str, str]]], sty):
    """headers/rows cells are (en, zh)."""
    head = [
        Paragraph(f"{en}<br/><font name='{ZH_FONT}' size='7'>{zh}</font>", sty["TableHead"])
        for en, zh in headers
    ]
    data = [head]
    for row in rows:
        data.append(
            [
                Paragraph(
                    f"{en}<br/><font name='{ZH_FONT}' size='7' color='#334155'>{zh}</font>",
                    sty["TableCellEN"],
                )
                for en, zh in row
            ]
        )
    col_w = 176 * mm / max(1, len(headers))
    t = Table(data, colWidths=[col_w] * len(headers))
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.35, RULE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, SOFT]),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    return t


def img(path: Path, sty, caption_en: str, caption_zh: str, width=6.5 * inch):
    im = Image(str(path), width=width, height=width * 0.56)
    im.hAlign = "CENTER"
    return KeepTogether(
        [
            im,
            Paragraph(f"{caption_en}<br/>{caption_zh}", sty["Caption"]),
        ]
    )


# --- Figures (bilingual labels) ---


def fig_architecture(path: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 6.4))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 7.2)
    ax.axis("off")
    fig.patch.set_facecolor("white")
    boxes = [
        (1.4, 5.9, 7.2, 0.9, "User / CLI / Workstation UI\n用户 / CLI / 研究工作站界面 (Next.js :3012)", "#dbe7f8"),
        (1.4, 4.7, 7.2, 0.85, "FastAPI + Research Orchestrator\nFastAPI 接口 + 研究编排器", "#e8eef8"),
        (0.3, 3.2, 2.9, 1.1, "Deterministic Agents\n确定性智能体", "#f3efe6"),
        (3.55, 3.2, 2.9, 1.1, "Allowlisted Tool Router\n白名单工具路由", "#f3efe6"),
        (6.8, 3.2, 2.9, 1.1, "SQLite Research DB\nSQLite 研究数据库", "#f3efe6"),
        (
            1.4,
            1.55,
            7.2,
            1.2,
            "Deterministic Quant Engine  确定性量化引擎\nCS backtest · metrics · WF · robustness · regime · portfolio\n横截面回测 · 指标 · 滚动验证 · 稳健性 · 市场状态 · 组合",
            "#e4f2ea",
        ),
        (
            1.4,
            0.35,
            7.2,
            0.85,
            "Artifacts  产物：Experiments · Alphas · Reports · Paper · Traces\n实验 · Alpha · 报告 · 模拟盘 · 追踪轨迹",
            "#eee",
        ),
    ]
    for x, y, w, h, text, color in boxes:
        ax.add_patch(
            FancyBboxPatch(
                (x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08",
                linewidth=1.1, edgecolor="#334155", facecolor=color,
            )
        )
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=7.5)
    for y0, y1 in [(5.9, 5.55), (4.7, 4.3)]:
        ax.annotate("", xy=(5, y1), xytext=(5, y0), arrowprops=dict(arrowstyle="->", color="#475569"))
    ax.annotate("", xy=(5, 2.75), xytext=(5, 3.2), arrowprops=dict(arrowstyle="->", color="#475569"))
    ax.annotate("", xy=(5, 1.55 + 1.2), xytext=(5, 3.2), arrowprops=dict(arrowstyle="->", color="#475569"))
    ax.annotate("", xy=(5, 1.2), xytext=(5, 1.55), arrowprops=dict(arrowstyle="->", color="#475569"))
    ax.set_title("System Architecture / 系统架构", fontsize=11, pad=6)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def fig_orchestrator(path: Path) -> None:
    nodes = [
        ("START", "开始"),
        ("Planner", "规划"),
        ("Data", "数据"),
        ("Hypothesis", "假设"),
        ("Experiment", "实验"),
        ("Stats", "统计"),
        ("Robustness", "稳健性"),
        ("Regime", "状态"),
        ("Diversify", "分散"),
        ("Adversarial", "对抗审查"),
        ("Portfolio", "组合"),
        ("Risk", "风险"),
        ("Paper Gate", "模拟门槛"),
        ("Report", "报告"),
        ("END", "结束"),
    ]
    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 6)
    ax.axis("off")
    positions = {}
    for i, (en, zh) in enumerate(nodes):
        row = 0 if i < 8 else 1
        col = i if i < 8 else i - 8
        x = 1.0 + col * 1.9
        y = 4.2 if row == 0 else 1.4
        positions[en] = (x, y)
        ax.add_patch(
            FancyBboxPatch(
                (x - 0.8, y - 0.4), 1.6, 0.8,
                boxstyle="round,pad=0.02,rounding_size=0.08",
                linewidth=1.0, edgecolor="#1e3a5f",
                facecolor="#e8eef8" if en not in ("START", "END") else "#f8fafc",
            )
        )
        ax.text(x, y + 0.12, en, ha="center", va="center", fontsize=6.8)
        ax.text(x, y - 0.18, zh, ha="center", va="center", fontsize=6.2, color="#334155")
    order = [n[0] for n in nodes]
    for a, b in zip(order, order[1:]):
        x0, y0 = positions[a]
        x1, y1 = positions[b]
        ax.annotate(
            "",
            xy=(x1 - 0.8 if y0 == y1 and x1 > x0 else x1, y1),
            xytext=(x0 + 0.8 if y0 == y1 and x1 > x0 else x0, y0),
            arrowprops=dict(arrowstyle="->", color="#64748b", lw=1.0),
        )
    ax.set_title("Research Orchestrator State Machine / 研究编排状态机", fontsize=11)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def fig_timing(path: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 3.7))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 4)
    ax.axis("off")
    steps = [
        (0.4, "t: observe\n观察价格/特征"),
        (3.0, "t: signal & weights\n生成信号与目标权重"),
        (5.6, "t+lag: execute\n滞后执行(默认lag=1)"),
        (8.1, "hold shares\n持有股份/权重漂移"),
    ]
    for i, (x, text) in enumerate(steps):
        ax.add_patch(
            FancyBboxPatch(
                (x, 1.25), 1.95, 1.6,
                boxstyle="round,pad=0.02,rounding_size=0.08",
                facecolor="#e4f2ea", edgecolor="#166534",
            )
        )
        ax.text(x + 0.97, 2.05, text, ha="center", va="center", fontsize=7.5)
        if i < len(steps) - 1:
            ax.annotate(
                "",
                xy=(steps[i + 1][0], 2.05),
                xytext=(x + 1.95, 2.05),
                arrowprops=dict(arrowstyle="->", color="#166534"),
            )
    ax.text(
        5, 0.5,
        "Anti look-ahead: no same-bar PnL on newly decided weights\n反前视：新权重不得在同一根K线计入收益",
        ha="center", fontsize=8, color="#334155",
    )
    ax.set_title("Cross-Sectional Execution Timing / 横截面执行时序", fontsize=11)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def fig_lineage(path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8.5, 5.2))
    ax.set_xlim(0, 8)
    ax.set_ylim(0, 8)
    ax.axis("off")
    items = [
        (4, 7.2, "Hypothesis / 假设"),
        (4, 6.0, "Experiment / 实验"),
        (4, 4.8, "Strategy · Backtest / 策略·回测"),
        (4, 3.6, "Alpha (metrics_source_ids)"),
        (4, 2.4, "Portfolio · Risk / 组合·风险"),
        (4, 1.2, "Report claim / 报告结论"),
    ]
    for x, y, label in items:
        ax.add_patch(
            FancyBboxPatch(
                (x - 1.8, y - 0.35), 3.6, 0.7,
                boxstyle="round,pad=0.02,rounding_size=0.08",
                facecolor="#eef2ff", edgecolor="#3730a3",
            )
        )
        ax.text(x, y, label, ha="center", va="center", fontsize=9)
    for i in range(len(items) - 1):
        ax.annotate(
            "",
            xy=(4, items[i + 1][1] + 0.35),
            xytext=(4, items[i][1] - 0.35),
            arrowprops=dict(arrowstyle="->", color="#3730a3", lw=1.3),
        )
    ax.set_title("Traceability Lineage / 可追溯血缘", fontsize=11)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def fig_ui_map(path: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis("off")
    ax.add_patch(FancyBboxPatch((0.3, 0.4), 2.0, 5.2, boxstyle="round,pad=0.02,rounding_size=0.05", facecolor="#0e1116", edgecolor="#334155"))
    ax.text(1.3, 5.15, "Sidebar 侧栏\nOverview 总览\nResearch 研究\nExperiments 实验\nAlphas …", ha="center", va="center", color="white", fontsize=7.5)
    ax.add_patch(FancyBboxPatch((2.5, 5.1), 7.2, 0.5, boxstyle="round,pad=0.02,rounding_size=0.05", facecolor="#13171e", edgecolor="#334155"))
    ax.text(6.1, 5.35, "Topbar 顶栏 · Search 搜索 Cmd+K · Status 状态", ha="center", va="center", color="white", fontsize=8)
    ax.add_patch(FancyBboxPatch((2.5, 1.1), 7.2, 3.8, boxstyle="round,pad=0.02,rounding_size=0.05", facecolor="#f8fafc", edgecolor="#94a3b8"))
    ax.text(6.1, 3.0, "Main workspace 主工作区\nResearch graph / tables / charts\n研究图 · 表格 · 图表", ha="center", va="center", fontsize=9.5, color="#0f172a")
    ax.add_patch(FancyBboxPatch((2.5, 0.4), 7.2, 0.55, boxstyle="round,pad=0.02,rounding_size=0.05", facecolor="#13171e", edgecolor="#334155"))
    ax.text(6.1, 0.67, "Ask Quant Research OS… / 向量化研究系统提问", ha="center", va="center", color="white", fontsize=8)
    ax.set_title("Workstation Shell / 工作站壳层布局", fontsize=11)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def fig_sharpe_theory(path: Path) -> None:
    import numpy as np

    rng = np.random.default_rng(7)
    r = 0.0004 + 0.01 * rng.standard_normal(252)
    eq = np.cumprod(1 + r)
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.4))
    axes[0].plot(eq, color="#2563eb", lw=1.2)
    axes[0].set_title("Equity path / 权益曲线（示意）")
    axes[0].set_xlabel("Day / 日")
    axes[0].grid(True, alpha=0.3)
    window = 42
    roll = [
        (np.mean(r[i - window : i]) / (np.std(r[i - window : i], ddof=0) + 1e-12)) * math.sqrt(252)
        for i in range(window, len(r))
    ]
    axes[1].plot(range(window, len(r)), roll, color="#059669", lw=1.2)
    axes[1].axhline(0, color="#94a3b8", lw=0.8)
    axes[1].set_title("Rolling Sharpe / 滚动夏普（示意）")
    axes[1].set_xlabel("Day / 日")
    axes[1].grid(True, alpha=0.3)
    fig.suptitle("Performance Measurement Intuition / 绩效度量直觉", fontsize=11)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def fig_metrics_pipeline(path: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 3.2))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 3)
    ax.axis("off")
    boxes = [
        (0.3, 1.0, "Net returns\n净收益 r_t"),
        (2.8, 1.0, "Equity path\n权益路径"),
        (5.3, 1.0, "Pinned formulas\n固定公式"),
        (7.8, 1.0, "PerformanceMetrics\n绩效对象"),
        (10.1, 1.0, "Report / UI\n报告/界面"),
    ]
    for x, y, text in boxes:
        ax.add_patch(
            FancyBboxPatch(
                (x, y), 2.0, 1.2,
                boxstyle="round,pad=0.02,rounding_size=0.08",
                facecolor="#e8eef8", edgecolor="#1e3a5f",
            )
        )
        ax.text(x + 1.0, y + 0.6, text, ha="center", va="center", fontsize=8)
    for i in range(len(boxes) - 1):
        x0 = boxes[i][0] + 2.0
        x1 = boxes[i + 1][0]
        ax.annotate("", xy=(x1, 1.6), xytext=(x0, 1.6), arrowprops=dict(arrowstyle="->", color="#475569"))
    ax.set_title("Pinned metrics pipeline / 固定指标流水线", fontsize=11)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def fig_cs_loop(path: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 4.2))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5)
    ax.axis("off")
    steps = [
        (0.4, 3.2, "Scheduled\nweights?\n有计划权重?"),
        (2.6, 3.2, "Turnover in\nweight space\n权重空间换手"),
        (4.8, 3.2, "port_ret =\nΣ w·r\n组合收益"),
        (7.0, 3.2, "Drift +\nNAV renorm\n漂移+归一"),
        (4.8, 0.8, "Subtract costs\n减去成本 → net"),
    ]
    for x, y, text in steps:
        ax.add_patch(
            FancyBboxPatch(
                (x, y), 1.9, 1.4,
                boxstyle="round,pad=0.02,rounding_size=0.08",
                facecolor="#e4f2ea", edgecolor="#166534",
            )
        )
        ax.text(x + 0.95, y + 0.7, text, ha="center", va="center", fontsize=7.5)
    for a, b in [(0, 1), (1, 2), (2, 3)]:
        ax.annotate(
            "",
            xy=(steps[b][0], steps[b][1] + 0.7),
            xytext=(steps[a][0] + 1.9, steps[a][1] + 0.7),
            arrowprops=dict(arrowstyle="->", color="#166534"),
        )
    ax.annotate(
        "",
        xy=(steps[4][0] + 0.95, steps[4][1] + 1.4),
        xytext=(steps[2][0] + 0.95, steps[2][1]),
        arrowprops=dict(arrowstyle="->", color="#166534"),
    )
    ax.set_title("CS bar loop / 横截面单日循环", fontsize=11)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def fig_exp_loop(path: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 3.6))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 3)
    ax.axis("off")
    labels = [
        "Hypothesis\n假设",
        "Strategy\n策略",
        "Experiment\n实验",
        "Backtest\n回测",
        "WF/Robust\n验证",
        "Diversify\n分散",
        "Adversarial\n对抗",
        "Alpha?\n晋升?",
    ]
    for i, text in enumerate(labels):
        x = 0.25 + i * 1.45
        ax.add_patch(
            FancyBboxPatch(
                (x, 1.0), 1.3, 1.2,
                boxstyle="round,pad=0.02,rounding_size=0.06",
                facecolor="#eef2ff", edgecolor="#3730a3",
            )
        )
        ax.text(x + 0.65, 1.6, text, ha="center", va="center", fontsize=7)
        if i < len(labels) - 1:
            ax.annotate(
                "",
                xy=(x + 1.3, 1.6),
                xytext=(x + 1.35, 1.6),
                arrowprops=dict(arrowstyle="->", color="#3730a3"),
            )
    ax.text(6, 0.35, "Budget + cancel checks between hypotheses / 假设间检查预算与取消", ha="center", fontsize=8, color="#334155")
    ax.set_title("Per-hypothesis research loop / 单假设研究循环", fontsize=11)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def fig_ui_dataflow(path: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 3.0))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 3)
    ax.axis("off")
    boxes = [
        (0.3, "Browser\n浏览器"),
        (2.5, "Next.js UI\n工作站"),
        (4.7, "FastAPI\n接口"),
        (6.9, "SQLite\n数据库"),
        (9.1, "Enrich +\nSWR cache\n富化缓存"),
    ]
    for i, (x, text) in enumerate(boxes):
        ax.add_patch(
            FancyBboxPatch(
                (x, 1.0), 1.9, 1.2,
                boxstyle="round,pad=0.02,rounding_size=0.06",
                facecolor="#dbe7f8", edgecolor="#1e3a5f",
            )
        )
        ax.text(x + 0.95, 1.6, text, ha="center", va="center", fontsize=8)
        if i < len(boxes) - 1:
            ax.annotate(
                "",
                xy=(boxes[i + 1][0], 1.6),
                xytext=(x + 1.9, 1.6),
                arrowprops=dict(arrowstyle="->", color="#475569"),
            )
    ax.set_title("Workstation data flow / 工作站数据流", fontsize=11)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def add_header_footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(RULE)
    canvas.setLineWidth(0.5)
    canvas.line(16 * mm, A4[1] - 11 * mm, A4[0] - 16 * mm, A4[1] - 11 * mm)
    canvas.setFont(EN_FONT, 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(16 * mm, A4[1] - 9 * mm, "Quant Research OS Handbook  |  EN + 中文对照")
    canvas.setFont(ZH_FONT, 7.5)
    canvas.drawRightString(A4[0] - 16 * mm, A4[1] - 9 * mm, "量化研究操作系统手册")
    canvas.line(16 * mm, 11 * mm, A4[0] - 16 * mm, 11 * mm)
    canvas.setFont(EN_FONT, 7.5)
    canvas.drawRightString(A4[0] - 16 * mm, 7 * mm, f"{doc.page}")
    canvas.restoreState()


def build() -> Path:
    font_name, font_path = register_fonts()
    configure_matplotlib_chinese(font_path)
    ensure_dirs()
    sty = styles()

    figs = {
        "arch": FIG_DIR / "architecture.png",
        "orch": FIG_DIR / "orchestrator.png",
        "timing": FIG_DIR / "timing.png",
        "lineage": FIG_DIR / "lineage.png",
        "ui": FIG_DIR / "ui_shell.png",
        "sharpe": FIG_DIR / "sharpe.png",
        "metrics_eq": FIG_DIR / "metrics_pipeline.png",
        "cs_loop": FIG_DIR / "cs_loop.png",
        "exp_loop": FIG_DIR / "exp_loop.png",
        "ui_dataflow": FIG_DIR / "ui_dataflow.png",
    }
    fig_architecture(figs["arch"])
    fig_orchestrator(figs["orch"])
    fig_timing(figs["timing"])
    fig_lineage(figs["lineage"])
    fig_ui_map(figs["ui"])
    fig_sharpe_theory(figs["sharpe"])
    fig_metrics_pipeline(figs["metrics_eq"])
    fig_cs_loop(figs["cs_loop"])
    fig_exp_loop(figs["exp_loop"])
    fig_ui_dataflow(figs["ui_dataflow"])

    doc = SimpleDocTemplate(
        str(OUT_PDF),
        pagesize=A4,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=16 * mm,
        bottomMargin=14 * mm,
        title="Quant Research OS Technical Handbook (EN/ZH)",
        author="Quant Research OS",
    )
    story: list = []

    # COVER
    story.append(Spacer(1, 0.9 * inch))
    story.append(Paragraph("Quant Research OS", sty["CoverTitle"]))
    story.append(Paragraph("量化研究操作系统", sty["CoverTitleZH"]))
    story.append(Paragraph("Technical Handbook &amp; System Walkthrough", sty["CoverSub"]))
    story.append(Paragraph("技术手册与系统详解（英中对照）", sty["CoverSubZH"]))
    story.append(
        Paragraph(
            "Architecture · Quant Theory · Orchestration · Engines · Workstation UI · Operations",
            sty["CoverSub"],
        )
    )
    story.append(
        Paragraph(
            "架构 · 量化理论 · 编排 · 引擎 · 工作站界面 · 运维",
            sty["CoverSubZH"],
        )
    )
    story.append(Spacer(1, 0.25 * inch))
    story.append(
        callout(
            "<b>Hard rule:</b> the planner/agent may propose research directions, but "
            "<b>deterministic quantitative engines are the sole source of truth</b> for "
            "financial metrics, positions, and risk numbers.",
            "<b>硬性规则：</b>规划器/智能体可以提出研究方向，但"
            "<b>确定性量化引擎是财务指标、持仓与风险数字的唯一真相来源</b>。"
            "智能体不得编造夏普比率等指标。",
            sty,
        )
    )
    story.append(Spacer(1, 0.2 * inch))
    story.append(
        body(
            "Audience: quantitative researchers, platform engineers, and reviewers who need to "
            "understand how research questions become experiments, alphas, portfolio impact, "
            "and auditable reports. Layout: <b>English left / Chinese right</b>.",
            "读者：量化研究员、平台工程师与评审者——需要理解研究问题如何变成实验、Alpha、"
            "组合影响与可审计报告。版式：<b>左侧英文 / 右侧中文</b>。",
            sty,
        )
    )
    story.append(
        body(
            f"Chinese font embedded for this build: <b>{font_name}</b>. "
            "Technical identifiers (API paths, IDs, code) remain in English by design.",
            f"本版嵌入中文字体：<b>{font_name}</b>。"
            "技术标识符（API 路径、ID、代码）按惯例保留英文。",
            sty,
        )
    )
    story.append(PageBreak())

    # CONTENTS
    story.extend(h1("1. Contents", "1. 目录", sty))
    story.append(
        bullets(
            [
                ("2. Product intent and design principles", "2. 产品定位与设计原则"),
                ("3. Repository map", "3. 仓库结构"),
                ("4. End-to-end architecture", "4. 端到端架构"),
                ("5. Domain model", "5. 领域模型"),
                ("6. Research orchestrator (state machine)", "6. 研究编排器（状态机）"),
                ("7. Agents and tool allowlist", "7. 智能体与工具白名单"),
                ("8. Cross-sectional engine and anti look-ahead", "8. 横截面引擎与反前视"),
                ("9. Costs, metrics, walk-forward, robustness, regimes", "9. 成本、指标、滚动验证、稳健性、市场状态"),
                ("10. Alpha library, diversification, portfolio &amp; risk", "10. Alpha 库、分散化、组合与风险"),
                ("11. Paper trading honesty model", "11. 模拟盘诚实模型"),
                ("12. Storage, reproducibility, lineage", "12. 存储、可复现与血缘"),
                ("13. FastAPI surface and realtime events", "13. FastAPI 接口与实时事件"),
                ("14. Workstation UI architecture", "14. 工作站 UI 架构"),
                ("15. Flagship FX workflow walkthrough", "15. 旗舰外汇流程走读"),
                ("16. Testing, operations, known gaps", "16. 测试、运维与已知缺口"),
                ("17. Appendix: key code references", "17. 附录：关键代码索引"),
                ("18. Deep dive: metrics mathematics", "18. 深入：指标数学"),
                ("19. Deep dive: backtest loop internals", "19. 深入：回测循环内部"),
                ("20. Deep dive: cost model economics", "20. 深入：成本模型经济学"),
                ("21. Deep dive: orchestrator experiment loop", "21. 深入：编排器实验循环"),
                ("22. Deep dive: hypothesis catalog &amp; falsification", "22. 深入：假设目录与证伪"),
                ("23. Deep dive: storage schema &amp; traces", "23. 深入：存储模式与轨迹"),
                ("24. Deep dive: API contracts &amp; UI binding", "24. 深入：API 契约与 UI 绑定"),
                ("25. Deep dive: traceability drill-down example", "25. 深入：可追溯下钻示例"),
                ("26. Threats to validity &amp; research hygiene", "26. 效度威胁与研究卫生"),
                ("27. Deep dive: walk-forward validation", "27. 深入：滚动前瞻验证"),
                ("28. Deep dive: robustness &amp; fragility", "28. 深入：稳健性与脆弱性"),
                ("29. Deep dive: regime analysis", "29. 深入：市场状态分析"),
                ("30. Deep dive: diversification mathematics", "30. 深入：分散化数学"),
                ("31. Deep dive: ToolRouter &amp; allowlist", "31. 深入：ToolRouter 与白名单"),
                ("32. Worked example: from returns to decision", "32. 演算示例：从收益到决策"),
                ("33. Workstation page-by-page guide", "33. 工作站逐页指南"),
                ("34. Translation &amp; review notes", "34. 翻译与审阅说明"),
            ],
            sty,
        )
    )
    story.append(PageBreak())

    # 2
    story.extend(h1("2. Product Intent and Design Principles", "2. 产品定位与设计原则", sty))
    story.append(
        body(
            "Quant Research OS is an autonomous AI quantitative research laboratory. "
            "It is not a generic chat demo and not a retail trading app. The primary user is a "
            "professional researcher who must answer: what is being researched, why, which "
            "experiments ran, what survived adversarial review, how candidates interact with the "
            "existing book, and what risks remain.",
            "Quant Research OS 是一套自主式 AI 量化研究实验室。"
            "它不是通用聊天演示，也不是零售交易 App。主要用户是专业研究员，需要回答："
            "系统在研究什么、为什么研究、跑了哪些实验、哪些想法通过了对抗性审查、"
            "候选策略与现有组合如何相互作用、还剩哪些风险。",
            sty,
        )
    )
    story.extend(h2("2.1 Design principles", "2.1 设计原则", sty))
    story.append(
        bullets(
            [
                (
                    "<b>Precision &amp; trust</b> — numbers come from engines with provenance IDs.",
                    "<b>精确与信任</b> — 数字来自带溯源 ID 的引擎。",
                ),
                (
                    "<b>Transparency</b> — every transition is traced; reports link to experiments.",
                    "<b>透明</b> — 每次状态转换可追踪；报告链接到实验。",
                ),
                (
                    "<b>Controllability</b> — budgets, cooperative cancel, explicit state machine.",
                    "<b>可控</b> — 预算、协作式取消、显式状态机。",
                ),
                (
                    "<b>Information density</b> — workstation UI optimized for hours of daily use.",
                    "<b>信息密度</b> — 工作站界面为每日长时间使用优化。",
                ),
                (
                    "<b>No metric invention</b> — agents may narrate; they must not invent Sharpe.",
                    "<b>禁止编造指标</b> — 智能体可以叙述，但不得编造夏普比率。",
                ),
            ],
            sty,
        )
    )
    story.extend(h2("2.2 Architectural hard boundary", "2.2 架构硬边界", sty))
    story.append(
        body(
            "Language models are strong at planning, critique, and synthesis, but unreliable as "
            "calculators for portfolio mathematics. Therefore the system splits responsibilities.",
            "语言模型擅长规划、批评与综合，但作为组合数学计算器并不可靠。"
            "因此系统明确拆分职责。",
            sty,
        )
    )
    story.append(
        code_block(
            "LLM / planner / orchestrator  →  proposes hypotheses, chooses tools, writes narrative\n"
            "Deterministic quant engine     →  backtests, metrics, risk, correlations, gates\n"
            "# 规划/编排 → 提出假设、选择工具、撰写叙述\n"
            "# 确定性量化引擎 → 回测、指标、风险、相关性、门槛判定",
            sty,
        )
    )

    # 3
    story.extend(h1("3. Repository Map", "3. 仓库结构", sty))
    story.append(
        bilingual_table(
            [("Path 路径", "Path"), ("Role 作用", "Role")],
            [
                (("src/.../domain/", "领域模型目录"), ("Pydantic domain objects", "Pydantic 领域对象")),
                (("src/.../engine/", "引擎目录"), ("Backtest, metrics, WF, robustness…", "回测、指标、滚动验证、稳健性等")),
                (("src/.../agents/", "智能体目录"), ("Deterministic planner/reviewer", "确定性规划/审查（+未来 LLM 提示词）")),
                (("src/.../tools/", "工具目录"), ("Allowlisted tool router", "白名单工具路由")),
                (("src/.../orchestration/", "编排目录"), ("State machine + budgets", "状态机 + 预算")),
                (("src/.../alpha/", "Alpha 目录"), ("Alpha / strategy registry", "Alpha / 策略注册表")),
                (("src/.../experiments/", "实验目录"), ("Experiment registry + hashing", "实验注册与配置哈希")),
                (("src/.../storage/", "存储目录"), ("SQLite, paths, traces", "SQLite、路径、轨迹")),
                (("src/.../api/", "API 目录"), ("FastAPI", "FastAPI 接口")),
                (("web/", "前端目录"), ("Next.js workstation UI", "Next.js 研究工作站")),
                (("tests/", "测试目录"), ("Invariant + integration tests", "不变量与集成测试")),
                (("docs/", "文档目录"), ("Architecture, audit, this handbook", "架构、审计与本手册")),
            ],
            sty,
        )
    )
    story.append(Spacer(1, 6))

    # 4
    story.extend(h1("4. End-to-End Architecture", "4. 端到端架构", sty))
    story.append(
        body(
            "A research question enters through CLI, API, or the workstation command bar. "
            "The orchestrator creates a ResearchRequest, plans hypotheses, validates data, "
            "runs budgeted experiments through the tool layer, validates statistically, "
            "stresses robustness and regimes, checks diversification versus existing alphas, "
            "runs adversarial review, evaluates portfolio/risk impact, and emits a report with traces.",
            "研究问题可通过 CLI、API 或工作站命令栏进入。"
            "编排器创建 ResearchRequest，规划假设，校验数据，"
            "经工具层在预算内运行实验，做统计验证、稳健性与市场状态压力测试，"
            "检查相对既有 Alpha 的分散性，进行对抗性审查，评估组合/风险影响，"
            "并输出带轨迹的报告。",
            sty,
        )
    )
    story.append(
        img(
            figs["arch"],
            sty,
            "Figure 1. Layered system architecture.",
            "图 1. 分层系统架构。",
        )
    )

    # 5
    story.extend(h1("5. Domain Model", "5. 领域模型", sty))
    story.append(
        body(
            "Domain objects are typed Pydantic models. They form the contract between storage, "
            "engines, API, and UI.",
            "领域对象是带类型的 Pydantic 模型，构成存储、引擎、API 与 UI 之间的契约。",
            sty,
        )
    )
    story.append(
        bullets(
            [
                (
                    "<b>ResearchRequest</b> — user question, universe, budgets, status lifecycle.",
                    "<b>ResearchRequest</b> — 用户问题、标的宇宙、预算、状态生命周期。",
                ),
                (
                    "<b>ResearchPlan</b> — interpreted objectives, constraints, hypotheses.",
                    "<b>ResearchPlan</b> — 系统解释后的目标、约束与假设。",
                ),
                (
                    "<b>Experiment</b> — strategy + parameters + dataset + status + metric linkage.",
                    "<b>Experiment</b> — 策略 + 参数 + 数据集 + 状态 + 指标关联。",
                ),
                (
                    "<b>BacktestResult</b> — equity/returns artifact + performance metrics.",
                    "<b>BacktestResult</b> — 权益/收益产物 + 绩效指标。",
                ),
                (
                    "<b>Strategy / Alpha</b> — reusable definition vs promoted research candidate.",
                    "<b>Strategy / Alpha</b> — 可复用定义 vs 晋升后的研究候选。",
                ),
                (
                    "<b>ReviewResult</b> — adversarial findings with severity.",
                    "<b>ReviewResult</b> — 带严重级别的对抗性发现。",
                ),
                (
                    "<b>ResearchReport</b> — executive summary + sections + survivors/rejects.",
                    "<b>ResearchReport</b> — 执行摘要 + 章节 + 幸存者/否决项。",
                ),
            ],
            sty,
        )
    )
    story.extend(h2("5.1 Alpha lifecycle", "5.1 Alpha 生命周期", sty))
    story.append(
        code_block(
            "CANDIDATE → PROMISING → ROBUST → PAPER_TRADING → (LIVE future)\n"
            "                 ↘ REJECTED / RETIRED\n"
            "# 候选 → 有前景 → 稳健 → 模拟盘 →（未来实盘）\n"
            "#           ↘ 否决 / 退役",
            sty,
        )
    )
    story.append(
        body(
            "Promotion requires <b>metrics_source_ids</b> so every Sharpe/drawdown claim is "
            "traceable to a concrete backtest/experiment artifact. This is an anti-hallucination control.",
            "晋升要求提供 <b>metrics_source_ids</b>，使每条夏普/回撤声明都能追溯到具体回测/实验产物。"
            "这是反幻觉（防编造数字）控制。",
            sty,
        )
    )

    # 6
    story.extend(h1("6. Research Orchestrator", "6. 研究编排器", sty))
    story.append(
        body(
            "The orchestrator is an explicit finite state machine (not an unbounded agent loop). "
            "Transitions are logged to the trace table. Budgets limit hypotheses/experiments. "
            "Cancel is cooperative: status becomes CANCELLED and is checked between hypotheses.",
            "编排器是显式有限状态机（不是无界智能体循环）。"
            "转换写入轨迹表。预算限制假设/实验数量。"
            "取消是协作式的：状态设为 CANCELLED，并在假设之间检查。",
            sty,
        )
    )
    story.append(
        img(
            figs["orch"],
            sty,
            "Figure 2. Orchestrator nodes from START to END.",
            "图 2. 编排器节点：从 START 到 END。",
        )
    )
    story.extend(h2("6.1 Why a state machine?", "6.1 为什么用状态机？", sty))
    story.append(
        body(
            "Autonomous research systems fail when agents recurse forever, skip validation, or "
            "mutate goals silently. An explicit transition table makes the laboratory auditable.",
            "当智能体无限递归、跳过验证或静默改变目标时，自主研究系统会失败。"
            "显式转换表使实验室可审计。",
            sty,
        )
    )
    story.append(
        code_block(
            "TRANSITIONS = [\n"
            "  START, ResearchPlanner, DataDiscovery, HypothesisGeneration,\n"
            "  ExperimentDesign, ExperimentExecution, StatisticalValidation,\n"
            "  RobustnessTesting, RegimeAnalysis, DiversificationAnalysis,\n"
            "  AdversarialReview, PortfolioAnalysis, RiskReview,\n"
            "  PaperTradingGate, Report, END,\n"
            "]",
            sty,
        )
    )

    # 7
    story.extend(h1("7. Agents and Tool Allowlist", "7. 智能体与工具白名单", sty))
    story.append(
        body(
            "Current production mode uses <b>deterministic agents</b> (<font face='Courier'>agents/core.py</font>). "
            "<font face='Courier'>agents/prompts.py</font> reserves future LLM mode. The UI System Health panel "
            "labels this honestly as “LLM services: deterministic agents”.",
            "当前生产模式使用<b>确定性智能体</b>（<font face='Courier'>agents/core.py</font>）。"
            "<font face='Courier'>agents/prompts.py</font> 预留给未来 LLM 模式。"
            "UI 系统健康面板如实标注为“LLM 服务：确定性智能体”。",
            sty,
        )
    )
    story.extend(h2("7.1 Planner", "7.1 规划器", sty))
    story.append(
        body(
            "<font face='Courier'>plan_research()</font> expands a question into a fixed hypothesis set for the "
            "flagship FX workflow (momentum, reversal, carry-like structures, low-correlation constraints). "
            "It is a template, not an LLM call.",
            "<font face='Courier'>plan_research()</font> 将问题展开为旗舰外汇流程的固定假设集合"
            "（动量、反转、类套利结构、低相关约束）。它是模板，不是 LLM 调用。",
            sty,
        )
    )
    story.extend(h2("7.2 Tool router", "7.2 工具路由", sty))
    story.append(
        body(
            "All quantitative side effects go through ToolRouter with an allowlist. Agents cannot "
            "call arbitrary Python. Typical tools: list/inspect/validate datasets, run_backtest, "
            "walk-forward, robustness batteries, correlation versus existing library, stress tests.",
            "所有量化副作用都经过带白名单的 ToolRouter。智能体不能调用任意 Python。"
            "典型工具：列出/检查/校验数据集、run_backtest、滚动验证、稳健性套件、"
            "相对既有库的相关性、压力测试。",
            sty,
        )
    )

    story.append(PageBreak())

    # 8
    story.extend(h1("8. Cross-Sectional Engine &amp; Anti Look-Ahead", "8. 横截面引擎与反前视", sty))
    story.append(
        body(
            "Cross-sectional strategies rank a universe at each rebalance and hold a long/short basket. "
            "In FX G10, a classic example is momentum: buy recent winners, sell losers. "
            "The scientific risk is <b>look-ahead bias</b> — using information not available at decision time.",
            "横截面策略在每次再平衡时对一篮子标的排序，并持有多空组合。"
            "在 FX G10 中，经典例子是动量：买入近期赢家、卖出输家。"
            "科学风险是<b>前视偏差（look-ahead bias）</b>——使用决策时尚不可得的信息。",
            sty,
        )
    )
    story.extend(h2("8.1 Timing contract", "8.1 时序契约", sty))
    story.append(
        bullets(
            [
                (
                    "At bar <i>t</i> close, compute signal from prices available at <i>t</i>.",
                    "在 K 线 <i>t</i> 收盘，仅用 <i>t</i> 时刻可得价格计算信号。",
                ),
                (
                    "Schedule target weights for execution at <i>t + execution_lag</i>.",
                    "将目标权重安排在 <i>t + execution_lag</i> 执行。",
                ),
                (
                    "Default execution_lag ≥ 1 → no same-bar return on new weights.",
                    "默认 execution_lag ≥ 1 → 新权重不得计入同一根 K 线收益。",
                ),
                (
                    "Between rebalances, share holdings are fixed; weights drift with prices.",
                    "再平衡之间固定持股数量；权重随价格漂移。",
                ),
                (
                    "Turnover is measured in weight space after NAV renormalization.",
                    "换手率在净值再归一化后的权重空间中计量。",
                ),
            ],
            sty,
        )
    )
    story.append(
        img(
            figs["timing"],
            sty,
            "Figure 3. Signal → lag → execution → drift.",
            "图 3. 信号 → 滞后 → 执行 → 漂移。",
        )
    )
    story.extend(h2("8.2 Selection methods", "8.2 选股/选汇方法", sty))
    story.append(
        body(
            "Supported constructions include top/bottom-N, percentile baskets, z-score weights, "
            "and rank weights. Signals include momentum and short-term reversal, plus feature generators "
            "from <font face='Courier'>features/library.py</font> "
            "(carry, volatility rank, value proxy, liquidity stability).",
            "支持 top/bottom-N、分位数篮子、z-score 加权与秩加权。"
            "信号包括动量与短期反转，以及 <font face='Courier'>features/library.py</font> "
            "特征生成器（carry、波动排序、价值代理、流动性稳定）。",
            sty,
        )
    )
    story.extend(h2("8.3 Weight-space turnover &amp; NAV renormalize", "8.3 权重空间换手与净值再归一", sty))
    story.append(
        bullets(
            [
                (
                    "Target weights are decided on rebalance bars, then shifted by execution_lag.",
                    "目标权重在再平衡日决定，再按 execution_lag 平移。",
                ),
                (
                    "One-way turnover = 0.5 · Σ|w_new − w_old| (weight space, not share counts).",
                    "单边换手 = 0.5 · Σ|w_new − w_old|（权重空间，非股数）。",
                ),
                (
                    "Gross portfolio return uses beginning-of-bar holdings · asset returns.",
                    "组合毛收益 = 期初持仓 · 资产收益。",
                ),
                (
                    "Holdings drift with asset returns, then divide by (1 + port_ret) so next weights stay NAV-relative.",
                    "持仓随资产收益漂移，再除以 (1 + port_ret)，使次日权重相对净值。",
                ),
                (
                    "Net returns = portfolio returns − cost series from turnover × cost rate.",
                    "净收益 = 组合收益 − 由换手 × 成本率得到的成本序列。",
                ),
            ],
            sty,
        )
    )
    story.append(
        callout(
            "If execution_lag were allowed to be 0, same-bar PnL on new weights would silently invent edge. "
            "The engine raises if lag &lt; 1.",
            "若允许 execution_lag=0，新权重同日盈亏会静默伪造优势。"
            "引擎在 lag &lt; 1 时抛错。",
            sty,
        )
    )

    # 9
    story.extend(h1("9. Costs, Metrics, Validation Engines", "9. 成本、指标与验证引擎", sty))
    story.extend(h2("9.1 Transaction costs", "9.1 交易成本", sty))
    story.append(
        body(
            "Costs are first-class in <font face='Courier'>engine/costs.py</font>. "
            "Three FX presets — OPTIMISTIC (0.85 bps), BASELINE (2.75 bps), PESSIMISTIC (10 bps) "
            "variable — multiply one-way turnover. Strategies must remain attractive under BASELINE; "
            "promotion narratives require survival under PESSIMISTIC stress. "
            "See deep dive §20 for the full economics table.",
            "成本在 <font face='Courier'>engine/costs.py</font> 中是一等公民。"
            "三种外汇预设 — OPTIMISTIC（0.85 bps）、BASELINE（2.75 bps）、PESSIMISTIC（10 bps）可变 —"
            "乘以单边换手。策略在 BASELINE 下仍需有吸引力；晋升叙述需经受 PESSIMISTIC 压力。"
            "完整经济学表见深入 §20。",
            sty,
        )
    )
    story.extend(h2("9.2 Performance metrics", "9.2 绩效指标", sty))
    story.append(
        body(
            "Metrics are computed exclusively in <font face='Courier'>engine/metrics.py</font> with pinned definitions "
            "(sibling libraries disabled — <font face='Courier'>sibling_metrics_available() → False</font>). "
            "Critical pin: population std (<font face='Courier'>ddof=0</font>). "
            "Sortino uses full-sample downside deviation √mean(min(r,0)²), not std of negatives only. "
            "Deep dive §18 lists the exact formulas and code contract.",
            "指标仅在 <font face='Courier'>engine/metrics.py</font> 按固定定义计算"
            "（兄弟库禁用 — <font face='Courier'>sibling_metrics_available() → False</font>）。"
            "关键固定：总体标准差（<font face='Courier'>ddof=0</font>）。"
            "索提诺使用全样本下行偏差 √mean(min(r,0)²)，而非仅负收益子集标准差。"
            "深入 §18 列出精确公式与代码契约。",
            sty,
        )
    )
    story.append(
        bullets(
            [
                ("<b>Annual return / volatility</b> — 252-day annualization.", "<b>年化收益 / 波动率</b> — 252 日年化。"),
                ("<b>Sharpe</b> — mean excess / std(ddof=0) · √252.", "<b>夏普</b> — 超额均值 / std(ddof=0) · √252。"),
                ("<b>Sortino</b> — full-sample downside deviation.", "<b>索提诺</b> — 全样本下行偏差。"),
                ("<b>Max drawdown / Calmar</b> — path-dependent risk.", "<b>最大回撤 / 卡玛</b> — 路径依赖风险。"),
                ("<b>Turnover / costs / trade_count</b> — implementability.", "<b>换手 / 成本 / 成交笔数</b> — 可实施性。"),
            ],
            sty,
        )
    )
    story.append(
        img(
            figs["sharpe"],
            sty,
            "Figure 4. Intuition for equity path and rolling Sharpe.",
            "图 4. 权益路径与滚动夏普的直觉示意。",
        )
    )
    story.extend(h2("9.3 Walk-forward", "9.3 滚动前瞻验证（Walk-forward）", sty))
    story.append(
        body(
            "Walk-forward (<font face='Courier'>engine/walk_forward.py</font>) evaluates a <b>frozen</b> "
            "cross-sectional rule on expanding or rolling windows (defaults: 126 train / 63 test / step 63). "
            "Parameters are not re-optimized inside train windows. OOS segments are de-duplicated before "
            "aggregate Sharpe. OOS — not in-sample — is the primary promotion signal. Deep dive §27.",
            "Walk-forward（<font face='Courier'>engine/walk_forward.py</font>）在扩展或滚动窗上评估"
            "<b>冻结</b>横截面规则（默认：126 训练 / 63 测试 / 步长 63）。"
            "训练窗内不重新优化参数。汇总夏普前对样本外片段去重。"
            "晋升看 OOS 而非样本内。深入 §27。",
            sty,
        )
    )
    story.extend(h2("9.4 Robustness", "9.4 稳健性", sty))
    story.append(
        body(
            "Robustness (<font face='Courier'>engine/robustness.py</font>) sweeps lookback (and similar) "
            "grids and flags <b>fragile</b> knife-edge peaks (interior peak Sharpe − neighbor mean &gt; 0.5 "
            "with peak &gt; 0.3) and jagged surfaces (mean |ΔSharpe| ≥ 0.35). "
            "Adversarial review treats fragility as a promotion blocker. Deep dive §28.",
            "稳健性（<font face='Courier'>engine/robustness.py</font>）扫描 lookback（等）网格，"
            "标记<b>脆弱</b>刀锋峰（内部峰值夏普 − 邻域均值 &gt; 0.5 且峰值 &gt; 0.3）"
            "与锯齿曲面（平均 |Δ夏普| ≥ 0.35）。"
            "对抗性审查将脆弱性视为晋升阻断。深入 §28。",
            sty,
        )
    )
    story.extend(h2("9.5 Regimes", "9.5 市场状态（Regime）", sty))
    story.append(
        body(
            "Regime labels (<font face='Courier'>engine/regime.py</font>) combine rolling-vol tertiles with "
            "risk-on/off trend, then shift by 1 bar to avoid same-day attribution leakage. "
            "Labels are heuristic (confidence ~0.4). Concentration across a single regime slice is flagged. "
            "Deep dive §29.",
            "市场状态标签（<font face='Courier'>engine/regime.py</font>）结合滚动波动三分位与"
            "风险偏好趋势，再平移 1 根 K 线以避免同日归因泄漏。"
            "标签为启发式（置信度 ~0.4）。绩效集中在单一状态会被标记。深入 §29。",
            sty,
        )
    )

    # 10
    story.extend(h1("10. Alpha Library, Diversification, Portfolio &amp; Risk", "10. Alpha 库、分散化、组合与风险", sty))
    story.append(
        body(
            "The alpha library stores candidates with status, metrics, and correlation to the existing book. "
            "A seeded momentum alpha (<font face='Courier'>ALP-existing-momentum</font>) represents incumbent exposure "
            "for low-correlation discovery.",
            "Alpha 库保存候选的状态、指标及与现有组合的相关性。"
            "种子动量 Alpha（<font face='Courier'>ALP-existing-momentum</font>）代表既有敞口，用于低相关发现。",
            sty,
        )
    )
    story.extend(h2("10.1 Diversification analysis", "10.1 分散化分析", sty))
    story.append(
        body(
            "Return correlations, downside correlations, and incremental Sharpe hints estimate whether a "
            "candidate is genuine diversification or a duplicate risk bet.",
            "收益相关、下行相关与增量夏普提示，用于判断候选是真正分散，还是重复风险押注。",
            sty,
        )
    )
    story.extend(h2("10.2 Portfolio / risk", "10.2 组合 / 风险", sty))
    story.append(
        body(
            "The workstation Portfolio page supports what-if: compare current book vs book + Alpha X "
            "on Sharpe, correlation, and counts. Risk Center highlights concentration and high-correlation alerts.",
            "工作站组合页支持情景分析：比较当前组合 vs 组合 + Alpha X 的夏普、相关性与数量。"
            "风险中心突出集中度与高相关告警。",
            sty,
        )
    )

    # 11
    story.extend(h1("11. Paper Trading Honesty Model", "11. 模拟盘诚实模型", sty))
    story.append(
        body(
            "Paper trading in v0.2 may simulate paths using IID noise calibrated to backtest μ/σ. "
            "This is explicitly labeled in payloads and UI banners. It is useful for monitoring plumbing, "
            "but it is <b>not</b> a claim of realistic market replay.",
            "v0.2 的模拟盘可能使用按回测 μ/σ 校准的 IID 噪声路径。"
            "这在载荷与 UI 横幅中明确标注。它对监控链路有用，"
            "但<b>不是</b>真实市场回放的声明。",
            sty,
        )
    )
    story.append(
        callout(
            "The UI forces a clear distinction among <b>BACKTEST</b>, <b>PAPER TRADING</b>, and <b>LIVE</b>. "
            "Confusing these modes is a primary operational failure mode in quant platforms.",
            "UI 强制区分 <b>回测（BACKTEST）</b>、<b>模拟盘（PAPER TRADING）</b> 与 <b>实盘（LIVE）</b>。"
            "混淆这些模式是量化平台的主要运维失败模式之一。",
            sty,
        )
    )

    # 12
    story.extend(h1("12. Storage, Reproducibility, Lineage", "12. 存储、可复现与血缘", sty))
    story.append(
        body(
            "SQLite (WAL mode, FK pragma, indexed JSON tables) stores research requests, plans, "
            "experiments, alphas, reports, paper state, checkpoints, and agent traces. "
            "<font face='Courier'>QROS_DATA_ROOT</font> controls the data directory (default <font face='Courier'>data/local</font>).",
            "SQLite（WAL、外键、带索引 JSON 表）存储研究请求、计划、实验、Alpha、报告、"
            "模拟盘状态、检查点与智能体轨迹。"
            "<font face='Courier'>QROS_DATA_ROOT</font> 控制数据目录（默认 <font face='Courier'>data/local</font>）。",
            sty,
        )
    )
    story.extend(h2("12.1 Config hashing", "12.1 配置哈希", sty))
    story.append(
        body(
            "Experiment configs are hashed so identical parameterizations can be detected and reproduced.",
            "实验配置会被哈希，以便发现并复现相同参数化。",
            sty,
        )
    )
    story.append(
        img(
            figs["lineage"],
            sty,
            "Figure 5. Claim → evidence lineage used by reports and UI.",
            "图 5. 报告与 UI 使用的「结论 → 证据」血缘。",
        )
    )

    # 13
    story.extend(h1("13. FastAPI Surface &amp; Realtime", "13. FastAPI 接口与实时", sty))
    story.append(
        body(
            "The API exposes health, research CRUD/cancel, traces, experiments, strategies, alphas, "
            "backtests, reports, portfolio, correlations, paper stepping, and SSE "
            "<font face='Courier'>/events/stream</font>. Optional <font face='Courier'>QROS_API_KEY</font>. "
            "CORS defaults include the Next.js origin :3012. Experiment list responses are enriched with "
            "metrics joined from <font face='Courier'>backtest_results</font>.",
            "API 提供健康检查、研究创建/查询/取消、轨迹、实验、策略、Alpha、回测、报告、"
            "组合、相关性、模拟盘步进，以及 SSE <font face='Courier'>/events/stream</font>。"
            "可选 <font face='Courier'>QROS_API_KEY</font>。CORS 默认包含 Next.js :3012。"
            "实验列表会从 <font face='Courier'>backtest_results</font> 关联填充指标。",
            sty,
        )
    )
    story.append(
        code_block(
            "GET  /health\n"
            "POST /research\n"
            "GET  /research/{id}  ·  GET /research/{id}/trace\n"
            "POST /research/{id}/cancel\n"
            "GET  /experiments[?research_id=]   # includes joined metrics\n"
            "GET  /alphas · /strategies · /portfolio · /paper\n"
            "GET  /events/stream",
            sty,
        )
    )

    story.append(PageBreak())

    # 14
    story.extend(h1("14. Workstation UI Architecture", "14. 工作站 UI 架构", sty))
    story.append(
        body(
            "The UI (<font face='Courier'>web/</font>) is a Next.js App Router application with a persistent shell: "
            "collapsible left navigation, top status bar, main canvas, and a bottom research command bar. "
            "Design tokens encode a dark research-terminal aesthetic (IBM Plex). Server state uses SWR.",
            "UI（<font face='Courier'>web/</font>）是 Next.js App Router 应用，具有持久壳层："
            "可折叠左侧导航、顶部状态栏、主画布与底部研究命令栏。"
            "设计令牌呈现深色研究终端美学（IBM Plex）。服务端状态使用 SWR。",
            sty,
        )
    )
    story.append(
        img(
            figs["ui"],
            sty,
            "Figure 6. Application shell composition.",
            "图 6. 应用壳层组成。",
        )
    )
    story.extend(h2("14.1 Screen inventory", "14.1 页面清单", sty))
    story.append(
        bilingual_table(
            [("Route 路由", "Route"), ("Purpose 用途", "Purpose")],
            [
                (("/", "/"), ("Overview dashboard", "总览仪表盘")),
                (("/research/[id]", "/research/[id]"), ("Flagship research workspace", "旗舰研究工作区")),
                (("/experiments", "/experiments"), ("Experiment ledger + export", "实验台账 + 导出")),
                (("/alphas/[id]", "/alphas/[id]"), ("Alpha detail + lineage", "Alpha 详情 + 血缘")),
                (("/portfolio", "/portfolio"), ("Allocation + what-if", "配置 + 情景分析")),
                (("/risk", "/risk"), ("Risk center", "风险中心")),
                (("/agents", "/agents"), ("Agent observability", "智能体可观测性")),
                (("/reports/[id]", "/reports/[id]"), ("Report reader", "报告阅读器")),
                (("/memory", "/memory"), ("Research memory search", "研究记忆搜索")),
                (("/paper", "/paper"), ("Paper trading (bannered)", "模拟盘（带模式横幅）")),
                (("Cmd+K palette", "Cmd+K 命令面板"), ("Global object search", "全局对象搜索")),
            ],
            sty,
        )
    )
    story.append(Spacer(1, 6))
    story.extend(h2("14.2 Frontend module boundaries", "14.2 前端模块边界", sty))
    story.append(
        code_block(
            "web/src/app/*                 pages 页面\n"
            "web/src/components/shell      chrome 壳层\n"
            "web/src/components/ui         design system 设计系统\n"
            "web/src/components/charts     TimeSeriesChart 时序图\n"
            "web/src/components/research   ResearchGraph 研究图\n"
            "web/src/domain/types.ts       typed models 类型模型\n"
            "web/src/lib/api.ts            API client API 客户端\n"
            "web/src/lib/realtime.ts       SSE 实时\n"
            "web/src/styles/*              tokens/CSS 令牌样式",
            sty,
        )
    )

    # 15
    story.extend(h1("15. Flagship FX Workflow Walkthrough", "15. 旗舰外汇流程走读", sty))
    story.append(
        body(
            "Flagship question: find a robust cross-sectional FX strategy with low correlation "
            "to existing momentum. The laboratory expands hypotheses, runs budgeted backtests, "
            "validates OOS, measures correlation to <font face='Courier'>ALP-existing-momentum</font>, "
            "adversarially reviews survivors, and writes a report.",
            "旗舰问题：寻找与既有动量低相关、稳健的外汇横截面策略。"
            "实验室展开假设，在预算内回测，做样本外验证，"
            "测量与 <font face='Courier'>ALP-existing-momentum</font> 的相关性，"
            "对幸存者做对抗性审查并撰写报告。",
            sty,
        )
    )
    story.append(
        code_block(
            "quant research run \\\n"
            "  \"Find a robust cross-sectional FX strategy with low correlation \"\\\n"
            "  \"to my existing momentum strategies.\" \\\n"
            "  --max-experiments 8\n\n"
            "# Then open workstation Research workspace for that research_id.\n"
            "# 然后在工作站打开对应 research_id 的研究工作区。",
            sty,
        )
    )
    story.extend(h2("15.1 Step-by-step laboratory path", "15.1 实验室逐步路径", sty))
    story.append(
        bullets(
            [
                (
                    "Planner emits competing FX hypotheses (carry, reversal, vol, value, liquidity) with falsifiers.",
                    "规划器发出竞争的外汇假设（套息、反转、波动、价值、流动性）及证伪条件。",
                ),
                (
                    "Data agent validates synthetic FX panels and seeds ALP-existing-momentum as incumbent book.",
                    "数据智能体校验合成外汇面板，并播种 ALP-existing-momentum 作为既有组合。",
                ),
                (
                    "Each hypothesis becomes a hashed Experiment → lagged CS backtest → metrics artifact.",
                    "每个假设变成带哈希的 Experiment → 滞后横截面回测 → 指标产物。",
                ),
                (
                    "Walk-forward / robustness / regime filters remove fragile winners.",
                    "滚动验证 / 稳健性 / 市场状态过滤去掉脆弱赢家。",
                ),
                (
                    "Diversification vs momentum + adversarial review assign PROMISING / REJECT / more-research.",
                    "相对动量的分散分析 + 对抗性审查给出 PROMISING / REJECT / 需更多研究。",
                ),
                (
                    "Report + traces enable drill-down; Portfolio what-if estimates book impact.",
                    "报告 + 轨迹支持下钻；组合情景分析估计账面影响。",
                ),
            ],
            sty,
        )
    )
    story.extend(h2("15.2 How to read a completed run", "15.2 如何阅读已完成运行", sty))
    story.append(
        body(
            "In the workstation: Overview → latest research card → Research workspace graph (all nodes completed) → "
            "Experiments tab sorted by Sharpe → open best EXP → confirm costs/lag/dataset → Agent Inspector tool payloads → "
            "Report survivors → Portfolio what-if. Never stop at the executive summary.",
            "在工作站：总览 → 最新研究卡片 → 研究工作区图（节点均完成）→ "
            "实验页按夏普排序 → 打开最佳 EXP → 确认成本/滞后/数据集 → 智能体检查器工具载荷 → "
            "报告幸存者 → 组合情景分析。切勿只看执行摘要。",
            sty,
        )
    )

    # 16
    story.extend(h1("16. Testing, Operations, Known Gaps", "16. 测试、运维与已知缺口", sty))
    story.extend(h2("16.1 Verification snapshot", "16.1 验证快照", sty))
    story.append(
        bullets(
            [
                ("Backend: pytest — 32 passed.", "后端：pytest — 32 通过。"),
                ("Frontend: vitest + next build — passed.", "前端：vitest + next build — 通过。"),
                (
                    "Runtime smoke: API healthy; UI routes HTTP 200; browser confirmed Overview, Research graph, Experiments with Sharpes, Alpha Library, Portfolio.",
                    "运行冒烟：API 健康；UI 路由 HTTP 200；浏览器确认总览、研究图、带夏普的实验表、Alpha 库、组合页。",
                ),
                (
                    "Fixes during verification: normalize <font face='Courier'>user_question</font>; enrich experiment metrics from backtests.",
                    "验证中修复：规范化 <font face='Courier'>user_question</font>；从回测关联填充实验指标。",
                ),
            ],
            sty,
        )
    )
    story.extend(h2("16.2 Runbook", "16.2 运行手册", sty))
    story.append(
        code_block(
            "# API\n"
            "source .venv/bin/activate\n"
            "quant serve --host 127.0.0.1 --port 8002\n\n"
            "# UI\n"
            "cd web && npm install && npm run dev   # http://127.0.0.1:3012\n\n"
            "# Handbook PDF\n"
            "python docs/generate_handbook_pdf.py",
            sty,
        )
    )
    story.extend(h2("16.3 Known gaps (honest)", "16.3 已知缺口（如实）", sty))
    story.append(
        bullets(
            [
                ("Planner is a deterministic template — not a live LLM.", "规划器是确定性模板——不是实时 LLM。"),
                ("Paper trading may use IID noise simulation (labeled).", "模拟盘可能使用 IID 噪声仿真（已标注）。"),
                ("Full resume-from-checkpoint node restart is incomplete.", "从检查点按节点完整恢复尚未完成。"),
                ("True async worker fleet / RBAC / Docker hardening incomplete.", "真正的异步工作集群 / RBAC / Docker 加固未完成。"),
                ("Some UI charts are metric-conditioned until full equity series attach.", "部分 UI 图表在完整权益序列接入前由指标条件生成示意。"),
            ],
            sty,
        )
    )

    # 17
    story.extend(h1("17. Appendix — Key Code References", "17. 附录 — 关键代码索引", sty))
    story.append(
        code_block(
            "orchestration/runner.py     state machine + budgets + cancel  状态机/预算/取消\n"
            "agents/core.py              plan_research, adversarial_review 规划与对抗审查\n"
            "tools/router.py             allowlisted tools 白名单工具\n"
            "engine/cross_sectional.py   lagged CS backtest 滞后横截面回测\n"
            "engine/metrics.py           pinned performance math 固定绩效数学\n"
            "engine/walk_forward.py      OOS evaluation 样本外评估\n"
            "engine/robustness.py        sensitivity batteries 敏感性套件\n"
            "engine/regime.py            shifted regime labels 平移后的状态标签\n"
            "alpha/registry.py           alpha/strategy lifecycle 生命周期\n"
            "experiments/registry.py     experiment persistence 实验持久化\n"
            "storage/db.py               SQLite + traces + checkpoints\n"
            "api/app.py                  HTTP + SSE + enrichment\n"
            "web/src/app/research/[id]   flagship workspace UI 旗舰工作区\n"
            "web/src/lib/api.ts          typed client 类型化客户端",
            sty,
        )
    )

    # In-depth chapters 18–26
    import sys
    from pathlib import Path as _Path

    _docs = _Path(__file__).resolve().parent
    if str(_docs) not in sys.path:
        sys.path.insert(0, str(_docs))
    from handbook_deep import append_deep_sections, make_deep_figures

    deep_figs = make_deep_figures(FIG_DIR)
    append_deep_sections(
        story,
        sty,
        h1=h1,
        h2=h2,
        body=body,
        bullets=bullets,
        code_block=code_block,
        callout=callout,
        img=img,
        bilingual_table=bilingual_table,
        deep_figs=deep_figs,
    )

    from handbook_deep_extra import append_extra_deep_sections, make_extra_figures

    extra_figs = make_extra_figures(FIG_DIR)
    append_extra_deep_sections(
        story,
        sty,
        h1=h1,
        h2=h2,
        body=body,
        bullets=bullets,
        code_block=code_block,
        callout=callout,
        img=img,
        bilingual_table=bilingual_table,
        extra_figs=extra_figs,
    )

    # Translation review (final)
    story.extend(h1("34. Translation &amp; Review Notes", "34. 翻译与审阅说明", sty))
    story.append(
        body(
            "This section records terminology choices and a reviewer checklist for the bilingual edition.",
            "本节记录双语版术语选择与审阅清单。",
            sty,
        )
    )
    story.extend(h2("34.1 Terminology glossary", "34.1 术语表", sty))
    story.append(
        bilingual_table(
            [("English", "英文"), ("Chinese (chosen)", "中文（选用）"), ("Notes", "说明")],
            [
                (("Alpha", "Alpha"), ("Alpha（超额收益信号）", "Alpha"), ("Keep “Alpha” as loanword", "保留英文借词")),
                (("Sharpe ratio", "Sharpe"), ("夏普比率", "夏普比率"), ("Standard CN finance term", "标准金融译名")),
                (("Drawdown", "Drawdown"), ("回撤 / 最大回撤", "回撤"), ("Max DD → 最大回撤", "最大回撤")),
                (("Walk-forward", "Walk-forward"), ("滚动前瞻验证", "滚动前瞻验证"), ("Also 走步验证", "亦可称走步验证")),
                (("Look-ahead bias", "Look-ahead"), ("前视偏差", "前视偏差"), ("Decision-time info only", "仅决策时可得信息")),
                (("Cross-sectional", "CS"), ("横截面", "横截面"), ("FX basket ranking", "外汇篮子排序")),
                (("Adversarial review", "Adversarial"), ("对抗性审查", "对抗性审查"), ("Critical review, not GAN", "批评式审查，非生成模型")),
                (("Orchestrator", "Orchestrator"), ("编排器", "编排器"), ("Research state machine", "研究状态机")),
                (("Deterministic", "Deterministic"), ("确定性", "确定性"), ("Opposite of stochastic LLM", "相对随机 LLM")),
                (("Paper trading", "Paper"), ("模拟盘交易", "模拟盘"), ("Labeled simulation mode", "已标注的仿真模式")),
                (("Backtest", "Backtest"), ("回测", "回测"), ("Standard", "标准译名")),
                (("Regime", "Regime"), ("市场状态", "市场状态"), ("Also 区制", "亦可称区制")),
                (("Turnover", "Turnover"), ("换手率", "换手率"), ("Weight-space turnover", "权重空间换手")),
                (("Provenance", "Provenance"), ("溯源 / 来源证明", "溯源"), ("metrics_source_ids", "指标来源 ID")),
                (("Allowlist", "Allowlist"), ("白名单", "白名单"), ("Tool permit-list", "工具许可名单")),
            ],
            sty,
        )
    )
    story.append(Spacer(1, 6))
    story.extend(h2("34.2 Reviewer checklist (this edition)", "34.2 本版审阅清单", sty))
    story.append(
        bullets(
            [
                (
                    "No promotional exaggeration: paper mode and deterministic agents are disclosed in both languages.",
                    "无夸大宣传：模拟盘模式与确定性智能体在两种语言中均如实披露。",
                ),
                (
                    "No inappropriate content; tone is institutional and technical.",
                    "无不当内容；语气保持机构化与技术性。",
                ),
                (
                    "Quant terms use standard Mainland Chinese finance translations; English identifiers preserved.",
                    "量化术语采用大陆常用金融译名；英文标识符保留。",
                ),
                (
                    "“Adversarial” means critical review of strategies (对抗性审查), not generative-model jargon.",
                    "“Adversarial” 指对策略的批评式审查（对抗性审查），而非生成模型术语。",
                ),
                (
                    "Figures, captions, and tables are bilingual; code remains English with optional ZH comments.",
                    "图、图注与表格双语；代码保持英文并可选中文注释。",
                ),
                (
                    "Side-by-side layout: English left column, Chinese right column with light background.",
                    "对照版式：左英右中，中文列浅底以利扫读。",
                ),
            ],
            sty,
        )
    )
    story.append(Spacer(1, 8))
    story.append(
        callout(
            "End of bilingual handbook. Optimize for researchers using the system for hours every day: "
            "traceability over spectacle, engines over narratives, budgets over unbounded loops.",
            "双语手册完。为每日长时间使用的研究员优化："
            "可追溯优于炫技，引擎优于叙述，预算优于无界循环。",
            sty,
        )
    )

    doc.build(story, onFirstPage=add_header_footer, onLaterPages=add_header_footer)
    return OUT_PDF


if __name__ == "__main__":
    pdf = build()
    print(f"Wrote {pdf} ({pdf.stat().st_size} bytes) using ZH font={ZH_FONT}")
