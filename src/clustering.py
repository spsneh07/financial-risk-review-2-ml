"""K-means, Gaussian Mixture Models and agglomerative hierarchical clustering."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import linkage
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.metrics import silhouette_score
from sklearn.mixture import GaussianMixture

import config

GMM_REG_COVAR = 0.1


# ------------------------------------------------------------------ K-means
def kmeans_fit(X, k, seed=config.SEED, n_init=20):
    """Lloyd's algorithm with k-means++ init; minimises within-cluster *squared Euclidean*
    distance (it is not defined for Manhattan/Cosine/Mahalanobis)."""
    return KMeans(n_clusters=k, n_init=n_init, random_state=seed).fit(X)


def kmeans_sweep(X, k_range=config.K_RANGE, seed=config.SEED) -> pd.DataFrame:
    rows = []
    for k in k_range:
        if k >= len(X):
            continue
        km = kmeans_fit(X, k, seed)
        rows.append({"k": k, "inertia": km.inertia_,
                     "silhouette": silhouette_score(X, km.labels_)})
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ GMM
def gmm_fit(X, k, covariance_type="spherical", seed=config.SEED, n_init=10):
    """EM-fitted Gaussian mixture. With n=12 assets and p=7 features a *full* covariance per
    component (28 params each) is not identifiable, so 'diag'/'spherical' are used and a
    variance floor (reg_covar=0.1 in standardised units) stops EM from shrinking a component
    onto 2-3 assets -- without it BIC keeps improving as k grows, which is overfitting."""
    return GaussianMixture(n_components=k, covariance_type=covariance_type,
                           n_init=n_init, random_state=seed, reg_covar=GMM_REG_COVAR).fit(X)


def gmm_sweep(X, k_range=range(1, 6), cov_types=("spherical", "diag"),
              seed=config.SEED) -> pd.DataFrame:
    rows = []
    for cov in cov_types:
        for k in k_range:
            if k >= len(X):
                continue
            g = gmm_fit(X, k, cov, seed)
            labels = g.predict(X)
            sil = silhouette_score(X, labels) if 1 < len(set(labels)) < len(X) else np.nan
            rows.append({"covariance": cov, "k": k, "bic": g.bic(X), "aic": g.aic(X),
                         "silhouette": sil, "n_used": len(set(labels))})
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ hierarchical
def hierarchical_fit(X, k, linkage_method="ward"):
    """Ward is only valid with Euclidean geometry (it merges the pair that least increases
    the within-cluster sum of squares)."""
    return AgglomerativeClustering(n_clusters=k, linkage=linkage_method,
                                   metric="euclidean").fit(X)


def hierarchical_precomputed(D, k, linkage_method="average"):
    """Agglomerative clustering on an arbitrary precomputed dissimilarity.
    Only average/complete/single linkage are valid here -- never Ward."""
    if linkage_method == "ward":
        raise ValueError("Ward linkage requires Euclidean distances; not allowed with "
                         "precomputed dissimilarities.")
    return AgglomerativeClustering(n_clusters=k, linkage=linkage_method,
                                   metric="precomputed").fit(D)


def linkage_matrix(X, method="ward"):
    return linkage(X, method=method, metric="euclidean")


def hierarchical_sweep(X, k, methods=config.LINKAGES) -> pd.DataFrame:
    rows = []
    for m in methods:
        labels = hierarchical_fit(X, k, m).labels_
        sizes = np.bincount(labels)
        rows.append({"linkage": m, "silhouette": silhouette_score(X, labels),
                     "min_cluster_size": int(sizes.min()),
                     "sizes": "/".join(map(str, sorted(sizes, reverse=True)))})
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ utilities
def best_gmm(gmm_table: pd.DataFrame) -> tuple[str, int]:
    """Lowest-BIC (covariance type, k) combination."""
    best = gmm_table.sort_values("bic").iloc[0]
    return str(best["covariance"]), int(best["k"])


def choose_k(kmeans_table: pd.DataFrame) -> int:
    """Pick k with the best K-means silhouette (ties -> smaller k)."""
    best = kmeans_table.sort_values(["silhouette", "k"], ascending=[False, True]).iloc[0]
    return int(best["k"])


def relabel_by_risk(labels, risk_score) -> np.ndarray:
    """Map arbitrary cluster ids to 0 = lowest-risk ... K-1 = highest-risk using the mean of a
    risk score (e.g. volatility) inside each cluster. Makes tables readable; it does not change
    the partition."""
    labels = np.asarray(labels)
    uniq = np.unique(labels)
    means = {u: np.mean(np.asarray(risk_score)[labels == u]) for u in uniq}
    order = sorted(uniq, key=lambda u: means[u])
    mapping = {u: i for i, u in enumerate(order)}
    return np.array([mapping[l] for l in labels])
