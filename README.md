# Portfolio Risk & Concentration Analyser — Web App

![Python](https://img.shields.io/badge/Python-3.11-blue) ![Flask](https://img.shields.io/badge/Flask-3.0-lightgrey) ![yfinance](https://img.shields.io/badge/Data-yfinance-green) ![Render](https://img.shields.io/badge/Deployed-Render-purple) ![Status](https://img.shields.io/badge/Status-Live-brightgreen)

**Live app:** https://portfolio-risk-analyser.onrender.com

A web application that analyses any stock portfolio for sector concentration risk, correlation, volatility, and drawdown exposure — generating a plain-English risk report instantly in the browser. No Python, no terminal, no setup required.

---

## The problem this solves

Most investors think they are diversified. They are not.

A portfolio holding Apple, Microsoft, Nvidia, Google, and Meta feels like 5 positions. It behaves like 1 — because all five are Technology stocks that move together when rates rise or regulation hits the sector. The investor finds out only when their portfolio drops 30%.

This tool makes invisible concentration risk visible in under 60 seconds.

---

## Live demo

Visit **https://portfolio-risk-analyser.onrender.com**

Three example portfolios are preloaded:
- **Tech-heavy** — shows HIGH RISK (70/100) with 45% Technology exposure
- **Well diversified** — shows WELL DIVERSIFIED (15/100) across 11 sectors
- **Income focused** — shows dividend-heavy defensive positioning

Or enter your own stock tickers and weights.

> Note: Free tier hosting spins down after inactivity — first load may take 30–60 seconds.

---

## What it analyses

| Metric | Description |
|---|---|
| Concentration score 0–100 | Single number summarising overall portfolio risk |
| Sector exposure vs benchmark | Where the portfolio is overweight vs a balanced allocation |
| Annualised volatility | Expected yearly price swing of the combined portfolio |
| Portfolio beta | How much the portfolio moves relative to the market |
| Estimated drawdown | Expected loss in a 2022-style tech selloff scenario |
| Correlation heatmap | Which stocks move together — reveals hidden concentration |
| Risk factors | Specific problems flagged automatically in plain English |
| Recommendations | Actionable steps to reduce concentration risk |

---

## Key findings from testing

**Tech-heavy portfolio** (AAPL, MSFT, NVDA, GOOGL, META + 4 others)

| Metric | Value |
|---|---|
| Concentration score | 70/100 — HIGH RISK |
| Technology exposure | 45% — significantly above 25% recommended |
| Annualised volatility | 11.6% |
| Portfolio beta | 1.01 |
| Est. drawdown (2022 scenario) | -24.0% |

**Well-diversified portfolio** (12 stocks across 11 sectors)

| Metric | Value |
|---|---|
| Concentration score | 15/100 — WELL DIVERSIFIED |
| Largest sector | 16.7% — within safe range |
| Annualised volatility | 9.5% — 18% lower |
| Portfolio beta | 0.81 — defensive |
| Est. drawdown (2022 scenario) | -18.3% — 6% less loss in a crisis |

**Key insight:** Sector matters more than company name. Holding Apple and Microsoft feels diversified — both are Technology and fall together in a rate rise. The correlation heatmap reveals this hidden risk instantly.

---

## How it works

```
User inputs portfolio
        ↓
Flask app reads from data/stock_data.json (pre-fetched daily)
        ↓
Calculates sector exposure, volatility, beta, correlation
        ↓
Generates risk score, plain English risk factors, recommendations
        ↓
Returns interactive report with charts in browser
```

**Data pipeline:**
GitHub Actions runs `fetch_data.py` every weekday at 6am UTC — fetches live data for 100+ S&P 500 stocks via Yahoo Finance and commits `data/stock_data.json` to the repo. Render serves the app from this cached data — no live API calls needed, no Yahoo Finance blocking.

---

## Tech stack

| Layer | Tool |
|---|---|
| Web framework | Flask 3.0 |
| Data source | Yahoo Finance via `yfinance` |
| Data pipeline | GitHub Actions (daily, weekdays 6am UTC) |
| Charts | Matplotlib, Seaborn |
| Deployment | Render (Docker) |
| Environment | Python 3.11 |

---

## Run locally

```bash
git clone https://github.com/jumma786/portfolio-risk-web
cd portfolio-risk-web
pip install flask yfinance pandas numpy matplotlib seaborn gunicorn
python fetch_data.py   # fetch stock data (~5 minutes)
python app.py          # start Flask server
```

Open **http://localhost:5000**

---

## Project structure

```
portfolio-risk-web/
├── app.py                          — Flask application + risk engine
├── fetch_data.py                   — daily data fetcher
├── templates/
│   └── index.html                  — web interface
├── data/
│   └── stock_data.json             — pre-fetched stock data (auto-updated)
├── .github/workflows/
│   └── fetch_data.yml              — GitHub Actions daily pipeline
├── requirements.txt
├── Dockerfile
└── README.md
```

---

## Limitations

- Data refreshed daily — not real-time intraday prices
- Beta and correlation based on 1-year historical returns
- Drawdown estimate uses simplified 2022 scenario, not Monte Carlo simulation
- Free tier hosting spins down after inactivity — cold start takes 30–60 seconds
- Stocks not in the pre-fetched list fall back to live Yahoo Finance fetch

---

## Related projects

- [S&P 500 Stock Screener](https://github.com/jumma786/sp500-stock-screener) — live screener with XGBoost analyst rating classifier
- [Portfolio Risk Analyser (CLI)](https://github.com/jumma786/portfolio-risk-analyser) — command-line version with HTML report output

---

## About

Built by **Jumma Mohammad Teli** — Data Analyst & ML Engineer at UBS London.

Part of a financial analytics portfolio spanning live market data pipelines, XGBoost modelling, NLP analysis, and MLOps engineering.

[LinkedIn](https://linkedin.com/in/jumma-mohammad) · [GitHub](https://github.com/jumma786)
