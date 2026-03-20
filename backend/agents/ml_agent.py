import numpy as np

FEATURE_NAMES = [
    "rsi_norm",
    "macd_ratio",
    "adx_norm",
    "ma50_slope_norm",
    "volume_ratio",
    "price_vs_ma20",
    "price_vs_ma50",
    "atr_pct",
    "momentum_5d",
    "momentum_10d",
    "rsi_change",
    "reversal_candle",
    "rsi_x_momentum",
    "macd_x_adx",
    "vol_x_momentum",
]


def extract_features(df, i):
    close = float(df["Close"].iloc[i])
    ma20 = float(df["ma20"].iloc[i])
    ma50 = float(df["ma50"].iloc[i])
    rsi = float(df["rsi"].iloc[i])
    macd = float(df["macd"].iloc[i])
    macd_signal = float(df["macd_signal"].iloc[i])
    volume = float(df["Volume"].iloc[i])
    volume_avg = float(df["volume_avg"].iloc[i])
    adx = float(df["adx"].iloc[i])
    ma50_slope = float(df["ma50_slope"].iloc[i])
    close_5 = float(df["Close"].iloc[i - 5])
    close_10 = float(df["Close"].iloc[i - 10])
    rsi_5 = float(df["rsi"].iloc[i - 5])
    atr = (
        float(df["atr"].iloc[i])
        if "atr" in df.columns
        else abs(close - float(df["Close"].iloc[i - 1]))
    )

    rsi_norm = rsi / 100.0
    macd_ratio = (macd - macd_signal) / (abs(macd_signal) + 1e-9)
    adx_norm = min(adx / 50.0, 1.0)
    ma50_slope_norm = ma50_slope / (close + 1e-9)
    volume_ratio = volume / (volume_avg + 1e-9)
    price_vs_ma20 = (close - ma20) / (ma20 + 1e-9)
    price_vs_ma50 = (close - ma50) / (ma50 + 1e-9)
    atr_pct = atr / (close + 1e-9)
    momentum_5d = (close - close_5) / (close_5 + 1e-9)
    momentum_10d = (close - close_10) / (close_10 + 1e-9)
    rsi_change = (rsi - rsi_5) / 100.0
    reversal = 1.0 if close > float(df["Close"].iloc[i - 1]) else -1.0

    rsi_x_momentum = rsi_norm * momentum_5d
    macd_x_adx = macd_ratio * adx_norm
    vol_x_momentum = volume_ratio * momentum_5d

    return [
        rsi_norm,
        macd_ratio,
        adx_norm,
        ma50_slope_norm,
        volume_ratio,
        price_vs_ma20,
        price_vs_ma50,
        atr_pct,
        momentum_5d,
        momentum_10d,
        rsi_change,
        reversal,
        rsi_x_momentum,
        macd_x_adx,
        vol_x_momentum,
    ]


def build_training_data(df):
    """
    TRAINING PHASE — offline label generation.

    Target definition (explicit):
        label = 1 if trade_return > 0 (profitable trade within 25 bars)
        label = 0 if trade_return <= 0 (unprofitable or stopped out)

    Trade simulation:
        entry = Close[i]
        take_profit = entry * 1.10  (+10%)
        stop_loss   = entry * 0.975 (-2.5%)
        hold_window = 25 bars max
    """
    features = []
    labels = []

    for i in range(50, len(df) - 25):
        try:
            feat = extract_features(df, i)
        except Exception:
            continue

        entry = float(df["Close"].iloc[i])
        take_profit = entry * 1.10
        stop_loss = entry * 0.975
        exit_price = entry

        for j in range(i + 1, min(i + 25, len(df))):
            future_high = (
                float(df["High"].iloc[j])
                if "High" in df.columns
                else float(df["Close"].iloc[j])
            )
            future_low = (
                float(df["Low"].iloc[j])
                if "Low" in df.columns
                else float(df["Close"].iloc[j])
            )
            if future_low <= stop_loss:
                exit_price = stop_loss
                break
            if future_high >= take_profit:
                exit_price = take_profit
                break
            exit_price = float(df["Close"].iloc[j])

        trade_return = (exit_price - entry) / entry
        label = 1 if trade_return > 0 else 0

        features.append(feat)
        labels.append(label)

    return np.array(features), np.array(labels)


def train_model(df):
    """
    TRAINING PHASE — fits GradientBoosting on labeled trade data.
    Returns trained pipeline. Call once per symbol per session.
    """
    try:
        from sklearn.ensemble import GradientBoostingClassifier
        from sklearn.preprocessing import StandardScaler
        from sklearn.pipeline import Pipeline
        from sklearn.metrics import accuracy_score, roc_auc_score
        from sklearn.utils.class_weight import compute_sample_weight
    except ImportError:
        return None

    X, y = build_training_data(df)

    if len(X) < 30 or y.sum() < 5 or (y == 0).sum() < 5:
        return None

    split = int(len(X) * 0.8)
    X_train, y_train = X[:split], y[:split]
    X_test, y_test = X[split:], y[split:]

    if len(X_test) < 5:
        return None

    sample_weights = compute_sample_weight("balanced", y_train)

    model = Pipeline(
        [
            ("scaler", StandardScaler()),
            (
                "clf",
                GradientBoostingClassifier(
                    n_estimators=200,
                    max_depth=3,
                    learning_rate=0.03,
                    subsample=0.7,
                    min_samples_leaf=5,
                    random_state=42,
                ),
            ),
        ]
    )

    model.fit(X_train, y_train, clf__sample_weight=sample_weights)

    val_acc = round(float(accuracy_score(y_test, model.predict(X_test))), 3)
    try:
        val_auc = round(
            float(roc_auc_score(y_test, model.predict_proba(X_test)[:, 1])), 3
        )
    except Exception:
        val_auc = None

    importances = model.named_steps["clf"].feature_importances_
    top_features = sorted(
        zip(FEATURE_NAMES, importances), key=lambda x: x[1], reverse=True
    )[:3]

    model._val_acc = val_acc
    model._val_auc = val_auc
    model._top_features = [(f, round(float(w), 3)) for f, w in top_features]
    model._train_size = len(X_train)
    model._test_size = len(X_test)

    return model


def predict_proba(model, df, i):
    """
    INFERENCE PHASE — returns P(trade_return > 0) for bar i.
    This is the primary decision signal.
    """
    if model is None:
        return None
    try:
        feat = extract_features(df, i)
        prob = model.predict_proba([feat])[0][1]
        return float(prob)
    except Exception:
        return None


def get_model_stats(model):
    if model is None:
        return {}
    return {
        "val_accuracy": getattr(model, "_val_acc", None),
        "val_auc": getattr(model, "_val_auc", None),
        "top_features": getattr(model, "_top_features", []),
        "train_size": getattr(model, "_train_size", None),
        "test_size": getattr(model, "_test_size", None),
    }
