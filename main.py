"""Financial Market Risk Profiling & Regime Detection -- end-to-end pipeline.

Run everything (uses cached data in data/raw if present):
    python main.py
Options:
    --quick            fewer bootstrap / restart iterations (fast live demo, ~30 s)
    --refresh-data     ignore cache, download again (yfinance -> eod2 GitHub -> synthetic)
    --source NAME      force one source: cache | yfinance | eod2 | synthetic
    --part A|B|all     run only Part A (clustering) or Part B (HMM / LDS)
"""
from __future__ import annotations

import argparse
import json
import logging
import time
import warnings

import numpy as np
import pandas as pd

import config
from src import clustering as cl
from src import data_loader as dl
from src import distance_metrics as dm
from src import evaluation as ev
from src import hmm_model as hm
from src import linear_dynamical_system as lds
from src import pca_analysis as pa
from src import risk_features as rf
from src import stability as st
from src import sum_product as sp
from src import visualization as viz

warnings.filterwarnings("ignore")
logging.getLogger("yfinance").setLevel(logging.CRITICAL)
pd.set_option("display.width", 160)
pd.set_option("display.max_columns", 20)
pd.set_option("display.precision", 4)


def banner(txt):
    print("\n" + "=" * 78 + f"\n  {txt}\n" + "=" * 78)


def jsonable(o):
    if isinstance(o, dict):
        return {str(k): jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [jsonable(v) for v in o]
    if isinstance(o, np.ndarray):
        return jsonable(o.tolist())
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    return o


# =============================================================================== PART A
def run_part_a(args, results):
    t0 = time.time()
    banner("PART A | Step 1  Load stock prices")
    prices, src = dl.load_stock_prices(prefer=args.source, refresh=args.refresh_data)
    note = f"Data: {src} | NSE daily close {prices.index.min():%Y-%m-%d} to {prices.index.max():%Y-%m-%d}"
    if "SYNTHETIC" in src:
        note = "SYNTHETIC DATA (simulated, NOT market data)"
    print(f"Source: {src}\nShape: {prices.shape}  ({prices.index.min():%Y-%m-%d} -> {prices.index.max():%Y-%m-%d})")
    returns = dl.log_returns(prices)

    banner("PART A | Step 2  Risk features")
    F = rf.compute_risk_features(returns, config.VAR_LEVEL)
    X, _ = rf.standardize(F)
    readable = rf.annualised_view(F)
    print(readable.round(2))
    F.to_csv(config.TAB_DIR / "risk_features_raw.csv")
    readable.round(3).to_csv(config.TAB_DIR / "risk_features_readable.csv")
    names = list(F.index)
    vol = F["volatility"].values

    banner("PART A | Step 3  Choose k: elbow, silhouette, GMM BIC")
    km_tab = cl.kmeans_sweep(X)
    gmm_tab = cl.gmm_sweep(X)
    k_sil = cl.choose_k(km_tab)
    gmm_cov, k_bic = cl.best_gmm(gmm_tab)
    K = config.N_CLUSTERS or k_bic
    print(km_tab.round(3).to_string(index=False))
    print(gmm_tab.round(3).to_string(index=False))
    print(f"\nBest K-means silhouette at k={k_sil}; lowest GMM BIC: {gmm_cov}, k={k_bic}.")
    if k_sil != K:
        print(f"=> We selected K={K} for the main risk-profile comparison based on the GMM BIC criterion. "
              f"K-means silhouette favors K={k_sil}, so the selection criteria do not fully agree. "
              f"{K} clusters were retained for the principal comparison to support the intended "
              "risk-profile interpretation.")
    else:
        print(f"=> Using K={K}: GMM BIC and K-means silhouette agree.")
    km_tab.to_csv(config.TAB_DIR / "kmeans_selection.csv", index=False)
    gmm_tab.to_csv(config.TAB_DIR / "gmm_selection.csv", index=False)

    banner("PART A | Step 4  K-means, GMM, Hierarchical clustering")
    hier_tab = cl.hierarchical_sweep(X, K)
    print("Hierarchical linkage comparison (Euclidean):\n", hier_tab.round(3).to_string(index=False))
    hier_tab.to_csv(config.TAB_DIR / "hierarchical_linkages.csv", index=False)
    labels = {
        "K-means": cl.relabel_by_risk(cl.kmeans_fit(X, K).labels_, vol),
        f"GMM ({gmm_cov})": cl.relabel_by_risk(cl.gmm_fit(X, K, gmm_cov).predict(X), vol),
        "Hierarchical (Ward)": cl.relabel_by_risk(cl.hierarchical_fit(X, K, "ward").labels_, vol),
    }
    assign = pd.DataFrame(labels, index=names)
    print("\nCluster assignments (0 = lowest-volatility cluster):\n", assign)
    assign.to_csv(config.TAB_DIR / "cluster_assignments.csv")
    algo_scores = pd.DataFrame({m: ev.euclidean_scores(X, l) for m, l in labels.items()}).T
    print("\nInternal validity in standardised 7-D feature space:\n", algo_scores.round(3))
    keys = list(labels)
    algo_ari = pd.DataFrame([[ev.ari(labels[a], labels[b]) for b in keys] for a in keys],
                            index=keys, columns=keys)
    print("\nAgreement between algorithms (ARI):\n", algo_ari.round(3))

    banner("PART A | Step 5  PCA and before/after evaluation")
    pca = pa.fit_pca(X)
    var_tab = pa.variance_table(pca)
    n_pc = pa.n_components_for(pca)
    Zp = pa.transform(pca, X, n_pc)
    Z2 = pa.transform(pca, X, 2)
    print(var_tab.round(3).to_string(index=False))
    print(f"Keeping {n_pc} PCs (>= {config.PCA_VARIANCE_TARGET:.0%} variance).")
    load = pa.loadings_table(pca, F.columns, n_pc)
    print("Loadings:\n", load.round(2))
    var_tab.to_csv(config.TAB_DIR / "pca_variance.csv", index=False)
    load.to_csv(config.TAB_DIR / "pca_loadings.csv")
    rows = []
    for name, fit in [("K-means", lambda Z: cl.kmeans_fit(Z, K).labels_),
                      ("GMM", lambda Z: cl.gmm_fit(Z, K, gmm_cov).predict(Z)),
                      ("Hierarchical (Ward)", lambda Z: cl.hierarchical_fit(Z, K, "ward").labels_)]:
        l_full, l_pca = fit(X), fit(Zp)
        s_full, s_pca = ev.euclidean_scores(X, l_full), ev.euclidean_scores(Zp, l_pca)
        rows.append({"algorithm": name,
                     "silhouette_7D": s_full["silhouette"], f"silhouette_PCA{n_pc}": s_pca["silhouette"],
                     "DB_7D": s_full["davies_bouldin"], f"DB_PCA{n_pc}": s_pca["davies_bouldin"],
                     "CH_7D": s_full["calinski_harabasz"], f"CH_PCA{n_pc}": s_pca["calinski_harabasz"],
                     "ARI_7D_vs_PCA": ev.ari(l_full, l_pca)})
    pca_eval = pd.DataFrame(rows)
    print("\nBefore vs after PCA (each scored in its own space; DB lower=better):\n",
          pca_eval.round(3).to_string(index=False))
    pca_eval.to_csv(config.TAB_DIR / "pca_before_after.csv", index=False)

    banner("PART A | Step 6  Dissimilarity metrics (average-linkage on precomputed D)")
    mats = dm.all_distance_matrices(X)
    metric_rows, metric_labels = [], {}
    for mname, obj in mats.items():
        D = obj["D"]
        checks = dm.validate_distance_matrix(D)
        for link in ("average", "complete"):
            lab = cl.relabel_by_risk(cl.hierarchical_precomputed(D, K, link).labels_, vol)
            sc_own = ev.precomputed_scores(D, lab)
            sc_euc = ev.euclidean_scores(X, lab)
            sizes = "/".join(map(str, sorted(np.bincount(lab), reverse=True)))
            metric_rows.append({"metric": mname, "linkage": link,
                                "silhouette_precomputed": sc_own["silhouette"],
                                "silhouette_euclid_space": sc_euc["silhouette"],
                                "DB_euclid_space": sc_euc["davies_bouldin"],
                                "CH_euclid_space": sc_euc["calinski_harabasz"],
                                "cluster_sizes": sizes, "valid_matrix": all(checks.values())})
            if link == "average":
                metric_labels[mname] = lab
        print(f"{mname:12s} valid={checks}  notes={obj['notes']}")
    metric_tab = pd.DataFrame(metric_rows)
    print("\n", metric_tab.round(3).to_string(index=False))
    print("DB/CH for non-Euclidean metrics are computed on the partition in the common Euclidean "
          "feature space, never on the precomputed matrix itself.")
    metric_tab.to_csv(config.TAB_DIR / "distance_metric_comparison.csv", index=False)
    m_assign = pd.DataFrame(metric_labels, index=names)
    m_assign.to_csv(config.TAB_DIR / "distance_metric_assignments.csv")
    mk = list(metric_labels)
    metric_ari = pd.DataFrame([[ev.ari(metric_labels[a], metric_labels[b]) for b in mk] for a in mk],
                              index=mk, columns=mk)
    print("\nARI between metric partitions:\n", metric_ari.round(3))
    metric_ari.to_csv(config.TAB_DIR / "distance_metric_ari.csv")

    banner("PART A | Step 7  Stability (ARI)")
    n_boot = 30 if args.quick else config.N_BOOTSTRAP
    n_seed = 20 if args.quick else config.N_SEED_RUNS
    seed_tab = st.seed_stability(X, K, n_runs=n_seed, gmm_cov=gmm_cov)
    print(seed_tab.round(3).to_string(index=False))
    boot_sum, boot_raw = st.bootstrap_stability(returns, K, n_boot=n_boot, gmm_cov=gmm_cov)
    print(f"\nBlock bootstrap ({n_boot} resamples, block={config.BOOTSTRAP_BLOCK} days):")
    print(boot_sum.round(3).to_string(index=False))
    loo = st.leave_one_out_stability(X, names, K, gmm_cov=gmm_cov)
    print("\nLeave-one-asset-out:\n", loo.round(3).to_string(index=False))
    seed_tab.to_csv(config.TAB_DIR / "stability_seeds.csv", index=False)
    boot_sum.to_csv(config.TAB_DIR / "stability_bootstrap.csv", index=False)
    boot_raw.to_csv(config.RES_DIR / "stability_bootstrap_raw.csv", index=False)
    loo.to_csv(config.TAB_DIR / "stability_leave_one_out.csv", index=False)

    banner("PART A | Step 8  Risk-profile summary")
    primary = max(labels, key=lambda m: algo_scores.loc[m, "silhouette"])
    lab = labels[primary]
    tier_names = {0: "Low risk", 1: "Moderate risk", 2: "High risk"} if K == 3 else \
        {i: f"Tier {i}" for i in range(K)}
    prof = readable.copy()
    prof["cluster"] = lab
    summary = prof.groupby("cluster").mean(numeric_only=True)
    summary.insert(0, "Members", prof.groupby("cluster").apply(lambda g: ", ".join(g.index)))
    zdf = pd.DataFrame(X, index=names, columns=F.columns)
    zdf["cluster"] = lab
    zmean = zdf.groupby("cluster").mean()
    summary.insert(1, "Most distinctive feature (mean z)", [
        f"{zmean.loc[c].abs().idxmax()} ({zmean.loc[c, zmean.loc[c].abs().idxmax()]:+.2f})"
        for c in summary.index])
    summary.index = [f"{c}: {tier_names[c]}" for c in summary.index]
    print(f"Primary partition: {primary} (highest silhouette)\n", summary.round(2))
    summary.round(3).to_csv(config.TAB_DIR / "risk_profile_summary.csv")

    banner("PART A | Figures")
    viz.setup_style()
    f = config.FIG_DIR
    viz.plot_return_distributions(returns, f / "A1_return_distributions.png", note)
    viz.plot_feature_heatmap(F, X, f / "A2_risk_feature_heatmap.png", note)
    viz.plot_model_selection(km_tab, gmm_tab, f / "A3_elbow_silhouette_bic.png", K, note)
    viz.plot_pca_variance(var_tab, f / "A4_pca_explained_variance.png", note)
    viz.plot_pca_clusters(Z2, names, labels, f / "A5_pca_clusters.png",
                          pca.explained_variance_ratio_, note)
    viz.plot_dendrograms(cl.linkage_matrix(X, "ward"), cl.linkage_matrix(X, "average"), names,
                         f / "A6_dendrograms.png", K, note)
    mt = metric_tab[metric_tab["linkage"] == "average"].reset_index(drop=True)
    viz.plot_metric_comparison(mt, m_assign, metric_ari, f / "A7_distance_metric_comparison.png", note)
    viz.plot_stability(boot_raw, seed_tab, f / "A8_cluster_stability.png", note)
    tbl = summary.drop(columns=["Members", "Most distinctive feature (mean z)"]).round(1).astype(str)
    tbl.insert(0, "n", prof.groupby("cluster").size().values.astype(str))
    viz.plot_table(tbl, f / "A9_risk_profile_table.png",
                   f"Risk-profile summary ({primary}, K={K}; cluster means)", note=note,
                   row_colors=viz.CAT[:K])
    mem = pd.DataFrame({"Members": summary["Members"],
                        "Most distinctive feature (mean z)": summary["Most distinctive feature (mean z)"]})
    viz.plot_table(mem, f / "A9b_cluster_members.png", "Cluster members", col_width=3.2, note=note,
                   row_colors=viz.CAT[:K])
    print(f"Saved figures to {f}")

    results["part_a"] = {
        "data_source": src, "n_days": int(len(returns)), "assets": names,
        "window": [str(prices.index.min().date()), str(prices.index.max().date())],
        "k_best_silhouette_kmeans": k_sil, "gmm_best": {"covariance": gmm_cov, "k": k_bic},
        "K_used": K, "assignments": assign.to_dict(), "algorithm_scores": algo_scores.to_dict(),
        "algorithm_ari": algo_ari.to_dict(), "pca_components_kept": n_pc,
        "pca_explained": var_tab["explained_variance_ratio"].tolist(),
        "pca_before_after": pca_eval.to_dict(orient="records"),
        "metric_comparison": metric_tab.to_dict(orient="records"),
        "metric_ari": metric_ari.to_dict(), "mahalanobis_notes": mats["Mahalanobis"]["notes"],
        "cosine_near_zero_rows": mats["Cosine"]["notes"]["near_zero_rows"],
        "stability_seeds": seed_tab.to_dict(orient="records"),
        "stability_bootstrap": boot_sum.to_dict(orient="records"),
        "stability_loo": loo.to_dict(orient="records"),
        "primary_partition": primary, "seconds": round(time.time() - t0, 1),
    }


# =============================================================================== PART B
def run_part_b(args, results):
    t0 = time.time()
    banner("PART B | Step 1  Load market index (NIFTY 50)")
    px, src = dl.load_index_prices(prefer=args.source, refresh=args.refresh_data)
    note = f"Data: {src} | NIFTY 50 daily close {px.index.min():%Y-%m-%d} to {px.index.max():%Y-%m-%d}"
    if "SYNTHETIC" in src:
        note = "SYNTHETIC DATA (simulated regime-switching index, NOT market data)"
    r = dl.log_returns(px) * config.RETURN_SCALE          # percent log returns
    roll_vol = r.rolling(config.ROLLING_VOL_WINDOW).std() * np.sqrt(252)
    train = r[r.index <= config.TRAIN_END]
    test = r[r.index > config.TRAIN_END]
    y_tr, y_te, y = train.values, test.values, r.values
    dates = r.index
    print(f"Source: {src}\nTrain: {train.index.min():%Y-%m-%d} -> {train.index.max():%Y-%m-%d} "
          f"({len(train)} days)  |  Test: {test.index.min():%Y-%m-%d} -> {test.index.max():%Y-%m-%d} "
          f"({len(test)} days)  [chronological, no shuffling]")

    banner("PART B | Step 2  Fit 3-state Gaussian HMM (Baum-Welch, restarts)")
    restarts = 4 if args.quick else config.HMM_RESTARTS
    t_h = time.time()
    model, info = hm.fit_hmm(y_tr, config.HMM_STATES, restarts=restarts)
    hmm_fit_s = time.time() - t_h
    P = hm.params(model)
    names = hm.name_states(P["means"], P["variances"])
    print("Restart train log-likelihoods:", np.round(info["restart_logliks"], 2))
    print("Initial probabilities pi:", np.round(P["pi"], 4))
    order = sorted(names, key=lambda s: ["Bull", "Bear", "High-Volatility"].index(names[s]))
    A_df = pd.DataFrame(P["A"], index=[f"{s}:{names[s]}" for s in range(3)],
                        columns=[f"{s}:{names[s]}" for s in range(3)])
    print("Transition matrix A (rows = from):\n", A_df.round(4))
    em = pd.DataFrame({"state": list(range(3)), "regime": [names[s] for s in range(3)],
                       "mean_%": P["means"], "std_%": np.sqrt(P["variances"]),
                       "expected_duration_days": 1 / (1 - np.diag(P["A"]))}).set_index("state")
    print("Emission parameters (named from learned mean/variance):\n", em.round(4))
    A_df.to_csv(config.TAB_DIR / "hmm_transition_matrix.csv")
    em.to_csv(config.TAB_DIR / "hmm_emissions.csv")

    banner("PART B | Step 3  Sum-Product (forward-backward) inference -- our NumPy code")
    lb = sp.gaussian_log_emissions(y, P["means"], P["variances"])
    t_sp = time.time()
    out = sp.sum_product(P["pi"], P["A"], lb)
    sp_s = time.time() - t_sp
    gamma = out["gamma"]
    filt = sp.filtered_probs(out["log_alpha"])
    row_sums = gamma.sum(axis=1)
    ref_gamma = model.predict_proba(y.reshape(-1, 1))
    ref_ll = model.score(y.reshape(-1, 1))
    print(f"log p(y_1:T): ours = {out['loglik']:.6f}   hmmlearn = {ref_ll:.6f}")
    print(f"max |gamma_ours - gamma_hmmlearn| = {np.abs(gamma - ref_gamma).max():.2e}")
    print(f"posterior rows sum to 1: min={row_sums.min():.12f}  max={row_sums.max():.12f}")
    post = pd.DataFrame(gamma, index=dates, columns=[names[s] for s in range(3)])
    post.to_csv(config.RES_DIR / "hmm_posterior_probabilities.csv")
    print("\nSMOOTHED posterior p(z_t | y_1:T), last 8 trading days "
          "(retrospective: uses the full observation sequence):\n", post.tail(8).round(4))
    filt_df = pd.DataFrame(filt, index=dates, columns=[names[s] for s in range(3)])
    print("\nFILTERED posterior p(z_t | y_1:t), last 8 trading days "
          "(causal: uses only data up to day t -> real-time detection):\n", filt_df.tail(8).round(4))

    # toy hand-checkable example
    pi0, A0, B0 = sp.toy_example()
    toy = sp.sum_product(pi0, A0, np.log(B0))
    bf_marg, bf_p, bf_path = sp.brute_force(pi0, A0, B0)
    tv, _ = sp.viterbi(pi0, A0, np.log(B0))
    print(f"\nToy 2-state HMM check: p(y) forward={np.exp(toy['loglik']):.6f} brute-force={bf_p:.6f}; "
          f"max marginal diff={np.abs(toy['gamma'] - bf_marg).max():.1e}; "
          f"Viterbi {tv.tolist()} vs brute-force {bf_path.tolist()}")

    banner("PART B | Step 4  Viterbi decoding (max-product) -- distinct from Sum-Product")
    vpath, vlogp = sp.viterbi(P["pi"], P["A"], lb)
    agree_lib = float((vpath == model.predict(y.reshape(-1, 1))).mean())
    agree_post = float((vpath == gamma.argmax(1)).mean())
    print("Full-sequence Viterbi decoding uses the whole observation sequence: the path is a "
          "retrospective (historical) labelling, not a real-time prediction.")
    print(f"Viterbi path log p(z*, y) = {vlogp:.2f}; agreement with hmmlearn Viterbi = {agree_lib:.4f}")
    print(f"Days where Viterbi state != argmax of Sum-Product marginal: "
          f"{int((vpath != gamma.argmax(1)).sum())} of {len(y)} ({1 - agree_post:.2%})")
    regime_rows = []
    for s in order:
        m = vpath == s
        runs = np.diff(np.flatnonzero(np.diff(np.r_[0, m.astype(int), 0])))[::2]
        regime_rows.append({"regime": names[s], "share_of_days_%": m.mean() * 100,
                            "share_test_%": m[len(y_tr):].mean() * 100,
                            "realised_mean_%": y[m].mean(), "realised_std_%": y[m].std(),
                            "n_episodes": len(runs), "avg_episode_days": runs.mean() if len(runs) else 0})
    reg_tab = pd.DataFrame(regime_rows).set_index("regime")
    print(reg_tab.round(3))
    reg_tab.to_csv(config.TAB_DIR / "hmm_regime_statistics.csv")
    pd.DataFrame({"viterbi_state": vpath, "viterbi_regime": [names[s] for s in vpath]},
                 index=dates).to_csv(config.RES_DIR / "hmm_viterbi_path.csv")

    banner("PART B | Step 5  HMM model selection & out-of-sample likelihood")
    sel = hm.model_selection(y_tr, y_te, ks=(1, 2, 3, 4))
    print(sel.round(4).to_string(index=False))
    k_bic_hmm = int(sel.loc[sel["bic"].idxmin(), "states"])
    k_test_hmm = int(sel.loc[sel["test_loglik_per_day"].idxmax(), "states"])
    if k_bic_hmm != k_test_hmm:
        tl = sel.set_index("states")["test_loglik_per_day"]
        print(f"BIC selects the {k_bic_hmm}-state HMM as a balance between model fit and complexity. "
              f"The {k_test_hmm}-state model achieves a slightly better held-out predictive log-likelihood "
              f"({tl[k_test_hmm]:.4f} vs {tl[k_bic_hmm]:.4f} per day). We retain {config.HMM_STATES} states "
              "because they support the intended Bull, Bear and High-Volatility interpretation, while "
              "acknowledging that the optimal number of states depends on the selection criterion.")
    sel.to_csv(config.TAB_DIR / "hmm_model_selection.csv", index=False)

    banner("PART B | Step 6  Linear Dynamical Systems (NumPy Kalman filter + RTS smoother)")
    t_l = time.time()
    ll_model, ll_info = lds.fit_local_level(y_tr)
    f_tr = ll_model.filter(y)
    trend_s, _ = ll_model.smooth(f_tr)
    lv_model, lv_info = lds.fit_logvol(y_tr)
    f_lv = lv_model.filter(lds.log_sq_obs(y))
    h_s, Ph_s = lv_model.smooth(f_lv)
    lds_s = time.time() - t_l
    lds_sigma = np.exp(h_s[:, 0] / 2 + Ph_s[:, 0, 0] / 8)
    lv_pred_ll, _ = lds.logvol_predictive_loglik(lv_model, y, y_tr.mean())
    print("LDS-Trend (local level) MLE:", {k: round(v, 8) for k, v in ll_info.items()})
    print("LDS-Vol (AR(1) log-variance) MLE:", {k: round(v, 5) for k, v in lv_info.items()})
    hmm_mean = gamma @ P["means"]
    hmm_sigma = np.sqrt(gamma @ (P["variances"] + P["means"] ** 2) - hmm_mean ** 2)
    rv_daily = (roll_vol / np.sqrt(252)).values
    ok = ~np.isnan(rv_daily)
    corr_hmm = float(np.corrcoef(hmm_sigma[ok], rv_daily[ok])[0, 1])
    corr_lds = float(np.corrcoef(lds_sigma[ok], rv_daily[ok])[0, 1])
    print(f"Correlation with 21-day realised vol: HMM sigma_t = {corr_hmm:.3f} | LDS-Vol sigma_t = {corr_lds:.3f}")
    pd.DataFrame({"return_%": y, "lds_trend_smoothed": trend_s[:, 0], "lds_sigma_smoothed": lds_sigma,
                  "hmm_expected_mean": hmm_mean, "hmm_sigma": hmm_sigma},
                 index=dates).to_csv(config.RES_DIR / "lds_and_hmm_latent_estimates.csv")

    banner("PART B | Step 7  HMM vs LDS: one-step-ahead predictive log-likelihood on TEST")
    n_tr = len(y_tr)
    hmm_pred = sp.one_step_predictive_loglik(P["pi"], P["A"], lb)
    iid = sp.gaussian_log_emissions(y_te, [y_tr.mean()], [y_tr.var()]).ravel()
    comp = pd.DataFrame([
        {"model": "i.i.d. Gaussian (baseline)", "test_loglik_per_day": iid.mean(),
         "latent_state": "none", "exact_likelihood": True},
        {"model": "LDS-Trend (Kalman, continuous drift)", "test_loglik_per_day": f_tr["loglik_t"][n_tr:].mean(),
         "latent_state": "continuous", "exact_likelihood": True},
        {"model": "LDS-Vol (Kalman QML, plug-in density)*", "test_loglik_per_day": lv_pred_ll[n_tr:].mean(),
         "latent_state": "continuous", "exact_likelihood": False},
        {"model": "HMM-3 (forward filter, discrete)", "test_loglik_per_day": hmm_pred[n_tr:].mean(),
         "latent_state": "discrete", "exact_likelihood": True},
    ])
    print(comp.round(4).to_string(index=False))
    print("Protocol: parameters fitted on train only; each test day scored with p(y_t | y_1:t-1) "
          "from a causal filter, same data and units (percent log return) for every model.\n"
          "* LDS-Vol is a quasi-likelihood linearisation; its return density is an approximation.")
    comp.to_csv(config.TAB_DIR / "hmm_vs_lds_predictive.csv", index=False)
    qual = pd.DataFrame({
        "Aspect": ["Latent state", "Interpretability", "Abrupt transitions", "Smooth trends",
                   "Volatility clustering", "Test log-lik / day", "Corr. with realised vol",
                   "Fit time (s)", "Key assumptions"],
        "HMM (3 Gaussian states)": [
            "Discrete z_t in {Bull, Bear, High-Vol}", "Named regimes + transition probabilities",
            "Yes: jump between states in one step", "Only as a mixture of a few levels",
            "Yes: high-variance state", f"{hmm_pred[n_tr:].mean():.4f}", f"{corr_hmm:.3f}",
            f"{hmm_fit_s:.1f} (EM x{restarts})", "Markov switching, Gaussian emissions, constant params"],
        "LDS (Kalman)": [
            "Continuous x_t in R (drift or log-variance)", "No labels; a smooth continuous signal",
            "No: Gaussian random-walk moves gradually", "Yes: optimal linear-Gaussian smoothing",
            "Only LDS-Vol (via log r^2 transform)",
            f"Trend {f_tr['loglik_t'][n_tr:].mean():.4f} / Vol* {lv_pred_ll[n_tr:].mean():.4f}",
            f"{corr_lds:.3f} (LDS-Vol)", f"{lds_s:.1f} (both models)",
            "Linear dynamics, Gaussian noise, constant Q and R"],
    })
    qual.to_csv(config.TAB_DIR / "hmm_vs_lds_comparison.csv", index=False)
    print(qual.to_string(index=False))

    banner("PART B | Figures")
    viz.setup_style()
    f = config.FIG_DIR
    viz.plot_index_regimes(px.loc[dates], dates, vpath, names, config.TRAIN_END,
                           f / "B1_nifty_regimes_viterbi.png",
                           "NIFTY 50 HMM regimes: full-sequence Viterbi path (retrospective; parameters fitted on train only)", note)
    viz.plot_returns_vol(r, roll_vol, f / "B2_returns_rolling_vol.png", note)
    viz.plot_posteriors(dates, gamma, names, f / "B3_posterior_probabilities.png", config.TRAIN_END, note)
    viz.plot_hmm_params(P["A"], P["means"], P["variances"], names, f / "B4_transition_emissions.png", note)
    viz.plot_sp_vs_viterbi(dates, y, gamma, filt, vpath, names, ("2020-01-01", "2020-12-31"),
                           f / "B5_sumproduct_vs_viterbi_2020.png", note)
    viz.plot_sp_vs_viterbi(dates, y, gamma, filt, vpath, names, ("2024-01-01", str(dates.max().date())),
                           f / "B5b_sumproduct_vs_viterbi_test.png", note)
    viz.plot_lds_comparison(dates, rv_daily, hmm_sigma, lds_sigma, trend_s[:, 0], hmm_mean,
                            config.TRAIN_END, f / "B6_hmm_vs_lds.png", note)
    viz.plot_predictive(comp, f / "B7_predictive_loglik.png", note)
    viz.plot_table(A_df.round(3), f / "B8_transition_table.png", "Learned transition matrix", note=note)
    print(f"Saved figures to {f}")

    results["part_b"] = {
        "data_source": src, "train_days": int(len(y_tr)), "test_days": int(len(y_te)),
        "train_window": [str(train.index.min().date()), str(train.index.max().date())],
        "test_window": [str(test.index.min().date()), str(test.index.max().date())],
        "pi": P["pi"], "A": P["A"], "means": P["means"], "variances": P["variances"],
        "state_names": names, "loglik_ours": out["loglik"], "loglik_hmmlearn": ref_ll,
        "max_gamma_diff_vs_hmmlearn": float(np.abs(gamma - ref_gamma).max()),
        "posterior_row_sum_range": [float(row_sums.min()), float(row_sums.max())],
        "viterbi_agreement_hmmlearn": agree_lib, "viterbi_vs_posterior_argmax_agreement": agree_post,
        "toy_check": {"p_forward": float(np.exp(toy["loglik"])), "p_bruteforce": float(bf_p),
                      "max_marginal_diff": float(np.abs(toy["gamma"] - bf_marg).max()),
                      "viterbi": tv.tolist(), "bruteforce_best": bf_path.tolist()},
        "model_selection": sel.to_dict(orient="records"),
        "lds_trend": ll_info, "lds_vol": lv_info,
        "corr_realised_vol": {"hmm": corr_hmm, "lds_vol": corr_lds},
        "predictive_comparison": comp.to_dict(orient="records"),
        "regime_stats": reg_tab.reset_index().to_dict(orient="records"),
        "timing_s": {"hmm_fit": hmm_fit_s, "sum_product": sp_s, "lds_fit_and_smooth": lds_s},
        "seconds": round(time.time() - t0, 1),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--refresh-data", action="store_true")
    ap.add_argument("--source", choices=dl.SOURCES, default=None)
    ap.add_argument("--part", choices=["A", "B", "all"], default="all")
    args = ap.parse_args()
    if args.source == "synthetic":   # keep synthetic outputs apart from real-data outputs
        base = config.OUT_DIR / "synthetic"
        config.FIG_DIR, config.TAB_DIR, config.RES_DIR = base / "figures", base / "tables", base / "results"
    for d in (config.FIG_DIR, config.TAB_DIR, config.RES_DIR, config.RAW_DIR):
        d.mkdir(parents=True, exist_ok=True)
    np.random.seed(config.SEED)
    t0 = time.time()
    results = {"config": {"seed": config.SEED, "quick": args.quick, "source_flag": args.source}}
    if args.part in ("A", "all"):
        run_part_a(args, results)
    if args.part in ("B", "all"):
        run_part_b(args, results)
    results["total_seconds"] = round(time.time() - t0, 1)
    name = "results_synthetic.json" if args.source == "synthetic" else "results.json"
    (config.RES_DIR / name).write_text(json.dumps(jsonable(results), indent=2))
    banner(f"DONE in {results['total_seconds']} s  |  results -> {config.RES_DIR / name}")


if __name__ == "__main__":
    main()
