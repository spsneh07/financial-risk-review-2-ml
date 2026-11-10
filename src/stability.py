"""Cluster-stability experiments measured with the Adjusted Rand Index (ARI).

Raw labels are arbitrary integers: run A may call the low-risk group "0" and run B call the
same group "2". ARI compares *partitions* (which pairs of assets are grouped together), so it
is invariant to label permutations: 1 = identical partition, ~0 = chance agreement.

Experiments
-----------
1. Initialisation stability -- same data, different random seeds (K-means, GMM).
   Agglomerative clustering is deterministic, so its ARI is 1 by construction.
2. Moving-block bootstrap   -- resample blocks of trading days (same days for every asset, so
   cross-asset correlation and volatility clustering are preserved), recompute the risk
   features, re-standardise, re-cluster and compare with the full-sample partition.
3. Leave-one-asset-out      -- drop each asset, re-cluster the other 11, compare on them.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.mixture import GaussianMixture

import config
from src import clustering, distance_metrics as dm
from src.evaluation import ari, pairwise_ari
from src.risk_features import compute_risk_features, standardize


def seed_stability(X, k, n_runs=config.N_SEED_RUNS, gmm_cov="spherical") -> pd.DataFrame:
    km_labels, gmm_labels = [], []
    for s in range(n_runs):
        km_labels.append(KMeans(n_clusters=k, n_init=1, init="random",
                                random_state=s).fit_predict(X))
        gmm_labels.append(GaussianMixture(n_components=k, covariance_type=gmm_cov,
                                          n_init=1, init_params="random", random_state=s,
                                          reg_covar=clustering.GMM_REG_COVAR).fit(X).predict(X))
    kmpp = [clustering.kmeans_fit(X, k, seed=s, n_init=20).labels_ for s in range(n_runs)]
    hc = clustering.hierarchical_fit(X, k, "ward").labels_
    rows = []
    for name, labs in [("K-means (random init, n_init=1)", km_labels),
                       ("K-means (k-means++, n_init=20)", kmpp),
                       ("GMM (random init, n_init=1)", gmm_labels),
                       ("Hierarchical (Ward)", [hc, clustering.hierarchical_fit(X, k, "ward").labels_])]:
        a = pairwise_ari(labs)
        rows.append({"method": name, "mean_ARI": a.mean(), "std_ARI": a.std(),
                     "min_ARI": a.min(), "n_runs": len(labs)})
    return pd.DataFrame(rows)


def _block_bootstrap_index(T, block, rng):
    n_blocks = int(np.ceil(T / block))
    starts = rng.integers(0, T - block + 1, n_blocks)
    idx = np.concatenate([np.arange(s, s + block) for s in starts])[:T]
    return idx


def _cluster_all(X, k, gmm_cov):
    out = {
        "K-means": clustering.kmeans_fit(X, k, n_init=10).labels_,
        "GMM": clustering.gmm_fit(X, k, gmm_cov, n_init=5).predict(X),
        "Hierarchical-Ward": clustering.hierarchical_fit(X, k, "ward").labels_,
    }
    mats = dm.all_distance_matrices(X)
    for name in ["Euclidean", "Manhattan", "Cosine", "Mahalanobis"]:
        out[f"Avg-link {name}"] = clustering.hierarchical_precomputed(
            mats[name]["D"], k, "average").labels_
    return out


def bootstrap_stability(returns: pd.DataFrame, k, n_boot=config.N_BOOTSTRAP,
                        block=config.BOOTSTRAP_BLOCK, gmm_cov="spherical",
                        seed=config.SEED) -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    X_ref, _ = standardize(compute_risk_features(returns))
    ref = _cluster_all(X_ref, k, gmm_cov)
    records = []
    R = returns.values
    for b in range(n_boot):
        idx = _block_bootstrap_index(len(R), block, rng)
        boot = pd.DataFrame(R[idx], columns=returns.columns)
        Xb, _ = standardize(compute_risk_features(boot))
        labs = _cluster_all(Xb, k, gmm_cov)
        for m in ref:
            records.append({"run": b, "method": m, "ARI": ari(ref[m], labs[m])})
    raw = pd.DataFrame(records)
    summary = (raw.groupby("method")["ARI"]
               .agg(mean_ARI="mean", std_ARI="std", median_ARI="median",
                    p10_ARI=lambda s: s.quantile(0.10))
               .reset_index().sort_values("mean_ARI", ascending=False))
    return summary, raw


def leave_one_out_stability(X, names, k, gmm_cov="spherical") -> pd.DataFrame:
    ref = _cluster_all(X, k, gmm_cov)
    rows = []
    for i, nm in enumerate(names):
        keep = np.array([j for j in range(len(X)) if j != i])
        Xi = X[keep]                       # features keep the full-sample scaling
        labs = _cluster_all(Xi, k, gmm_cov)
        for m in ref:
            rows.append({"dropped": nm, "method": m, "ARI": ari(ref[m][keep], labs[m])})
    df = pd.DataFrame(rows)
    return (df.groupby("method")["ARI"].agg(mean_ARI="mean", min_ARI="min")
            .reset_index().sort_values("mean_ARI", ascending=False))
