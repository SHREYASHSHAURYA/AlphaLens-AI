import numpy as np
from backend.utils.indicators import add_indicators
from backend.agents.ml_agent import train_model, predict_proba, get_model_stats


def backtest_breakout(df):
    df = df.copy()
    df = add_indicators(df)
    df = df.dropna(subset=["Close", "ma20", "ma50", "rsi", "macd", "macd_signal"])

    if len(df) < 60:
        return {
            "win_rate": 0.0,
            "avg_return": 0.0,
            "trades": 0,
            "sharpe": 0.0,
            "max_drawdown": 0.0,
            "std_dev": 0.0,
            "trade_returns": [],
            "ml_model": {},
        }

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

    df = df.dropna(subset=["adx", "ma50_slope", "atr"])

    model = train_model(df)
    ml_stats = get_model_stats(model)

    results = []

    for i in range(50, len(df) - 5):
        close = float(df["Close"].iloc[i])
        ma20 = float(df["ma20"].iloc[i])
        ma50 = float(df["ma50"].iloc[i])
        rsi = float(df["rsi"].iloc[i])
        macd = float(df["macd"].iloc[i])
        macd_signal = float(df["macd_signal"].iloc[i])
        prev_close_val = float(df["Close"].iloc[i - 1])
        adx = float(df["adx"].iloc[i])
        ma50_slope = float(df["ma50_slope"].iloc[i])

        trending = adx >= 20 and ma50_slope > 0
        if not trending:
            continue

        trend_up = ma20 > ma50
        near_ma20 = ma20 * 0.99 <= close <= ma20 * 1.05
        rsi_ok = 40 <= rsi <= 75
        macd_bullish = macd > macd_signal
        reversal = close > prev_close_val

        base_entry = trend_up and near_ma20 and rsi_ok and macd_bullish and reversal

        if model is not None:
            prob = predict_proba(model, df, i)
            ml_entry = prob is not None and prob >= 0.55
            if not (base_entry or ml_entry):
                continue
        else:
            if not base_entry:
                continue

        entry = close
        take_profit = entry * 1.10
        stop_loss = entry * 0.975
        exit_price = entry

        for j in range(i + 1, min(i + 25, len(df))):
            future_close = float(df["Close"].iloc[j])
            future_high = (
                float(df["High"].iloc[j]) if "High" in df.columns else future_close
            )
            future_low = (
                float(df["Low"].iloc[j]) if "Low" in df.columns else future_close
            )

            if future_low <= stop_loss:
                exit_price = stop_loss
                break
            if future_high >= take_profit:
                exit_price = take_profit
                break
            exit_price = future_close

        ret = (exit_price - entry) / entry
        results.append(ret)

    if len(results) == 0:
        return {
            "win_rate": 0.0,
            "avg_return": 0.0,
            "trades": 0,
            "sharpe": 0.0,
            "max_drawdown": 0.0,
            "std_dev": 0.0,
            "trade_returns": [],
            "ml_model": ml_stats,
        }

    results = np.array(results)
    win_rate = float((results > 0).mean())
    avg_return = float(results.mean())
    std_dev = float(results.std()) if len(results) > 1 else 0.0
    sharpe = float(avg_return / std_dev) if std_dev > 0 else 0.0
    cumulative = np.cumprod(1 + results)
    peak = np.maximum.accumulate(cumulative)
    drawdowns = (cumulative - peak) / peak
    max_drawdown = float(drawdowns.min())

    return {
        "win_rate": round(win_rate, 2),
        "avg_return": round(avg_return, 3),
        "trades": len(results),
        "sharpe": round(sharpe, 2),
        "max_drawdown": round(max_drawdown, 3),
        "std_dev": round(std_dev, 3),
        "trade_returns": [round(r, 4) for r in results.tolist()],
        "ml_model": ml_stats,
    }
