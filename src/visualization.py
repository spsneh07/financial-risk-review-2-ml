"""All figures. Every function takes computed results and saves a PNG (150 dpi)."""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")  # headless / no GUI needed
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import seaborn as sns  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402
from scipy.cluster.hierarchy import dendrogram  # noqa: E402

# validated categorical slots (light mode) + chart ink
BLUE, ORANGE, AQUA, YELLOW, MAGENTA, GREEN, VIOLET, RED = (
    "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948")
CAT = [BLUE, ORANGE, AQUA, YELLOW, MAGENTA, GREEN, VIOLET, RED]
INK, INK2, MUTED, GRID, SURFACE = "#0b0b0b", "#52514e", "#8a8984", "#e6e5e0", "#fcfcfb"
REGIME_COLORS = {"Bull": AQUA, "Bear": ORANGE, "High-Volatility": BLUE}
SEQ = LinearSegmentedColormap.from_list("seq_blue", ["#cde2fb", "#6da7ec", "#256abf", "#0d366b"])
DIV = LinearSegmentedColormap.from_list("div", ["#256abf", "#86b6ef", "#f0efec", "#f0a3a3", "#c23636"])


def setup_style():
    plt.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "axes.edgecolor": MUTED, "axes.labelcolor": INK2, "axes.titlecolor": INK,
        "axes.titleweight": "bold", "axes.titlesize": 12, "axes.labelsize": 10,
        "xtick.color": INK2, "ytick.color": INK2, "xtick.labelsize": 9, "ytick.labelsize": 9,
        "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8,
        "axes.spines.top": False, "axes.spines.right": False,
        "legend.frameon": False, "legend.fontsize": 9, "font.size": 10,
        "lines.linewidth": 1.6, "figure.dpi": 100, "axes.axisbelow": True,
    })


def _save(fig, path, note=None):
    if note:
        fig.text(0.995, 0.005, note, ha="right", va="bottom", fontsize=7, color=MUTED)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


# ====================================================================== PART A
def plot_return_distributions(returns: pd.DataFrame, path, note=None):
    order = returns.std().sort_values().index
    long = (returns[order] * 100).melt(var_name="Stock", value_name="Daily log return (%)")
    fig, ax = plt.subplots(figsize=(11, 4.6))
    sns.boxplot(data=long, x="Stock", y="Daily log return (%)", ax=ax, color="#9ec5f4",
                fliersize=1.5, linewidth=1, flierprops={"markerfacecolor": MUTED,
                                                         "markeredgecolor": MUTED})
    ax.set_title("Daily return distributions (sorted by volatility, low to high)")
    ax.set_xlabel("")
    ax.tick_params(axis="x", rotation=35)
    return _save(fig, path, note)


def plot_feature_heatmap(features: pd.DataFrame, X_std: np.ndarray, path, note=None):
    z = pd.DataFrame(X_std, index=features.index, columns=features.columns)
    fig, ax = plt.subplots(figsize=(9.5, 6))
    sns.heatmap(z, cmap=DIV, center=0, vmin=-2.5, vmax=2.5, annot=True, fmt=".1f",
                linewidths=2, linecolor=SURFACE, cbar_kws={"label": "z-score"}, ax=ax,
                annot_kws={"fontsize": 8})
    ax.set_title("Standardised risk-feature matrix (12 assets x 7 features)")
    ax.tick_params(axis="x", rotation=30)
    ax.grid(False)
    return _save(fig, path, note)


def plot_model_selection(km_tab, gmm_tab, path, k_final=None, note=None):
    fig, axes = plt.subplots(1, 3, figsize=(13, 3.8))
    axes[0].plot(km_tab["k"], km_tab["inertia"], "o-", color=BLUE, ms=7)
    axes[0].set(title="K-means elbow", xlabel="k", ylabel="Inertia (within-cluster SSE)")
    axes[1].plot(km_tab["k"], km_tab["silhouette"], "o-", color=BLUE, ms=7, label="K-means")
    g = gmm_tab[gmm_tab["covariance"] == "spherical"].dropna(subset=["silhouette"])
    axes[1].plot(g["k"], g["silhouette"], "s--", color=ORANGE, ms=7, label="GMM (spherical)")
    axes[1].set(title="Silhouette vs k", xlabel="k", ylabel="Silhouette (higher = better)")
    axes[1].legend()
    for cov, c, mk in [("spherical", ORANGE, "s-"), ("diag", AQUA, "^-")]:
        t = gmm_tab[gmm_tab["covariance"] == cov]
        axes[2].plot(t["k"], t["bic"], mk, color=c, ms=7, label=f"BIC {cov}")
    axes[2].set(title="GMM BIC (lower = better)", xlabel="k", ylabel="BIC")
    axes[2].legend()
    if k_final:
        for a in axes:
            a.axvline(k_final, color=MUTED, ls=":", lw=1.2)
    return _save(fig, path, note)


def plot_pca_variance(var_tab, path, note=None):
    fig, ax = plt.subplots(figsize=(6.5, 3.8))
    x = np.arange(1, len(var_tab) + 1)
    ax.bar(x, var_tab["explained_variance_ratio"] * 100, color=BLUE, width=0.6, label="Per component")
    ax.plot(x, var_tab["cumulative"] * 100, "o-", color=ORANGE, ms=7, label="Cumulative")
    ax.axhline(80, color=MUTED, ls=":", lw=1.2)
    ax.text(len(x) + 0.3, 80, "80%", va="center", color=INK2, fontsize=8)
    for xi, c in zip(x, var_tab["cumulative"] * 100):
        ax.text(xi, c + 3, f"{c:.0f}%", ha="center", fontsize=8, color=INK2)
    ax.set(title="PCA explained variance", xlabel="Principal component",
           ylabel="Variance explained (%)", ylim=(0, 110), xticks=x)
    ax.legend(loc="center right")
    return _save(fig, path, note)


def plot_pca_clusters(Z2, names, label_sets: dict, path, evr=None, note=None):
    fig, axes = plt.subplots(1, len(label_sets), figsize=(5 * len(label_sets), 4.4),
                             sharex=True, sharey=True)
    for ax, (title, labels) in zip(np.atleast_1d(axes), label_sets.items()):
        for k in np.unique(labels):
            m = labels == k
            ax.scatter(Z2[m, 0], Z2[m, 1], s=90, color=CAT[k], edgecolor=SURFACE, lw=2,
                       label=f"Cluster {k}", zorder=3)
        for i, nm in enumerate(names):
            ax.annotate(nm, Z2[i], xytext=(5, 4), textcoords="offset points", fontsize=7.5,
                        color=INK2)
        ax.set_title(title)
        xl = "PC1" + (f" ({evr[0] * 100:.0f}%)" if evr is not None else "")
        yl = "PC2" + (f" ({evr[1] * 100:.0f}%)" if evr is not None else "")
        ax.set(xlabel=xl, ylabel=yl)
        ax.legend(loc="best", fontsize=8)
    fig.suptitle("Assets in PC1-PC2 space, coloured by cluster (0 = lowest mean volatility)",
                 fontsize=11, color=INK2)
    return _save(fig, path, note)


def plot_dendrograms(Z_ward, Z_avg, names, path, k=None, note=None):
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.4))
    for ax, Z, t in [(axes[0], Z_ward, "Ward linkage (Euclidean)"),
                     (axes[1], Z_avg, "Average linkage (Euclidean)")]:
        thr = Z[-(k - 1), 2] - 1e-9 if k else None
        dendrogram(Z, labels=list(names), ax=ax, leaf_rotation=55, color_threshold=thr,
                   above_threshold_color=MUTED)
        if thr is not None:
            ax.axhline(thr, color=RED, ls="--", lw=1)
        ax.set_title(t)
        ax.set_ylabel("Merge distance")
        ax.grid(False)
    return _save(fig, path, note)


def plot_metric_comparison(metric_tab: pd.DataFrame, assign: pd.DataFrame, ari_mat: pd.DataFrame,
                           path, note=None):
    fig = plt.figure(figsize=(14, 4.6))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.0, 1.25, 1.0])
    ax0 = fig.add_subplot(gs[0])
    cols = [MUTED if m == "Euclidean" else BLUE for m in metric_tab["metric"]]
    ax0.barh(metric_tab["metric"], metric_tab["silhouette_precomputed"], color=cols, height=0.55)
    for i, v in enumerate(metric_tab["silhouette_precomputed"]):
        ax0.text(v + 0.01, i, f"{v:.2f}", va="center", fontsize=9, color=INK)
    ax0.set(title="Silhouette in each metric's own space", xlabel="Silhouette (precomputed D)")
    ax0.invert_yaxis()
    ax0.set_xlim(0, max(metric_tab["silhouette_precomputed"]) * 1.25)
    ax1 = fig.add_subplot(gs[1])
    k = int(assign.values.max()) + 1
    cmap = matplotlib.colors.ListedColormap(CAT[:k])
    sns.heatmap(assign.T, cmap=cmap, cbar=False, linewidths=2, linecolor=SURFACE, ax=ax1,
                annot=True, fmt="d", annot_kws={"fontsize": 8, "color": "white"})
    ax1.set_title("Cluster assignment per metric")
    ax1.tick_params(axis="x", rotation=55, labelsize=8)
    ax1.grid(False)
    ax2 = fig.add_subplot(gs[2])
    sns.heatmap(ari_mat, cmap=SEQ, vmin=0, vmax=1, annot=True, fmt=".2f", linewidths=2,
                linecolor=SURFACE, ax=ax2, cbar_kws={"label": "ARI"}, annot_kws={"fontsize": 9})
    ax2.set_title("Agreement between metrics (ARI)")
    ax2.grid(False)
    return _save(fig, path, note)


def plot_stability(boot_raw: pd.DataFrame, seed_tab: pd.DataFrame, path, note=None):
    fig, axes = plt.subplots(1, 2, figsize=(14, 4.6), gridspec_kw={"width_ratios": [1.5, 1]})
    order = boot_raw.groupby("method")["ARI"].mean().sort_values(ascending=False).index
    sns.boxplot(data=boot_raw, y="method", x="ARI", order=order, ax=axes[0], color="#9ec5f4",
                fliersize=2, linewidth=1)
    means = boot_raw.groupby("method")["ARI"].mean()
    axes[0].scatter(means[order], range(len(order)), color=ORANGE, zorder=4, s=30, label="mean")
    axes[0].set(title="Bootstrap stability (block bootstrap of trading days)",
                xlabel="ARI vs full-sample partition", ylabel="")
    axes[0].axvline(0, color=MUTED, lw=1)
    axes[0].legend(loc="lower right")
    t = seed_tab.copy()
    axes[1].barh(t["method"], t["mean_ARI"], xerr=t["std_ARI"], color=BLUE, height=0.55,
                 error_kw={"ecolor": INK2, "lw": 1})
    for i, (v, sdv) in enumerate(zip(t["mean_ARI"], t["std_ARI"])):
        axes[1].text(min(v + sdv, 1.0) + 0.03, i, f"{v:.2f}", va="center", fontsize=9,
                     weight="bold", color=INK)
    axes[1].set(title="Initialisation stability (pairwise ARI across seeds)",
                xlabel="Mean pairwise ARI (bar = +/- 1 sd)", xlim=(0, 1.3))
    axes[1].invert_yaxis()
    return _save(fig, path, note)


def plot_table(df: pd.DataFrame, path, title, col_width=1.25, fontsize=9, note=None,
               row_colors=None):
    nrows, ncols = df.shape
    fig, ax = plt.subplots(figsize=(max(6, col_width * (ncols + 1)), 0.42 * (nrows + 2)))
    ax.axis("off")
    tbl = ax.table(cellText=df.values, colLabels=df.columns, rowLabels=df.index,
                   loc="center", cellLoc="center")
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(fontsize)
    tbl.scale(1, 1.35)
    for (r, c), cell in tbl.get_celld().items():
        cell.set_edgecolor(GRID)
        if r == 0:
            cell.set_facecolor("#256abf"); cell.set_text_props(color="white", weight="bold")
        elif row_colors is not None and c == -1:
            cell.set_facecolor(row_colors[r - 1]); cell.set_text_props(color="white", weight="bold")
        elif r % 2 == 0:
            cell.set_facecolor("#f3f2ee")
    ax.set_title(title, fontsize=11, weight="bold", color=INK)
    return _save(fig, path, note)


# ====================================================================== PART B
def _shade_regimes(ax, dates, labels, names, alpha=0.18):
    labels = np.asarray(labels)
    change = np.flatnonzero(np.diff(labels)) + 1
    starts = np.r_[0, change]
    ends = np.r_[change, len(labels)]
    for s, e in zip(starts, ends):
        nm = names[int(labels[s])]
        ax.axvspan(dates[s], dates[min(e, len(dates) - 1)], color=REGIME_COLORS[nm],
                   alpha=alpha, lw=0)


def _regime_legend(ax, names):
    from matplotlib.patches import Patch
    handles = [Patch(color=REGIME_COLORS[n], alpha=0.5, label=n)
               for n in ["Bull", "Bear", "High-Volatility"] if n in names.values()]
    ax.legend(handles=handles, loc="upper left", ncol=3)


def plot_index_regimes(prices: pd.Series, dates, path_states, names, split_date, path,
                       title, note=None):
    fig, ax = plt.subplots(figsize=(12, 4.4))
    _shade_regimes(ax, dates, path_states, names)
    ax.plot(prices.index, prices.values, color=INK, lw=1.2)
    ax.axvline(pd.Timestamp(split_date), color=RED, ls="--", lw=1.2)
    ax.text(pd.Timestamp(split_date), ax.get_ylim()[1], "  test period", color=RED,
            va="top", fontsize=9)
    ax.set(title=title, ylabel="Index level", xlabel="")
    _regime_legend(ax, names)
    return _save(fig, path, note)


def plot_returns_vol(r: pd.Series, vol: pd.Series, path, note=None):
    fig, axes = plt.subplots(2, 1, figsize=(12, 5), sharex=True)
    axes[0].plot(r.index, r.values, color=BLUE, lw=0.6)
    axes[0].set(title="NIFTY 50 daily log returns (%)", ylabel="%")
    axes[1].plot(vol.index, vol.values, color=ORANGE, lw=1.2)
    axes[1].set(title="21-day rolling volatility (annualised %)", ylabel="%")
    return _save(fig, path, note)


def plot_posteriors(dates, gamma, names, path, split_date=None, note=None):
    order = sorted(range(gamma.shape[1]), key=lambda s: ["Bull", "Bear", "High-Volatility"].index(names[s]))
    fig, ax = plt.subplots(figsize=(12, 3.8))
    ax.stackplot(dates, *[gamma[:, s] for s in order], colors=[REGIME_COLORS[names[s]] for s in order],
                 labels=[names[s] for s in order], alpha=0.9, lw=0)
    if split_date is not None:
        ax.axvline(pd.Timestamp(split_date), color=INK, ls="--", lw=1)
    ax.set(title="Smoothed posterior  p(z_t = k | y_1:T)  - retrospective, uses all data (stacked, sums to 1)",
           ylabel="Probability", ylim=(0, 1))
    ax.legend(loc="upper left", ncol=3, bbox_to_anchor=(0, -0.08))
    ax.grid(False)
    return _save(fig, path, note)


def plot_hmm_params(A, means, variances, names, path, note=None):
    order = sorted(range(len(means)), key=lambda s: ["Bull", "Bear", "High-Volatility"].index(names[s]))
    lab = [names[s] for s in order]
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.2), gridspec_kw={"width_ratios": [1, 1.3]})
    sns.heatmap(A[np.ix_(order, order)], annot=True, fmt=".3f", cmap=SEQ, vmin=0, vmax=1,
                xticklabels=lab, yticklabels=lab, ax=axes[0], linewidths=2, linecolor=SURFACE,
                cbar_kws={"label": "probability"})
    axes[0].set(title="Transition matrix  A_ij = p(z_t=j | z_t-1=i)", xlabel="to", ylabel="from")
    axes[0].grid(False)
    x = np.linspace(-6, 6, 600)
    for s in order:
        sd = np.sqrt(variances[s])
        pdf = np.exp(-0.5 * ((x - means[s]) / sd) ** 2) / (sd * np.sqrt(2 * np.pi))
        axes[1].plot(x, pdf, color=REGIME_COLORS[names[s]], lw=2,
                     label=f"{names[s]}: mu={means[s]:+.3f}%, sigma={sd:.2f}%")
    axes[1].set(title="Gaussian emission densities p(y_t | z_t)", xlabel="Daily return (%)",
                ylabel="Density")
    axes[1].legend(loc="upper left", fontsize=8)
    return _save(fig, path, note)


def plot_sp_vs_viterbi(dates, r, gamma, filt, vpath, names, window, path, note=None):
    d = pd.DatetimeIndex(dates)
    m = (d >= pd.Timestamp(window[0])) & (d <= pd.Timestamp(window[1]))
    hv = [s for s in names if names[s] == "High-Volatility"][0]
    fig, axes = plt.subplots(3, 1, figsize=(12, 6.4), sharex=True,
                             gridspec_kw={"height_ratios": [1.1, 1, 0.45]})
    axes[0].bar(d[m], np.asarray(r)[m], color=BLUE, width=1.0)
    axes[0].set(title=f"Daily returns (%)  {window[0]} to {window[1]}", ylabel="%")
    axes[1].plot(d[m], gamma[m, hv], color=BLUE, lw=2, label="Smoothed  p(z_t=HV | y_1:T)  (Sum-Product, retrospective)")
    axes[1].plot(d[m], filt[m, hv], color=ORANGE, lw=1.4, ls="--", label="Filtered  p(z_t=HV | y_1:t)  (forward only, real-time)")
    axes[1].set(title="Marginal probability of the High-Volatility regime", ylabel="Probability",
                ylim=(-0.03, 1.03))
    axes[1].legend(loc="center right", fontsize=8)
    v = np.asarray(vpath)[m]
    for s in names:
        axes[2].fill_between(d[m], 0, 1, where=(v == s), color=REGIME_COLORS[names[s]],
                             step="mid", lw=0, label=names[s])
    axes[2].set(title="Viterbi: most probable full-sequence state path (retrospective)", yticks=[])
    axes[2].legend(loc="upper left", ncol=3, fontsize=8, bbox_to_anchor=(0, -0.25))
    axes[2].grid(False)
    return _save(fig, path, note)


def plot_lds_comparison(dates, rolling_vol, hmm_sigma, lds_sigma, lds_trend, hmm_mean, split_date,
                        path, note=None):
    fig, axes = plt.subplots(2, 1, figsize=(12, 6.2), sharex=True)
    axes[0].plot(dates, rolling_vol, color=MUTED, lw=1, label="21-day realised vol (reference)")
    axes[0].plot(dates, hmm_sigma, color=ORANGE, lw=1.4, label="HMM: posterior mixture sigma_t from gamma_tk (discrete states)")
    axes[0].plot(dates, lds_sigma, color=BLUE, lw=1.6, label="LDS-Vol: RTS-smoothed exp(h_t/2) (continuous)")
    axes[0].set(title="Latent volatility (smoothed, retrospective): discrete HMM vs continuous LDS",
                ylabel="Daily sigma (%)")
    axes[0].legend(loc="upper right", fontsize=8)
    axes[1].plot(dates, hmm_mean, color=ORANGE, lw=1.2, label="HMM: sum_k gamma_tk * mu_k")
    axes[1].plot(dates, lds_trend, color=BLUE, lw=2, label="LDS-Trend: Kalman-smoothed drift mu_t")
    axes[1].axhline(0, color=MUTED, lw=1)
    axes[1].set(title="Latent expected daily return (smoothed, retrospective)", ylabel="%")
    axes[1].legend(loc="lower right", fontsize=8)
    for a in axes:
        a.axvline(pd.Timestamp(split_date), color=RED, ls="--", lw=1)
    return _save(fig, path, note)


def plot_predictive(tab: pd.DataFrame, path, note=None):
    """Gain in mean one-step predictive log-likelihood over the i.i.d. Gaussian baseline."""
    base = tab.loc[tab["model"].str.startswith("i.i.d."), "test_loglik_per_day"].iloc[0]
    t = tab.assign(gain=tab["test_loglik_per_day"] - base).sort_values("gain")
    fig, ax = plt.subplots(figsize=(9, 3.6))
    cols = [ORANGE if "HMM" in m else (BLUE if "LDS" in m else MUTED) for m in t["model"]]
    ax.barh(t["model"], t["gain"], color=cols, height=0.55)
    ax.axvline(0, color=INK2, lw=1)
    for i, (g, v) in enumerate(zip(t["gain"], t["test_loglik_per_day"])):
        ax.text(max(g, 0) + 0.003, i, f"{g:+.4f}  (abs {v:.4f})", va="center", fontsize=9)
    ax.set_xlim(min(t["gain"].min(), 0) - 0.01, t["gain"].max() * 1.6 + 0.01)
    ax.set(title="Test-period predictive log-likelihood gain vs i.i.d. Gaussian (nats/day, higher = better)",
           xlabel="mean log p(y_t | y_1:t-1) minus baseline")
    ax.title.set_fontsize(10.5)
    return _save(fig, path, note)
