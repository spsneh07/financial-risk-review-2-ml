import numpy as np
import pytest
from scipy.spatial.distance import mahalanobis

from src import distance_metrics as dm


@pytest.fixture
def X():
    rng = np.random.default_rng(0)
    return rng.standard_normal((12, 7))


@pytest.mark.parametrize("fn", [dm.manhattan_matrix, dm.euclidean_matrix])
def test_metric_matrices_valid(X, fn):
    D = fn(X)
    assert D.shape == (12, 12)
    assert all(dm.validate_distance_matrix(D).values())


def test_manhattan_hand_value():
    X = np.array([[0.0, 0.0], [1.0, -2.0]])
    assert dm.manhattan_matrix(X)[0, 1] == pytest.approx(3.0)


def test_cosine_scale_invariant_and_range(X):
    D, _ = dm.cosine_matrix(X)
    D2, _ = dm.cosine_matrix(X * 7.5)
    assert np.allclose(D, D2)
    assert (D >= 0).all() and (D <= 2).all()
    assert all(dm.validate_distance_matrix(D).values())


def test_cosine_flags_near_zero_vector(X):
    X = X.copy()
    X[3] = 1e-9
    D, flagged = dm.cosine_matrix(X)
    assert 3 in flagged
    assert np.isfinite(D).all()


def test_mahalanobis_matches_scipy_with_same_precision(X):
    D, info = dm.mahalanobis_matrix(X)
    VI, _ = dm.shrunk_precision(X)
    assert D[0, 5] == pytest.approx(mahalanobis(X[0], X[5], VI))
    assert 0 <= info["shrinkage"] <= 1
    assert info["cond_shrunk_cov"] <= info["cond_raw_cov"]
    assert all(dm.validate_distance_matrix(D).values())


def test_mahalanobis_handles_singular_covariance():
    rng = np.random.default_rng(1)
    X = rng.standard_normal((6, 7))          # n < p -> raw covariance singular
    D, info = dm.mahalanobis_matrix(X)
    assert info["rank_raw_cov"] < 7
    assert np.isfinite(D).all()
