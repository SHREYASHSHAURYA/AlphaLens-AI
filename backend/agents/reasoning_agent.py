def generate_reasoning(signals):
    if not signals:
        return "No qualifying setup detected in current market conditions."

    reasons_map = {
        "Trend Pullback Buy": "Price pulled back to MA20 in an uptrend with RSI, momentum, and volume all confirming.",
        "Momentum Shift": "MACD just crossed bullish inside an uptrend with healthy RSI and volume — momentum resuming.",
        "Volume Breakout": "Price at resistance with strong volume surge — breakout setup confirmed.",
        "Support Bounce": "Price at support with RSI oversold and reversal candle — bounce setup active.",
        "ML Signal": "Machine learning model detected elevated win probability without a classical setup pattern.",
        "No Active Setup": "No qualifying setup in current market conditions — system is waiting.",
    }

    reasons = [reasons_map[s["type"]] for s in signals if s["type"] in reasons_map]
    return " ".join(reasons)


def generate_ml_explanation(decision, backtest):
    if decision.get("ml_prediction") is None:
        return None

    prob = round(decision["ml_prediction"] * 100, 1)

    ml = backtest.get("ml_model", {})
    features = ml.get("top_features", [])

    if not features:
        return f"ML predicts {prob}% win probability."

    mapping = {
        "atr_pct": "rising volatility (ATR)",
        "ma50_slope_norm": "trend strength (MA50 slope)",
        "adx_norm": "momentum strength (ADX)",
        "price_vs_ma50": "price relative to trend (MA50)",
        "rsi_norm": "momentum (RSI)",
        "macd_x_adx": "trend + momentum alignment",
    }

    readable = []
    for f in features[:3]:
        name = f[0]
        readable.append(mapping.get(name, name))

    return {"probability": prob, "drivers": readable}
