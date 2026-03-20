import yfinance as yf


def fetch_stock_data(symbol: str, period="2y", interval="1d"):

    df = yf.download(symbol, period=period, interval=interval, auto_adjust=True)

    if hasattr(df.columns, "levels"):
        df.columns = df.columns.get_level_values(0)

    if df is None or df.empty:
        return None

    df = df.dropna()

    if df.empty:
        return None

    return df
