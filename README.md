# Financial Market Risk Profiling and Regime Detection
**Clustering · Gaussian Mixture Models · Hidden Markov Models · Linear Dynamical Systems**

Machine Learning Project Review 2. Everything below is implemented, executed on real NSE data and covered by tests.

---

## 1. Overview
| Part | Question | Methods |
|---|---|---|
| **A: Unit III** | Which stocks share a risk profile? | 7 risk features → StandardScaler → PCA → K-means, GMM, agglomerative (Ward/average/complete); Manhattan, Cosine and Mahalanobis distances; silhouette, Davies-Bouldin, Calinski-Harabasz; ARI stability |
| **B: Unit IV** | Which market regime is NIFTY 50 in? | 3-state Gaussian HMM (Baum-Welch via hmmlearn); **our own NumPy Sum-Product (forward-backward) and Viterbi** in log space; Kalman-filter LDS (trend and log-volatility) with an out-of-sample predictive comparison |

### Objectives mapped to the brief
- **A1 Data**: 12 NSE large caps, 9 sectors, 2021-10-01 to 2026-09-25 (1,235 daily log returns), with a synthetic fallback.
- **A2 Features**: mean, volatility, skewness, excess kurtosis, VaR95, CVaR95, max drawdown (`src/risk_features.py`).
- **A3 Algorithms**: K-means, GMM, hierarchical; k assessed with elbow, silhouette and BIC (`src/clustering.py`).
- **A4 Metrics**: valid distance matrices plus average-linkage clustering on precomputed D (`src/distance_metrics.py`).
- **A5 PCA**: explained variance, 2-D projection, before/after scores (`src/pca_analysis.py`).
- **A6 Stability**: seeds, moving-block bootstrap and leave-one-asset-out, all with ARI (`src/stability.py`).
- **B1 Data**: NIFTY 50 2015-01-01 to 2026-09-25; chronological split, train ≤ 2023-12-31 < test.
- **B2 HMM**: π, A, Gaussian emissions, forward, backward, Sum-Product, Viterbi (`src/hmm_model.py`, `src/sum_product.py`).
- **B3 Interpretation**: names come from the learned parameters; timeline, posterior and parameter plots.
- **B4 LDS**: NumPy Kalman filter, RTS smoother and MLE fitting; comparison with the HMM (`src/linear_dynamical_system.py`).

---

## 2. Installation
Python 3.10+ (tested on 3.13), CPU only.
```bash
cd financial-risk-regime-project
python -m venv .venv
# Windows: .venv\Scripts\activate      macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

## 3. Run
```bash
python main.py              # full pipeline, about 30-50 s, writes everything under outputs/
python main.py --quick      # fewer bootstrap/restart iterations (overwrites outputs with quick-mode numbers;
                            # for the review demo use plain `python main.py`, see presentation/live_demo_guide.md)
python main.py --part A     # Part A only   (--part B for Part B only)
python main.py --refresh-data          # re-download (yfinance -> eod2 -> synthetic)
python main.py --source synthetic      # demonstrate the synthetic fallback -> outputs/synthetic/
pytest -q                   # 31 tests
```
**Single-notebook option:** `Financial_Risk_Regime_Project.ipynb` (project root) contains *all* the code inline (data loading, every module, Part A, Part B and the verification checks) with outputs already saved. Open it in Jupyter or VS Code and use *Restart & Run All* (about 45 s). Run it **from the project folder** so it uses the cached data in `data/raw/` and reproduces the slide numbers. Run elsewhere, it downloads fresh data (yfinance first), so the numbers shift slightly. Regenerate it with `python presentation/build/make_notebook.py`.

Rebuild the slides after re-running (needs Node.js and `npm i pptxgenjs`):
`node presentation/build/build_deck.js presentation/build/imgsizes.json`

## 4. Data sources and fallback
See `data/README.md`. The default run uses the cached CSVs in `data/raw/`, which were downloaded from the public eod2 NSE end-of-day dataset (adjusted for splits and bonuses, not dividends), so the demo needs no internet. The loader tries cache → yfinance → eod2 → synthetic. Synthetic data is always labelled synthetic and written to a separate folder.

## 5. Outputs
| Folder | Content |
|---|---|
| `outputs/figures/` | A1–A9 (Part A) and B1–B8 (Part B) PNGs, each with a data-source footer |
| `outputs/tables/` | Every table as CSV: features, k-selection, assignments, metric comparison, stability, HMM parameters, model selection, predictive comparison |
| `outputs/results/results.json` | All headline numbers; `run_log.txt` is the console output of the last full run |
| `outputs/results/*.csv` | Posterior probabilities, Viterbi path, latent LDS/HMM estimates per day |
| `presentation/` | `project_review_2.pptx` and `presentation_notes.md` |

---

## 6. Algorithms
**K-means** minimises Σ_k Σ_{i∈C_k} ‖x_i − μ_k‖². It is defined only for squared Euclidean distance, so it is never presented as "Manhattan/Cosine/Mahalanobis K-means".

**GMM**: p(x) = Σ_k π_k N(x | μ_k, Σ_k), fitted by EM. With n = 12 and p = 7 a full Σ_k is not identifiable, so we compare spherical and diagonal covariances with `reg_covar = 0.1` (a variance floor in z-units). Without the floor, BIC kept improving as k grew because components collapsed onto 2–3 assets.

**Agglomerative**: Ward (Euclidean only, since it minimises the increase in SSE), average and complete linkage. The distance-metric experiment uses **average linkage on a precomputed D** for every metric. Ward is rejected in code for precomputed distances.

**Distances**: Manhattan Σ|x_j − y_j|. Cosine 1 − x·y/(‖x‖‖y‖): scale-invariant, not a metric, and undefined at the zero vector, so rows with norm below 25% of the median are flagged and divided by max(‖x‖, ε). Mahalanobis √((x−y)ᵀS⁻¹(x−y)), with S the Ledoit-Wolf shrunk covariance (raw condition number 524 → 5.8) and S⁻¹ computed as a pseudo-inverse.

**HMM**: z_t ∈ {1,2,3}, A_ij = p(z_t=j | z_{t−1}=i), y_t | z_t=k ~ N(μ_k, σ_k²), with returns in percent.
- *Forward*: α_t(j) = b_j(y_t) Σ_i α_{t−1}(i) A_ij
- *Backward*: β_t(i) = Σ_j A_ij b_j(y_{t+1}) β_{t+1}(j)
- *Sum-Product posterior*: γ_t(i) = α_t(i) β_t(i) / p(y_{1:T}). This **sums** over paths and gives marginals.
- *Viterbi*: δ_t(j) = b_j(y_t) max_i δ_{t−1}(i) A_ij, then backtracking. This **maximises** over paths and gives one jointly best sequence.

All recursions use log-sum-exp. Naming rule: the largest σ is High-Volatility; of the other two, the higher μ is Bull and the lower μ is Bear.

**LDS**: x_t = F x_{t−1} + c + w_t, y_t = H x_t + d + v_t, with a Kalman filter, RTS smoother and MLE of the noise variances.
- *LDS-Trend*: a random-walk drift of returns.
- *LDS-Vol*: an AR(1) log-variance observed through log(r²+c) = h_t − 1.2704 + v_t, Var v = π²/2. This is the Harvey-Ruiz-Shephard quasi-likelihood.

## 7. Evaluation metrics
- **Silhouette**: valid for any distance (computed with `metric="precomputed"` in the metric experiment).
- **Davies-Bouldin, Calinski-Harabasz**: need centroids in a vector space, so they are computed only on coordinates (z-scored features or PCs). For non-Euclidean partitions they are computed on the partition in the common Euclidean feature space, never on the precomputed matrix.
- **ARI**: label-permutation invariant (raw labels 0/1/2 are arbitrary between runs).
- **HMM/LDS**: train BIC, plus the **one-step-ahead predictive log-likelihood** log p(y_t | y_{1:t−1}) on the test period from a causal filter. All models use the same data and units, so the scores are comparable. LDS-Vol's return density is a plug-in approximation and is marked as such.

## 8. Key results (from `outputs/results/results.json`)
- K = 3, selected by GMM BIC; K-means silhouette favours K = 2, so the criteria do not fully agree, and 3 clusters are retained for the risk-profile interpretation. Ward partition: **Low risk** = RELIANCE, HDFCBANK, ICICIBANK, HINDUNILVR, SUNPHARMA, MARUTI, BHARTIARTL; **Tail risk** = ITC, LT (skew −0.62); **High risk** = TCS, INFY, TATASTEEL (CVaR 4.0%, max DD 49%).
- PCA: 53% / 22% / 18%; 3 PCs keep 93%.
- Metrics: Euclidean = Manhattan partitions; Cosine silhouette 0.47 (own space); Mahalanobis is the most bootstrap-stable (ARI 0.50).
- HMM (3 states, BIC-best): Bull μ = +0.117%, σ = 0.60%; Bear μ = −0.003%, σ = 1.05%; High-Vol μ = −0.34%, σ = 3.88% (COVID-2020).
- Our Sum-Product log-likelihood equals hmmlearn's; max posterior difference is 1.2e-12; Viterbi agrees on 100% of days.
- Test predictive log-lik/day: HMM-3 −1.174 > LDS-Vol* −1.242 > i.i.d. −1.303 ≈ LDS-Trend −1.304.

## 9. Limitations
- 12 assets is a small sample: bootstrap ARI of 0.26–0.50 means the risk profiles are only moderately stable, and BIC/AIC on n = 12 needs regularisation.
- Regime names are statistical interpretations ("Bear" has a mean near 0, so it is better read as a choppy, risk-off regime).
- Constant parameters; Gaussian emissions underweight fat tails; the LDS-Vol density is approximate.
- Prices are not dividend-adjusted. During development Yahoo Finance was unreachable from the build machine, so cached data came from eod2. yfinance is still tried first on `--refresh-data`.
- HMM-4 has a slightly better test likelihood than HMM-3 (−1.1726 vs −1.1744) but a worse BIC. We report it rather than hide it.

## 10. Troubleshooting
| Problem | Fix |
|---|---|
| `ModuleNotFoundError: hmmlearn` | `pip install hmmlearn` (wheels exist for Windows; if a compiler is needed, use Python 3.10–3.12) |
| yfinance errors / empty data | Ignore. The cache is used by default; `--refresh-data` falls through to eod2, then synthetic |
| Plots do not open in a window | Expected: figures are saved headless (`Agg`) to `outputs/figures/` |
| `No module named src` when running tests | Run `pytest` from the project root |
| Slow run | Use `python main.py --quick` |
| PowerPoint shows different fonts | The deck uses Cambria and Calibri, which ship with Office |

## 11. Project structure
```
config.py            all settings (tickers, windows, seeds, K, restarts)
main.py              end-to-end pipeline and demo printout
src/data_loader.py   cache -> yfinance -> eod2 -> synthetic; cleaning; log returns
src/risk_features.py src/clustering.py src/distance_metrics.py src/pca_analysis.py
src/stability.py     src/evaluation.py  src/visualization.py
src/hmm_model.py     src/sum_product.py src/linear_dynamical_system.py
tests/               31 pytest tests (distances, clustering, sum-product, HMM, LDS)
presentation/        project_review_2.pptx, presentation_notes.md, build/ (deck generator)
```
