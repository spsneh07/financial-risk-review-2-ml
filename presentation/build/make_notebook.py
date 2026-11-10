"""Generate the single self-contained notebook `Financial_Risk_Regime_Project.ipynb`
from the tested project sources (same code -> same results).

Run from the project root:  python presentation/build/make_notebook.py
"""
import re
import textwrap
from pathlib import Path

import nbformat as nbf

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
PREFIX = re.compile(r"\b(cl|dm|ev|sp|hm|lds|rf|st|viz|pa|dl|clustering)\.(?=[A-Za-z_])")


def clean_module(name: str) -> str:
    code = (SRC / f"{name}.py").read_text()
    code = re.sub(r'^""".*?"""\n', "", code, count=1, flags=re.S)          # module docstring
    out = []
    for line in code.splitlines():
        s = line.strip()
        if s in ("import config",) or s.startswith("from src") or s.startswith("from __future__"):
            continue
        if s.startswith("matplotlib.use("):
            continue
        out.append(line)
    code = "\n".join(out).strip() + "\n"
    code = PREFIX.sub("", code)
    if name == "visualization":
        code = code.replace("    plt.close(fig)\n    return path", "    plt.show()\n    return path")
        code = code.replace("import matplotlib\n\n", "import matplotlib\n")
    return code


def config_cell() -> str:
    code = (ROOT / "config.py").read_text()
    code = re.sub(r'^""".*?"""\n', "", code, count=1, flags=re.S)
    code = code.replace("from pathlib import Path\n", "")
    code = code.replace("ROOT = Path(__file__).resolve().parent", "ROOT = Path.cwd()   # run the notebook from the project folder (or any folder)")
    body = textwrap.indent(code.strip(), "    ")
    return ("from pathlib import Path\n\n\nclass config:\n    \"\"\"All settings in one place (same values as config.py).\"\"\"\n"
            + body + "\n\n\nfor _d in (config.FIG_DIR, config.TAB_DIR, config.RES_DIR, config.RAW_DIR):\n"
            "    _d.mkdir(parents=True, exist_ok=True)\nprint('Working folder:', config.ROOT)\n")


def main_sections(func: str):
    """Split run_part_a / run_part_b of main.py into cells at each banner()."""
    code = (ROOT / "main.py").read_text()
    start = code.index(f"def {func}(args, results):")
    end = code.index("\ndef ", start + 10)
    body = [l for l in code[start:end].splitlines()[1:] if not l.startswith("#")]
    body = textwrap.dedent("\n".join(body)).strip("\n").splitlines()
    cells, cur = [], []
    for line in body:
        if line.startswith("banner(") and cur:
            cells.append("\n".join(cur).strip("\n"))
            cur = []
        cur.append(line)
    cells.append("\n".join(cur).strip("\n"))
    return [PREFIX.sub("", c) + "\n" for c in cells if c.strip()]


md = nbf.v4.new_markdown_cell
cc = nbf.v4.new_code_cell
nb = nbf.v4.new_notebook()
C = []

C.append(md("""# Financial Market Risk Profiling and Regime Detection
### Clustering · Gaussian Mixture Models · Hidden Markov Models · Linear Dynamical Systems
**Machine Learning: Project Review 2**
**Made by:** Srushti More [298], Agadh Khanolkar [299], Sneh Prasad [311]

This single notebook contains **all** of the project's code and runs it end to end:

| Part | Question | Methods |
|---|---|---|
| **A: Unit III** | Which stocks share a risk profile? | 7 risk features → PCA → K-means, GMM, Hierarchical; Manhattan / Cosine / Mahalanobis; silhouette, DB, CH; ARI stability |
| **B: Unit IV** | Which market regime are we in? | 3-state Gaussian HMM; our own NumPy **Sum-Product** and **Viterbi**; Kalman-filter **LDS** comparison |

**How to run:** *Kernel → Restart & Run All* (about 1 minute). Data is read from `data/raw/` if it is present; otherwise it is downloaded (yfinance → NSE eod2 dataset on GitHub). Simulated data is used only as a last resort, and is then clearly labelled **SYNTHETIC**."""))

C.append(md("## 0. Setup\nThe next cell installs any missing packages (safe to re-run)."))
C.append(cc("%pip install numpy pandas scipy scikit-learn matplotlib seaborn hmmlearn yfinance"))
C.append(cc("""import io, json, logging, time, warnings, itertools, urllib.parse, urllib.request
from dataclasses import dataclass

import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from scipy.special import logsumexp
from scipy.optimize import minimize
from scipy.spatial.distance import pdist, squareform
from scipy.cluster.hierarchy import linkage, dendrogram
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.mixture import GaussianMixture
from sklearn.covariance import LedoitWolf
from sklearn.metrics import (silhouette_score, davies_bouldin_score, calinski_harabasz_score,
                             adjusted_rand_score)
from hmmlearn.hmm import GaussianHMM

%matplotlib inline
warnings.filterwarnings("ignore")
logging.getLogger("yfinance").setLevel(logging.CRITICAL)
pd.set_option("display.width", 160); pd.set_option("display.max_columns", 20); pd.set_option("display.precision", 4)


def banner(txt):
    print("\\n" + "=" * 78 + f"\\n  {txt}\\n" + "=" * 78)


def jsonable(o):
    if isinstance(o, dict):
        return {str(k): jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [jsonable(v) for v in o]
    if isinstance(o, np.ndarray):
        return jsonable(o.tolist())
    if isinstance(o, np.floating):
        return float(o)
    if isinstance(o, np.integer):
        return int(o)
    return o"""))
C.append(md("### Configuration (tickers, windows, seeds, K, restarts)"))
C.append(cc(config_cell()))
C.append(cc("""class args:                 # run options (same as the command-line flags of main.py)
    source = None           # None = automatic fallback; or "cache" | "yfinance" | "eod2" | "synthetic"
    refresh_data = False    # True = ignore the local cache and download again
    quick = False           # True = fewer bootstrap / restart iterations (faster demo)

np.random.seed(config.SEED)
results = {"config": {"seed": config.SEED, "quick": args.quick, "source_flag": args.source}}
T_START = time.time()"""))

modules_a = [
    ("data_loader", "## 1. Data acquisition and preprocessing\nOrdered fallback: **cache → yfinance → eod2 (NSE, GitHub) → synthetic**. We align trading dates, forward-fill gaps of 3 days or less, **never back-fill** (that would leak future prices), and use daily log returns."),
    ("risk_features", "## 2. Risk features\nMean, volatility, skewness, excess kurtosis, historical **VaR95**, **CVaR95** and **max drawdown**, all on daily log returns, then z-scored."),
    ("distance_metrics", "## 3. Dissimilarity metrics\nManhattan, Cosine (scale-invariant; near-zero vectors are flagged) and Mahalanobis (**Ledoit-Wolf shrinkage + pseudo-inverse**, because 12 assets and 7 correlated features make the covariance near-singular)."),
    ("clustering", "## 4. Clustering algorithms\nK-means (squared Euclidean only), GMM (EM, spherical/diag with a variance floor) and agglomerative clustering. **Ward is Euclidean only** and is refused for precomputed distances."),
    ("evaluation", "## 5. Evaluation metrics\nSilhouette is valid for any distance. Davies-Bouldin and Calinski-Harabasz need Euclidean coordinates, so they are never computed on a precomputed matrix. ARI ignores label numbering."),
    ("pca_analysis", "## 6. PCA helpers"),
    ("stability", "## 7. Stability experiments (ARI)\nSeeds, moving-block bootstrap of trading days, and leave-one-asset-out."),
    ("visualization", "## 8. Plotting functions"),
]
for name, text in modules_a:
    C.append(md(text))
    C.append(cc(clean_module(name)))

C.append(md("---\n# PART A: Risk profiling with clustering (Unit III)"))
for code in main_sections("run_part_a"):
    C.append(cc(code))

C.append(md("---\n# PART B: Market regimes with HMM and LDS (Unit IV)"))
modules_b = [
    ("sum_product", "## 9. Sum-Product (forward-backward) and Viterbi, written in NumPy\n"
     "* **Forward** αₜ(j) = bⱼ(yₜ) Σᵢ αₜ₋₁(i) Aᵢⱼ  ·  **Backward** βₜ(i) = Σⱼ Aᵢⱼ bⱼ(yₜ₊₁) βₜ₊₁(j)\n"
     "* **Sum-Product posterior** γₜ(i) = αₜ(i) βₜ(i) / p(y₁:T): sums over all paths, giving a marginal per day\n"
     "* **Viterbi** δₜ(j) = bⱼ(yₜ) maxᵢ δₜ₋₁(i) Aᵢⱼ: maximises over paths, giving one best sequence\n\n"
     "All recursions use log-sum-exp, so there is no underflow.\n\n"
     "**Real-time vs retrospective:**\n"
     "* **Filtered posterior** p(zₜ | y₁:ₜ) uses only data up to day t, so it is causal and suitable for real-time detection.\n"
     "* **Smoothed posterior** p(zₜ | y₁:T) uses the full sequence, so it is retrospective (historical analysis).\n"
     "* **Full-sequence Viterbi** gives the most probable complete path for the supplied sequence, so it is also retrospective.\n"
     "* The out-of-sample comparison uses the one-step-ahead predictive density p(yₜ | y₁:ₜ₋₁) from causal filters only."),
    ("hmm_model", "## 10. Gaussian HMM (Baum-Welch via hmmlearn, restarts) and regime naming\nStates are named from **learned** parameters: largest σ → High-Volatility; of the other two, higher μ → Bull and lower μ → Bear."),
    ("linear_dynamical_system", "## 11. Linear Dynamical System: NumPy Kalman filter, RTS smoother, MLE\n"
     "xₜ = F xₜ₋₁ + c + wₜ,  yₜ = H xₜ + d + vₜ. **LDS-Trend** = random-walk drift of returns; **LDS-Vol** = AR(1) log-variance observed through log r²."),
]
for name, text in modules_b:
    C.append(md(text))
    C.append(cc(clean_module(name)))

for code in main_sections("run_part_b"):
    C.append(cc(code))

C.append(md("## 12. Save the summary"))
C.append(cc("""results["total_seconds"] = round(time.time() - T_START, 1)
name = "results_synthetic.json" if args.source == "synthetic" else "results.json"
(config.RES_DIR / name).write_text(json.dumps(jsonable(results), indent=2))
banner(f"DONE in {results['total_seconds']} s  |  results -> {config.RES_DIR / name}")"""))

C.append(md("## 13. Verification checks (the key tests, run inline)"))
C.append(cc('''def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    assert cond, name

# 1) Sum-Product on the toy HMM equals brute-force enumeration of all 2^3 paths; hand-computed alphas
pi0, A0, B0 = toy_example()
toy = sum_product(pi0, A0, np.log(B0))
bf_marg, bf_p, bf_best = brute_force(pi0, A0, B0)
la, ll = forward(np.log(pi0), np.log(A0), np.log(B0))
check("toy p(y) = brute force (0.10248)", abs(np.exp(toy["loglik"]) - bf_p) < 1e-12)
check("toy marginals = brute force", np.allclose(toy["gamma"], bf_marg, atol=1e-12))
check("hand-computed alpha values", np.allclose(np.exp(la), [[0.48, 0.12], [0.0768, 0.1512], [0.022848, 0.079632]]))
check("toy Viterbi = brute-force best path", viterbi(pi0, A0, np.log(B0))[0].tolist() == bf_best.tolist())

# 2) On the real NIFTY model: our code = hmmlearn, posteriors normalised, xi consistent
check("log-likelihood = hmmlearn", abs(out["loglik"] - ref_ll) < 1e-6)
check("posteriors = hmmlearn (< 1e-8)", np.abs(gamma - ref_gamma).max() < 1e-8)
check("posterior rows sum to 1", np.allclose(gamma.sum(1), 1))
check("sum_j xi_t(i,j) = gamma_t(i)", np.allclose(out["xi"].sum(2), gamma[:-1], atol=1e-8))
check("Viterbi = hmmlearn on every day", agree_lib == 1.0)
check("regime names from learned params", set(names.values()) == {"Bull", "Bear", "High-Volatility"})

# 3) Distances are valid matrices; Ward refused on precomputed D
for m, obj in mats.items():
    check(f"{m} matrix valid", all(validate_distance_matrix(obj["D"]).values()))
try:
    hierarchical_precomputed(mats["Manhattan"]["D"], 3, "ward"); check("Ward refused", False)
except ValueError:
    check("Ward refused on precomputed distances", True)

# 4) Kalman filter + smoother recover a simulated random walk better than raw observations
rng = np.random.default_rng(0)
xt = np.cumsum(rng.normal(0, np.sqrt(0.05), 500)); yt = xt + rng.normal(0, 1, 500)
kf = local_level(0.05, 1.0, 0.0, 1.0); fk = kf.filter(yt); xs_, _ = kf.smooth(fk)
rm = lambda e: np.sqrt(np.mean(e ** 2))
check("Kalman: smoothed < filtered < raw error", rm(xs_[:, 0] - xt) < rm(fk["x_filt"][:, 0] - xt) < rm(yt - xt))
print("\\nAll checks passed.")'''))

C.append(md("""## Conclusion
* **Part A:** three risk tiers: a low-risk core, a tail-risk pair (ITC, LT) and a high-risk group (TCS, INFY, TATASTEEL). The choice of distance changes the clusters; Mahalanobis is the most stable.
* **Part B:** BIC selects the 3-state HMM as a balance between fit and complexity; the 4-state model has a slightly better held-out log-likelihood (−1.1726 vs −1.1744 per day). We keep 3 states for the Bull, Bear and High-Volatility interpretation, so the optimal number of states depends on the criterion. The regime timeline (full-sequence Viterbi and smoothed posteriors) is a retrospective labelling that includes the COVID-2020 crash; real-time detection would use the filtered posterior. Our Sum-Product and Viterbi match hmmlearn exactly. On unseen 2024–26 data the HMM predicts better than the Kalman LDS and the i.i.d. baseline.
* **Limitations:** only 12 assets; regime names are statistical interpretations; the LDS-Vol density is approximate; prices are not dividend-adjusted.
* **Future scope:** a larger universe, multivariate HMM emissions, a regime-aware portfolio."""))

nb["cells"] = C
nb["metadata"] = {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                  "language_info": {"name": "python"}}
out = ROOT / "Financial_Risk_Regime_Project.ipynb"
nbf.write(nb, out)
print("wrote", out, len(C), "cells")
