# Viva Preparation: 20 Likely Questions
All numbers are from our saved run (`outputs/results/results.json`). Answers are short enough to memorise.

---

## Part A: Risk profiling and clustering

**1. Why is financial risk profiling needed?**
Two stocks can have the same volatility but very different downside behaviour, such as frequent crashes or deep drawdowns. Grouping stocks by several risk features at once helps with diversification and with understanding portfolio risk. That is why we used seven features, not one.

**2. Why use daily returns instead of closing prices?**
Prices aren't comparable across stocks: a ₹3,000 share isn't riskier than a ₹200 share. Prices also trend over time, so they are non-stationary. Daily log returns, ln(Pₜ/Pₜ₋₁), are unit-free and comparable, and every risk feature is defined on them.

**3. K-means vs GMM: what's the difference?**
K-means gives hard assignments: each stock goes to the nearest centroid by squared Euclidean distance. A GMM models each group as a Gaussian and gives soft, probabilistic membership, fitted by Expectation-Maximisation. With only 12 stocks we used spherical covariances with a variance floor (`reg_covar = 0.1`), because a full covariance per cluster can't be estimated.

**4. How does hierarchical clustering build a dendrogram?**
It starts with every stock as its own cluster and repeatedly merges the two closest clusters. The dendrogram records each merge and the distance at which it happened. Cutting the tree at a height gives K groups. Ward linkage merges the pair that least increases the within-cluster sum of squares, which is why it needs Euclidean distance.

**5. Explain Manhattan, Cosine and Mahalanobis distance.**
Manhattan adds the absolute differences feature by feature. Cosine compares the direction, or shape, of two risk profiles and ignores their size; it is not a true metric and is undefined for zero vectors. Mahalanobis measures distance in units of the data's own spread and discounts correlated features. We stabilised its covariance with Ledoit-Wolf shrinkage (condition number 524 → 5.8) and a pseudo-inverse.

**6. What does PCA do, and what is explained variance?**
PCA rotates the standardised features into uncorrelated components, ordered by how much variance each captures. Explained variance is the share of total variance a component keeps. Ours: PC1 53%, PC2 22%, PC3 18%, so 3 components keep 93%.

**7. What do the silhouette score and ARI measure?**
Silhouette compares each stock's distance to its own cluster with its distance to the nearest other cluster. It ranges from −1 to 1, and higher means better separated. Our best was Ward at 0.27. The Adjusted Rand Index compares two groupings by which pairs of stocks are together; 1 means identical and 0 means chance level.

**8. Why do cluster assignments change across distance metrics?**
Each metric defines "similar" differently. Cosine looks only at the shape of the profile, and Mahalanobis down-weights the correlated VaR, CVaR and volatility features. So the nearest neighbours change, and so do the groups. In our results Manhattan matched Euclidean exactly (ARI 1.0), Cosine agreed partly (ARI 0.42), and Mahalanobis agreed least (ARI 0.14).

**9. Why only 12 stocks?**
The brief suggested 8–12 stocks across sectors, so we chose 12 large caps from 9 sectors to keep the results interpretable and quick to run. The cost is statistical: the bootstrap ARI is only 0.26–0.50, so boundary stocks can switch groups. A larger universe such as the NIFTY 100 is our first future improvement.

---

## Part B: HMM and LDS

**10. Hidden state vs observed return: what's the difference?**
The observed return is the number we actually see each day. The hidden state is the unobserved market regime (Bull, Bear or High-Volatility) that we assume generated that return. The HMM infers the hidden state from the pattern of returns.

**11. What does the transition matrix tell us?**
Aᵢⱼ is the probability of moving from regime i today to regime j tomorrow, and each row sums to 1. Ours shows persistent Bull (0.988) and Bear (0.981) regimes. High-Volatility stays with probability 0.857, so it lasts about 7 days, and it always exits to Bear, never directly to Bull.

**12. What are forward and backward probabilities?**
The forward probability αₜ(j) is the probability of all the data up to day t, ending in state j: it is evidence from the past. The backward probability βₜ(i) is the probability of all the future data given state i at day t: it is evidence from the future. Multiplying them and normalising gives the posterior for each day.

**13. Sum-Product vs Viterbi?**
Sum-Product sums over all possible state paths and gives the marginal probability of each regime on each day. Viterbi takes the maximum over paths and gives the single most probable complete sequence. They disagreed on 3.7% of our days, because picking the best state day by day is not the same as picking the best whole path.

**14. Why do the posterior probabilities sum to one?**
On each day the market must be in exactly one of the three regimes, so p(zₜ = k | data) summed over k must equal 1. Mathematically, αₜ·βₜ summed over states equals p(y₁:T), the same normaliser for every day. Our code checks this: every row sums to 1 within 10⁻¹².

**15. How did you verify your Sum-Product implementation?**
We used three checks. Our log-likelihood equals hmmlearn's (−3642.938) and our posteriors match it to 1.2×10⁻¹². On a toy 2-state, 3-step HMM, our marginals equal brute-force enumeration of all 8 paths, and the hand-computed forward values match. Viterbi agrees with hmmlearn on 100% of days. These are covered in our 31 pytest tests.

**16. How are the regimes named? Isn't state 0 always Bull?**
No. EM can return the states in any order, so we name them after fitting, from the learned parameters. The largest variance is High-Volatility. Of the other two, the higher mean is Bull and the lower is Bear. Our "Bear" mean is −0.003% a day, about zero, so it is better described as a weak or choppy regime.

**17. Why three HMM states?**
BIC selects three states as the best balance between fit and complexity (BIC 5796, vs 5837 for four states). The four-state model has a slightly better held-out log-likelihood (−1.1726 vs −1.1744 per day). We kept three because they map onto Bull, Bear and High-Volatility, so the "best" number of states depends on the criterion.

**18. HMM vs LDS: what's the difference, and which did better?**
The HMM has a discrete hidden state (3 regimes) and can jump abruptly. The LDS has a continuous hidden state, estimated with our NumPy Kalman filter and RTS smoother, and changes smoothly. On unseen 2024–26 data, each model's one-step predictive log-likelihood improved on the i.i.d. baseline by: HMM +0.129 nats/day, LDS-Vol +0.061, and LDS-Trend about 0. LDS-Vol's density is a quasi-likelihood approximation, which we flag.

**19. Why did the trend LDS estimate near-zero process noise?**
Maximum likelihood chose the state noise Q ≈ 0, so the estimated drift is constant. Daily index returns have no time-varying trend that is predictable from past returns, which is consistent with weak-form market efficiency. It isn't a bug: a test shows the same code recovers a real random-walk signal on simulated data.

**20. What are the limitations, and what would you improve?**
Limitations: only 12 stocks, so cluster stability is moderate; the regime names are statistical interpretations; Gaussian emissions underweight fat tails; prices aren't dividend-adjusted; and the LDS-Vol likelihood is approximate. Improvements: a larger universe, multivariate HMM emissions (returns plus volatility), Student-t emissions, and a regime-aware portfolio backtest.

---

## Likely follow-up probes
- **"Can K-means use Manhattan distance?"** No. The mean update is only optimal for squared Euclidean distance; with L1 you would need K-medians. That's why the metric test used average-linkage clustering on precomputed distance matrices.
- **"Can Ward linkage use Cosine?"** No. Ward minimises the increase in Euclidean sum of squares, and our code raises an error if you try it on a precomputed matrix.
- **"Why did the selection criteria disagree on K?"** GMM BIC (244.6) chose K = 3, while K-means silhouette (0.361) chose K = 2, which only splits off TATASTEEL and INFY. We kept K = 3 for the risk-profile interpretation and report the disagreement openly.
- **"Is the regime chart a real-time prediction?"** No. The full-sequence Viterbi path and the smoothed posteriors use the whole series, so they are retrospective. Real-time detection uses the filtered posterior p(zₜ | y₁:ₜ). All out-of-sample scores use causal one-step-ahead predictions with parameters fitted on 2015–2023 only.
- **"How do you avoid numerical underflow?"** The recursions run in log space with log-sum-exp; a test runs 20,000 steps without underflow.
- **"Is there look-ahead bias in your preprocessing?"** No. We forward-fill gaps of at most 3 days and never back-fill, and train/test is split by date with no shuffling.
- **"Where does the data come from?"** NSE end-of-day closes from the public eod2 dataset (adjusted for splits and bonuses), cached in `data/raw/`. yfinance is tried first when refreshing, and synthetic data is a labelled last resort.

---

## Essential terms (one line each)
| Term | Meaning |
|---|---|
| Log return | ln(Pₜ / Pₜ₋₁): the daily percentage change, comparable across stocks |
| Volatility | Standard deviation of daily returns: how much a stock swings |
| Skewness / kurtosis | Asymmetry of returns (negative = big falls) / how often extreme moves happen |
| VaR 95% | The daily loss exceeded on only the worst 5% of days |
| CVaR 95% | The average loss on those worst 5% of days |
| Max drawdown | Largest fall from a previous peak |
| Standardisation | Rescaling each feature to mean 0 and standard deviation 1 |
| Centroid | The mean point of a K-means cluster |
| BIC | Fit penalised by number of parameters; lower is better |
| Silhouette | How well each point fits its own cluster vs the next nearest (−1 to 1) |
| ARI | Agreement between two groupings, ignoring label numbers (1 = identical) |
| PCA | Rotation into uncorrelated components ordered by variance |
| Transition matrix | Probabilities of moving between hidden regimes from one day to the next |
| Emission | The distribution of returns given a regime (Gaussian here) |
| Filtered posterior | p(zₜ \| y₁:ₜ): uses data up to today, so real-time |
| Smoothed posterior | p(zₜ \| y₁:T): uses all data, so retrospective |
| Viterbi path | The single most probable complete sequence of regimes |
| Kalman filter | Optimal recursive estimate of a continuous hidden state under linear-Gaussian assumptions |
| Predictive log-likelihood | How much probability a model gave to tomorrow's actual return, using only the past |
