import pandas as pd
import numpy as np
import os

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'stocks.csv')

# ── Module-level cache: CSV read once per process ─────────────────────────────
_DF_CACHE = None

def load_data():
    global _DF_CACHE
    if _DF_CACHE is None:
        df = pd.read_csv(DATA_PATH, parse_dates=['Date'])
        df.set_index('Date', inplace=True)
        _DF_CACHE = df
    return _DF_CACHE

def get_available_symbols():
    return list(load_data().columns)

def compute_portfolio_value(portfolio_items):
    if not portfolio_items:
        return None, None
    df = load_data()
    symbols    = [p['symbol'] for p in portfolio_items]
    quantities = {p['symbol']: p['quantity'] for p in portfolio_items}
    valid      = [s for s in symbols if s in df.columns]
    if not valid:
        return None, None
    prices = df[valid].dropna()
    value  = sum(prices[s] * quantities[s] for s in valid)
    return value, prices

def compute_metrics(portfolio_items):
    value, prices = compute_portfolio_value(portfolio_items)
    if value is None or len(value) < 2:
        return {}
    returns      = value.pct_change().dropna()
    annual_return = returns.mean() * 252
    volatility    = returns.std()  * np.sqrt(252)
    sharpe        = annual_return / volatility if volatility != 0 else 0
    cumulative    = (1 + returns).cumprod()
    rolling_max   = cumulative.cummax()
    drawdown      = (cumulative - rolling_max) / rolling_max
    max_drawdown  = drawdown.min()
    var_95        = np.percentile(returns, 5)
    return {
        'annual_return':        round(float(annual_return) * 100, 2),
        'volatility':           round(float(volatility)    * 100, 2),
        'sharpe_ratio':         round(float(sharpe), 3),
        'max_drawdown':         round(float(max_drawdown)  * 100, 2),
        'var_95':               round(float(var_95)        * 100, 2),
        'total_value':          round(float(value.iloc[-1]), 2),
        'portfolio_return_pct': round(((float(value.iloc[-1]) / float(value.iloc[0])) - 1) * 100, 2)
    }

def compute_correlation(portfolio_items):
    if not portfolio_items:
        return None
    df      = load_data()
    symbols = [p['symbol'] for p in portfolio_items if p['symbol'] in df.columns]
    if len(symbols) < 2:
        return None
    returns = df[symbols].pct_change().dropna()
    return returns.corr()
