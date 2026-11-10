"""Exact inference in a discrete-state HMM, written out explicitly in NumPy (log space).

Notation: K hidden states, T observations.
  pi_i      = p(z_1 = i)                        initial distribution
  A_ij      = p(z_t = j | z_{t-1} = i)          transition matrix (rows sum to 1)
  b_j(y_t)  = p(y_t | z_t = j)                  emission likelihood

Sum-Product (forward-backward) -- computes MARGINAL posteriors by SUMMING over paths
  alpha_t(j) = b_j(y_t) * sum_i alpha_{t-1}(i) A_ij           alpha_1(j) = pi_j b_j(y_1)
  beta_t(i)  = sum_j A_ij b_j(y_{t+1}) beta_{t+1}(j)          beta_T(i)  = 1
  gamma_t(i) = p(z_t = i | y_{1:T}) = alpha_t(i) beta_t(i) / p(y_{1:T})
  xi_t(i,j)  = alpha_t(i) A_ij b_j(y_{t+1}) beta_{t+1}(j) / p(y_{1:T})
  p(y_{1:T}) = sum_j alpha_T(j)

Max-Product (Viterbi) -- finds the single most probable PATH by MAXIMISING over paths
  delta_t(j) = b_j(y_t) * max_i delta_{t-1}(i) A_ij, then back-track the argmax pointers.

All recursions run on logs with log-sum-exp, so they never underflow even for T ~ 3000.
"""
from __future__ import annotations

import itertools

import numpy as np
from scipy.special import logsumexp


def gaussian_log_emissions(y: np.ndarray, means: np.ndarray, variances: np.ndarray) -> np.ndarray:
    """log N(y_t; mu_j, s2_j) for univariate y. Returns (T, K)."""
    y = np.asarray(y, dtype=float).reshape(-1, 1)
    means = np.asarray(means, dtype=float).reshape(1, -1)
    variances = np.asarray(variances, dtype=float).reshape(1, -1)
    return -0.5 * (np.log(2 * np.pi * variances) + (y - means) ** 2 / variances)


def forward(log_pi, log_A, log_B):
    """log alpha (T, K) and total log-likelihood log p(y_{1:T})."""
    T, K = log_B.shape
    log_alpha = np.empty((T, K))
    log_alpha[0] = log_pi + log_B[0]
    for t in range(1, T):
        # log sum_i exp(log_alpha[t-1, i] + log_A[i, j])  for every j
        log_alpha[t] = logsumexp(log_alpha[t - 1][:, None] + log_A, axis=0) + log_B[t]
    return log_alpha, float(logsumexp(log_alpha[-1]))


def backward(log_A, log_B):
    T, K = log_B.shape
    log_beta = np.zeros((T, K))
    for t in range(T - 2, -1, -1):
        log_beta[t] = logsumexp(log_A + (log_B[t + 1] + log_beta[t + 1])[None, :], axis=1)
    return log_beta


def sum_product(pi, A, log_B):
    """Forward-backward. Returns dict with gamma (T,K), xi (T-1,K,K), loglik, log_alpha."""
    log_pi = np.log(np.asarray(pi, dtype=float) + 1e-300)
    log_A = np.log(np.asarray(A, dtype=float) + 1e-300)
    log_alpha, loglik = forward(log_pi, log_A, log_B)
    log_beta = backward(log_A, log_B)
    log_gamma = log_alpha + log_beta - loglik
    gamma = np.exp(log_gamma)
    gamma /= gamma.sum(axis=1, keepdims=True)          # remove round-off only
    log_xi = (log_alpha[:-1, :, None] + log_A[None, :, :]
              + (log_B[1:] + log_beta[1:])[:, None, :] - loglik)
    xi = np.exp(log_xi)
    return {"gamma": gamma, "xi": xi, "loglik": loglik, "log_alpha": log_alpha,
            "log_beta": log_beta}


def filtered_probs(log_alpha):
    """p(z_t | y_{1:t}) -- the causal (real-time) version of gamma."""
    return np.exp(log_alpha - logsumexp(log_alpha, axis=1, keepdims=True))


def one_step_predictive_loglik(pi, A, log_B):
    """log p(y_t | y_{1:t-1}) for every t (t=1 uses pi). Sums to the total log-likelihood.
    Used for an honest out-of-sample comparison with the Kalman filter."""
    log_pi = np.log(np.asarray(pi) + 1e-300)
    log_A = np.log(np.asarray(A) + 1e-300)
    log_alpha, _ = forward(log_pi, log_A, log_B)
    out = np.empty(len(log_B))
    out[0] = logsumexp(log_alpha[0])
    for t in range(1, len(log_B)):
        out[t] = logsumexp(log_alpha[t]) - logsumexp(log_alpha[t - 1])
    return out


def viterbi(pi, A, log_B):
    """Most probable state sequence argmax_z p(z_{1:T} | y_{1:T}) and its log joint prob."""
    log_pi = np.log(np.asarray(pi, dtype=float) + 1e-300)
    log_A = np.log(np.asarray(A, dtype=float) + 1e-300)
    T, K = log_B.shape
    delta = np.empty((T, K))
    psi = np.zeros((T, K), dtype=int)
    delta[0] = log_pi + log_B[0]
    for t in range(1, T):
        scores = delta[t - 1][:, None] + log_A          # (from i, to j)
        psi[t] = np.argmax(scores, axis=0)
        delta[t] = scores[psi[t], np.arange(K)] + log_B[t]
    path = np.empty(T, dtype=int)
    path[-1] = int(np.argmax(delta[-1]))
    for t in range(T - 2, -1, -1):
        path[t] = psi[t + 1, path[t + 1]]
    return path, float(delta[-1].max())


# ------------------------------------------------------------------ verification helpers
def brute_force(pi, A, B_obs):
    """Enumerate all K^T paths (tiny problems only).

    B_obs is the (T, K) matrix of emission *probabilities* b_j(y_t).
    Returns exact marginals p(z_t=i|y), p(y) and the best path.
    """
    T, K = B_obs.shape
    marg = np.zeros((T, K))
    total, best, best_p = 0.0, None, -1.0
    for path in itertools.product(range(K), repeat=T):
        p = pi[path[0]] * B_obs[0, path[0]]
        for t in range(1, T):
            p *= A[path[t - 1], path[t]] * B_obs[t, path[t]]
        total += p
        for t, s in enumerate(path):
            marg[t, s] += p
        if p > best_p:
            best, best_p = path, p
    return marg / total, total, np.array(best)


def toy_example():
    """Hand-checkable 2-state, 3-step HMM (weather-style) used in tests and the demo."""
    pi = np.array([0.6, 0.4])
    A = np.array([[0.7, 0.3],
                  [0.4, 0.6]])
    # emission probabilities for the observed sequence y = (up, down, down)
    # state 0 = "calm": p(up)=0.8 ; state 1 = "stressed": p(up)=0.3
    B_obs = np.array([[0.8, 0.3],
                      [0.2, 0.7],
                      [0.2, 0.7]])
    return pi, A, B_obs
