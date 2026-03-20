import math


def generate_action(signals, backtest):
    win_rate = backtest["win_rate"]
    avg_return = backtest["avg_return"]
    trades = backtest.get("trades", 0)
    ml_stats = backtest.get("ml_model", {})
    val_auc = ml_stats.get("val_auc") if ml_stats else None
    ml_valid = val_auc is not None and val_auc >= 0.55

    ml_prob = None
    for s in signals:
        if s["type"] not in ("No Active Setup",):
            ml_prob = s.get("ml_prediction")
            break

    raw_confidence = round(sum(s["strength"] for s in signals) / len(signals), 2)

    if trades >= 5:
        backtest_confidence = win_rate * 0.6 + min(max(avg_return * 10, 0), 0.4)
        if ml_valid and ml_prob is not None:
            confidence = round(
                0.3 * raw_confidence + 0.3 * backtest_confidence + 0.4 * ml_prob, 2
            )
        else:
            confidence = round(0.5 * raw_confidence + 0.5 * backtest_confidence, 2)
    else:
        confidence = round(raw_confidence * 0.5, 2)

    if trades < 20:
        return {
            "action": "WATCH",
            "confidence": confidence,
            "risk": "Medium",
            "ml_prediction": ml_prob,
            "ml_auc": val_auc,
        }

    if all(s["type"] == "No Active Setup" for s in signals):
        return {
            "action": "WATCH",
            "confidence": confidence,
            "risk": "Medium",
            "ml_prediction": None,
            "ml_auc": val_auc,
        }

    if not ml_valid:
        if trades >= 5:
            raw = math.log(trades) / math.log(50)
            reliability = min(raw**2.5, 1.0)
        else:
            reliability = 0.0
        adj_win_rate = win_rate * reliability + 0.5 * (1 - reliability)
        adj_avg_return = avg_return * reliability
        has_real_signal = not all(s["type"] in ("No Active Setup",) for s in signals)
        if has_real_signal and adj_win_rate >= 0.50 and adj_avg_return >= 0.005:
            risk = "Low" if adj_win_rate >= 0.60 else "Medium"
            return {
                "action": "BUY",
                "confidence": confidence,
                "risk": risk,
                "ml_prediction": None,
                "ml_auc": val_auc,
            }
        return {
            "action": "WATCH",
            "confidence": confidence,
            "risk": "Medium",
            "ml_prediction": None,
            "ml_auc": val_auc,
        }

    if ml_prob is None:
        return {
            "action": "WATCH",
            "confidence": confidence,
            "risk": "Medium",
            "ml_prediction": None,
            "ml_auc": val_auc,
        }

    if ml_prob > 0.60:
        risk = "Low" if ml_prob >= 0.75 else "Medium"
        return {
            "action": "BUY",
            "confidence": confidence,
            "risk": risk,
            "ml_prediction": round(ml_prob, 3),
            "ml_auc": val_auc,
        }

    if ml_prob < 0.40:
        return {
            "action": "AVOID",
            "confidence": confidence,
            "risk": "High",
            "ml_prediction": round(ml_prob, 3),
            "ml_auc": val_auc,
        }

    return {
        "action": "WATCH",
        "confidence": confidence,
        "risk": "Medium",
        "ml_prediction": round(ml_prob, 3),
        "ml_auc": val_auc,
    }
