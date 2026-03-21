from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
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
    symbols = [
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

    data = scan_market(symbols)

    formatted = _format_output(
        data["top_pick"],
        data["all_opportunities"],
        data["portfolio"],
    )

    return formatted
