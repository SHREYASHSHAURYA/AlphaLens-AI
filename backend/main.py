from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone
from backend.services.orchestrator import (
    run_pipeline,
    scan_market,
    _score,
    simulate_portfolio,
    _format_output,
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/analyze/{symbol}")
def analyze_stock(symbol: str):
    result = run_pipeline(symbol.upper())
    return result


@app.get("/scan")
def scan():
    SYMBOLS = [
        "RELIANCE.NS",
        "TCS.NS",
        "INFY.NS",
        "HDFCBANK.NS",
        "ICICIBANK.NS",
        "SBIN.NS",
        "WIPRO.NS",
        "BAJFINANCE.NS",
        "ADANIENT.NS",
        "TITAN.NS",
        "HINDUNILVR.NS",
        "KOTAKBANK.NS",
        "AXISBANK.NS",
        "MARUTI.NS",
        "SUNPHARMA.NS",
    ]
    result = scan_market(SYMBOLS)
    result["scanned_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    result["symbols_scanned"] = len(SYMBOLS)
    return result


@app.get("/report", response_class=PlainTextResponse)
def report():
    SYMBOLS = [
        "RELIANCE.NS",
        "TCS.NS",
        "INFY.NS",
        "HDFCBANK.NS",
        "ICICIBANK.NS",
        "SBIN.NS",
        "WIPRO.NS",
        "BAJFINANCE.NS",
        "ADANIENT.NS",
        "TITAN.NS",
        "HINDUNILVR.NS",
        "KOTAKBANK.NS",
        "AXISBANK.NS",
        "MARUTI.NS",
        "SUNPHARMA.NS",
    ]

    data = scan_market(SYMBOLS)

    formatted = _format_output(
        data["top_pick"],
        data["all_opportunities"],
        data["portfolio"],
    )

    return formatted
