"""
Portfolio Risk Analyser — Flask Web App
========================================
Run locally:
  conda activate mlops
  pip install flask yfinance pandas numpy matplotlib seaborn gunicorn --break-system-packages
  python app.py

Deploy to Render:
  - Connect GitHub repo
  - Build command: pip install -r requirements.txt
  - Start command: gunicorn app:app
"""

from flask import Flask, render_template, request, jsonify
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import base64
import io
import time
import json
import os
import warnings
warnings.filterwarnings("ignore")

app = Flask(__name__)

# ── Sector colours ────────────────────────────────────────────────────────────
SECTOR_COLORS = {
    "Technology":               "#185FA5",
    "Financial Services":       "#0C447C",
    "Healthcare":               "#3B6D11",
    "Consumer Defensive":       "#534AB7",
    "Industrials":              "#0F6E56",
    "Energy":                   "#854F0B",
    "Basic Materials":          "#993C1D",
    "Utilities":                "#993556",
    "Consumer Cyclical":        "#639922",
    "Real Estate":              "#A32D2D",
    "Communication Services":   "#378ADD",
    "Other":                    "#888780",
}

BENCHMARK = {
    "Technology":25,"Financial Services":15,"Healthcare":15,
    "Consumer Defensive":10,"Industrials":10,"Energy":8,
    "Communication Services":8,"Other":9
}


def fig_to_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    buf.seek(0)
    img_b64 = base64.b64encode(buf.read()).decode("utf-8")
    plt.close(fig)
    return img_b64


def load_stock_cache():
    """Load pre-fetched stock data from JSON file."""
    cache_path = os.path.join(os.path.dirname(__file__), "data", "stock_data.json")
    if os.path.exists(cache_path):
        with open(cache_path) as f:
            data = json.load(f)
        return data.get("stocks", {}), data.get("updated_at", "")
    return {}, ""


def fetch_data(portfolio):
    import pandas as pd
    info_data  = {}
    price_data = {}

    # Try loading from cache first
    cache, updated_at = load_stock_cache()

    for ticker in portfolio:
        if ticker in cache:
            s = cache[ticker]
            info_data[ticker] = {
                "name":      s.get("name", ticker),
                "sector":    s.get("sector", "Other"),
                "price":     s.get("price", 0),
                "pe_ratio":  s.get("pe_ratio"),
                "div_yield": s.get("div_yield", 0),
                "beta":      s.get("beta", 1.0),
                "mkt_cap":   s.get("mkt_cap", 0),
            }
            closes = s.get("closes", [])
            if closes:
                price_data[ticker] = pd.Series(closes)
        else:
            # Fallback: try live fetch for tickers not in cache
            try:
                t    = yf.Ticker(ticker)
                info = t.info
                hist = t.history(period="1y")
                info_data[ticker] = {
                    "name":      (info.get("shortName") or ticker).replace(" Inc.","").replace(" Inc",""),
                    "sector":    info.get("sector") or "Other",
                    "price":     round(info.get("currentPrice") or info.get("regularMarketPrice") or 0, 2),
                    "pe_ratio":  round(info.get("trailingPE"), 1) if info.get("trailingPE") and info.get("trailingPE") < 1000 else None,
                    "div_yield": round((info.get("trailingAnnualDividendYield") or 0) * 100, 2),
                    "beta":      round(info.get("beta"), 2) if info.get("beta") else 1.0,
                    "mkt_cap":   info.get("marketCap") or 0,
                }
                if not hist.empty:
                    price_data[ticker] = hist["Close"]
                time.sleep(0.3)
            except Exception:
                info_data[ticker] = {
                    "name": ticker, "sector": "Other", "price": 0,
                    "pe_ratio": None, "div_yield": 0, "beta": 1.0, "mkt_cap": 0
                }

    return info_data, price_data


def calculate_metrics(portfolio, info_data, price_data):
    sector_exposure = {}
    for ticker, weight in portfolio.items():
        sector = info_data[ticker]["sector"]
        sector_exposure[sector] = sector_exposure.get(sector, 0) + weight

    max_sector_weight = max(sector_exposure.values())
    n_sectors = len(sector_exposure)

    if max_sector_weight >= 0.50:   concentration_score = 85
    elif max_sector_weight >= 0.40: concentration_score = 70
    elif max_sector_weight >= 0.30: concentration_score = 50
    elif max_sector_weight >= 0.20: concentration_score = 30
    else:                           concentration_score = 15

    if n_sectors <= 3:   concentration_score = min(100, concentration_score + 15)
    elif n_sectors <= 5: concentration_score = min(100, concentration_score + 5)

    max_single = max(portfolio.values()) * 100
    if max_single > 30:   concentration_score = min(100, concentration_score + 15)
    elif max_single > 20: concentration_score = min(100, concentration_score + 10)

    returns_df = pd.DataFrame()
    for ticker, prices in price_data.items():
        if len(prices) > 50:
            returns_df[ticker] = prices.pct_change().dropna()

    correlation_matrix = returns_df.corr() if not returns_df.empty else pd.DataFrame()

    if not returns_df.empty:
        weights    = np.array([portfolio.get(t, 0) for t in returns_df.columns])
        weights    = weights / weights.sum()
        cov_matrix = returns_df.cov() * 252
        port_vol   = round(np.sqrt(weights.T @ cov_matrix.values @ weights) * 100, 1)
    else:
        port_vol = None

    port_beta      = round(sum(portfolio[t] * info_data[t]["beta"] for t in portfolio), 2)
    port_div_yield = round(sum(portfolio[t] * info_data[t]["div_yield"] for t in portfolio), 2)
    pe_values      = [(portfolio[t], info_data[t]["pe_ratio"]) for t in portfolio if info_data[t]["pe_ratio"]]
    port_pe        = round(sum(w*pe for w,pe in pe_values) / sum(w for w,_ in pe_values), 1) if pe_values else None
    tech_weight    = sector_exposure.get("Technology", 0)
    est_drawdown   = round(-(tech_weight * 35 + (1 - tech_weight) * 15), 1)

    return {
        "sector_exposure":      sector_exposure,
        "concentration_score":  round(concentration_score, 1),
        "correlation_matrix":   correlation_matrix,
        "port_volatility":      port_vol,
        "port_beta":            port_beta,
        "port_div_yield":       port_div_yield,
        "port_pe":              port_pe,
        "estimated_drawdown":   est_drawdown,
        "max_single_holding":   round(max_single, 1),
        "n_sectors":            n_sectors,
    }


def assess_risk(metrics):
    risks = []
    recs  = []
    sec   = metrics["sector_exposure"]

    for sector, weight in sorted(sec.items(), key=lambda x: -x[1]):
        pct = round(weight * 100, 1)
        if sector == "Technology" and weight > 0.35:
            risks.append(f"Technology overweight at {pct}% — high sensitivity to rate rises and regulatory risk")
            recs.append("Reduce Technology below 30% — consider adding Healthcare or Consumer Staples")
        elif weight > 0.40:
            risks.append(f"{sector} dominates at {pct}% — single sector concentration risk")
            recs.append(f"Reduce {sector} and spread across 3+ sectors")

    if metrics["port_beta"] > 1.3:
        risks.append(f"Portfolio beta {metrics['port_beta']} — significantly more volatile than the market")
        recs.append("Add low-beta defensive stocks — Utilities, Consumer Staples, Healthcare")
    elif metrics["port_beta"] > 1.1:
        risks.append(f"Portfolio beta {metrics['port_beta']} — moderately above market volatility")

    if metrics["max_single_holding"] > 25:
        risks.append(f"Largest single holding is {metrics['max_single_holding']}% — excessive single stock concentration")
        recs.append("Cap individual positions at 15-20% maximum")

    missing = [s for s in ["Healthcare","Consumer Defensive","Utilities","Energy","Industrials"] if s not in sec]
    if len(missing) >= 3:
        risks.append(f"No exposure to {', '.join(missing[:3])} — lacks defensive positioning")
        recs.append(f"Add {missing[0]} and {missing[1]} for downside protection")

    score = metrics["concentration_score"]
    if score >= 70:   rating, color = "HIGH RISK",          "#dc2626"
    elif score >= 40: rating, color = "MODERATE RISK",      "#d97706"
    else:             rating, color = "WELL DIVERSIFIED",   "#2d6a04"

    return risks[:5], recs[:3], rating, color


def build_charts(portfolio, info_data, metrics):
    sec    = metrics["sector_exposure"]
    labels = [f"{s}\n{round(w*100,1)}%" for s, w in sec.items()]
    colors = [SECTOR_COLORS.get(s, "#888780") for s in sec.keys()]

    # Chart 1: Sector pie + holdings bar
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    axes[0].pie(list(sec.values()), labels=labels, colors=colors, startangle=90)
    axes[0].set_title("Sector exposure", fontweight="bold")

    tickers     = list(portfolio.keys())
    weights     = [portfolio[t] * 100 for t in tickers]
    bar_colors  = [SECTOR_COLORS.get(info_data[t]["sector"], "#888780") for t in tickers]
    axes[1].barh(tickers, weights, color=bar_colors)
    axes[1].axvline(20, color="red", linestyle="--", linewidth=1, label="20% threshold")
    axes[1].set_xlabel("Weight (%)")
    axes[1].set_title("Holdings weight", fontweight="bold")
    axes[1].legend(fontsize=9)
    axes[1].spines[["top","right"]].set_visible(False)
    plt.tight_layout()
    sector_img = fig_to_base64(fig)

    # Chart 2: Correlation heatmap
    corr = metrics["correlation_matrix"]
    if not corr.empty and len(corr) > 1:
        fig2, ax2 = plt.subplots(figsize=(max(8, len(corr)), max(6, len(corr)-1)))
        mask = np.triu(np.ones_like(corr, dtype=bool))
        sns.heatmap(corr, mask=mask, annot=True, fmt=".2f", cmap="RdYlGn_r",
                    vmin=-1, vmax=1, center=0, ax=ax2, cbar_kws={"shrink":0.8})
        ax2.set_title("Stock correlation matrix (1-year daily returns)\nRed = moves together, Green = diversified", fontsize=11)
        plt.tight_layout()
        corr_img = fig_to_base64(fig2)
    else:
        corr_img = None

    return sector_img, corr_img


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/analyse", methods=["POST"])
def analyse():
    try:
        data     = request.get_json()
        holdings = data.get("holdings", [])

        if not holdings:
            return jsonify({"error": "No holdings provided"}), 400

        portfolio = {}
        for h in holdings:
            ticker = h["ticker"].strip().upper()
            weight = float(h["weight"]) / 100
            if ticker and weight > 0:
                portfolio[ticker] = weight

        if not portfolio:
            return jsonify({"error": "Invalid portfolio data"}), 400

        total = sum(portfolio.values())
        if abs(total - 1.0) > 0.01:
            portfolio = {k: v/total for k, v in portfolio.items()}

        info_data, price_data = fetch_data(portfolio)
        metrics               = calculate_metrics(portfolio, info_data, price_data)
        risks, recs, rating, rating_color = assess_risk(metrics)
        sector_img, corr_img  = build_charts(portfolio, info_data, metrics)

        holdings_data = []
        for ticker, weight in sorted(portfolio.items(), key=lambda x: -x[1]):
            info = info_data[ticker]
            holdings_data.append({
                "ticker":    ticker,
                "name":      info["name"],
                "sector":    info["sector"],
                "weight":    round(weight * 100, 1),
                "price":     info["price"],
                "pe_ratio":  info["pe_ratio"],
                "div_yield": info["div_yield"],
                "beta":      info["beta"],
            })

        sector_data = []
        for sector, weight in sorted(metrics["sector_exposure"].items(), key=lambda x: -x[1]):
            pct   = round(weight * 100, 1)
            bench = BENCHMARK.get(sector, 5)
            diff  = round(pct - bench, 1)
            sector_data.append({
                "sector": sector, "pct": pct,
                "bench": bench, "diff": diff
            })

        return jsonify({
            "rating":             rating,
            "rating_color":       rating_color,
            "concentration_score": metrics["concentration_score"],
            "port_volatility":    metrics["port_volatility"],
            "port_beta":          metrics["port_beta"],
            "port_div_yield":     metrics["port_div_yield"],
            "estimated_drawdown": metrics["estimated_drawdown"],
            "max_single_holding": metrics["max_single_holding"],
            "n_sectors":          metrics["n_sectors"],
            "risks":              risks,
            "recommendations":    recs,
            "holdings":           holdings_data,
            "sectors":            sector_data,
            "sector_img":         sector_img,
            "corr_img":           corr_img,
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
# test
