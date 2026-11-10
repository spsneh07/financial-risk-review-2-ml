"""Gaussian-emission HMM for market regimes.

Parameter estimation (Baum-Welch / EM) uses hmmlearn with several random restarts.
Inference on the fitted parameters is done by our own NumPy code in src/sum_product.py
and cross-checked against hmmlearn.
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
from hmmlearn.hmm import GaussianHMM

import config
from src import sum_product as sp


def fit_hmm(y_train: np.ndarray, n_states=config.HMM_STATES, restarts=config.HMM_RESTARTS,
            n_iter=config.HMM_N_ITER, seed=config.SEED):
    """Fit a univariate Gaussian HMM with several random restarts; keep the best train log-lik."""
    Y = np.asarray(y_train, dtype=float).reshape(-1, 1)
    best, best_ll, lls = None, -np.inf, []
    for r in range(restarts):
        m = GaussianHMM(n_components=n_states, covariance_type="diag", n_iter=n_iter,
                        tol=1e-6, random_state=seed + r, min_covar=1e-4)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            m.fit(Y)
        ll = m.score(Y)
        lls.append(ll)
        if np.isfinite(ll) and ll > best_ll:
            best, best_ll = m, ll
    return best, {"restart_logliks": lls, "best_train_loglik": best_ll}


def params(model) -> dict:
    """Extract pi, A, means, variances as plain arrays (univariate)."""
    return {
        "pi": np.asarray(model.startprob_),
        "A": np.asarray(model.transmat_),
        "means": np.asarray(model.means_).ravel(),
        "variances": np.asarray(model.covars_).reshape(model.n_components, -1)[:, 0],
    }


def name_states(means, variances) -> dict:
    """Assign economic names from the *learned* parameters (state ids are arbitrary):
      * highest emission variance            -> "High-Volatility"
      * of the remaining, higher mean return -> "Bull"
      * the other                            -> "Bear"
    For K != 3 states are just ranked by variance.
    """
    K = len(means)
    order_var = np.argsort(variances)
    if K != 3:
        return {int(s): f"Regime-{i + 1} (vol rank)" for i, s in enumerate(order_var)}
    hv = int(order_var[-1])
    rest = [s for s in range(3) if s != hv]
    bull = max(rest, key=lambda s: means[s])
    bear = min(rest, key=lambda s: means[s])
    return {bull: "Bull", bear: "Bear", hv: "High-Volatility"}


def log_emissions(model, y) -> np.ndarray:
    p = params(model)
    return sp.gaussian_log_emissions(y, p["means"], p["variances"])


def bic(model, y) -> float:
    K = model.n_components
    n_params = (K - 1) + K * (K - 1) + 2 * K          # pi, A, means, variances
    return -2 * model.score(np.asarray(y).reshape(-1, 1)) + n_params * np.log(len(y))


def model_selection(y_train, y_test, ks=(1, 2, 3, 4), seed=config.SEED) -> pd.DataFrame:
    """Train BIC and out-of-sample predictive log-likelihood for different numbers of states.
    K=1 is the i.i.d. Gaussian baseline."""
    rows = []
    y_all = np.concatenate([y_train, y_test])
    for K in ks:
        if K == 1:
            mu, var = y_train.mean(), y_train.var()
            ll_tr = sp.gaussian_log_emissions(y_train, [mu], [var]).sum()
            ll_te = sp.gaussian_log_emissions(y_test, [mu], [var]).sum()
            rows.append({"states": 1, "train_loglik": ll_tr, "bic": -2 * ll_tr + 2 * np.log(len(y_train)),
                         "test_loglik": ll_te, "test_loglik_per_day": ll_te / len(y_test)})
            continue
        m, _ = fit_hmm(y_train, K, restarts=6, seed=seed)
        p = params(m)
        lb = sp.gaussian_log_emissions(y_all, p["means"], p["variances"])
        pred = sp.one_step_predictive_loglik(p["pi"], p["A"], lb)
        ll_te = pred[len(y_train):].sum()
        rows.append({"states": K, "train_loglik": m.score(y_train.reshape(-1, 1)),
                     "bic": bic(m, y_train), "test_loglik": ll_te,
                     "test_loglik_per_day": ll_te / len(y_test)})
    return pd.DataFrame(rows)
