# QuantRisk India Pro — Portfolio Risk Management Platform

A professional, INR-localised portfolio analytics dashboard built with Flask, Python, and Plotly.

## Features
- Secure user authentication (register / login / session / SQLite)
- Portfolio Builder with searchable stock dropdown
- Dashboard — 5 metric cards: Annual Return, Volatility, Sharpe Ratio, Max Drawdown, VaR (95%)
- Portfolio Value chart + Correlation Heatmap
- Risk Analytics page — full metric breakdown + charts
- AI Evaluation — Random Forest Classifier portfolio quality assessment
- All monetary values in Indian Rupees (₹), IST clock, NIFTY/SENSEX indicators

## Quick Start

### 1. Generate sample data (run once)
```bash
cd data
python generate_sample_data.py
cd ..
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the app
```bash
python app.py
```

### 4. Open browser
```
http://localhost:5000
```
Register an account, then go to **Portfolio Builder** and add stocks.

## Available Symbols
AAPL, MSFT, TSLA, GOOGL, AMZN, META, NVDA, JPM, BAC, GS,
XOM, CVX, JNJ, PFE, UNH, WMT, HD, DIS, NFLX, PYPL

## Project Structure
```
portfolio_platform/
├── app.py                    ← Flask app + all routes + chart builders
├── requirements.txt
├── data/
│   ├── generate_sample_data.py
│   └── stocks.csv            ← Generated historical prices
├── database/models.py        ← SQLite schema
├── auth/auth.py              ← Secure password hashing
├── portfolio/portfolio.py    ← CRUD operations
├── analytics/analytics.py   ← Financial metrics engine
├── ml/evaluator.py           ← Random Forest classifier
├── templates/                ← Jinja2 HTML templates
└── static/                   ← CSS (Deep Navy theme) + JS utils
```
