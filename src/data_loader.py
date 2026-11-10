"""Data acquisition with a transparent, ordered fallback chain.

Order (first success wins):
  1. local cache       data/raw/*.csv   (written by a previous successful download)
  2. yfinance          Yahoo Finance adjusted close (needs internet)
  3. eod2 GitHub       real NSE end-of-day data, split/bonus adjusted (needs internet)
  4. synthetic         simulated prices -- ALWAYS labelled "SYNTHETIC" in every output

The source actually used is returned with the data and printed/saved, so a
synthetic run can never be mistaken for real market data.
"""
from __future__ import annotations

import io
import json
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

import config

SOURCES = ("cache", "yfinance", "eod2", "synthetic")


# ------------------------------------------------------------------ helpers
def _meta_path(kind: str) -> Path:
    return config.RAW_DIR / f"{kind}_source.json"


def _save_cache(df: pd.DataFrame, kind: str, source: str) -> None:
    config.RAW_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(config.RAW_DIR / f"{kind}_prices.csv", index_label="Date")
    _meta_path(kind).write_text(json.dumps({"source": source}, indent=2))


def _load_cache(kind: str) -> tuple[pd.DataFrame, str] | None:
    path = config.RAW_DIR / f"{kind}_prices.csv"
    if not path.exists():
        return None
    df = pd.read_csv(path, index_col="Date", parse_dates=True)
    src = "unknown"
    if _meta_path(kind).exists():
        src = json.loads(_meta_path(kind).read_text()).get("source", "unknown")
    return df, f"cache ({src})"


def _clean(df: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
    """Align trading dates and handle missing values.

    * keep only the requested window
    * drop dates where *every* series is missing (exchange holidays)
    * forward-fill gaps of at most 3 days (isolated missing prints), never back-fill
      (back-filling would leak future prices into the past)
    * drop any remaining rows with NaN so all assets share one calendar
    """
    df = df.sort_index()
    df = df.loc[(df.index >= pd.Timestamp(start)) & (df.index <= pd.Timestamp(end))]
    df = df.dropna(how="all")
    df = df.ffill(limit=3).dropna(how="any")
    df = df[(df > 0).all(axis=1)]
    return df


def _from_yfinance(tickers: dict[str, str], start: str, end: str) -> pd.DataFrame:
    import yfinance as yf  # optional dependency

    end_excl = (pd.Timestamp(end) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    raw = yf.download(list(tickers.values()), start=start, end=end_excl,
                      auto_adjust=True, progress=False, threads=True)
    if raw is None or raw.empty:
        raise RuntimeError("yfinance returned no data")
    close = raw["Close"] if isinstance(raw.columns, pd.MultiIndex) else raw[["Close"]]
    if isinstance(close, pd.Series):
        close = close.to_frame()
    inv = {v: k for k, v in tickers.items()}
    close = close.rename(columns=inv)
    if len(tickers) == 1 and list(close.columns) == ["Close"]:
        close.columns = list(tickers.keys())
    missing = set(tickers) - set(close.columns)
    if missing or close.dropna(how="all").shape[0] < 100:
        raise RuntimeError(f"yfinance incomplete (missing={missing})")
    close.index = pd.to_datetime(close.index).tz_localize(None)
    return close


def _from_eod2(names: dict[str, str], start: str, end: str) -> pd.DataFrame:
    frames = {}
    for key, name in names.items():
        url = config.EOD2_URL.format(name=urllib.parse.quote(name))
        with urllib.request.urlopen(url, timeout=60) as resp:
            text = resp.read().decode("utf-8")
        df = pd.read_csv(io.StringIO(text), parse_dates=["Date"], index_col="Date")
        frames[key] = df["Close"].astype(float)
    return pd.DataFrame(frames)


def synthetic_prices(names: list[str], start: str, end: str, seed: int = config.SEED,
                     regime_switching: bool = False) -> pd.DataFrame:
    """SYNTHETIC prices (clearly not market data).

    Assets are generated from a 2-factor model with per-asset betas, volatilities and
    Student-t shocks so the risk features differ meaningfully between assets.
    With ``regime_switching`` a 3-state Markov chain drives drift/volatility (used for
    the synthetic index so the HMM has real structure to recover).
    """
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range(start, end)
    T, N = len(dates), len(names)
    if regime_switching:
        mu = np.array([0.06, -0.08, -0.05])  # % per day: bull, bear, high-vol
        sd = np.array([0.7, 1.1, 2.6])
        P = np.array([[0.985, 0.010, 0.005], [0.020, 0.970, 0.010], [0.030, 0.020, 0.950]])
        s = np.zeros(T, dtype=int)
        for t in range(1, T):
            s[t] = rng.choice(3, p=P[s[t - 1]])
        r = (mu[s] + sd[s] * rng.standard_normal(T)) / 100
        prices = 10000 * np.exp(np.cumsum(r))
        return pd.DataFrame({names[0]: prices}, index=dates)
    market = rng.standard_t(5, T) * 0.009
    style = rng.standard_t(5, T) * 0.006
    beta = rng.uniform(0.5, 1.5, N)
    gamma = rng.uniform(-1, 1, N)
    idio = rng.uniform(0.006, 0.02, N)
    drift = rng.uniform(-0.0002, 0.0008, N)
    shocks = rng.standard_t(4, (T, N)) * idio / np.sqrt(2)
    r = drift + np.outer(market, beta) + np.outer(style, gamma) + shocks
    prices = 100 * np.exp(np.cumsum(r, axis=0))
    return pd.DataFrame(prices, index=dates, columns=names)


def _load(kind: str, yf_map: dict, eod_map: dict, start: str, end: str,
          prefer: str | None, refresh: bool, regime_switching: bool):
    order = list(SOURCES)
    if prefer:
        order = [prefer]
    elif refresh:
        order = [s for s in SOURCES if s != "cache"]
    errors = {}
    for src in order:
        try:
            if src == "cache":
                hit = _load_cache(kind)
                if hit is None:
                    raise FileNotFoundError("no cache")
                df, label = hit
                return _clean(df, start, end), label
            if src == "yfinance":
                df = _from_yfinance(yf_map, start, end)
            elif src == "eod2":
                df = _from_eod2(eod_map, start, end)
            else:
                df = synthetic_prices(list(yf_map), start, end,
                                      regime_switching=regime_switching)
            df = _clean(df, start, end)
            if src != "synthetic":
                _save_cache(df, kind, src)
            label = "SYNTHETIC (simulated, not market data)" if src == "synthetic" else src
            return df, label
        except Exception as exc:  # noqa: BLE001 -- we report and fall through
            errors[src] = f"{type(exc).__name__}: {str(exc)[:120]}"
    raise RuntimeError(f"All data sources failed: {errors}")


def load_stock_prices(prefer: str | None = None, refresh: bool = False):
    yf_map = {k: v[0] for k, v in config.STOCKS.items()}
    eod_map = {k: v[1] for k, v in config.STOCKS.items()}
    return _load("stocks", yf_map, eod_map, config.STOCK_START, config.STOCK_END,
                 prefer, refresh, regime_switching=False)


def load_index_prices(prefer: str | None = None, refresh: bool = False):
    yf_map = {config.INDEX_NAME: config.INDEX_YF}
    eod_map = {config.INDEX_NAME: config.INDEX_EOD2}
    df, label = _load("index", yf_map, eod_map, config.INDEX_START, config.INDEX_END,
                      prefer, refresh, regime_switching=True)
    return df[config.INDEX_NAME], label


def log_returns(prices: pd.DataFrame | pd.Series):
    """Daily log returns r_t = ln(P_t / P_{t-1}); first row dropped."""
    return np.log(prices / prices.shift(1)).dropna()
