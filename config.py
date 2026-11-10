"""Central configuration for the Financial Risk Profiling & Regime Detection project.

Every experiment reads its settings from here so results are reproducible.
"""
from pathlib import Path

# ---------------------------------------------------------------- paths
ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
OUT_DIR = ROOT / "outputs"
FIG_DIR = OUT_DIR / "figures"
TAB_DIR = OUT_DIR / "tables"
RES_DIR = OUT_DIR / "results"

# ---------------------------------------------------------------- reproducibility
SEED = 42

# ---------------------------------------------------------------- Part A: asset universe
# 12 NSE (India) large caps across 9 sectors.
# key = short name used everywhere; value = (yfinance ticker, eod2 file name, sector)
STOCKS = {
    "RELIANCE":   ("RELIANCE.NS",   "reliance",   "Energy"),
    "TCS":        ("TCS.NS",        "tcs",        "IT Services"),
    "INFY":       ("INFY.NS",       "infy",       "IT Services"),
    "HDFCBANK":   ("HDFCBANK.NS",   "hdfcbank",   "Banking"),
    "ICICIBANK":  ("ICICIBANK.NS",  "icicibank",  "Banking"),
    "HINDUNILVR": ("HINDUNILVR.NS", "hindunilvr", "FMCG"),
    "ITC":        ("ITC.NS",        "itc",        "FMCG"),
    "SUNPHARMA":  ("SUNPHARMA.NS",  "sunpharma",  "Pharma"),
    "MARUTI":     ("MARUTI.NS",     "maruti",     "Automobile"),
    "TATASTEEL":  ("TATASTEEL.NS",  "tatasteel",  "Metals"),
    "BHARTIARTL": ("BHARTIARTL.NS", "bhartiartl", "Telecom"),
    "LT":         ("LT.NS",         "lt",         "Infrastructure"),
}
STOCK_START = "2021-10-01"   # ~5 years of daily data
STOCK_END = "2026-09-25"     # last date available in the cached dataset

# ---------------------------------------------------------------- Part B: market index
INDEX_NAME = "NIFTY50"
INDEX_YF = "^NSEI"
INDEX_EOD2 = "nifty 50"
INDEX_START = "2015-01-01"   # longer window so the HMM sees several regimes (incl. 2020 crash)
INDEX_END = STOCK_END
TRAIN_END = "2023-12-31"     # chronological split: train <= TRAIN_END < test

# ---------------------------------------------------------------- data sources
# Tried in this order unless a cache exists (see data_loader.load_* functions).
EOD2_URL = "https://raw.githubusercontent.com/BennyThadikaran/eod2_data/main/daily/{name}.csv"

# ---------------------------------------------------------------- Part A settings
RETURN_TYPE = "log"           # daily log returns
VAR_LEVEL = 0.95              # VaR / CVaR confidence
K_RANGE = range(2, 7)         # candidate cluster counts (n_assets = 12)
N_CLUSTERS = None             # None -> chosen automatically by silhouette (K-means)
LINKAGES = ["ward", "average", "complete"]
PCA_VARIANCE_TARGET = 0.80    # keep the fewest PCs explaining >= 80% variance
N_SEED_RUNS = 50              # initialisation-stability runs
N_BOOTSTRAP = 100             # block-bootstrap stability runs
BOOTSTRAP_BLOCK = 20          # trading days per block (~1 month) keeps volatility clustering
MAHALANOBIS_SHRINKAGE = "ledoit_wolf"

# ---------------------------------------------------------------- Part B settings
HMM_STATES = 3
HMM_RESTARTS = 10             # random restarts of Baum-Welch, best train log-lik kept
HMM_N_ITER = 500
ROLLING_VOL_WINDOW = 21       # ~1 trading month
RETURN_SCALE = 100.0          # model returns in percent for numerical conditioning
