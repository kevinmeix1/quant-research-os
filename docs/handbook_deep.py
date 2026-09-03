"""In-depth bilingual deep-dive chapters for the Quant Research OS handbook."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from reportlab.lib.units import inch
from reportlab.platypus import PageBreak, Spacer


# ---------------------------------------------------------------------------
# Figure generators (bilingual labels)
# ---------------------------------------------------------------------------


def _fig_metrics_formulas(path: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 4.0))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 4)
    ax.axis("off")
    boxes = [
        (0.2, 1.5, "Daily net\nreturns r_t\n日净收益"),
        (2.5, 1.5, "Equity E_t\n权益路径"),
        (4.8, 1.5, "Sharpe / Sortino\n/ MDD / Calmar\n固定公式"),
        (7.1, 1.5, "PerformanceMetrics\n绩效对象"),
        (9.4, 1.5, "Report & UI\n报告与界面"),
    ]
    for x, y, text in boxes:
        ax.add_patch(
            FancyBboxPatch(
                (x, y),
                2.0,
                1.4,
                boxstyle="round,pad=0.02,rounding_size=0.08",
                facecolor="#e8eef8",
                edgecolor="#1e3a5f",
            )
        )
        ax.text(x + 1.0, y + 0.7, text, ha="center", va="center", fontsize=7.5)
    for i in range(len(boxes) - 1):
        x0 = boxes[i][0] + 2.0
        x1 = boxes[i + 1][0]
        ax.annotate(
            "",
            xy=(x1, 2.2),
            xytext=(x0, 2.2),
            arrowprops=dict(arrowstyle="->", color="#475569"),
        )
    ax.text(
        6.0,
        0.45,
        "ddof=0 pinned · full-sample Sortino downside · no sibling imports\n"
        "固定 ddof=0 · 全样本索提诺下行 · 不导入兄弟库",
        ha="center",
        fontsize=7.5,
        color="#334155",
    )
    ax.set_title("Metrics Mathematics Pipeline / 指标数学流水线", fontsize=11)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def _fig_backtest_loop(path: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5)
    ax.axis("off")
    steps = [
        (0.3, 3.0, "Signal @ t\n信号 @ t"),
        (2.4, 3.0, "Target weights\n目标权重"),
        (4.5, 3.0, "shift(lag≥1)\n滞后执行"),
        (6.6, 3.0, "Turnover\n0.5·Σ|Δw|\n权重换手"),
        (8.3, 3.0, "NAV renorm\n净值归一"),
        (4.5, 0.7, "port_ret − costs\n→ net returns\n组合收益减成本"),
    ]
    for x, y, text in steps[:5]:
        ax.add_patch(
            FancyBboxPatch(
                (x, y),
                1.7,
                1.5,
                boxstyle="round,pad=0.02,rounding_size=0.08",
                facecolor="#e4f2ea",
                edgecolor="#166534",
            )
        )
        ax.text(x + 0.85, y + 0.75, text, ha="center", va="center", fontsize=7.2)
    ax.add_patch(
        FancyBboxPatch(
            (4.5, 0.7),
            2.0,
            1.3,
            boxstyle="round,pad=0.02,rounding_size=0.08",
            facecolor="#fef3c7",
            edgecolor="#92400e",
        )
    )
    ax.text(5.5, 1.35, steps[5][2], ha="center", va="center", fontsize=7.2)
    for i in range(4):
        ax.annotate(
            "",
            xy=(steps[i + 1][0], steps[i + 1][1] + 0.75),
            xytext=(steps[i][0] + 1.7, steps[i][1] + 0.75),
            arrowprops=dict(arrowstyle="->", color="#166534"),
        )
    ax.annotate(
        "",
        xy=(5.5, 2.0),
        xytext=(7.45, 3.0),
        arrowprops=dict(arrowstyle="->", color="#92400e"),
    )
    ax.set_title("Cross-Sectional Backtest Loop / 横截面回测循环", fontsize=11)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def _fig_experiment_pipeline(path: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 3.8))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 3.5)
    ax.axis("off")
    labels = [
        "Budget\ncheck\n预算检查",
        "Feature\nmap\n特征映射",
        "Strategy\n策略",
        "Experiment\n实验",
        "Backtest\n回测",
        "WF / Robust\n滚动/稳健",
        "Diversify\n分散性",
        "Adversarial\n对抗审查",
        "Alpha?\n晋升?",
    ]
    for i, text in enumerate(labels):
        x = 0.15 + i * 1.28
        ax.add_patch(
            FancyBboxPatch(
                (x, 1.2),
                1.15,
                1.3,
                boxstyle="round,pad=0.02,rounding_size=0.06",
                facecolor="#eef2ff",
                edgecolor="#3730a3",
            )
        )
        ax.text(x + 0.57, 1.85, text, ha="center", va="center", fontsize=6.5)
        if i < len(labels) - 1:
            ax.annotate(
                "",
                xy=(x + 1.15, 1.85),
                xytext=(x + 1.18, 1.85),
                arrowprops=dict(arrowstyle="->", color="#3730a3"),
            )
    ax.text(
        6.0,
        0.35,
        "Cancel checked between hypotheses · fx_synthetic_momentum / fx_synthetic_meanrev\n"
        "假设间检查取消 · 动量盘 / 均值回复盘数据集",
        ha="center",
        fontsize=7.5,
        color="#334155",
    )
    ax.set_title("Orchestrator Experiment Pipeline / 编排器实验流水线", fontsize=11)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def _fig_traceability_example(path: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 5.0))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 7)
    ax.axis("off")
    nodes = [
        (5.0, 6.3, "Report decision\n报告结论\nREQUIRES_MORE_RESEARCH"),
        (5.0, 5.0, "Survivor alpha_id\n幸存者 Alpha\nmetrics_source_ids"),
        (2.0, 3.5, "Experiment\n实验\nEXP-…"),
        (5.0, 3.5, "Backtest\n回测\nBT-…"),
        (8.0, 3.5, "Validation\n验证\nWF / robustness"),
        (2.0, 1.8, "Strategy config\n策略配置\nlookback · signal"),
        (5.0, 1.8, "Agent trace\n智能体轨迹\ntool call payload"),
        (8.0, 1.8, "Lineage edge\n血缘边\nproduced→"),
        (5.0, 0.4, "Researcher drill-down path\n研究员下钻路径"),
    ]
    for x, y, text in nodes:
        w, h = (2.6, 0.85) if y > 4 else (2.2, 0.9)
        ax.add_patch(
            FancyBboxPatch(
                (x - w / 2, y - h / 2),
                w,
                h,
                boxstyle="round,pad=0.02,rounding_size=0.08",
                facecolor="#eef2ff" if y > 4 else "#f8fafc",
                edgecolor="#3730a3",
            )
        )
        ax.text(x, y, text, ha="center", va="center", fontsize=6.8)
    arrows = [
        ((5, 5.85), (5, 5.45)),
        ((5, 4.55), (5, 3.95)),
        ((4.2, 5.0), (2.5, 3.95)),
        ((5, 4.55), (5, 3.95)),
        ((5.8, 5.0), (7.5, 3.95)),
        ((2, 3.05), (2, 2.25)),
        ((5, 3.05), (5, 2.25)),
        ((8, 3.05), (8, 2.25)),
        ((5, 1.35), (5, 0.85)),
    ]
    for (x0, y0), (x1, y1) in arrows:
        ax.annotate(
            "",
            xy=(x1, y1),
            xytext=(x0, y0),
            arrowprops=dict(arrowstyle="->", color="#3730a3", lw=1.0),
        )
    ax.set_title("Traceability Drill-Down Example / 可追溯下钻示例", fontsize=11)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def make_deep_figures(fig_dir: Path) -> dict[str, Path]:
    """Create four deep-dive matplotlib figures and return path mapping."""
    fig_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "metrics_formulas": fig_dir / "metrics_formulas.png",
        "backtest_loop": fig_dir / "backtest_loop.png",
        "experiment_pipeline": fig_dir / "experiment_pipeline.png",
        "traceability_example": fig_dir / "traceability_example.png",
    }
    _fig_metrics_formulas(paths["metrics_formulas"])
    _fig_backtest_loop(paths["backtest_loop"])
    _fig_experiment_pipeline(paths["experiment_pipeline"])
    _fig_traceability_example(paths["traceability_example"])
    return paths


# ---------------------------------------------------------------------------
# Deep sections 16–24
# ---------------------------------------------------------------------------


def append_deep_sections(
    story,
    sty,
    *,
    h1,
    h2,
    body,
    bullets,
    code_block,
    callout,
    img,
    bilingual_table,
    deep_figs,
) -> None:
    """Append bilingual EN|ZH deep-dive sections 18–26 to story."""

    # --- Section 16: Metrics Mathematics ---
    story.append(PageBreak())
    story.extend(h1("18. Deep Dive: Metrics Mathematics", "18. 深入解析：指标数学", sty))
    story.append(
        body(
            "All performance numbers in Quant Research OS are computed exclusively in "
            "<font face='Courier'>engine/metrics.py</font>. Sibling metric libraries are "
            "<b>disabled</b> (<font face='Courier'>sibling_metrics_available() → False</font>) "
            "because different <font face='Courier'>ddof</font> conventions silently change Sharpe. "
            "The pinned formulas below are the contract — agents and tools must not invent numbers.",
            "Quant Research OS 中的全部绩效数字仅在 "
            "<font face='Courier'>engine/metrics.py</font> 计算。兄弟指标库被<b>禁用</b>"
            "（<font face='Courier'>sibling_metrics_available() → False</font>），"
            "因为不同的 <font face='Courier'>ddof</font> 约定会静默改变夏普。"
            "以下固定公式即为契约——智能体与工具不得编造数字。",
            sty,
        )
    )
    story.extend(h2("18.1 Equity path and annualization", "18.1 权益路径与年化", sty))
    story.append(
        body(
            "Given net daily returns <font face='Courier'>r_t</font>, equity is "
            "<font face='Courier'>E_t = Π(1 + r_t)</font>. Cumulative return is "
            "<font face='Courier'>E_T − 1</font>. Annualized return uses "
            "<font face='Courier'>(1 + cum)^(252/N) − 1</font> with N = number of daily "
            "observations and 252 trading days per year.",
            "给定净日收益 <font face='Courier'>r_t</font>，权益为 "
            "<font face='Courier'>E_t = Π(1 + r_t)</font>。累计收益为 "
            "<font face='Courier'>E_T − 1</font>。年化收益使用 "
            "<font face='Courier'>(1 + cum)^(252/N) − 1</font>，N 为日观测数，每年 252 个交易日。",
            sty,
        )
    )
    story.extend(h2("18.2 Sharpe, Sortino, MDD (pinned)", "18.2 夏普、索提诺、最大回撤（固定）", sty))
    story.append(
        bullets(
            [
                (
                    "<b>Volatility</b>: <font face='Courier'>σ = std(r, ddof=0) · √252</font>. "
                    "Population standard deviation (ddof=0) is pinned — not sample std.",
                    "<b>波动率</b>：<font face='Courier'>σ = std(r, ddof=0) · √252</font>。"
                    "固定使用总体标准差（ddof=0）——非样本标准差。",
                ),
                (
                    "<b>Sharpe</b>: <font face='Courier'>mean(r − r_f/252) / std(r, ddof=0) · √252</font>. "
                    "Excess return over daily risk-free; denominator uses full-sample std with ddof=0.",
                    "<b>夏普</b>：<font face='Courier'>mean(r − r_f/252) / std(r, ddof=0) · √252</font>。"
                    "超额为日无风险利率之上；分母为全样本 ddof=0 标准差。",
                ),
                (
                    "<b>Sortino</b>: downside deviation = "
                    "<font face='Courier'>√mean(min(r, 0)²)</font> over the <b>full sample</b> "
                    "(zero returns contribute). Not std of negative returns only.",
                    "<b>索提诺</b>：下行偏差 = 全样本上的 "
                    "<font face='Courier'>√mean(min(r, 0)²)</font>（零收益也计入）。"
                    "不是仅对负收益子集求标准差。",
                ),
                (
                    "<b>Max drawdown (MDD)</b>: <font face='Courier'>min(E_t / cummax(E) − 1)</font>.",
                    "<b>最大回撤（MDD）</b>：<font face='Courier'>min(E_t / cummax(E) − 1)</font>。",
                ),
                (
                    "<b>Calmar</b>: annualized return / |MDD| when MDD &lt; 0.",
                    "<b>卡玛</b>：当 MDD &lt; 0 时，年化收益 / |MDD|。",
                ),
            ],
            sty,
        )
    )
    story.append(
        code_block(
            "# engine/metrics.py — pinned implementation\n"
            "equity = (1 + r).cumprod()\n"
            "ann_ret = (1 + cum) ** (252 / len(r)) - 1\n"
            "vol = r.std(ddof=0) * sqrt(252)\n"
            "excess = r - risk_free_rate / 252\n"
            "sharpe = excess.mean() / r.std(ddof=0) * sqrt(252)\n"
            "downside = np.minimum(r, 0.0)\n"
            "down_dev = sqrt(np.mean(downside ** 2))   # full-sample\n"
            "sortino = excess.mean() / down_dev * sqrt(252)\n"
            "mdd = (equity / equity.cummax() - 1.0).min()\n"
            "calmar = ann_ret / abs(mdd) if mdd < 0 else 0.0",
            sty,
        )
    )
    story.append(
        callout(
            "If a reported Sharpe cannot be reproduced by these formulas on the linked return "
            "series, the number is invalid — regardless of narrative quality.",
            "若报告的夏普无法用这些公式在关联收益序列上复现，则该数字无效——"
            "无论叙述多么有说服力。",
            sty,
        )
    )
    story.append(
        img(
            deep_figs["metrics_formulas"],
            sty,
            "Figure 7. Pinned metrics pipeline from net returns to report fields.",
            "图 7. 从净收益到报告字段的固定指标流水线。",
        )
    )
    story.append(Spacer(1, 6))

    # --- Section 17: Backtest Loop Internals ---
    story.extend(h1("19. Deep Dive: Backtest Loop Internals", "19. 深入解析：回测循环内部", sty))
    story.append(
        body(
            "File: <font face='Courier'>engine/cross_sectional.py</font>. The cross-sectional engine "
            "constructs long/short baskets from scores and simulates portfolio returns under a strict "
            "anti-look-ahead timing contract: signal at bar t, execution at t + "
            "<font face='Courier'>execution_lag</font> (≥ 1), weight-space turnover, NAV "
            "renormalization, and transaction costs.",
            "文件：<font face='Courier'>engine/cross_sectional.py</font>。横截面引擎由分数构建多空篮子，"
            "并在严格反前视时序契约下模拟组合收益：t 时刻信号、t + "
            "<font face='Courier'>execution_lag</font>（≥ 1）执行、权重空间换手、净值再归一化与交易成本。",
            sty,
        )
    )
    story.extend(h2("19.1 Configuration surface", "19.1 配置面", sty))
    story.append(
        code_block(
            "class CrossSectionalConfig(BaseModel):\n"
            "    lookback: int = 20\n"
            "    top_n: int = 3\n"
            "    bottom_n: int = 3\n"
            "    selection: TOP_BOTTOM_N | PERCENTILE | ZSCORE_WEIGHT | RANK_WEIGHT\n"
            "    rebalance_every: int = 5\n"
            "    execution_lag: int = Field(default=1, ge=1)  # hard floor\n"
            "    gross_exposure: float = 1.0\n"
            "    cost_assumption: optimistic | baseline | pessimistic\n"
            "    signal_name: str = \"momentum\"  # or reversal / feature library",
            sty,
        )
    )
    story.extend(h2("19.2 Selection methods", "19.2 选择方法", sty))
    story.append(
        bilingual_table(
            [
                ("Method", "方法"),
                ("Mechanism", "机制"),
                ("When to use", "适用场景"),
            ],
            [
                (
                    ("TOP_BOTTOM_N", "Top/Bottom N"),
                    ("Long top N, short bottom N with equal split", "多头 top N、空头 bottom N 等权"),
                    ("Default FX basket; interpretable book", "默认外汇篮子；可解释持仓"),
                ),
                (
                    ("PERCENTILE", "分位数"),
                    ("Long above percentile_long; short below percentile_short", "高于上分位做多；低于下分位做空"),
                    ("Smooth basket sizing across universe", "跨宇宙平滑篮子规模"),
                ),
                (
                    ("ZSCORE_WEIGHT", "Z 分数加权"),
                    ("Center scores; weight proportional to z-score", "中心化分数；按 z 分数比例加权"),
                    ("Continuous exposure to signal strength", "对信号强度连续暴露"),
                ),
                (
                    ("RANK_WEIGHT", "秩加权"),
                    ("Center ranks; weight proportional to rank", "中心化秩；按秩比例加权"),
                    ("Robust to outliers in raw scores", "对原始分数异常值稳健"),
                ),
            ],
            sty,
        )
    )
    story.extend(h2("19.3 Simulation loop (critical)", "19.3 仿真循环（关键）", sty))
    story.append(
        bullets(
            [
                (
                    "On rebalance bars, compute target weights from cross-sectional scores.",
                    "在再平衡日由横截面分数计算目标权重。",
                ),
                (
                    "Shift targets by <font face='Courier'>execution_lag</font> bars (≥ 1). "
                    "Default lag=1 → no same-bar PnL on newly decided weights.",
                    "将目标按 <font face='Courier'>execution_lag</font> 根 K 线平移（≥ 1）。"
                    "默认 lag=1 → 新权重不得在同一根 K 线计入收益。",
                ),
                (
                    "Turnover in <b>weight space</b>: "
                    "<font face='Courier'>turnover = 0.5 · Σ|w_new − w_old|</font>. "
                    "One-way traded fraction.",
                    "<b>权重空间</b>换手：<font face='Courier'>turnover = 0.5 · Σ|w_new − w_old|</font>。"
                    "单边交易比例。",
                ),
                (
                    "Portfolio return: <font face='Courier'>port_ret = Σ(w · r_asset)</font> "
                    "using beginning-of-bar weights.",
                    "组合收益：<font face='Courier'>port_ret = Σ(w · r_asset)</font>，使用期初权重。",
                ),
                (
                    "<b>NAV renormalize</b>: drift holdings by asset returns, then divide by "
                    "<font face='Courier'>(1 + port_ret)</font> so next-day weights remain return-relative.",
                    "<b>净值再归一</b>：按资产收益漂移持仓，再除以 "
                    "<font face='Courier'>(1 + port_ret)</font>，使次日权重仍相对净值。",
                ),
                (
                    "Subtract cost series derived from turnover × cost rate.",
                    "减去由换手 × 成本率导出的成本序列。",
                ),
            ],
            sty,
        )
    )
    story.append(
        code_block(
            "# Anti look-ahead guard\n"
            "if cfg.execution_lag < 1:\n"
            "    raise ValueError(\"execution_lag must be >= 1\")\n"
            "scheduled = target.shift(cfg.execution_lag)\n"
            "turnover = abs(new_w - cur_w).sum() / 2.0   # weight space\n"
            "port_ret = (holdings * asset_rets).sum()\n"
            "holdings = holdings * (1 + asset_rets) / (1 + port_ret)  # NAV renormalize\n"
            "net = ret_series - cost_series",
            sty,
        )
    )
    story.append(
        img(
            deep_figs["backtest_loop"],
            sty,
            "Figure 8. One bar of the cross-sectional simulation loop.",
            "图 8. 横截面仿真循环中的一根 K 线。",
        )
    )
    story.append(Spacer(1, 6))

    # --- Section 18: Cost Model Economics ---
    story.extend(h1("20. Deep Dive: Cost Model Economics", "20. 深入解析：成本模型经济学", sty))
    story.append(
        body(
            "File: <font face='Courier'>engine/costs.py</font>. Transaction costs are applied to "
            "one-way turnover (<font face='Courier'>0.5 · Σ|Δw|</font>). Three FX-oriented presets "
            "bracket realistic execution: OPTIMISTIC, BASELINE, and PESSIMISTIC. Variable cost rate = "
            "(proportional + spread + slippage) bps / 10,000.",
            "文件：<font face='Courier'>engine/costs.py</font>。交易成本作用于单边换手"
            "（<font face='Courier'>0.5 · Σ|Δw|</font>）。三种外汇取向预设框定现实执行："
            "OPTIMISTIC（乐观）、BASELINE（基准）、PESSIMISTIC（悲观）。"
            "可变成本率 = (比例 + 点差 + 滑点) bps / 10,000。",
            sty,
        )
    )
    story.append(
        bilingual_table(
            [
                ("Assumption", "假设"),
                ("Prop bps", "比例 bps"),
                ("Spread bps", "点差 bps"),
                ("Slippage bps", "滑点 bps"),
                ("Total var bps", "可变合计 bps"),
            ],
            [
                (
                    ("OPTIMISTIC", "乐观"),
                    ("0.5", "0.5"),
                    ("0.25", "0.25"),
                    ("0.1", "0.1"),
                    ("0.85", "0.85"),
                ),
                (
                    ("BASELINE", "基准"),
                    ("1.5", "1.5"),
                    ("0.75", "0.75"),
                    ("0.5", "0.5"),
                    ("2.75", "2.75"),
                ),
                (
                    ("PESSIMISTIC", "悲观"),
                    ("5.0", "5.0"),
                    ("3.0", "3.0"),
                    ("2.0", "2.0"),
                    ("10.0", "10.0"),
                ),
            ],
            sty,
        )
    )
    story.append(Spacer(1, 4))
    story.append(
        body(
            "Cost per rebalance ≈ <font face='Courier'>turnover × variable_bps / 10,000</font>. "
            "Strategies must remain attractive under BASELINE costs; promotion pressure requires "
            "survival under PESSIMISTIC assumptions. Walk-forward and robustness batteries re-run "
            "with cost stress.",
            "每次再平衡成本 ≈ <font face='Courier'>turnover × variable_bps / 10,000</font>。"
            "策略在 BASELINE 成本下仍需有吸引力；晋升压力要求经受 PESSIMISTIC 假设。"
            "滚动验证与稳健性套件以成本压力重跑。",
            sty,
        )
    )
    story.append(
        callout(
            "A strategy with Sharpe 2.0 under OPTIMISTIC but negative Sharpe under PESSIMISTIC "
            "is a cost-sensitivity failure, not a candidate for promotion.",
            "在 OPTIMISTIC 下夏普 2.0、在 PESSIMISTIC 下夏普为负的策略是成本敏感失败，"
            "不是晋升候选。",
            sty,
        )
    )
    story.append(Spacer(1, 6))

    # --- Section 19: Orchestrator Experiment Loop ---
    story.append(PageBreak())
    story.extend(h1("21. Deep Dive: Orchestrator Experiment Loop", "21. 深入解析：编排器实验循环", sty))
    story.append(
        body(
            "File: <font face='Courier'>orchestration/runner.py</font>. After "
            "<font face='Courier'>plan_research()</font> and dataset validation, the runner iterates "
            "candidate hypotheses. Each iteration is budget-gated "
            "(<font face='Courier'>budget.can_run_experiment()</font>) and cancel-aware "
            "(<font face='Courier'>db.is_cancelled(research_id)</font> checked between hypotheses).",
            "文件：<font face='Courier'>orchestration/runner.py</font>。"
            "在 <font face='Courier'>plan_research()</font> 与数据集校验之后，"
            "运行器遍历候选假设。每次迭代受预算门控"
            "（<font face='Courier'>budget.can_run_experiment()</font>）并感知取消"
            "（假设间检查 <font face='Courier'>db.is_cancelled(research_id)</font>）。",
            sty,
        )
    )
    story.extend(h2("21.1 Feature → dataset mapping", "21.1 特征 → 数据集映射", sty))
    story.append(
        bilingual_table(
            [
                ("Feature", "特征"),
                ("SIGNAL_MAP key", "映射键"),
                ("Dataset", "数据集"),
                ("Lookback (typical)", "回看（典型）"),
            ],
            [
                (
                    ("carry", "carry"),
                    ("cross_sectional_carry", "cross_sectional_carry"),
                    ("fx_synthetic_momentum", "fx_synthetic_momentum"),
                    ("60", "60"),
                ),
                (
                    ("reversal", "reversal"),
                    ("short_term_reversal", "short_term_reversal"),
                    ("fx_synthetic_meanrev", "fx_synthetic_meanrev"),
                    ("1", "1"),
                ),
                (
                    ("volatility", "volatility"),
                    ("volatility_ranked", "volatility_ranked"),
                    ("fx_synthetic_momentum", "fx_synthetic_momentum"),
                    ("20", "20"),
                ),
                (
                    ("value", "value"),
                    ("value_proxy", "value_proxy"),
                    ("fx_synthetic_meanrev", "fx_synthetic_meanrev"),
                    ("20", "20"),
                ),
                (
                    ("liquidity", "liquidity"),
                    ("liquidity_stability", "liquidity_stability"),
                    ("fx_synthetic_momentum", "fx_synthetic_momentum"),
                    ("20", "20"),
                ),
            ],
            sty,
        )
    )
    story.extend(h2("21.2 Per-hypothesis pipeline", "21.2 每个假设的流水线", sty))
    story.append(
        bullets(
            [
                (
                    "Map hypothesis name → feature via <font face='Courier'>SIGNAL_MAP</font>.",
                    "经 <font face='Courier'>SIGNAL_MAP</font> 将假设名映射到特征。",
                ),
                (
                    "Persist Strategy with lookback, signal, rebalance_every; link hypothesis edge.",
                    "持久化 Strategy（含 lookback、signal、rebalance_every）；链接假设边。",
                ),
                (
                    "Create Experiment; call <font face='Courier'>run_backtest</font> via ToolRouter.",
                    "创建 Experiment；经 ToolRouter 调用 <font face='Courier'>run_backtest</font>。",
                ),
                (
                    "Run walk-forward, robustness, regime, diversification vs seeded momentum alpha.",
                    "运行滚动验证、稳健性、市场状态、相对种子动量 Alpha 的分散性分析。",
                ),
                (
                    "Adversarial review emits severity-tagged findings; survivors may register as Alpha.",
                    "对抗性审查产出带严重级别的发现；幸存者可能注册为 Alpha。",
                ),
            ],
            sty,
        )
    )
    story.append(
        code_block(
            "# Pseudocode — orchestration/runner.py inner loop\n"
            "for hyp in plan.candidate_hypotheses:\n"
            "    if db.is_cancelled(research_id): break\n"
            "    if not budget.can_run_experiment(): break\n"
            "    feature = SIGNAL_MAP.get(hyp.name, \"momentum\")\n"
            "    dataset = DATASET_FOR[feature]  # momentum vs meanrev panel\n"
            "    strategy = Strategy(..., parameters={lookback, signal, rebalance_every})\n"
            "    budget.consume_experiment()\n"
            "    exp = tools.call(\"create_experiment\", hypothesis_id=hyp.hypothesis_id, ...)\n"
            "    bt  = tools.call(\"run_backtest\", experiment_id=exp.id, dataset_id=dataset, ...)\n"
            "    wf  = tools.call(\"walk_forward\", ...)\n"
            "    rob = tools.call(\"robustness_battery\", ...)\n"
            "    div = tools.call(\"analyze_diversification\", vs=\"ALP-existing-momentum\")\n"
            "    rev = adversarial_review(candidate, evidence)\n"
            "    maybe_register_alpha(bt, metrics_source_ids=[bt.backtest_id])",
            sty,
        )
    )
    story.append(
        img(
            deep_figs["experiment_pipeline"],
            sty,
            "Figure 9. Budgeted hypothesis → experiment → validation loop.",
            "图 9. 有预算的 假设→实验→验证 循环。",
        )
    )
    story.append(Spacer(1, 6))

    # --- Section 20: Hypothesis Catalog & Falsification ---
    story.extend(h1("22. Deep Dive: Hypothesis Catalog &amp; Falsification", "22. 深入解析：假设目录与证伪", sty))
    story.append(
        body(
            "File: <font face='Courier'>agents/core.py</font> — "
            "<font face='Courier'>plan_research()</font> emits five fixed candidate hypotheses. "
            "Each carries explicit <font face='Courier'>falsification_criteria</font> so researchers "
            "know in advance what evidence would reject the idea.",
            "文件：<font face='Courier'>agents/core.py</font> — "
            "<font face='Courier'>plan_research()</font> 产出五个固定候选假设。"
            "每个假设带有明确的 <font face='Courier'>falsification_criteria</font>，"
            "使研究员事先知道何种证据会否决该想法。",
            sty,
        )
    )
    story.append(
        bilingual_table(
            [
                ("Hypothesis", "假设"),
                ("Economic intuition", "经济直觉"),
                ("Falsification criteria", "证伪标准"),
            ],
            [
                (
                    ("cross_sectional_carry", "横截面 carry"),
                    ("High-yield currencies earn carry premium", "高息货币赚取 carry 溢价"),
                    ("OOS Sharpe ≤ 0 after costs or corr(momentum) &gt; 0.5", "成本后 OOS 夏普 ≤ 0 或与动量相关 &gt; 0.5"),
                ),
                (
                    ("short_term_reversal", "短期反转"),
                    ("Transitory flows reverse over short horizons", "短期资金流反转"),
                    ("Fails walk-forward or excessive turnover under costs", "滚动验证失败或成本下换手过高"),
                ),
                (
                    ("volatility_ranked", "波动率排序"),
                    ("Relative vol forecasts risk-adjusted opportunity", "相对波动预测风险调整机会"),
                    ("No OOS edge; pure risk packaging without alpha", "无 OOS 优势；纯风险包装无 alpha"),
                ),
                (
                    ("value_proxy", "价值代理"),
                    ("Mean-reversion to longer-run fair value", "向长期公允价值均值回复"),
                    ("Collapses to slow momentum/reversal with high corr", "坍缩为高相关的慢动量/反转"),
                ),
                (
                    ("liquidity_stability", "流动性稳定"),
                    ("Stable/liquid names earn premium in stress", "稳定/高流动名称在压力下溢价"),
                    ("Indistinguishable from low-vol factor; no diversification", "与低波因子不可区分；无分散性"),
                ),
            ],
            sty,
        )
    )
    story.append(Spacer(1, 4))
    story.append(
        callout(
            "Success criteria (plan-level): OOS Sharpe &gt; 0.3 after baseline costs, "
            "|corr(momentum)| &lt; 0.35, parameter surface not fragile, adversarial severity &lt; CRITICAL.",
            "成功标准（计划级）：基准成本后 OOS 夏普 &gt; 0.3，"
            "|corr(动量)| &lt; 0.35，参数面不脆弱，对抗性严重度 &lt; CRITICAL。",
            sty,
        )
    )
    story.append(Spacer(1, 6))

    # --- Section 21: Storage Schema & Trace Model ---
    story.extend(h1("23. Deep Dive: Storage Schema &amp; Trace Model", "23. 深入解析：存储模式与轨迹模型", sty))
    story.append(
        body(
            "File: <font face='Courier'>storage/db.py</font>. SQLite stores JSON payloads with indexed "
            "columns for status queries. WAL mode and <font face='Courier'>foreign_keys=ON</font> are "
            "enabled. Every orchestrator action writes structured "
            "<font face='Courier'>agent_traces</font> rows.",
            "文件：<font face='Courier'>storage/db.py</font>。SQLite 存储 JSON 载荷，"
            "索引列支持状态查询。启用 WAL 与 <font face='Courier'>foreign_keys=ON</font>。"
            "每个编排动作写入结构化 <font face='Courier'>agent_traces</font> 行。",
            sty,
        )
    )
    story.append(
        code_block(
            "research_requests(research_id PK, payload, status, created_at)\n"
            "research_plans(research_id PK → requests, payload, created_at)\n"
            "hypotheses(hypothesis_id PK, research_id, payload)\n"
            "experiments(experiment_id PK, research_id, payload, status,\n"
            "             configuration_hash, created_at)\n"
            "strategies(strategy_id PK, payload, version)\n"
            "alphas(alpha_id PK, strategy_id, payload, status)\n"
            "backtest_results(backtest_id PK, experiment_id, payload)\n"
            "validation_results(validation_id PK, experiment_id, payload)\n"
            "reports(research_id PK, payload, decision, created_at)\n"
            "agent_traces(id, research_id, agent, event_type, payload, created_at)\n"
            "lineage_edges(src_type, src_id, rel, dst_type, dst_id, meta)\n"
            "checkpoints(research_id, node, payload, ...)",
            sty,
        )
    )
    story.extend(h2("23.1 Lineage edges and traces", "23.1 血缘边与轨迹", sty))
    story.append(
        bullets(
            [
                ("research —has_hypothesis→ hypothesis", "research —has_hypothesis→ hypothesis"),
                ("hypothesis —implements→ strategy", "hypothesis —implements→ strategy"),
                ("strategy —used_in→ experiment", "strategy —used_in→ experiment"),
                ("experiment —produced→ backtest", "experiment —produced→ backtest"),
                ("experiment —validated_by→ validation", "experiment —validated_by→ validation"),
                (
                    "Alpha.metrics_source_ids → backtest_id(s) for provenance",
                    "Alpha.metrics_source_ids → backtest_id（们）用于溯源",
                ),
                (
                    "agent_traces: planner, data, orchestrator, adversarial events with JSON payloads",
                    "agent_traces：规划、数据、编排、对抗性事件及 JSON 载荷",
                ),
            ],
            sty,
        )
    )
    story.append(Spacer(1, 6))

    # --- Section 22: API Contracts & UI Binding ---
    story.append(PageBreak())
    story.extend(h1("24. Deep Dive: API Contracts &amp; UI Binding", "24. 深入解析：API 契约与 UI 绑定", sty))
    story.append(
        body(
            "File: <font face='Courier'>api/app.py</font>. Base URL default: "
            "<font face='Courier'>http://127.0.0.1:8002</font>. Optional header "
            "<font face='Courier'>X-API-Key</font> when <font face='Courier'>QROS_API_KEY</font> is set. "
            "CORS allows workstation origin <font face='Courier'>:3012</font>.",
            "文件：<font face='Courier'>api/app.py</font>。默认基址："
            "<font face='Courier'>http://127.0.0.1:8002</font>。"
            "若设置 <font face='Courier'>QROS_API_KEY</font>，需头 "
            "<font face='Courier'>X-API-Key</font>。CORS 允许工作站来源 "
            "<font face='Courier'>:3012</font>。",
            sty,
        )
    )
    story.extend(h2("24.1 Experiment enrichment", "24.1 实验富化", sty))
    story.append(
        body(
            "<font face='Courier'>GET /experiments</font> returns registry rows joined with "
            "<font face='Courier'>backtest_results</font> metrics. Aliases "
            "<font face='Courier'>ann_return</font> and <font face='Courier'>ann_vol</font> are exposed "
            "so the workstation experiment table Sharpe column is never blank when a backtest exists.",
            "<font face='Courier'>GET /experiments</font> 返回注册表行并关联 "
            "<font face='Courier'>backtest_results</font> 指标。暴露别名 "
            "<font face='Courier'>ann_return</font> 与 <font face='Courier'>ann_vol</font>，"
            "使工作站实验表在存在回测时夏普列不为空。",
            sty,
        )
    )
    story.extend(h2("24.2 SWR vs UI state", "24.2 SWR 与 UI 状态", sty))
    story.append(
        bullets(
            [
                (
                    "<b>Server state (SWR)</b>: keys like "
                    "<font face='Courier'>overview-research</font>, "
                    "<font face='Courier'>research-{id}</font>, "
                    "<font face='Courier'>experiments-all</font>. Stale-while-revalidate polling.",
                    "<b>服务端状态（SWR）</b>：键如 "
                    "<font face='Courier'>overview-research</font>、"
                    "<font face='Courier'>research-{id}</font>、"
                    "<font face='Courier'>experiments-all</font>。陈旧-重验证轮询。",
                ),
                (
                    "<b>UI state (React)</b>: selected graph node, table sort, sidebar collapse, "
                    "command palette query — local component state / localStorage.",
                    "<b>UI 状态（React）</b>：选中图节点、表排序、侧栏折叠、"
                    "命令面板查询 — 组件本地状态 / localStorage。",
                ),
                (
                    "<b>SSE</b>: <font face='Courier'>GET /events/stream</font> emits "
                    "<font face='Courier'>research.updated</font>. EventSource cannot attach API keys; "
                    "UI falls back to SWR when key required.",
                    "<b>SSE</b>：<font face='Courier'>GET /events/stream</font> 发出 "
                    "<font face='Courier'>research.updated</font>。EventSource 无法附加 API key；"
                    "需要密钥时 UI 回退 SWR。",
                ),
            ],
            sty,
        )
    )
    story.append(
        code_block(
            "GET /research/{id} → {\n"
            "  request: { research_id, user_question, budget, status, ... },\n"
            "  plan: { objectives, hypotheses, success_criteria, ... },\n"
            "  report: { executive_summary, survivors, decision, ... },\n"
            "  checkpoint: { node, payload } | null\n"
            "}\n"
            "GET /research/{id}/trace → [ { agent, event_type, payload, created_at }, ... ]",
            sty,
        )
    )
    story.append(Spacer(1, 6))

    # --- Section 23: Traceability Drill-Down Example ---
    story.extend(h1("25. Deep Dive: Traceability Drill-Down Example", "25. 深入解析：可追溯下钻示例", sty))
    story.append(
        body(
            "Worked path for a flagship FX research run (synthetic panels). Numbers vary by seed; "
            "the evidence chain structure is invariant.",
            "旗舰外汇研究运行的走查路径（合成面板）。数字因种子而异；证据链结构不变。",
            sty,
        )
    )
    story.append(
        bilingual_table(
            [
                ("Step", "步骤"),
                ("Entity / field", "实体/字段"),
                ("What to inspect", "检查内容"),
            ],
            [
                (
                    ("1", "1"),
                    ("Report.decision", "Report.decision"),
                    ("REQUIRES_MORE_RESEARCH — honest outcome", "REQUIRES_MORE_RESEARCH — 诚实结果"),
                ),
                (
                    ("2", "2"),
                    ("Report.survivors[0].alpha_id", "幸存者 alpha_id"),
                    ("Link to alpha registry row", "链接 Alpha 注册表行"),
                ),
                (
                    ("3", "3"),
                    ("Alpha.metrics_source_ids", "metrics_source_ids"),
                    ("List of backtest_id values — provenance anchor", "backtest_id 列表 — 溯源锚点"),
                ),
                (
                    ("4", "4"),
                    ("backtest_results.payload", "回测载荷"),
                    ("Sharpe, Sortino, MDD, turnover, cost breakdown", "夏普、索提诺、MDD、换手、成本分解"),
                ),
                (
                    ("5", "5"),
                    ("experiments.configuration_hash", "配置哈希"),
                    ("Reproducibility fingerprint (params + dataset + costs)", "可复现指纹（参数+数据+成本）"),
                ),
                (
                    ("6", "6"),
                    ("agent_traces (orchestrator)", "编排轨迹"),
                    ("Tool call params/results for run_backtest, walk_forward", "run_backtest、walk_forward 工具调用参数/结果"),
                ),
            ],
            sty,
        )
    )
    story.append(
        bullets(
            [
                ("Report conclusion → survivor alpha_id", "报告结论 → 幸存者 alpha_id"),
                ("Alpha.metrics_source_ids → backtest_id", "Alpha.metrics_source_ids → backtest_id"),
                ("backtest_id → experiment_id → strategy parameters", "backtest_id → experiment_id → 策略参数"),
                ("Trace → exact tool inputs that produced the number", "轨迹 → 产生该数字的精确工具输入"),
            ],
            sty,
        )
    )
    story.append(
        img(
            deep_figs["traceability_example"],
            sty,
            "Figure 10. Report → experiment → backtest → trace drill-down.",
            "图 10. 报告 → 实验 → 回测 → 轨迹下钻。",
        )
    )
    story.append(Spacer(1, 6))

    # --- Section 24: Threats to Validity & Research Hygiene ---
    story.extend(h1("26. Threats to Validity &amp; Research Hygiene", "26. 效度威胁与研究卫生", sty))
    story.append(
        body(
            "Quant Research OS is a laboratory, not a live trading system. Researchers must actively "
            "guard against threats that make backtests look better than deployable reality.",
            "Quant Research OS 是实验室，不是实盘系统。研究员必须主动防范"
            "使回测看起来优于可部署现实的威胁。",
            sty,
        )
    )
    story.extend(h2("26.1 Threat catalog", "26.1 威胁目录", sty))
    story.append(
        bilingual_table(
            [
                ("Threat", "威胁"),
                ("Manifestation in QROS", "在 QROS 中的表现"),
                ("Mitigation", "缓解"),
            ],
            [
                (
                    ("Look-ahead bias", "前视偏差"),
                    ("Same-bar execution on new weights", "新权重同一根 K 线执行"),
                    ("execution_lag ≥ 1 enforced in engine", "引擎强制 execution_lag ≥ 1"),
                ),
                (
                    ("Overfitting / data snooping", "过拟合/数据窥探"),
                    ("Many hypotheses on same panel", "同一面板上多假设"),
                    ("Budget caps, walk-forward, adversarial review", "预算上限、滚动验证、对抗性审查"),
                ),
                (
                    ("Cost underestimation", "成本低估"),
                    ("Ignoring spread/slippage", "忽略点差/滑点"),
                    ("Three-tier FX cost presets; pessimistic stress", "三层 FX 成本预设；悲观压力"),
                ),
                (
                    ("Metric inconsistency", "指标不一致"),
                    ("ddof=1 Sharpe from external lib", "外部库 ddof=1 夏普"),
                    ("Pinned metrics.py; sibling imports disabled", "固定 metrics.py；禁用兄弟库"),
                ),
                (
                    ("Narrative invention", "叙述编造"),
                    ("Agent prose without tool backing", "无工具支撑的智能体 prose"),
                    ("Numbers only via ToolRouter; metrics_source_ids", "数字仅经 ToolRouter；metrics_source_ids"),
                ),
                (
                    ("Mode confusion", "模式混淆"),
                    ("PAPER / synthetic treated as LIVE", "模拟盘/合成数据当成实盘"),
                    ("UI banners; BACKTEST labels on synthetic data", "UI 横幅；合成数据 BACKTEST 标签"),
                ),
                (
                    ("Survivorship in alpha library", "Alpha 库幸存者偏差"),
                    ("Only winners visible", "仅见赢家"),
                    ("Failed experiments persisted; adversarial findings surfaced", "失败实验持久化；对抗性发现展示"),
                ),
            ],
            sty,
        )
    )
    story.extend(h2("26.2 Practitioner checklist", "26.2 从业者清单", sty))
    story.append(
        bullets(
            [
                (
                    "Verify Sharpe by recomputing from stored net returns with ddof=0 formulas.",
                    "用 ddof=0 公式从已存净收益重算以验证夏普。",
                ),
                (
                    "Check OOS walk-forward Sharpe, not just in-sample.",
                    "检查 OOS 滚动验证夏普，而非仅样本内。",
                ),
                (
                    "Re-run under PESSIMISTIC costs before any promotion narrative.",
                    "任何晋升叙述前在 PESSIMISTIC 成本下重跑。",
                ),
                (
                    "Confirm |corr vs momentum| &lt; 0.35 for diversification claims.",
                    "对分散性声明确认 |相对动量相关| &lt; 0.35。",
                ),
                (
                    "Drill report → metrics_source_ids → backtest payload before trusting a number.",
                    "信任数字前先下钻 报告 → metrics_source_ids → 回测载荷。",
                ),
                (
                    "Read adversarial findings — HIGH/CRITICAL blocks promotion.",
                    "阅读对抗性发现 — HIGH/CRITICAL 阻断晋升。",
                ),
                (
                    "Treat synthetic FX panels (fx_synthetic_*) as structural demos, not live edge.",
                    "将合成 FX 面板（fx_synthetic_*）视为结构演示，非实盘优势。",
                ),
                (
                    "Run pytest invariants: <font face='Courier'>tests/test_quant_invariants.py</font>.",
                    "运行 pytest 不变量：<font face='Courier'>tests/test_quant_invariants.py</font>。",
                ),
            ],
            sty,
        )
    )
    story.append(
        callout(
            "Extension rule: if a change lets natural language create a number that cannot be "
            "recomputed from stored returns + pinned formulas, reject the change.",
            "扩展规则：若某改动使自然语言能产生无法由已存收益 + 固定公式重算的数字，则拒绝该改动。",
            sty,
        )
    )
    story.append(Spacer(1, 6))
