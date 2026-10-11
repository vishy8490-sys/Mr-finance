from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
import numpy as np
from functools import wraps

from database.models import init_db
from auth.auth import register_user, login_user
from portfolio.portfolio import get_portfolio, add_stock, delete_stock
from analytics.analytics import (compute_metrics, compute_correlation,
                                   compute_portfolio_value, get_available_symbols)
from ml.evaluator import evaluate_portfolio

app = Flask(__name__)
app.secret_key = 'quantrisk_india_2024'

with app.app_context():
    init_db()

# ── Plotly chart builder (pure JSON, no server-side plotly needed) ──
def make_chart(traces, layout_extra=None):
    base = {
        'paper_bgcolor': 'rgba(0,0,0,0)',
        'plot_bgcolor':  'rgba(0,0,0,0)',
        'font': {'color': '#94a3b8', 'family': 'Inter, sans-serif'},
        'margin': {'l': 50, 'r': 20, 't': 20, 'b': 50},
        'xaxis': {'gridcolor': 'rgba(255,255,255,0.04)', 'linecolor': 'rgba(255,255,255,0.08)'},
        'yaxis': {'gridcolor': 'rgba(255,255,255,0.04)', 'linecolor': 'rgba(255,255,255,0.08)'},
        'hovermode': 'x unified',
        'legend': {'bgcolor': 'rgba(10,22,40,0.8)', 'bordercolor': 'rgba(255,255,255,0.08)', 'borderwidth': 1}
    }
    if layout_extra:
        base.update(layout_extra)
    return {'data': traces, 'layout': base}

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# ── Auth routes ──
@app.route('/')
def index():
    return redirect(url_for('dashboard') if 'user_id' in session else url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.json or request.form
        ok, user = login_user(data.get('username', ''), data.get('password', ''))
        if ok:
            session['user_id'] = user['id']
            session['username'] = user['username']
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Invalid credentials'})
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.json or request.form
        ok, msg = register_user(data.get('username', ''), data.get('password', ''), data.get('email', ''))
        return jsonify({'success': ok, 'message': msg})
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ── Page routes ──
@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', username=session['username'])

@app.route('/portfolio-builder')
@login_required
def portfolio_builder():
    return render_template('portfolio_builder.html',
                           symbols=get_available_symbols(),
                           username=session['username'])

@app.route('/risk-analytics')
@login_required
def risk_analytics():
    return render_template('risk_analytics.html', username=session['username'])

@app.route('/ai-evaluation')
@login_required
def ai_evaluation():
    return render_template('ai_evaluation.html', username=session['username'])

# ── Portfolio API ──
@app.route('/api/portfolio')
@login_required
def api_get_portfolio():
    return jsonify({'portfolio': get_portfolio(session['user_id'])})

@app.route('/api/portfolio/add', methods=['POST'])
@login_required
def api_add_stock():
    data = request.json
    sym = data.get('symbol', '').upper()
    qty = float(data.get('quantity', 0))
    if sym not in get_available_symbols():
        return jsonify({'success': False, 'message': f'{sym} not found in dataset'})
    if qty <= 0:
        return jsonify({'success': False, 'message': 'Quantity must be positive'})
    add_stock(session['user_id'], sym, qty)
    return jsonify({'success': True})

@app.route('/api/portfolio/delete', methods=['POST'])
@login_required
def api_delete_stock():
    delete_stock(session['user_id'], request.json.get('symbol', '').upper())
    return jsonify({'success': True})

@app.route('/api/metrics')
@login_required
def api_metrics():
    return jsonify(compute_metrics(get_portfolio(session['user_id'])))

# ── Chart API ──
@app.route('/api/chart/portfolio-value')
@login_required
def api_portfolio_value_chart():
    items = get_portfolio(session['user_id'])
    value, _ = compute_portfolio_value(items)
    if value is None:
        return jsonify({'error': 'No portfolio data'})
    traces = [{
        'type': 'scatter', 'mode': 'lines', 'name': 'Portfolio Value',
        'x': value.index.strftime('%Y-%m-%d').tolist(),
        'y': [round(v, 2) for v in value.tolist()],
        'line': {'color': '#6366f1', 'width': 2},
        'fill': 'tozeroy', 'fillcolor': 'rgba(99,102,241,0.06)'
    }]
    return jsonify(make_chart(traces, {'yaxis': {'title': 'Portfolio Value (₹)', 'gridcolor': 'rgba(255,255,255,0.04)'}}))

@app.route('/api/chart/correlation')
@login_required
def api_correlation():
    items = get_portfolio(session['user_id'])
    corr = compute_correlation(items)
    if corr is None:
        return jsonify({'error': 'Need at least 2 stocks'})
    z    = corr.values.tolist()
    text = [[f'{v:.2f}' for v in row] for row in z]
    traces = [{
        'type': 'heatmap',
        'z': z, 'x': corr.columns.tolist(), 'y': corr.index.tolist(),
        'text': text, 'texttemplate': '%{text}',
        'colorscale': [[0, '#0a1628'], [0.5, '#1e3a5f'], [1, '#6366f1']],
        'showscale': True, 'zmin': -1, 'zmax': 1
    }]
    return jsonify(make_chart(traces, {
        'hovermode': 'closest',
        'margin': {'l': 70, 'r': 20, 't': 20, 'b': 70}
    }))

@app.route('/api/ai-evaluation')
@login_required
def api_ai_evaluation():
    items   = get_portfolio(session['user_id'])
    metrics = compute_metrics(items)
    return jsonify(evaluate_portfolio(metrics))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
