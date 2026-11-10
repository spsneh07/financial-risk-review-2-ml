# Live Demo Guide (90–120 seconds)
All commands and file names below exist in the project. Run them from the project folder.

> **Notebook-only demo (simplest, matches the slides):** open `Financial_Risk_Regime_Project.ipynb` from the project folder and scroll the saved outputs, or use **Restart & Run All** (about 1 minute). Point at the same things listed below: the "We selected K=3" line, the PCA cluster plots, the transition matrix, "log p(y_1:T): ours = … hmmlearn = …", the FILTERED posterior table, the regime and 2020 charts, and "All checks passed" at the end. The `python main.py` route below is optional.

## Before the review (tonight)
```
cd /d "D:\ML Review 2\financial-risk-regime-project"
.venv\Scripts\activate
python main.py
```
- This confirms everything works on your laptop and refreshes all outputs with the full-mode numbers used on the slides.
- Leave this terminal window open for tomorrow.
- Also open `Financial_Risk_Regime_Project.ipynb` once, so its saved outputs are ready as a backup.

> ⚠️ **Do not use `--quick` or `--part A` / `--part B` during the review.** They overwrite the saved tables and results with lower-iteration or partial numbers, which won't match the slides. If you ran one by accident, run `python main.py` again.

---

## Demo sequence

### Step 1: Run the pipeline (≈ 40–60 s while you talk)
```
python main.py
```
**Say while it runs:**
"This one command loads the cached NSE data, so no internet is needed. It computes the seven risk features, runs K-means, GMM and hierarchical clustering with three distance metrics, and fits the Hidden Markov Model and Kalman filter. Every number on our slides comes from this run."

### Step 2: Part A output (≈ 20 s)
Scroll up in the terminal to these lines:
| Look for | Say |
|---|---|
| `Source: cache (eod2)` | "Real NSE data, cached locally." |
| `We selected K=3 … K-means silhouette favors K=2 …` | "BIC chose three clusters; silhouette preferred two, and we report that openly." |
| The `Cluster assignments` table | "Ward puts TCS, Infosys and Tata Steel in the high-risk group." |
| `Keeping 3 PCs (>= 80% variance)` | "Three principal components keep 93% of the variance." |

**Open the figure:** `outputs\figures\A5_pca_clusters.png` (three panels: K-means, GMM, Ward). If it's there, `A5b_pca_primary.png` is a larger single-panel view of the Ward groups.
"The plot only visualises clusters on two components; the clustering used all seven features."

### Step 3: Part B output (≈ 25 s)
| Look for | Say |
|---|---|
| `Transition matrix A` and the `Emission parameters` table | "Three regimes, named from their learned mean and variance." |
| `log p(y_1:T): ours = -3642.937947   hmmlearn = -3642.937947` | "Our own NumPy Sum-Product gives exactly the library's answer." |
| `Toy 2-state HMM check … brute-force` | "And it matches brute-force enumeration on a small example." |
| `FILTERED posterior p(z_t \| y_1:t)` | "This is the real-time view. On the last day, 25 Sep 2026, it gives Bull 0.77 and Bear 0.23." |
| `BIC selects the 3-state HMM … 4-state model … slightly better` | "BIC picks three states; four fit the test data slightly better." |
| The `HMM-3 (forward filter, discrete)  -1.1744` row | "On unseen data the HMM predicts best." |

**Open the figures:**
- `outputs\figures\B1_nifty_regimes_viterbi.png`: "Retrospective regime labels; the blue band is the COVID-2020 crash."
- `outputs\figures\B5_sumproduct_vs_viterbi_2020.png`: "Smoothed vs real-time filtered probability, and the Viterbi path."

### Step 4 (optional, if asked): tests (≈ 10–35 s)
```
pytest -q
```
Expected: `31 passed`.

---

## Fallbacks
| Problem | What to do |
|---|---|
| No internet | Nothing to do. The default run reads `data\raw\` (cached NSE data); no download happens. |
| You want to show the synthetic fallback | `python main.py --source synthetic --quick`. It writes to `outputs\synthetic\` (separate from the real results) and every chart footer says **SYNTHETIC**. |
| Python or environment error on the day | Open `Financial_Risk_Regime_Project.ipynb` and scroll the saved outputs: the "We selected K=3" cell, the PCA plots, the "log p(y_1:T): ours = … hmmlearn = …" cell, and the final "All checks passed". |
| Even the notebook won't open | Open the PNGs in `outputs\figures\` and the console log `outputs\results\run_log.txt`, which holds the full printed output of the last run. |
| Run is slow | Keep talking through Step 1's script. The full run takes about 35–60 s on a laptop. |

## Expected key outputs (for a quick sanity check)
- Part A: `K-means silhouette favors K=2`; Ward silhouette `0.269`; PCA cumulative `0.528 / 0.750 / 0.930`.
- Part B: Bull mean `+0.1168%`, σ `0.6027%`; High-Volatility σ `3.8765%`; `ours = hmmlearn = -3642.937947`; Viterbi agreement `1.0000`.
- Comparison: HMM-3 `-1.1744` > LDS-Vol* `-1.2423` > i.i.d. `-1.3034` ≈ LDS-Trend `-1.3036`.
