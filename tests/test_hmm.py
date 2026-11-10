import numpy as np
import pytest

from src import hmm_model as hm
from src import sum_product as sp


@pytest.fixture(scope="module")
def regime_data():
    rng = np.random.default_rng(0)
    mu, sd = np.array([0.1, -0.1, -0.3]), np.array([0.5, 1.0, 3.0])
    A = np.array([[0.98, 0.015, 0.005], [0.02, 0.97, 0.01], [0.05, 0.05, 0.90]])
    s = [0]
    for _ in range(2999):
        s.append(rng.choice(3, p=A[s[-1]]))
    s = np.array(s)
    return mu[s] + sd[s] * rng.standard_normal(3000), s


@pytest.fixture(scope="module")
def fitted(regime_data):
    y, _ = regime_data
    m, _ = hm.fit_hmm(y, 3, restarts=3)
    return m


def test_naming_uses_learned_parameters():
    names = hm.name_states(np.array([-0.2, 0.1, 0.0]), np.array([1.0, 0.4, 9.0]))
    assert names == {1: "Bull", 0: "Bear", 2: "High-Volatility"}


def test_fitted_hmm_recovers_volatility_states(fitted):
    p = hm.params(fitted)
    sds = np.sort(np.sqrt(p["variances"]))
    assert sds[-1] > 2.0 and sds[0] < 0.8
    assert np.allclose(p["A"].sum(1), 1)


def test_our_sum_product_matches_hmmlearn(fitted, regime_data):
    y, _ = regime_data
    p = hm.params(fitted)
    out = sp.sum_product(p["pi"], p["A"], hm.log_emissions(fitted, y))
    assert out["loglik"] == pytest.approx(fitted.score(y.reshape(-1, 1)), rel=1e-9)
    assert np.abs(out["gamma"] - fitted.predict_proba(y.reshape(-1, 1))).max() < 1e-8


def test_our_viterbi_matches_hmmlearn(fitted, regime_data):
    y, _ = regime_data
    p = hm.params(fitted)
    path, _ = sp.viterbi(p["pi"], p["A"], hm.log_emissions(fitted, y))
    assert (path == fitted.predict(y.reshape(-1, 1))).mean() == 1.0


def test_decoded_states_track_truth(fitted, regime_data):
    y, s = regime_data
    p = hm.params(fitted)
    path, _ = sp.viterbi(p["pi"], p["A"], hm.log_emissions(fitted, y))
    from sklearn.metrics import adjusted_rand_score
    assert adjusted_rand_score(s, path) > 0.4
