def add_indicators(df):
    df["ma20"] = df["Close"].rolling(20).mean()
    df["ma50"] = df["Close"].rolling(50).mean()

    df["resistance"] = df["High"].rolling(20).max()
    df["support"] = df["Low"].rolling(20).min()
    df["volume_avg"] = df["Volume"].rolling(20).mean()

    df = add_rsi(df)
    df = add_macd(df)

    return df


def add_rsi(df, period=14):
    delta = df["Close"].diff()

    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

    rs = gain / loss
    df["rsi"] = 100 - (100 / (1 + rs))

    return df


def add_macd(df):
    exp1 = df["Close"].ewm(span=12, adjust=False).mean()
    exp2 = df["Close"].ewm(span=26, adjust=False).mean()

    df["macd"] = exp1 - exp2
    df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()

    return df
