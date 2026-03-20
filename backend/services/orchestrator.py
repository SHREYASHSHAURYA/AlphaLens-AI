import math
from backend.agents.data_agent import fetch_stock_data
from backend.agents.signal_agent import detect_signals
from backend.agents.backtest_agent import backtest_breakout
from backend.agents.reasoning_agent import generate_reasoning
from backend.agents.action_agent import generate_action


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

    return {
        "symbol": symbol,
        "signals": signals,
        "why": why_summary,
        "reasoning": reasoning,
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


def _format_output(top, opportunities, portfolio):
    lines = []

    def _clean_truncate(text, limit=60):
        if len(text) <= limit:
            return text
        cut = text[:limit]
        if " " in cut:
            cut = cut.rsplit(" ", 1)[0]
        return cut + "..."

    lines.append("=" * 60)
    lines.append("           ALPHALENS AI  --  MARKET SCAN REPORT")
    lines.append("=" * 60)

    if top:
        d = top["data"]
        bt = d["backtest"]
        decision = d["decision"]
        signals = d["signals"]
        signal_types = ", ".join(s["type"] for s in signals)
        ml = bt.get("ml_model", {})
        lines.append("")
        lines.append("  TOP PICK")
        lines.append("  " + "-" * 56)
        lines.append(f"  Symbol        : {d['symbol']}")
        lines.append(f"  Action        : {decision['action']}")
        lines.append(f"  Confidence    : {int(decision['confidence'] * 100)}%")
        lines.append(f"  Risk          : {decision['risk']}")
        lines.append(f"  Signal        : {signal_types}")
        lines.append(f"  Reasoning     : {d['reasoning']}")
        if d.get("why"):
            why_text = (
                " | ".join(d["why"][:2])
                if isinstance(d["why"], list)
                else str(d["why"])
            )
            lines.append(f"  Why           : {why_text}")
        lines.append("")
        lines.append("  Backtest Performance:")
        lines.append(f"    Win Rate        : {int(bt['win_rate'] * 100)}%")
        lines.append(f"    Avg Return      : {round(bt['avg_return'] * 100, 2)}%")
        lines.append(f"    Trades          : {bt['trades']}")
        lines.append(f"    Sharpe Ratio    : {bt['sharpe']}")
        lines.append(f"    Max Drawdown    : {round(bt['max_drawdown'] * 100, 2)}%")
        lines.append(f"    Std Deviation   : {round(bt['std_dev'] * 100, 2)}%")
        if decision.get("ml_prediction") is not None:
            lines.append(
                f"    ML Prediction   : {round(decision['ml_prediction'] * 100, 1)}% win probability"
            )
            lines.append(
                f"    ML AUC          : {decision.get('ml_auc', 'N/A')}  (model reliability)"
            )
        if ml:
            top_f = ml.get("top_features", [])
            if top_f:
                feat_str = ", ".join(f[0] for f in top_f)
                lines.append(f"    Top ML Features : {feat_str}")
            lines.append(
                f"    Train / Test    : {ml.get('train_size','?')} / {ml.get('test_size','?')} samples"
            )

    lines.append("")
    lines.append("  ALL OPPORTUNITIES")
    lines.append("  " + "-" * 56)
    lines.append(
        f"{'Symbol':<16} {'Action':<7} {'Conf':>5}  {'WR':>5}  {'Ret':>6}  {'ML Prob':>8}  {'Sharpe':>7}  {'Why':<60}"
    )
    lines.append("  " + "-" * 56)
    for r in opportunities:
        d = r["data"]
        dec = d["decision"]
        bt = d["backtest"]
        why_short = ""
        if d.get("why"):
            why_short = d["why"][0] if isinstance(d["why"], list) else str(d["why"])
            why_short = _clean_truncate(why_short, 60)

        if not why_short:
            why_short = "-"
        ml_str = (
            f"{round(dec['ml_prediction'] * 100, 1)}%"
            if dec.get("ml_prediction") is not None
            else "N/A"
        )
        lines.append(
            f"  {d['symbol']:<16} {dec['action']:<7} "
            f"{int(dec['confidence'] * 100):>4}%  "
            f"{int(bt['win_rate'] * 100):>4}%  "
            f"{round(bt['avg_return'] * 100, 1):>5}%  "
            f"{ml_str:>8}  "
            f"{bt['sharpe']:>7}  {why_short:<60}"
        )

    lines.append("")
    lines.append("  PORTFOLIO POSITIONS")
    lines.append("  " + "-" * 56)
    if portfolio.get("positions"):
        lines.append(
            f"  {'Symbol':<16} {'Alloc':>7}  {'Exp Return':>11}  {'Profit':>12}"
        )
        lines.append("  " + "-" * 56)
        for p in portfolio["positions"]:
            lines.append(
                f"  {p['symbol']:<16} {p['allocation_pct']:>6}%  "
                f"{'+' + str(p['expected_return_pct']) + '%':>11}  "
                f"{'Rs.' + '{:,.2f}'.format(p['profit']):>12}"
            )
        lines.append("")
        lines.append("  PORTFOLIO SUMMARY")
        lines.append("  " + "-" * 56)
        pvb = portfolio.get("performance_vs_benchmark", {})
        lines.append(f"  Initial Capital   : Rs.{portfolio['initial_capital']:,.0f}")
        lines.append(f"  Final Capital     : Rs.{portfolio['final_capital']:,.2f}")
        lines.append(f"  Strategy Return   : {pvb.get('strategy_return_pct', 0)}%")
        lines.append(
            f"  Benchmark Return  : {pvb.get('benchmark_return_pct', 0)}%  (Buy & Hold equal weight)"
        )
        lines.append(f"  Outperformance    : +{pvb.get('outperformance_pct', 0)}%")
        lines.append(
            f"  Max Drawdown      : {pvb.get('strategy_max_drawdown_pct', 0)}%"
        )
        lines.append(f"  Compounded Growth : {portfolio.get('compounded_growth', 1)}x")
    else:
        lines.append("  No active BUY positions.")
        lines.append(
            "  Market conditions do not meet entry criteria -- capital preserved."
        )

    lines.append("")
    lines.append("=" * 60)
    lines.append("  System: An AI-driven trading system combining regime awareness,")
    lines.append("  risk-adjusted scoring, and ML to adapt to market conditions.")
    lines.append("=" * 60)

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

        positions.append(
            {
                "symbol": trade["symbol"],
                "allocated": round(allocation, 2),
                "allocation_pct": round(weight * 100, 1),
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
