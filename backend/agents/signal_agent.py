import numpy as np
from backend.utils.indicators import add_indicators
from backend.agents.ml_agent import train_model, predict_proba, extract_features


def _compute_adx_slope(df):
    high = df["High"] if "High" in df.columns else df["Close"]
    low = df["Low"] if "Low" in df.columns else df["Close"]
    up_move = high.diff()
    down_move = -low.diff()
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    prev_close = df["Close"].shift(1)
    tr = np.maximum(
        high - low, np.maximum(abs(high - prev_close), abs(low - prev_close))
    )
    tr_series = tr.rolling(14).mean()
    df["atr"] = tr_series
    plus_di_series = df["Close"].copy()
    plus_di_series[:] = plus_dm
    plus_di_smooth = plus_di_series.rolling(14).mean() / tr_series * 100
    minus_di_series = df["Close"].copy()
    minus_di_series[:] = minus_dm
    minus_di_smooth = minus_di_series.rolling(14).mean() / tr_series * 100
    dx = (
        abs(plus_di_smooth - minus_di_smooth) / (plus_di_smooth + minus_di_smooth)
    ) * 100
    df["adx"] = dx.rolling(14).mean()
    df["ma50_slope"] = df["ma50"].diff(5)
    return df


def detect_signals(df):
    df = add_indicators(df)
    df = _compute_adx_slope(df)
    df = df.dropna().copy()

    if df.empty or len(df) < 60:
        return []

    model = train_model(df)

    def val(x):
        try:
            return float(x.iloc[0])
        except Exception:
            return float(x)

    latest = df.iloc[-1]
    prev = df.iloc[-2]
    i = len(df) - 1

    close = val(latest["Close"])
    resistance = val(latest["resistance"])
    support = val(latest["support"])
    ma20 = val(latest["ma20"])
    ma50 = val(latest["ma50"])
    volume = val(latest["Volume"])
    volume_avg = val(latest["volume_avg"])
    rsi = val(latest["rsi"])
    macd = val(latest["macd"])
    macd_signal = val(latest["macd_signal"])
    prev_close = val(prev["Close"])
    prev_macd = val(prev["macd"])
    prev_macd_signal = val(prev["macd_signal"])
    ma50_slope = val(latest["ma50_slope"])
    adx = val(latest["adx"])

    trend_up = ma20 > ma50 and ma50_slope > 0
    pullback_zone = ma20 * 0.99 <= close <= ma20 * 1.05
    momentum_ok = macd > macd_signal
    rsi_healthy = 40 <= rsi <= 72
    volume_present = volume >= volume_avg * 0.9
    reversal_candle = close > prev_close
    macd_just_crossed = macd > macd_signal and prev_macd <= prev_macd_signal
    at_resistance = close >= resistance * 0.98
    volume_surge = volume > volume_avg * 1.3
    at_support = close <= support * 1.02
    rsi_oversold = rsi < 38

    raw_ml_prob = predict_proba(model, df, i) if model is not None else None
    ml_auc = getattr(model, "_val_auc", None) if model is not None else None
    ml_valid = ml_auc is not None and ml_auc >= 0.55

    ml_prob = raw_ml_prob if ml_valid else None
    ml_pred = round(ml_prob, 3) if ml_prob is not None else None

    signals = []

    if (
        trend_up
        and pullback_zone
        and momentum_ok
        and rsi_healthy
        and volume_present
        and reversal_candle
    ):
        strength = ml_prob if ml_prob is not None else 0.85
        signals.append(
            {
                "type": "Trend Pullback Buy",
                "strength": round(strength, 3),
                "ml_prediction": ml_pred,
            }
        )

    if trend_up and macd_just_crossed and rsi_healthy and volume_present:
        strength = ml_prob if ml_prob is not None else 0.80
        signals.append(
            {
                "type": "Momentum Shift",
                "strength": round(strength, 3),
                "ml_prediction": ml_pred,
            }
        )

    if trend_up and at_resistance and volume_surge and rsi < 75:
        strength = ml_prob if ml_prob is not None else 0.85
        signals.append(
            {
                "type": "Volume Breakout",
                "strength": round(strength, 3),
                "ml_prediction": ml_pred,
            }
        )

    if at_support and rsi_oversold and reversal_candle and volume_present:
        strength = ml_prob if ml_prob is not None else 0.75
        signals.append(
            {
                "type": "Support Bounce",
                "strength": round(strength, 3),
                "ml_prediction": ml_pred,
            }
        )

    if not signals and ml_prob is not None and ml_prob >= 0.60:
        signals.append(
            {
                "type": "ML Signal",
                "strength": round(ml_prob, 3),
                "ml_prediction": ml_pred,
            }
        )

    if not signals:
        signals.append(
            {"type": "No Active Setup", "strength": 0.0, "ml_prediction": None}
        )

    explanations = []

    for s in signals:
        if s["type"] == "Trend Pullback Buy":
            explanations.append(
                [
                    "Trend up (MA20 > MA50, positive slope)",
                    "Pullback near MA20",
                    "Momentum positive (MACD > signal)",
                    "Healthy RSI",
                    "Volume present",
                    "Reversal candle",
                ]
            )

        elif s["type"] == "Momentum Shift":
            explanations.append(
                [
                    "Trend up",
                    "MACD bullish crossover",
                    "Momentum strengthening",
                    "Volume confirmation",
                ]
            )

        elif s["type"] == "Volume Breakout":
            explanations.append(
                [
                    "Near resistance breakout",
                    "High volume surge",
                    "Momentum intact",
                ]
            )

        elif s["type"] == "Support Bounce":
            explanations.append(
                [
                    "Price near support",
                    "RSI oversold",
                    "Reversal candle",
                    "Volume confirmation",
                ]
            )

        elif s["type"] == "ML Signal":
            explanations.append(
                [
                    f"ML predicts high probability ({ml_pred})",
                    f"Model AUC: {round(ml_auc,3) if ml_auc else 'N/A'}",
                ]
            )

        else:
            explanations.append(
                [
                    "No valid setup",
                    "Market conditions not favorable",
                ]
            )

    for i in range(len(signals)):
        signals[i]["why"] = explanations[i]

    return signals
