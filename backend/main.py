from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from backend.services.orchestrator import (
    run_pipeline,
    scan_market,
    _score,
    simulate_portfolio,
    _format_output,
)

app = FastAPI()


@app.get("/analyze/{symbol}")
def analyze_stock(symbol: str):
    result = run_pipeline(symbol.upper())
    return result


@app.get("/scan")
def scan():
    symbols = [
        "RELIANCE.NS",
        "TCS.NS",
        "INFY.NS",
        "HDFCBANK.NS",
        "ICICIBANK.NS",
        "SBIN.NS",
    ]
    return scan_market(symbols)


@app.get("/report", response_class=PlainTextResponse)
def report():
    symbols = [
        "RELIANCE.NS",
        "TCS.NS",
        "INFY.NS",
        "HDFCBANK.NS",
        "ICICIBANK.NS",
        "SBIN.NS",
    ]

    result = scan_market(symbols)

    return _format_output(
        result["top_pick"],
        result["all_opportunities"],
        result["portfolio"],
    )
