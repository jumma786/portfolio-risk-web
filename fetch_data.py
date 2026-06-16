"""
Daily S&P 500 Data Fetcher
===========================
Fetches stock data for common S&P 500 tickers and saves to data/stock_data.json
Run by GitHub Actions daily at 6am UTC.

Usage:
  python fetch_data.py
"""

import json
import os
import time
import yfinance as yf
from datetime import datetime

TICKERS = [
    "AAPL","MSFT","AMZN","NVDA","GOOGL","META","TSLA","JPM","UNH","XOM",
    "JNJ","V","PG","MA","HD","CVX","MRK","ABBV","PEP","KO","AVGO","COST",
    "WMT","BAC","TMO","MCD","ACN","LIN","ABT","CRM","DHR","NEE","TXN","PM",
    "UNP","RTX","HON","BMY","AMGN","LOW","QCOM","IBM","GE","CAT","BA","GS",
    "MS","BLK","SPGI","WFC","NFLX","ADBE","COP","AMD","INTC","AMAT","MU",
    "NOW","ISRG","VRTX","REGN","GILD","MDLZ","ADI","KLAC","LRCX","SNPS",
    "CDNS","MCHP","NXPI","TER","MPWR","ENPH","FSLR","NEE","AEP","DUK","SO",
    "D","EXC","SRE","PEG","ED","ES","ETR","FE","PPL","CMS","NI","AES",
    "JPM","BAC","WFC","GS","MS","C","USB","PNC","TFC","COF","AXP","BK",
    "STT","SCHW","BLK","MCO","SPGI","ICE","CME","NDAQ"
]
TICKERS = list(set(TICKERS))

def fetch_all():
    print(f"Fetching data for {len(TICKERS)} tickers...")
    stock_data = {}
    failed = []

    for i, ticker in enumerate(TICKERS, 1):
        print(f"  [{i}/{len(TICKERS)}] {ticker}", end="\r")
        try:
            t    = yf.Ticker(ticker)
            info = t.info
            hist = t.history(period="1y")

            if not info.get("sector"):
                failed.append(ticker)
                continue

            closes = []
            if not hist.empty:
                closes = hist["Close"].dropna().tolist()[-252:]

            stock_data[ticker] = {
                "name":      (info.get("shortName") or ticker).replace(" Inc.","").replace(" Inc",""),
                "sector":    info.get("sector") or "Other",
                "industry":  info.get("industry") or "",
                "price":     round(info.get("currentPrice") or info.get("regularMarketPrice") or 0, 2),
                "pe_ratio":  round(info.get("trailingPE"), 1) if info.get("trailingPE") and 0 < info.get("trailingPE") < 1000 else None,
                "div_yield": round((info.get("trailingAnnualDividendYield") or 0) * 100, 2),
                "beta":      round(info.get("beta"), 2) if info.get("beta") else 1.0,
                "mkt_cap":   info.get("marketCap") or 0,
                "closes":    closes,
            }
            time.sleep(0.3)

        except Exception as e:
            failed.append(ticker)
            continue

    print(f"\nFetched: {len(stock_data)} stocks. Failed: {len(failed)}")

    os.makedirs("data", exist_ok=True)
    output = {
        "updated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        "stocks":     stock_data
    }
    with open("data/stock_data.json", "w") as f:
        json.dump(output, f)
    print(f"Saved: data/stock_data.json ({len(stock_data)} stocks)")

if __name__ == "__main__":
    fetch_all()
