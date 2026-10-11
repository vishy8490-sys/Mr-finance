"""
Mr Finance — AI Portfolio Evaluator
Fast version: model built once at module load (~150ms), cached for all requests.
Per-request prediction time: <10ms.
"""

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

# ── Criterion definitions ─────────────────────────────────────────────────────
# (feature_idx, 'higher'|'lower', ideal, terrible, weight)
CRITERIA = [
    (0, 'higher',  20.0,  -5.0,  2.0),   # annual_return
    (1, 'lower',   10.0,  50.0,  1.5),   # volatility
    (2, 'higher',   2.0,   0.0,  2.5),   # sharpe
    (3, 'higher',  -5.0, -50.0,  1.5),   # max_drawdown
    (4, 'higher',   2.5,   0.0,  2.0),   # sortino
    (5, 'higher',   1.5,   0.0,  1.5),   # calmar
    (6, 'higher',   3.0,   0.0,  1.0),   # recovery_factor
    (7, 'higher',   0.5,  -2.0,  0.5),   # skewness proxy
    (8, 'higher',  -0.5,  -5.0,  1.0),   # var_95
]
TOTAL_WEIGHT = sum(c[4] for c in CRITERIA)

FEATURE_NAMES = [
    'Annual Return', 'Volatility', 'Sharpe Ratio', 'Max Drawdown',
    'Sortino Ratio', 'Calmar Ratio', 'Recovery Factor', 'Return Skewness', 'VaR (95%)'
]

# ── Scoring helper ────────────────────────────────────────────────────────────
def _criterion_score(val, direction, ideal, terrible):
    if direction == 'higher':
        s = (val - terrible) / (ideal - terrible)
    else:
        s = (terrible - val) / (terrible - ideal)
    return max(0.0, min(1.0, s))

def _composite_score(features):
    ws = sum(
        _criterion_score(features[idx], d, ideal, terrible) * w
        for idx, d, ideal, terrible, w in CRITERIA
    )
    return (ws / TOTAL_WEIGHT) * 100.0

# ── Training data ─────────────────────────────────────────────────────────────
def _generate_training_data(n=800):
    rng = np.random.default_rng(42)
    rows, labels = [], []
    strong = weak = 0
    target = n // 2

    for _ in range(n * 25):
        if strong >= target and weak >= target:
            break
        ret      = float(rng.uniform(-15, 45))
        vol      = float(rng.uniform(5,   65))
        sharpe   = float(rng.uniform(-0.5, 3.5))
        mdd      = float(rng.uniform(-70, -2))
        sortino  = max(0.0, sharpe * float(rng.uniform(0.9, 1.8)))
        calmar   = max(0.0, ret / abs(mdd)) if mdd != 0 else 0.0
        recovery = max(0.0, (ret / abs(mdd)) * float(rng.uniform(0.5, 2.5))) if mdd != 0 else 0.0
        skew     = float(rng.uniform(-2.5, 1.5))
        var95    = float(rng.uniform(-6.0, -0.3))
        feats    = [ret, vol, sharpe, mdd, sortino, calmar, recovery, skew, var95]
        score    = _composite_score(feats)
        if score >= 55 and strong < target:
            rows.append(feats); labels.append(1); strong += 1
        elif score < 45 and weak < target:
            rows.append(feats); labels.append(0); weak += 1

    return np.array(rows, dtype=float), np.array(labels, dtype=int)

# ── Build model ONCE at module load ──────────────────────────────────────────
_X, _y          = _generate_training_data(n=800)
_SCALER         = StandardScaler()
_X_sc           = _SCALER.fit_transform(_X)
_CLF            = RandomForestClassifier(
                    n_estimators=30,
                    random_state=42,
                    min_samples_leaf=4,
                    n_jobs=1
                  )
_CLF.fit(_X_sc, _y)

# ── Feature extraction ────────────────────────────────────────────────────────
def _compute_features(metrics):
    ret    = float(metrics.get('annual_return', 0.0))
    vol    = float(metrics.get('volatility',    0.0))
    sharpe = float(metrics.get('sharpe_ratio',  0.0))
    mdd    = float(metrics.get('max_drawdown',  -1.0))
    var95  = float(metrics.get('var_95',        -2.0))
    total  = float(metrics.get('portfolio_return_pct', ret))

    dv       = vol * 0.7 if vol > 0 else 1.0
    sortino  = ret / dv  if dv != 0 else 0.0
    calmar   = ret / abs(mdd)   if mdd != 0 else 0.0
    recovery = total / abs(mdd) if mdd != 0 else 0.0

    expected_var = -1.645 * (vol / 100.0) * 100.0
    skew_proxy   = -(expected_var - var95) / (vol + 1e-9)

    return [ret, vol, sharpe, mdd, sortino, calmar, recovery, skew_proxy, var95]

# ── Public API ────────────────────────────────────────────────────────────────
def evaluate_portfolio(metrics):
    if not metrics:
        return {
            'label': 'No Portfolio', 'is_strong': False,
            'probability': 0, 'score': 0,
            'feature_importance': {}, 'breakdown': []
        }

    feats    = _compute_features(metrics)
    score    = _composite_score(feats)
    feats_sc = _SCALER.transform([feats])
    proba    = _CLF.predict_proba(feats_sc)[0]
    strong_p = float(proba[1])

    # Label from score (primary) + model (secondary)
    if score >= 65:
        is_strong, label = True,  'Strong Portfolio'
    elif score <= 35:
        is_strong, label = False, 'Weak Portfolio'
    else:
        is_strong = strong_p >= 0.5
        label     = 'Moderate Portfolio'

    # Blended confidence
    confidence = round(score * 0.55 + strong_p * 100 * 0.45, 1)
    confidence = max(5.0, min(99.5, confidence))

    # Per-criterion breakdown
    breakdown = []
    for i, (idx, direction, ideal, terrible, weight) in enumerate(CRITERIA):
        val = feats[idx]
        s   = round(_criterion_score(val, direction, ideal, terrible) * 100, 1)
        breakdown.append({
            'name':   FEATURE_NAMES[i],
            'value':  round(val, 3),
            'score':  s,
            'weight': weight,
            'pass':   s >= 50
        })

    feature_imp = {
        FEATURE_NAMES[i]: round(float(_CLF.feature_importances_[i]), 4)
        for i in range(9)
    }

    return {
        'label':              label,
        'is_strong':          bool(is_strong),
        'probability':        confidence,
        'score':              round(score, 1),
        'feature_importance': feature_imp,
        'breakdown':          breakdown
    }
