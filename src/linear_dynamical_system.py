"""Linear Dynamical System (linear-Gaussian state-space model) with a NumPy Kalman filter,
Rauch-Tung-Striebel smoother and maximum-likelihood parameter fitting.

General model (state x_t in R^n, observation y_t in R^m):
    x_t = F x_{t-1} + c + w_t,     w_t ~ N(0, Q)
    y_t = H x_t     + d + v_t,     v_t ~ N(0, R)

Kalman filter (predict / update):
    x_{t|t-1} = F x_{t-1|t-1} + c            P_{t|t-1} = F P F^T + Q
    S_t = H P_{t|t-1} H^T + R                K_t = P_{t|t-1} H^T S_t^{-1}
    x_{t|t} = x_{t|t-1} + K_t (y_t - H x_{t|t-1} - d)
    P_{t|t} = (I - K_t H) P_{t|t-1}
    log p(y_t | y_{1:t-1}) = log N(y_t; H x_{t|t-1} + d, S_t)   (prediction-error decomposition)

Two concrete models are used:
  * LDS-Trend : latent continuous *drift* of returns follows a random walk (local-level model)
                  mu_t = mu_{t-1} + w_t ;  r_t = mu_t + v_t
  * LDS-Vol   : latent continuous *log-variance* h_t follows a mean-reverting AR(1); the
                observation is log(r_t^2) (Harvey-Ruiz-Shephard quasi-likelihood linearisation
                of a stochastic-volatility model):
                  h_t = m + phi (h_{t-1} - m) + w_t ;  log(r_t^2 + c) = h_t - 1.2704 + v_t,
                  Var(v_t) = pi^2/2.  (E[log chi2_1] = -1.2704, Var = pi^2/2)
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import minimize

LOG_CHI2_MEAN = -1.2704
LOG_CHI2_VAR = np.pi ** 2 / 2


@dataclass
class LDS:
    F: np.ndarray
    H: np.ndarray
    Q: np.ndarray
    R: np.ndarray
    c: np.ndarray
    d: np.ndarray
    x0: np.ndarray
    P0: np.ndarray

    # -------------------------------------------------------------- filter
    def filter(self, y):
        y = np.asarray(y, dtype=float).reshape(len(y), -1)
        if len(self.x0) == 1 and y.shape[1] == 1:
            return self._filter_scalar(y)
        T, n = len(y), len(self.x0)
        xp = np.zeros((T, n)); Pp = np.zeros((T, n, n))
        xf = np.zeros((T, n)); Pf = np.zeros((T, n, n))
        y_pred = np.zeros_like(y); S_all = np.zeros((T, y.shape[1], y.shape[1]))
        ll = np.zeros(T)
        x, P = self.x0.copy(), self.P0.copy()
        I = np.eye(n)
        for t in range(T):
            x_pred = self.F @ x + self.c
            P_pred = self.F @ P @ self.F.T + self.Q
            yhat = self.H @ x_pred + self.d
            S = self.H @ P_pred @ self.H.T + self.R
            Sinv = np.linalg.inv(S)
            K = P_pred @ self.H.T @ Sinv
            e = y[t] - yhat
            x = x_pred + K @ e
            P = (I - K @ self.H) @ P_pred
            P = (P + P.T) / 2
            sign, logdet = np.linalg.slogdet(2 * np.pi * S)
            ll[t] = -0.5 * (logdet + e @ Sinv @ e)
            xp[t], Pp[t], xf[t], Pf[t] = x_pred, P_pred, x, P
            y_pred[t], S_all[t] = yhat, S
        return {"x_pred": xp, "P_pred": Pp, "x_filt": xf, "P_filt": Pf,
                "y_pred": y_pred, "S": S_all, "loglik_t": ll, "loglik": float(ll.sum())}

    def _filter_scalar(self, y):
        """Same equations as filter(), with Python floats (about 20x faster for 1-D models)."""
        F, H, Q, R = float(self.F[0, 0]), float(self.H[0, 0]), float(self.Q[0, 0]), float(self.R[0, 0])
        c, d = float(self.c[0]), float(self.d[0])
        x, P = float(self.x0[0]), float(self.P0[0, 0])
        T = len(y)
        yv = y[:, 0]
        xp = np.empty(T); Pp = np.empty(T); xf = np.empty(T); Pf = np.empty(T)
        yp = np.empty(T); S_all = np.empty(T); ll = np.empty(T)
        log2pi = np.log(2 * np.pi)
        for t in range(T):
            x_pred = F * x + c
            P_pred = F * P * F + Q
            yhat = H * x_pred + d
            S = H * P_pred * H + R
            K = P_pred * H / S
            e = yv[t] - yhat
            x = x_pred + K * e
            P = (1.0 - K * H) * P_pred
            ll[t] = -0.5 * (log2pi + np.log(S) + e * e / S)
            xp[t], Pp[t], xf[t], Pf[t], yp[t], S_all[t] = x_pred, P_pred, x, P, yhat, S
        return {"x_pred": xp[:, None], "P_pred": Pp[:, None, None], "x_filt": xf[:, None],
                "P_filt": Pf[:, None, None], "y_pred": yp[:, None], "S": S_all[:, None, None],
                "loglik_t": ll, "loglik": float(ll.sum())}

    # -------------------------------------------------------------- RTS smoother
    def smooth(self, filt):
        xf, Pf, xp, Pp = filt["x_filt"], filt["P_filt"], filt["x_pred"], filt["P_pred"]
        T = len(xf)
        xs, Ps = xf.copy(), Pf.copy()
        for t in range(T - 2, -1, -1):
            J = Pf[t] @ self.F.T @ np.linalg.inv(Pp[t + 1])
            xs[t] = xf[t] + J @ (xs[t + 1] - xp[t + 1])
            Ps[t] = Pf[t] + J @ (Ps[t + 1] - Pp[t + 1]) @ J.T
        return xs, Ps


def _m(a):
    return np.atleast_2d(np.asarray(a, dtype=float))


# ------------------------------------------------------------------ LDS-Trend (local level)
def local_level(q, r, x0, p0):
    return LDS(F=_m(1.0), H=_m(1.0), Q=_m(q), R=_m(r), c=np.zeros(1), d=np.zeros(1),
               x0=np.array([x0], float), P0=_m(p0))


def fit_local_level(y_train):
    """MLE of (q, r) by L-BFGS on log-parameters; x0 = train mean, P0 = train variance."""
    y = np.asarray(y_train, float)
    x0, p0 = y.mean(), y.var()

    def nll(theta):
        q, r = np.exp(theta)
        return -local_level(q, r, x0, p0).filter(y)["loglik"]

    best = None
    for q0 in (1e-6, 1e-4, 1e-2):
        res = minimize(nll, x0=np.log([q0, y.var()]), method="L-BFGS-B",
                       bounds=[(np.log(1e-10), np.log(10.0)), (np.log(1e-4), np.log(100.0))])
        if best is None or res.fun < best.fun:
            best = res
    q, r = np.exp(best.x)
    return local_level(q, r, x0, p0), {"q": float(q), "r": float(r),
                                       "signal_to_noise_q_over_r": float(q / r),
                                       "train_loglik": float(-best.fun)}


# ------------------------------------------------------------------ LDS-Vol (log-variance AR(1))
def log_sq_obs(r, c=1e-3):
    return np.log(np.asarray(r, float) ** 2 + c)


def ar1_logvol(m, phi, sw2, h0=None, p0=None):
    h0 = m if h0 is None else h0
    p0 = sw2 / max(1 - phi ** 2, 1e-6) if p0 is None else p0
    return LDS(F=_m(phi), H=_m(1.0), Q=_m(sw2), R=_m(LOG_CHI2_VAR),
               c=np.array([(1 - phi) * m]), d=np.array([LOG_CHI2_MEAN]),
               x0=np.array([h0], float), P0=_m(p0))


def fit_logvol(r_train, c=1e-3):
    z = log_sq_obs(r_train, c)

    def nll(theta):
        m, a, ls = theta
        phi = np.tanh(a)
        return -ar1_logvol(m, phi, np.exp(ls)).filter(z)["loglik"]

    res = minimize(nll, x0=[z.mean() - LOG_CHI2_MEAN, np.arctanh(0.95), np.log(0.05)],
                   method="L-BFGS-B",
                   bounds=[(-10, 10), (np.arctanh(0.0), np.arctanh(0.999)), (np.log(1e-5), np.log(5))])
    m, a, ls = res.x
    phi, sw2 = float(np.tanh(a)), float(np.exp(ls))
    return ar1_logvol(m, phi, sw2), {"m": float(m), "phi": phi, "sigma_w2": sw2,
                                     "half_life_days": float(np.log(0.5) / np.log(phi)),
                                     "train_quasi_loglik": float(-res.fun)}


def logvol_predictive_loglik(model: LDS, r, mu, c=1e-3):
    """Plug-in one-step predictive density for the *returns*:
    r_t | past ~ N(mu, exp(h_{t|t-1} + P_{t|t-1}/2)) (log-normal mean of sigma^2).
    An approximation (the QML model is not an exact likelihood for r_t) -- reported as such."""
    f = model.filter(log_sq_obs(r, c))
    h, P = f["x_pred"][:, 0], f["P_pred"][:, 0, 0]
    s2 = np.exp(h + P / 2)
    r = np.asarray(r, float)
    return -0.5 * (np.log(2 * np.pi * s2) + (r - mu) ** 2 / s2), np.sqrt(s2)
