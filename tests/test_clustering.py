import numpy as np
import pandas as pd
import pytest

from src import clustering as cl
from src import evaluation as ev
from src import risk_features as rf
from src import stability as st


@pytest.fixture
def blobs():
    rng = np.random.default_rng(0)
    centers = np.array([[0, 0, 0], [6, 6, 0], [0, 6, 6]])
    X = np.vstack([c + rng.normal(0, 0.4, (8, 3)) for c in centers])
    y = np.repeat([0, 1, 2], 8)
    return X, y


def test_three_algorithms_recover_blobs(blobs):
    X, y = blobs
    assert ev.ari(y, cl.kmeans_fit(X, 3).labels_) == pytest.approx(1.0)
    assert ev.ari(y, cl.gmm_fit(X, 3).predict(X)) == pytest.approx(1.0)
    assert ev.ari(y, cl.hierarchical_fit(X, 3, "ward").labels_) == pytest.approx(1.0)


def test_ward_rejects_precomputed(blobs):
    X, _ = blobs
    with pytest.raises(ValueError):
        cl.hierarchical_precomputed(np.zeros((len(X), len(X))), 3, "ward")


def test_precomputed_average_linkage(blobs):
    from src.distance_metrics import manhattan_matrix
    X, y = blobs
    lab = cl.hierarchical_precomputed(manhattan_matrix(X), 3, "average").labels_
    assert ev.ari(y, lab) == pytest.approx(1.0)


def test_ari_label_permutation_invariant():
    a = np.array([0, 0, 1, 1, 2, 2])
    b = np.array([2, 2, 0, 0, 1, 1])
    assert ev.ari(a, b) == pytest.approx(1.0)


def test_relabel_by_risk_orders_clusters():
    labels = np.array([5, 5, 9, 9])
    risk = np.array([3.0, 3.0, 1.0, 1.0])
    assert cl.relabel_by_risk(labels, risk).tolist() == [1, 1, 0, 0]


def test_precomputed_scores_no_db_ch(blobs):
    from src.distance_metrics import cosine_matrix
    X, y = blobs
    s = ev.precomputed_scores(cosine_matrix(X)[0], y)
    assert s["davies_bouldin"] is None and s["calinski_harabasz"] is None


def test_risk_features_known_values():
    r = pd.DataFrame({"A": np.log([1.1, 0.5, 2.0])})
    f = rf.compute_risk_features(r)
    assert f.loc["A", "max_drawdown"] == pytest.approx(1 - 0.55 / 1.1)
    var, cvar = rf.historical_var_cvar(np.arange(-50, 50) / 100, 0.95)
    assert var > 0 and cvar >= var


def test_seed_stability_runs(blobs):
    X, _ = blobs
    tab = st.seed_stability(X, 3, n_runs=5)
    assert (tab["mean_ARI"] <= 1 + 1e-9).all()
    assert tab.loc[tab["method"] == "Hierarchical (Ward)", "mean_ARI"].iloc[0] == 1.0
