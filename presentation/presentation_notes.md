# 📌 Presentation package (start here)
| Situation | Use |
|---|---|
| **5–7 minute slot (main plan)** | `project_review_2.pptx` (12 slides) + **`5_to_7_minute_script.md`**: word-for-word, 789 words ≈ 5 min 50 s; Srushti slides 1–5, Agadh 6–7, Sneh 8–12 |
| Under 5 minutes | `project_review_2_short.pptx` (7 slides) + the short script directly below |
| Questions | **`viva_questions.md`**: 20 questions, follow-up probes, glossary |
| Demo | **`live_demo_guide.md`**: commands, what to point at, fallbacks |

**Concise speaking notes (12-slide deck, 6 min):**
1. Title: two parts, Unit III and Unit IV. *(Srushti, 10 s)*
2. Problem: one number can't describe risk; markets switch regimes. *(25 s)*
3. Pipeline: real NSE data → Part A clustering lane / Part B HMM lane → one command. *(20 s)*
4. Data: 12 stocks, 9 sectors, 1,235 returns; returns, not prices; 7 features; standardised. *(35 s)*
5. Algorithms: hard (K-means) vs soft (GMM) vs tree (Ward); BIC → 3, silhouette → 2, so the criteria don't fully agree; K = 3 kept. *(30 s)*
6. Distances: Manhattan = Euclidean here; Cosine and Mahalanobis regroup stocks; K-means is Euclidean only; PCA 53 / 22 / 18%. *(Agadh, 55 s)*
7. Results: Ward silhouette 0.27; Low / Tail / High risk; bootstrap ARI 0.26–0.50; Mahalanobis most stable. *(55 s)*
8. HMM: hidden regime vs observed return; Bull +0.12%/day, Bear ≈ 0 (choppy), High-Vol σ ≈ 3.9%; BIC → 3, 4 slightly better on test. *(Sneh, 35 s)*
9. Sum-Product sums over paths (per-day probabilities); Viterbi maximises (one best path); both retrospective, filtered = real-time; matches hmmlearn. *(35 s)*
10. LDS: continuous hidden state; no predictable trend; smooth volatility; HMM jumps, LDS glides. *(20 s)*
11. Held-out, causal comparison: HMM best, LDS-Vol second, LDS-Trend ≈ baseline; limitations. *(20 s)*
12. Conclusion: three tiers, metric matters, regimes beat trends. *(10 s)*

---

# ⏱ SHORT VERSION: use this (`project_review_2_short.pptx`, 7 slides, about 4 minutes)
Split between three speakers (suggested): **Srushti** slides 1–3 · **Agadh** slides 4–5 · **Sneh** slides 6–7.

| # | Slide | Say this (≈ 30–40 s each) |
|---|---|---|
| 1 | Title | "We built a system that groups stocks by risk and detects hidden market regimes, using clustering for Unit III and HMMs for Unit IV." |
| 2 | Two questions, one pipeline | "Part A: which stocks share a risk profile? Part B: which regime is the market in? One command loads real NSE data, runs every model and produces all plots in about 30 seconds." |
| 3 | Data and features | "12 NSE stocks from 9 sectors over 5 years. Each stock gets 7 risk numbers, including VaR, CVaR and drawdown. We standardise them so no single feature dominates. Red in the heatmap means riskier than average." |
| 4 | Three risk profiles | "We compared K-means, GMM and hierarchical clustering. GMM BIC chose 3 groups (K-means silhouette preferred 2, so the criteria don't fully agree; we kept 3 for the risk-profile interpretation): a low-risk core, a tail-risk pair (ITC and LT), and a high-risk group (TCS, Infosys, Tata Steel). Switching between Manhattan, Cosine and Mahalanobis distance changes the groups, and Mahalanobis was the most stable." |
| 5 | Hidden regimes | "A 3-state Hidden Markov Model on NIFTY 50 returns finds Bull, Bear and High-Volatility regimes. It caught the 2020 COVID crash. We fitted it on data up to 2023 and tested on 2024 onwards. The coloured regime chart is a retrospective labelling from full-sequence Viterbi; real-time detection would use the filtered probabilities." |
| 6 | Inference and LDS | "Sum-Product gives the probability of each regime on each day. Viterbi gives the single most likely path. We coded both ourselves and they match the library exactly. Against a continuous Kalman-filter model, the HMM predicts unseen data best, because regime jumps matter more than smooth trends." |
| 7 | Conclusion | "We built and tested everything on real data, with 31 passing tests. Next steps: more stocks and a regime-aware portfolio. Thank you." |

**If asked one question**, the key one is: *Sum-Product vs Viterbi?* Sum-Product **sums** over all paths and gives a probability per day. Viterbi **maximises** over paths and gives one best sequence.
Detailed answers to other questions are in section C below. The 12-slide `project_review_2.pptx` is the backup.

---

# Presentation Notes: Project Review 2
**Financial Market Risk Profiling and Regime Detection**
Target: 6 minutes of talk, then about 2–3 minutes of live demo. Every number below comes from `outputs/results/results.json` (full run on real NSE data).

---

## A. Script, slide by slide (≈ 6 min)

**1. Title (20 s)**
"Our project has two parts that map to Units III and IV. Part A groups 12 NSE stocks into risk profiles using three clustering algorithms and three distance measures. Part B detects hidden market regimes in the NIFTY 50 with a Hidden Markov Model, runs exact Sum-Product inference we coded ourselves, and compares it with a continuous Linear Dynamical System."

**2. Problem and objectives (30 s)**
- Risk is multi-dimensional: two stocks with the same volatility can have very different crash behaviour.
- Markets switch between calm and stressed periods, so one fixed model is wrong.
- Real numbers: 12 stocks / 9 sectors, 2,893 index days, 31 tests passing, full run in about 30 s.

**3. Architecture (40 s)**
- Data layer tries cache → yfinance → the eod2 NSE dataset → synthetic (always labelled).
- Cleaning: one trading calendar, forward-fill gaps of 3 days or less, never back-fill, log returns.
- Lane A: features → z-score → PCA → clustering → validity and stability.
- Lane B: chronological split → HMM fitted on 2015–2023 only → our Sum-Product and Viterbi → Kalman LDS → predictive test on 2024–2026.

**4. Data and features (35 s)**
- 1,235 daily log returns per stock, Oct 2021 to Sep 2026.
- Seven features: mean, volatility, skew, excess kurtosis, historical VaR95, CVaR95, max drawdown.
- Z-scored, because otherwise kurtosis (large unitless numbers) would dominate the distances.
- VaR, CVaR and volatility have correlation ≈ 0.95. That is the motivation for Mahalanobis distance and PCA.

**5. Clustering algorithms (45 s)**
- K-means minimises squared Euclidean SSE, so it is never "Manhattan K-means".
- GMM is soft and probabilistic. With 12 assets a full covariance is impossible, so spherical/diagonal with a variance floor.
- Ward merges the pair with the least SSE increase, so it is Euclidean only.
- Choosing k: we selected K = 3 for the main risk-profile comparison based on the GMM BIC criterion (BIC 244.6). K-means silhouette favours K = 2 (0.361; it just isolates TATASTEEL and INFY), so the selection criteria do not fully agree. Three clusters were retained for the principal comparison to support the intended risk-profile interpretation.

**6. Distances and PCA (45 s)**
- Fair test: the algorithm is fixed (average linkage on a precomputed D) and only the distance changes.
- Euclidean = Manhattan here (ARI 1.0). Cosine has the highest own-space silhouette (0.47): it groups by the shape of the risk profile. Mahalanobis (0.16) removes duplicated tail-risk information.
- Mahalanobis needed shrinkage: condition number 524 → 5.8 with Ledoit-Wolf (λ = 0.43), plus a pseudo-inverse.
- PCA: PC1 53% (tail risk), PC2 22%, PC3 18%; 3 PCs keep 93%.

**7. Part A results (50 s)**
- Ward has the best silhouette (0.27). Three tiers:
  - **Low risk**: RELIANCE, HDFCBANK, ICICIBANK, HINDUNILVR, SUNPHARMA, MARUTI, BHARTIARTL (vol 21%, max DD 27%).
  - **Tail risk**: ITC, LT. Average volatility but skew −0.62, kurtosis 6.5, drawdown 40%.
  - **High risk**: TCS, INFY, TATASTEEL (CVaR 4.0%, drawdown 49%).
- Stability, stated honestly: K-means with one random start has ARI 0.34 across seeds, and k-means++ with 20 starts raises it to 0.78. Under a block bootstrap of trading days, ARI is only 0.26–0.50, so with 12 assets the profiles are moderately stable. Mahalanobis is the most stable.
- The PCA plot is a visualisation, not proof of cluster quality.

**8. HMM (45 s)**
- Three hidden states, transition matrix A, one Gaussian per state; fitted by Baum-Welch on 2,213 training days, best of 10 restarts.
- State ids are arbitrary, so names come from learned parameters: largest σ = High-Vol; then higher μ = Bull, lower μ = Bear.
- BIC: 6606 (1 state), 5901 (2), **5796 (3)**, 5837 (4). BIC selects the three-state HMM as a balance between model fit and complexity. The four-state model achieves a slightly better held-out predictive log-likelihood (−1.1726 vs −1.1744 per day). We retain three states because they support the Bull, Bear and High-Volatility interpretation, while acknowledging that the optimal number of states depends on the selection criterion.
- Learned: Bull μ +0.117%/day, σ 0.60%, expected stay ≈ 86 days. Bear μ ≈ 0, σ 1.05%, ≈ 51 days. High-Vol σ 3.9%, ≈ 7 days, and always exits to Bear.

**9. Sum-Product vs Viterbi (50 s)**
- Sum-Product (forward-backward) sums over all paths and gives p(z_t | all data) for each day.
- Viterbi maximises over paths and gives the single best sequence. They disagree on 3.7% of days.
- Verification: our log-likelihood equals hmmlearn's (−3642.938); posterior difference 1.2e-12; rows sum to 1; Viterbi matches hmmlearn on 100% of days; a toy 2-state example matches brute-force enumeration of all 8 paths.
- 2020 plot: the filtered posterior p(z_t | y_1:t) is the real-time (causal) view. The smoothed posterior p(z_t | y_1:T) and the full-sequence Viterbi path are retrospective: they use the whole series, which is why the smoothed curve is steadier.

**10. LDS (45 s)**
- Continuous hidden state; our NumPy Kalman filter and RTS smoother; Q and R by maximum likelihood.
- LDS-Trend: MLE drives the drift noise Q to 0, so the drift is constant. Daily index returns have no predictable trend.
- LDS-Vol: an AR(1) on log-variance, φ = 0.988, half-life ≈ 56 days. A smooth volatility curve.
- Both track realised volatility (correlation 0.79 HMM, 0.80 LDS-Vol). The HMM jumps; the LDS glides.

**11. Results and limitations (45 s)**
- Fair test: the one-step predictive density on unseen 2024–2026 data. HMM-3 gains +0.129 nats/day over i.i.d., LDS-Vol +0.061, LDS-Trend ≈ 0.
- Limitations: small universe, statistical regime names, approximate LDS-Vol density, no dividend adjustment, HMM-4 marginally better on test but worse BIC.

**12. Conclusion (20 s)**
"Everything in green is implemented and tested. The lessons: risk profiles depend on the distance you choose, and for daily index returns volatility regimes matter far more than drift. Future work is listed separately and is not built. Thank you. Happy to run the demo."

---

## B. Live demo (90–120 s)
See **`live_demo_guide.md`** for the full sequence. In short:
1. Run `python main.py` (≈ 40–60 s, full mode, reproduces the slide numbers) and talk while it runs.
2. Point at `We selected K=3 …`, the cluster assignments, and `Keeping 3 PCs`, then open `outputs/figures/A5_pca_clusters.png`.
3. Point at the transition matrix, `log p(y_1:T): ours = … hmmlearn = …`, the FILTERED posterior table and the HMM-3 row, then open `B1_nifty_regimes_viterbi.png` and `B5_sumproduct_vs_viterbi_2020.png`.
4. Optional: `pytest -q` → `31 passed`.

Do **not** use `--quick` or `--part A/B` during the review: they overwrite the saved results with lower-iteration or partial numbers. The synthetic fallback (`python main.py --source synthetic --quick`) is safe, because it writes to `outputs/synthetic/`.

---

## C. Likely evaluator questions

**Q: Why not use Manhattan distance inside K-means?**
K-means' centroid update (the mean) is optimal only for squared Euclidean distance. With L1 the optimal centre is the median (that is K-medians), so calling it Manhattan K-means would be wrong. For the metric comparison we used agglomerative average linkage on precomputed matrices.

**Q: Why can't Ward use Mahalanobis or Cosine?**
Ward's merge cost is the increase in within-cluster sum of squares, which is defined through Euclidean centroids. Our code raises an error if you try Ward with a precomputed matrix.

**Q: Why did you shrink the covariance for Mahalanobis?**
12 samples and 7 highly correlated features make the sample covariance nearly singular (condition number 524). Inverting it amplifies noise. Ledoit-Wolf shrinks it towards a scaled identity (λ = 0.43, condition number 5.8), and we use a pseudo-inverse for safety.

**Q: What happens with Cosine distance at zero vectors?**
Cosine is undefined at a zero vector. After z-scoring, an "average" stock sits near the origin, so its direction is noise. We flag rows with norm below 25% of the median (none were flagged here) and guard the division with ε.

**Q: Why K = 3 when silhouette prefers 2?**
We selected K = 3 for the main risk-profile comparison based on the GMM BIC criterion (with a variance floor). K-means silhouette favours K = 2, which only splits off two outliers, so the selection criteria do not fully agree. Three clusters were retained to support the intended risk-profile interpretation, and we report the K = 2 result rather than hiding it.

**Q: Why is ARI used instead of comparing labels directly?**
Cluster ids are arbitrary: run A's cluster 0 may be run B's cluster 2. ARI compares which pairs of assets are grouped together, so it ignores the numbering and is corrected for chance (0 = random, 1 = identical).

**Q: Your bootstrap ARI is low. Is the clustering useless?**
It shows that with 12 assets some boundary assets move between groups when the sample period changes. Per asset, we checked how often its "same group / different group" relation to the other 11 is preserved across 100 Ward bootstraps. The least consistent are TCS 0.47, HDFCBANK 0.53 and ITC 0.56. The most consistent are TATASTEEL 0.86, INFY 0.79, and SUNPHARMA and BHARTIARTL 0.72. So the extremes are robust and the middle is fuzzy. More assets would help, and that is listed as future work.

**Q: Difference between Sum-Product and Viterbi?**
Sum-Product sums over all paths and gives the marginal probability of each state on each day. Viterbi takes the max over paths and gives the single most likely complete sequence. Picking the argmax of each marginal can give a sequence that is not the most likely as a whole. On our data they differ on 3.7% of days.

**Q: How do you avoid numerical underflow?**
Probabilities of 2,900-step sequences are around e^-3600. We work in log space with log-sum-exp, and a test runs 20,000 steps without underflow.

**Q: How do you know your forward-backward is correct?**
(1) The total log-likelihood equals hmmlearn's to all printed digits. (2) The posteriors match to 1e-12. (3) A hand-computed toy example: α values are checked in a test, and the marginals match brute-force enumeration of all 2³ paths. (4) Σ_j ξ_t(i,j) = γ_t(i) is tested.

**Q: Why is state 0 not automatically "Bull"?**
EM can converge with any permutation of states. We name them after fitting: the largest variance is High-Volatility; of the other two, the higher mean is Bull.

**Q: Isn't "Bear" with mean ≈ 0 misleading?**
Yes, it is a statistical label. Its distinguishing feature is moderate volatility (1.05% vs 0.60% for Bull). We describe it as a choppy, risk-off regime.

**Q: Is the HMM vs LDS comparison fair?**
Both are scored on the same unseen days, in the same units, by the one-step-ahead predictive density p(y_t | y_1:t-1) from a causal filter with parameters fitted on training data only. The LDS-Vol density is an approximation (quasi-likelihood), and we flag it.

**Q: Why did the LDS-Trend give a flat line?**
Maximum likelihood chose state noise Q ≈ 0. The data supports no time-varying drift in daily returns, consistent with weak-form market efficiency. That is a result, not a bug: a test confirms the same code recovers a real random-walk signal on simulated data.

**Q: Is this real data?**
Yes. NSE end-of-day closes from the public eod2 dataset, adjusted for splits and bonuses, cached in `data/raw/`. yfinance is tried first on refresh. Synthetic data exists only as a fallback, is labelled on every chart, and is written to a separate folder.

**Q: Any look-ahead bias?**
The HMM and LDS parameters are fitted on 2015–2023 only, and the test scoring uses causal filters. The smoothed posteriors and the full-sequence Viterbi path in the regime plots use the full sample by design, so they are retrospective (historical) analysis, not real-time predictions. The filtered curve p(z_t | y_1:t) in the 2020 plot is the real-time view, and all out-of-sample scores use one-step-ahead predictive densities from causal filters.

**Q: Why three HMM states if four fits the test data slightly better?**
BIC selects the three-state HMM as a balance between model fit and complexity. The four-state model achieves a slightly better held-out predictive log-likelihood (−1.1726 vs −1.1744 per day). We retain three states because they support the intended Bull, Bear and High-Volatility interpretation, while acknowledging that the optimal number of states depends on the selection criterion.

---

## D. Key equations in plain words
- **VaR95**: the daily loss exceeded on only 5% of days. **CVaR95**: the average loss on those worst 5% of days.
- **Max drawdown**: the biggest fall from a previous peak of the wealth curve.
- **K-means objective** Σ‖x − μ‖²: make every point close to its cluster's average.
- **GMM** p(x) = Σ π_k N(x | μ_k, Σ_k): data comes from a few bell curves; EM alternates "which curve did each point probably come from?" and "refit the curves".
- **Mahalanobis** (x−y)ᵀS⁻¹(x−y): distance measured in units of the data's own spread, discounting directions where features move together.
- **Forward** α_t(j) = b_j(y_t) Σ_i α_{t−1}(i)A_ij: the probability of the data so far and being in state j today. Yesterday's beliefs are pushed through the transition matrix, then weighted by how well state j explains today's return.
- **Backward** β_t(i): how well state i today explains all future data.
- **Posterior** γ_t = αβ / p(y): combine past evidence (α) and future evidence (β).
- **Viterbi** δ_t(j) = b_j max_i δ_{t−1}(i)A_ij: the same recursion with max instead of sum, remembering the best predecessor.
- **Kalman gain** K = P Hᵀ(HPHᵀ + R)⁻¹: how much to trust today's observation versus the model's prediction. Large observation noise R means small K, so the estimate moves slowly.

## E. What the implementation actually does (one paragraph)
`python main.py` loads cached real NSE prices, computes 1,235 daily log returns for 12 stocks, builds a 12×7 risk-feature matrix and standardises it. It sweeps k for K-means (inertia, silhouette) and for GMM (BIC/AIC, spherical and diagonal), fits all three algorithms at K = 3, scores them with silhouette, DB and CH, and compares them with ARI. It runs PCA and re-scores in 3-PC space, builds valid Euclidean, Manhattan, Cosine and shrinkage-Mahalanobis matrices and clusters each with average and complete linkage. It measures stability over 50 seeds, 100 block bootstraps and leave-one-asset-out. For NIFTY 50 it splits 2015–2023 / 2024–2026, fits a 3-state Gaussian HMM with 10 EM restarts, names the states from their parameters, and runs **our** log-space forward-backward and Viterbi, cross-checked against hmmlearn and brute force. It compares 1–4 states by BIC and test likelihood, fits two Kalman-filter LDS models by maximum likelihood, and scores every model by one-step predictive log-likelihood on the test years. It writes 19 figures, about 20 CSV tables and a JSON summary.
