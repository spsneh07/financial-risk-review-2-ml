"""Per-asset risk features computed from a daily log-return matrix (T x N)."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.preprocessing import StandardScaler

FEATURES = ["mean_return", "volatility", "skewness", "kurtosis", "VaR_95", "CVaR_95",
            "max_drawdown"]

TRADING_DAYS = 252


def max_drawdown(returns: pd.Series) -> float:
    """Largest peak-to-trough fall of the cumulative wealth curve, as a positive fraction."""
    wealth = np.exp(np.cumsum(np.asarray(returns, dtype=float)))
    wealth = np.concatenate([[1.0], wealth])
    peak = np.maximum.accumulate(wealth)
    return float(np.max(1.0 - wealth / peak))


def historical_var_cvar(returns, level: float = 0.95) -> tuple[float, float]:
    """Historical VaR and CVaR (expected shortfall) reported as positive daily losses.

    VaR_a  = -quantile_{1-a}(r)
    CVaR_a = -E[r | r <= quantile_{1-a}(r)]
    """
    r = np.asarray(returns, dtype=float)
    q = np.quantile(r, 1 - level)
    tail = r[r <= q]
    return float(-q), float(-tail.mean())


def compute_risk_features(returns: pd.DataFrame, level: float = 0.95) -> pd.DataFrame:
    """Return an (N assets x 7 features) DataFrame.

    mean_return and volatility are daily figures (not annualised) so every feature is on the
    daily horizon; kurtosis is *excess* kurtosis (normal = 0).
    """
    rows = {}
    for col in returns.columns:
        r = returns[col].dropna()
        var, cvar = historical_var_cvar(r, level)
        rows[col] = {
            "mean_return": r.mean(),
            "volatility": r.std(ddof=1),
            "skewness": stats.skew(r, bias=False),
            "kurtosis": stats.kurtosis(r, fisher=True, bias=False),
            "VaR_95": var,
            "CVaR_95": cvar,
            "max_drawdown": max_drawdown(r),
        }
    return pd.DataFrame(rows).T[FEATURES].astype(float)


def standardize(features: pd.DataFrame) -> tuple[np.ndarray, StandardScaler]:
    """z-score each feature: distance-based methods otherwise weight features by their units."""
    scaler = StandardScaler()
    return scaler.fit_transform(features.values), scaler


def annualised_view(features: pd.DataFrame) -> pd.DataFrame:
    """Human-readable version for the summary table (annualised return/vol, % units)."""
    out = pd.DataFrame(index=features.index)
    out["Ann. return %"] = features["mean_return"] * TRADING_DAYS * 100
    out["Ann. vol %"] = features["volatility"] * np.sqrt(TRADING_DAYS) * 100
    out["Skew"] = features["skewness"]
    out["Ex. kurtosis"] = features["kurtosis"]
    out["VaR95 %"] = features["VaR_95"] * 100
    out["CVaR95 %"] = features["CVaR_95"] * 100
    out["Max DD %"] = features["max_drawdown"] * 100
    return out
