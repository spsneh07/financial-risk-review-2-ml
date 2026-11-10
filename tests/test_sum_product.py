import numpy as np
import pytest

from src import sum_product as sp


def test_toy_matches_brute_force_enumeration():
    pi, A, B = sp.toy_example()
    out = sp.sum_product(pi, A, np.log(B))
    marg, p_y, best = sp.brute_force(pi, A, B)
    assert np.exp(out["loglik"]) == pytest.approx(p_y, rel=1e-12)
    assert np.allclose(out["gamma"], marg, atol=1e-12)
    path, _ = sp.viterbi(pi, A, np.log(B))
    assert path.tolist() == best.tolist()


def test_toy_hand_computed_forward():
    # alpha_1 = pi*b(y1) = [0.48, 0.12]
    # alpha_2 = [(0.48*0.7+0.12*0.4)*0.2, (0.48*0.3+0.12*0.6)*0.7] = [0.0768, 0.1512]
    # alpha_3 = [(0.0768*0.7+0.1512*0.4)*0.2, (0.0768*0.3+0.1512*0.6)*0.7] = [0.022848, 0.079632]
    pi, A, B = sp.toy_example()
    la, ll = sp.forward(np.log(pi), np.log(A), np.log(B))
    assert np.allclose(np.exp(la), [[0.48, 0.12], [0.0768, 0.1512], [0.022848, 0.079632]])
    assert np.exp(ll) == pytest.approx(0.10248)


def test_posteriors_normalised_and_xi_consistent():
    rng = np.random.default_rng(0)
    K, T = 3, 200
    A = rng.dirichlet(np.ones(K) * 5, K)
    pi = np.ones(K) / K
    logB = sp.gaussian_log_emissions(rng.standard_normal(T), [-1, 0, 1], [1, 0.5, 2])
    out = sp.sum_product(pi, A, logB)
    assert np.allclose(out["gamma"].sum(1), 1)
    assert np.allclose(out["xi"].sum((1, 2)), 1)
    assert np.allclose(out["xi"].sum(2), out["gamma"][:-1], atol=1e-10)


def test_no_underflow_long_sequence():
    rng = np.random.default_rng(1)
    T = 20000
    logB = sp.gaussian_log_emissions(rng.standard_normal(T) * 3, [0, 0], [1, 9])
    out = sp.sum_product([0.5, 0.5], [[0.99, 0.01], [0.01, 0.99]], logB)
    assert np.isfinite(out["loglik"]) and np.isfinite(out["gamma"]).all()


def test_predictive_sums_to_loglik():
    rng = np.random.default_rng(2)
    logB = sp.gaussian_log_emissions(rng.standard_normal(100), [0, 1], [1, 2])
    pi, A = [0.3, 0.7], [[0.9, 0.1], [0.2, 0.8]]
    pred = sp.one_step_predictive_loglik(pi, A, logB)
    assert pred.sum() == pytest.approx(sp.sum_product(pi, A, logB)["loglik"])


def test_viterbi_differs_from_marginal_argmax_conceptually():
    # Viterbi maximises the joint path probability; brute force confirms optimality.
    rng = np.random.default_rng(3)
    pi = np.array([0.5, 0.3, 0.2])
    A = rng.dirichlet(np.ones(3), 3)
    B = rng.uniform(0.05, 1, (6, 3))
    path, logp = sp.viterbi(pi, A, np.log(B))
    _, _, best = sp.brute_force(pi, A, B)
    assert path.tolist() == best.tolist()
