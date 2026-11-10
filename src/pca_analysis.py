"""PCA on the standardised asset-feature matrix."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA

import config


def fit_pca(X_std: np.ndarray, seed: int = config.SEED) -> PCA:
    """Full PCA (all components) on already-standardised features."""
    return PCA(random_state=seed).fit(X_std)


def n_components_for(pca: PCA, target: float = config.PCA_VARIANCE_TARGET) -> int:
    cum = np.cumsum(pca.explained_variance_ratio_)
    return int(np.searchsorted(cum, target) + 1)


def transform(pca: PCA, X_std: np.ndarray, n: int) -> np.ndarray:
    return pca.transform(X_std)[:, :n]


def loadings_table(pca: PCA, feature_names, n: int) -> pd.DataFrame:
    return pd.DataFrame(pca.components_[:n].T, index=feature_names,
                        columns=[f"PC{i + 1}" for i in range(n)])


def variance_table(pca: PCA) -> pd.DataFrame:
    r = pca.explained_variance_ratio_
    return pd.DataFrame({"PC": [f"PC{i + 1}" for i in range(len(r))],
                         "explained_variance_ratio": r,
                         "cumulative": np.cumsum(r)})
