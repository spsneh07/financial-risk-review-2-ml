# Project Review 2: 6-Minute Presentation Script
**Financial Market Risk Profiling and Regime Detection Using Clustering, GMMs, HMMs and LDS**
Srushti More [298] · Agadh Khanolkar [299] · Sneh Prasad [311]

**Deck:** `presentation/project_review_2.pptx` (12 slides). Every number below comes from the saved run (`outputs/results/results.json`, `outputs/results/run_log.txt`).
**Length:** 789 spoken words ≈ **5 min 50 s** at a relaxed 135 words per minute, including transitions (about 5:15 if you speak quickly); with slide changes and pauses, plan on **6 minutes** (see the word count at the end).
**Rule of thumb:** say the words in the quote blocks; point at what each slide's "Point at" line says. Don't read the slide text aloud.

| Member | Slides | Topic | Words | Time |
|---|---|---|---|---|
| Srushti | 1–5 | Problem, pipeline, data, Part A algorithms | 274 | ≈ 2:00 |
| Agadh | 6–7 | Distance metrics, PCA, evaluation, Part A results | 248 | ≈ 1:50 |
| Sneh | 8–12 | HMM, Sum-Product vs Viterbi, LDS, results, conclusion | 267 | ≈ 2:00 |

> If the examiner says you have **under 5 minutes**, switch to `project_review_2_short.pptx` (7 slides) and its script at the top of `presentation_notes.md`.

---

## MEMBER 1: SRUSHTI MORE (≈ 2:00)

### Slide 1: Title (≈ 10 s)
**Key point:** two parts, mapped to Unit III and Unit IV.
> Good morning. We are Srushti, Agadh and Sneh. Our project is Financial Market Risk Profiling and Regime Detection. Part A uses clustering, from Unit Three, and Part B uses Hidden Markov Models, from Unit Four.

### Slide 2: Problem statement and objectives (≈ 25 s)
**Point at:** the A and B cards. **Key point:** risk has many dimensions, and markets change behaviour.
> Why does this matter? Two stocks can have the same volatility but very different crash behaviour, so one number cannot describe risk. Markets also switch between calm, choppy and crisis periods. So we ask two questions. Which stocks share a risk profile? And which hidden regime is the market in?

### Slide 3: System architecture (≈ 20 s)
**Point at:** the two lanes, left to right. **Key point:** one reproducible pipeline.
> This is our pipeline. The top lane clusters twelve stocks. The bottom lane fits a Hidden Markov Model to the NIFTY 50 and compares it with a Kalman filter. One notebook, run top to bottom, regenerates our figures and tables.

### Slide 4: Dataset and risk features (≈ 35 s)
**Point at:** the data table, then the heatmap. **Key point:** returns, not prices; standardise before clustering.
> We used twelve NSE stocks from nine sectors, October 2021 to September 2026: one thousand two hundred thirty-five daily returns each. We don't cluster prices, because a high price doesn't mean high risk, so we use daily log returns. Each stock gets seven risk features, including Value at Risk, the loss exceeded on only the worst five percent of days, and maximum drawdown, the biggest fall from a peak. We standardise every feature so no single unit dominates the distances.

### Slide 5: Clustering algorithms (≈ 30 s)
**Point at:** the three algorithm cards, then the BIC panel. **Key point:** hard vs soft vs hierarchical assignment; the selection criteria don't fully agree.
> K-means assigns each stock to its nearest centroid. A Gaussian Mixture Model gives soft, probabilistic membership in bell-shaped groups. Hierarchical clustering merges the closest groups step by step, building a tree called a dendrogram. GMM's BIC chose three clusters, but K-means silhouette preferred two, so the criteria didn't fully agree. We kept three for the risk-profile comparison.

**Transition:**
> Agadh will now show how the choice of distance changes these groups.

---

## MEMBER 2: AGADH KHANOLKAR (≈ 1:50)

### Slide 6: Distance metrics and PCA (≈ 55 s)
**Point at:** the three metric cards, then the assignment grid in the middle. **Key point:** the distance metric changes the clusters; K-means is Euclidean only.
> Thanks, Srushti. Clustering depends on how we measure difference. Manhattan distance adds up feature-by-feature gaps. Cosine compares the shape of a risk profile, not its size. Mahalanobis corrects for correlated features: VaR, CVaR and volatility move together, so without it that information counts three times. K-means only works with Euclidean distance, so for a fair test we ran the same average-linkage hierarchical clustering on every distance matrix. Manhattan matched Euclidean exactly, but Cosine and Mahalanobis grouped stocks differently. We also used PCA, which compresses correlated features into fewer components. Explained variance is the share of information each component keeps: fifty-three, twenty-two and eighteen percent, so three components keep ninety-three percent.

### Slide 7: Part A results (≈ 55 s)
**Point at:** the right-hand scatter (Ward), then the table. **Key point:** three risk tiers, honestly moderate stability.
> These plots only visualise the clusters on two principal components; the clustering itself used all seven features. Ward clustering had the best silhouette, zero point two seven. Silhouette measures how much closer a stock is to its own group than to the next one. We found three groups: a low-risk core of seven stocks, a tail-risk pair, ITC and L and T, with negative skew and fat tails, and a high-risk group, TCS, Infosys and Tata Steel, with drawdowns near forty-nine percent. For stability we used the Adjusted Rand Index, which compares groupings while ignoring cluster numbers. When we resampled the trading days, the ARI was only zero point two six to zero point five, because twelve stocks is a small sample. Mahalanobis was the most stable.

**Transition:**
> Sneh will now take us from stocks to the whole market.

---

## MEMBER 3: SNEH PRASAD (≈ 2:00)

### Slide 8: Hidden Markov Model (≈ 35 s)
**Point at:** the transition matrix, then the three emission curves. **Key point:** hidden regime vs observed return; names come from learned parameters.
> Thanks, Agadh. The market's regime is hidden; we only observe daily returns. Our HMM has three hidden states, a transition matrix for switching between them, and a Gaussian distribution of returns for each state. We trained it on 2015 to 2023. Bull averages plus zero point one two percent a day. Bear averages almost zero, so it's really a weak, choppy regime. High-volatility swings about four percent a day and lasts about a week. BIC chose three states, although four scored slightly better on test data.

### Slide 9: Sum-Product vs Viterbi (≈ 35 s)
**Point at:** the two equation cards, then the 2020 chart. **Key point:** sum over paths vs max over paths; retrospective vs real-time.
> We coded the inference ourselves. The forward pass collects evidence from the past, the backward pass from the future, and together they give each regime's probability on each day. That's Sum-Product: it sums over all paths. Viterbi takes the maximum instead, giving one most likely complete path. Both use the whole series, so they're retrospective; the filtered curve is the real-time view. Our results match the hmmlearn library exactly.

### Slide 10: LDS vs HMM (≈ 20 s)
**Point at:** the top chart, the blue curve against the orange one. **Key point:** continuous vs discrete hidden state.
> We also built a Kalman-filter Linear Dynamical System, where the hidden state is continuous. It found no predictable trend in daily returns, but it tracks volatility smoothly. Both models follow realised volatility closely; the HMM jumps between regimes, while the LDS moves smoothly.

### Slide 11: Results and limitations (≈ 20 s)
**Point at:** the bar chart at bottom left. **Key point:** fair, causal, held-out comparison.
> On unseen 2024 to 2026 data, each model predicted tomorrow's return using only past data. The HMM scored best, the volatility LDS second, and the trend LDS matched the simple baseline. Our limitations: only twelve stocks, and regime names are statistical labels.

### Slide 12: Conclusion (≈ 10 s)
**Key point:** what was built and what was learned.
> To conclude: stocks form three risk tiers, the distance metric matters, and regime switching predicts better than smooth trends. Thank you. We're happy to show the demo.

---

## Timing checklist
- Rehearse once with a timer. If you run long, cut these optional sentences first: the dendrogram sentence (slide 5), the PCA sentence (slide 6), and the trend sentence (slide 10).
- **Hand-offs:** Srushti → Agadh after slide 5; Agadh → Sneh after slide 7. Click to the next slide while saying the transition line.
- **Numbers to remember:** 12 stocks · 9 sectors · 1,235 returns · 7 features · K = 3 · 93% variance in 3 PCs · silhouette 0.27 · 3 HMM states · Bull +0.12%/day · High-Vol ≈ 3.9%/day.
