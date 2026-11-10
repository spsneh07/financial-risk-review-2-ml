"""Dissimilarity matrices for the metric-comparison experiment.

All functions take the *standardised* asset-feature matrix X (n x p) and return a
symmetric (n x n) matrix with a zero diagonal.

Notes on correctness
--------------------
* Manhattan  d(x,y) = sum_j |x_j - y_j|                 -- a true metric, scale dependent.
* Cosine     d(x,y) = 1 - x.y / (||x|| ||y||)           -- compares *direction* only; it is
  not a metric (no triangle inequality) and is undefined for zero vectors. After
  standardisation an asset close to the cross-sectional average has a near-zero vector
  whose direction is essentially noise, so we flag such rows and add a tiny epsilon.
* Mahalanobis d(x,y) = sqrt((x-y)^T S^-1 (x-y))          -- removes feature correlation
  (e.g. VaR, CVaR and volatility are highly collinear). With 12 assets and 7 features the
  sample covariance is near-singular, so S is Ledoit-Wolf shrunk and inverted with a
  pseudo-inverse.
"""
from __future__ import annotations

import numpy as np
from scipy.spatial.distance import pdist, squareform
from sklearn.covariance import LedoitWolf

EPS = 1e-12


def manhattan_matrix(X: np.ndarray) -> np.ndarray:
    return squareform(pdist(X, metric="cityblock"))


def euclidean_matrix(X: np.ndarray) -> np.ndarray:
    return squareform(pdist(X, metric="euclidean"))


def cosine_matrix(X: np.ndarray, near_zero_tol: float = 0.25) -> tuple[np.ndarray, list[int]]:
    """Cosine distance + indices of rows whose norm is suspiciously small.

    near_zero_tol is relative to the median row norm.
    """
    norms = np.linalg.norm(X, axis=1)
    flagged = list(np.where(norms < near_zero_tol * np.median(norms))[0])
    Xs = X / np.maximum(norms, EPS)[:, None]
    D = 1.0 - Xs @ Xs.T
    D = np.clip((D + D.T) / 2, 0.0, 2.0)
    np.fill_diagonal(D, 0.0)
    return D, flagged


def shrunk_precision(X: np.ndarray) -> tuple[np.ndarray, dict]:
    """Ledoit-Wolf shrunk covariance -> pseudo-inverse. Returns precision + diagnostics."""
    lw = LedoitWolf().fit(X)
    S = lw.covariance_
    raw = np.cov(X, rowvar=False)
    info = {
        "shrinkage": float(lw.shrinkage_),
        "cond_raw_cov": float(np.linalg.cond(raw)),
        "cond_shrunk_cov": float(np.linalg.cond(S)),
        "rank_raw_cov": int(np.linalg.matrix_rank(raw)),
    }
    return np.linalg.pinv(S, hermitian=True), info


def mahalanobis_matrix(X: np.ndarray) -> tuple[np.ndarray, dict]:
    VI, info = shrunk_precision(X)
    D = squareform(pdist(X, metric="mahalanobis", VI=VI))
    return D, info


def validate_distance_matrix(D: np.ndarray, tol: float = 1e-9) -> dict:
    """Checks every dissimilarity must satisfy before clustering on it."""
    return {
        "symmetric": bool(np.allclose(D, D.T, atol=tol)),
        "zero_diagonal": bool(np.allclose(np.diag(D), 0.0, atol=tol)),
        "non_negative": bool((D >= -tol).all()),
        "finite": bool(np.isfinite(D).all()),
    }


def all_distance_matrices(X: np.ndarray) -> dict:
    cos, flagged = cosine_matrix(X)
    mah, info = mahalanobis_matrix(X)
    return {
        "Euclidean": {"D": euclidean_matrix(X), "notes": {}},
        "Manhattan": {"D": manhattan_matrix(X), "notes": {}},
        "Cosine": {"D": cos, "notes": {"near_zero_rows": flagged}},
        "Mahalanobis": {"D": mah, "notes": info},
    }
