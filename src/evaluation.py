"""Internal cluster-validity metrics, applied only where mathematically appropriate."""
from __future__ import annotations

import itertools

import numpy as np
from sklearn.metrics import (adjusted_rand_score, calinski_harabasz_score,
                             davies_bouldin_score, silhouette_score)


def _valid(labels) -> bool:
    k = len(set(labels))
    return 1 < k < len(labels)


def euclidean_scores(X, labels) -> dict:
    """Silhouette, Davies-Bouldin and Calinski-Harabasz in a Euclidean feature space.

    DB and CH are defined through centroids / between- and within-cluster *Euclidean*
    scatter, so they are only reported for coordinate data (standardised features or PCs).
    """
    if not _valid(labels):
        return {"silhouette": np.nan, "davies_bouldin": np.nan, "calinski_harabasz": np.nan}
    return {
        "silhouette": float(silhouette_score(X, labels)),
        "davies_bouldin": float(davies_bouldin_score(X, labels)),
        "calinski_harabasz": float(calinski_harabasz_score(X, labels)),
    }


def precomputed_scores(D, labels) -> dict:
    """For an arbitrary dissimilarity matrix only the silhouette is valid (it needs nothing
    but pairwise distances). DB/CH need centroids in a vector space -> reported as N/A."""
    if not _valid(labels):
        return {"silhouette": np.nan, "davies_bouldin": None, "calinski_harabasz": None}
    return {"silhouette": float(silhouette_score(D, labels, metric="precomputed")),
            "davies_bouldin": None, "calinski_harabasz": None}


def pairwise_ari(label_sets) -> np.ndarray:
    """All pairwise ARIs between a list of labelings (label-permutation invariant)."""
    vals = [adjusted_rand_score(a, b) for a, b in itertools.combinations(label_sets, 2)]
    return np.asarray(vals, dtype=float)


def ari(a, b) -> float:
    return float(adjusted_rand_score(a, b))
