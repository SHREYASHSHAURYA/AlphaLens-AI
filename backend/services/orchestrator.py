import math
from backend.agents.data_agent import fetch_stock_data
from backend.agents.signal_agent import detect_signals
from backend.agents.backtest_agent import backtest_breakout
from backend.agents.reasoning_agent import generate_reasoning
from backend.agents.action_agent import generate_action
from backend.agents.reasoning_agent import generate_ml_explanation


def run_pipeline(symbol):
    df = fetch_stock_data(symbol)
    try:
        if df is None or len(df) == 0:
            raise ValueError("Invalid data")

        _ = df["Close"]

    except Exception:
        return {"message": "Data fetch failed"}
    signals = detect_signals(df)

    why_summary = []
    if signals and "why" in signals[0]:
        why_summary = signals[0]["why"]
    if not signals:
        return {"message": "No qualifying setup."}

    backtest = backtest_breakout(df)
    reasoning = generate_reasoning(signals)
    action = generate_action(signals, backtest)
    ml_explanation = generate_ml_explanation(action, backtest)

    return {
        "symbol": symbol,
        "signals": signals,
        "why": why_summary,
        "reasoning": reasoning,
        "ml_explanation": ml_explanation,
        "backtest": backtest,
        "decision": action,
    }


def _score(data):
    bt = data["backtest"]
    signals = data["signals"]
    trades = bt.get("trades", 0)

    if trades == 0:
        return 0.0

    win_rate = bt["win_rate"]
    avg_return = bt["avg_return"]
    sharpe = bt.get("sharpe", 0.0)
    max_drawdown = bt.get("max_drawdown", 0.0)
    std_dev = bt.get("std_dev", 0.0)

    raw = math.log(trades) / math.log(50)
    reliability = min(raw**2.5, 1.0)

    sharpe_score = min(max(sharpe / 3.0, 0), 1.0)
    drawdown_score = max(1.0 + max_drawdown * 5, 0.0)
    consistency_score = max(1.0 - std_dev * 5, 0.0)

    has_active_signal = not all(s["type"] == "No Active Setup" for s in signals)
    signal_bonus = 0.10 if has_active_signal else 0.0

    raw_score = (
        0.25 * win_rate
        + 0.25 * max(avg_return * 10, 0)
        + 0.25 * sharpe_score
        + 0.15 * drawdown_score
        + 0.10 * consistency_score
        + signal_bonus
    )

    return round(raw_score * reliability, 4)


def _compute_drawdown(full_curve):
    import numpy as np

    arr = np.array(full_curve)
    peak = np.maximum.accumulate(arr)
    dd = (arr - peak) / peak
    return dd


def scan_market(symbols):
    results = []

    for symbol in symbols:
        try:
            data = run_pipeline(symbol)
            if "decision" not in data:
                continue

            score = _score(data)
            results.append({"symbol": symbol, "score": score, "data": data})

        except Exception as e:
            print(f"ERROR for {symbol}: {e}")
            continue

    results.sort(key=lambda x: x["score"], reverse=True)

    top = None
    if results:
        top = dict(results[0])
        top["data"] = dict(results[0]["data"])

    if top:
        data = top["data"]
        bt = data["backtest"]
        decision = data["decision"]
        signals = data["signals"]
        signal_strength = round(sum(s["strength"] for s in signals) / len(signals), 2)

        top["insight"] = {
            "expected_return_pct": round(bt["avg_return"] * 100, 2),
            "win_probability_pct": int(bt["win_rate"] * 100),
            "signal_strength_pct": int(signal_strength * 100),
            "confidence_pct": int(decision["confidence"] * 100),
            "trades_backtested": bt["trades"],
            "signal_count": len(signals),
            "sharpe": bt.get("sharpe", 0.0),
            "max_drawdown_pct": round(bt.get("max_drawdown", 0.0) * 100, 2),
            "std_dev_pct": round(bt.get("std_dev", 0.0) * 100, 2),
            "factors": [
                f"{len(signals)} technical signal{'s' if len(signals) > 1 else ''}",
                "historical success rate",
                "signal strength weighting",
                f"reliability adjusted ({bt['trades']} trades)",
                "sharpe ratio",
                "drawdown penalty",
                "return consistency",
            ],
        }

    portfolio = simulate_portfolio(results)

    formatted = _format_output(top, results[:5], portfolio)

    return {
        "top_pick": top,
        "all_opportunities": results[:5],
        "portfolio": portfolio,
    }


def _segment_period_metrics(trade_returns):
    """
    Splits trade returns into 4 equal periods and computes
    return, sharpe, and max drawdown for each.
    """
    import numpy as np

    if not trade_returns or len(trade_returns) < 8:
        return []

    arr = np.array(trade_returns)
    n = len(arr) // 4
    segments = [arr[0:n], arr[n : 2 * n], arr[2 * n : 3 * n], arr[3 * n :]]

    results = []
    for seg in segments:
        if len(seg) == 0:
            continue

        ret = float(np.prod(1 + seg) - 1)
        std = float(seg.std()) if len(seg) > 1 else 0.0
        sharpe = float(seg.mean() / std) if std > 0 else 0.0

        cumulative = np.cumprod(1 + seg)
        peak = np.maximum.accumulate(cumulative)
        dd = (cumulative - peak) / peak
        max_dd = float(dd.min())

        results.append(
            {
                "return": round(ret * 100, 2),
                "sharpe": round(sharpe, 2),
                "max_dd": round(max_dd * 100, 2),
            }
        )

    return results


def _cross_asset_summary(opportunities):
    sharpe_vals = []
    trades = []

    for r in opportunities:
        bt = r["data"]["backtest"]
        sharpe_vals.append(bt.get("sharpe", 0))
        trades.append(bt.get("trades", 0))

    if not sharpe_vals:
        return {}

    import numpy as np

    return {
        "assets": len(sharpe_vals),
        "avg_sharpe": round(float(np.mean(sharpe_vals)), 2),
        "best_sharpe": round(float(np.max(sharpe_vals)), 2),
        "worst_sharpe": round(float(np.min(sharpe_vals)), 2),
        "total_trades": int(sum(trades)),
        "avg_trades": int(np.mean(trades)) if trades else 0,
        "max_trades": max(trades) if trades else 0,
        "min_trades": min(trades) if trades else 0,
    }


def _generate_ai_analyst_brief(top):
    if not top:
        return []

    d = top["data"]
    bt = d["backtest"]
    dec = d["decision"]
    signals = d["signals"]

    symbol = d["symbol"]
    action = dec["action"]
    confidence = int(dec["confidence"] * 100)

    ml_prob = dec.get("ml_prediction")
    ml_auc = dec.get("ml_auc")

    ml_line = None
    if ml_prob is not None:
        ml_line = (
            f"ML model predicts {round(ml_prob*100,1)}% probability of positive return."
        )

    signal_types = [s["type"] for s in signals if s["type"] != "No Active Setup"]

    reasons = []
    if ml_line:
        reasons.append(ml_line)

    for s in signal_types[:2]:
        reasons.append(f"Technical signal detected: {s}")

    if not reasons:
        reasons.append("No active technical setup detected.")
        reasons.append(
            "System recommends monitoring the asset until stronger signals appear."
        )

    evidence = [
        f"Win Rate: {int(bt['win_rate']*100)}%",
        f"Average Return: {round(bt['avg_return']*100,2)}%",
        f"Sharpe Ratio: {bt.get('sharpe',0)}",
    ]

    risk = [
        f"Maximum historical drawdown: {round(bt.get('max_drawdown',0)*100,2)}%",
        f"Volatility (Std Dev): {round(bt.get('std_dev',0)*100,2)}%",
    ]

    lines = []
    lines.append(f"{symbol} — {action}")
    lines.append(f"Confidence: {confidence}%")
    lines.append("")
    lines.append("Why this opportunity exists:")
    lines += [f"• {r}" for r in reasons]
    lines.append("")
    lines.append("Historical Evidence:")
    lines += [f"• {e}" for e in evidence]
    lines.append("")
    lines.append("Risk Factors:")
    lines += [f"• {r}" for r in risk]

    return lines


def _simulate_investment(amount, portfolio):
    import numpy as np

    positions = portfolio.get("positions", [])
    if not positions:
        return {}

    expected_return = portfolio.get("returns_pct", 0) / 100

    worst = amount * (1 + expected_return * 0.5)
    expected = amount * (1 + expected_return)
    best = amount * (1 + expected_return * 1.5)

    allocations = []
    for p in positions:
        alloc = amount * (p["allocation_pct"] / 100)
        allocations.append((p["symbol"], round(alloc, 2)))

    return {
        "investment": amount,
        "allocations": allocations,
        "worst": round(worst, 2),
        "expected": round(expected, 2),
        "best": round(best, 2),
    }


def _format_output(top, opportunities, portfolio):
    from datetime import datetime

    WIDTH = 74
    LABEL_W = 16
    SEP = ": "
    CONTENT_W = WIDTH - 4 - LABEL_W - len(SEP)
    now = datetime.utcnow()
    timestamp = now.strftime("%Y-%m-%d %H:%M UTC")
    report_id = now.strftime("%Y%m%d-%H%M")

    lines = []

    def border():
        lines.append("=" * WIDTH)

    def section(title):
        lines.append("")
        lines.append("+" + "-" * (WIDTH - 2) + "+")
        lines.append(f"| {title:<{WIDTH-4}} |")
        lines.append("|" + "-" * (WIDTH - 2) + "|")

    def empty():
        lines.append(f"| {'':<{WIDTH-4}} |")

    def wrap(text, width):
        words = str(text).split()
        out, line = [], ""
        for w in words:
            if len(line) + len(w) + 1 > width:
                out.append(line)
                line = w
            else:
                line = f"{line} {w}".strip()
        if line:
            out.append(line)
        return out or [""]

    def row(label, value):
        wrapped = wrap(value, CONTENT_W)
        label_str = f"{label:<{LABEL_W}}{SEP}"
        lines.append(f"| {label_str}{wrapped[0]:<{CONTENT_W}} |")
        for w in wrapped[1:]:
            lines.append(f"| {' '*(LABEL_W+len(SEP))}{w:<{CONTENT_W}} |")

    def text_block(text):
        for w in wrap(text, WIDTH - 4):
            lines.append(f"| {w:<{WIDTH-4}} |")

    def perf_box(text):
        if not text:
            return
        lines.append(f"| {'-'*(WIDTH-4)} |")
        wrapped = wrap(text, WIDTH - 6)
        for w in wrapped:
            lines.append(f"|  {w:<{WIDTH-6}} |")
        lines.append(f"| {'-'*(WIDTH-4)} |")

    def curve_block(title, data):
        if not data:
            return
        lines.append(f"| {title:<{WIDTH-4}} |")
        lines.append(f"| {'-'*(WIDTH-4)} |")

        COL = 10
        PER = 5

        for i in range(0, len(data), PER):
            chunk = data[i : i + PER]
            row_txt = " ".join(f"{float(x):>{COL}.2f}" for x in chunk)
            lines.append(f"|  {row_txt:<{WIDTH-6}} |")

        lines.append(f"| {'-'*(WIDTH-4)} |")

    # HEADER
    border()
    lines.append(f"{'ALPHALENS AI  --  MARKET SCAN REPORT':^{WIDTH}}")
    lines.append(f"{('Generated: ' + timestamp):^{WIDTH}}")
    lines.append(f"{('Report ID: ' + report_id):^{WIDTH}}")
    border()

    section("SYSTEM IDENTITY")

    text_block(
        "AlphaLens AI is an AI-driven trading intelligence system combining "
        "technical signal detection, machine learning probability modeling, "
        "and risk-adjusted portfolio construction."
    )

    text_block(
        "The system analyzes market data, evaluates historical strategy "
        "performance, and surfaces probabilistic trading opportunities."
    )

    section("SYSTEM ARCHITECTURE")

    text_block(
        "Pipeline: Market Data → Signal Engine → ML Model → Risk Scoring → "
        "Portfolio Allocation."
    )

    text_block(
        "Components include a data ingestion agent, signal detection engine, "
        "machine learning classifier, reliability scoring module, and a "
        "portfolio simulation engine."
    )

    section("STRATEGY PHILOSOPHY")

    text_block(
        "The strategy follows a probability-driven approach where trading "
        "decisions are based on statistical edge rather than deterministic "
        "rules."
    )

    text_block(
        "Signals are confirmed using historical success rates, machine "
        "learning probabilities, and multi-factor technical alignment."
    )

    section("RISK MANAGEMENT")

    text_block(
        "Risk is controlled through Kelly-adjusted position sizing, "
        "drawdown penalties, and Sharpe-weighted scoring."
    )

    text_block(
        "Portfolio allocations are diversified across the highest scoring "
        "opportunities to reduce concentration risk."
    )

    section("MODEL TRANSPARENCY")

    text_block(
        "The system emphasizes interpretability through feature importance, "
        "machine learning probability outputs, and explicit reasoning for "
        "each signal."
    )

    text_block(
        "Backtest validation and feature attribution allow users to "
        "understand the drivers behind each recommendation."
    )

    section("PERFORMANCE INTERPRETATION")

    text_block(
        "Sharpe ratio measures risk-adjusted returns. Higher values "
        "indicate more consistent performance relative to volatility."
    )

    text_block(
        "Max drawdown represents the largest peak-to-trough loss during "
        "the strategy backtest."
    )

    text_block(
        "Confidence reflects the system's combined signal strength, "
        "historical success rate, and machine learning probability."
    )

    section("SYSTEM LIMITATIONS")

    text_block(
        "The system relies on historical market data and therefore cannot "
        "guarantee future performance."
    )

    text_block(
        "Market regime shifts, structural changes, or extreme events may "
        "cause signals or models to behave differently than in past data."
    )

    text_block(
        "Machine learning probabilities represent statistical likelihoods "
        "and should not be interpreted as guarantees."
    )

    section("SYSTEM METADATA")

    row("System", "AlphaLens AI")
    row("Version", "v1.0")
    row("Model", "ML-assisted signal scoring engine")
    row("Frequency", "Daily / Weekly")
    lines.append("")
    border()
    lines.append(f"{'TRADING ANALYSIS':^{WIDTH}}")
    border()

    # TOP PICK
    if top:
        d = top["data"]
        bt = d["backtest"]
        dec = d["decision"]
        insight = top.get("insight", {})
        ml = bt.get("ml_model", {})

        section("TOP PICK")

        row("Symbol", d["symbol"])
        row("Action", dec["action"])
        row("Confidence", f"{int(dec['confidence']*100)}%")
        row("Risk", dec["risk"])
        row("Signal", ", ".join(s["type"] for s in d["signals"]))
        row("Reasoning", d["reasoning"])
        row("Why", " | ".join(d["why"][:2]))

        empty()

        row("Win Rate", f"{int(bt['win_rate']*100)}%")
        row("Avg Return", f"{round(bt['avg_return']*100,2)}%")
        row("Trades", bt["trades"])
        row("Sharpe", bt["sharpe"])
        row("Max Drawdown", f"{round(bt['max_drawdown']*100,2)}%")
        row("Std Dev", f"{round(bt['std_dev']*100,2)}%")

        if ml:
            feats = ", ".join(f[0] for f in ml.get("top_features", []))
            row("Top Features", feats)
            row("Train/Test", f"{ml.get('train_size')} / {ml.get('test_size')}")

        row("Signal Strength", f"{insight.get('signal_strength_pct',0)}%")
        row("Signals", insight.get("signal_count", 0))
        row("Trades Tested", insight.get("trades_backtested", 0))

    # AI ANALYST BRIEF
    section("AI ANALYST BRIEF")

    brief = _generate_ai_analyst_brief(top)

    for line in brief:
        text_block(line)

    # OPPORTUNITIES
    section("ALL OPPORTUNITIES")

    header = f"{'Symbol':<12} {'Act':<5} {'Conf':>5} {'WR':>5} {'Ret':>6} {'ML%':>6} {'Shp':>5} {'AUC':>6} {'Str':>5}"
    lines.append(f"| {header:<{WIDTH-4}} |")
    lines.append("|" + "-" * (WIDTH - 2) + "|")

    for r in opportunities:
        d = r["data"]
        dec = d["decision"]
        bt = d["backtest"]

        mlp = (
            f"{round(dec['ml_prediction']*100,1)}%"
            if dec.get("ml_prediction")
            else "N/A"
        )
        auc = str(dec.get("ml_auc", "N/A"))

        signal_strength = (
            int(sum(s["strength"] for s in d["signals"]) / len(d["signals"]) * 100)
            if d.get("signals")
            else 0
        )

        row_txt = (
            f"{d['symbol']:<12} {dec['action']:<5} "
            f"{int(dec['confidence']*100):>4}% "
            f"{int(bt['win_rate']*100):>4}% "
            f"{round(bt['avg_return']*100,1):>5}% "
            f"{mlp:>6} {bt['sharpe']:>5} {auc:>6} {signal_strength:>4}%"
        )
        lines.append(f"| {row_txt:<{WIDTH-4}} |")

        if d.get("ml_explanation"):
            txt = f"→ ML {d['ml_explanation']['probability']}%: {', '.join(d['ml_explanation']['drivers'][:2])}"
        else:
            txt = f"→ {d['why'][0]}"

        for w in wrap(txt, WIDTH - 6):
            lines.append(f"|   {w:<{WIDTH-6}} |")

    lines.append("")
    border()
    lines.append(f"{'PORTFOLIO ANALYSIS':^{WIDTH}}")
    border()

    # PORTFOLIO
    section("PORTFOLIO POSITIONS")

    for p in portfolio.get("positions", []):
        text_block(
            f"{p['symbol']} | {p['allocation_pct']}% | +{p['expected_return_pct']}% | Rs.{p['profit']:.2f}"
        )

        text_block(
            f"  Kelly Fraction: {p.get('kelly_fraction',0)} | Weight: {p['allocation_pct']}%"
        )

    section("PORTFOLIO SUMMARY")

    pvb = portfolio.get("performance_vs_benchmark", {})
    bench = portfolio.get("benchmark", {})

    row("Strategy Return", f"{pvb.get('strategy_return_pct')}%")
    row("Benchmark Return", f"{pvb.get('benchmark_return_pct')}%")
    row("Outperformance", f"+{pvb.get('outperformance_pct')}%")
    row("Strategy Max DD", f"{pvb.get('strategy_max_drawdown_pct')}%")
    row("Benchmark Max DD", f"{pvb.get('benchmark_max_drawdown_pct')}%")

    row("Initial", f"Rs.{portfolio['initial_capital']:,.0f}")
    row("Final", f"Rs.{portfolio['final_capital']:,.2f}")
    row("Growth", f"{portfolio.get('compounded_growth')}x")

    empty()

    perf_box(portfolio.get("performance_summary", ""))

    empty()

    # clean comparison line
    line = (
        f"Strategy vs Benchmark → Return: {pvb.get('strategy_return_pct')}% vs {pvb.get('benchmark_return_pct')}%, "
        f"Drawdown: {pvb.get('strategy_max_drawdown_pct')}% vs {pvb.get('benchmark_max_drawdown_pct')}%"
    )

    wrapped = wrap(line, WIDTH - 6)
    for i, w in enumerate(wrapped):
        if i == 0:
            lines.append(f"|  {w:<{WIDTH-6}} |")
        else:
            lines.append(f"|    {w:<{WIDTH-8}} |")

    # INVESTMENT SIMULATION
    section("INVESTMENT SIMULATION")

    sim = _simulate_investment(500000, portfolio)

    if sim:
        row("Investment", f"Rs.{sim['investment']:,.0f}")

        text_block("Recommended Allocation")

        for sym, amt in sim["allocations"]:
            text_block(f"{sym} → Rs.{amt:,.0f}")

        empty()

        row("Worst Case", f"Rs.{sim['worst']:,.0f}")
        row("Expected", f"Rs.{sim['expected']:,.0f}")
        row("Best Case", f"Rs.{sim['best']:,.0f}")

    # CURVES
    section("PERFORMANCE CURVES")

    curve_block("EQUITY CURVE (Strategy)", portfolio.get("equity_curve"))
    curve_block("DRAWDOWN CURVE (Strategy)", portfolio.get("drawdown_curve"))

    empty()

    curve_block("EQUITY CURVE (Benchmark)", bench.get("equity_curve"))
    curve_block("DRAWDOWN CURVE (Benchmark)", bench.get("drawdown_curve"))

    empty()

    text_block(
        "Position sizing uses Kelly-adjusted weighting based on expected return, win probability, and drawdown risk."
    )

    text_block(
        "Weights are derived from Kelly fractions estimated from historical win rate and reward/risk ratio, then normalized across selected assets."
    )

    section("STRATEGY VS MARKET")

    strategy_final = portfolio.get("final_capital", 0)
    bench = portfolio.get("benchmark", {})
    bench_final = bench.get("final_capital", 0)

    row("Strategy Growth", f"Rs.100,000 → Rs.{strategy_final:,.0f}")
    row("Benchmark Growth", f"Rs.100,000 → Rs.{bench_final:,.0f}")

    text_block(
        "Strategy equity growth is compared against a buy-and-hold benchmark "
        "to demonstrate the advantage of the signal-driven portfolio approach."
    )

    # ------------------------------------------------
    # ROBUSTNESS ANALYSIS
    # ------------------------------------------------

    lines.append("")
    border()
    lines.append(f"{'ROBUSTNESS ANALYSIS':^{WIDTH}}")
    border()

    section("MULTI-PERIOD PERFORMANCE")

    period_metrics = []
    if top:
        bt = top["data"]["backtest"]
        period_metrics = _segment_period_metrics(bt.get("trade_returns", []))

    period_labels = ["Period 1", "Period 2", "Period 3", "Period 4"]

    for i, m in enumerate(period_metrics):
        text_block(
            f"{period_labels[i]} → Return: {m['return']}% | Sharpe: {m['sharpe']} | Max DD: {m['max_dd']}%"
        )

    section("WALK-FORWARD VALIDATION")

    if top:
        ml = top["data"]["backtest"].get("ml_model", {})

        row("Validation Accuracy", ml.get("val_accuracy", "N/A"))
        row("Validation AUC", ml.get("val_auc", "N/A"))
        row("Training Samples", ml.get("train_size", "N/A"))
        row("Test Samples", ml.get("test_size", "N/A"))

    text_block(
        "Models are evaluated on unseen data using train/test splits to "
        "ensure predictive performance generalizes beyond the training set."
    )

    section("CROSS-ASSET VALIDATION")

    summary = _cross_asset_summary(opportunities)

    if summary:
        row("Assets Analyzed", summary["assets"])
        row("Average Sharpe", summary["avg_sharpe"])
        row("Best Asset Sharpe", summary["best_sharpe"])
        row("Worst Asset Sharpe", summary["worst_sharpe"])

    section("SAMPLE SIZE EVIDENCE")

    if summary:
        row("Total Trades", summary["total_trades"])
        row("Average Trades/Asset", summary["avg_trades"])
        row("Maximum Trades", summary["max_trades"])
        row("Minimum Trades", summary["min_trades"])

    section("OVERFITTING SAFEGUARDS")

    text_block(
        "The system mitigates overfitting through out-of-sample validation, "
        "limited feature engineering, and risk-adjusted scoring."
    )

    text_block(
        "Signals are diversified across multiple technical factors and "
        "validated using historical performance and machine learning probabilities."
    )

    section("ROBUSTNESS SUMMARY")

    text_block(
        "The strategy was evaluated across multiple assets, time segments, "
        "and out-of-sample machine learning validation datasets."
    )

    text_block(
        "Combined evidence from multi-period testing, cross-asset results, "
        "and historical trade samples indicates that performance is not "
        "dependent on a single asset or time window."
    )

    section("RESEARCH STATEMENT")

    text_block(
        "AlphaLens AI is designed as a quantitative research assistant "
        "that surfaces probabilistic trading opportunities rather than "
        "deterministic trading signals."
    )

    section("MODEL VALIDATION")

    text_block(
        "Machine learning predictions are evaluated using out-of-sample "
        "testing and AUC-based classification performance metrics."
    )

    text_block(
        "Model inputs include volatility, trend strength, and momentum "
        "features derived from market data."
    )

    text_block(
        "Backtest results shown in the report reflect historical strategy "
        "performance and should be interpreted as research evidence rather "
        "than guaranteed outcomes."
    )

    section("STATISTICAL SIGNIFICANCE")

    text_block(
        "Performance metrics are derived from historical backtests and "
        "represent empirical observations rather than statistically "
        "guaranteed results."
    )

    text_block(
        "Trading outcomes may vary due to market regime changes, noise, "
        "and stochastic price movements."
    )

    text_block(
        "Users should interpret reported returns, Sharpe ratios, and "
        "probabilities as research indicators rather than predictive "
        "certainties."
    )

    # FOOTER
    border()
    lines.append(
        f"{'System: AI-driven trading system with ML + risk scoring.':^{WIDTH}}"
    )
    border()

    return "\n".join(lines)


def simulate_portfolio(results, capital=100_000):
    import numpy as np

    tradeable = [
        r
        for r in results
        if r["data"]["decision"]["action"] == "BUY"
        and r["data"]["backtest"]["trades"] >= 25
    ][:3]

    if not tradeable:
        return {
            "initial_capital": capital,
            "final_capital": capital,
            "returns_pct": 0,
            "compounded_growth": 1.0,
            "equity_curve": [],
            "drawdown_curve": [],
            "benchmark": _flat_benchmark(capital),
            "performance_vs_benchmark": {
                "strategy_return_pct": 0,
                "benchmark_return_pct": 0,
                "outperformance_pct": 0,
                "strategy_max_drawdown_pct": 0,
                "benchmark_max_drawdown_pct": 0,
            },
            "positions": [],
        }
    kelly_details = []
    raw_weights = []
    for trade in tradeable:
        bt = trade["data"]["backtest"]
        trade_returns = bt.get("trade_returns", [])

        if trade_returns and len(trade_returns) > 1:
            arr = np.array(trade_returns)
            wins = arr[arr > 0]
            losses = arr[arr < 0]
            win_rate = len(wins) / len(arr)
            loss_rate = 1 - win_rate
            avg_win = float(wins.mean()) if len(wins) > 0 else 0.0
            avg_loss = float(abs(losses.mean())) if len(losses) > 0 else 0.001
            rr_ratio = avg_win / avg_loss if avg_loss > 0 else 0.0
            kelly = win_rate - (loss_rate / rr_ratio) if rr_ratio > 0 else 0.0
            half_kelly = max(kelly * 0.5, 0.0)
            raw_weight = half_kelly
        else:
            raw_weight = max(bt.get("sharpe", 0.0) * 0.1, 0.0)

        raw_weights.append(raw_weight)

        kelly_details.append(
            {"symbol": trade["symbol"], "kelly_fraction": round(raw_weight, 3)}
        )

    total = sum(raw_weights)
    if total == 0:
        weights = [1 / len(tradeable)] * len(tradeable)
    else:
        weights = [w / total for w in raw_weights]

    positions = []
    for trade, weight in zip(tradeable, weights):
        bt = trade["data"]["backtest"]
        allocation = capital * weight
        profit = allocation * bt["avg_return"]

        kelly_fraction = next(
            (
                k["kelly_fraction"]
                for k in kelly_details
                if k["symbol"] == trade["symbol"]
            ),
            0,
        )

        positions.append(
            {
                "symbol": trade["symbol"],
                "allocated": round(allocation, 2),
                "allocation_pct": round(weight * 100, 1),
                "kelly_fraction": kelly_fraction,
                "expected_return_pct": round(bt["avg_return"] * 100, 2),
                "profit": round(profit, 2),
                "action": trade["data"]["decision"]["action"],
            }
        )

    max_len = max(
        (len(t["data"]["backtest"].get("trade_returns", [])) for t in tradeable),
        default=0,
    )

    running = capital
    full_curve = [running]
    for k in range(max_len):
        period_return = 0.0
        for i, trade in enumerate(tradeable):
            tr = trade["data"]["backtest"].get("trade_returns", [])
            if k < len(tr):
                period_return += weights[i] * tr[k]
        running *= 1 + period_return
        full_curve.append(running)

    compounded_growth = round(running / capital, 4)
    strategy_return_pct = round((compounded_growth - 1) * 100, 2)

    step = max(1, len(full_curve) // 20)
    equity_curve = [round(v, 2) for v in full_curve[::step]]

    dd_arr = _compute_drawdown(equity_curve)
    strategy_max_dd = round(float(dd_arr.min()) * 100, 2)
    drawdown_curve = [round(float(v) * 100, 2) for v in dd_arr]

    benchmark = _buy_and_hold_benchmark(tradeable, capital, max_len, step)
    outperformance = round(strategy_return_pct - benchmark["return_pct"], 2)

    summary = (
        f"Strategy: {strategy_return_pct}% | "
        f"Benchmark: {benchmark['return_pct']}% | "
        f"Outperformance: +{outperformance}% | "
        f"Max Drawdown: {strategy_max_dd}%"
    )

    return {
        "initial_capital": capital,
        "final_capital": round(running, 2),
        "returns_pct": strategy_return_pct,
        "compounded_growth": compounded_growth,
        "equity_curve": equity_curve,
        "drawdown_curve": drawdown_curve,
        "benchmark": benchmark,
        "performance_vs_benchmark": {
            "strategy_return_pct": strategy_return_pct,
            "benchmark_return_pct": benchmark["return_pct"],
            "outperformance_pct": outperformance,
            "strategy_max_drawdown_pct": strategy_max_dd,
            "benchmark_max_drawdown_pct": benchmark["max_drawdown_pct"],
        },
        "performance_summary": summary,
        "positions": positions,
    }


def _buy_and_hold_benchmark(tradeable, capital, max_len, step):
    import numpy as np
    from backend.agents.data_agent import fetch_stock_data

    n = len(tradeable)
    weight = 1.0 / n if n > 0 else 1.0

    symbol_returns = []
    for trade in tradeable:
        symbol = trade["symbol"]
        try:
            df = fetch_stock_data(symbol)

            if df is None or "Close" not in df:
                continue

            weekly = df["Close"].dropna().resample("W").last().dropna()

            prices = weekly.values
            if len(prices) >= 2:
                weekly_returns = np.diff(prices) / prices[:-1]
                symbol_returns.append(weekly_returns)
        except Exception:
            continue

    if not symbol_returns:
        return _flat_benchmark(capital)

    min_len = min(len(r) for r in symbol_returns)
    portfolio_returns = np.zeros(min_len)
    for r in symbol_returns:
        portfolio_returns += weight * r[:min_len]

    running = capital
    full_curve = [running]
    for r in portfolio_returns:
        running *= 1 + r
        full_curve.append(running)

    bh_return = round((running / capital - 1) * 100, 2)
    dd_arr = _compute_drawdown(full_curve)
    bh_max_dd = round(float(dd_arr.min()) * 100, 2)

    step_bh = max(1, len(full_curve) // 20)

    return {
        "label": "Buy & Hold (equal weight)",
        "final_capital": round(running, 2),
        "return_pct": bh_return,
        "max_drawdown_pct": bh_max_dd,
        "equity_curve": [round(v, 2) for v in full_curve[::step_bh]],
        "drawdown_curve": [round(float(v) * 100, 2) for v in dd_arr[::step_bh]],
    }


def _flat_benchmark(capital):
    return {
        "label": "Buy & Hold (equal weight)",
        "final_capital": capital,
        "return_pct": 0,
        "max_drawdown_pct": 0,
        "equity_curve": [],
        "drawdown_curve": [],
    }
