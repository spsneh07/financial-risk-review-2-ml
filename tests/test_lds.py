import numpy as np
import pytest

from src import linear_dynamical_system as lds


def test_kalman_tracks_latent_random_walk():
    rng = np.random.default_rng(0)
    T, q, r = 500, 0.05, 1.0
    x = np.cumsum(rng.normal(0, np.sqrt(q), T))
    y = x + rng.normal(0, np.sqrt(r), T)
    m = lds.local_level(q, r, 0.0, 1.0)
    f = m.filter(y)
    xs, _ = m.smooth(f)
    rmse_obs = np.sqrt(np.mean((y - x) ** 2))
    rmse_filt = np.sqrt(np.mean((f["x_filt"][:, 0] - x) ** 2))
    rmse_smooth = np.sqrt(np.mean((xs[:, 0] - x) ** 2))
    assert rmse_smooth < rmse_filt < rmse_obs


def test_mle_recovers_noise_ratio():
    rng = np.random.default_rng(1)
    T, q, r = 2000, 0.02, 1.0
    x = np.cumsum(rng.normal(0, np.sqrt(q), T))
    y = x + rng.normal(0, np.sqrt(r), T)
    _, info = lds.fit_local_level(y)
    assert info["r"] == pytest.approx(r, rel=0.15)
    assert 0.005 < info["q"] < 0.08


def test_loglik_matches_statsmodels_if_available():
    sm = pytest.importorskip("statsmodels.api")
    rng = np.random.default_rng(2)
    y = np.cumsum(rng.normal(0, 0.2, 300)) + rng.normal(0, 1, 300)
    q, r = 0.04, 1.0
    ours = lds.local_level(q, r, 0.0, 1e7).filter(y)["loglik_t"][1:].sum()
    mod = sm.tsa.UnobservedComponents(y, level="llevel", initialization="diffuse")
    ref = mod.loglike([r, q])
    assert ours == pytest.approx(ref, abs=0.5)


def test_logvol_model_recovers_persistence():
    rng = np.random.default_rng(3)
    T, m, phi, sw = 3000, 0.0, 0.97, 0.2
    h = np.zeros(T)
    for t in range(1, T):
        h[t] = m + phi * (h[t - 1] - m) + rng.normal(0, sw)
    r = np.exp(h / 2) * rng.standard_normal(T)
    _, info = lds.fit_logvol(r)
    assert 0.9 < info["phi"] < 0.995


def test_filter_shapes_and_positive_variance():
    m = lds.ar1_logvol(0.0, 0.9, 0.1)
    f = m.filter(np.random.default_rng(4).standard_normal(50))
    assert f["x_filt"].shape == (50, 1)
    assert (f["P_filt"][:, 0, 0] > 0).all()
