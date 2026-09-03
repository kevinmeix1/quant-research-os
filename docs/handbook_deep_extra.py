"""Additional deep-dive handbook sections (27–33) for Quant Research OS."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from reportlab.platypus import PageBreak, Spacer


def _box(ax, xy, w, h, text, fc="#eef1f5", ec="#2f5f9e"):
    x, y = xy
    p = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.02", facecolor=fc, edgecolor=ec, lw=1.2)
    ax.add_patch(p)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=8, color="#12161d", wrap=True)


def _fig_walk_forward(path: Path) -> None:
    fig, ax = plt.subplots(figsize=(9.2, 3.4))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 4)
    ax.axis("off")
    ax.set_title("Walk-forward: expanding train → OOS test (deduped)", fontsize=11, pad=8)
    # timeline
    ax.plot([0.4, 9.6], [1.2, 1.2], color="#5a6575", lw=1.5)
    windows = [
        (0.5, 3.2, 3.2, 4.6, "W1"),
        (0.5, 4.6, 4.6, 6.0, "W2"),
        (0.5, 6.0, 6.0, 7.4, "W3"),
    ]
    colors_train = "#c5d4e8"
    colors_test = "#f0d9b5"
    for i, (ts, te, vs, ve, lab) in enumerate(windows):
        y = 2.6 - i * 0.55
        ax.barh(y, te - ts, left=ts, height=0.35, color=colors_train, edgecolor="#2f5f9e")
        ax.barh(y, ve - vs, left=vs, height=0.35, color=colors_test, edgecolor="#8a5a1a")
        ax.text(0.2, y, lab, fontsize=8, va="center")
    ax.text(2.0, 3.5, "train (expanding)", fontsize=8, color="#2f5f9e")
    ax.text(5.0, 3.5, "OOS test", fontsize=8, color="#8a5a1a")
    ax.text(5.0, 0.45, "Aggregate OOS Sharpe uses de-duplicated OOS return segments", fontsize=8, color="#5a6575")
    fig.tight_layout()
    fig.savefig(path, dpi=160, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def _fig_robustness(path: Path) -> None:
    fig, ax = plt.subplots(figsize=(7.5, 3.6))
    xs = [10, 15, 20, 25, 30, 40, 60]
    # illustrative surfaces
    smooth = [0.35, 0.42, 0.48, 0.50, 0.47, 0.40, 0.32]
    fragile = [0.20, 0.25, 0.28, 1.15, 0.30, 0.22, 0.18]
    ax.plot(xs, smooth, "o-", color="#2f5f9e", label="smooth / preferred")
    ax.plot(xs, fragile, "s--", color="#a33", label="fragile peak (overfit risk)")
    ax.axhline(0.3, color="#999", ls=":", lw=1)
    ax.set_xlabel("lookback")
    ax.set_ylabel("Sharpe")
    ax.set_title("Parameter surface: smooth plateau vs knife-edge peak")
    ax.legend(fontsize=8, loc="upper right")
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=160, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def _fig_tool_router(path: Path) -> None:
    fig, ax = plt.subplots(figsize=(9.0, 3.8))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 5)
    ax.axis("off")
    ax.set_title("ToolRouter: agents call tools; engines compute numbers", fontsize=11)
    _box(ax, (0.4, 2.0), 2.2, 1.4, "Agent\n(planner / data /\norchestrator)", fc="#eef1f5")
    _box(ax, (3.5, 2.0), 2.4, 1.4, "ToolRouter\nallowlist + audit", fc="#dfe8f4")
    _box(ax, (6.8, 3.2), 2.3, 1.2, "run_backtest\n→ CS engine", fc="#f7f1e6")
    _box(ax, (6.8, 1.6), 2.3, 1.2, "walk_forward /\nrobustness / regime", fc="#f7f1e6")
    _box(ax, (6.8, 0.2), 2.3, 1.1, "calculate_metrics\n(pinned)", fc="#f7f1e6")
    _box(ax, (9.8, 1.8), 1.8, 1.4, "SQLite\nartifacts +\nmetrics_source_ids", fc="#e8efe6")
    for y in (3.7, 2.1, 0.7):
        ax.annotate("", xy=(6.8, y), xytext=(5.9, 2.7), arrowprops=dict(arrowstyle="->", color="#2f5f9e", lw=1.2))
    ax.annotate("", xy=(3.5, 2.7), xytext=(2.6, 2.7), arrowprops=dict(arrowstyle="->", color="#2f5f9e", lw=1.2))
    ax.annotate("", xy=(9.8, 2.5), xytext=(9.1, 2.5), arrowprops=dict(arrowstyle="->", color="#2f5f9e", lw=1.2))
    fig.tight_layout()
    fig.savefig(path, dpi=160, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def make_extra_figures(fig_dir: Path) -> dict[str, Path]:
    fig_dir.mkdir(parents=True, exist_ok=True)
    out = {
        "walk_forward": fig_dir / "walk_forward.png",
        "robustness": fig_dir / "robustness_surface.png",
        "tool_router": fig_dir / "tool_router.png",
    }
    _fig_walk_forward(out["walk_forward"])
    _fig_robustness(out["robustness"])
    _fig_tool_router(out["tool_router"])
    return out


def append_extra_deep_sections(
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
    extra_figs,
) -> None:
    """Append bilingual deep-dive sections 27–33."""

    # --- 27 Walk-forward ---
    story.append(PageBreak())
    story.extend(h1("27. Deep Dive: Walk-Forward Validation", "27. 深入解析：滚动前瞻验证", sty))
    story.append(
        body(
            "File: <font face='Courier'>engine/walk_forward.py</font>. Walk-forward in QROS is "
            "<b>segmented out-of-sample evaluation of a frozen rule</b> — parameters in "
            "<font face='Courier'>CrossSectionalConfig</font> are treated as exogenous and are "
            "<b>not</b> re-fit inside each train window. This is intentionally stricter and more "
            "honest than nested parameter search that quietly overfits the train set.",
            "文件：<font face='Courier'>engine/walk_forward.py</font>。QROS 中的 walk-forward 是"
            "<b>对冻结规则的分段样本外评估</b>——"
            "<font face='Courier'>CrossSectionalConfig</font> 中的参数视为外生，"
            "<b>不会</b>在每个训练窗内重新拟合。这比在训练集上静默过拟合的嵌套参数搜索更严格、更诚实。",
            sty,
        )
    )
    story.extend(h2("27.1 Window modes and defaults", "27.1 窗口模式与默认值", sty))
    story.append(
        bilingual_table(
            [("Field", "字段"), ("Default", "默认"), ("Meaning", "含义")],
            [
                (("mode", "mode"), ("expanding_window", "expanding_window"), ("Train grows from t=0; alternate rolling_window", "训练自 t=0 扩展；可改 rolling")),
                (("train_bars", "train_bars"), ("126", "126"), ("~0.5y initial train (expanding)", "扩展模式初始训练约半年")),
                (("test_bars", "test_bars"), ("63", "63"), ("~1 quarter OOS per window", "每窗约一季样本外")),
                (("step_bars", "step_bars"), ("63", "63"), ("Advance train/test frontier", "训练/测试前沿步进")),
                (("rolling_train_bars", "rolling_train_bars"), ("252", "252"), ("1y train when mode=rolling", "滚动模式 1 年训练")),
                (("cost_assumption", "cost_assumption"), ("BASELINE", "BASELINE"), ("Costs applied inside each slice backtest", "每片回测内应用成本")),
            ],
            sty,
        )
    )
    story.extend(h2("27.2 Algorithm", "27.2 算法", sty))
    story.append(
        bullets(
            [
                (
                    "Build window bounds (train_start, train_end, test_start, test_end) exclusive end indices.",
                    "构建窗口边界（train_start…test_end），终点索引为开区间。",
                ),
                (
                    "For each window, run full <font face='Courier'>run_cross_sectional_backtest</font> on the price slice "
                    "(rolling mode prepends warm-up bars so lookback signals are defined).",
                    "每窗对价格切片跑完整 <font face='Courier'>run_cross_sectional_backtest</font>"
                    "（滚动模式前置预热 K 线，使回看信号有定义）。",
                ),
                (
                    "Extract only OOS returns in [test_start, test_end); store per-window metrics.",
                    "仅抽取 [test_start, test_end) 的样本外收益；保存每窗指标。",
                ),
                (
                    "Concatenate OOS segments with de-duplication so overlapping steps do not double-count.",
                    "拼接样本外片段并去重，避免步进重叠导致双重计数。",
                ),
                (
                    "Aggregate OOS Sharpe / return / drawdown from the de-duplicated OOS path — "
                    "this is the promotion-relevant number, not in-sample Sharpe.",
                    "由去重后的样本外路径汇总 OOS 夏普/收益/回撤——"
                    "这才是与晋升相关的数字，而非样本内夏普。",
                ),
            ],
            sty,
        )
    )
    story.append(
        code_block(
            "# engine/walk_forward.py (conceptual)\n"
            "for (ts, te, vs, ve) in _window_bounds(n, wf_cfg):\n"
            "    slice_prices = prices.iloc[:ve]          # expanding\n"
            "    # rolling: include warm-up before ts\n"
            "    bt = run_cross_sectional_backtest(slice_prices, cs_cfg, cost_model)\n"
            "    oos = returns_in_original_index[vs:ve]   # exclusive end\n"
            "    windows.append(WalkForwardWindow(..., metrics=calculate_metrics(oos)))\n"
            "aggregate = calculate_metrics(dedupe_concat(oos_parts))",
            sty,
        )
    )
    story.append(
        callout(
            "Interpretation: a strategy with IS Sharpe 1.8 but aggregate OOS Sharpe ≤ 0 is a "
            "failed candidate — regardless of narrative quality.",
            "解读：样本内夏普 1.8 但汇总 OOS 夏普 ≤ 0 的策略是失败候选——"
            "无论叙述多漂亮。",
            sty,
        )
    )
    story.append(
        img(
            extra_figs["walk_forward"],
            sty,
            "Figure 11. Expanding walk-forward train/test schedule.",
            "图 11. 扩展式 walk-forward 训练/测试日程。",
        )
    )

    # --- 28 Robustness ---
    story.extend(h1("28. Deep Dive: Robustness &amp; Fragility", "28. 深入解析：稳健性与脆弱性", sty))
    story.append(
        body(
            "File: <font face='Courier'>engine/robustness.py</font> — "
            "<font face='Courier'>analyze_parameter_surface()</font>. "
            "The battery re-runs the cross-sectional backtest across a grid of one parameter "
            "(default: lookback ∈ {10,15,20,25,30,40,60}) and classifies the Sharpe surface.",
            "文件：<font face='Courier'>engine/robustness.py</font> — "
            "<font face='Courier'>analyze_parameter_surface()</font>。"
            "套件在单一参数网格上重跑横截面回测（默认 lookback ∈ {10,15,20,25,30,40,60}），"
            "并对夏普曲面分类。",
            sty,
        )
    )
    story.extend(h2("28.1 Fragility and smoothness rules", "28.1 脆弱性与平滑规则", sty))
    story.append(
        bullets(
            [
                (
                    "<b>Fragile</b>: interior peak Sharpe exceeds neighbor mean by &gt; 0.5 AND peak Sharpe &gt; 0.3 "
                    "→ flagged as possible overfit knife-edge.",
                    "<b>脆弱</b>：内部峰值夏普高于邻域均值 &gt; 0.5 且峰值 &gt; 0.3 → 标记为可能过拟合的刀锋峰。",
                ),
                (
                    "<b>Boundary peak</b>: peak at first/last grid point → note to extend the grid before calling knife-edge.",
                    "<b>边界峰</b>：峰在网格首/末点 → 提示先扩展网格再下刀锋结论。",
                ),
                (
                    "<b>Smooth</b>: mean |ΔSharpe| across adjacent grid points &lt; 0.35.",
                    "<b>平滑</b>：相邻网格点平均 |Δ夏普| &lt; 0.35。",
                ),
                (
                    "Preferred outcome: broad-ish stable region with positive Sharpe — not a single spike.",
                    "更优结果：宽平台、正夏普区域——而非单点尖峰。",
                ),
            ],
            sty,
        )
    )
    story.append(
        code_block(
            "# Fragility test (interior peaks)\n"
            "gap = peak_sharpe - mean(neighbor_sharpes)\n"
            "fragile = (gap > 0.5) and (peak_sharpe > 0.3)\n"
            "smooth = mean(abs(diff(sharpes))) < 0.35",
            sty,
        )
    )
    story.append(
        img(
            extra_figs["robustness"],
            sty,
            "Figure 12. Illustrative smooth vs fragile lookback surfaces.",
            "图 12. 平滑 vs 脆弱 lookback 曲面示意。",
        )
    )
    story.append(
        callout(
            "Adversarial review treats fragile=True / jagged surfaces as promotion blockers even when "
            "the chosen lookback prints a high in-sample Sharpe.",
            "对抗性审查将 fragile=True / 锯齿曲面视为晋升阻断，即使所选 lookback 样本内夏普很高。",
            sty,
        )
    )

    # --- 29 Regimes ---
    story.extend(h1("29. Deep Dive: Regime Analysis", "29. 深入解析：市场状态分析", sty))
    story.append(
        body(
            "File: <font face='Courier'>engine/regime.py</font>. Labels are <b>heuristic</b> "
            "(rolling volatility tertiles × risk-on/off trend), not a claim of true latent states. "
            "Confidence is intentionally low (~0.4) so UI/report consumers do not over-trust the taxonomy.",
            "文件：<font face='Courier'>engine/regime.py</font>。标签是<b>启发式</b>的"
            "（滚动波动率三分位 × 风险偏好趋势），并非真实隐状态声明。"
            "置信度故意偏低（~0.4），避免 UI/报告读者过度信任该分类。",
            sty,
        )
    )
    story.append(
        bullets(
            [
                (
                    "vol = rolling_std(market_proxy, 20); trend = rolling_mean(market_proxy, 20).",
                    "vol = 市场代理 20 日滚动标准差；trend = 20 日滚动均值。",
                ),
                (
                    "vol_bin ∈ {low_vol, mid_vol, high_vol}; trend_bin ∈ {risk_on, risk_off}.",
                    "vol_bin ∈ {low_vol, mid_vol, high_vol}；trend_bin ∈ {risk_on, risk_off}。",
                ),
                (
                    "Label string: <font face='Courier'>\"{vol}|{trend}\"</font>; shifted by 1 bar so day-t "
                    "return is attributed to regimes known through t−1 (no same-day leakage).",
                    "标签：<font face='Courier'>\"{vol}|{trend}\"</font>；平移 1 根 K 线，"
                    "使第 t 日收益归因于截至 t−1 已知状态（无同日泄漏）。",
                ),
                (
                    "Per-regime metrics via pinned <font face='Courier'>calculate_metrics</font> "
                    "(skip cells with &lt; 5 observations).",
                    "各状态指标经固定 <font face='Courier'>calculate_metrics</font> 计算"
                    "（观测 &lt; 5 的单元跳过）。",
                ),
                (
                    "Concentration note when best regime Sharpe &gt; 0.5 and worst &lt; 0.",
                    "当最佳状态夏普 &gt; 0.5 且最差 &lt; 0 时附加集中度备注。",
                ),
            ],
            sty,
        )
    )
    story.append(
        callout(
            "A strategy that only works in one historical regime slice is not book-ready — "
            "even if full-sample Sharpe looks fine.",
            "仅在单一历史状态切片有效的策略不具备入册条件——"
            "即使全样本夏普看起来不错。",
            sty,
        )
    )

    # --- 30 Diversification ---
    story.extend(h1("30. Deep Dive: Diversification Mathematics", "30. 深入解析：分散化数学", sty))
    story.append(
        body(
            "File: <font face='Courier'>alpha/registry.py</font> — "
            "<font face='Courier'>analyze_diversification()</font>. "
            "Flagship workflow compares candidates against seeded "
            "<font face='Courier'>ALP-existing-momentum</font>.",
            "文件：<font face='Courier'>alpha/registry.py</font> — "
            "<font face='Courier'>analyze_diversification()</font>。"
            "旗舰流程将候选与种子 <font face='Courier'>ALP-existing-momentum</font> 比较。",
            sty,
        )
    )
    story.append(
        bilingual_table(
            [("Output field", "输出字段"), ("Definition", "定义"), ("Promotion heuristic", "晋升启发式")],
            [
                (
                    ("return_correlations", "收益相关"),
                    ("Pearson corr(candidate, existing_i) on aligned days", "对齐日上 Pearson 相关"),
                    ("Track max |corr| vs book", "跟踪相对组合的最大 |相关|"),
                ),
                (
                    ("downside_correlations", "下行相关"),
                    ("Corr on days where either series is negative", "任一侧为负的日子上的相关"),
                    ("Crash co-movement matters more than calm corr", "崩盘共动比平静相关更重要"),
                ),
                (
                    ("genuine_diversification", "真实分散"),
                    ("|avg corr| &lt; 0.35 AND |avg downside corr| &lt; 0.45", "|平均相关| &lt; 0.35 且 |平均下行相关| &lt; 0.45"),
                    ("False → duplicate risk bet", "False → 重复风险押注"),
                ),
                (
                    ("incremental_sharpe_hint", "增量夏普提示"),
                    ("Equal-weight existing vs existing+candidate Sharpe (ddof=0)", "既有等权 vs 既有+候选 夏普（ddof=0）"),
                    ("delta &gt; 0 preferred but not sufficient alone", "delta &gt; 0 更优但单独不足"),
                ),
            ],
            sty,
        )
    )
    story.append(
        code_block(
            "# Diversification core\n"
            "corr = aligned.c.corr(aligned.e)\n"
            "down_mask = (aligned.c < 0) | (aligned.e < 0)\n"
            "down_corr = aligned.loc[down_mask].corr()\n"
            "genuine = abs(avg_corr) < 0.35 and abs(avg_down) < 0.45\n"
            "port_old = existing_df.mean(axis=1)\n"
            "port_new = concat([port_old, candidate], axis=1).mean(axis=1)\n"
            "delta = sharpe(port_new) - sharpe(port_old)   # ddof=0 annualized",
            sty,
        )
    )
    story.append(Spacer(1, 6))

    # --- 31 ToolRouter ---
    story.extend(h1("31. Deep Dive: ToolRouter &amp; Allowlist", "31. 深入解析：ToolRouter 与白名单", sty))
    story.append(
        body(
            "File: <font face='Courier'>tools/router.py</font>. Agents never call engine functions "
            "directly for research numbers. They invoke named tools through "
            "<font face='Courier'>ToolRouter</font>, which enforces an allowlist, records audit payloads, "
            "and returns structured <font face='Courier'>ToolResult</font> objects. "
            "This is the hard boundary that prevents LLM prose from inventing Sharpes.",
            "文件：<font face='Courier'>tools/router.py</font>。智能体从不直接调用引擎函数获取研究数字。"
            "它们经 <font face='Courier'>ToolRouter</font> 调用具名工具；路由强制白名单、记录审计载荷，"
            "并返回结构化 <font face='Courier'>ToolResult</font>。"
            "这是阻止 LLM 叙述编造夏普的硬边界。",
            sty,
        )
    )
    story.append(
        bilingual_table(
            [("Tool", "工具"), ("Engine / store", "引擎/存储"), ("Produces", "产出")],
            [
                (("create_experiment", "create_experiment"), ("SQLite experiments", "SQLite experiments"), ("experiment_id + configuration_hash", "实验 ID + 配置哈希")),
                (("run_backtest", "run_backtest"), ("cross_sectional + metrics + costs", "横截面+指标+成本"), ("backtest_id, returns, PerformanceMetrics", "回测 ID、收益、指标")),
                (("walk_forward", "walk_forward"), ("walk_forward.py", "walk_forward.py"), ("OOS windows + aggregate", "样本外窗 + 汇总")),
                (("robustness_battery", "robustness_battery"), ("robustness.py", "robustness.py"), ("surface, fragile, smooth", "曲面、脆弱、平滑")),
                (("analyze_diversification", "analyze_diversification"), ("alpha/registry.py", "alpha/registry.py"), ("corr, genuine_diversification", "相关、真实分散")),
                (("run_stress_test", "run_stress_test"), ("portfolio.py", "portfolio.py"), ("stress scenarios", "压力情景")),
                (("run_bootstrap", "run_bootstrap"), ("statistics.py", "statistics.py"), ("uncertainty / multiple-testing aware stats", "不确定性/多重检验感知统计")),
            ],
            sty,
        )
    )
    story.append(
        img(
            extra_figs["tool_router"],
            sty,
            "Figure 13. Numbers flow Agent → ToolRouter → Engine → Storage.",
            "图 13. 数字流：智能体 → ToolRouter → 引擎 → 存储。",
        )
    )
    story.append(
        callout(
            "Extension rule: new research capabilities must land as allowlisted tools with "
            "deterministic engines behind them — never as free-form model arithmetic.",
            "扩展规则：新研究能力必须以白名单工具落地、背后是确定性引擎——"
            "绝非自由形式的模型算术。",
            sty,
        )
    )

    # --- 32 Worked numerical example ---
    story.append(PageBreak())
    story.extend(h1("32. Worked Example: From Returns to Decision", "32. 演算示例：从收益到决策", sty))
    story.append(
        body(
            "The following toy path illustrates how a researcher should mentally audit a candidate. "
            "Numbers are pedagogical (not a live run dump).",
            "以下玩具路径说明研究员应如何心智审计一个候选。"
            "数字用于教学（非实况运行转储）。",
            sty,
        )
    )
    story.extend(h2("32.1 Net daily returns → pinned metrics", "32.1 净日收益 → 固定指标", sty))
    story.append(
        body(
            "Suppose a 5-day net return series after costs: "
            "<font face='Courier'>r = [+0.4%, −0.2%, +0.3%, −0.1%, +0.2%]</font>. "
            "Equity path: <font face='Courier'>1.004 → 1.0020 → 1.0050 → 1.0040 → 1.0060</font>. "
            "Cumulative ≈ +0.60%. With N=5 the annualization factor is noisy — in production N is hundreds "
            "of bars — but the formulas stay identical: "
            "<font face='Courier'>σ = std(r, ddof=0)·√252</font>, "
            "<font face='Courier'>Sharpe = mean(r)/std(r,ddof=0)·√252</font> (rf=0).",
            "假设成本后 5 日净收益序列："
            "<font face='Courier'>r = [+0.4%, −0.2%, +0.3%, −0.1%, +0.2%]</font>。"
            "权益路径：<font face='Courier'>1.004 → 1.0020 → 1.0050 → 1.0040 → 1.0060</font>。"
            "累计 ≈ +0.60%。N=5 时年化噪声大——生产中 N 为数百根 K 线——但公式不变："
            "<font face='Courier'>σ = std(r, ddof=0)·√252</font>，"
            "<font face='Courier'>Sharpe = mean(r)/std(r,ddof=0)·√252</font>（rf=0）。",
            sty,
        )
    )
    story.extend(h2("32.2 Cost stress", "32.2 成本压力", sty))
    story.append(
        body(
            "If average one-way turnover per rebalance is 0.40 and rebalance_every=5, "
            "daily average turnover ≈ 0.40/5 = 0.08. Under BASELINE (2.75 bps variable) "
            "daily cost ≈ 0.08 × 2.75e-4 = 2.2e-5 (~0.22 bps/day). Under PESSIMISTIC (10 bps) "
            "≈ 0.8 bps/day. A thin edge that disappears under this haircut is not promotable.",
            "若每次再平衡单边换手 0.40 且 rebalance_every=5，"
            "日均换手 ≈ 0.40/5 = 0.08。BASELINE（2.75 bps 可变）下"
            "日成本 ≈ 0.08 × 2.75e-4 = 2.2e-5（约 0.22 bps/日）。PESSIMISTIC（10 bps）下"
            "≈ 0.8 bps/日。被这层摩擦吃掉的薄优势不可晋升。",
            sty,
        )
    )
    story.extend(h2("32.3 Decision table", "32.3 决策表", sty))
    story.append(
        bilingual_table(
            [("Check", "检查"), ("Pass criterion", "通过标准"), ("Example outcome", "示例结果")],
            [
                (("IS Sharpe (audit only)", "样本内夏普（仅审计）"), ("Recomputable from returns", "可由收益重算"), ("1.1 — not decisive", "1.1 — 非决定性")),
                (("OOS Sharpe", "OOS 夏普"), ("&gt; 0.3 after BASELINE costs", "BASELINE 成本后 &gt; 0.3"), ("0.18 — fail", "0.18 — 失败")),
                (("Fragility", "脆弱性"), ("fragile=False, smooth≈True", "fragile=False，smooth≈True"), ("fragile=True — fail", "fragile=True — 失败")),
                (("|corr(momentum)|", "|corr(动量)|"), ("&lt; 0.35", "&lt; 0.35"), ("0.62 — duplicate risk", "0.62 — 重复风险")),
                (("Adversarial", "对抗性"), ("severity &lt; CRITICAL", "严重度 &lt; CRITICAL"), ("HIGH cost sensitivity", "HIGH 成本敏感")),
                (("Decision", "决策"), ("PROMOTABLE / MORE_RESEARCH / REJECT", "可晋升 / 需更多研究 / 拒绝"), ("REQUIRES_MORE_RESEARCH", "REQUIRES_MORE_RESEARCH")),
            ],
            sty,
        )
    )
    story.append(
        callout(
            "Honest outcome for the flagship synthetic FX demo is often REQUIRES_MORE_RESEARCH — "
            "that is a feature of scientific hygiene, not a product defect.",
            "旗舰合成外汇演示的诚实结果常常是 REQUIRES_MORE_RESEARCH——"
            "这是科研卫生的特性，不是产品缺陷。",
            sty,
        )
    )

    # --- 33 UI page-by-page ---
    story.extend(h1("33. Workstation Page-by-Page Guide", "33. 工作站逐页指南", sty))
    story.append(
        body(
            "The Next.js app under <font face='Courier'>web/</font> is the daily operator surface. "
            "Each page has one primary job. Use this map when onboarding or auditing a run.",
            "<font face='Courier'>web/</font> 下的 Next.js 应用是日常操作面。"
            "每页只有一个主职责。入门或审计运行时用此地图。",
            sty,
        )
    )
    story.append(
        bilingual_table(
            [("Route", "路由"), ("Primary job", "主职责"), ("Evidence to open next", "下一步打开的证据")],
            [
                (("/ ", "/"), ("Fleet pulse: latest research, counts, health", "总览：最新研究、计数、健康"), ("Click research → /research/[id]", "点研究 → /research/[id]")),
                (("/research", "/research"), ("Queue of research requests + statuses", "研究请求队列与状态"), ("Open workspace for a run", "打开某次运行的工作区")),
                (("/research/[id]", "/research/[id]"), ("Workflow graph, plan, agents, report", "工作流图、计划、智能体、报告"), ("Experiments sorted by Sharpe", "按夏普排序的实验")),
                (("/experiments", "/experiments"), ("All experiments with enriched metrics", "全部实验（富化指标）"), ("Row → config hash + backtest", "行 → 配置哈希 + 回测")),
                (("/alphas", "/alphas"), ("Library status + metrics_source_ids", "库状态 + metrics_source_ids"), ("Drill to source backtest", "下钻到来源回测")),
                (("/portfolio", "/portfolio"), ("What-if book + Alpha X", "情景：组合 + Alpha X"), ("Risk page for concentration", "风险页看集中度")),
                (("/risk", "/risk"), ("Correlation / concentration alerts", "相关/集中度告警"), ("Reject high-corr adds", "拒绝高相关新增")),
                (("/data", "/data"), ("Dataset catalog / synthetic panels", "数据集目录/合成面板"), ("Confirm fx_synthetic_* labels", "确认 fx_synthetic_* 标签")),
                (("/regimes", "/regimes"), ("Regime performance breakdown", "状态绩效分解"), ("Check concentration notes", "检查集中度备注")),
                (("/paper", "/paper"), ("Paper mode (IID honesty banners)", "模拟盘（IID 诚实横幅）"), ("Never treat as LIVE", "绝不当作实盘")),
                (("/reports", "/reports"), ("Decision + survivors + narrative", "决策 + 幸存者 + 叙述"), ("Traceability chain", "可追溯链")),
                (("/agents", "/agents"), ("Allowlist / agent roles", "白名单/角色"), ("Inspector payloads", "检查器载荷")),
                (("/memory", "/memory"), ("Prior findings / memory store", "既有发现/记忆库"), ("Avoid repeating failed ideas", "避免重复失败想法")),
                (("/system", "/system"), ("API health, versions, ops", "API 健康、版本、运维"), ("Restart / key config", "重启/密钥配置")),
            ],
            sty,
        )
    )
    story.extend(h2("33.1 Research workspace mental model", "33.1 研究工作区心智模型", sty))
    story.append(
        bullets(
            [
                (
                    "Graph nodes = orchestrator stages; green/completed means tools finished, not that alpha is good.",
                    "图节点 = 编排阶段；绿色/完成表示工具跑完，不表示 Alpha 优良。",
                ),
                (
                    "Agent Inspector shows tool args/results — this is the audit log for numbers.",
                    "智能体检查器显示工具参数/结果——这是数字的审计日志。",
                ),
                (
                    "Report decision is downstream of validation; always verify survivors’ metrics_source_ids.",
                    "报告决策在验证下游；务必核幸存者 metrics_source_ids。",
                ),
                (
                    "Bottom command bar starts new research with budget (max_experiments) — budgets are first-class.",
                    "底部命令栏以预算（max_experiments）启动新研究——预算是一等公民。",
                ),
            ],
            sty,
        )
    )
    story.append(Spacer(1, 6))
